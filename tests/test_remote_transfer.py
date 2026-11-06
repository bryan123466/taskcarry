"""Real local bare Git endpoints and synthetic sealed recovery-copy effects."""
from pathlib import Path
import inspect
import os
import tempfile
import unittest
from unittest import mock

from taskcarry.core import Core
from taskcarry.gitops import git, out
from taskcarry.project_recovery import ProjectRecovery
from taskcarry.remote_transfer import RemoteTransfer, _snapshot, _git
from taskcarry.store import GovernanceError
from taskcarry.transfer_contracts import SCHEMAS


class RemoteTransferTests(unittest.TestCase):
    def setUp(self):
        sandbox = Path(__file__).resolve().parents[1] / 'validation' / 'local' / 'transfer-tests'
        sandbox.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-', dir=sandbox)
        self.root = Path(self.temp.name)
        self.control = self.root / 'control'
        Core.initialize(self.control, 'Synthetic exchange')
        self.core = RemoteTransfer(self.control)
        self.core.task('catalog', state='active')
        self.repo = self.root / 'author'
        self.repo.mkdir()
        git(self.repo, 'init', '-b', 'main')
        git(self.repo, 'config', 'user.name', 'Synthetic Author')
        git(self.repo, 'config', 'user.email', 'author@example.invalid')
        (self.repo / 'guide.txt').write_text('first revision\n', encoding='utf-8')
        git(self.repo, 'add', 'guide.txt')
        git(self.repo, 'commit', '-m', 'Synthetic initial commit')
        self.first = out(self.repo, 'rev-parse', 'HEAD')
        self.remote = self.root / 'remote.git'
        git(self.root, 'init', '--bare', str(self.remote))
        git(self.repo, 'remote', 'add', 'backup', str(self.remote))

    def tearDown(self):
        self.temp.cleanup()

    def assertCode(self, code, call, *args, **kwargs):
        with self.assertRaises(GovernanceError) as caught:
            call(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def plan(self, **values):
        return self.core.transfer('publish_plan', **{'repository': str(self.repo), 'remote': 'backup',
            'ref': 'refs/heads/backup', 'commit': self.first, **values})['plan']

    def execute(self, plan):
        return self.core.transfer('publish_execute', plan_id=plan['plan_id'])

    def second_commit(self):
        (self.repo / 'guide.txt').write_text('second revision\n', encoding='utf-8')
        git(self.repo, 'add', 'guide.txt')
        git(self.repo, 'commit', '-m', 'Synthetic second revision')
        return out(self.repo, 'rev-parse', 'HEAD')

    def media(self):
        recovery = ProjectRecovery(self.control)
        media = self.root / 'sealed-media'
        plan = recovery.recovery('backup_plan', destination=str(media))
        result = recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        return result

    def copy_plan(self, media=None):
        media = media or self.media()
        return self.core.transfer('copy_plan', manifest=media['manifest'], expected_sha256=media['manifest_sha256'],
                                  destination=str(self.root / 'sync-folder' / 'selected-set'))['plan']

    def test_plan_freezes_single_ref_and_execute_preserves_dirty_index_and_worktree(self):
        (self.repo / 'guide.txt').write_text('staged local draft\n', encoding='utf-8')
        git(self.repo, 'add', 'guide.txt')
        (self.repo / 'guide.txt').write_text('unstaged further draft\n', encoding='utf-8')
        (self.repo / 'notes.txt').write_text('untracked synthetic notes', encoding='utf-8')
        (self.repo / '.env').write_text('SYNTHETIC_PLACEHOLDER=not-a-secret', encoding='utf-8')
        before = _snapshot(self.repo)
        plan = self.plan()
        self.assertEqual(self.first, plan['commit'])
        self.assertIsNone(plan['expected_old_ref'])
        self.assertEqual('', out(self.remote, 'for-each-ref', '--format=%(refname)'))
        result = self.execute(plan)
        self.assertTrue(result['observed_effect']['verified'])
        self.assertTrue(result['receipt']['worktree_unchanged'])
        self.assertEqual(before, _snapshot(self.repo))
        self.assertEqual('refs/heads/backup', out(self.remote, 'for-each-ref', '--format=%(refname)'))
        self.assertEqual('first revision', out(self.remote, 'show', self.first + ':guide.txt'))
        self.assertEqual('active', self.core.store.get('tasks', 'catalog')['state'])

    def test_identical_retry_reads_real_effect_and_writes_no_duplicate_receipt(self):
        plan = self.plan()
        first = self.execute(plan)
        events = self.core.store.events()
        with mock.patch('taskcarry.remote_transfer._git', wraps=_git) as commands:
            again = self.execute(plan)
            self.assertFalse(any(call.args[1] == 'push' for call in commands.call_args_list))
        self.assertTrue(again['reused'])
        self.assertEqual(first['receipt'], again['receipt'])
        self.assertEqual(events, self.core.store.events())

    def test_crash_after_real_push_repairs_only_missing_receipt(self):
        plan = self.plan()
        with mock.patch.object(self.core, '_finish', side_effect=RuntimeError('synthetic receipt crash')):
            with self.assertRaises(RuntimeError):
                self.execute(plan)
        self.assertEqual(self.first, out(self.remote, 'rev-parse', 'refs/heads/backup'))
        self.assertIsNone(self.core.store.get('transfer_receipts', plan['plan_id']))
        with mock.patch('taskcarry.remote_transfer._git', wraps=_git) as commands:
            recovered = self.execute(plan)
            self.assertFalse(any(call.args[1] == 'push' for call in commands.call_args_list))
        self.assertTrue(recovered['receipt']['effect_reused'])

    def test_lost_transport_response_is_resolved_by_remote_effect_not_replayed(self):
        plan = self.plan()
        calls = []
        def transport(root, *args, **kwargs):
            value = _git(root, *args, **kwargs)
            if args[0] == 'push':
                calls.append(args)
                raise GovernanceError('TRANSFER_TRANSPORT_UNKNOWN', 'Synthetic connection closed after effect')
            return value
        with mock.patch('taskcarry.remote_transfer._git', side_effect=transport):
            result = self.execute(plan)
        self.assertEqual(1, len(calls))
        self.assertTrue(result['observed_effect']['verified'])
        self.assertEqual('TRANSFER_TRANSPORT_UNKNOWN', result['receipt']['transport_warning']['code'])

    def test_remote_ref_changed_after_plan_is_preserved(self):
        plan = self.plan()
        second = self.second_commit()
        git(self.repo, 'push', str(self.remote), second + ':refs/heads/backup')
        self.assertCode('TRANSFER_REMOTE_CHANGED', self.execute, plan)
        self.assertEqual(second, out(self.remote, 'rev-parse', 'refs/heads/backup'))
        self.assertIsNone(self.core.store.get('transfer_attempts', plan['plan_id']))

    def test_race_between_inspection_and_push_is_stopped_by_exact_lease(self):
        second = self.second_commit()
        plan = self.plan(commit=second)
        first = self.first
        calls = []
        def raced(root, *args, **kwargs):
            if args[0] == 'push':
                calls.append(args)
                git(self.repo, 'push', str(self.remote), first + ':refs/heads/backup')
            return _git(root, *args, **kwargs)
        with mock.patch('taskcarry.remote_transfer._git', side_effect=raced):
            self.assertCode('TRANSFER_NOT_APPLIED', self.execute, plan)
        self.assertEqual(1, len(calls))
        self.assertIn('--force-with-lease=refs/heads/backup:', calls[0])
        self.assertEqual(first, out(self.remote, 'rev-parse', 'refs/heads/backup'))

    def test_existing_tag_cannot_be_replaced_and_follow_tags_never_expands_scope(self):
        tag_plan = self.plan(ref='refs/tags/review-one')
        self.execute(tag_plan)
        second = self.second_commit()
        self.assertCode('TRANSFER_TAG_CONFLICT', self.plan, ref='refs/tags/review-one', commit=second)
        git(self.repo, 'tag', '-a', 'unrelated-tag', '-m', 'must remain local')
        git(self.repo, 'config', 'push.followTags', 'true')
        branch_plan = self.plan(commit=second)
        self.execute(branch_plan)
        refs = out(self.remote, 'for-each-ref', '--format=%(refname)').splitlines()
        self.assertEqual(['refs/heads/backup', 'refs/tags/review-one'], refs)

    def test_fast_forward_only_with_current_reviewed_remote_ref(self):
        self.execute(self.plan())
        second = self.second_commit()
        next_plan = self.plan(commit=second)
        self.assertEqual(self.first, next_plan['expected_old_ref'])
        self.execute(next_plan)
        self.assertCode('TRANSFER_NOT_FAST_FORWARD', self.plan, commit=self.first)

    def test_url_and_local_wip_changes_require_a_new_plan(self):
        plan = self.plan()
        (self.repo / 'new-note.txt').write_text('new synthetic work', encoding='utf-8')
        self.assertCode('TRANSFER_SOURCE_CHANGED', self.execute, plan)
        plan = self.plan()
        other = self.root / 'other.git'
        git(self.root, 'init', '--bare', str(other))
        git(self.repo, 'remote', 'set-url', 'backup', str(other))
        self.assertCode('TRANSFER_TARGET_CHANGED', self.execute, plan)
        self.assertEqual('', out(other, 'for-each-ref', '--format=%(refname)'))

    def test_verify_detects_later_remote_changes_and_does_not_replay_old_publication(self):
        plan = self.plan()
        self.execute(plan)
        second = self.second_commit()
        git(self.repo, 'push', str(self.remote), second + ':refs/heads/backup')
        events = self.core.store.events()
        result = self.core.transfer('verify', plan_id=plan['plan_id'])
        self.assertFalse(result['verified'])
        self.assertEqual(second, result['actual_ref'])
        self.assertEqual(events, self.core.store.events())
        self.assertCode('TRANSFER_EFFECT_CHANGED', self.execute, plan)

    def test_multiple_push_urls_and_embedded_credentials_are_not_silently_transported(self):
        git(self.repo, 'remote', 'set-url', '--add', '--push', 'backup', str(self.remote))
        git(self.repo, 'remote', 'set-url', '--add', '--push', 'backup', str(self.root / 'other.git'))
        self.assertCode('TRANSFER_REMOTE', self.plan)
        git(self.repo, 'config', '--unset-all', 'remote.backup.pushurl')
        git(self.repo, 'remote', 'set-url', 'backup', 'https://synthetic-token@example.invalid/repository.git')
        self.assertCode('TRANSFER_REMOTE_CREDENTIALS', self.plan)

    def test_sealed_media_copy_has_full_hash_verification_without_cloud_claims(self):
        plan = self.copy_plan()
        target = Path(plan['destination'])
        self.assertFalse(target.exists())
        result = self.core.transfer('copy_execute', plan_id=plan['plan_id'])
        effect = result['observed_effect']
        self.assertTrue(effect['local_copy_verified'])
        self.assertFalse(effect['cloud_upload_verified'])
        self.assertFalse(effect['cloud_download_verified'])
        self.assertFalse(effect['offsite_recovery_verified'])
        names = sorted(path.relative_to(target).as_posix() for path in target.rglob('*') if path.is_file())
        self.assertEqual(sorted(item['path'] for item in plan['files']), names)
        verified = self.core.transfer('verify', plan_id=plan['plan_id'])
        self.assertTrue(verified['verified'])
        self.assertTrue(verified['state_references_verified'])

    def test_copy_interruption_resumes_original_object_selection(self):
        plan = self.copy_plan()
        from taskcarry.remote_transfer import atomic
        calls = []
        def interrupted(path, data):
            if len(calls) == 1:
                raise RuntimeError('synthetic media interruption')
            calls.append(path)
            return atomic(path, data)
        with mock.patch('taskcarry.remote_transfer.atomic', side_effect=interrupted):
            with self.assertRaises(RuntimeError):
                self.core.transfer('copy_execute', plan_id=plan['plan_id'])
        self.assertFalse((Path(plan['destination']) / 'manifest.json').exists())
        result = self.core.transfer('copy_execute', plan_id=plan['plan_id'])
        self.assertTrue(result['observed_effect']['verified'])

    def test_complete_copy_can_repair_missing_receipt_even_when_original_media_is_absent(self):
        plan = self.copy_plan()
        with mock.patch.object(self.core, '_finish', side_effect=RuntimeError('synthetic receipt crash')):
            with self.assertRaises(RuntimeError):
                self.core.transfer('copy_execute', plan_id=plan['plan_id'])
        source = Path(plan['manifest'])
        source.rename(source.with_name('retained-original.json'))
        result = self.core.transfer('copy_execute', plan_id=plan['plan_id'])
        self.assertTrue(result['receipt']['effect_reused'])

    def test_conflicting_destination_bytes_are_preserved(self):
        plan = self.copy_plan()
        target = Path(plan['destination'])
        target.mkdir(parents=True)
        collision = target / 'manifest.json'
        collision.write_text('unrelated synthetic user bytes', encoding='utf-8')
        self.assertCode('TRANSFER_DESTINATION_CONFLICT', self.core.transfer, 'copy_execute', plan_id=plan['plan_id'])
        self.assertEqual('unrelated synthetic user bytes', collision.read_text(encoding='utf-8'))
        self.assertFalse((target / 'objects').exists())

    def test_future_manifest_and_tampered_plan_are_rejected(self):
        media = self.media()
        source = Path(media['manifest'])
        import json
        content = json.loads(source.read_text(encoding='utf-8'))
        content['schema'] = 'taskcarry.project-recovery.v99'
        source.write_text(json.dumps(content), encoding='utf-8')
        self.assertCode('RECOVERY_SCHEMA_UNSUPPORTED', self.core.transfer, 'copy_plan', manifest=str(source), destination=str(self.root / 'copy'))
        plan = self.plan()
        self.core.store.put('transfer_plans', plan['plan_id'], {**plan, 'ref': 'refs/heads/other'})
        self.assertCode('TRANSFER_PLAN_CHANGED', self.execute, plan)

    def test_standby_replicas_cannot_execute_external_transfer_even_with_valid_old_plan(self):
        plan = self.plan()
        config = self.core.store.get('config', 'project')
        self.core.store.put('config', 'project', {**config, 'recovery_writer_state': 'standby'})
        self.assertCode('RECOVERY_STANDBY', self.execute, plan)
        self.assertEqual('', out(self.remote, 'for-each-ref', '--format=%(refname)'))
        self.assertFalse(self.core.transfer('verify', plan_id=plan['plan_id'])['verified'])

    def test_contract_matches_the_shared_implementation_signature(self):
        parameters = inspect.signature(RemoteTransfer.transfer).parameters
        self.assertEqual(set(parameters) - {'self'}, set(SCHEMAS['transfer']['properties']))


if __name__ == '__main__':
    unittest.main()
