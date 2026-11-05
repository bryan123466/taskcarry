"""Project-only MCP merges preserve user text and recover after the file effect."""
import tempfile
from pathlib import Path
import tomllib
import unittest
from unittest.mock import patch

from taskcarry.connection import Connection
from taskcarry.core import Core
from taskcarry.setup import configure
from taskcarry.store import GovernanceError


class ConnectionMergeTests(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).resolve().parents[1] / 'validation/local/tests'
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base, prefix='connection-')
        self.root = Path(self.temp.name).resolve()
        Core.initialize(self.root)
        configure(self.root, mode='install')
        self.engine = Connection(self.root)
        self.file = self.root / '.codex/config.toml'
        self.file.parent.mkdir()
        self.original = b'# keep my comment\nmodel = "chosen-model"\n[mcp_servers.existing]\ncommand = "existing"\n'
        self.file.write_bytes(self.original)

    def tearDown(self):
        self.temp.cleanup()

    def plan(self):
        return self.engine.connect()['plan']['plan_id']

    def test_plan_retains_config_and_execute_preserves_unrelated_bytes(self):
        key = self.plan()
        self.assertEqual(self.file.read_bytes(), self.original)
        saved = self.engine.connect(action='execute', plan_id=key)
        self.assertTrue(saved['file_written'])
        self.assertTrue(self.file.read_bytes().startswith(self.original))
        data = tomllib.loads(self.file.read_text())
        self.assertEqual(set(data['mcp_servers']), {'existing', 'taskcarry'})
        self.assertFalse(saved['native_acceptance_verified'])
        self.assertFalse(self.engine.connect(action='execute', plan_id=key)['file_written'])

    def test_crash_after_effect_only_repairs_receipt(self):
        from taskcarry.connection import atomic_write
        key = self.plan()
        def interrupt(path, content):
            atomic_write(path, content)
            raise RuntimeError('synthetic post-effect interruption')
        with patch('taskcarry.connection.atomic_write', side_effect=interrupt):
            with self.assertRaises(RuntimeError):
                self.engine.connect(action='execute', plan_id=key)
        before = self.file.stat().st_mtime_ns
        with patch('taskcarry.connection.atomic_write', side_effect=AssertionError('effect replayed')):
            result = self.engine.connect(action='execute', plan_id=key)
        self.assertEqual(result['plan']['state'], 'COMPLETED')
        self.assertEqual(before, self.file.stat().st_mtime_ns)

    def test_edit_after_plan_preserved(self):
        key = self.plan()
        changed = self.original + b'# user changed this after preview\n'
        self.file.write_bytes(changed)
        with self.assertRaises(GovernanceError) as raised:
            self.engine.connect(action='execute', plan_id=key)
        self.assertEqual(raised.exception.code, 'CONNECTION_CONFIG_CHANGED')
        self.assertEqual(changed, self.file.read_bytes())

    def test_unmanaged_same_name_service_is_not_replaced(self):
        changed = self.original + b'[mcp_servers.taskcarry]\ncommand = "user-custom-command"\n'
        self.file.write_bytes(changed)
        with self.assertRaises(GovernanceError) as raised:
            self.plan()
        self.assertEqual(raised.exception.code, 'CONNECTION_CONFLICT')
        self.assertEqual(changed, self.file.read_bytes())

    def test_identical_existing_service_is_reused(self):
        self.file.write_bytes(self.original + (self.root / '.taskcarry/codex.mcp.toml').read_bytes())
        before = self.file.read_bytes()
        result = self.engine.connect(action='execute', plan_id=self.plan())
        self.assertFalse(result['file_written'])
        self.assertEqual(before, self.file.read_bytes())

    def test_user_level_root_rejected(self):
        with patch('taskcarry.connection.Path.home', return_value=self.root):
            with self.assertRaises(GovernanceError) as raised:
                self.plan()
        self.assertEqual(raised.exception.code, 'PROJECT_CONFIG_REQUIRED')


if __name__ == '__main__':
    unittest.main()
