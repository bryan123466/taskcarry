"""Explicit legacy identity adoption; reads never initialize or migrate state."""
import json
import uuid

from .core import Core, _id, digest_bytes
from .store import GovernanceError, now


def _fingerprint(value):
    return digest_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(',', ':')).encode('utf-8'))


class ProjectIdentity(Core):
    def identity(self, action='status', plan_id=None):
        if action == 'status':
            if plan_id is not None:
                raise GovernanceError('IDENTITY_ARGUMENT', 'Status does not accept a plan.')
            return {'source': self.source(), 'effects_executed': False}
        if action not in ('plan', 'execute'):
            raise GovernanceError('IDENTITY_ACTION', 'Use status, plan or execute.')
        with self.store.transaction():
            config = self.store.get('config', 'project')
            if action == 'plan':
                if plan_id is not None:
                    raise GovernanceError('IDENTITY_ARGUMENT', 'Plan does not accept a prior plan ID.')
                if config.get('project_id'):
                    return {'source': self.source(), 'state': 'ALREADY_PORTABLE', 'effects_executed': False}
                fingerprint = _fingerprint(config)
                pid = 'identity-' + fingerprint[:24]
                prior = self.store.get('identity_plans', pid)
                if prior:
                    return prior
                plan = {'plan_id': pid, 'state': 'PLANNED', 'config_fingerprint': fingerprint,
                        'previous_source': self.source(), 'project_id': 'project-' + uuid.uuid4().hex,
                        'replica_id': 'replica-' + uuid.uuid4().hex, 'created_at': now()}
                self.store.put('identity_plans', pid, plan)
                return plan
            plan = self.store.get('identity_plans', _id(plan_id, 'Identity plan'))
            if not plan:
                raise GovernanceError('IDENTITY_PLAN_UNKNOWN', 'Prepare a legacy identity plan first.')
            if config.get('project_id') == plan['project_id']:
                return {'source': self.source(), 'state': 'COMPLETED', 'reused': True}
            if _fingerprint(config) != plan['config_fingerprint']:
                raise GovernanceError('IDENTITY_CHANGED', 'Project configuration changed; prepare a new plan.')
            config.update(project_id=plan['project_id'], replica_id=plan['replica_id'],
                          source_aliases=[plan['previous_source']['source_id']])
            self.store.put('config', 'project', config)
            self.store.put('identity_plans', plan['plan_id'], {**plan, 'state': 'COMPLETED'})
            self.store.event('project_identity_adopted', {'plan_id': plan['plan_id'], 'source': self.source()})
            return {'source': self.source(), 'state': 'COMPLETED', 'reused': False}
