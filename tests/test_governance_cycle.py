"""Synthetic effects, bounded metadata and interruption recovery evidence."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from taskcarry.core import Core
from taskcarry.governance_cycle import GovernanceCycle
from taskcarry.store import GovernanceError
from taskcarry.cycle_contracts import SCHEMAS, DESCRIPTIONS


class GovernanceCycleTests(unittest.TestCase):
    def setUp(self):
        sandbox = Path(__file__).resolve().parents[1] / 'validation' / 'local' / 'cycle-tests'
        sandbox.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-', dir=sandbox)
        self.root = Path(self.temp.name)
        self.project = self.root / 'control'
        Core.initialize(self.project, 'Synthetic cycle')
        self.core = GovernanceCycle(self.project)
        self.core.task('catalog', state='active')
        self.core.task('guide', state='active')

    def tearDown(self):
        self.temp.cleanup()

    def assertCode(self, code, call, *args, **kwargs):
        with self.assertRaises(GovernanceError) as caught:
            call(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def start(self, **values):
        return self.core.cycle('start', **{'cycle_id': 'daily', 'owner': 'governor', 'task_id': 'catalog',
                                          'scope': ['catalog-memory'], **values})

    def action(self, action, data, request='one', **values):
        return self.core.cycle(action, **{'cycle_id': 'daily', 'owner': 'governor',
                                          'request_id': request, 'data': data, **values})

    def plan(self):
        return self.action('effect_plan', {'effect_id': 'write-guide', 'kind': 'local_document',
                                          'resource': 'catalog-memory', 'expected': 'Guide has the reviewed summary.'})

    def fact(self, **values):
        return self.core.facts('record', **{'source_id': 'chat:catalog', 'fact_id': 'scope',
            'source_revision': 'turn-1', 'task_id': 'catalog', 'kind': 'decision',
            'statement': 'Keep catalog scope local.', 'evidence': {'reference': 'chat:turn-1', 'summary': 'User selected local scope.'},
            'judgment': {'statement': 'No remote deployment is needed.', 'basis': 'The selected local scope.'}, **values})

    def register(self, **values):
        self.source = self.root / 'materials'
        self.source.mkdir(exist_ok=True)
        return self.core.source_scan('register', **{'source_id': 'files:catalog', 'root': str(self.source),
            'authorization_ref': 'user:synthetic-source-selection', **values})

    def scan(self, **values):
        return self.core.source_scan('start', **{'source_id': 'files:catalog', 'scan_id': 'inventory', 'max_entries': 2, **values})

    def pages(self, cursor):
        pages = []
        while cursor:
            page = self.core.source_scan('page', 'files:catalog', scan_id='inventory', cursor=cursor)['page']
            pages.append(page)
            cursor = page['next_cursor']
            self.assertLess(len(pages), 100)
        return pages

    def test_effect_plan_receipt_finish_are_distinct_and_retry_is_idempotent(self):
        self.start()
        self.plan()
        self.assertCode('CYCLE_EFFECTS_PENDING', self.action, 'finish', {'state': 'completed', 'next_step': 'None.'}, 'finish')
        result = self.action('effect_result', {'effect_id': 'write-guide', 'outcome': 'confirmed',
                             'evidence_ref': 'synthetic:guide-hash', 'statement': 'The exact expected file was read back.'}, 'verify')
        events = self.core.store.events()
        repeat = self.action('effect_result', {'effect_id': 'write-guide', 'outcome': 'confirmed',
                             'evidence_ref': 'synthetic:guide-hash', 'statement': 'The exact expected file was read back.'}, 'verify')
        self.assertTrue(repeat['reused'])
        self.assertEqual(result['receipt'], repeat['receipt'])
        self.assertEqual(events, self.core.store.events())
        done = self.action('finish', {'state': 'completed', 'next_step': 'Wait for actual user review.'}, 'finish')
        self.assertEqual('completed', done['cycle']['state'])
        self.assertEqual('active', self.core.store.get('tasks', 'catalog')['state'])
        self.assertFalse(done['cycle']['lock']['durable_reservation'])
        self.start(cycle_id='tomorrow')

    def test_unfinished_reservation_survives_reopen_without_ttl_stealing(self):
        self.start()
        reopened = GovernanceCycle(self.project)
        self.assertCode('CYCLE_RESERVED', reopened.cycle, 'start', cycle_id='other', owner='other',
                        task_id='catalog', scope=['catalog-memory'])
        self.assertCode('CYCLE_ID_CONFLICT', reopened.cycle, 'resume', cycle_id='daily', owner='other', scope=['catalog-memory'])
        self.assertCode('CYCLE_ID_CONFLICT', reopened.cycle, 'resume', cycle_id='daily', owner='governor', scope=['different'])
        resumed = reopened.cycle('resume', cycle_id='daily', owner='governor', scope=['catalog-memory'])
        self.assertTrue(resumed['reused'])
        self.assertFalse(resumed['cycle']['lock']['os_lock_held_by_this_session'])
        self.start(cycle_id='independent', task_id='guide', scope=['guide-memory'])

    def test_real_os_session_blocks_same_resource_but_not_database_or_other_resource(self):
        with self.core.cycle_session('daily', 'governor', ['catalog-memory'], task_id='catalog'):
            current = self.core.cycle('status', cycle_id='daily')['cycle']
            self.assertTrue(current['lock']['os_lock_held_by_this_session'])
            other = GovernanceCycle(self.project)
            self.assertCode('CYCLE_BUSY', other.cycle, 'resume', cycle_id='daily', owner='governor', scope=['catalog-memory'])
            # An OS cycle lock never holds the database mutation lock across AI work.
            other.task('guide', title='Can still save unrelated work')
            other.cycle('start', cycle_id='other', owner='other', task_id='guide', scope=['guide-memory'])
            self.plan()
        self.assertFalse(self.core.cycle('status', cycle_id='daily')['cycle']['lock']['os_lock_held_by_this_session'])

    def test_process_crash_releases_os_lock_but_retains_exact_reservation(self):
        code = """import sys,time
sys.path.insert(0, sys.argv[1])
from taskcarry.governance_cycle import GovernanceCycle
c=GovernanceCycle(sys.argv[2])
with c.cycle_session('daily','governor',['catalog-memory'],task_id='catalog'):
 print('held',flush=True)
 time.sleep(30)
"""
        process = subprocess.Popen([sys.executable, '-I', '-B', '-c', code,
                                    str(Path(__file__).resolve().parents[1]), str(self.project)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        try:
            self.assertEqual('held', process.stdout.readline().strip())
            self.assertCode('CYCLE_BUSY', self.core.cycle, 'resume', cycle_id='daily', owner='governor', scope=['catalog-memory'])
        finally:
            process.kill()
            process.communicate(timeout=10)
        self.assertCode('CYCLE_RESERVED', self.start, cycle_id='different')
        result = self.core.cycle('resume', cycle_id='daily', owner='governor', scope=['catalog-memory'])
        self.assertTrue(result['reused'])

    def test_exception_exits_session_without_fabricating_completion(self):
        with self.assertRaises(RuntimeError):
            with self.core.cycle_session('daily', 'governor', ['catalog-memory'], task_id='catalog'):
                self.plan()
                raise RuntimeError('synthetic interruption')
        result = self.core.cycle('resume', cycle_id='daily', owner='governor', scope=['catalog-memory'])
        self.assertEqual('pending', result['cycle']['effects']['write-guide']['outcome'])
        self.assertEqual('active', result['cycle']['state'])

    def test_effect_scope_terminal_receipt_and_request_identity_are_enforced(self):
        self.start()
        self.assertCode('CYCLE_SCOPE_MISMATCH', self.action, 'effect_plan', {'effect_id': 'bad', 'kind': 'write',
                         'resource': 'other', 'expected': 'outside declared scope'})
        self.assertCode('EFFECT_NOT_PLANNED', self.action, 'effect_result', {'effect_id': 'missing', 'outcome': 'confirmed',
                         'evidence_ref': 'synthetic:receipt', 'statement': 'No plan exists.'})
        self.plan()
        self.assertCode('IDEMPOTENCY_CONFLICT', self.action, 'finish', {'state': 'waiting', 'next_step': 'Await evidence.'})
        self.action('effect_result', {'effect_id': 'write-guide', 'outcome': 'rejected', 'evidence_ref': 'synthetic:check',
                                     'statement': 'Expected file not written.'}, 'verified')
        self.assertCode('EFFECT_TERMINAL', self.action, 'effect_result', {'effect_id': 'write-guide', 'outcome': 'confirmed',
                         'evidence_ref': 'synthetic:other', 'statement': 'Different receipt.'}, 'replacement')

    def test_receipts_and_event_rollback_together_on_failure(self):
        self.start()
        before = self.core.store.get('governance_cycles', 'daily')
        with mock.patch.object(self.core.store, 'event', side_effect=RuntimeError('synthetic disk error')):
            with self.assertRaises(RuntimeError):
                self.plan()
        self.assertEqual(before, self.core.store.get('governance_cycles', 'daily'))
        self.assertIsNone(self.core.store.get('cycle_requests', 'daily:one'))
        self.plan()

    def test_source_phases_require_exact_revision_and_consuming_target(self):
        self.start()
        data = {'source_id': 'chat:design', 'source_revision': 'turn-4', 'evidence_ref': 'host:review-4',
                'statement': 'Read and interpreted the selected message.'}
        self.assertCode('SOURCE_PHASE_MISSING', self.action, 'source', {**data, 'phase': 'understood'})
        self.action('source', {**data, 'phase': 'observed'}, 'observed')
        self.action('source', {**data, 'phase': 'understood'}, 'understood')
        self.action('source', {**data, 'phase': 'published', 'target': 'workbench:author'}, 'published')
        self.assertCode('SOURCE_PHASE_MISSING', self.action, 'source', {**data, 'phase': 'consumed', 'target': 'workbench:reviewer'}, 'wrong-target')
        consumed = self.action('source', {**data, 'phase': 'consumed', 'target': 'workbench:author'}, 'consumed')
        self.assertEqual(4, len(next(iter(consumed['cycle']['sources'].values()))['phases']))
        self.assertCode('SOURCE_PHASE_MISSING', self.action, 'source', {**data, 'source_revision': 'turn-5', 'phase': 'understood'}, 'new-revision')

    def test_health_freshness_is_not_a_permanent_green_status(self):
        self.start()
        timestamp = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        result = self.action('health', {'dimension': 'native-host', 'status': 'healthy', 'observed_at': timestamp,
                                      'freshness_seconds': 60, 'evidence_ref': 'host:previous-call'})
        self.assertEqual('unknown', result['cycle']['health']['native-host']['effective_status'])
        newer = datetime.now(timezone.utc).isoformat()
        self.action('health', {'dimension': 'native-host', 'status': 'healthy', 'observed_at': newer,
                              'freshness_seconds': 60, 'evidence_ref': 'host:current-call'}, 'newer')
        self.assertCode('HEALTH_STALE_WRITE', self.action, 'health', {'dimension': 'native-host', 'status': 'healthy',
                         'observed_at': timestamp, 'freshness_seconds': 60, 'evidence_ref': 'host:older'}, 'older')

    def test_questions_count_real_distinct_dates_across_cycles_and_stop_after_response(self):
        self.start()
        base = datetime.now(timezone.utc) - timedelta(days=2)
        for index, date in enumerate((base, base, base + timedelta(days=1))):
            data = {'question_id': 'confirm-destination', 'receipt_ref': 'host:delivery-' + str(index),
                    'delivered_at': date.isoformat(), 'utc_offset_minutes': 0, 'local_date': date.date().isoformat()}
            self.action('question_delivered', data, 'question-' + str(index))
        result = self.action('question_check', {'question_id': 'confirm-destination'})
        self.assertEqual(2, len(result['distinct_dates']))
        self.assertTrue(result['stop_proactive'])
        self.action('question_response', {'question_id': 'confirm-destination', 'receipt_ref': 'host:user-answer',
                                         'statement': 'Use the local destination.'}, 'response')
        self.action('finish', {'state': 'completed', 'next_step': 'Continue next scheduled cycle.'}, 'finish')
        self.start(cycle_id='next')
        result = self.action('question_check', {'question_id': 'confirm-destination'}, cycle_id='next')
        self.assertTrue(result['answered'])
        self.assertTrue(result['stop_proactive'])

    def test_delivery_dates_and_report_receipts_cannot_be_invented_or_overwritten(self):
        self.start()
        date = datetime.now(timezone.utc) - timedelta(minutes=2)
        data = {'report_id': 'daily-summary', 'receipt_ref': 'host:message-1', 'delivered_at': date.isoformat(),
                'utc_offset_minutes': 0, 'local_date': date.date().isoformat()}
        self.assertCode('DELIVERY_DATE_MISMATCH', self.action, 'report_delivered', {**data, 'local_date': '2000-01-01'})
        self.action('report_delivered', data, 'report')
        self.assertCode('REPORT_ALREADY_DELIVERED', self.action, 'report_delivered', {**data, 'receipt_ref': 'host:message-2'}, 'other')

    def test_actual_delivery_receipt_cannot_be_counted_again_on_another_date(self):
        self.start()
        date = datetime.now(timezone.utc) - timedelta(days=2)
        data = {'question_id': 'destination', 'receipt_ref': 'host:exact-message', 'delivered_at': date.isoformat(),
                'utc_offset_minutes': 0, 'local_date': date.date().isoformat()}
        self.action('question_delivered', data, 'first')
        later = date + timedelta(days=1)
        self.assertCode('RECEIPT_CONFLICT', self.action, 'question_delivered', {**data,
                         'delivered_at': later.isoformat(), 'local_date': later.date().isoformat()}, 'repeat')
        actual = self.action('question_check', {'question_id': 'destination'})
        self.assertEqual([date.date().isoformat()], actual['distinct_dates'])

    def test_total_scan_budget_and_wrong_continuation_remain_explicit(self):
        self.register()
        for index in range(5):
            (self.source / str(index)).write_text('synthetic', encoding='utf-8')
        start = self.scan(max_total_entries=3)['scan']
        self.assertCode('SCAN_CURSOR_INVALID', self.core.source_scan, 'page', 'files:catalog',
                        scan_id='inventory', cursor='inventory:0000009999')
        pages = self.pages(start['next_cursor'])
        self.assertEqual(3, sum(len(page['items']) for page in pages))
        self.assertEqual('incomplete', pages[-1]['state'])
        self.assertFalse(pages[-1]['enumeration_complete'])

    def test_future_cycle_schema_is_refused_without_writes(self):
        self.start()
        record = self.core.store.get('governance_cycles', 'daily')
        self.core.store.put('governance_cycles', 'daily', {**record, 'schema': 'taskcarry.cycle.v99'})
        events = self.core.store.events()
        self.assertCode('SCHEMA_VERSION_UNSUPPORTED', self.core.cycle, 'status', cycle_id='daily')
        self.assertCode('SCHEMA_VERSION_UNSUPPORTED', self.plan)
        self.assertEqual(events, self.core.store.events())

    def test_facts_cas_retains_history_and_separates_evidence_from_judgment(self):
        first = self.fact()['fact']
        self.assertTrue(self.fact()['reused'])
        self.assertNotEqual(first['statement'], first['judgment']['statement'])
        self.assertCode('FACT_CHANGED', self.fact, statement='Changed scope.')
        second = self.fact(source_revision='turn-2', statement='Changed scope.', expected_revision=1)['fact']
        self.assertEqual(2, second['revision'])
        history = self.core.facts('history', fact_id='scope', source_id='chat:catalog', limit=1)
        self.assertEqual([first], history['items'])
        self.assertIsNotNone(history['next_cursor'])
        next_page = self.core.facts('history', fact_id='scope', source_id='chat:catalog', limit=1, cursor=history['next_cursor'])
        self.assertEqual([second], next_page['items'])
        self.assertIsNone(next_page['next_cursor'])
        self.assertEqual(first['source_id'], second['source_id'])

    def test_facts_identity_is_source_qualified_and_relations_require_existing_fact(self):
        original = self.fact()['fact']
        other = self.fact(source_id='chat:other', task_id='guide')['fact']
        self.assertEqual(original['fact_id'], other['fact_id'])
        self.assertNotEqual(original['source_id'], other['source_id'])
        self.assertCode('RELATED_FACT_NOT_FOUND', self.fact, fact_id='missing-relation', relations=[
            {'source_id': 'chat:unknown', 'fact_id': 'scope', 'relation': 'implements'}])
        relation = self.fact(fact_id='plan', relations=[{'source_id': 'chat:catalog', 'fact_id': 'scope', 'relation': 'implements'}])
        self.assertEqual('scope', relation['fact']['relations'][0]['fact_id'])
        self.assertCode('FACT_ID_CONFLICT', self.fact, task_id='guide', expected_revision=1)

    def test_fact_read_paths_do_not_mutate_and_reject_future_record(self):
        value = self.fact()['fact']
        events = self.core.store.events()
        self.core.facts('get', fact_id='scope', source_id='chat:catalog')
        self.core.facts('list', source_id='chat:catalog', limit=1)
        self.core.facts('history', fact_id='scope', source_id='chat:catalog', limit=1)
        self.assertEqual(events, self.core.store.events())
        from taskcarry.governance_cycle import _hash
        self.core.store.put('governance_facts', _hash('chat:catalog') + ':scope', {**value, 'schema': 'taskcarry.fact.v2'})
        self.assertCode('SCHEMA_VERSION_UNSUPPORTED', self.core.facts, 'get', fact_id='scope', source_id='chat:catalog')

    def test_metadata_paging_is_durable_deterministic_and_source_zero_write(self):
        self.register()
        for index in range(7):
            (self.source / ('file-' + str(index) + '.txt')).write_text('synthetic ' + str(index), encoding='utf-8')
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.source.iterdir()}
        first = self.scan()['scan']
        page = self.core.source_scan('page', 'files:catalog', scan_id='inventory', cursor=first['next_cursor'])['page']
        events = self.core.store.events()
        repeated = GovernanceCycle(self.project).source_scan('page', 'files:catalog', scan_id='inventory', cursor=first['next_cursor'])
        self.assertTrue(repeated['reused'])
        self.assertEqual(page, repeated['page'])
        self.assertEqual(events, self.core.store.events())
        pages = [page] + self.pages(page['next_cursor'])
        names = [item['path'] for page in pages for item in page['items']]
        self.assertEqual(sorted(before), names)
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(pages[-1]['enumeration_complete'])
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.source.iterdir()})
        self.assertTrue(all(page['entries_processed'] <= 2 for page in pages))

    def test_metadata_scan_excludes_subtrees_without_opening_file_bodies(self):
        self.register(exclusions=['private'])
        for directory in ('private', '.git', 'allowed'):
            (self.source / directory).mkdir()
            (self.source / directory / 'data.txt').write_text('synthetic data', encoding='utf-8')
        start = self.scan()['scan']
        with mock.patch.object(Path, 'read_bytes', side_effect=AssertionError('No bodies may be read')):
            pages = self.pages(start['next_cursor'])
        names = [item['path'] for page in pages for item in page['items']]
        self.assertEqual(['allowed', 'allowed/data.txt'], names)
        self.assertTrue(pages[-1]['enumeration_complete'])

    def test_directory_change_invalidates_scan_without_missing_or_deletion_claim(self):
        self.register()
        for index in range(4):
            (self.source / str(index)).write_text('data', encoding='utf-8')
        start = self.scan()['scan']
        page = self.core.source_scan('page', 'files:catalog', scan_id='inventory', cursor=start['next_cursor'])['page']
        (self.source / 'late').write_text('new', encoding='utf-8')
        # Set an observably different watermark even on coarse timestamp filesystems.
        stamp = self.source.stat().st_mtime_ns + 1000000000
        os.utime(self.source, ns=(stamp, stamp))
        result = self.core.source_scan('page', 'files:catalog', scan_id='inventory', cursor=page['next_cursor'])['page']
        self.assertEqual('invalidated', result['state'])
        self.assertFalse(result['enumeration_complete'])
        self.assertEqual('unknown_due_to_incomplete_scan', result['missing_assessment'])
        self.assertIsNone(result['next_cursor'])

    def test_scan_budget_exhaustion_is_incomplete_not_restart_or_omission(self):
        self.register()
        for index in range(5):
            (self.source / str(index)).write_text('data', encoding='utf-8')
        pages = self.pages(self.scan(max_directory_entries=2)['scan']['next_cursor'])
        self.assertEqual('incomplete', pages[-1]['state'])
        self.assertEqual('directory_entry_budget', pages[-1]['errors'][0]['reason'])
        self.assertLessEqual(pages[0]['directory_entries_listed'], 3)
        self.assertFalse(pages[-1]['enumeration_complete'])

    def test_scan_registration_cas_overlap_and_future_schema(self):
        self.assertCode('SOURCE_OUTPUT_OVERLAP', self.core.source_scan, 'register', 'bad', root=str(self.root), authorization_ref='user:scope')
        self.register()
        self.assertCode('SOURCE_REGISTRY_CHANGED', self.register, exclusions=['new'])
        self.register(exclusions=['new'], expected_revision=1)
        self.scan()
        self.assertCode('SCAN_ID_CONFLICT', self.scan, max_entries=3)
        from taskcarry.governance_cycle import _hash
        key = _hash('files:catalog') + ':inventory'
        value = self.core.store.get('source_scans', key)
        self.core.store.put('source_scans', key, {**value, 'schema': 'taskcarry.source_scan.v2'})
        self.assertCode('SCHEMA_VERSION_UNSUPPORTED', self.core.source_scan, 'status', 'files:catalog', scan_id='inventory')

    def test_symlink_source_is_never_followed(self):
        self.register()
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'private.txt').write_text('synthetic excluded data', encoding='utf-8')
        try:
            (self.source / 'link').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not grant synthetic symlink creation.')
        pages = self.pages(self.scan()['scan']['next_cursor'])
        self.assertEqual([], [item for page in pages for item in page['items']])
        self.assertEqual('link', pages[-1]['skipped'][0]['reason'])

    def test_contracts_match_public_signatures(self):
        import inspect
        for name, schema in SCHEMAS.items():
            parameters = inspect.signature(getattr(GovernanceCycle, name)).parameters
            self.assertEqual(set(parameters) - {'self'}, set(schema['properties']))
            self.assertIn(name, DESCRIPTIONS)


if __name__ == '__main__':
    unittest.main()
