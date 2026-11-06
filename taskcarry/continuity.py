"""Host-supplied evidence and bounded run receipts over existing local records.

These records do not read chats, authorize actions, run Git or accept business
outcomes. The host supplies its already-reviewed references; the shared engine
preserves their versions and checks only the selected recorded work.
"""
from __future__ import annotations

import json

from .core import Core, _id, digest_bytes
from .store import GovernanceError, now


def _fingerprint(value):
    return digest_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(',', ':'), allow_nan=False).encode('utf-8'))


def _text(value, label, maximum=2048):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\x00' in value:
        raise GovernanceError('INVALID_EVIDENCE', f'{label} must be nonempty text of at most {maximum} characters.')
    return value


def _ids(values, label):
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > 100:
        raise GovernanceError('INVALID_SELECTION', f'{label} must be a list of at most 100 identities.')
    result = [_id(value, label) for value in values]
    if len(set(result)) != len(result):
        raise GovernanceError('INVALID_SELECTION', f'{label} must not contain duplicates.')
    return sorted(result)


class Continuity(Core):
    def observe(self, observation_id, workspace, task_id, source_ref, source_revision,
                summary, relations=None, expected_revision=None):
        """Record a host-reviewed reference; replacing it requires its prior revision."""
        observation_id = _id(observation_id, 'Observation ID')
        workspace = _id(workspace, 'Workspace') if workspace is not None else None
        task_id = _id(task_id, 'Task ID')
        _text(source_ref, 'Source reference')
        _text(source_revision, 'Source revision', 512)
        _text(summary, 'Evidence summary', 8192)
        if expected_revision is not None and (isinstance(expected_revision, bool)
                or not isinstance(expected_revision, int) or expected_revision < 1):
            raise GovernanceError('INVALID_REVISION', 'Expected revision must be a positive integer.')
        if relations is None:
            relations = []
        if not isinstance(relations, list) or len(relations) > 100:
            raise GovernanceError('INVALID_RELATION', 'Evidence may name at most 100 explicit relationships.')
        with self.store.transaction():
            self._task(task_id)
            registered = self.store.get('workspaces', workspace) if workspace else None
            if workspace is not None and not registered:
                raise GovernanceError('WORKSPACE_UNKNOWN', 'Register this workspace before recording its evidence.')
            if registered and not registered.get('identity'):
                raise GovernanceError('WORKSPACE_IDENTITY_MISSING', 'The workspace needs a registered identity.')
            linked, seen = [], set()
            for relation in relations:
                if not isinstance(relation, dict) or set(relation) != {'kind', 'id'} or relation['kind'] not in ('stage', 'artifact'):
                    raise GovernanceError('INVALID_RELATION', 'Use a stage or artifact relationship with an exact id.')
                identity = _id(relation['id'], 'Related object ID')
                if workspace is None and relation['kind'] == 'stage':
                    raise GovernanceError('RELATION_SCOPE_MISMATCH', 'Git stages require their real registered workspace.')
                key = (relation['kind'], identity)
                if key in seen:
                    raise GovernanceError('INVALID_RELATION', 'Evidence relationships must be unique.')
                seen.add(key)
                collection = 'stages' if relation['kind'] == 'stage' else 'artifacts'
                item = self.store.get(collection, identity)
                if not item:
                    raise GovernanceError('RELATED_RECORD_UNKNOWN', 'Register the related object first.', relation)
                if item.get('task_id') != task_id or item.get('workspace', workspace) != workspace:
                    raise GovernanceError('RELATION_SCOPE_MISMATCH', 'A relationship must match the observed task and its workspace.', relation)
                content = ({'commit': item.get('commit'), 'base': item.get('base'), 'paths': item.get('paths'),
                            'declaration_hash': item.get('declaration_hash')} if relation['kind'] == 'stage'
                           else {'sha256': item.get('sha256'), 'size': item.get('size'), 'path': item.get('path')})
                linked.append({**relation, 'content_fingerprint': _fingerprint(content)})
            linked.sort(key=lambda value: (value['kind'], value['id']))
            body = {'observation_id': observation_id, 'workspace': workspace, 'task_id': task_id,
                    'workspace_identity': registered['identity'] if registered else None, 'source_ref': source_ref,
                    'source_revision': source_revision, 'summary': summary, 'relations': linked}
            fingerprint = _fingerprint(body)
            prior = self.store.get('observations', observation_id)
            if prior:
                if any(prior[key] != body[key] for key in ('workspace', 'task_id', 'source_ref')):
                    raise GovernanceError('OBSERVATION_ID_CONFLICT', 'An observation identity cannot move to another source, task or workspace.')
                if prior['fingerprint'] == fingerprint:
                    return {'observation': prior, 'reused': True}
                if expected_revision != prior['revision']:
                    raise GovernanceError('OBSERVATION_CHANGED', 'Reread the current observation before replacing it.',
                                          {'current_revision': prior['revision']})
            elif expected_revision is not None:
                raise GovernanceError('OBSERVATION_CHANGED', 'This observation does not yet have a revision.')
            revision = prior['revision'] + 1 if prior else 1
            record = {**body, 'fingerprint': fingerprint, 'revision': revision,
                      'recorded_at': now(), 'host_reviewed': True,
                      'meaning': 'Host-supplied evidence reference, not independent source verification or authorization.'}
            self.store.put('observations', observation_id, record)
            self.store.put('observation_history', observation_id + ':' + str(revision), record)
            self.store.event('observation_recorded', {'observation_id': observation_id, 'revision': revision,
                                                    'fingerprint': fingerprint, 'task_id': task_id})
            return {'observation': record, 'reused': False}

    @staticmethod
    def _read(db, collection, key):
        row = db.execute('SELECT value FROM records WHERE collection=? AND key=?', (collection, key)).fetchone()
        return json.loads(row[0]) if row else None

    @staticmethod
    def _covers(load, successor, identity):
        remaining, seen = list(successor.get('supersedes', [])), set()
        while remaining:
            ancestor = remaining.pop()
            if ancestor in seen:
                continue
            seen.add(ancestor)
            old = load('stages', ancestor)
            if (not old or old.get('task_id') != successor.get('task_id')
                    or old.get('workspace') != successor.get('workspace')):
                return False
            if ancestor == identity:
                return True
            remaining.extend(old.get('supersedes', []))
        return False

    @staticmethod
    def _stage_complete(load, identity):
        """Check receipt linkage; no external effects are executed or re-verified."""
        seen = set()
        while identity not in seen:
            seen.add(identity)
            stage = load('stages', identity)
            if not stage:
                return False, 'RECORD_MISSING'
            if stage.get('status') == 'COMMITTED':
                if not stage.get('accepted_commit'):
                    return False, 'RECEIPT_INCOMPLETE'
                if stage.get('operation_id'):
                    operation = load('operations', stage['operation_id'])
                    if (not operation or operation.get('status') != 'COMPLETED'
                            or operation.get('candidate') != stage['accepted_commit']
                            or operation.get('stage_id') != identity):
                        return False, 'RECEIPT_INCOMPLETE'
                return True, None
            if stage.get('status') != 'SUPERSEDED':
                return False, stage.get('code') or stage.get('status') or 'STATE_UNKNOWN'
            successor = load('stages', stage.get('successor', ''))
            if (not successor or successor.get('task_id') != stage.get('task_id')
                    or successor.get('workspace') != stage.get('workspace')
                    or not Continuity._covers(load, successor, identity)):
                return False, 'SUPERSESSION_UNVERIFIED'
            identity = successor['stage_id']
        return False, 'SUPERSESSION_CYCLE'

    @staticmethod
    def _operation_complete(load, identity, seen=None):
        """Follow verified named replacements without treating a label as proof."""
        seen = set() if seen is None else seen
        if identity in seen:
            return False, 'SUPERSESSION_CYCLE'
        seen.add(identity)
        operation = load('operations', identity)
        if not operation:
            return False, 'RECORD_MISSING'
        if operation.get('status') == 'SUPERSEDED':
            # Adoption retires only a no-effect preparation after its explicit
            # successor is verified. Never infer this from newer timestamps.
            successor = load('operations', operation.get('resolved_by_operation', ''))
            if (operation.get('kind') != 'adopt' or operation.get('effect_state') != 'NOT_APPLIED'
                    or operation.get('candidate') or operation.get('stash') or not successor
                    or successor.get('kind') != 'adopt'
                    or operation.get('workspace') != successor.get('workspace')
                    or operation.get('baseline') != successor.get('baseline')
                    or not operation.get('resolved_by_plan')
                    or operation['resolved_by_plan'] != successor.get('plan_id')
                    or identity not in successor.get('resolves_preparation_failures', [])):
                return False, 'SUPERSESSION_UNVERIFIED'
            return Continuity._operation_complete(load, successor['operation_id'], seen)
        if operation.get('status') != 'COMPLETED':
            return False, operation.get('code') or operation.get('status') or 'STATE_UNKNOWN'
        if operation.get('resolved_by_successor'):
            if operation.get('kind') != 'reconcile':
                return False, 'SUPERSESSION_UNVERIFIED'
            successor = load('stages', operation['resolved_by_successor'])
            if (not successor or operation.get('task_id') != successor.get('task_id')
                    or not operation.get('stage_id')
                    or not Continuity._covers(load, successor, operation['stage_id'])):
                return False, 'SUPERSESSION_UNVERIFIED'
            return Continuity._stage_complete(load, successor['stage_id'])
        if operation.get('kind') == 'reconcile':
            stage = load('stages', operation.get('stage_id', ''))
            if (not stage or not operation.get('candidate')
                    or stage.get('accepted_commit') != operation['candidate']
                    or stage.get('operation_id') not in (None, identity)
                    or stage.get('task_id') != operation.get('task_id')):
                return False, 'RECEIPT_INCOMPLETE'
            # A formerly received stage keeps its accepted_commit after a
            # cumulative successor. Check that successor rather than reopening
            # the old completed operation just because its stage was retired.
            return Continuity._stage_complete(load, stage['stage_id'])
        if operation.get('kind') == 'adopt':
            if operation.get('effect_state') == 'VERIFIED' and operation.get('candidate'):
                return True, None
            return False, 'RECEIPT_INCOMPLETE'
        if operation.get('kind') == 'restore':
            receipt = load('restore_receipts', identity)
            checkpoint = load('checkpoints', operation.get('checkpoint_id', ''))
            fields = ('operation_id', 'checkpoint_id', 'checkpoint_sha256', 'destination', 'effect_sha256')
            if (any(type(operation.get(key)) is not int or operation[key] != 1
                    for key in ('operation_protocol', 'restore_protocol'))
                    or operation.get('effect_state') != 'VERIFIED'
                    or not receipt or receipt.get('verified') is not True
                    or not checkpoint or checkpoint.get('task_id') != operation.get('task_id')
                    or Core._restore_digest(checkpoint) != operation.get('checkpoint_sha256')
                    or any(not operation.get(field) or receipt.get(field) != operation[field] for field in fields)):
                return False, 'RECEIPT_INCOMPLETE'
            # This closes a selected recorded operation, not a fresh claim
            # that the restored destination remains unchanged today.
            return True, None
        return False, 'OPERATION_KIND_UNSUPPORTED'

    def _inspection(self, record, load):
        pending, changed = [], []
        for identity in record['stage_ids']:
            complete, reason = self._stage_complete(load, identity)
            if not complete:
                pending.append({'kind': 'stage', 'id': identity, 'reason': reason})
        for identity in record['operation_ids']:
            complete, reason = self._operation_complete(load, identity)
            if not complete:
                pending.append({'kind': 'operation', 'id': identity, 'reason': reason})
        for identity in record['observation_ids']:
            observed = load('observations', identity)
            if not observed or observed.get('fingerprint') != record['observation_fingerprints'][identity]:
                changed.append(identity)
        return {'scope': 'selected_records', 'selected_complete': not pending,
                'pending': pending, 'changed_observations': changed,
                'effects_executed': False, 'project_complete': None,
                'meaning': 'Checks selected durable receipts only; does not reverify external effects, accept business outcomes or complete the project.'}

    def run(self, run_id, mode='start', stage_ids=None, operation_ids=None,
            observation_ids=None, note=''):
        """Freeze a finite selection, inspect its receipts, then record its closeout."""
        run_id = _id(run_id, 'Run ID')
        if mode not in ('start', 'finish', 'inspect'):
            raise GovernanceError('INVALID_RUN_MODE', 'Use start, finish or inspect.')
        if mode != 'inspect' and run_id in (self.store.get('config', 'project') or {}).get('recovery_inert_run_ids', []):
            raise GovernanceError('RESTORED_RUN_INERT', 'Historical runs cannot be replayed on a recovered replica.')
        if not isinstance(note, str) or len(note) > 8192 or '\x00' in note:
            raise GovernanceError('INVALID_NOTE', 'A run note must be text of at most 8192 characters.')
        supplied = (stage_ids, operation_ids, observation_ids)
        if mode != 'start' and (any(value is not None for value in supplied) or note):
            raise GovernanceError('RUN_SELECTION_FROZEN', 'Finish and inspect use the original selection and note.')
        if mode == 'inspect':
            with self.store._connect(readonly=True) as db:
                load = lambda collection, key: self._read(db, collection, key)
                record = load('runs', run_id)
                if not record:
                    raise GovernanceError('RUN_UNKNOWN', 'Start this run before inspecting it.')
                return {'run': record, 'inspection': self._inspection(record, load), 'reused': True}
        with self.store.transaction():
            prior = self.store.get('runs', run_id)
            if mode == 'start':
                selection = {'stage_ids': _ids(stage_ids, 'Stage ID'),
                             'operation_ids': _ids(operation_ids, 'Operation ID'),
                             'observation_ids': _ids(observation_ids, 'Observation ID')}
                if prior:
                    if any(prior[key] != value for key, value in selection.items()) or prior['note'] != note:
                        raise GovernanceError('RUN_ID_CONFLICT', 'This run already has a different frozen selection or note.')
                    return {'run': prior, 'inspection': self._inspection(prior, self.store.get), 'reused': True}
                for field, collection in (('stage_ids', 'stages'), ('operation_ids', 'operations'), ('observation_ids', 'observations')):
                    for identity in selection[field]:
                        if not self.store.get(collection, identity):
                            raise GovernanceError('RUN_RECORD_UNKNOWN', 'A selected record is not registered.',
                                                  {'kind': collection, 'id': identity})
                record = {'run_id': run_id, **selection, 'note': note, 'state': 'OPEN', 'created_at': now(),
                          'observation_fingerprints': {identity: self.store.get('observations', identity)['fingerprint']
                                                       for identity in selection['observation_ids']}}
                self.store.put('runs', run_id, record)
                self.store.event('run_started', {'run_id': run_id, **selection})
                return {'run': record, 'inspection': self._inspection(record, self.store.get), 'reused': False}
            if not prior:
                raise GovernanceError('RUN_UNKNOWN', 'Start this run before finishing it.')
            inspection = self._inspection(prior, self.store.get)
            state = 'COMPLETED' if inspection['selected_complete'] else 'WAITING'
            if prior.get('last_inspection') == inspection and prior['state'] == state:
                return {'run': prior, 'inspection': inspection, 'reused': True}
            record = {**prior, 'state': state, 'last_inspection': inspection, 'checked_at': now()}
            if state == 'COMPLETED':
                record['completed_at'] = prior.get('completed_at', now())
            elif 'completed_at' in record:
                record['previous_completed_at'] = record.pop('completed_at')
            self.store.put('runs', run_id, record)
            self.store.event('run_finished' if state == 'COMPLETED' else 'run_waiting',
                             {'run_id': run_id, 'inspection': inspection})
            return {'run': record, 'inspection': inspection, 'reused': False}
