"""Versioned complete-governance acceptance without changing legacy receipts."""
import re
from pathlib import Path

from .core import digest_bytes
from .onboarding import Onboarding, fingerprint, text
from .store import GovernanceError


PROFILE = 'complete_v1'


class CompleteOnboarding(Onboarding):
    def _scope(self, scope):
        if not isinstance(scope, dict) or scope.get('profile') != PROFILE:
            return super()._scope(scope)
        if set(scope) != {'profile', 'governance_thread', 'windows', 'schedule', 'channel'}:
            raise GovernanceError('ONBOARDING_SCOPE', 'Use the complete_v1 project, windows, channel and schedule scope.')
        schedule = scope['schedule']
        if not isinstance(schedule, dict) or set(schedule) != {'timezone', 'slots'}:
            raise GovernanceError('ONBOARDING_SCOPE', 'Choose a timezone, one report and one or two absorption slots.')
        slots = schedule['slots']
        if not isinstance(slots, list) or not 2 <= len(slots) <= 3:
            raise GovernanceError('ONBOARDING_SCOPE', 'Choose two or three daily slots.')
        ids, times, reports = set(), set(), 0
        for slot in slots:
            if not isinstance(slot, dict) or set(slot) != {'slot_id', 'purpose', 'time'}:
                raise GovernanceError('ONBOARDING_SCOPE', 'Each slot needs slot_id, purpose and time.')
            sid = text(slot['slot_id'], 'Slot ID', 64)
            if not re.fullmatch(r'[a-zA-Z0-9_-]+', sid) or sid in ids or slot['time'] in times:
                raise GovernanceError('ONBOARDING_SCOPE', 'Use unique simple slot IDs and distinct daily times.')
            if slot['purpose'] not in ('report', 'absorb'):
                raise GovernanceError('ONBOARDING_SCOPE', 'Slot purpose must be report or absorb.')
            reports += slot['purpose'] == 'report'
            ids.add(sid)
            times.add(slot['time'])
            base = {k: scope[k] for k in ('governance_thread', 'windows', 'channel')}
            base['schedule'] = {'time': slot['time'], 'timezone': schedule['timezone']}
            super()._scope(base)
        if reports != 1:
            raise GovernanceError('ONBOARDING_SCOPE', 'Exactly one report slot is required; others absorb changes.')
        return {**base, 'profile': PROFILE, 'schedule': schedule}

    @staticmethod
    def _keys(scope):
        keys = Onboarding._keys(scope)
        if scope.get('profile') == PROFILE:
            keys += ['identity', 'sources', 'workbenches', 'recovery', 'first_cycle']
        return keys

    def _optional_keys(self, scope):
        if scope.get('profile') != PROFILE:
            return super()._optional_keys(scope)
        return ['remote', 'cloud'] + ['schedule_trigger:' + s['slot_id'] for s in scope['schedule']['slots']]

    def _slot_prompt(self, scope, slot):
        return (super()._prompt(scope) + ' Complete-governance profile complete_v1; slot ' + slot['slot_id'] +
                ' has purpose ' + slot['purpose'] + '. '
                'Read the current workspace view and project rules. Reserve one bounded governance cycle with '
                'an exact owner and resource scope; resume its saved effects after interruption. '
                'Read only selected chat/material sources, record revisions and distinguish observed, understood, '
                'published and consumed. Reconcile current facts, decisions and dependencies without reviving '
                'completed history. Review applicable fixes and update identities; do not equate recorded fixes '
                'with installation. Publish current rules/progress to affected workbenches with exact plans and '
                'preserve their configuration and WIP. Verify selected recovery coverage and health; a local '
                'manifest is not an offsite download or restore. Record execution separately from actual report '
                'delivery; count unanswered questions only on distinct dates with a real delivery receipt. ' +
                ('Deliver one concise project report with decisions, evidence, missing conditions and next work.'
                 if slot['purpose'] == 'report' else
                 'Absorb meaningful changes; stay quiet if unchanged, and escalate only a necessary decision.'))

    def _verify_item_binding(self, prior, item):
        if prior['scope'].get('profile') != PROFILE:
            return super()._verify_item_binding(prior, item)
        if item['key'].startswith('schedule_trigger:'):
            slot_id = item['key'].split(':', 1)[1]
            slots = prior['items'].get('schedule_config', {}).get('evidence', {}).get('slots', [])
            config = next((s for s in slots if s.get('slot_id') == slot_id), {})
            if config.get('automation_id') != item['evidence'].get('automation_id'):
                raise GovernanceError('ONBOARDING_BINDING', 'The actual trigger must match this configured slot.')

    def _verify(self, scope, key, evidence):
        if scope.get('profile') != PROFILE:
            return super()._verify(scope, key, evidence)
        if not isinstance(evidence, dict):
            raise GovernanceError('ONBOARDING_EVIDENCE', 'Provide structured actual evidence.')
        text(evidence.get('receipt_ref'), 'Evidence receipt')
        if key == 'identity':
            actual = self.source()
            if (actual['identity_scope'] != 'persistent_project'
                    or evidence.get('source_id') != actual['source_id']
                    or evidence.get('replica_id') != actual['replica_id']):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Verify this portable project and replica identity.')
        elif key == 'workbenches':
            from .workbench import Workbench
            expected = {w['workspace'] for w in scope['windows'] if w['mode'] == 'active'}
            entries = evidence.get('entries')
            if (not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries)
                    or {e.get('workspace') for e in entries} != expected or len(entries) != len(expected)):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Verify each active workspace current entry and consumption.')
            for entry in entries:
                items = Workbench(self.root).workbench('status', workspace=entry['workspace'])['items']
                selected = next(w for w in scope['windows'] if w.get('workspace') == entry['workspace'])
                if (len(items) != 1 or items[0].get('view_id') != entry.get('view_id')
                        or items[0].get('task_id') != selected['task_id']
                        or items[0].get('thread_id') != selected['thread_id']
                        or items[0].get('state') != 'PUBLISHED'
                        or items[0].get('consumer_state') != 'REVIEWED_EVIDENCE_RECORDED'
                        or items[0].get('finalization_pending') is not False
                        or not items[0].get('source_freshness')
                        or any(s.get('state') != 'MATCHES' for s in items[0]['source_freshness'])
                        or entry.get('native_doctor_status_verified') is not True):
                    raise GovernanceError('ONBOARDING_EVIDENCE', 'A generated entry alone is not a consumed native workspace.')
        elif key == 'recovery':
            from .project_recovery import ProjectRecovery
            verified = ProjectRecovery(self.root).recovery('verify', manifest=text(evidence.get('manifest'), 'Recovery manifest'),
                                                          expected_sha256=text(evidence.get('manifest_sha256'), 'Manifest hash'))
            # A success return proves verified bytes; the separately reviewed
            # rehearsal receipt describes its selected restore and exclusions.
            if verified.get('verified') is not True or verified.get('complete_scope') is not True:
                raise GovernanceError('ONBOARDING_EVIDENCE', 'The recovery set failed byte verification.')
            status = ProjectRecovery(self.root).recovery('status', plan_id=text(evidence.get('restore_plan_id'), 'Restore plan'))
            receipt = status.get('receipt') or {}
            effect = status.get('observed_effect') or {}
            if (status['plan']['kind'] != 'restore' or receipt.get('manifest_sha256') != evidence['manifest_sha256']
                    or receipt.get('state') != 'RESTORED_STANDBY' or effect.get('state_verified') is not True
                    or effect.get('complete_scope') is not True
                    or effect.get('git_verified') is not True):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Verify the actual isolated restore and its exact manifest receipt.')
            text(evidence.get('restore_receipt_ref'), 'Independent restore receipt')
            if evidence.get('restore_verified') is not True:
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Perform an isolated restore before completing setup.')
        elif key in ('sources', 'first_cycle'):
            from .governance_cycle import GovernanceCycle
            result = GovernanceCycle(self.root).cycle('status', cycle_id=text(evidence.get('cycle_id'), 'Cycle ID'))
            record = result.get('cycle', result)
            if record.get('state') != 'completed':
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Reference the completed bounded first governance cycle.')
            if key == 'sources':
                expected_sources = {w['source_ref'] for w in scope['windows']}
                understood = {s['source_id'] for s in record.get('sources', {}).values()
                              if s.get('source_revision') and 'observed' in s.get('phases', {})
                              and 'understood' in s.get('phases', {})}
                unread = [s for s in record.get('sources', {}).values()
                          if s.get('source_id') in expected_sources and 'observed' in s.get('phases', {})
                          and 'understood' not in s.get('phases', {})]
                if not expected_sources <= understood or unread:
                    raise GovernanceError('ONBOARDING_EVIDENCE', 'Understand every selected exact source revision; unrelated sources cannot fill the gap.',
                                          {'missing_sources': sorted(expected_sources - understood),
                                           'unread_revisions': [{'source_id': s['source_id'], 'source_revision': s['source_revision']}
                                                                for s in unread]})
            if key == 'first_cycle' and (not record.get('health') or any(
                    h.get('effective_status') != 'healthy' for h in record['health'].values())):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Review current healthy evidence or retain the concrete setup gap.')
            text(evidence.get('coverage_ref'), 'Reviewed coverage, exclusions and next work')
        elif key == 'schedule_config':
            entries = evidence.get('slots')
            if (not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries)
                    or len(entries) != len(scope['schedule']['slots'])):
                raise GovernanceError('ONBOARDING_BINDING', 'Read back every configured native schedule slot.')
            seen = set()
            for slot in scope['schedule']['slots']:
                actual = [e for e in entries if e.get('slot_id') == slot['slot_id']]
                if len(actual) != 1:
                    raise GovernanceError('ONBOARDING_BINDING', 'Each exact slot needs one native schedule readback.')
                actual = actual[0]
                expected = {'thread_id': scope['governance_thread'], 'time': slot['time'],
                            'timezone': scope['schedule']['timezone'], 'frequency': 'daily', 'kind': 'heartbeat',
                            'readback': True, 'active': True,
                            'prompt_sha256': digest_bytes(self._slot_prompt(scope, slot).encode('utf-8'))}
                if any(actual.get(k) != v for k, v in expected.items()):
                    raise GovernanceError('ONBOARDING_BINDING', 'Read back the exact prompt, time, zone and original chat.')
                aid = text(actual.get('automation_id'), 'Automation ID', 256)
                if aid in seen or Path(text(actual.get('cwd'), 'Schedule cwd')).resolve() != self.root:
                    raise GovernanceError('ONBOARDING_BINDING', 'Use distinct native schedules in the same control.')
                seen.add(aid)
                text(actual.get('runtime_ref'), 'Fixed isolated runtime receipt')
        elif key.startswith('schedule_trigger:'):
            slot = next(s for s in scope['schedule']['slots'] if 'schedule_trigger:' + s['slot_id'] == key)
            if (evidence.get('thread_id') != scope['governance_thread']
                    or evidence.get('trigger') != 'natural_heartbeat' or evidence.get('ai_execution_verified') is not True):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Actual natural trigger and original-chat AI execution are distinct required evidence.')
            for field in ('automation_id', 'received_at', 'run_ref', 'update_check_ref', 'local_save_ref'):
                text(evidence.get(field), field)
            if slot['purpose'] == 'report':
                text(evidence.get('delivered_at'), 'Actual report delivery time')
                text(evidence.get('delivery_ref'), 'Actual report delivery reference')
            elif evidence.get('outcome') not in ('changed', 'quiet_no_change', 'needs_decision'):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Record the actual absorption outcome, including a quiet no-change run.')
        else:
            return super()._verify(scope, key, evidence)

    def _report(self, record):
        result = super()._report(record)
        complete = record['scope'].get('profile') == PROFILE
        result.update(profile=PROFILE if complete else 'legacy_v1', complete_governance_ready=complete and not result['pending'])
        if not complete:
            result['meaning'] += ' Legacy readiness does not attest complete_v1 governance coverage.'
            return result
        verified = []
        for slot in record['scope']['schedule']['slots']:
            key = 'schedule_trigger:' + slot['slot_id']
            item = record['items'].get(key, {})
            try:
                if item.get('status') != 'verified':
                    continue
                self._verify(record['scope'], key, item['evidence'])
                self._verify_item_binding(record, item)
                verified.append(slot['slot_id'])
            except GovernanceError:
                continue
        result.update(natural_trigger_verified=len(verified) == len(record['scope']['schedule']['slots']),
                      verified_natural_slots=verified,
                      closed_loop_verified=result['complete_governance_ready'] and len(verified) == len(record['scope']['schedule']['slots']))
        return result

    def schedule_plan(self, onboarding_id):
        record = self.onboarding(onboarding_id)['onboarding']
        scope = record['scope']
        if scope.get('profile') != PROFILE:
            return super().schedule_plan(onboarding_id)
        slots = []
        for slot in scope['schedule']['slots']:
            prompt = self._slot_prompt(scope, slot)
            slots.append({**slot, 'thread_id': scope['governance_thread'], 'kind': 'heartbeat', 'frequency': 'daily',
                          'timezone': scope['schedule']['timezone'], 'cwd': str(self.root), 'prompt': prompt,
                          'prompt_sha256': digest_bytes(prompt.encode('utf-8'))})
        return {'profile': PROFILE, 'slots': slots, 'control': str(self.root), 'execute': False,
                'preserve_model_and_permissions': True, 'natural_trigger_verified': False,
                'next_step': 'Use native host tools to create or reuse each exact original-chat slot, then read back all fields.'}
