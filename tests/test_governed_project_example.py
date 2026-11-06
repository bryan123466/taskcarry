"""The published three-step scenario through the shared API, with honest host gaps."""
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest import mock

from taskcarry.api import invoke
from taskcarry.onboarding import fingerprint
from taskcarry.preservation import _git, _head, _index
from taskcarry.setup import configure


class GovernedProjectExampleTests(unittest.TestCase):
    def test_existing_project_and_projectless_notes_continue_without_fabricated_host_success(self):
        source = Path(__file__).resolve().parents[1]
        scenario = json.loads((source / 'examples/governed-project/scenario.json').read_text(encoding='utf-8'))
        # The ordinary source directory must be outside any ancestor Git repo.
        # Developers can assign their approved external synthetic sandbox.
        parent = Path(os.environ.get('TASKCARRY_TEST_SANDBOX', tempfile.gettempdir())) / 'governed-example'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            root = Path(temporary)
            control, app, guide, notes = [root / name for name in ('control', 'existing-app', 'guide-work', 'original-notes')]
            for path in (control, app, guide, notes):
                path.mkdir()
            for path in (control, app, guide):
                _git(path, 'init', '-b', 'main')
                _git(path, 'config', 'user.name', 'Synthetic Example Author')
                _git(path, 'config', 'user.email', 'example@example.invalid')
                _git(path, 'config', 'core.autocrlf', 'false')
            (app / 'app.txt').write_bytes(b'initial synthetic USB acquisition viewer\n')
            _git(app, 'add', '--', 'app.txt')
            _git(app, 'commit', '-m', 'Existing synthetic application')
            (app / 'app.txt').write_bytes(b'staged validation change\n')
            _git(app, 'add', '--', 'app.txt')
            (app / 'app.txt').write_bytes(b'unstaged validation work\n')
            (app / 'research.txt').write_bytes(b'keep this untracked research\n')
            old_head, old_index = _head(app), _index(app).read_bytes()
            old_files = {p.name: p.read_bytes() for p in app.glob('*.txt')}
            (notes / 'decisions.txt').write_text(scenario['confirmed_decision'], encoding='utf-8')
            original_notes = (notes / 'decisions.txt').read_bytes()

            invoke(control, 'init', {'name': scenario['name']})
            for task, next_step in scenario['next_steps'].items():
                invoke(control, 'task', {'task_id': task, 'title': next_step})
            invoke(control, 'workspace', {'name': 'app-writer', 'path': str(app)})
            invoke(control, 'workspace', {'name': 'guide-writer', 'path': str(guide)})
            scope = {key: scenario[key] for key in ('governance_thread', 'channel', 'schedule', 'windows')}
            started = invoke(control, 'onboarding', {'onboarding_id': 'first-use', 'action': 'start', 'scope': scope})
            self.assertFalse(started['standard_ready'])
            scope_item = {'key': 'scope', 'status': 'verified', 'next_step': '',
                          'evidence': {'receipt_ref': 'example:confirmed-scope', 'user_confirmed': True,
                                       'scope_fingerprint': fingerprint(scope)}}
            invoke(control, 'onboarding', {'onboarding_id': 'first-use', 'action': 'update',
                                          'item': scope_item, 'expected_revision': 1})
            invoke(control, 'observe', {'observation_id': 'guide-source', 'workspace': None, 'task_id': 'guide',
                                       'source_ref': 'example:previously-projectless-notes', 'source_revision': '1',
                                       'summary': scenario['confirmed_decision']})
            checkpoint = invoke(control, 'checkpoint', {'task_id': 'guide', 'workspace': str(notes),
                                                       'paths': ['decisions.txt'], 'next_step': scenario['next_steps']['guide']})
            restored = root / 'restored-notes'
            invoke(control, 'restore', {'checkpoint_id': checkpoint['checkpoint_id'], 'destination': str(restored)})
            self.assertEqual(original_notes, (restored / 'decisions.txt').read_bytes())
            self.assertFalse((notes / '.git').exists())
            (guide / 'GUIDE.md').write_text('Draft: simulated data replay and reconnect instructions.\n', encoding='utf-8')
            draft = invoke(control, 'preserve', {'repository': str(guide), 'paths': ['GUIDE.md'], 'message': 'Start the guide'})
            invoke(control, 'preserve', {'action': 'execute', 'plan_id': draft['plan_id']})
            for workspace, task, target in (('app-writer', 'app', app), ('guide-writer', 'guide', guide)):
                configure(control, mode='install', target=target, workspace=workspace, task_id=task)
                plan = invoke(control, 'connect', {'target': str(target), 'workspace': workspace, 'task_id': task})
                connection = invoke(control, 'connect', {'action': 'execute', 'plan_id': plan['plan']['plan_id']})
                self.assertFalse(connection['native_acceptance_verified'])
                config = tomllib.loads((target / '.codex/config.toml').read_text())
                self.assertEqual(['--project', str(control), 'mcp'], config['mcp_servers']['taskcarry']['args'][-3:])

            (control / 'PROJECT_RULES.md').write_text(scenario['confirmed_decision'], encoding='utf-8')
            local_plan = invoke(control, 'preserve', {'repository': str(control), 'paths': ['PROJECT_RULES.md'],
                                                     'message': 'Save the confirmed project scope'})
            local_saved = invoke(control, 'preserve', {'action': 'execute', 'plan_id': local_plan['plan_id']})
            local_item = {'key': 'local_git', 'status': 'verified', 'next_step': '', 'evidence': {
                'receipt_ref': 'example:local-save', 'plan_id': local_saved['plan_id'], 'commit': local_saved['commit']}}
            invoke(control, 'onboarding', {'onboarding_id': 'first-use', 'action': 'update',
                                          'item': local_item, 'expected_revision': 2})
            invoke(control, 'update_source', {'channel': scenario['channel']})
            with mock.patch('taskcarry.updates._fetch_json', return_value=([], '0' * 64)):
                check = invoke(control, 'update_check')
            invoke(control, 'update_assess', {'check': check, 'decision': 'keep',
                                              'reason': 'The synthetic release window is empty; retain the installed candidate.'})
            update_item = {'key': 'update_check', 'status': 'verified', 'next_step': '', 'evidence': {
                'receipt_ref': 'example:synthetic-release-check', 'channel': scenario['channel'], 'checked': True,
                'source': 'https://github.com/bryan123466/taskcarry/releases',
                'result_fingerprint': check['fingerprint'], 'assessment_ref': check['fingerprint']}}
            invoke(control, 'onboarding', {'onboarding_id': 'first-use', 'action': 'update',
                                          'item': update_item, 'expected_revision': 3})
            schedule = invoke(control, 'schedule_plan', {'onboarding_id': 'first-use'})
            self.assertFalse(schedule['execute'])
            self.assertEqual(scenario['governance_thread'], schedule['thread_id'])
            report = invoke(control, 'onboarding', {'onboarding_id': 'first-use'})
            self.assertEqual({'runtime', 'window:example-app', 'window:example-guide', 'schedule_config'}, set(report['pending']))
            self.assertFalse(report['standard_ready'])
            self.assertFalse(report['natural_trigger_verified'])
            self.assertNotIn('window:example-history', report['required'])
            self.assertTrue(invoke(control, 'onboarding', {'onboarding_id': 'first-use', 'action': 'start', 'scope': scope})['reused'])
            context = invoke(control, 'context', {'task_id': 'guide'})
            self.assertEqual(scenario['next_steps']['guide'], context['latest_checkpoint']['next_step'])
            self.assertEqual('guide-source', context['items'][0]['local_id'])
            self.assertEqual(old_head, _head(app))
            self.assertEqual(old_index, _index(app).read_bytes())
            self.assertEqual(old_files, {p.name: p.read_bytes() for p in app.glob('*.txt')})
            self.assertEqual(original_notes, (notes / 'decisions.txt').read_bytes())
            self.assertEqual(b'PROJECT_RULES.md\n', _git(control, 'ls-tree', '-r', '--name-only', 'HEAD').stdout)


if __name__ == '__main__':
    unittest.main()
