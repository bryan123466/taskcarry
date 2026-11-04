"""Existing-project onboarding through CLI and generated MCP, using synthetic work."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ExistingProjectOnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='taskcarry-existing-project-')
        self.root = Path(self.temp.name)
        self.control = self.root / 'existing-control'
        self.package = Path(os.environ.get('TASKCARRY_ONBOARDING_PACKAGE', str(ROOT))).resolve()
        self.environment = {**os.environ, 'PYTHONPATH': str(self.package), 'PYTHONUTF8': '1'}

    def tearDown(self):
        self.temp.cleanup()

    def git(self, path, *args):
        result = subprocess.run(['git', '-C', str(path), *args], capture_output=True,
                                text=True, encoding='utf-8', timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.strip()

    def call(self, action, **arguments):
        request = self.root / 'request.json'
        request.write_text(json.dumps(arguments, ensure_ascii=False), encoding='utf-8')
        process = subprocess.run([sys.executable, '-m', 'taskcarry', '--project', str(self.control),
                                  action, '--input', str(request)], cwd=self.root, env=self.environment,
                                 capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(0, process.returncode, process.stdout + process.stderr)
        envelope = json.loads(process.stdout)
        self.assertTrue(envelope['ok'], envelope)
        return envelope['result']

    def snapshot(self, workspace):
        files = {str(path.relative_to(workspace)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in workspace.rglob('*') if path.is_file()
                 and path.relative_to(workspace).parts[0] not in ('.git', '.taskcarry', '.agents')}
        return {'head': self.git(workspace, 'rev-parse', 'HEAD'),
                'index': self.git(workspace, 'ls-files', '--stage'), 'files': files}

    def scenario(self, count):
        repository = self.root / 'existing-repository'
        repository.mkdir()
        self.git(repository, 'init', '-b', 'main')
        self.git(repository, 'config', 'user.name', 'Synthetic Onboarding')
        self.git(repository, 'config', 'user.email', 'onboarding@example.invalid')
        (repository / 'notes.md').write_text('Existing accepted result\n', encoding='utf-8')
        self.git(repository, 'add', '--', 'notes.md')
        self.git(repository, 'commit', '-m', 'Existing synthetic project')
        self.call('init', name='Existing synthetic project')
        self.call('setup', mode='install', server_name='project_memory')
        workers, before, checkpoints = [], {}, {}
        for index in range(count):
            name, task_id = f'original-{index}', f'existing-task-{index}'
            worker = self.root / name
            self.git(repository, 'worktree', 'add', '-b', 'codex/' + name, str(worker))
            self.call('workspace', name=name, path=str(worker))
            self.call('task', task_id=task_id, title='Existing responsibility ' + str(index), workstream=name)
            (worker / 'notes.md').write_text('Staged existing work\n', encoding='utf-8')
            self.git(worker, 'add', '--', 'notes.md')
            (worker / 'notes.md').write_text('Later unfinished work\n', encoding='utf-8')
            (worker / 'draft.txt').write_text('Untracked idea\n', encoding='utf-8')
            (worker / 'AGENTS.md').write_text('Keep the original working instructions.\n', encoding='utf-8')
            (worker / '.codex').mkdir()
            (worker / '.codex/config.toml').write_text('[mcp_servers.existing]\ncommand = "existing-tool"\n', encoding='utf-8')
            checkpoint = self.call('checkpoint', task_id=task_id, workspace=name,
                                   paths=['notes.md', 'draft.txt'], next_step='Continue original work',
                                   decision='The user confirmed the existing responsibility')
            checkpoints[task_id] = checkpoint['checkpoint_id']
            before[name] = self.snapshot(worker)
            workers.append((name, task_id, worker))
        original = self.call('status')
        for name, task_id, worker in workers:
            arguments = {'target': str(worker), 'workspace': name, 'task_id': task_id,
                         'server_name': 'project_memory'}
            self.call('setup', mode='preview', **arguments)
            self.assertFalse((worker / '.taskcarry').exists(), 'Preview must not create a second state store')
            self.call('setup', mode='install', **arguments)
            manifest = (worker / '.taskcarry/setup-manifest.json').read_bytes()
            self.call('setup', mode='install', **arguments)
            self.assertEqual(manifest, (worker / '.taskcarry/setup-manifest.json').read_bytes())
            self.assertFalse((worker / '.taskcarry/state.sqlite3').exists())
            self.assertEqual(before[name], self.snapshot(worker))
            self.assertEqual(4, len(list((worker / '.agents/skills').glob('*/SKILL.md'))))
            self.assertTrue((worker / '.agents/skills/taskcarry-project-setup/references/onboarding.md').is_file())
            binding = json.loads((worker / '.taskcarry/workbench.json').read_text(encoding='utf-8'))
            self.assertEqual(str(self.control.resolve()), binding['control'])
            self.assertEqual(task_id, binding['task_id'])
            config = tomllib.loads((worker / '.taskcarry/codex.mcp.toml').read_text(encoding='utf-8'))['mcp_servers']['project_memory']
            frames = [
                {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
                    'protocolVersion': '2025-11-25', 'capabilities': {},
                    'clientInfo': {'name': 'synthetic-existing-project', 'version': '1'}}},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'taskcarry_status'}},
                {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'taskcarry_doctor'}},
            ]
            # A misleading source cwd/environment must not override the
            # installation selected by setup (also exercised on an actual wheel).
            environment = {**self.environment, 'PYTHONPATH': str(ROOT)}
            process = subprocess.run([config['command'], *config['args']], cwd=worker,
                                     env=environment, input='\n'.join(json.dumps(f) for f in frames) + '\n',
                                     capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(0, process.returncode, process.stderr)
            replies = [json.loads(line) for line in process.stdout.splitlines()]
            self.assertFalse(replies[1]['result']['isError'])
            self.assertFalse(replies[2]['result']['isError'])
            state = replies[1]['result']['structuredContent']['result']
            self.assertEqual(checkpoints, {t['task_id']: t['latest_checkpoint'] for t in state['tasks']})
            loaded = replies[2]['result']['structuredContent']['result']['runtime']['loaded_runtime']
            self.assertEqual(self.package / 'taskcarry', Path(loaded['module_root']))
        final = self.call('status')
        self.assertEqual(original['tasks'], final['tasks'])
        self.assertEqual(original['workspaces'], final['workspaces'])
        self.assertEqual([], final['stages'], 'Onboarding must not manufacture old deliveries')
        self.assertEqual(len(checkpoints), len(final['checkpoints']))

    def test_single_existing_chat_needs_no_new_professional_task(self):
        self.scenario(1)

    def test_multiple_existing_chats_keep_identity_wip_and_one_control(self):
        self.scenario(3)


if __name__ == '__main__':
    unittest.main()
