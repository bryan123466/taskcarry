"""Restore, identity and workbench boundaries through the public dispatcher."""
from pathlib import Path
from unittest import mock

from taskcarry.api import invoke
from taskcarry.core import Core
from taskcarry.governance_cycle import GovernanceCycle
from taskcarry.store import Store, GovernanceError
from tests.test_complete_governance_integration import GovernanceFixture


class GovernanceRecoveryBoundaryTests(GovernanceFixture):
    def activate(self, control):
        identity = invoke(control, 'identity', {})['source']
        plan = invoke(control, 'recovery', {'action': 'activation_plan'})
        result = invoke(control, 'recovery', {'action': 'activate', 'plan_id': plan['plan_id'],
            'authorization': 'Synthetic explicit writer handoff fixture.', 'old_writer_stopped': True,
            'old_replica_id': plan['old_replica_id'], 'native_evidence': {
                'source_id': identity['source_id'], 'replica_id': identity['replica_id'], 'control': str(control),
                'doctor': True, 'status': True, 'evidence_ref': 'synthetic attestation; not native host proof'}})
        self.assertTrue(result['writer_activated'])
        self.assertFalse(result['native_evidence_independently_verified'])
        self.assertFalse(result['old_writer_remotely_fenced'])
        self.assertFalse(result['automations_enabled'])
        return result

    def retained_work(self):
        self.call('cycle', action='start', cycle_id='unfinished', owner='governor', task_id='booking', scope=['project-memory'])
        self.call('cycle', action='effect_plan', cycle_id='unfinished', owner='governor', request_id='plan',
                  data={'effect_id': 'document', 'kind': 'write', 'resource': 'project-memory', 'expected': 'An exact reviewed summary.'})
        self.call('checkpoint', task_id='booking', workspace='booking', paths=['governance.md'], next_step='Continue original cancellation clarification.')
        _, publication = self.publish()
        _, restore, restored = self.backup_restore()
        return Path(restored['effect']['control']), restore, publication

    def test_standby_rejects_mutations_and_retains_original_evidence_for_review(self):
        restored, _, publication = self.retained_work()
        target = Core(restored)
        self.assertEqual('standby', target.source()['writer_state'])
        self.assertEqual(self.call('identity')['source']['source_id'], target.source()['source_id'])
        self.assertCode('RECOVERY_STANDBY', invoke, restored, 'task', {'task_id': 'booking', 'state': 'complete'})
        self.assertCode('RECOVERY_STANDBY', invoke, restored, 'cycle', {'action': 'resume', 'cycle_id': 'unfinished', 'owner': 'governor', 'scope': ['project-memory']})
        self.assertCode('RECOVERY_STANDBY', invoke, restored, 'workbench', {'action': 'execute', 'plan_id': publication['plan_id']})
        self.assertIsNone(target.store.get('governance_cycles', 'unfinished'))
        history = next(item for item in target.store.list('recovery_history')
                       if item.get('original_collection') == 'governance_cycles'
                       and item.get('original_key') == 'unfinished'
                       and item.get('restore_id') == target.store.get('config', 'project')['recovery_restore_id'])
        self.assertFalse(history['executable'])
        self.assertEqual('pending', history['record']['effects']['document']['outcome'])
        before = target.store.events()
        status = invoke(restored, 'status', {})
        invoke(restored, 'identity', {})
        invoke(restored, 'workbench', {'action': 'status', 'workspace': 'booking'})
        self.assertEqual(before, target.store.events())
        self.assertEqual('paused', next(task for task in status['tasks'] if task['task_id'] == 'payments')['state'])

    def test_activated_replica_keeps_old_cycles_and_publication_plans_inert(self):
        restored, _, publication = self.retained_work()
        self.activate(restored)
        self.assertCode('RESTORED_RUN_INERT', invoke, restored, 'cycle', {
            'action': 'start', 'cycle_id': 'unfinished', 'owner': 'governor', 'task_id': 'booking', 'scope': ['project-memory']})
        self.assertCode('RESTORED_PLAN_INERT', invoke, restored, 'workbench', {'action': 'execute', 'plan_id': publication['plan_id']})
        fresh = invoke(restored, 'cycle', {'action': 'start', 'cycle_id': 'new-replica-cycle',
            'owner': 'governor', 'task_id': 'booking', 'scope': ['project-memory']})
        self.assertEqual('active', fresh['cycle']['state'])
        self.assertEqual('booking', fresh['cycle']['task_id'])

    def test_direct_cycle_engine_cannot_reanimate_historical_cycle_after_activation(self):
        restored, _, _ = self.retained_work()
        self.activate(restored)
        self.assertCode('RESTORED_RUN_INERT', GovernanceCycle(restored).cycle, 'start', cycle_id='unfinished',
                        owner='governor', task_id='booking', scope=['project-memory'])

    def test_legacy_reads_are_nonmutating_and_identity_adoption_keeps_explicit_fact_source(self):
        config = self.store.get('config', 'project')
        # Build an actual old-format synthetic state. This is not a product migration path.
        config.pop('project_id', None)
        config.pop('replica_id', None)
        config.pop('source_aliases', None)
        self.store.put('config', 'project', config)
        legacy = self.call('identity')['source']
        self.assertEqual('resolved_local_path', legacy['identity_scope'])
        self.call('facts', action='record', fact_id='approval', source_revision='old-turn', task_id='booking', kind='decision',
                  statement='Manual approval remains accepted.', evidence={'reference': 'synthetic:old-turn', 'summary': 'Accepted prior decision.'})
        before = self.store.events()
        self.call('identity')
        self.call('status')
        self.call('facts', action='get', fact_id='approval')
        self.assertEqual(before, self.store.events())
        self.assertNotIn('project_id', self.store.get('config', 'project'))
        plan = self.call('identity', action='plan')
        current = self.call('identity', action='execute', plan_id=plan['plan_id'])['source']
        self.assertIn(legacy['source_id'], current['aliases'])
        self.assertEqual('persistent_project', current['identity_scope'])
        saved = self.call('facts', action='get', fact_id='approval', source_id=legacy['source_id'])['fact']
        self.assertEqual('Manual approval remains accepted.', saved['statement'])
        self.assertEqual(1, saved['revision'])

    def test_legacy_identity_adoption_does_not_break_existing_workbench_reads(self):
        config = self.store.get('config', 'project')
        config.pop('project_id', None)
        config.pop('replica_id', None)
        config.pop('source_aliases', None)
        self.store.put('config', 'project', config)
        view, _ = self.publish(source_file='governance.md')
        before = self.call('workbench', action='status', workspace='booking')['items'][0]
        self.assertEqual('PUBLISHED', before['state'])
        plan = self.call('identity', action='plan')
        self.call('identity', action='execute', plan_id=plan['plan_id'])
        after = self.call('workbench', action='status', workspace='booking')['items'][0]
        self.assertEqual('PUBLISHED', after['state'])
        self.assertEqual(view['view_id'], after['view_id'])
        self.assertEqual('REVIEWED_EVIDENCE_RECORDED', after['consumer_state'])

    def test_recovery_copy_preserves_scope_declarations_without_treating_them_as_payload_objects(self):
        artifact = self.root / 'external.txt'
        artifact.write_text('Synthetic external evidence explicitly not included in this selected recovery set.', encoding='utf-8')
        self.call('artifact', task_id='booking', path=str(artifact), decision='retain')
        backup, _, _ = self.backup_restore()
        plan = self.call('transfer', action='copy_plan', manifest=backup['manifest'],
                         expected_sha256=backup['manifest_sha256'], destination=str(self.root / 'static-copy'))['plan']
        copied = self.call('transfer', action='copy_execute', plan_id=plan['plan_id'])
        self.assertTrue(copied['observed_effect']['local_copy_verified'])
        self.assertFalse(copied['observed_effect']['cloud_upload_verified'])
        verified = self.call('recovery', action='verify', manifest=str(self.root / 'static-copy/manifest.json'), expected_sha256=backup['manifest_sha256'])
        self.assertTrue(verified['verified'])
        self.assertFalse(verified['complete_scope'])
        self.assertTrue(verified['missing_artifact_payloads'])

    def test_prepared_legacy_checkpoint_restore_operation_cannot_replay_old_destination(self):
        checkpoint = self.call('checkpoint', task_id='booking', workspace='booking', paths=['governance.md'],
                               next_step='Retain original decision.')
        destination = self.root / 'old-prepared-restore-destination'
        real_put = Store.put

        def interrupt_before_effect(store, collection, key, value):
            if collection == 'operations' and value.get('kind') == 'restore' and value.get('status') == 'APPLYING':
                raise RuntimeError('Synthetic interruption after PREPARED receipt, before any effect.')
            return real_put(store, collection, key, value)

        with mock.patch.object(Store, 'put', new=interrupt_before_effect):
            with self.assertRaises(RuntimeError):
                self.call('restore', checkpoint_id=checkpoint['checkpoint_id'], destination=str(destination))
        operation = next(record for record in self.store.list('operations') if record['kind'] == 'restore')
        self.assertEqual('PREPARED', operation['status'])
        self.assertNotIn('plan_id', operation)
        self.assertFalse(destination.exists())
        _, _, restored = self.backup_restore()
        new_control = Path(restored['effect']['control'])
        self.activate(new_control)
        with self.assertRaises(GovernanceError):
            invoke(new_control, 'restore', {'checkpoint_id': checkpoint['checkpoint_id'], 'destination': str(destination)})
        self.assertFalse(destination.exists(), 'A restored old operation must not create its old-machine destination.')


if __name__ == '__main__':
    import unittest
    unittest.main()
