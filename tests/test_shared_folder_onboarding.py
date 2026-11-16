"""Per-chat current-entry acceptance with synthetic receipts, never native proof."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from taskcarry.core import Core, digest_bytes
from taskcarry.integration import Integration
from taskcarry.onboarding_complete import CompleteOnboarding
from taskcarry.setup import configure
from taskcarry.store import GovernanceError
from taskcarry.workbench import Workbench, git_snapshot


class SharedFolderOnboardingTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / 'validation/local/shared-folder-onboarding-tests'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-', dir=parent)
        self.base = Path(self.temp.name)
        self.control = self.base / 'control'
        Core.initialize(self.control, name='Synthetic original chats in one project')
        self.core = Core(self.control)
        self.engine = Workbench(self.control)
        self.service = CompleteOnboarding(self.control)
        for task in ('software', 'algorithm'):
            self.core.task(task, title='Continue original ' + task)
        self.worker = self.repository('shared')
        self.windows = [self.window('software-chat', 'software'), self.window('algorithm-chat', 'algorithm')]
        self.original_tasks = self.core.store.list('tasks')
        self.original_git = self.snapshot(self.worker)
        self.view = self.freeze('First shared project decision')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, root, *args):
        return subprocess.check_output(['git', '-C', str(root), *args],
                                       env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))

    def repository(self, workspace):
        root = self.base / workspace
        root.mkdir()
        self.git(root, 'init', '-b', 'main')
        self.git(root, 'config', 'user.name', 'Synthetic Original Project')
        self.git(root, 'config', 'user.email', 'synthetic@example.invalid')
        self.git(root, 'config', 'core.autocrlf', 'false')
        (root / '.gitignore').write_text('.taskcarry/\n.codex/\n.agents/\n.local/\n', encoding='utf-8')
        (root / 'project.txt').write_bytes(b'original committed project\n')
        self.git(root, 'add', '--', '.gitignore', 'project.txt')
        self.git(root, 'commit', '-m', 'Original synthetic project')
        (root / 'project.txt').write_bytes(b'original staged work\n')
        self.git(root, 'add', '--', 'project.txt')
        (root / 'project.txt').write_bytes(b'original unstaged continuation\n')
        (root / 'notes.txt').write_bytes(b'original untracked notes\n')
        (root / '.codex').mkdir()
        (root / '.codex/config.toml').write_text(
            'developer_instructions = "Keep existing project conventions."\nmodel = "synthetic-model"\n', encoding='utf-8')
        Integration(self.control).workspace(workspace, str(root))
        return root

    def snapshot(self, root):
        return {'git': git_snapshot(root), 'status': self.git(root, 'status', '--porcelain=v1'),
                'staged': self.git(root, 'ls-files', '--stage'),
                'files': {name: (root / name).read_bytes() for name in ('project.txt', 'notes.txt')}}

    @staticmethod
    def window(thread, task, workspace='shared'):
        return {'thread_id': thread, 'task_id': task, 'workspace': workspace, 'mode': 'active',
                'source_ref': 'synthetic:' + thread, 'responsibility': 'Retain original task and conversation.'}

    def scope(self, windows=None):
        return {'profile': 'complete_v1', 'governance_thread': 'synthetic-governance', 'channel': 'rc',
                'schedule': {'timezone': 'UTC', 'slots': [
                    {'slot_id': 'report', 'purpose': 'report', 'time': '09:00'},
                    {'slot_id': 'absorb', 'purpose': 'absorb', 'time': '15:00'}]},
                'windows': windows if windows is not None else self.windows}

    def start(self, windows=None):
        return self.service.onboarding('original-setup', 'start', scope=self.scope(windows))

    def directory_setup(self):
        return configure(self.control, mode='install', target=self.worker, workspace='shared', binding_mode='directory')

    def freeze(self, text):
        rules = self.control / 'PROJECT_RULES.md'
        rules.write_text(text + '\n', encoding='utf-8')
        return self.engine.workbench('freeze', body=text, sources=[{'source_id': 'synthetic-rules',
            'path': 'PROJECT_RULES.md', 'revision': digest_bytes(rules.read_bytes())}])

    def publish(self, windows=None, legacy=False):
        targets = [{**{key: w[key] for key in ('workspace', 'task_id', 'thread_id')}, 'host': 'codex',
                    'code_assessment': {'status': 'NO_CODE_DEPENDENCY', 'reason': 'Synthetic project navigation only.'}}
                   for w in (windows if windows is not None else self.windows)]
        arguments = {} if legacy else {'routing': 'shared'}
        plan = self.engine.workbench('plan', view_id=self.view['view_id'], targets=targets, **arguments)
        self.assertEqual('COMPLETED', self.engine.workbench('execute', plan_id=plan['plan_id'])['status'])
        return plan

    def consume(self, plan, window):
        evidence = self.control / ('synthetic-' + window['thread_id'] + '-' + plan['plan_id'][:10] + '.json')
        evidence.write_text(json.dumps({'fixture': 'synthetic reviewed consumption; no actual native host',
                                       'thread': window['thread_id'], 'view': self.view['view_id']}) + '\n', encoding='utf-8')
        proof = {**{k: window[k] for k in ('workspace', 'task_id', 'thread_id')},
                 'source_id': self.engine.source()['source_id'], 'plan_id': plan['plan_id'], 'view_id': self.view['view_id'],
                 'turn_id': 'synthetic-turn', 'evidence_path': evidence.name,
                 'evidence_sha256': digest_bytes(evidence.read_bytes()), 'reviewer': 'synthetic fixture reviewer',
                 'observed_at': '2026-01-01T00:00:00Z'}
        return self.engine.workbench('consume', proof=proof)

    def entries(self, windows=None, legacy=False):
        entries = [{**{k: w[k] for k in ('workspace', 'task_id', 'thread_id')},
                    'view_id': self.view['view_id'], 'native_doctor_status_verified': True}
                   for w in (windows if windows is not None else self.windows)]
        if legacy:
            entries = [{k: v for k, v in e.items() if k not in ('task_id', 'thread_id')} for e in entries]
        return entries

    def update(self, entries):
        prior = self.service.onboarding('original-setup')['onboarding']
        return self.service.onboarding('original-setup', 'update', expected_revision=prior['revision'], item={
            'key': 'workbenches', 'status': 'verified', 'next_step': '', 'evidence': {
                'receipt_ref': 'synthetic:validator-fixture', 'fixture_notice': 'Synthetic attestations are not native host evidence.',
                'entries': entries}})

    def assert_rejected_unchanged(self, entries):
        before = self.core.store.get('onboarding', 'original-setup')
        events = self.core.store.events()
        with self.assertRaises(GovernanceError) as caught:
            self.update(entries)
        self.assertEqual('ONBOARDING_EVIDENCE', caught.exception.code)
        self.assertEqual(before, self.core.store.get('onboarding', 'original-setup'))
        self.assertEqual(events, self.core.store.events())

    def test_two_original_tasks_share_one_directory_and_need_both_consumptions(self):
        self.directory_setup()
        self.start()
        plan = self.publish()
        self.consume(plan, self.windows[0])
        self.assert_rejected_unchanged(self.entries())
        self.consume(plan, self.windows[1])
        result = self.update(self.entries())
        self.assertNotIn('workbenches', result['pending'])
        self.assertFalse(result['complete_governance_ready'], 'Other required items still have no actual host evidence.')
        self.assertEqual(2, len(self.engine.workbench('status', workspace='shared')['items']))
        self.assertEqual(self.original_tasks, self.core.store.list('tasks'))
        self.assertEqual(self.original_git, self.snapshot(self.worker))

    def test_same_task_two_original_chats_are_independent_consumers(self):
        self.windows[1]['task_id'] = 'software'
        self.directory_setup()
        self.start()
        plan = self.publish()
        first = self.consume(plan, self.windows[0])
        self.assert_rejected_unchanged(self.entries())
        second = self.consume(plan, self.windows[1])
        self.assertNotEqual(first['consumption_id'], second['consumption_id'])
        self.assertNotIn('workbenches', self.update(self.entries())['pending'])
        for window in self.windows:
            current = self.engine.workbench('status', workspace='shared', thread_id=window['thread_id'])['items']
            self.assertEqual(1, len(current))
            self.assertEqual(window['thread_id'], current[0]['thread_id'])
            self.assertEqual('REVIEWED_EVIDENCE_RECORDED', current[0]['consumer_state'])

    def test_new_view_requires_each_chat_again_without_rewriting_old_evidence(self):
        self.directory_setup()
        self.start()
        old = self.publish()
        for window in self.windows:
            self.consume(old, window)
        self.update(self.entries())
        retained = self.core.store.get('onboarding', 'original-setup')
        old_view_id = self.view['view_id']
        self.view = self.freeze('New shared project decision')
        plan = self.publish()
        self.consume(plan, self.windows[0])
        events = self.core.store.events()
        status = self.service.onboarding('original-setup')
        self.assertIn('workbenches', status['pending'])
        self.assertIn('workbenches', status['invalidated'])
        self.assertEqual(retained, self.core.store.get('onboarding', 'original-setup'))
        self.assertEqual(events, self.core.store.events())
        self.assertEqual(old_view_id, retained['items']['workbenches']['evidence']['entries'][0]['view_id'])
        self.assert_rejected_unchanged(self.entries())
        self.consume(plan, self.windows[1])
        self.assertNotIn('workbenches', self.update(self.entries())['pending'])
        self.assertEqual(self.original_git, self.snapshot(self.worker))

    def test_missing_wrong_duplicate_or_extra_chat_identity_is_rejected(self):
        self.directory_setup()
        self.start()
        plan = self.publish()
        for window in self.windows:
            self.consume(plan, window)
        entries = self.entries()
        cases = [entries[:1], entries + [entries[0]], [entries[0], entries[0]], self.entries(legacy=True)]
        for field, value in (('task_id', 'software'), ('thread_id', 'wrong-chat'), ('workspace', 'wrong-workspace'),
                             ('workspace', []), ('task_id', None), ('view_id', '0' * 64),
                             ('native_doctor_status_verified', False)):
            changed = deepcopy(entries)
            changed[1][field] = value
            cases.append(changed)
        for field in ('task_id', 'thread_id'):
            changed = deepcopy(entries)
            del changed[1][field]
            cases.append(changed)
        for case in cases:
            with self.subTest(entries=case):
                self.assert_rejected_unchanged(case)

    def test_legacy_single_chat_entry_remains_valid_and_is_not_rewritten(self):
        self.windows = self.windows[:1]
        configure(self.control, mode='install', target=self.worker, workspace='shared', task_id='software')
        self.start()
        plan = self.publish(legacy=True)
        self.consume(plan, self.windows[0])
        compact = self.entries(legacy=True)
        result = self.update(compact)
        self.assertNotIn('workbenches', result['pending'])
        self.assertEqual(compact, result['onboarding']['items']['workbenches']['evidence']['entries'])
        before = self.core.store.get('onboarding', 'original-setup')
        events = self.core.store.events()
        self.assertNotIn('workbenches', self.service.onboarding('original-setup')['pending'])
        self.assertEqual(before, self.core.store.get('onboarding', 'original-setup'))
        self.assertEqual(events, self.core.store.events())
        self.assertEqual(self.original_git, self.snapshot(self.worker))

    def test_old_compact_entries_are_unique_per_directory_not_per_whole_project(self):
        self.repository('algorithm-work')
        self.windows[1]['workspace'] = 'algorithm-work'
        self.start()
        plan = self.publish(legacy=True)
        for window in self.windows:
            self.consume(plan, window)
        compact = self.entries(legacy=True)
        result = self.update(compact)
        self.assertNotIn('workbenches', result['pending'])
        self.assertEqual(compact, result['onboarding']['items']['workbenches']['evidence']['entries'])

    def test_legacy_compact_evidence_does_not_follow_a_changed_selected_chat(self):
        self.windows = self.windows[:1]
        self.start()
        plan = self.publish(legacy=True)
        self.consume(plan, self.windows[0])
        compact = self.entries(legacy=True)
        self.update(compact)
        retained = self.core.store.get('onboarding', 'original-setup')
        other = self.window('another-chat', 'software')
        self.service.onboarding('original-setup', 'start', scope=self.scope([other]),
                                expected_revision=retained['revision'])
        self.assert_rejected_unchanged(compact)
        status = self.service.onboarding('original-setup')
        self.assertIn('workbenches', status['pending'])
        self.assertEqual(retained, self.core.store.get('onboarding_history', 'original-setup:' + str(retained['revision'])))

    def test_reference_only_history_does_not_require_a_workspace_entry(self):
        reference = {'thread_id': 'historical-chat', 'mode': 'reference', 'source_ref': 'synthetic:history',
                     'responsibility': 'Keep earlier decisions as reference.'}
        self.start(windows=[reference])
        self.assertNotIn('workbenches', self.update([])['pending'])


if __name__ == '__main__':
    unittest.main()
