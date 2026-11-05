"""Independent synthetic checks for project binding and owned-block upgrades."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import tomllib

from taskcarry.connection import Connection
from taskcarry.core import Core
from taskcarry.integration import Integration
from taskcarry.preservation import _git
from taskcarry.setup import atomic_write, configure, loaded_runtime, planned_files, SetupError
from taskcarry.store import GovernanceError


class ConnectionIndependentReviewTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / 'validation/local/tests'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='connection-review-', dir=parent)
        self.root = Path(self.temp.name)
        self.control = self.root / 'control'
        Core.initialize(self.control)
        self.engine = Connection(self.control)
        self.work = self.root / 'work'
        self.work.mkdir()
        _git(self.work, 'init', '-b', 'main')
        Integration(self.control).workspace('writer', self.work)
        self.engine.task('guide')

    def tearDown(self):
        self.temp.cleanup()

    def test_unbound_workbench_materials_cannot_activate_another_control(self):
        configure(self.work, mode='install')
        fragment = (self.work / '.taskcarry/codex.mcp.toml').read_text()
        self.assertIn(str(self.work).replace('\\', '/'), fragment.replace('\\\\', '/'))
        with self.assertRaises((GovernanceError, SetupError)):
            self.engine.connect(target=str(self.work), workspace='writer', task_id='guide')
        self.assertFalse((self.work / '.codex/config.toml').exists())

    def test_owned_server_upgrade_preserves_other_configuration(self):
        configure(self.control, mode='install')
        config = self.control / '.codex/config.toml'
        config.parent.mkdir()
        original = b'# keep this comment\nmodel="synthetic-choice"\n[mcp_servers.other]\ncommand="other-tool"\n'
        config.write_bytes(original)
        p = self.engine.connect()['plan']['plan_id']
        self.engine.connect('execute', plan_id=p)
        changed_runtime = loaded_runtime()
        changed_runtime['interpreter'] = str(self.root / 'next-runtime' / 'python.exe')
        with patch('taskcarry.setup.sys.executable', changed_runtime['interpreter']):
            configure(self.control, mode='install')
            p = self.engine.connect()['plan']['plan_id']
            self.engine.connect('execute', plan_id=p)
        self.assertTrue(config.read_bytes().startswith(original))
        parsed = tomllib.loads(config.read_text())
        self.assertEqual(Path(changed_runtime['interpreter']), Path(parsed['mcp_servers']['taskcarry']['command']))
        self.assertEqual('other-tool', parsed['mcp_servers']['other']['command'])
        self.assertEqual(1, config.read_bytes().count(b'[mcp_servers.taskcarry]'))

    def test_sealed_inline_mcp_table_returns_structured_conflict_without_edit(self):
        configure(self.control, mode='install')
        config = self.control / '.codex/config.toml'
        config.parent.mkdir()
        original = b'mcp_servers = { other = { command = "synthetic-tool" } }\n'
        config.write_bytes(original)
        with self.assertRaises(GovernanceError):
            self.engine.connect()
        self.assertEqual(original, config.read_bytes())

    def _interrupt_setup_after_intent(self):
        """Leave a real pending setup update whose MCP fragment is unchanged."""
        original_fragment = (self.control / '.taskcarry/codex.mcp.toml').read_bytes()

        def next_files(*args, **kwargs):
            files = planned_files(*args, **kwargs)
            name = next(name for name in files if name.endswith('SKILL.md'))
            return {**files, name: files[name] + b'\nSynthetic next method revision.\n'}

        def stop_after_intent(path, content):
            atomic_write(path, content)
            if path.name == 'setup-intent.json':
                raise RuntimeError('Synthetic interruption after durable setup intent')

        with patch('taskcarry.setup.planned_files', side_effect=next_files), \
                patch('taskcarry.setup.atomic_write', side_effect=stop_after_intent):
            with self.assertRaisesRegex(RuntimeError, 'durable setup intent'):
                configure(self.control, mode='install')
        self.assertTrue((self.control / '.taskcarry/setup-intent.json').exists())
        self.assertEqual(original_fragment, (self.control / '.taskcarry/codex.mcp.toml').read_bytes())

    def test_missing_manifest_returns_setup_required_without_config_write(self):
        configure(self.control, mode='install')
        (self.control / '.taskcarry/setup-manifest.json').unlink()
        self.assertTrue((self.control / '.taskcarry/codex.mcp.toml').exists())
        with self.assertRaises(GovernanceError) as error:
            self.engine.connect()
        self.assertIn(error.exception.code, ('SETUP_REQUIRED', 'CONNECTION_SETUP_REQUIRED'))
        self.assertFalse((self.control / '.codex/config.toml').exists())

    def test_pending_setup_after_plan_blocks_new_connection_write(self):
        configure(self.control, mode='install')
        config = self.control / '.codex/config.toml'
        config.parent.mkdir()
        original = b'# keep user configuration\nmodel="synthetic-choice"\n'
        config.write_bytes(original)
        plan_id = self.engine.connect()['plan']['plan_id']
        self._interrupt_setup_after_intent()
        with self.assertRaises(GovernanceError) as error:
            self.engine.connect('execute', plan_id=plan_id)
        self.assertEqual('CONNECTION_SETUP_PENDING', error.exception.code)
        self.assertEqual(original, config.read_bytes())
        self.assertEqual('PLANNED', self.engine.connect('status', plan_id=plan_id)['plan']['state'])
        self.assertTrue((self.control / '.taskcarry/setup-intent.json').exists())

    def test_pending_setup_allows_receipt_recovery_for_existing_exact_effect(self):
        configure(self.control, mode='install')
        plan_id = self.engine.connect()['plan']['plan_id']
        config = self.control / '.codex/config.toml'

        def stop_after_config(path, content):
            atomic_write(path, content)
            raise RuntimeError('Synthetic interruption after exact config write')

        with patch('taskcarry.connection.atomic_write', side_effect=stop_after_config):
            with self.assertRaisesRegex(RuntimeError, 'exact config write'):
                self.engine.connect('execute', plan_id=plan_id)
        saved = config.read_bytes()
        self.assertEqual('PREPARED', self.engine.connect('status', plan_id=plan_id)['plan']['state'])
        self._interrupt_setup_after_intent()
        with patch('taskcarry.connection.atomic_write', side_effect=AssertionError('Do not replay config writes')):
            recovered = self.engine.connect('execute', plan_id=plan_id)
        self.assertEqual('COMPLETED', recovered['plan']['state'])
        self.assertFalse(recovered['file_written'])
        self.assertFalse(recovered['host_loading_verified'])
        self.assertFalse(recovered['native_acceptance_verified'])
        self.assertEqual(saved, config.read_bytes())
        self.assertTrue((self.control / '.taskcarry/setup-intent.json').exists())


if __name__ == '__main__':
    unittest.main()
