"""Synthetic evidence provenance and selected-scope closeout, with no host access."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from taskcarry.continuity import Continuity
from taskcarry.core import Core
from taskcarry.store import GovernanceError
from taskcarry.gitops import commit, out
from tests.test_integration import GitFixture


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='taskcarry-continuity-')
        self.project = Path(self.temp.name) / 'control'
        Core.initialize(self.project, 'Synthetic continuity')
        self.core = Continuity(self.project)
        self.store = self.core.store
        self.core.task('forms', state='active')
        self.core.task('guide', state='paused')
        for name in ('author', 'reviewer'):
            self.store.put('workspaces', name, {'name': name, 'identity': {'branch': name, 'gitdir': 'synthetic-' + name}})
        self.stage('draft')

    def tearDown(self):
        self.temp.cleanup()

    def stage(self, identity, **updates):
        record = {'stage_id': identity, 'task_id': 'forms', 'workspace': 'author',
                  'status': 'QUEUED', 'commit': 'synthetic-source', 'base': 'synthetic-base',
                  'paths': ['form.txt'], 'supersedes': [], **updates}
        self.store.put('stages', identity, record)
        return record

    def observe(self, **updates):
        return self.core.observe(**{'observation_id': 'host-review', 'workspace': 'author',
                                   'task_id': 'forms', 'source_ref': 'chat:synthetic:turn-1',
                                   'source_revision': 'host-fingerprint-1',
                                   'summary': 'The author linked this stage to the synthetic form task.',
                                   'relations': [{'kind': 'stage', 'id': 'draft'}], **updates})

    def assertCode(self, code, function, **kwargs):
        with self.assertRaises(GovernanceError) as failure:
            function(**kwargs)
        self.assertEqual(code, failure.exception.code)

    def test_observation_is_durable_and_identical_retry_writes_no_event(self):
        first = self.observe()
        before = self.store.events()
        repeated = self.observe()
        self.assertTrue(repeated['reused'])
        self.assertEqual(first['observation'], repeated['observation'])
        self.assertEqual(before, self.store.events())
        reopened = Continuity(self.project)
        self.assertEqual(first['observation'], reopened.store.get('observations', 'host-review'))
        self.assertEqual(1, len(reopened.store.list('observation_history')))
        self.assertEqual('QUEUED', self.store.get('stages', 'draft')['status'])
        self.assertIsNone(self.store.get('tasks', 'forms').get('business_acceptance'))

    def test_changed_observation_requires_cas_and_retains_prior_source(self):
        old = self.observe()['observation']
        self.assertCode('OBSERVATION_CHANGED', self.observe, source_revision='host-fingerprint-2')
        self.assertCode('OBSERVATION_CHANGED', self.observe, source_revision='host-fingerprint-2', expected_revision=2)
        current = self.observe(source_revision='host-fingerprint-2', expected_revision=1)['observation']
        self.assertEqual(2, current['revision'])
        self.assertEqual(old, self.store.get('observation_history', 'host-review:1'))
        self.assertEqual(current, self.store.get('observation_history', 'host-review:2'))

    def test_unknown_or_cross_task_workspace_relations_rejected(self):
        self.assertCode('TASK_NOT_FOUND', self.observe, task_id='unknown')
        self.assertCode('WORKSPACE_UNKNOWN', self.observe, workspace='unknown')
        self.assertCode('RELATION_SCOPE_MISMATCH', self.observe, task_id='guide')
        self.assertCode('RELATION_SCOPE_MISMATCH', self.observe, workspace='reviewer')
        self.assertCode('RELATED_RECORD_UNKNOWN', self.observe, relations=[{'kind': 'stage', 'id': 'unknown'}])
        self.assertEqual([], self.store.list('observations'))

    def test_observation_identity_cannot_move_to_another_source_or_task(self):
        self.observe()
        self.assertCode('OBSERVATION_ID_CONFLICT', self.observe, source_ref='chat:other:turn-1', expected_revision=1)
        self.assertCode('OBSERVATION_ID_CONFLICT', self.observe, task_id='guide', relations=[], expected_revision=1)

    def test_artifact_content_change_changes_evidence_even_if_host_revision_reused(self):
        self.store.put('artifacts', 'source-file', {'artifact_id': 'source-file', 'task_id': 'forms',
                                                 'sha256': 'old-content', 'size': 10, 'path': 'synthetic.dat'})
        links = [{'kind': 'artifact', 'id': 'source-file'}]
        old = self.observe(relations=links)['observation']
        changed = self.store.get('artifacts', 'source-file')
        changed['sha256'] = 'new-content'
        self.store.put('artifacts', 'source-file', changed)
        self.assertCode('OBSERVATION_CHANGED', self.observe, relations=links)
        new = self.observe(relations=links, expected_revision=1)['observation']
        self.assertNotEqual(old['relations'], new['relations'])
        self.assertEqual('host-fingerprint-1', new['source_revision'])

    def test_invalid_observation_fields_and_duplicate_relations_rejected(self):
        self.assertCode('INVALID_EVIDENCE', self.observe, source_ref=' ')
        self.assertCode('INVALID_EVIDENCE', self.observe, source_revision='')
        self.assertCode('INVALID_REVISION', self.observe, expected_revision=True)
        self.assertCode('INVALID_RELATION', self.observe, relations=[{'kind': 'file', 'id': 'draft'}])
        self.assertCode('INVALID_RELATION', self.observe, relations=[{'kind': 'stage', 'id': 'draft'}] * 2)
        self.assertCode('OBSERVATION_CHANGED', self.observe, expected_revision=1)

    def test_observation_event_failure_rolls_back_current_and_history(self):
        old = self.observe()['observation']
        before = self.store.events()
        with mock.patch.object(self.store, 'event', side_effect=OSError('synthetic event failure')):
            with self.assertRaises(OSError):
                self.observe(source_revision='new', expected_revision=1)
        reopened = Continuity(self.project)
        self.assertEqual(old, reopened.store.get('observations', 'host-review'))
        self.assertEqual([old], reopened.store.list('observation_history'))
        self.assertEqual(before, reopened.store.events())

    def test_run_selection_cannot_change_or_claim_missing_records(self):
        first = self.core.run('morning', stage_ids=['draft'])
        before = self.store.events()
        self.assertTrue(self.core.run('morning', stage_ids=['draft'])['reused'])
        self.assertEqual(before, self.store.events())
        self.assertCode('RUN_ID_CONFLICT', self.core.run, run_id='morning', stage_ids=[])
        self.assertCode('RUN_RECORD_UNKNOWN', self.core.run, run_id='missing', stage_ids=['missing'])
        self.assertCode('RUN_SELECTION_FROZEN', self.core.run, run_id='morning', mode='finish', stage_ids=[])
        self.assertEqual(first['run'], self.store.get('runs', 'morning'))

    def test_pending_work_blocks_only_selected_closeout_and_no_repeat_event(self):
        self.core.run('morning', stage_ids=['draft'])
        result = self.core.run('morning', mode='finish')
        self.assertEqual('WAITING', result['run']['state'])
        self.assertFalse(result['inspection']['selected_complete'])
        self.assertEqual([{'kind': 'stage', 'id': 'draft', 'reason': 'QUEUED'}], result['inspection']['pending'])
        before = self.store.events()
        self.assertTrue(self.core.run('morning', mode='finish')['reused'])
        self.assertEqual(before, self.store.events())
        self.assertEqual('active', self.store.get('tasks', 'forms')['state'])
        self.assertEqual('paused', self.store.get('tasks', 'guide')['state'])

    def test_finished_selection_does_not_imply_all_project_work_complete(self):
        self.stage('unselected')
        self.core.run('morning', stage_ids=['draft'])
        self.stage('draft', status='COMMITTED', accepted_commit='synthetic-accepted')
        result = self.core.run('morning', mode='finish')
        self.assertEqual('COMPLETED', result['run']['state'])
        self.assertTrue(result['inspection']['selected_complete'])
        self.assertIsNone(result['inspection']['project_complete'])
        self.assertFalse(result['inspection']['effects_executed'])
        self.assertEqual('selected_records', result['inspection']['scope'])
        self.assertEqual('QUEUED', self.store.get('stages', 'unselected')['status'])
        self.assertTrue(self.core.run('morning', mode='finish')['reused'])

    def test_changed_observation_is_visible_without_replaying_completed_work(self):
        self.observe()
        self.core.run('morning', stage_ids=['draft'], observation_ids=['host-review'])
        self.observe(source_revision='next-turn', expected_revision=1)
        self.stage('draft', status='COMMITTED', accepted_commit='synthetic-accepted')
        result = self.core.run('morning', mode='finish')
        self.assertTrue(result['inspection']['selected_complete'])
        self.assertEqual(['host-review'], result['inspection']['changed_observations'])
        self.assertFalse(result['inspection']['effects_executed'])

    def test_inspect_is_readonly_and_missing_run_is_not_created(self):
        self.assertCode('RUN_UNKNOWN', self.core.run, run_id='missing', mode='inspect')
        self.assertEqual([], self.store.list('runs'))
        self.core.run('morning', stage_ids=['draft'])
        before_records, before_events = self.store.list('runs'), self.store.events()
        with mock.patch.object(self.store, 'put', side_effect=AssertionError('inspect wrote records')):
            self.core.run('morning', mode='inspect')
        self.assertEqual(before_records, self.store.list('runs'))
        self.assertEqual(before_events, self.store.events())

    def test_run_start_and_finish_are_atomic_when_event_write_fails(self):
        with mock.patch.object(self.store, 'event', side_effect=OSError('synthetic failure')):
            with self.assertRaises(OSError):
                self.core.run('morning', stage_ids=['draft'])
        self.assertIsNone(Continuity(self.project).store.get('runs', 'morning'))
        initial = self.core.run('morning', stage_ids=['draft'])['run']
        self.stage('draft', status='COMMITTED', accepted_commit='synthetic-accepted')
        with mock.patch.object(self.store, 'event', side_effect=OSError('synthetic failure')):
            with self.assertRaises(OSError):
                self.core.run('morning', mode='finish')
        self.assertEqual(initial, Continuity(self.project).store.get('runs', 'morning'))
        self.assertTrue(self.core.run('morning', mode='finish')['inspection']['selected_complete'])

    def test_operation_completion_requires_matching_receipt_not_status_only(self):
        self.store.put('operations', 'receive', {'operation_id': 'receive', 'kind': 'reconcile',
                                               'task_id': 'forms', 'stage_id': 'draft',
                                               'status': 'COMPLETED', 'candidate': 'synthetic-accepted'})
        self.core.run('morning', operation_ids=['receive'])
        result = self.core.run('morning', mode='finish')
        self.assertEqual('RECEIPT_INCOMPLETE', result['inspection']['pending'][0]['reason'])
        self.stage('draft', status='COMMITTED', accepted_commit='different-commit')
        self.assertFalse(self.core.run('morning', mode='finish')['inspection']['selected_complete'])
        self.stage('draft', status='COMMITTED', accepted_commit='synthetic-accepted')
        self.assertTrue(self.core.run('morning', mode='finish')['inspection']['selected_complete'])

    def test_restore_run_requires_matching_durable_receipt(self):
        source = self.project.parent / 'plain-documents'
        source.mkdir()
        (source / 'notes.md').write_text('Synthetic existing project\n', encoding='utf-8')
        checkpoint = self.core.checkpoint('forms', str(source), ['notes.md'], 'Continue the existing project')
        target = self.project.parent / 'restored-documents'
        result = self.core.restore(checkpoint['checkpoint_id'], str(target))
        identity = result['operation_id']
        self.core.run('restore-round', operation_ids=[identity])
        receipt = self.store.get('restore_receipts', identity)
        operation = self.store.get('operations', identity)
        for change in ({'verified': False}, {'destination': 'different-target'},
                       {'effect_sha256': 'different-effect'}, {'checkpoint_id': 'different-checkpoint'}):
            with self.subTest(change=change):
                self.store.put('restore_receipts', identity, {**receipt, **change})
                inspected = self.core.run('restore-round', mode='inspect')['inspection']
                self.assertFalse(inspected['selected_complete'])
                self.assertEqual('RECEIPT_INCOMPLETE', inspected['pending'][0]['reason'])
        self.store.put('restore_receipts', identity, receipt)
        self.store.put('operations', identity, {**operation, 'restore_protocol': 99})
        self.assertFalse(self.core.run('restore-round', mode='inspect')['inspection']['selected_complete'])
        self.store.put('operations', identity, operation)
        # A later edit is not an unfinished historical operation. run only
        # checks durable receipts and must not rewrite the target or source.
        (target / 'notes.md').write_text('Later user work\n', encoding='utf-8')
        finished = self.core.run('restore-round', mode='finish')
        self.assertEqual('COMPLETED', finished['run']['state'])
        self.assertFalse(finished['inspection']['effects_executed'])
        self.assertEqual('Later user work\n', (target / 'notes.md').read_text(encoding='utf-8'))
        self.assertEqual('Synthetic existing project\n', (source / 'notes.md').read_text(encoding='utf-8'))

    def test_transitive_supersession_resolves_history_with_real_successor_receipt(self):
        self.stage('draft', status='SUPERSEDED', successor='release')
        self.stage('revision', status='SUPERSEDED', successor='release', supersedes=['draft'])
        self.stage('release', status='QUEUED', supersedes=['revision'])
        self.core.run('morning', stage_ids=['draft', 'revision'])
        self.assertFalse(self.core.run('morning', mode='finish')['inspection']['selected_complete'])
        self.stage('release', status='COMMITTED', accepted_commit='synthetic-accepted', supersedes=['revision'])
        self.assertTrue(self.core.run('morning', mode='finish')['inspection']['selected_complete'])
        self.stage('release', status='COMMITTED', accepted_commit='synthetic-accepted', supersedes=[])
        self.assertFalse(self.core.run('morning', mode='inspect')['inspection']['selected_complete'])

    def test_empty_selection_is_explicit_and_does_not_complete_active_task(self):
        self.core.run('observation-only', note='No deliveries selected this round.')
        result = self.core.run('observation-only', mode='finish')
        self.assertTrue(result['inspection']['selected_complete'])
        self.assertIsNone(result['inspection']['project_complete'])
        self.assertEqual('active', self.store.get('tasks', 'forms')['state'])

    def test_legacy_partial_stage_receipt_does_not_hide_unfinished_operation(self):
        self.stage('draft', status='COMMITTED', accepted_commit='accepted', operation_id='receive')
        self.store.put('operations', 'receive', {'operation_id': 'receive', 'kind': 'reconcile',
                                               'stage_id': 'draft', 'task_id': 'forms',
                                               'candidate': 'accepted', 'status': 'EFFECT_APPLIED'})
        self.core.run('legacy', stage_ids=['draft'])
        result = self.core.run('legacy', mode='finish')
        self.assertEqual('WAITING', result['run']['state'])
        self.assertEqual('RECEIPT_INCOMPLETE', result['inspection']['pending'][0]['reason'])

    def test_adoption_replacement_requires_same_scope_and_reciprocal_link(self):
        old = {'operation_id': 'old-preparation', 'kind': 'adopt', 'workspace': 'author',
               'baseline': 'baseline', 'status': 'SUPERSEDED', 'effect_state': 'NOT_APPLIED',
               'resolved_by_operation': 'new-adoption', 'resolved_by_plan': 'new-plan'}
        successor = {'operation_id': 'new-adoption', 'kind': 'adopt', 'workspace': 'author',
                     'baseline': 'baseline', 'plan_id': 'new-plan', 'status': 'COMPLETED',
                     'effect_state': 'VERIFIED', 'candidate': 'accepted',
                     'resolves_preparation_failures': ['old-preparation']}
        self.store.put('operations', 'old-preparation', old)
        self.store.put('operations', 'new-adoption', successor)
        self.core.run('adopt', operation_ids=['old-preparation'])
        self.assertTrue(self.core.run('adopt', mode='finish')['inspection']['selected_complete'])
        for changes in ({'workspace': 'reviewer'}, {'baseline': 'other-baseline'},
                        {'plan_id': 'other-plan'}, {'resolves_preparation_failures': []},
                        {'status': 'EFFECT_APPLIED'}, {'effect_state': 'NOT_APPLIED'}):
            with self.subTest(changes=changes):
                self.store.put('operations', 'new-adoption', {**successor, **changes})
                self.assertFalse(self.core.run('adopt', mode='inspect')['inspection']['selected_complete'])
        self.store.put('operations', 'new-adoption', successor)
        self.store.put('operations', 'old-preparation', {**old, 'candidate': 'unexpected-effect'})
        self.assertFalse(self.core.run('adopt', mode='inspect')['inspection']['selected_complete'])

    def test_adoption_replacement_cycle_is_not_a_completion(self):
        first = {'operation_id': 'first', 'kind': 'adopt', 'workspace': 'author', 'baseline': 'baseline',
                 'status': 'SUPERSEDED', 'effect_state': 'NOT_APPLIED', 'plan_id': 'plan-first',
                 'resolved_by_operation': 'second', 'resolved_by_plan': 'plan-second',
                 'resolves_preparation_failures': ['second']}
        second = {**first, 'operation_id': 'second', 'plan_id': 'plan-second',
                  'resolved_by_operation': 'first', 'resolved_by_plan': 'plan-first',
                  'resolves_preparation_failures': ['first']}
        self.store.put('operations', 'first', first)
        self.store.put('operations', 'second', second)
        self.core.run('cyclic', operation_ids=['first'])
        result = self.core.run('cyclic', mode='finish')
        self.assertFalse(result['inspection']['selected_complete'])
        self.assertEqual('SUPERSESSION_CYCLE', result['inspection']['pending'][0]['reason'])


class ContinuityGitTests(GitFixture):
    def test_run_closes_after_successor_adoption_resolves_old_preparation(self):
        continuity = Continuity(self.control)
        old_plan = self.engine.adopt('worker', 'baseline')['plan']['plan_id']
        with mock.patch.object(self.engine, '_prepare_adoption',
                               side_effect=GovernanceError('WIP_CONFLICT', 'Synthetic preparation failure')):
            with self.assertRaises(GovernanceError):
                self.engine.adopt('worker', 'baseline', True, old_plan)
        old = self.engine.store.list('operations')[0]
        continuity.run('old-adoption-round', operation_ids=[old['operation_id']])
        self.assertFalse(continuity.run('old-adoption-round', mode='finish')['inspection']['selected_complete'])
        self.write_commit(self.base, {'rules.txt': 'accepted revised rules\n'})
        next_plan = self.engine.adopt('worker', 'baseline')['plan']['plan_id']
        self.engine.adopt('worker', 'baseline', True, next_plan)
        head = commit(self.worker, 'HEAD')
        self.assertEqual('SUPERSEDED', self.engine.store.get('operations', old['operation_id'])['status'])
        completed = continuity.run('old-adoption-round', mode='finish')
        self.assertTrue(completed['inspection']['selected_complete'])
        self.assertEqual('COMPLETED', completed['run']['state'])
        self.assertEqual(head, commit(self.worker, 'HEAD'))

    def test_received_operation_stays_complete_after_cumulative_stage(self):
        first = self.delivery(stage_id='v1')
        self.execute()
        old_operation = self.engine.store.get('stages', first['stage_id'])['operation_id']
        continuity = Continuity(self.control)
        continuity.run('first-round', stage_ids=['v1'], operation_ids=[old_operation])
        self.assertTrue(continuity.run('first-round', mode='finish')['inspection']['selected_complete'])
        self.delivery({'form.txt': 'name\nstatus\nreviewer\nresolution\n'}, stage_id='v2',
                      relation='cumulative', supersedes=['v1'])
        self.execute()
        self.assertEqual('SUPERSEDED', self.engine.store.get('stages', 'v1')['status'])
        head = commit(self.base, 'HEAD')
        result = continuity.run('first-round', mode='finish')
        self.assertTrue(result['inspection']['selected_complete'])
        self.assertEqual('COMPLETED', result['run']['state'])
        self.assertEqual(head, commit(self.base, 'HEAD'))

    def test_receipt_interruption_run_closeout_and_experience_recovery_preserve_effect(self):
        stage = self.delivery(stage_id='delivery')
        continuity = Continuity(self.control)
        observation = dict(observation_id='author-turn', workspace='worker', task_id='forms',
                           source_ref='chat:synthetic:author', source_revision='turn-1',
                           summary='Author identifies this committed form revision as the current delivery.',
                           relations=[{'kind': 'stage', 'id': stage['stage_id']}])
        continuity.observe(**observation)
        continuity.run('receive-round', stage_ids=[stage['stage_id']], observation_ids=['author-turn'])
        pid = self.plan()
        (self.control / '.taskcarry' / 'SYNTHETIC_TEST_ONLY').write_text('synthetic', encoding='utf-8')
        with mock.patch.dict(os.environ, {'TASKCARRY_TEST_FAULTS': '1'}):
            with self.assertRaises(GovernanceError) as interrupted:
                self.execute(pid, fault='after_effect')
        self.assertEqual('INJECTED_INTERRUPTION', interrupted.exception.code)
        original_head = commit(self.base, 'HEAD')
        original_content = (self.base / 'form.txt').read_bytes()
        before_resume = continuity.run('receive-round', mode='finish')
        self.assertFalse(before_resume['inspection']['selected_complete'])
        operation_id = self.engine.store.list('operations')[0]['operation_id']
        continuity.run('resume-round', stage_ids=[stage['stage_id']], operation_ids=[operation_id],
                       observation_ids=['author-turn'])
        observation['source_revision'] = 'turn-2'
        continuity.observe(**observation, expected_revision=1)
        restored = self.execute(pid)
        self.assertTrue(restored['results'][0]['recovered'])
        after_resume = continuity.run('resume-round', mode='finish')
        self.assertTrue(after_resume['inspection']['selected_complete'])
        self.assertEqual(['author-turn'], after_resume['inspection']['changed_observations'])
        self.assertEqual(original_head, commit(self.base, 'HEAD'))
        self.assertEqual(original_content, (self.base / 'form.txt').read_bytes())
        self.assertEqual('2', out(self.base, 'rev-list', '--count', 'HEAD'))
        self.assertTrue(continuity.run('receive-round', mode='finish')['inspection']['selected_complete'])
        self.assertEqual(1, sum(event['kind'] == 'stage_received' for event in self.engine.store.events()))
        self.assertIsNone(after_resume['inspection']['project_complete'])


if __name__ == '__main__':
    unittest.main()
