"""Observe a governance composition and retain explicit, content-bound reviews.

The installed package, managed methods and user rules have independent identity.
Recording a review never installs a package or certifies another host process.
"""
from __future__ import annotations

import json

from .core import Core, _id, digest_bytes, read_file_bytes, validate_relative_path
from .maintenance import _revision, _text
from .setup import runtime_info
from .store import GovernanceError, now


def _fingerprint(value):
    return digest_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(',', ':')).encode('utf-8'))


class Governance(Core):
    def governance(self, mode='inspect', rule_paths=None, record_id=None,
                   expected_fingerprint=None, evidence_refs=None, expected_revision=None):
        if mode not in ('inspect', 'record'):
            raise GovernanceError('INVALID_ARGUMENT', 'Use inspect or record.')
        paths = [] if rule_paths is None else rule_paths
        if (not isinstance(paths, list) or len(paths) > 100
                or any(not isinstance(path, str) for path in paths)
                or len({path.casefold() for path in paths}) != len(paths)):
            raise GovernanceError('INVALID_ARGUMENT', 'Select at most 100 unique project-relative rule files.')
        rules = []
        for path in sorted(paths):
            content = read_file_bytes(validate_relative_path(self.root, path, allow_missing=False))
            rules.append({'path': path, 'sha256': digest_bytes(content), 'size': len(content),
                          'origin': 'user_project', 'update_policy': 'preserve_and_review_conflicts'})
        runtime = runtime_info(self.root)
        loaded = runtime.get('loaded_runtime', {})
        composition = {
            'schema_version': 1, 'control': str(self.root),
            'core': {key: loaded.get(key) for key in
                     ('version', 'interpreter', 'module_root', 'source_sha256')},
            'methods': {'version': runtime.get('managed_setup_version'),
                        'status': runtime.get('setup_status'),
                        'files': runtime.get('files', []),
                        'managed_files_match': runtime.get('managed_files_match'),
                        'pending_installation': runtime.get('pending_installation')},
            'user_rules': rules,
            'identity_scope': 'current_process_location_and_on_disk_content',
        }
        fingerprint = _fingerprint(composition)
        result = {'composition': composition, 'fingerprint': fingerprint,
                  'host_loading_verified': False, 'loaded_code_verified': False,
                  'package_upgrade_performed': False,
                  'meaning': 'Observed composition; user rules remain separate from package methods. '
                             'A saved review is not installation, host reload, or problem resolution.'}
        if mode == 'inspect':
            if any(value is not None for value in (record_id, expected_fingerprint, evidence_refs, expected_revision)):
                raise GovernanceError('INVALID_ARGUMENT', 'Review fields are only valid in record mode.')
            return result
        key = _id(record_id, 'Governance review ID')
        if expected_fingerprint != fingerprint:
            raise GovernanceError('COMPOSITION_CHANGED', 'Inspect the current composition before recording its review.',
                                  {'current_fingerprint': fingerprint})
        if not isinstance(evidence_refs, list) or not evidence_refs or len(evidence_refs) > 50:
            raise GovernanceError('INVALID_ARGUMENT', 'Provide 1-50 reviewed evidence references.')
        for ref in evidence_refs:
            _text(ref, 'evidence_refs item')
        body = {'record_id': key, 'fingerprint': fingerprint, 'composition': composition,
                'evidence_refs': sorted(set(evidence_refs)), 'evidence_scope': 'host_reviewed_references',
                'host_loading_verified': False, 'package_upgrade_performed': False}
        with self.store.transaction():
            # Recheck disk identities inside the guard before publishing a review.
            current = self.governance(rule_paths=paths)
            if current['fingerprint'] != fingerprint:
                raise GovernanceError('COMPOSITION_CHANGED', 'The composition changed before recording.')
            previous = self.store.get('governance_reviews', key)
            if previous and all(previous.get(k) == v for k, v in body.items()):
                result.update(review=previous, reused=True)
                return result
            revision = _revision(expected_revision, previous)
            record = dict(body, revision=revision,
                          created_at=previous['created_at'] if previous else now(), updated_at=now())
            self.store.put('governance_reviews', key, record)
            self.store.put('governance_review_history', key + '.' + str(revision), record)
            self.store.event('governance_review_recorded', {'record_id': key, 'fingerprint': fingerprint,
                                                         'revision': revision})
        result.update(review=record, reused=False)
        return result
