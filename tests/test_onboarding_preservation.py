"""Synthetic local Git effects and resumable onboarding evidence contracts."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from taskcarry.core import Core
from taskcarry.integration import Integration
from taskcarry.onboarding import Onboarding, fingerprint
from taskcarry.preservation import Preservation, _git, _head, _index
from taskcarry.store import GovernanceError
from taskcarry.updates import Updates


class OnboardingPreservationTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / 'validation' / 'local' / 'synthetic-onboarding'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='case-', dir=parent)
        self.root = Path(self.temp.name)
        self.control = self.root / 'control'
        Core.initialize(self.control, 'Synthetic booking project')
        self.core = Core(self.control)
        self.core.task('docs', title='Synthetic documentation')
        self.save = Preservation(self.control)
        self.onboard = Onboarding(self.control)
        self.repo = self.root / 'work'
        self.repo.mkdir()
        _git(self.repo, 'init', '-b', 'main')
        _git(self.repo, 'config', 'user.name', 'Synthetic Author')
        _git(self.repo, 'config', 'user.email', 'author@example.invalid')
        _git(self.repo, 'config', 'core.autocrlf', 'false')
        for name in ('guide.txt', 'other.txt'):
            (self.repo / name).write_bytes(b'initial\n')
        _git(self.repo, 'add', '--', 'guide.txt', 'other.txt')
        _git(self.repo, 'commit', '-m', 'Initial synthetic state')
        Integration(self.control).workspace('writer', self.repo)
        self.scope = {'governance_thread': 'synthetic-governance', 'channel': 'rc',
                      'schedule': {'time': '09:00', 'timezone': 'UTC'},
                      'windows': [{'thread_id': 'synthetic-writer', 'mode': 'active', 'task_id': 'docs',
                                   'workspace': 'writer', 'source_ref': 'chat:synthetic-writer',
                                   'responsibility': 'Maintain the guide'},
                                  {'thread_id': 'synthetic-history', 'mode': 'reference',
                                   'source_ref': 'chat:synthetic-history', 'responsibility': 'Prior decisions'}]}

    def tearDown(self):
        self.temp.cleanup()

    def assertCode(self, code, call, *args, **kwargs):
        with self.assertRaises(GovernanceError) as failure:
            call(*args, **kwargs)
        self.assertEqual(code, failure.exception.code)

    def plan(self, paths=None):
        return self.save.preserve(repository=str(self.repo), paths=paths or ['guide.txt'], message='Save selected guide')

    def test_exact_commit_retains_other_staged_and_unstaged_bytes(self):
        (self.repo / 'other.txt').write_bytes(b'staged other\n')
        _git(self.repo, 'add', '--', 'other.txt')
        (self.repo / 'other.txt').write_bytes(b'unstaged other\n')
        (self.repo / 'extra.txt').write_bytes(b'untracked\n')
        (self.repo / 'guide.txt').write_bytes(b'new guide\r\n')
        staged = _git(self.repo, 'ls-files', '--stage', '--', 'other.txt').stdout
        old = _head(self.repo)
        p = self.plan()
        self.assertEqual(old, _head(self.repo))
        result = self.save.preserve('execute', plan_id=p['plan_id'])
        self.assertEqual('COMPLETED', result['state'])
        self.assertEqual(b'guide.txt\n', _git(self.repo, 'diff', '--name-only', old, result['commit']).stdout)
        self.assertEqual(b'new guide\r\n', _git(self.repo, 'show', result['commit'] + ':guide.txt').stdout)
        self.assertEqual(staged, _git(self.repo, 'ls-files', '--stage', '--', 'other.txt').stdout)
        self.assertEqual(b'unstaged other\n', (self.repo / 'other.txt').read_bytes())
        self.assertEqual(b'untracked\n', (self.repo / 'extra.txt').read_bytes())
        self.assertEqual(b'', _git(self.repo, 'diff', '--cached', '--', 'guide.txt').stdout)
        self.assertEqual('Synthetic Author <author@example.invalid>', _git(self.repo, 'log', '-1', '--format=%an <%ae>').stdout.decode().strip())
        before = self.save.store.events()
        self.assertTrue(self.save.preserve('execute', plan_id=p['plan_id'])['reused'])
        self.assertEqual(before, self.save.store.events())

    def test_no_change_does_not_create_commit_or_touch_index(self):
        before, index = _head(self.repo), _index(self.repo).read_bytes()
        result = self.save.preserve('execute', plan_id=self.plan()['plan_id'])
        self.assertFalse(result['changed'])
        self.assertEqual(before, _head(self.repo))
        self.assertEqual(index, _index(self.repo).read_bytes())

    def test_selected_staged_work_is_never_consumed(self):
        (self.repo / 'guide.txt').write_bytes(b'staged\n')
        _git(self.repo, 'add', '--', 'guide.txt')
        before = _index(self.repo).read_bytes()
        self.assertCode('PRESERVE_SELECTED_STAGED', self.plan)
        self.assertEqual(before, _index(self.repo).read_bytes())

    def test_selected_source_or_unrelated_index_change_invalidates_plan(self):
        p = self.plan()
        (self.repo / 'guide.txt').write_bytes(b'changed\n')
        self.assertCode('PRESERVE_CHANGED', self.save.preserve, 'execute', plan_id=p['plan_id'])
        p = self.plan()
        (self.repo / 'other.txt').write_bytes(b'other staged\n')
        _git(self.repo, 'add', '--', 'other.txt')
        self.assertCode('PRESERVE_CHANGED', self.save.preserve, 'execute', plan_id=p['plan_id'])

    def test_ref_effect_then_index_failure_recovers_without_duplicate_commit(self):
        (self.repo / 'guide.txt').write_bytes(b'recovered\n')
        p = self.plan()
        with mock.patch('taskcarry.preservation.os.replace', side_effect=OSError('synthetic replacement interruption')):
            with self.assertRaises(OSError):
                self.save.preserve('execute', plan_id=p['plan_id'])
        head = _head(self.repo)
        record = self.save.preserve('status', plan_id=p['plan_id'])
        self.assertEqual(head, record['candidate'])
        self.assertEqual('PREPARED', record['state'])
        (self.repo / 'guide.txt').write_bytes(b'newer uncommitted work\n')
        recovered = self.save.preserve('execute', plan_id=p['plan_id'])
        self.assertEqual(head, recovered['commit'])
        self.assertEqual(b'newer uncommitted work\n', (self.repo / 'guide.txt').read_bytes())
        self.assertEqual(b'', _git(self.repo, 'diff', '--cached', '--', 'guide.txt').stdout)

    def test_receipt_failure_rolls_back_bookkeeping_only_then_recovers(self):
        (self.repo / 'guide.txt').write_bytes(b'saved\n')
        p = self.plan()
        with mock.patch.object(self.save.store, 'event', side_effect=OSError('synthetic receipt interruption')):
            with self.assertRaises(OSError):
                self.save.preserve('execute', plan_id=p['plan_id'])
        head = _head(self.repo)
        self.assertEqual('PREPARED', self.save.preserve('status', plan_id=p['plan_id'])['state'])
        self.assertEqual(head, self.save.preserve('execute', plan_id=p['plan_id'])['commit'])

    def test_changed_index_after_interruption_is_preserved_for_review(self):
        (self.repo / 'guide.txt').write_bytes(b'saved\n')
        p = self.plan()
        with mock.patch('taskcarry.preservation.os.replace', side_effect=OSError('synthetic interruption')):
            with self.assertRaises(OSError):
                self.save.preserve('execute', plan_id=p['plan_id'])
        (self.repo / 'other.txt').write_bytes(b'new staging\n')
        _git(self.repo, 'add', '--', 'other.txt')
        index = _index(self.repo).read_bytes()
        self.assertCode('PRESERVE_REVIEW_REQUIRED', self.save.preserve, 'execute', plan_id=p['plan_id'])
        self.assertEqual(index, _index(self.repo).read_bytes())

    def test_first_commit_and_tracked_deletion(self):
        fresh = self.root / 'fresh'
        fresh.mkdir()
        _git(fresh, 'init', '-b', 'main')
        _git(fresh, 'config', 'user.name', 'Synthetic Author')
        _git(fresh, 'config', 'user.email', 'author@example.invalid')
        (fresh / 'RULES.md').write_bytes(b'governance rules\n')
        p = self.save.preserve(repository=str(fresh), paths=['RULES.md'], message='Initial rules')
        result = self.save.preserve('execute', plan_id=p['plan_id'])
        self.assertEqual(result['commit'], _head(fresh))
        (self.repo / 'guide.txt').unlink()
        p = self.plan()
        result = self.save.preserve('execute', plan_id=p['plan_id'])
        self.assertEqual(b'', _git(self.repo, 'ls-tree', result['commit'], '--', 'guide.txt').stdout)

    def test_busy_lock_and_excluded_runtime_do_not_write_git(self):
        p = self.plan()
        lock = Path(str(_index(self.repo)) + '.lock')
        lock.write_bytes(b'someone else')
        self.assertCode('PRESERVE_BUSY', self.save.preserve, 'execute', plan_id=p['plan_id'])
        self.assertEqual(b'someone else', lock.read_bytes())
        lock.unlink()
        (self.repo / 'runtime').mkdir()
        (self.repo / 'runtime/python.txt').write_text('synthetic')
        self.assertCode('PRESERVE_EXCLUDED', self.plan, ['runtime/python.txt'])

    def test_onboarding_cas_resume_and_reference_windows(self):
        first = self.onboard.onboarding('setup', 'start', self.scope)
        self.assertNotIn('window:synthetic-history', first['required'])
        self.assertFalse(first['standard_ready'])
        self.assertTrue(self.onboard.onboarding('setup', 'start', self.scope)['reused'])
        item = {'key': 'scope', 'status': 'verified', 'next_step': '',
                'evidence': {'receipt_ref': 'chat:scope-confirmed', 'user_confirmed': True,
                             'scope_fingerprint': fingerprint(self.scope)}}
        self.assertCode('ONBOARDING_CHANGED', self.onboard.onboarding, 'setup', 'update', item=item)
        result = self.onboard.onboarding('setup', 'update', item=item, expected_revision=1)
        before = self.onboard.store.events()
        self.assertTrue(self.onboard.onboarding('setup', 'update', item=item, expected_revision=1)['reused'])
        self.assertEqual(before, self.onboard.store.events())
        reopened = Onboarding(self.control).onboarding('setup')
        self.assertEqual(result, {**reopened, 'reused': False})

    def test_native_window_needs_real_binding_and_later_drift_is_detected(self):
        self.onboard.onboarding('setup', 'start', self.scope)
        evidence = {'receipt_ref': 'chat:synthetic-writer:tool-results', 'thread_id': 'synthetic-writer',
                    'task_id': 'docs', 'workspace': 'writer', 'transport': 'stdio', 'doctor_ok': True,
                    'status_ok': True, 'cwd': str(self.repo), 'control': str(self.control),
                    'runtime': {'version': '0.2.0rc7', 'interpreter': 'synthetic/python', 'module_root': 'synthetic/package'}}
        item = {'key': 'window:synthetic-writer', 'status': 'verified', 'evidence': evidence, 'next_step': ''}
        self.assertCode('ONBOARDING_BINDING', self.onboard.onboarding, 'setup', 'update', item=item, expected_revision=1)
        evidence['transport'] = 'native_mcp'
        result = self.onboard.onboarding('setup', 'update', item=item, expected_revision=1)
        self.assertNotIn(item['key'], result['pending'])
        _git(self.repo, 'checkout', '-b', 'another-task')
        result = self.onboard.onboarding('setup')
        self.assertEqual('WORKSPACE_CHANGED', result['invalidated'][item['key']]['code'])

    def test_schedule_plan_does_not_create_scheduler_and_manual_is_not_natural(self):
        self.onboard.onboarding('setup', 'start', self.scope)
        before = self.onboard.store.events()
        plan = self.onboard.schedule_plan('setup')
        self.assertFalse(plan['execute'])
        self.assertIn('releases', plan['prompt'])
        self.assertEqual(before, self.onboard.store.events())
        evidence = {'receipt_ref': 'host:readback', 'automation_id': 'synthetic-schedule', 'thread_id': plan['thread_id'],
                    'frequency': 'daily', 'time': '09:00', 'timezone': 'UTC', 'readback': True, 'active': True,
                    'kind': 'heartbeat', 'prompt_sha256': plan['prompt_sha256'],
                    'cwd': str(self.control), 'runtime_ref': 'identity:synthetic'}
        item = {'key': 'schedule_config', 'status': 'verified', 'next_step': '', 'evidence': evidence}
        self.onboard.onboarding('setup', 'update', item=item, expected_revision=1)
        trigger = {'receipt_ref': 'host:trigger', 'automation_id': 'synthetic-schedule', 'thread_id': plan['thread_id'],
                   'trigger': 'manual', 'received_at': '2026-01-01T09:00:00Z', 'run_ref': 'run:synthetic',
                   'update_check_ref': 'update:synthetic', 'local_save_ref': 'save:synthetic'}
        item = {'key': 'schedule_trigger', 'status': 'verified', 'next_step': '', 'evidence': trigger}
        self.assertCode('ONBOARDING_EVIDENCE', self.onboard.onboarding, 'setup', 'update', item=item, expected_revision=2)
        trigger['trigger'] = 'natural_heartbeat'
        result = self.onboard.onboarding('setup', 'update', item=item, expected_revision=2)
        self.assertTrue(result['natural_trigger_verified'])
        self.assertFalse(result['standard_ready'])
        self.assertFalse(result['closed_loop_verified'])

    def test_complete_standard_ready_needs_every_real_record_but_not_future_heartbeat(self):
        self.onboard.onboarding('setup', 'start', self.scope)
        saved = self.save.preserve('execute', plan_id=self.plan()['plan_id'])
        schedule = self.onboard.schedule_plan('setup')
        updates = Updates(self.control)
        updates.update_source(channel='rc')
        with mock.patch('taskcarry.updates._fetch_json', return_value=([], '0' * 64)):
            check = updates.update_check()
        assessment = updates.update_assess(check, 'keep', 'Synthetic official source returned no release.')['assessment']
        receipts = {
            'scope': {'user_confirmed': True, 'scope_fingerprint': fingerprint(self.scope)},
            'runtime': {'isolated': True, 'version': '0.2.0rc7', 'interpreter': 'synthetic/python',
                        'module_root': 'synthetic/package', 'identity_ref': 'identity:synthetic',
                        'thread_id': self.scope['governance_thread'], 'transport': 'native_mcp',
                        'doctor_ok': True, 'status_ok': True, 'control': str(self.control)},
            'local_git': {'plan_id': saved['plan_id'], 'commit': saved['commit']},
            'update_check': {'channel': 'rc', 'checked': True,
                             'source': 'https://github.com/bryan123466/taskcarry/releases',
                             'result_fingerprint': check['fingerprint'], 'assessment_ref': assessment['check_fingerprint']},
            'schedule_config': {'automation_id': 'synthetic-schedule', 'thread_id': schedule['thread_id'],
                                'time': '09:00', 'timezone': 'UTC', 'frequency': 'daily', 'kind': 'heartbeat',
                                'active': True, 'readback': True, 'prompt_sha256': schedule['prompt_sha256'],
                                'cwd': str(self.control), 'runtime_ref': 'identity:synthetic'},
            'window:synthetic-writer': {'thread_id': 'synthetic-writer', 'task_id': 'docs', 'workspace': 'writer',
                                       'transport': 'native_mcp', 'doctor_ok': True, 'status_ok': True,
                                       'cwd': str(self.repo), 'control': str(self.control),
                                       'runtime': {'version': '0.2.0rc7', 'interpreter': 'synthetic/python', 'module_root': 'synthetic/package'}}}
        revision = 1
        for key, evidence in receipts.items():
            item = {'key': key, 'status': 'verified', 'next_step': '',
                    'evidence': {**evidence, 'receipt_ref': 'synthetic-receipt:' + key}}
            result = self.onboard.onboarding('setup', 'update', item=item, expected_revision=revision)
            revision += 1
        self.assertTrue(result['standard_ready'])
        self.assertEqual([], result['pending'])
        self.assertFalse(result['natural_trigger_verified'])
        item = {'key': 'window:synthetic-writer', 'status': 'pending', 'next_step': 'Reload this one window', 'evidence': {}}
        result = self.onboard.onboarding('setup', 'update', item=item, expected_revision=revision)
        self.assertEqual(['window:synthetic-writer'], result['pending'])
        self.assertEqual('verified', result['onboarding']['items']['local_git']['status'])

    def test_unverified_local_save_and_offline_update_cannot_complete_setup(self):
        self.onboard.onboarding('setup', 'start', self.scope)
        p = self.plan()
        item = {'key': 'local_git', 'status': 'verified', 'next_step': '',
                'evidence': {'receipt_ref': 'synthetic:plan-only', 'plan_id': p['plan_id'], 'commit': p['head']}}
        self.assertCode('ONBOARDING_EVIDENCE', self.onboard.onboarding, 'setup', 'update', item=item, expected_revision=1)
        updates = Updates(self.control)
        updates.update_source(channel='rc')
        with mock.patch('taskcarry.updates._fetch_json', side_effect=OSError('Synthetic network unavailable')):
            check = updates.update_check()
        updates.update_assess(check, 'wait', 'Wait for an actual online check.')
        item = {'key': 'update_check', 'status': 'verified', 'next_step': '',
                'evidence': {'receipt_ref': 'synthetic:offline', 'channel': 'rc', 'checked': True,
                             'source': 'https://github.com/bryan123466/taskcarry/releases',
                             'result_fingerprint': check['fingerprint'], 'assessment_ref': check['fingerprint']}}
        self.assertCode('ONBOARDING_EVIDENCE', self.onboard.onboarding, 'setup', 'update', item=item, expected_revision=1)

    def test_governance_window_requires_its_own_native_acceptance(self):
        self.onboard.onboarding('setup', 'start', self.scope)
        evidence = {'receipt_ref': 'synthetic:cli-runtime', 'isolated': True, 'version': '0.2.0rc7',
                    'interpreter': 'synthetic/python', 'module_root': 'synthetic/package',
                    'identity_ref': 'identity:synthetic', 'thread_id': self.scope['governance_thread'],
                    'transport': 'cli', 'doctor_ok': True, 'status_ok': True, 'control': str(self.control)}
        item = {'key': 'runtime', 'status': 'verified', 'next_step': '', 'evidence': evidence}
        self.assertCode('ONBOARDING_BINDING', self.onboard.onboarding, 'setup', 'update', item=item, expected_revision=1)
        evidence['transport'] = 'native_mcp'
        evidence['thread_id'] = 'synthetic-writer'
        self.assertCode('ONBOARDING_BINDING', self.onboard.onboarding, 'setup', 'update', item=item, expected_revision=1)
        evidence['thread_id'] = self.scope['governance_thread']
        result = self.onboard.onboarding('setup', 'update', item=item, expected_revision=1)
        self.assertNotIn('runtime', result['pending'])

    def test_update_evidence_requires_stored_current_assessment(self):
        self.onboard.onboarding('setup', 'start', self.scope)
        evidence = {'receipt_ref': 'synthetic:update', 'checked': True, 'channel': 'rc',
                    'source': 'https://github.com/bryan123466/taskcarry/releases',
                    'result_fingerprint': 'synthetic-unrecorded', 'assessment_ref': 'synthetic-unrecorded'}
        item = {'key': 'update_check', 'status': 'verified', 'next_step': '', 'evidence': evidence}
        self.assertCode('ONBOARDING_EVIDENCE', self.onboard.onboarding, 'setup', 'update', item=item, expected_revision=1)
        updates = Updates(self.control)
        updates.update_source(channel='rc')
        with mock.patch('taskcarry.updates._fetch_json', return_value=([], '0' * 64)):
            check = updates.update_check()
        assessment = updates.update_assess(check, 'keep', 'Synthetic empty official query.')['assessment']
        evidence.update(result_fingerprint=check['fingerprint'], assessment_ref=assessment['check_fingerprint'])
        self.onboard.onboarding('setup', 'update', item=item, expected_revision=1)
        updates.update_source(channel='stable', expected_revision=1)
        result = self.onboard.onboarding('setup')
        self.assertEqual('ONBOARDING_EVIDENCE', result['invalidated']['update_check']['code'])

    def test_missing_author_never_fabricates_identity(self):
        _git(self.repo, 'config', 'user.name', '')
        self.assertCode('GIT_AUTHOR_REQUIRED', self.plan)
        self.assertEqual([], self.save.store.list('preservation'))

    def test_same_content_new_plan_reuses_without_new_version(self):
        (self.repo / 'guide.txt').write_bytes(b'new content\n')
        first = self.save.preserve('execute', plan_id=self.plan()['plan_id'])
        second = self.save.preserve('execute', plan_id=self.plan()['plan_id'])
        self.assertFalse(second['changed'])
        self.assertEqual(first['commit'], second['commit'])

    def test_explicit_synthetic_remote_roundtrip_keeps_exact_commit_and_bytes(self):
        (self.repo / 'guide.txt').write_bytes(b'exact saved bytes\r\n')
        result = self.save.preserve('execute', plan_id=self.plan()['plan_id'])
        remote = self.root / 'remote.git'
        _git(self.root, 'init', '--bare', str(remote))
        # Explicit external transport is separate from the local save engine.
        _git(self.repo, 'push', str(remote), result['commit'] + ':refs/heads/main')
        fetched = self.root / 'download'
        _git(self.root, 'clone', '--branch', 'main', '--no-hardlinks', str(remote), str(fetched))
        self.assertEqual(result['commit'], _head(fetched))
        self.assertEqual(b'exact saved bytes\r\n', _git(fetched, 'show', 'HEAD:guide.txt').stdout)
        self.assertFalse(result['remote_backup'])

    def test_execution_cannot_silently_ignore_an_alternate_target(self):
        p = self.plan()
        before = _head(self.repo)
        self.assertCode('PRESERVE_ARGUMENT', self.save.preserve, 'execute', repository=str(self.root), plan_id=p['plan_id'])
        self.assertEqual(before, _head(self.repo))
        self.onboard.onboarding('setup', 'start', self.scope)
        self.assertCode('ONBOARDING_ACTION', self.onboard.onboarding, 'setup', 'status', scope=self.scope)


if __name__ == '__main__':
    unittest.main()
