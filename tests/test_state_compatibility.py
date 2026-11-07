"""Legacy database compatibility and whole-project recovery outcomes."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock

from taskcarry.core import Core
from taskcarry.project_recovery import ProjectRecovery, _state_rows
from taskcarry.recovery_git import git
from taskcarry.store import GovernanceError


class StateCompatibilityTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / 'validation' / 'local'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='legacy-state-', dir=parent)
        self.root = Path(self.temp.name)
        self.control = self.root / 'control'
        metadata = self.control / '.taskcarry'
        metadata.mkdir(parents=True)
        self.database = metadata / 'state.sqlite3'
        # Original schema-1 layout, with SQLite's default application_id=0.
        # Final package validation also creates states using the actual rc5/rc6 wheels.
        with closing(sqlite3.connect(self.database)) as db, db:
            db.executescript('''
                CREATE TABLE records (collection TEXT NOT NULL, key TEXT NOT NULL,
                    value TEXT NOT NULL, PRIMARY KEY(collection,key));
                CREATE TABLE events (sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);
            ''')
            db.execute('INSERT INTO records VALUES(?,?,?)', ('config', 'project', json.dumps(
                {'name': 'Synthetic USB acquisition tool', 'schema_version': 1})))
        self.core = Core(self.control)
        self.core.task('protocol', 'Specify sample frames')
        self.core.task('firmware', 'Wait for a synthetic board parameter', state='paused')
        self.core.task('decoder', 'Complete decoder checks', state='complete')
        self.workspace = self.root / 'protocol'
        self.workspace.mkdir()
        git(self.workspace, 'init', '--quiet', '-b', 'synthetic')
        git(self.workspace, 'config', 'user.name', 'Synthetic Author')
        git(self.workspace, 'config', 'user.email', 'author@example.invalid')
        (self.workspace / 'PROTOCOL.md').write_bytes(b'SAMPLE,timestamp,value\n')
        git(self.workspace, 'add', '--', 'PROTOCOL.md')
        git(self.workspace, 'commit', '-qm', 'Specify synthetic protocol')
        self.checkpoint = self.core.checkpoint('protocol', str(self.workspace), ['PROTOCOL.md'],
                                               'Review frame specification')
        self.core.store.put('decisions', 'frame-format',
                            {'task_id': 'protocol', 'decision_id': 'frame-format', 'format': 'text-v1'})
        self.recovery = ProjectRecovery(self.control)

    def tearDown(self):
        self.temp.cleanup()

    def application_id(self):
        with closing(sqlite3.connect(self.database.as_uri() + '?mode=ro', uri=True)) as db:
            return db.execute('PRAGMA application_id').fetchone()[0]

    def plan(self):
        return self.recovery.recovery('backup_plan', destination=str(self.root / 'media'),
            workspaces=[{'name': 'protocol', 'path': str(self.workspace), 'kind': 'git',
                         'paths': ['PROTOCOL.md']}])

    def assert_code(self, code, callback, *args, **kwargs):
        with self.assertRaises(GovernanceError) as error:
            callback(*args, **kwargs)
        self.assertEqual(code, error.exception.code)

    def test_legacy_backup_verify_restore_preserves_history_without_header_migration(self):
        source = self.core.source()
        original_records = self.core.store.snapshot(['tasks', 'decisions'])
        original_events = self.core.store.events()
        plan = self.plan()
        original_bytes = self.database.read_bytes()
        backup = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertTrue(backup['verification']['verified'])
        self.assertTrue(backup['verification']['complete_scope'])
        self.assertEqual(original_bytes, self.database.read_bytes())
        self.assertEqual(0, self.application_id())
        controller = ProjectRecovery(self.root / 'controller')
        restore_plan = controller.recovery('restore_plan', manifest=backup['manifest'],
            expected_sha256=backup['manifest_sha256'], destination=str(self.root / 'restored'))
        restored = controller.recovery('restore_execute', plan_id=restore_plan['plan_id'])
        core = Core(restored['effect']['control'])
        self.assertEqual(original_records, core.store.snapshot(['tasks', 'decisions']))
        checkpoint = core.store.get('checkpoints', self.checkpoint['checkpoint_id'])
        self.assertEqual(self.checkpoint['files'], checkpoint['files'])
        self.assertEqual(self.checkpoint['task_id'], checkpoint['task_id'])
        self.assertEqual(original_events, core.store.events()[:len(original_events)])
        self.assertIn(source['source_id'], core.source()['aliases'])
        self.assertEqual('standby', core.source()['writer_state'])
        self.assertEqual('paused', core.store.get('tasks', 'firmware')['state'])
        self.assertEqual('complete', core.store.get('tasks', 'decoder')['state'])
        self.assertEqual(b'SAMPLE,timestamp,value\n',
                         (Path(restored['effect']['control']).parent / 'workspaces/protocol/PROTOCOL.md').read_bytes())
        self.assert_code('RECOVERY_STANDBY', core.task, 'unexpected')
        replay = controller.recovery('restore_execute', plan_id=restore_plan['plan_id'])
        self.assertEqual(restored['effect'], replay['effect'])

    def test_explicit_index_upgrade_keeps_legacy_records_and_backup_usable(self):
        before = self.core.store.snapshot(['tasks', 'checkpoints', 'decisions', 'config'])
        events = self.core.store.events()
        self.assertTrue(self.core.upgrade()['upgraded'])
        self.assertEqual(before, self.core.store.snapshot(['tasks', 'checkpoints', 'decisions', 'config']))
        self.assertEqual(events, self.core.store.events())
        self.assertEqual(0, self.application_id())
        plan = self.plan()
        self.assertTrue(self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])['verification']['verified'])

    def test_old_rejection_intent_continues_original_plan(self):
        plan = self.plan()
        with mock.patch('taskcarry.project_recovery._state_rows', side_effect=GovernanceError(
                'RECOVERY_STATE_CORRUPT', 'Synthetic previous reader rejected legacy header.')):
            self.assert_code('RECOVERY_STATE_CORRUPT', self.recovery.recovery,
                             'backup_execute', plan_id=plan['plan_id'])
        media = self.root / 'media'
        intent = (media / 'intent.json').read_bytes()
        self.assertFalse((media / 'manifest.json').exists())
        backup = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertEqual(plan['plan_id'], backup['plan_id'])
        self.assertEqual(intent, (media / 'intent.json').read_bytes())
        self.assertTrue(backup['verification']['verified'])
        self.assertTrue(self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])['reused_original_batch'])

    def test_legacy_manifest_effect_without_receipt_is_verified_then_reused(self):
        plan = self.plan()
        with mock.patch.object(self.recovery, '_receipt', side_effect=OSError('Synthetic receipt interruption')):
            with self.assertRaises(OSError):
                self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        manifest = (self.root / 'media/manifest.json').read_bytes()
        result = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertTrue(result['reused_original_batch'])
        self.assertTrue(result['verification']['verified'])
        self.assertEqual(manifest, (self.root / 'media/manifest.json').read_bytes())

    def test_foreign_application_id_is_rejected_even_with_matching_tables(self):
        with closing(sqlite3.connect(self.database)) as db:
            db.execute('PRAGMA application_id=12345')
        before = self.database.read_bytes()
        self.assertEqual('unknown', Core.identify(self.control)['state'])
        self.assert_code('STATE_UNRECOGNIZED', Core.initialize, self.control)
        self.assert_code('RECOVERY_STATE_CORRUPT', _state_rows, self.database)
        self.assertEqual(before, self.database.read_bytes())

    def test_legacy_requires_events_structure_and_project_config(self):
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('DROP TABLE events')
        self.assertEqual('unknown', Core.identify(self.control)['state'])
        self.assert_code('RECOVERY_STATE_CORRUPT', _state_rows, self.database)

    def test_non_object_config_is_corrupt_and_never_overwritten(self):
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("UPDATE records SET value='[]' WHERE collection='config' AND key='project'")
        before = self.database.read_bytes()
        self.assertEqual('corrupt', Core.identify(self.control)['state'])
        self.assert_code('RECOVERY_STATE_CORRUPT', _state_rows, self.database)
        self.assertEqual(before, self.database.read_bytes())

    def test_future_legacy_schema_is_unsupported_not_a_missing_marker_error(self):
        config = self.core.store.get('config', 'project')
        self.core.store.put('config', 'project', {**config, 'schema_version': 999})
        before = self.database.read_bytes()
        self.assertEqual('unsupported', Core.identify(self.control)['state'])
        self.assert_code('SCHEMA_VERSION_UNSUPPORTED', _state_rows, self.database)
        self.assertEqual(before, self.database.read_bytes())

    def test_invalid_legacy_formats_are_rejected_read_only(self):
        cases = (
            ('missing-config', "DELETE FROM records WHERE collection='config'", 'unknown', 'RECOVERY_STATE_CORRUPT'),
            ('bad-json', "UPDATE records SET value='{' WHERE collection='config'", 'corrupt', 'RECOVERY_STATE_CORRUPT'),
            ('bad-text', "UPDATE records SET value=x'ff' WHERE collection='config'", 'corrupt', 'RECOVERY_STATE_CORRUPT'),
            ('wrong-layout', 'ALTER TABLE events RENAME COLUMN payload TO unrelated', 'unknown', 'RECOVERY_STATE_CORRUPT'),
            ('future-index', 'CREATE TABLE context_schema(version INTEGER); INSERT INTO context_schema VALUES(999)',
             'unsupported', 'SCHEMA_VERSION_UNSUPPORTED'),
        )
        original = self.database.read_bytes()
        for name, sql, expected_state, code in cases:
            with self.subTest(name=name):
                root = self.root / name
                path = root / '.taskcarry/state.sqlite3'
                path.parent.mkdir(parents=True)
                path.write_bytes(original)
                with closing(sqlite3.connect(path)) as db, db:
                    db.executescript(sql)
                before = {p.name: p.read_bytes() for p in path.parent.iterdir()}
                self.assertEqual(expected_state, Core.identify(root)['state'])
                self.assert_code(code, _state_rows, path)
                self.assertEqual(before, {p.name: p.read_bytes() for p in path.parent.iterdir()})

    def test_unrelated_and_truncated_databases_are_not_legacy_projects(self):
        for name, content, state in (('unrelated', None, 'unknown'), ('truncated', b'not sqlite', 'corrupt')):
            with self.subTest(name=name):
                root = self.root / name
                path = root / '.taskcarry/state.sqlite3'
                path.parent.mkdir(parents=True)
                if content is None:
                    with closing(sqlite3.connect(path)) as db:
                        db.execute('CREATE TABLE measurements(sample INTEGER)')
                else:
                    path.write_bytes(content)
                before = path.read_bytes()
                self.assertEqual(state, Core.identify(root)['state'])
                self.assert_code('RECOVERY_STATE_CORRUPT', _state_rows, path)
                self.assertEqual(before, path.read_bytes())


if __name__ == '__main__':
    unittest.main()
