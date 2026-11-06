"""Observable recovery, source preservation and fail-closed synthetic cases."""
import copy
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest import mock

from taskcarry.core import Core
from taskcarry.integration import Integration
from taskcarry.project_recovery import ProjectRecovery
from taskcarry.recovery_files import atomic, digest, encoded, read_json
from taskcarry.recovery_git import git
from taskcarry.store import GovernanceError


class ProjectRecoveryTests(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).resolve().parents[1] / 'validation' / 'local'
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='recovery-test-', dir=base)
        self.root = Path(self.temp.name)
        self.control = self.root / 'brain'
        Core.initialize(self.control, 'Synthetic booking service')
        self.core = Core(self.control)
        self.core.task('booking', 'Finish booking flow')
        self.recovery = ProjectRecovery(self.control)
        self.repo = self.root / 'booking'
        self.repo.mkdir()
        git(self.repo, 'init', '--quiet', '-b', 'main')
        git(self.repo, 'config', 'user.name', 'Synthetic Author')
        git(self.repo, 'config', 'user.email', 'author@example.invalid')
        (self.repo / 'app.txt').write_bytes(b'first\n')
        (self.repo / 'remove.txt').write_bytes(b'remove me\n')
        (self.repo / '.gitignore').write_bytes(b'ignored/\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'Initial synthetic history')
        self.first = git(self.repo, 'rev-parse', 'HEAD').strip()
        (self.repo / 'app.txt').write_bytes(b'committed\n')
        git(self.repo, 'commit', '-qam', 'Second real ancestor')
        git(self.repo, 'tag', 'synthetic-v1')
        Integration(self.control).workspace('developer', str(self.repo))
        (self.repo / 'app.txt').write_bytes(b'staged\n')
        git(self.repo, 'add', 'app.txt')
        (self.repo / 'app.txt').write_bytes(b'unstaged\n')
        (self.repo / 'remove.txt').unlink()
        (self.repo / 'draft.txt').write_bytes(b'untracked chosen\n')
        (self.repo / 'excluded.txt').write_bytes(b'unselected\n')
        (self.repo / 'ignored').mkdir()
        (self.repo / 'ignored' / 'private.txt').write_bytes(b'do not select\n')
        self.checkpoint = self.core.checkpoint('booking', str(self.repo), ['app.txt', 'draft.txt'], 'Review booking draft')
        self.before = self.observe_source()

    def tearDown(self):
        self.temp.cleanup()

    def observe_source(self):
        return {'head': git(self.repo, 'rev-parse', 'HEAD'),
                'index': (self.repo / '.git' / 'index').read_bytes(),
                'status': git(self.repo, 'status', '--porcelain=v1', '-z'),
                'file': (self.repo / 'app.txt').read_bytes()}

    def assertCode(self, code, callback, *args, **kwargs):
        with self.assertRaises(GovernanceError) as result:
            callback(*args, **kwargs)
        self.assertEqual(code, result.exception.code)

    def backup(self, **kwargs):
        plan = self.recovery.recovery('backup_plan', destination=str(self.root / 'media'),
                                      workspaces=[{'name': 'developer', 'paths': ['draft.txt']}], **kwargs)
        result = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        return plan, result

    def restore(self, backup):
        # Restore controller has no initialized state and no access to the old brain.
        fresh = ProjectRecovery(self.root / 'restore-controller')
        plan = fresh.recovery('restore_plan', manifest=backup['manifest'], expected_sha256=backup['manifest_sha256'],
                              destination=str(self.root / 'recovered'))
        result = fresh.recovery('restore_execute', plan_id=plan['plan_id'])
        return fresh, plan, result

    def integration_fixture(self):
        control = self.root / 'integration-brain'
        Core.initialize(control, 'Synthetic restored delivery service')
        core, engine = Core(control), Integration(control)
        core.task('service', 'Deliver service improvements')
        baseline, worker = self.root / 'baseline', self.root / 'worker'
        baseline.mkdir()
        git(baseline, 'init', '--quiet', '-b', 'main')
        for name, value in [('user.name', 'Synthetic Author'), ('user.email', 'author@example.invalid')]:
            git(baseline, 'config', name, value)
        (baseline / 'service.txt').write_bytes(b'first\n')
        git(baseline, 'add', 'service.txt')
        git(baseline, 'commit', '-qm', 'Initial service')
        origin = git(baseline, 'rev-parse', 'HEAD').decode().strip()
        git(self.root, 'clone', '--quiet', '--no-hardlinks', str(baseline), str(worker))
        for name, value in [('user.name', 'Synthetic Author'), ('user.email', 'author@example.invalid')]:
            git(worker, 'config', name, value)
        engine.workspace('baseline', baseline)
        engine.workspace('worker', worker)
        (worker / 'service.txt').write_bytes(b'first\nreceived\n')
        git(worker, 'commit', '-qam', 'First delivery')
        tip = git(worker, 'rev-parse', 'HEAD').decode().strip()
        engine.submit('service', 'worker', tip, origin, ['service.txt'], stage_id='service-one')
        plan = engine.reconcile('baseline')['plan']
        self.assertEqual('COMPLETE', engine.reconcile('baseline', True, plan['plan_id'])['status'])
        return control, core, engine, baseline, worker, origin

    def activate_restored(self, control):
        recovery = ProjectRecovery(control)
        plan = recovery.recovery('activation_plan')
        evidence = {'source_id': recovery.source()['source_id'], 'replica_id': recovery.source()['replica_id'],
                    'control': str(recovery.root), 'doctor': True, 'status': True, 'evidence_ref': 'synthetic-native-attestation'}
        recovery.recovery('activate', plan_id=plan['plan_id'], authorization='Synthetic exact-replica handoff',
                          old_writer_stopped=True, old_replica_id=plan['old_replica_id'], native_evidence=evidence)
        return recovery

    def test_restored_bound_baseline_accepts_new_delivery_and_new_plans(self):
        from taskcarry.api import invoke
        control, core, engine, baseline, worker, origin = self.integration_fixture()
        old_binding = core.store.get('settings', 'integration_baseline')
        first_stage = core.store.get('stages', 'service-one')
        core.store.put('operations', 'historical-superseded',
                       {'operation_id': 'historical-superseded', 'kind': 'reconcile', 'baseline': str(baseline),
                        'status': 'SUPERSEDED', 'plan_id': 'historical-plan'})
        old_reconcile = engine.reconcile('baseline')['plan']
        old_adopt = engine.adopt('worker', 'baseline')['plan']
        self.assertEqual([], old_reconcile['pending_operations'])
        self.assertNotIn('recovery_context', old_reconcile)
        self.assertNotIn('recovery_context', old_adopt)
        old_head = git(baseline, 'rev-parse', 'HEAD')
        recovery = ProjectRecovery(control)
        backup_plan = recovery.recovery('backup_plan', destination=str(self.root / 'integration-media'),
                                        workspaces=[{'name': 'baseline'}, {'name': 'worker'}])
        backup = recovery.recovery('backup_execute', plan_id=backup_plan['plan_id'])
        _, _, result = self.restore(backup)
        restored = self.activate_restored(result['effect']['control'])
        new_base = Path(restored.store.get('workspaces', 'baseline')['path'])
        new_worker = Path(restored.store.get('workspaces', 'worker')['path'])
        plan = invoke(restored.root, 'reconcile', {'baseline': 'baseline'})['plan']
        self.assertNotEqual(old_reconcile['plan_id'], plan['plan_id'])
        self.assertEqual(restored.source()['replica_id'], plan['recovery_context']['replica_id'])
        self.assertCode('RESTORED_PLAN_INERT', invoke, restored.root, 'reconcile',
                        {'baseline': 'baseline', 'execute': True, 'plan_id': old_reconcile['plan_id']})
        self.assertEqual('COMPLETE', invoke(restored.root, 'reconcile',
                                          {'baseline': 'baseline', 'execute': True, 'plan_id': plan['plan_id']})['status'])
        adoption = invoke(restored.root, 'adopt', {'workspace': 'worker', 'baseline': 'baseline'})['plan']
        self.assertNotEqual(old_adopt['plan_id'], adoption['plan_id'])
        self.assertCode('RESTORED_PLAN_INERT', invoke, restored.root, 'adopt',
                        {'workspace': 'worker', 'baseline': 'baseline', 'execute': True, 'plan_id': old_adopt['plan_id']})
        invoke(restored.root, 'adopt', {'workspace': 'worker', 'baseline': 'baseline', 'execute': True, 'plan_id': adoption['plan_id']})
        for name, value in [('user.name', 'Synthetic Author'), ('user.email', 'author@example.invalid')]:
            git(new_worker, 'config', name, value)
        (new_worker / 'service.txt').write_bytes(b'first\nreceived\nnew restored work\n')
        git(new_worker, 'commit', '-qam', 'Restored second delivery')
        tip = git(new_worker, 'rev-parse', 'HEAD').decode().strip()
        invoke(restored.root, 'submit', {'task_id': 'service', 'workspace': 'worker', 'commit': tip,
                                        'base': origin, 'paths': ['service.txt'], 'stage_id': 'service-two',
                                        'relation': 'cumulative', 'supersedes': ['service-one']})
        new_plan = invoke(restored.root, 'reconcile', {'baseline': 'baseline'})['plan']
        received = invoke(restored.root, 'reconcile', {'baseline': 'baseline', 'execute': True, 'plan_id': new_plan['plan_id']})
        self.assertEqual('COMPLETE', received['status'])
        self.assertEqual('first\nreceived\nnew restored work\n', (new_base / 'service.txt').read_text(encoding='utf-8'))
        self.assertEqual(b'first\nreceived\nnew restored work\n', git(new_base, 'show', 'HEAD:service.txt'))
        self.assertEqual('COMMITTED', restored.store.get('stages', 'service-two')['status'])
        operation = restored.store.get('operations', restored.store.get('stages', 'service-two')['operation_id'])
        self.assertEqual(first_stage['commit'], operation['effective_base'])
        self.assertEqual(old_head, git(baseline, 'rev-parse', 'HEAD'))
        self.assertEqual(old_binding, core.store.get('settings', 'integration_baseline'))
        archived = restored.recovery('history', collection='settings', local_id='integration_baseline')['items']
        self.assertEqual(old_binding, archived[0]['record'])
        archived_stage = restored.recovery('history', collection='stages', local_id='service-one')['items']
        self.assertEqual(first_stage, archived_stage[0]['record'])
        self.assertTrue(backup['verification']['complete_scope'])
        self.assertTrue(result['effect']['complete_scope'])

    def test_omitted_bound_baseline_is_incomplete_and_cannot_receive_elsewhere(self):
        from taskcarry.api import invoke
        control, core, engine, baseline, worker, origin = self.integration_fixture()
        old_binding = core.store.get('settings', 'integration_baseline')
        old_head = git(baseline, 'rev-parse', 'HEAD')
        recovery = ProjectRecovery(control)
        plan = recovery.recovery('backup_plan', destination=str(self.root / 'partial-media'), workspaces=[{'name': 'worker'}])
        backup = recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertTrue(backup['verification']['verified'])
        self.assertFalse(backup['verification']['complete_scope'])
        self.assertEqual('REBIND_REQUIRED', backup['verification']['integration_baseline_recovery']['status'])
        _, _, result = self.restore(backup)
        self.assertFalse(result['effect']['complete_scope'])
        restored = self.activate_restored(result['effect']['control'])
        self.assertIsNone(restored.store.get('settings', 'integration_baseline'))
        self.assertEqual(old_binding, restored.recovery('history', collection='settings', local_id='integration_baseline')['items'][0]['record'])
        for name in ('baseline', 'worker'):
            self.assertCode('RECOVERY_BASELINE_REBIND_REQUIRED', invoke, restored.root, 'reconcile', {'baseline': name})
        self.assertEqual(old_head, git(baseline, 'rev-parse', 'HEAD'))
        self.assertEqual(old_binding, core.store.get('settings', 'integration_baseline'))

    def test_history_index_worktree_and_state_restore_to_other_directory(self):
        git(self.repo, 'update-ref', 'refs/remotes/example/main', self.before['head'].decode().strip())
        git(self.repo, 'symbolic-ref', 'refs/remotes/example/HEAD', 'refs/remotes/example/main')
        _, backup = self.backup()
        fresh, plan, result = self.restore(backup)
        target = Path(result['effect']['control']).parent / 'workspaces' / 'developer'
        self.assertEqual(self.before, self.observe_source())
        self.assertEqual(self.before['head'], git(target, 'rev-parse', 'HEAD'))
        self.assertEqual(self.first, git(target, 'rev-parse', 'HEAD~1').strip())
        self.assertEqual(git(self.repo, 'show-ref'), git(target, 'show-ref'))
        self.assertEqual(b'refs/remotes/example/main\n', git(target, 'symbolic-ref', 'refs/remotes/example/HEAD'))
        self.assertEqual(b'staged\n', git(target, 'show', ':app.txt'))
        self.assertEqual(b'unstaged\n', (target / 'app.txt').read_bytes())
        self.assertEqual(b'untracked chosen\n', (target / 'draft.txt').read_bytes())
        self.assertFalse((target / 'remove.txt').exists())
        self.assertFalse((target / 'excluded.txt').exists())
        self.assertFalse((target / 'ignored').exists())
        restored = Core(result['effect']['control'])
        self.assertEqual(self.checkpoint, restored.store.get('checkpoints', self.checkpoint['checkpoint_id']))
        self.assertEqual(str(target), restored.store.get('workspaces', 'developer')['path'])
        self.assertEqual('standby', restored.store.get('config', 'project')['recovery_writer_state'])
        self.assertNotEqual(self.core.source()['replica_id'], restored.source()['replica_id'])
        self.assertEqual(self.core.source()['source_id'], restored.source()['source_id'])
        self.assertTrue(result['effect']['git_verified'])
        self.assertTrue(result['effect']['state_verified'])
        self.assertTrue(fresh.recovery('status', plan_id=plan['plan_id'])['observed_effect']['state_verified'])
        self.assertFalse((Path(result['effect']['control']) / '.codex' / 'config.toml').exists())

    def test_plain_research_payload_and_legacy_identity(self):
        plain = self.root / 'research'
        plain.mkdir()
        (plain / 'notes.md').write_text('Synthetic interview themes', encoding='utf-8')
        config = self.core.store.get('config', 'project')
        config.pop('project_id', None); config.pop('replica_id', None)
        self.core.store.put('config', 'project', config)
        _, backup = self.backup(payloads=[{'name': 'notes', 'path': str(plain), 'paths': ['notes.md']}])
        _, plan, result = self.restore(backup)
        restored = Core(result['effect']['control'])
        self.assertTrue(restored.source()['source_id'].startswith('project-'))
        self.assertTrue(any(a.startswith('local-') for a in restored.source()['aliases']))
        self.assertEqual('Synthetic interview themes', (Path(plan['destination']) / 'payloads' / 'notes' / 'notes.md').read_text())

    def test_missing_state_object_fails_before_publication(self):
        ref = self.checkpoint['files'][0]['worktree']
        (self.control / '.taskcarry' / 'objects' / ref['sha256']).unlink()
        plan = self.recovery.recovery('backup_plan', destination=str(self.root / 'media'))
        self.assertCode('RECOVERY_OBJECT_MISSING', self.recovery.recovery, 'backup_execute', plan_id=plan['plan_id'])
        self.assertFalse((self.root / 'media' / 'manifest.json').exists())

    def test_missing_or_tampered_package_object_is_reported(self):
        _, backup = self.backup()
        value = json.loads(Path(backup['manifest']).read_text())
        ref = value['state']['objects'][0]
        (Path(backup['manifest']).parent / 'objects' / ref['sha256']).write_bytes(b'wrong')
        result = self.recovery.recovery('verify', manifest=backup['manifest'])
        self.assertFalse(result['verified'])
        self.assertEqual('RECOVERY_OBJECT_MISMATCH', result['failures'][0]['code'])
        self.assertCode('RECOVERY_VERIFY_FAILED', self.restore, backup)

    def test_future_schema_and_traversal_rejected(self):
        _, backup = self.backup()
        path = Path(backup['manifest'])
        value = json.loads(path.read_text())
        changed = copy.deepcopy(value)
        changed['schema'] = 'taskcarry.project-recovery.v900'
        path.write_bytes(encoded(changed))
        self.assertCode('RECOVERY_SCHEMA_UNSUPPORTED', self.recovery.recovery, 'verify', manifest=str(path))
        changed = copy.deepcopy(value)
        changed['components'][0]['files'][0]['path'] = '../escape.txt'
        path.write_bytes(encoded(changed))
        self.assertCode('RECOVERY_UNSAFE_PATH', self.recovery.recovery, 'verify', manifest=str(path))

    def test_mismatched_manifest_digest_rejected(self):
        _, backup = self.backup()
        self.assertCode('RECOVERY_MANIFEST_MISMATCH', self.recovery.recovery, 'verify',
                        manifest=backup['manifest'], expected_sha256='0' * 64)

    def test_capture_effect_without_receipt_reuses_original_batch(self):
        plan = self.recovery.recovery('backup_plan', destination=str(self.root / 'media'),
                                      workspaces=[{'name': 'developer', 'paths': ['draft.txt']}])
        with mock.patch.object(self.recovery, '_receipt', side_effect=RuntimeError('receipt interruption')):
            with self.assertRaises(RuntimeError):
                self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        (self.repo / 'app.txt').write_bytes(b'later legal work\n')
        resumed = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertTrue(resumed['reused_original_batch'])
        _, _, result = self.restore(resumed)
        self.assertEqual(b'unstaged\n', (Path(result['effect']['control']).parent / 'workspaces' / 'developer' / 'app.txt').read_bytes())
        self.assertEqual(b'later legal work\n', (self.repo / 'app.txt').read_bytes())

    def test_restore_effect_without_receipt_is_verified_before_finalizing(self):
        _, backup = self.backup()
        controller = ProjectRecovery(self.root / 'new-controller')
        plan = controller.recovery('restore_plan', manifest=backup['manifest'], destination=str(self.root / 'recovered'))
        with mock.patch.object(controller, '_receipt', side_effect=RuntimeError('interrupted final receipt')):
            with self.assertRaises(RuntimeError):
                controller.recovery('restore_execute', plan_id=plan['plan_id'])
        result = controller.recovery('restore_execute', plan_id=plan['plan_id'])
        self.assertTrue(result['recovered_existing_effect'])
        target = Path(result['effect']['control']).parent / 'workspaces' / 'developer' / 'app.txt'
        target.write_bytes(b'later destination edits\n')
        self.assertCode('RECOVERY_EFFECT_CHANGED', controller.recovery, 'restore_execute', plan_id=plan['plan_id'])
        self.assertEqual(b'later destination edits\n', target.read_bytes())

    def test_source_change_after_plan_does_not_get_new_capture_identity(self):
        plan = self.recovery.recovery('backup_plan', destination=str(self.root / 'media'), workspaces=[{'name': 'developer'}])
        (self.repo / 'app.txt').write_bytes(b'changed after plan\n')
        self.assertCode('RECOVERY_SOURCE_CHANGED', self.recovery.recovery, 'backup_execute', plan_id=plan['plan_id'])
        self.assertFalse((self.root / 'media' / 'manifest.json').exists())

    def test_partial_atomic_file_cannot_become_a_final_object(self):
        target = self.root / 'object'
        real_replace = os.replace
        with mock.patch('taskcarry.recovery_files.os.replace', side_effect=OSError('simulated interruption')):
            with self.assertRaises(OSError):
                atomic(target, b'exact bytes')
        self.assertFalse(target.exists())
        self.assertTrue(list(self.root.glob('object.*.partial')))
        atomic(target, b'exact bytes')
        self.assertEqual(b'exact bytes', target.read_bytes())

    def test_standby_old_plans_and_activation_require_exact_handoff(self):
        old = {'plan_id': 'old-plan', 'kind': 'reconcile', 'operation_protocol': 1, 'state': 'PLANNED'}
        self.core.store.put('plans', 'old-plan', old)
        self.core.store.put('operations', 'old-op', {'operation_id': 'old-op', 'plan_id': 'old-plan', 'status': 'PREPARED'})
        _, backup = self.backup()
        _, _, result = self.restore(backup)
        recovered = ProjectRecovery(result['effect']['control'])
        self.assertIsNone(recovered.store.get('plans', 'old-plan'))
        self.assertEqual(old, recovered.recovery('history', collection='plans', local_id='old-plan')['items'][0]['record'])
        self.assertEqual('SUPERSEDED', recovered.store.get('operations', 'old-op')['status'])
        self.assertCode('RECOVERY_STANDBY', recovered.task, 'new')
        activation = recovered.recovery('activation_plan')
        self.assertCode('RECOVERY_HANDOFF_REQUIRED', recovered.recovery, 'activate', plan_id=activation['plan_id'])
        evidence = {'source_id': recovered.source()['source_id'], 'replica_id': recovered.source()['replica_id'],
                    'control': str(recovered.root), 'doctor': True, 'status': True, 'evidence_ref': 'synthetic-native-receipt'}
        activated = recovered.recovery('activate', plan_id=activation['plan_id'], authorization='Synthetic test authorizes this exact replica',
                                        old_writer_stopped=True, old_replica_id=activation['old_replica_id'], native_evidence=evidence)
        self.assertTrue(activated['writer_activated'])
        self.assertFalse(activated['native_evidence_independently_verified'])
        self.assertFalse(activated['automations_enabled'])
        self.assertEqual('new', recovered.task('new')['task_id'])
        from taskcarry.api import invoke
        self.assertCode('RESTORED_PLAN_INERT', invoke, recovered.root, 'reconcile', {'baseline': 'developer', 'execute': True, 'plan_id': 'old-plan'})

    def test_legacy_checkpoint_restore_without_plan_id_cannot_replay(self):
        destination = self.root / 'old-restore-destination'
        cp = self.checkpoint
        operation_id = 'restore-' + self.core._restore_digest([cp['checkpoint_id'], os.path.normcase(str(destination))])[:24]
        old = {'operation_id': operation_id, 'kind': 'restore', 'operation_protocol': 1, 'restore_protocol': 1,
               'checkpoint_id': cp['checkpoint_id'], 'checkpoint_sha256': self.core._restore_digest(cp),
               'destination': str(destination), 'status': 'PREPARED', 'effect_state': 'NOT_APPLIED'}
        self.core.store.put('operations', operation_id, old)
        _, backup = self.backup()
        _, _, result = self.restore(backup)
        restored = Core(result['effect']['control'])
        self.assertEqual('SUPERSEDED', restored.store.get('operations', operation_id)['status'])
        with restored.store.recovery_transition():
            self.assertCode('RESTORE_REVIEW_REQUIRED', restored.restore, cp['checkpoint_id'], str(destination))
        self.assertFalse(destination.exists())
        history = ProjectRecovery(restored.root).recovery('history', collection='operations', local_id=operation_id)
        self.assertEqual(old, history['items'][0]['record'])

    def test_standby_full_records_and_events_are_checked(self):
        _, backup = self.backup()
        controller, plan, result = self.restore(backup)
        restored = Core(result['effect']['control'])
        with restored.store.recovery_transition():
            restored.store.put('tasks', 'booking', {'task_id': 'booking', 'title': 'Tampered current task'})
        self.assertCode('RECOVERY_EFFECT_CHANGED', controller.recovery, 'restore_execute', plan_id=plan['plan_id'])
        self.assertCode('RECOVERY_EFFECT_CHANGED', ProjectRecovery(restored.root).recovery, 'activation_plan')

    def test_old_runtime_reservations_and_key_only_plans_are_archived(self):
        self.core.store.put('workbench_plans', 'old-workbench', {'object': {'target': 'old location'}})
        self.core.store.put('governance_cycles', 'old-cycle', {'cycle_id': 'old-cycle', 'state': 'active'})
        self.core.store.put('cycle_reservations', 'resource', {'cycle_id': 'old-cycle', 'state': 'reserved'})
        self.core.store.put('runs', 'old-run', {'run_id': 'old-run', 'state': 'active'})
        _, backup = self.backup()
        _, _, result = self.restore(backup)
        store = Core(result['effect']['control']).store
        self.assertEqual([], store.list('cycle_reservations'))
        self.assertIsNone(store.get('workbench_plans', 'old-workbench'))
        self.assertEqual('active', ProjectRecovery(store.root).recovery('history', collection='governance_cycles', local_id='old-cycle')['items'][0]['record']['state'])
        config = store.get('config', 'project')
        self.assertIn('old-workbench', config['recovery_inert_plan_ids'])
        self.assertIn('old-cycle', config['recovery_inert_cycle_ids'])
        self.assertIn('old-run', config['recovery_inert_run_ids'])

    def test_missing_registered_workspace_or_artifact_is_an_explicit_gap(self):
        plain = self.root / 'external'
        plain.mkdir()
        artifact = plain / 'source.md'
        artifact.write_bytes(b'selected separately')
        self.core.artifact('booking', str(artifact))
        plan = self.recovery.recovery('backup_plan', destination=str(self.root / 'media'))
        backup = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertTrue(backup['verification']['verified'])
        self.assertFalse(backup['verification']['complete_scope'])
        self.assertEqual(['developer'], backup['verification']['missing_workspace_payloads'])
        self.assertEqual(str(artifact), backup['verification']['missing_artifact_payloads'][0]['path'])

    def test_tracked_and_untracked_native_configs_are_quarantined(self):
        (self.repo / '.codex').mkdir()
        config = b'[mcp_servers.example]\ncommand = "old-runtime"\n'
        (self.repo / '.codex' / 'config.toml').write_bytes(config)
        git(self.repo, 'add', '.codex/config.toml')
        (self.repo / '.mcp.json').write_bytes(b'{"old": "binding"}')
        plan = self.recovery.recovery('backup_plan', destination=str(self.root / 'media'),
                                      workspaces=[{'name': 'developer', 'paths': ['draft.txt', '.mcp.json']}])
        backup = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        controller, restore_plan, result = self.restore(backup)
        target = Path(result['effect']['control']).parent / 'workspaces' / 'developer'
        self.assertFalse((target / '.codex' / 'config.toml').exists())
        self.assertFalse((target / '.mcp.json').exists())
        self.assertEqual(config, (target / '.taskcarry-disabled-host' / '.codex' / 'config.toml').read_bytes())
        self.assertEqual(config, git(target, 'show', ':.codex/config.toml'))
        self.assertEqual(2, len(result['effect']['disabled_host_files']))
        (target / '.taskcarry-disabled-host' / '.codex' / 'config.toml').write_bytes(b'later edit')
        self.assertCode('RECOVERY_EFFECT_CHANGED', controller.recovery, 'restore_execute', plan_id=restore_plan['plan_id'])

    def test_declared_state_objects_cannot_omit_a_referenced_object(self):
        _, backup = self.backup()
        path = Path(backup['manifest'])
        value = json.loads(path.read_text())
        value['state']['objects'].pop()
        path.write_bytes(encoded(value))
        result = self.recovery.recovery('verify', manifest=str(path))
        self.assertFalse(result['verified'])
        self.assertEqual('RECOVERY_STATE_REFERENCE_MISSING', result['failures'][0]['code'])

    def test_restore_interruption_before_publication_reuses_prepared_build(self):
        _, backup = self.backup()
        controller = ProjectRecovery(self.root / 'new-controller')
        plan = controller.recovery('restore_plan', manifest=backup['manifest'], destination=str(self.root / 'recovered'))
        with mock.patch('taskcarry.project_recovery.os.rename', side_effect=OSError('publication interrupted')):
            with self.assertRaises(OSError):
                controller.recovery('restore_execute', plan_id=plan['plan_id'])
        prepared_path = controller._plan_path(plan['plan_id']).with_suffix('.prepared.json')
        original = prepared_path.read_bytes()
        result = controller.recovery('restore_execute', plan_id=plan['plan_id'])
        self.assertEqual(original, prepared_path.read_bytes())
        self.assertTrue(result['effect']['state_verified'])

    def test_selected_refs_report_uncovered_delivery_history(self):
        tree = git(self.repo, 'rev-parse', 'HEAD^{tree}').strip().decode()
        isolated = git(self.repo, 'commit-tree', tree, data=b'Independent synthetic history\n').strip().decode()
        git(self.repo, 'update-ref', 'refs/heads/independent', isolated)
        self.core.store.put('stages', 'isolated', {'stage_id': 'isolated', 'task_id': 'booking', 'workspace': 'developer',
                                                 'commit': isolated, 'base': self.first.decode(), 'status': 'QUEUED'})
        plan = self.recovery.recovery('backup_plan', destination=str(self.root / 'media'),
                                      workspaces=[{'name': 'developer', 'refs': ['refs/heads/main']}])
        backup = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertTrue(backup['verification']['verified'])
        self.assertFalse(backup['verification']['complete_scope'])
        self.assertEqual([isolated], backup['verification']['missing_history_dependencies'][0]['commits'])

    def test_future_actual_state_schema_is_rejected(self):
        _, backup = self.backup()
        path = Path(backup['manifest'])
        value = json.loads(path.read_text())
        snapshot = path.parent / 'objects' / value['state']['snapshot']['sha256']
        changed = self.root / 'future.sqlite3'
        shutil.copyfile(snapshot, changed)
        with closing(sqlite3.connect(changed)) as db:
            config = json.loads(db.execute("SELECT value FROM records WHERE collection='config' AND key='project'").fetchone()[0])
            config['schema_version'] = 900
            db.execute("UPDATE records SET value=? WHERE collection='config' AND key='project'", (json.dumps(config),))
            db.commit()
        data = changed.read_bytes()
        from taskcarry.recovery_files import put
        value['state']['snapshot'] = put(path.parent, data)
        path.write_bytes(encoded(value))
        self.assertCode('SCHEMA_VERSION_UNSUPPORTED', self.recovery.recovery, 'verify', manifest=str(path))

    def test_plain_research_brain_recovery_does_not_require_git(self):
        brain = self.root / 'research-brain'
        Core.initialize(brain, 'Synthetic interview study')
        Core(brain).task('themes', 'Review interview themes')
        files = self.root / 'study'
        files.mkdir()
        (files / 'themes.md').write_bytes(b'Interview themes without a repository\n')
        source = ProjectRecovery(brain)
        with mock.patch('taskcarry.recovery_git.git', side_effect=AssertionError('Git must not be invoked')):
            plan = source.recovery('backup_plan', destination=str(self.root / 'research-media'),
                                   workspaces=[{'name': 'research', 'path': str(files), 'kind': 'files', 'paths': ['themes.md']}])
            backup = source.recovery('backup_execute', plan_id=plan['plan_id'])
            self.assertFalse(backup['verification']['runtime']['git_required'])
            self.assertTrue(backup['verification']['complete_scope'])
            _, _, result = self.restore(backup)
        restored = Core(result['effect']['control'])
        self.assertEqual('Review interview themes', restored.store.get('tasks', 'themes')['title'])
        self.assertEqual(b'Interview themes without a repository\n',
                         (Path(result['effect']['control']).parent / 'workspaces' / 'research' / 'themes.md').read_bytes())

    def test_second_generation_restore_preserves_prior_archived_history(self):
        _, backup = self.backup()
        _, _, first = self.restore(backup)
        first_control = Path(first['effect']['control'])
        source = ProjectRecovery(first_control)
        old_history = source.recovery('history', collection='config', local_id='project')['items']
        second_plan = source.recovery('backup_plan', destination=str(self.root / 'second-media'),
                                      workspaces=[{'name': 'developer', 'paths': ['draft.txt']}])
        second_backup = source.recovery('backup_execute', plan_id=second_plan['plan_id'])
        controller = ProjectRecovery(self.root / 'second-controller')
        plan = controller.recovery('restore_plan', manifest=second_backup['manifest'], destination=str(self.root / 'second-restore'))
        result = controller.recovery('restore_execute', plan_id=plan['plan_id'])
        recovered = ProjectRecovery(result['effect']['control'])
        page = recovered.recovery('history', collection='config', local_id='project', limit=1)
        following = recovered.recovery('history', collection='config', local_id='project', limit=1, cursor=page['next_cursor'])
        history = page['items'] + following['items']
        self.assertEqual(2, len(history))
        self.assertIn(old_history[0], history)


if __name__ == '__main__':
    unittest.main()
