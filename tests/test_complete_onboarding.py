"""Complete setup coverage and actual per-slot receipts cannot be inferred."""
from pathlib import Path
import tempfile
import unittest

from taskcarry.api import invoke
from taskcarry.core import Core
from taskcarry.onboarding_complete import CompleteOnboarding
from taskcarry.store import GovernanceError


class CompleteOnboardingTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / 'validation/local/complete-onboarding-tests'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name)
        Core.initialize(self.root)
        self.service = CompleteOnboarding(self.root)
        self.scope = {'profile': 'complete_v1', 'governance_thread': 'governance', 'channel': 'rc',
                      'schedule': {'timezone': 'UTC', 'slots': [
                          {'slot_id': 'morning', 'purpose': 'report', 'time': '09:00'},
                          {'slot_id': 'afternoon', 'purpose': 'absorb', 'time': '15:00'}]},
                      'windows': [{'thread_id': 'history', 'mode': 'reference', 'source_ref': 'chat:history',
                                   'responsibility': 'Historical decisions'}]}

    def tearDown(self):
        self.temp.cleanup()

    def update(self, key, evidence):
        prior = self.service.onboarding('setup')['onboarding']
        return self.service.onboarding('setup', 'update', expected_revision=prior['revision'],
                                       item={'key': key, 'status': 'verified', 'evidence': evidence, 'next_step': ''})

    def configure_slots(self):
        plan = invoke(self.root, 'schedule_plan', {'onboarding_id': 'setup'})
        self.assertFalse(plan['execute'])
        slots = [{**s, 'automation_id': 'synthetic-' + s['slot_id'], 'active': True, 'readback': True,
                  'runtime_ref': 'synthetic:isolated-wheel'} for s in plan['slots']]
        self.update('schedule_config', {'receipt_ref': 'synthetic:host-readback', 'slots': slots})
        return slots

    def test_complete_profile_requires_new_evidence_without_relabeling_legacy(self):
        result = invoke(self.root, 'onboarding', {'onboarding_id': 'setup', 'action': 'start', 'scope': self.scope})
        self.assertFalse(result['complete_governance_ready'])
        self.assertTrue({'identity', 'sources', 'workbenches', 'recovery', 'first_cycle'} <= set(result['pending']))
        legacy = {k: v for k, v in self.scope.items() if k != 'profile'}
        legacy['schedule'] = {'time': '09:00', 'timezone': 'UTC'}
        prior = invoke(self.root, 'onboarding', {'onboarding_id': 'legacy', 'action': 'start', 'scope': legacy})
        self.assertEqual('legacy_v1', prior['profile'])
        self.assertFalse(prior['complete_governance_ready'])

    def test_all_slots_readback_trigger_execution_and_report_delivery_are_separate(self):
        self.service.onboarding('setup', 'start', scope=self.scope)
        slots = self.configure_slots()
        self.assertNotIn('schedule_config', self.service.onboarding('setup')['pending'])
        self.assertFalse(self.service.onboarding('setup')['natural_trigger_verified'])
        evidence = {'receipt_ref': 'synthetic:natural-host-turn', 'thread_id': 'governance',
                    'trigger': 'natural_heartbeat', 'ai_execution_verified': True,
                    'received_at': '2026-01-01T09:00:00+00:00', 'run_ref': 'synthetic:run',
                    'update_check_ref': 'synthetic:update', 'local_save_ref': 'synthetic:save'}
        with self.assertRaises(GovernanceError):
            self.update('schedule_trigger:morning', {**evidence, 'automation_id': slots[0]['automation_id']})
        self.update('schedule_trigger:morning', {**evidence, 'automation_id': slots[0]['automation_id'],
                                                'delivered_at': '2026-01-01T09:02:00+00:00', 'delivery_ref': 'synthetic:message'})
        self.assertFalse(self.service.onboarding('setup')['natural_trigger_verified'])
        with self.assertRaises(GovernanceError):
            self.update('schedule_trigger:afternoon', {**evidence, 'automation_id': 'wrong', 'outcome': 'quiet_no_change'})
        result = self.update('schedule_trigger:afternoon', {**evidence, 'automation_id': slots[1]['automation_id'],
                                                           'outcome': 'quiet_no_change'})
        self.assertTrue(result['natural_trigger_verified'])
        self.assertFalse(result['closed_loop_verified'])
        prior = result['onboarding']
        changed = {**self.scope, 'schedule': {'timezone': 'UTC', 'slots': [
            {**self.scope['schedule']['slots'][0], 'time': '10:00'}, self.scope['schedule']['slots'][1]]}}
        result = self.service.onboarding('setup', 'start', scope=changed, expected_revision=prior['revision'])
        self.assertFalse(result['natural_trigger_verified'])

    def test_scope_rejects_duplicate_times_or_missing_report_slot(self):
        for slots in ([self.scope['schedule']['slots'][0]] * 2,
                      [{**s, 'purpose': 'absorb'} for s in self.scope['schedule']['slots']]):
            with self.assertRaises(GovernanceError):
                self.service.onboarding('setup', 'start', scope={**self.scope, 'schedule': {'timezone': 'UTC', 'slots': slots}})

    def test_malformed_host_readback_preserves_pending_configuration(self):
        self.service.onboarding('setup', 'start', scope=self.scope)
        with self.assertRaises(GovernanceError) as caught:
            self.update('schedule_config', {'receipt_ref': 'synthetic:host-readback', 'slots': [None, 'unavailable']})
        self.assertEqual('ONBOARDING_BINDING', caught.exception.code)
        self.assertIn('schedule_config', self.service.onboarding('setup')['pending'])

    def test_new_observed_revision_stays_pending_until_all_selected_revisions_are_understood(self):
        invoke(self.root, 'onboarding', {'onboarding_id': 'setup', 'action': 'start', 'scope': self.scope})
        invoke(self.root, 'task', {'task_id': 'interface-notes', 'title': 'Review selected interface revisions'})

        def completed_cycle(cycle_id, understand_new_revision):
            invoke(self.root, 'cycle', {'action': 'start', 'cycle_id': cycle_id, 'owner': 'governor',
                                       'task_id': 'interface-notes', 'scope': ['selected-interface-memory']})
            phases = [('r1', 'observed'), ('r1', 'understood'), ('r2', 'observed')]
            if understand_new_revision:
                phases.append(('r2', 'understood'))
            for revision, phase in phases:
                invoke(self.root, 'cycle', {'action': 'source', 'cycle_id': cycle_id, 'owner': 'governor',
                    'request_id': revision + '-' + phase, 'data': {
                        'source_id': 'chat:history', 'source_revision': revision, 'phase': phase,
                        'evidence_ref': 'synthetic:interface-' + revision,
                        'statement': 'Selected interface notes were ' + phase + ' at this exact revision.'}})
            invoke(self.root, 'cycle', {'action': 'finish', 'cycle_id': cycle_id, 'owner': 'governor',
                'request_id': 'finish', 'data': {'state': 'completed',
                    'next_step': 'Continue reviewed work.' if understand_new_revision else 'Read the newly observed r2 before claiming complete source understanding.'}})

        def record_sources(cycle_id):
            prior = invoke(self.root, 'onboarding', {'onboarding_id': 'setup'})['onboarding']
            return invoke(self.root, 'onboarding', {'onboarding_id': 'setup', 'action': 'update',
                'expected_revision': prior['revision'], 'item': {'key': 'sources', 'status': 'verified',
                    'evidence': {'receipt_ref': 'synthetic:source-coverage', 'cycle_id': cycle_id,
                                 'coverage_ref': 'synthetic:selected-interface-notes'}, 'next_step': ''}})

        completed_cycle('review-incomplete', False)
        before = self.service.store.events()
        with self.assertRaises(GovernanceError) as caught:
            record_sources('review-incomplete')
        self.assertEqual('ONBOARDING_EVIDENCE', caught.exception.code)
        self.assertEqual([{'source_id': 'chat:history', 'source_revision': 'r2'}],
                         caught.exception.details['unread_revisions'])
        rejected = invoke(self.root, 'onboarding', {'onboarding_id': 'setup'})
        self.assertIn('sources', rejected['pending'])
        self.assertNotIn('sources', rejected['onboarding']['items'])
        self.assertEqual(1, rejected['onboarding']['revision'])
        self.assertEqual(before, self.service.store.events())

        completed_cycle('review-complete', True)
        accepted = record_sources('review-complete')
        self.assertNotIn('sources', accepted['pending'])
        self.assertEqual('review-complete', accepted['onboarding']['items']['sources']['evidence']['cycle_id'])
        self.assertFalse(accepted['complete_governance_ready'], 'Understanding sources alone does not complete other setup requirements.')


if __name__ == '__main__':
    unittest.main()
