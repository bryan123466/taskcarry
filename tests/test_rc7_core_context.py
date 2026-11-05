"""Synthetic state identification, scoped context and plain-source continuity."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock

from taskcarry.core import Core, git
from taskcarry.continuity import Continuity
from taskcarry.store import GovernanceError


class CoreContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='taskcarry-context-')
        self.root = Path(self.temp.name)
        self.project = self.root / 'governance'

    def tearDown(self):
        self.temp.cleanup()

    def start(self):
        Core.initialize(self.project, 'Synthetic project')
        self.core = Continuity(self.project)
        self.core.task('draft', state='paused')
        return self.core

    def assertCode(self, code, fn, *args, **kwargs):
        with self.assertRaises(GovernanceError) as result:
            fn(*args, **kwargs)
        self.assertEqual(code, result.exception.code)

    def bytes(self):
        return {str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.root.rglob('*') if path.is_file()}

    def durable_bytes(self):
        # Normal SQLite read transactions may create coordination sidecars;
        # they must not alter durable state or records. Identification itself
        # is tested above against every byte, including absent sidecars.
        return {key: value for key, value in self.bytes().items()
                if not key.endswith(('state.sqlite3-wal', 'state.sqlite3-shm'))}

    def test_identify_missing_and_ordinary_directory_never_initialize(self):
        self.assertEqual('absent', Core.identify(self.project)['state'])
        self.assertFalse(self.project.exists())
        self.project.mkdir()
        (self.project / 'notes.txt').write_text('Synthetic old notes', encoding='utf-8')
        before = self.bytes()
        self.assertEqual('uninitialized', Core.identify(self.project)['state'])
        self.assertEqual(before, self.bytes())

    def test_foreign_database_rejected_without_journal_schema_or_guard_changes(self):
        metadata = self.project / '.taskcarry'
        metadata.mkdir(parents=True)
        with closing(sqlite3.connect(metadata / 'state.sqlite3')) as db:
            db.execute('CREATE TABLE foreign_data(value TEXT)')
        before = self.bytes()
        self.assertEqual('unknown', Core.identify(self.project)['state'])
        self.assertCode('STATE_UNRECOGNIZED', Core.initialize, self.project)
        self.assertEqual(before, self.bytes())
        self.assertFalse((metadata / 'mutation.lock').exists())

    def test_future_config_and_future_index_refuse_without_effects(self):
        self.start()
        config = self.core.store.get('config', 'project')
        self.core.store.put('config', 'project', dict(config, schema_version=999))
        before = self.bytes()
        self.assertEqual('unsupported', Core.identify(self.project)['state'])
        self.assertCode('SCHEMA_VERSION_UNSUPPORTED', Core.initialize, self.project)
        self.assertEqual(before, self.bytes())
        self.core.store.put('config', 'project', config)
        with closing(sqlite3.connect(self.core.store.path)) as db:
            with db:
                db.execute('UPDATE store_schema SET version=999')
        before = self.bytes()
        self.assertCode('SCHEMA_VERSION_UNSUPPORTED', Core.initialize, self.project)
        self.assertEqual(before, self.bytes())

    def test_corrupt_database_and_unclaimed_metadata_are_preserved(self):
        metadata = self.project / '.taskcarry'
        metadata.mkdir(parents=True)
        (metadata / 'other-tool.json').write_text('{}', encoding='utf-8')
        before = self.bytes()
        self.assertCode('STATE_UNRECOGNIZED', Core.initialize, self.project)
        self.assertEqual(before, self.bytes())
        (metadata / 'state.sqlite3').write_bytes(b'not a database')
        before = self.bytes()
        self.assertEqual('corrupt', Core.identify(self.project)['state'])
        self.assertCode('STATE_CORRUPT', Core.initialize, self.project)
        self.assertEqual(before, self.bytes())

    def test_live_wal_not_ignored_or_checkpointed_by_identify(self):
        self.start()
        with closing(sqlite3.connect(self.core.store.path)) as db:
            db.execute('PRAGMA wal_autocheckpoint=0')
            db.execute("UPDATE records SET value=? WHERE collection='config'", (json.dumps({'schema_version': 999}),))
            db.commit()
            before = self.bytes()
            result = Core.identify(self.project)
            self.assertEqual('busy', result['state'])
            self.assertCode('BUSY', Core.initialize, self.project)
            self.assertEqual(before, self.bytes())

    def test_initialization_rechecks_inside_guard(self):
        self.start()
        from taskcarry.identification import identify
        calls = []
        def changed(project, initializing=False):
            calls.append(initializing)
            result = identify(project, initializing)
            return dict(result, state='unsupported') if initializing else result
        before = self.bytes()
        with mock.patch('taskcarry.identification.identify', side_effect=changed):
            self.assertCode('SCHEMA_VERSION_UNSUPPORTED', Core.initialize, self.project)
        self.assertEqual([False, True], calls)
        self.assertEqual(before, self.bytes())

    def test_initialization_failure_can_resume_only_its_recognized_format(self):
        from taskcarry.store import Store
        with mock.patch.object(Store, 'event', side_effect=OSError('synthetic receipt interruption')):
            with self.assertRaises(OSError):
                Core.initialize(self.project)
        self.assertEqual('incomplete', Core.identify(self.project)['state'])
        self.assertIsNone(Store(self.project).get('config', 'project'))
        Core.initialize(self.project)
        self.assertEqual('compatible', Core.identify(self.project)['state'])
        events = Store(self.project).events()
        self.assertEqual(1, len(events))
        Core.initialize(self.project)
        self.assertEqual(events, Store(self.project).events())

    def test_publication_rechecks_a_changed_target_before_writing(self):
        self.start()
        from taskcarry.store import Store
        changed = []
        def swap_after_open(*args, **kwargs):
            store = Store(*args, **kwargs)
            store.put('config', 'project', {'schema_version': 999})
            changed.append(self.bytes())
            return store
        with mock.patch('taskcarry.core.Store', side_effect=swap_after_open):
            self.assertCode('SCHEMA_VERSION_UNSUPPORTED', Core.initialize, self.project)
        self.assertEqual(changed[0], self.bytes())

    def test_context_preserves_pause_checkpoint_decision_and_source(self):
        self.start()
        folder = self.root / 'ordinary'
        folder.mkdir()
        # A nested synthetic repository isolates this test even when the test
        # temp directory itself is inside a checkout.
        git(folder, 'init', '--quiet')
        (folder / 'draft.txt').write_text('Synthetic draft', encoding='utf-8')
        cp = self.core.checkpoint('draft', folder, ['draft.txt'], 'Continue the second section', 'Keep the old goal', paused=True)
        self.core.observe('notes', None, 'draft', 'file:draft.txt', 'v1', 'A reviewed source')
        before = self.durable_bytes()
        result = self.core.context('draft')
        self.assertEqual('paused', result['task']['state'])
        self.assertEqual(cp['checkpoint_id'], result['latest_checkpoint']['checkpoint_id'])
        self.assertEqual('Keep the old goal', result['latest_checkpoint']['decision'])
        self.assertEqual('Continue the second section', result['task']['next_step'])
        self.assertEqual('observations', result['items'][0]['collection'])
        self.assertEqual(self.core.status()['source'], result['source'])
        self.assertEqual(self.core.agenda()['source'], result['source'])
        self.assertEqual(before, self.durable_bytes())
        self.assertEqual([], self.core.agenda()['items'])
        self.assertFalse(result['effects_executed'])

    def test_context_pagination_stale_and_unrelated_history_independence(self):
        self.start()
        with self.core.store.transaction():
            for index in range(5):
                self.core.store.put('stages', 'draft-' + str(index), {'task_id': 'draft', 'stage_id': 'draft-' + str(index), 'status': 'COMMITTED'})
        first = self.core.context('draft', limit=2)
        self.assertEqual(5, first['total'])
        with self.core.store.transaction():
            for index in range(1500):
                self.core.store.put('stages', 'other-' + str(index), {'task_id': 'other', 'stage_id': 'other-' + str(index), 'status': 'COMMITTED', 'summary': 'unrelated'})
        with mock.patch('taskcarry.task_context.json.loads', wraps=json.loads) as loads:
            second = self.core.context('draft', limit=2, cursor=first['next_cursor'])
        self.assertLessEqual(loads.call_count, 5)
        self.assertEqual(first['fingerprint'], second['fingerprint'])
        self.assertLessEqual(second['storage']['loaded_records'], 4)
        self.assertEqual(['draft-2', 'draft-3'], [item['local_id'] for item in second['items']])
        third = self.core.context('draft', limit=2, cursor=second['next_cursor'])
        self.assertIsNone(third['next_cursor'])
        self.core.store.put('stages', 'draft-4', {'task_id': 'draft', 'stage_id': 'draft-4', 'status': 'CONFLICT'})
        self.assertCode('CONTEXT_CURSOR_STALE', self.core.context, 'draft', cursor=first['next_cursor'])

    def test_identical_ids_in_two_sources_have_different_context_and_cursors(self):
        self.start()
        for name in ('one', 'two'):
            self.core.observe(name, None, 'draft', 'source:' + name, '1', name)
        other = self.root / 'second'
        Core.initialize(other)
        second = Core(other)
        second.task('draft')
        first = self.core.context('draft', limit=1)
        self.assertNotEqual(first['source']['source_id'], second.context('draft')['source']['source_id'])
        self.assertCode('CONTEXT_CURSOR_INVALID', second.context, 'draft', cursor=first['next_cursor'])

    def test_large_payload_omission_and_explicit_issue_change_are_visible(self):
        self.start()
        self.core.store.put('issues', 'large', {'issue_id': 'large', 'summary': 'x' * 50000})
        self.core.store.put('issues', 'scoped', {'issue_id': 'scoped', 'task_id': 'draft', 'summary': 'x' * 50000})
        first = self.core.context('draft', issue_ids=['large', 'missing'])
        self.assertTrue(first['selected_references'][0]['record']['payload_omitted'])
        self.assertEqual(3, len(first['missing']))
        self.core.store.put('issues', 'large', {'issue_id': 'large', 'summary': 'y' * 50000})
        second = self.core.context('draft', issue_ids=['large', 'missing'], previous_fingerprint=first['fingerprint'])
        self.assertTrue(second['changed'])
        self.assertLess(len(json.dumps(second)), 12000)

    def test_legacy_context_requests_explicit_upgrade_without_read_migration(self):
        self.start()
        with closing(sqlite3.connect(self.core.store.path)) as db:
            db.execute('DROP INDEX current_records_task')
        before = self.durable_bytes()
        self.assertCode('CONTEXT_INDEX_REQUIRED', self.core.context, 'draft')
        self.assertEqual(before, self.durable_bytes())
        self.assertTrue(self.core.upgrade()['upgraded'])
        self.assertEqual('draft', self.core.context('draft')['task']['task_id'])
        self.assertFalse(self.core.upgrade()['upgraded'])

    def test_old_current_index_reports_missing_context_without_changing_legacy_flag(self):
        self.start()
        with closing(sqlite3.connect(self.core.store.path)) as db:
            db.execute('DROP TABLE context_schema')
        before = self.durable_bytes()
        storage = self.core.status()['storage']
        self.assertFalse(storage['upgrade_required'])
        self.assertFalse(storage['context_ready'])
        self.assertTrue(storage['context_upgrade_required'])
        self.assertEqual(before, self.durable_bytes())
        self.core.upgrade()
        storage = self.core.status()['storage']
        self.assertTrue(storage['context_ready'])
        self.assertFalse(storage['context_upgrade_required'])

    def test_plain_observation_keeps_cas_and_git_workspace_constraints(self):
        self.start()
        first = self.core.observe('source', None, 'draft', 'file:notes.txt', '1', 'First')
        self.assertIsNone(first['observation']['workspace_identity'])
        self.assertTrue(self.core.observe('source', None, 'draft', 'file:notes.txt', '1', 'First')['reused'])
        self.assertCode('OBSERVATION_CHANGED', self.core.observe, 'source', None, 'draft', 'file:notes.txt', '2', 'Second')
        second = self.core.observe('source', None, 'draft', 'file:notes.txt', '2', 'Second', expected_revision=1)
        self.assertEqual(2, second['observation']['revision'])
        self.assertCode('WORKSPACE_UNKNOWN', self.core.observe, 'other', 'unregistered', 'draft', 'file:notes.txt', '1', 'Other')
        self.assertCode('RELATION_SCOPE_MISMATCH', self.core.observe, 'stage', None, 'draft', 'file:notes.txt', '1', 'Other', relations=[{'kind': 'stage', 'id': 'anything'}])
        self.assertEqual([], self.core.store.list('workspaces'))


if __name__ == '__main__':
    unittest.main()
