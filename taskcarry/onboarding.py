"""Resumable, evidence-qualified onboarding; never activates a host or scheduler."""
from __future__ import annotations

import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .core import Core, _id, digest_bytes
from .gitops import repo, identity
from .store import GovernanceError, now


def fingerprint(value):
    return digest_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(',', ':'), allow_nan=False).encode('utf-8'))


def text(value, label, maximum=8192):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\0' in value:
        raise GovernanceError('ONBOARDING_EVIDENCE', f'{label} requires bounded nonempty text.')
    return value


class Onboarding(Core):
    def _scope(self, scope):
        if not isinstance(scope, dict) or set(scope) != {'governance_thread', 'windows', 'schedule', 'channel'}:
            raise GovernanceError('ONBOARDING_SCOPE', 'Specify governance_thread, windows, schedule and channel.')
        text(scope['governance_thread'], 'Governance thread', 256)
        if scope['channel'] not in ('stable', 'rc'):
            raise GovernanceError('ONBOARDING_SCOPE', 'Select stable or rc updates.')
        schedule = scope['schedule']
        if (not isinstance(schedule, dict) or set(schedule) != {'time', 'timezone'}
                or not isinstance(schedule['time'], str)
                or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', schedule['time'])):
            raise GovernanceError('ONBOARDING_SCOPE', 'Specify a daily HH:MM time and timezone.')
        text(schedule['timezone'], 'Timezone', 128)
        # ZoneInfo databases are not bundled on every supported Windows host.
        # Require the host to verify its zone in the schedule readback below.
        try:
            ZoneInfo(schedule['timezone'])
        except ZoneInfoNotFoundError:
            if not re.fullmatch(r'[A-Za-z_]+(?:/[A-Za-z0-9_+.-]+)+|UTC', schedule['timezone']):
                raise GovernanceError('ONBOARDING_SCOPE', 'Use a named IANA timezone.')
        windows = scope['windows']
        if not isinstance(windows, list) or not windows or len(windows) > 100:
            raise GovernanceError('ONBOARDING_SCOPE', 'Select 1-100 explicit windows or history sources.')
        seen = set()
        for window in windows:
            if not isinstance(window, dict) or window.get('mode') not in ('active', 'reference'):
                raise GovernanceError('ONBOARDING_SCOPE', 'Each window needs active or reference mode.')
            allowed = {'thread_id', 'mode', 'task_id', 'workspace', 'source_ref', 'responsibility'}
            if set(window) - allowed:
                raise GovernanceError('ONBOARDING_SCOPE', 'Unknown window fields.')
            tid = text(window.get('thread_id'), 'Thread ID', 256)
            if tid in seen:
                raise GovernanceError('ONBOARDING_SCOPE', 'Duplicate thread selection.')
            seen.add(tid)
            text(window.get('source_ref'), 'Source reference')
            text(window.get('responsibility'), 'Responsibility', 2048)
            if window['mode'] == 'active':
                _id(window.get('task_id'), 'Task ID')
                _id(window.get('workspace'), 'Workspace')
        return json.loads(json.dumps(scope))

    @staticmethod
    def _keys(scope):
        return ['scope', 'runtime', 'local_git', 'update_check', 'schedule_config'] + [
            'window:' + item['thread_id'] for item in scope['windows'] if item['mode'] == 'active']

    def _optional_keys(self, scope):
        return ['schedule_trigger', 'remote', 'cloud']

    def _verify_item_binding(self, prior, item):
        if item['key'] == 'schedule_trigger':
            cfg = prior['items'].get('schedule_config', {}).get('evidence', {})
            if cfg.get('automation_id') != item['evidence']['automation_id']:
                raise GovernanceError('ONBOARDING_BINDING', 'Natural trigger must match the configured automation.')

    def _verify(self, scope, key, evidence):
        if not isinstance(evidence, dict) or len(json.dumps(evidence)) > 65536:
            raise GovernanceError('ONBOARDING_EVIDENCE', 'Use bounded structured evidence.')
        text(evidence.get('receipt_ref'), 'Actual evidence receipt reference')
        if key.startswith('window:'):
            window = next(w for w in scope['windows'] if 'window:' + w['thread_id'] == key)
            self._task(window['task_id'])
            registered = self.store.get('workspaces', window['workspace'])
            if not registered or 'path' not in registered:
                raise GovernanceError('WORKSPACE_UNKNOWN', 'Prepare and register the actual Git worktree first.')
            path = repo(registered['path'])
            if identity(path) != registered['identity']:
                raise GovernanceError('WORKSPACE_CHANGED', 'Recheck the registered Git identity.')
            expected = {'thread_id': window['thread_id'], 'task_id': window['task_id'],
                        'workspace': window['workspace'], 'transport': 'native_mcp',
                        'doctor_ok': True, 'status_ok': True}
            if any(evidence.get(k) != v for k, v in expected.items()):
                raise GovernanceError('ONBOARDING_BINDING', 'Use native doctor/status from the selected window and task.')
            if Path(text(evidence.get('cwd'), 'Actual cwd')).resolve() != path:
                raise GovernanceError('ONBOARDING_BINDING', 'The host cwd must match its registered worktree.')
            if Path(text(evidence.get('control'), 'Actual control')).resolve() != self.root:
                raise GovernanceError('ONBOARDING_BINDING', 'The native calls must use this control.')
            runtime = evidence.get('runtime', {})
            if not isinstance(runtime, dict):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Use a structured native runtime result.')
            for field in ('version', 'interpreter', 'module_root'):
                text(runtime.get(field), 'Runtime ' + field)
        elif key == 'scope':
            if evidence.get('user_confirmed') is not True or evidence.get('scope_fingerprint') != fingerprint(scope):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Confirm this exact project/window scope.')
        elif key == 'runtime':
            if evidence.get('isolated') is not True:
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Verify isolated package startup.')
            required = {'thread_id': scope['governance_thread'], 'transport': 'native_mcp',
                        'doctor_ok': True, 'status_ok': True}
            if any(evidence.get(k) != v for k, v in required.items()):
                raise GovernanceError('ONBOARDING_BINDING', 'Verify native doctor/status in the governance window itself.')
            if Path(text(evidence.get('control'), 'Governance control')).resolve() != self.root:
                raise GovernanceError('ONBOARDING_BINDING', 'The governance window must use this control.')
            for field in ('version', 'interpreter', 'module_root', 'identity_ref'):
                text(evidence.get(field), 'Runtime ' + field)
        elif key == 'local_git':
            from .preservation import Preservation
            plan = Preservation(self.root).preserve(action='status', plan_id=text(evidence.get('plan_id'), 'Save plan'))
            if plan['state'] != 'COMPLETED' or plan.get('commit') != evidence.get('commit'):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Reference an actual completed local preservation record.')
        elif key == 'update_check':
            if evidence.get('channel') != scope['channel'] or evidence.get('checked') is not True:
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Check the selected official release channel.')
            if evidence.get('source') != 'https://github.com/bryan123466/taskcarry/releases':
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Use the official release source.')
            text(evidence.get('result_fingerprint'), 'Update result fingerprint', 128)
            text(evidence.get('assessment_ref'), 'Update assessment')
            assessment = self.store.get('update_assessments', evidence['assessment_ref'])
            source = self.store.get('update_sources', 'official')
            if not assessment or not source:
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Save the official source and actual update assessment first.')
            check = assessment.get('check', {})
            if (assessment.get('check_fingerprint') != evidence['result_fingerprint']
                    or check.get('fingerprint') != evidence['result_fingerprint']
                    or check.get('channel') != scope['channel'] or source.get('channel') != scope['channel']
                    or check.get('source_revision') != source.get('revision')
                    or check.get('release_source') != evidence['source']
                    or check.get('status') not in ('CANDIDATE', 'CURRENT_MATCHES', 'CURRENT_IDENTITY_INCOMPLETE',
                                                 'NO_RELEASE_IN_WINDOW', 'NO_NEWER_RELEASE_IN_WINDOW',
                                                 'LEGACY_REVIEW_REQUIRED', 'SAME_VERSION_CONFLICT')):
                raise GovernanceError('ONBOARDING_EVIDENCE', 'Use a current, completed official check; offline/unverified remains pending.')
        elif key == 'schedule_config':
            expected = {'thread_id': scope['governance_thread'], 'time': scope['schedule']['time'],
                        'timezone': scope['schedule']['timezone'], 'frequency': 'daily',
                        'readback': True, 'active': True, 'kind': 'heartbeat',
                        'prompt_sha256': digest_bytes(self._prompt(scope).encode('utf-8'))}
            if any(evidence.get(k) != v for k, v in expected.items()):
                raise GovernanceError('ONBOARDING_BINDING', 'Read back the exact native schedule, original thread and prompt.')
            text(evidence.get('automation_id'), 'Automation ID', 256)
            if Path(text(evidence.get('cwd'), 'Schedule working directory')).resolve() != self.root:
                raise GovernanceError('ONBOARDING_BINDING', 'The native schedule must use the selected governance directory.')
            text(evidence.get('runtime_ref'), 'Verified fixed runtime identity reference')
        elif key == 'schedule_trigger':
            if evidence.get('thread_id') != scope['governance_thread'] or evidence.get('trigger') != 'natural_heartbeat':
                raise GovernanceError('ONBOARDING_EVIDENCE', 'A manual run is not a natural heartbeat.')
            for field in ('automation_id', 'received_at', 'run_ref', 'update_check_ref', 'local_save_ref'):
                text(evidence.get(field), field)
        elif key in ('remote', 'cloud'):
            text(evidence.get('coverage_ref'), 'Explicit capture/upload/download/restore coverage')
            text(evidence.get('destination'), 'User-selected destination')

    def _report(self, record):
        scope, items = record['scope'], record['items']
        pending, invalid = [], {}
        for key in self._keys(scope):
            item = items.get(key)
            if not item or item['status'] != 'verified':
                pending.append(key)
                continue
            try:
                self._verify(scope, key, item['evidence'])
            except (GovernanceError, OSError) as error:
                pending.append(key)
                invalid[key] = {'code': getattr(error, 'code', 'ONBOARDING_EVIDENCE_UNAVAILABLE'),
                                'message': getattr(error, 'message', str(error))}
        trigger = items.get('schedule_trigger', {})
        config = items.get('schedule_config', {})
        natural = (trigger.get('status') == 'verified' and config.get('status') == 'verified'
                   and 'schedule_config' not in pending and trigger.get('evidence', {}).get('automation_id')
                   == config.get('evidence', {}).get('automation_id'))
        return {'onboarding': record, 'required': self._keys(scope), 'pending': pending,
                'invalidated': invalid, 'standard_ready': not pending,
                'natural_trigger_verified': bool(natural), 'closed_loop_verified': not pending and bool(natural),
                'evidence_scope': 'host_reviewed_receipts_and_live_local_bindings',
                'host_effects_executed': False,
                'meaning': 'Recorded host evidence is not independent host access; configuration and natural trigger are distinct.'}

    def onboarding(self, onboarding_id, action='status', scope=None, item=None, expected_revision=None):
        onboarding_id = _id(onboarding_id, 'Onboarding ID')
        if action not in ('start', 'update', 'status'):
            raise GovernanceError('ONBOARDING_ACTION', 'Use start, update or status.')
        if expected_revision is not None and (type(expected_revision) is not int or expected_revision < 1):
            raise GovernanceError('INVALID_REVISION', 'Use a positive expected revision.')
        if action == 'status':
            if any(value is not None for value in (scope, item, expected_revision)):
                raise GovernanceError('ONBOARDING_ACTION', 'Status does not accept update fields.')
            record = self.store.get('onboarding', onboarding_id)
            if not record:
                raise GovernanceError('ONBOARDING_UNKNOWN', 'Start this onboarding first.')
            return self._report(record)
        with self.store.transaction():
            prior = self.store.get('onboarding', onboarding_id)
            if action == 'start':
                if item is not None:
                    raise GovernanceError('ONBOARDING_ACTION', 'Start does not accept an item update.')
                scope = self._scope(scope)
                body = {'onboarding_id': onboarding_id, 'scope': scope, 'items': {}}
                if prior and prior['scope'] == scope:
                    return {**self._report(prior), 'reused': True}
            else:
                if scope is not None:
                    raise GovernanceError('ONBOARDING_ACTION', 'Use start with an expected revision to replace the scope.')
                if not prior:
                    raise GovernanceError('ONBOARDING_UNKNOWN', 'Start this onboarding first.')
                if not isinstance(item, dict) or set(item) != {'key', 'status', 'evidence', 'next_step'}:
                    raise GovernanceError('ONBOARDING_EVIDENCE', 'Provide key, status, evidence and next_step.')
                allowed = self._keys(prior['scope']) + self._optional_keys(prior['scope'])
                if item['key'] not in allowed or item['status'] not in ('verified', 'pending', 'declined'):
                    raise GovernanceError('ONBOARDING_EVIDENCE', 'Unknown item or status.')
                if item['status'] == 'verified':
                    self._verify(prior['scope'], item['key'], item['evidence'])
                    self._verify_item_binding(prior, item)
                else:
                    if not isinstance(item['evidence'], dict):
                        raise GovernanceError('ONBOARDING_EVIDENCE', 'Use a structured evidence object, including pending items.')
                    text(item['next_step'], 'Remaining step')
                if not isinstance(item['next_step'], str) or len(json.dumps(item)) > 65536:
                    raise GovernanceError('ONBOARDING_EVIDENCE', 'Use bounded item text.')
                body = {k: prior[k] for k in ('onboarding_id', 'scope', 'items')}
                body['items'] = {**body['items'], item['key']: item}
                if prior['items'].get(item['key']) == item:
                    return {**self._report(prior), 'reused': True}
            if prior and expected_revision != prior['revision']:
                raise GovernanceError('ONBOARDING_CHANGED', 'Reread onboarding before changing it.', {'revision': prior['revision']})
            if not prior and expected_revision is not None:
                raise GovernanceError('ONBOARDING_CHANGED', 'This onboarding has no prior revision.')
            record = {**body, 'revision': prior['revision'] + 1 if prior else 1, 'updated_at': now(),
                      'scope_fingerprint': fingerprint(body['scope'])}
            self.store.put('onboarding', onboarding_id, record)
            self.store.put('onboarding_history', onboarding_id + ':' + str(record['revision']), record)
            self.store.event('onboarding_updated', {'onboarding_id': onboarding_id, 'revision': record['revision']})
            return {**self._report(record), 'reused': False}

    def _prompt(self, scope):
        selected = [{'task_id': w['task_id'], 'workspace': w['workspace']} for w in scope['windows'] if w['mode'] == 'active']
        return ('Continue this original governance conversation using its existing model and permissions. '
                'Use the fixed isolated TaskCarry runtime and control ' + str(self.root) + '. '
                'Read its recorded runtime identity before executing; do not import source from cwd. '
                'Selected active tasks/workspaces: ' + json.dumps(selected, sort_keys=True) + '. '
                'Reference-only historical chats do not become active work. '
                'Read bounded agenda and relevant task context; verify actual effects before retrying. '
                'Continue only authorized work, retain decisions and next steps, and preserve exact local Git files. '
                'Check https://github.com/bryan123466/taskcarry/releases on the ' + scope['channel'] +
                ' channel and record an applicability assessment; do not install updates automatically. '
                'No change means no new task, commit or repeated reminder. Report effects, evidence and missing conditions. '
                'Do not publish, message other chats or change production scope without authorization. '
                'A skipped interval is not permission to replay all previous work.')

    def schedule_plan(self, onboarding_id):
        record = self.onboarding(onboarding_id)['onboarding']
        scope = record['scope']
        prompt = self._prompt(scope)
        return {'thread_id': scope['governance_thread'], 'kind': 'heartbeat', 'frequency': 'daily',
                **scope['schedule'], 'prompt': prompt, 'prompt_sha256': digest_bytes(prompt.encode('utf-8')),
                'control': str(self.root), 'action': 'create_or_reuse_with_native_host', 'execute': False,
                'preserve_model_and_permissions': True, 'natural_trigger_verified': False,
                'next_step': 'Use supported native host scheduling; read back this exact configuration. Do not edit host databases.'}
