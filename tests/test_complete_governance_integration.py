"""Public dispatch integration using synthetic host attestations, never native proof."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from taskcarry.api import invoke
from taskcarry.core import Core, digest_bytes
from taskcarry.gitops import git, out
from taskcarry.onboarding import fingerprint
from taskcarry.store import GovernanceError


class GovernanceFixture(unittest.TestCase):
    def setUp(self):
        sandbox = Path(__file__).resolve().parents[1] / 'validation/local/complete-integration-tests'
        sandbox.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-', dir=sandbox)
        self.root = Path(self.temp.name)
        self.control = self.root / 'control'
        self.scenario = None
        if getattr(self, 'published_scenario', False):
            path = Path(__file__).resolve().parents[1] / 'examples/complete-governance/scenario.json'
            self.scenario = json.loads(path.read_text(encoding='utf-8'))
        invoke(self.control, 'init', {'name': self.scenario['name'] if self.scenario else 'Synthetic appointment governance'})
        self.store = Core(self.control).store
        self._repository(self.control)
        if not self.scenario:
            self.call('task', task_id='payments', title='Existing paused payment work', state='paused')
        self.scope = {'profile': 'complete_v1', 'governance_thread': 'governance', 'channel': 'rc',
                      'schedule': {'timezone': 'UTC', 'slots': [
                          {'slot_id': 'morning', 'purpose': 'report', 'time': '09:00'},
                          {'slot_id': 'afternoon', 'purpose': 'absorb', 'time': '15:00'}]},
                      'windows': [
                          {'thread_id': 'booking-chat', 'task_id': 'booking', 'workspace': 'booking', 'mode': 'active',
                           'source_ref': 'chat:booking', 'responsibility': 'Continue existing booking work.'},
                          {'thread_id': 'history-chat', 'mode': 'reference', 'source_ref': 'chat:history',
                           'responsibility': 'Retain accepted manual approval and paused payment decisions.'}]}
        if self.scenario:
            self.scope = self.scenario['scope']
        self.windows = [window for window in self.scope['windows'] if window['mode'] == 'active']
        self.primary = self.windows[0]
        self.workers = {}
        for window in self.windows:
            worker = self.root / window['workspace']
            self._repository(worker)
            self.call('workspace', name=window['workspace'], path=str(worker))
            self.call('task', task_id=window['task_id'], title=window['responsibility'])
            self.workers[window['workspace']] = worker
        self.worker = self.workers[self.primary['workspace']]
        self.call('onboarding', onboarding_id='setup', action='start', scope=self.scope)

    def tearDown(self):
        self.temp.cleanup()

    def _repository(self, path):
        path.mkdir(parents=True, exist_ok=True)
        git(path, 'init', '-b', 'main')
        git(path, 'config', 'user.name', 'Synthetic Governance')
        git(path, 'config', 'user.email', 'governance@example.invalid')
        (path / '.gitignore').write_text('.taskcarry/\n.local/\n.codex/\n.agents/\nevidence/\n', encoding='utf-8')
        baseline = self.scenario['effective_decision'] if self.scenario else 'Manual approval remains valid. Payment work is paused.'
        (path / 'governance.md').write_text(baseline + '\n', encoding='utf-8')
        git(path, 'add', '.gitignore', 'governance.md')
        git(path, 'commit', '-m', 'Synthetic existing baseline')

    def call(self, operation, **arguments):
        return invoke(self.control, operation, arguments)

    def assertCode(self, code, callback, *args, **kwargs):
        with self.assertRaises(GovernanceError) as caught:
            callback(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def update(self, key, **evidence):
        prior = self.call('onboarding', onboarding_id='setup')['onboarding']
        return self.call('onboarding', onboarding_id='setup', action='update', expected_revision=prior['revision'],
                         item={'key': key, 'status': 'verified', 'evidence': {'receipt_ref': 'synthetic:' + key,
                               'fixture_notice': 'Synthetic attestation only; not actual native host acceptance.', **evidence}, 'next_step': ''})

    def cycle(self, source_refs=None, cycle_id='first-governance', health_age=0):
        self.call('cycle', action='start', cycle_id=cycle_id, owner='governor', task_id=self.primary['task_id'], scope=['project-memory'])
        for index, source in enumerate(source_refs or [window['source_ref'] for window in self.scope['windows']]):
            for phase in ('observed', 'understood'):
                self.call('cycle', action='source', cycle_id=cycle_id, owner='governor', request_id=f'{phase}-{index}',
                          data={'source_id': source, 'source_revision': 'reviewed-turn-1', 'phase': phase,
                                'evidence_ref': 'synthetic:source-review', 'statement': 'Retained original accepted decisions and unfinished positions.'})
        self.call('cycle', action='health', cycle_id=cycle_id, owner='governor', request_id='health',
                  data={'dimension': 'governance-runtime', 'status': 'healthy',
                        'observed_at': (datetime.now(timezone.utc) - timedelta(seconds=health_age)).isoformat(),
                        'freshness_seconds': 3600, 'evidence_ref': 'synthetic:runtime-diagnostic'})
        self.call('cycle', action='finish', cycle_id=cycle_id, owner='governor', request_id='finish',
                  data={'state': 'completed', 'next_step': self.scenario['next_step'] if self.scenario else 'Clarify cancellation cases; retain payment pause.'})
        return cycle_id

    def publish(self, task_id=None, thread_id=None, source_file='governance.md', workspace=None):
        workspace = workspace or self.primary['workspace']
        window = next(window for window in self.windows if window['workspace'] == workspace)
        task_id, thread_id = task_id or window['task_id'], thread_id or window['thread_id']
        if source_file:
            sources = [{'source_id': self.call('identity')['source']['source_id'], 'path': source_file,
                        'revision': digest_bytes((self.control / source_file).read_bytes())}]
        else:
            sources = [{'source_id': 'chat:history', 'revision': 'reviewed-turn-1'}]
        body = ('\n'.join(self.scenario[key] for key in ('effective_decision', 'deferred_scope', 'next_step')) if self.scenario
                else 'Manual approval remains accepted. Payments remain paused. Clarify cancellation cases.')
        view = self.call('workbench', action='freeze', body=body, sources=sources)
        plan = self.call('workbench', action='plan', view_id=view['view_id'], targets=[{
            'workspace': workspace, 'task_id': task_id, 'thread_id': thread_id, 'host': 'none',
            'code_assessment': {'status': 'NO_CODE_DEPENDENCY', 'reason': 'Navigation and decisions only.'},
            'writes': [{'path': '.local/CURRENT.md', 'text': (self.scenario['next_step'] if self.scenario
                       else 'Read the retained project decisions and current cancellation question.')}]}])
        self.call('workbench', action='execute', plan_id=plan['plan_id'])
        evidence = self.control / 'evidence' / (workspace + '-review.json')
        evidence.parent.mkdir(exist_ok=True)
        evidence.write_text('{"kind":"synthetic consumption evidence, not a native host receipt"}\n', encoding='utf-8')
        self.call('workbench', action='consume', proof={'workspace': workspace, 'task_id': task_id,
            'source_id': self.call('identity')['source']['source_id'], 'plan_id': plan['plan_id'], 'view_id': view['view_id'],
            'thread_id': thread_id, 'turn_id': 'synthetic-turn', 'evidence_path': evidence.relative_to(self.control).as_posix(),
            'evidence_sha256': digest_bytes(evidence.read_bytes()), 'reviewer': 'synthetic reviewer',
            'observed_at': datetime.now(timezone.utc).isoformat()})
        return view, plan

    def backup_restore(self, suffix='one'):
        backup_plan = self.call('recovery', action='backup_plan', destination=str(self.root / ('media-' + suffix)),
            workspaces=[*[{'name': window['workspace']} for window in self.windows],
                        {'name': 'governance', 'path': str(self.control)}])
        backup = self.call('recovery', action='backup_execute', plan_id=backup_plan['plan_id'])
        restore_plan = self.call('recovery', action='restore_plan', manifest=backup['manifest'],
            expected_sha256=backup['manifest_sha256'], destination=str(self.root / ('restored-' + suffix)))
        restored = self.call('recovery', action='restore_execute', plan_id=restore_plan['plan_id'])
        return backup, restore_plan, restored

    def recovery_evidence(self, backup, restore):
        return {'manifest': backup['manifest'], 'manifest_sha256': backup['manifest_sha256'],
                'restore_plan_id': restore['plan_id'], 'restore_receipt_ref': 'synthetic:isolated-restore', 'restore_verified': True}

    def complete(self):
        self.update('scope', user_confirmed=True, scope_fingerprint=fingerprint(self.scope))
        identity = self.call('identity')['source']
        self.update('identity', source_id=identity['source_id'], replica_id=identity['replica_id'])
        self.update('runtime', thread_id=self.scope['governance_thread'], transport='native_mcp', doctor_ok=True, status_ok=True,
                    isolated=True, control=str(self.control), version='0.2.0rc7', interpreter='synthetic:python',
                    module_root='synthetic:installed-module', identity_ref='synthetic:runtime-identity')
        for window in self.windows:
            self.update('window:' + window['thread_id'], thread_id=window['thread_id'], task_id=window['task_id'], workspace=window['workspace'],
                        transport='native_mcp', doctor_ok=True, status_ok=True, cwd=str(self.workers[window['workspace']]), control=str(self.control),
                        runtime={'version': '0.2.0rc7', 'interpreter': 'synthetic:python', 'module_root': 'synthetic:installed-module'})
        current = ('\n'.join(self.scenario[key] for key in ('effective_decision', 'deferred_scope', 'next_step')) if self.scenario
                   else 'Manual approval valid. Payments paused. Cancellation question retained.')
        (self.control / 'governance.md').write_text(current + '\n', encoding='utf-8')
        saved = self.call('preserve', action='plan', repository=str(self.control), paths=['governance.md'], message='Retain synthetic decisions')
        saved = self.call('preserve', action='execute', plan_id=saved['plan_id'])
        self.update('local_git', plan_id=saved['plan_id'], commit=saved['commit'])
        self.call('update_source', channel='rc')
        with mock.patch('taskcarry.updates._fetch_json', return_value=([], 'synthetic-response-hash')):
            check = self.call('update_check')
        self.call('update_assess', check=check, decision='keep', reason='Synthetic empty remote response; no installation requested.')
        self.update('update_check', channel='rc', checked=True, source=check['release_source'],
                    result_fingerprint=check['fingerprint'], assessment_ref=check['fingerprint'])
        slots = self.call('schedule_plan', onboarding_id='setup')['slots']
        slots = [{**slot, 'automation_id': 'synthetic-' + slot['slot_id'], 'active': True, 'readback': True,
                  'runtime_ref': 'synthetic:fixed-runtime'} for slot in slots]
        self.update('schedule_config', slots=slots)
        materials = self.root / 'materials'
        materials.mkdir()
        if self.scenario:
            (materials / 'sample-frame.txt').write_bytes(self.scenario['protocol_example']['frame'].encode('utf-8'))
            (materials / 'replay-cases.json').write_text(json.dumps(self.scenario['simulation_cases']), encoding='utf-8')
        else:
            (materials / 'cancellation.md').write_text('Synthetic cancellation examples await clarification.', encoding='utf-8')
        self.call('source_scan', action='register', source_id='materials', root=str(materials), authorization_ref='synthetic:user-selected-root')
        scan = self.call('source_scan', action='start', source_id='materials', scan_id='first-materials')['scan']
        while scan.get('next_cursor'):
            scan = self.call('source_scan', action='page', source_id='materials', scan_id='first-materials', cursor=scan['next_cursor'])['page']
        self.assertTrue(scan['enumeration_complete'])
        history_source = next(window['source_ref'] for window in self.scope['windows'] if window['mode'] == 'reference')
        decision = self.scenario['effective_decision'] if self.scenario else 'Manual approval remains valid.'
        self.call('facts', action='record', fact_id='shared-frame' if self.scenario else 'manual-approval',
                  task_id=self.primary['task_id'], source_id=history_source,
                  source_revision='reviewed-turn-1', kind='decision', statement=decision,
                  evidence={'reference': 'synthetic:reviewed-history', 'summary': decision},
                  judgment={'statement': self.scenario['next_step'] if self.scenario else 'No reimplementation needed.',
                            'basis': 'The reviewed first-milestone scope.' if self.scenario else 'Existing acceptance remains current.'})
        cycle_id = self.cycle()
        entries = []
        for window in self.windows:
            view, _ = self.publish(workspace=window['workspace'])
            entries.append({'workspace': window['workspace'], 'view_id': view['view_id'], 'native_doctor_status_verified': True})
        self.update('sources', cycle_id=cycle_id, coverage_ref='synthetic:all-selected-sources-and-exclusions')
        self.update('first_cycle', cycle_id=cycle_id, coverage_ref='synthetic:first-cycle-effects-and-next-work')
        self.update('workbenches', entries=entries)
        backup, restore, _ = self.backup_restore()
        self.update('recovery', **self.recovery_evidence(backup, restore))
        return self.call('onboarding', onboarding_id='setup'), slots


class CompleteGovernanceIntegrationTests(GovernanceFixture):
    def test_complete_public_flow_retains_original_work_and_evidence_levels(self):
        result, slots = self.complete()
        self.assertEqual([], result['pending'])
        self.assertTrue(result['complete_governance_ready'])
        self.assertFalse(result['natural_trigger_verified'])
        self.assertFalse(result['closed_loop_verified'])
        self.assertFalse(result['host_effects_executed'])
        self.assertEqual('host_reviewed_receipts_and_live_local_bindings', result['evidence_scope'])
        self.assertEqual('paused', self.store.get('tasks', 'payments')['state'])
        self.assertEqual([], self.store.list('stages'))
        for slot in slots:
            evidence = {'thread_id': 'governance', 'automation_id': slot['automation_id'], 'trigger': 'natural_heartbeat',
                        'ai_execution_verified': True, 'received_at': datetime.now(timezone.utc).isoformat(),
                        'run_ref': 'synthetic:first-governance', 'update_check_ref': 'synthetic:update', 'local_save_ref': 'synthetic:save'}
            if slot['purpose'] == 'report':
                evidence.update(delivered_at=datetime.now(timezone.utc).isoformat(), delivery_ref='synthetic:report-message')
            else:
                evidence['outcome'] = 'quiet_no_change'
            result = self.update('schedule_trigger:' + slot['slot_id'], **evidence)
        self.assertTrue(result['closed_loop_verified'])
        self.assertFalse(result['host_effects_executed'], 'Synthetic receipt simulation cannot be described as real host execution.')

    def test_expired_health_invalidates_first_cycle_readiness(self):
        cycle_id = self.cycle(health_age=7200)
        self.assertCode('ONBOARDING_EVIDENCE', self.update, 'first_cycle', cycle_id=cycle_id, coverage_ref='synthetic:old-health')
        self.assertIn('first_cycle', self.call('onboarding', onboarding_id='setup')['pending'])

    def test_unrelated_understood_source_cannot_cover_selected_chats(self):
        cycle_id = self.cycle(source_refs=['chat:unrelated'])
        self.assertCode('ONBOARDING_EVIDENCE', self.update, 'sources', cycle_id=cycle_id, coverage_ref='synthetic:wrong-sources')

    def test_consumption_in_another_thread_cannot_satisfy_selected_workbench(self):
        view, _ = self.publish(thread_id='another-chat')
        self.assertCode('ONBOARDING_EVIDENCE', self.update, 'workbenches', entries=[
            {'workspace': 'booking', 'view_id': view['view_id'], 'native_doctor_status_verified': True}])

    def test_workbench_from_changed_governance_source_is_not_complete(self):
        view, _ = self.publish(source_file='governance.md')
        (self.control / 'governance.md').write_text('A newer decision changed cancellation scope.', encoding='utf-8')
        status = self.call('workbench', action='status', workspace='booking')['items'][0]
        self.assertEqual('CHANGED_OR_MISSING', status['source_freshness'][0]['state'])
        self.assertCode('ONBOARDING_EVIDENCE', self.update, 'workbenches', entries=[
            {'workspace': 'booking', 'view_id': view['view_id'], 'native_doctor_status_verified': True}])

    def test_missing_artifact_payload_cannot_pass_complete_recovery_gate(self):
        artifact = self.root / 'external-cancellation-study.txt'
        artifact.write_text('Synthetic retained artifact outside selected Git workspaces.', encoding='utf-8')
        self.call('artifact', task_id='booking', path=str(artifact), decision='retain')
        backup, restore, _ = self.backup_restore()
        verified = self.call('recovery', action='verify', manifest=backup['manifest'], expected_sha256=backup['manifest_sha256'])
        self.assertTrue(verified['verified'])
        self.assertFalse(verified['complete_scope'])
        self.assertTrue(verified['missing_artifact_payloads'])
        self.assertCode('ONBOARDING_EVIDENCE', self.update, 'recovery', **self.recovery_evidence(backup, restore))

    def test_missing_current_pointer_becomes_pending_instead_of_crashing_status(self):
        view, _ = self.publish()
        self.update('workbenches', entries=[{'workspace': 'booking', 'view_id': view['view_id'], 'native_doctor_status_verified': True}])
        current = self.call('workbench', action='status', workspace='booking')['items'][0]
        Path(current['current_path']).unlink()
        result = self.call('onboarding', onboarding_id='setup')
        self.assertIn('workbenches', result['pending'])
        self.assertEqual('ONBOARDING_EVIDENCE', result['invalidated']['workbenches']['code'])


class PublishedScenarioGovernanceTests(GovernanceFixture):
    published_scenario = True

    def test_published_example_reaches_setup_readiness_without_claiming_real_host_execution(self):
        import importlib.util
        fixture = Path(__file__).resolve().parents[1] / 'examples/complete-governance/fixture'
        spec = importlib.util.spec_from_file_location('synthetic_stream_example', fixture / 'replay.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIn('no USB', module.__doc__)
        self.assertIn('First milestone', self.scenario['effective_decision'])
        self.assertIn('sequence', (fixture / 'PROTOCOL.md').read_text(encoding='utf-8'))
        replay = module.Replay()
        replay.feed((fixture / 'normal_frames.txt').read_text(encoding='utf-8'))
        self.assertEqual([(42, 1000, 1.234), (43, 1100, 1.25), (44, 1200, 1.22)], replay.points)
        self.assertEqual((fixture / 'expected.csv').read_text(encoding='utf-8'), replay.csv_text())
        replay.feed('READ,45,1300,nan\nREAD,45,1300,')
        replay.disconnect()
        replay.feed('9.0\n')
        self.assertEqual(3, len(replay.points))
        replay.reconnect()
        replay.feed('READ,44,1200,1.220\nREAD,45,1300,1.210\n')
        self.assertEqual(1, replay.invalid_frames)
        self.assertEqual(1, replay.discarded_partial_frames)
        self.assertEqual(1, replay.stale_or_duplicate_frames)
        self.assertEqual((45, 1300, 1.21), replay.points[-1])
        self.assertEqual(4, len(replay.points))
        result, slots = self.complete()
        self.assertTrue(result['complete_governance_ready'])
        self.assertFalse(result['closed_loop_verified'])
        self.assertFalse(result['host_effects_executed'])
        self.assertEqual(3, len(self.windows))
        self.assertEqual(2, len(slots))
        self.assertEqual(self.scenario['scope'], result['onboarding']['scope'])
        for window in self.windows:
            current = self.call('workbench', action='status', workspace=window['workspace'])['items'][0]
            self.assertEqual(window['thread_id'], current['thread_id'])
            self.assertEqual(window['task_id'], current['task_id'])
            self.assertEqual('REVIEWED_EVIDENCE_RECORDED', current['consumer_state'])
            self.assertFalse(current['native_acceptance_verified'])
        self.assertEqual({'usb-firmware', 'usb-pc', 'usb-simulation'}, {task['task_id'] for task in self.store.list('tasks')})
        self.assertTrue(all(task['state'] == 'active' for task in self.store.list('tasks')))
        self.assertEqual('Wireless support is outside the first milestone.', self.scenario['deferred_scope'])
        self.assertNotIn('paused_scope', self.scenario)
        self.assertEqual({'normal', 'disconnect', 'reconnect'}, {case['case'] for case in self.scenario['simulation_cases']})
        self.assertEqual('READ,42,1000,1.234\n', self.scenario['protocol_example']['frame'])
        self.assertEqual([], self.store.list('stages'))


if __name__ == '__main__':
    unittest.main()
