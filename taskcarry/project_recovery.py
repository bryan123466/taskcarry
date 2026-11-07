"""Portable selected recovery sets and independent, inert restored replicas.

The media is an ordinary local directory suitable for a static offsite copy.
No live SQLite synchronization, remote writer fencing, credential copying or
host configuration is implied by a successful local recovery receipt.
"""
from contextlib import closing
import copy
import json
import os
from pathlib import Path
import sqlite3
import sys
import uuid

from . import __version__
from .core import Core, _id, read_file_bytes
from .store import Store, GovernanceError, now
from .state_format import inspect_state
from . import recovery_git as rg
from .recovery_files import (MAX_BYTES, MAX_FILE, MAX_FILES, SHA, atomic, digest, disjoint,
                             encoded, get, lock, normal, put, read_json, relative, safe, write_json)

SCHEMA = 'taskcarry.project-recovery.v1'
PLAN_SCHEMA = 'taskcarry.recovery-plan.v1'


def _baseline_recovery(binding, components, registered, prior=None):
    """Resolve an executable baseline only through its exact captured identity."""
    if not binding:
        if prior and prior.get('status') == 'REBIND_REQUIRED':
            return {'status': 'REBIND_REQUIRED', 'component': None,
                    'reason': 'The captured replica already requires a reviewed baseline recovery.'}
        return {'status': 'NOT_BOUND', 'component': None}
    matches = [c for c in components if c['kind'] == 'git'
               and normal(c['source']) == normal(binding.get('path', ''))
               and c.get('git', {}).get('branch') == binding.get('branch')
               and any(w.get('identity') == binding for w in registered.values())]
    if len(matches) == 1:
        return {'status': 'MAPPED', 'component': matches[0]['name']}
    return {'status': 'REBIND_REQUIRED', 'component': None,
            'reason': 'The bound baseline has no unique selected Git component with its registered source identity and branch.'}


def _complete_scope(value, baseline):
    return (baseline.get('status') != 'REBIND_REQUIRED'
            and not any(value.get(k) for k in ('missing_workspace_payloads', 'missing_artifact_payloads', 'missing_history_dependencies')))


def _state_references(rows):
    for collection, _, value in rows:
        if collection == 'checkpoints':
            yield from _refs(value.get('files', []))
        elif collection == 'preservation':
            yield from _refs([value.get('index_before'), value.get('index_after')])
        elif collection == 'recovery_history' and isinstance(value, dict):
            # Older recovery generations retain checkpoint/plan objects too.
            yield from _state_references([(value.get('original_collection'), value.get('original_key'), value.get('record', {}))])


def _state_rows(path):
    try:
        with closing(sqlite3.connect(normal(path).as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise GovernanceError('RECOVERY_STATE_CORRUPT', 'The governance snapshot failed SQLite integrity checking.')
            inspected = inspect_state(db)
            if inspected['state'] == 'unsupported':
                raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'The snapshot governance schema is unsupported.')
            if inspected['state'] != 'compatible':
                raise GovernanceError('RECOVERY_STATE_CORRUPT', 'The snapshot is not a complete supported TaskCarry state database.',
                                      {'reason': inspected['reason']})
            return [(c, k, json.loads(v)) for c, k, v in db.execute('SELECT collection,key,value FROM records')]
    except (sqlite3.Error, ValueError, TypeError, UnicodeError) as exc:
        raise GovernanceError('RECOVERY_STATE_CORRUPT', 'The governance snapshot cannot be read safely.') from exc


def _state_fingerprint(store):
    with store._connect(readonly=True) as db:
        records = list(db.execute('SELECT collection,key,value FROM records ORDER BY collection,key'))
        events = list(db.execute('SELECT sequence,created_at,kind,payload FROM events ORDER BY sequence'))
    return {'records_sha256': digest(encoded(records)), 'events_sha256': digest(encoded(events)),
            'records': len(records), 'events': len(events)}


def _archive(store, restore_id, collection, key, record):
    store.put('recovery_history', restore_id + ':' + collection + ':' + key,
              {'original_collection': collection, 'original_key': key, 'record': record,
               'restore_id': restore_id, 'executable': False})


def _refs(value):
    """Find only structurally explicit content-store references."""
    if isinstance(value, dict):
        if set(('sha256', 'size')).issubset(value):
            yield {'sha256': value['sha256'], 'size': value['size']}
        for child in value.values():
            yield from _refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _refs(child)


def _payload_refs(value):
    return _refs({'snapshot': value['state']['snapshot'], 'objects': value['state']['objects'],
                  'components': value['components']})


def _manifest(path, expected=None):
    try:
        return _manifest_data(path, expected)
    except (KeyError, TypeError, AttributeError, IndexError, RecursionError) as exc:
        raise GovernanceError('RECOVERY_MANIFEST', 'Recovery manifest structure is incomplete or invalid.') from exc


def _manifest_data(path, expected=None):
    value, checksum = read_json(path)
    if expected is not None and checksum != expected:
        raise GovernanceError('RECOVERY_MANIFEST_MISMATCH', 'The recovery manifest differs from the reviewed digest.')
    if not isinstance(value, dict) or value.get('schema') != SCHEMA:
        raise GovernanceError('RECOVERY_SCHEMA_UNSUPPORTED', 'Use a compatible project recovery reader.')
    if value.get('state', {}).get('schema_version') != 1 or type(value['state']['schema_version']) is not int:
        raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'The captured governance schema is unsupported.')
    if value.get('runtime', {}).get('python_minimum') != '3.11' or value['runtime'].get('recovery_schema') != 1:
        raise GovernanceError('RECOVERY_SCHEMA_UNSUPPORTED', 'The recovery runtime requirements are unsupported.')
    _id(value.get('set_id'), 'Recovery set')
    targets, names, count = [], set(), 0
    components = value.get('components')
    if not isinstance(components, list) or len(components) > 200:
        raise GovernanceError('RECOVERY_MANIFEST', 'Invalid recovery component list.')
    for component in components:
        _id(component.get('name'), 'Recovery component')
        target = relative(component.get('target')).as_posix()
        if target != 'control' and not target.startswith(('workspaces/', 'payloads/')):
            raise GovernanceError('RECOVERY_MANIFEST', 'Unsupported recovery target.')
        if component['name'].casefold() in names or any(target.casefold() == t or target.casefold().startswith(t + '/') or t.startswith(target.casefold() + '/') for t in targets):
            raise GovernanceError('RECOVERY_MANIFEST', 'Recovery component identities or destinations overlap.')
        names.add(component['name'].casefold()); targets.append(target.casefold())
        if component.get('kind') not in ('git', 'files') or not isinstance(component.get('files'), list):
            raise GovernanceError('RECOVERY_MANIFEST', 'Unsupported component kind or file list.')
        seen = set()
        for item in component['files']:
            name = relative(item.get('path')).as_posix()
            if name.split('/')[0].casefold() == '.taskcarry-disabled-host':
                raise GovernanceError('RECOVERY_MANIFEST', 'A selected input collides with the recovery host-quarantine namespace.')
            # Reject internal metadata, secret filenames, symlinks and aliases on import too.
            from .core import validate_relative_path
            validate_relative_path(Path(path).parent / 'validation-only', name)
            if name.casefold() in seen:
                raise GovernanceError('RECOVERY_MANIFEST', 'Duplicate recovery file path.')
            seen.add(name.casefold()); count += 1
            if not item.get('missing') and item.get('mode') not in ('100644', '100755'):
                raise GovernanceError('RECOVERY_MANIFEST', 'Unsupported recovery file mode.')
        if component['kind'] == 'git':
            info = component.get('git', {})
            if info.get('object_format') not in ('sha1', 'sha256'):
                raise GovernanceError('RECOVERY_MANIFEST', 'Unsupported Git object format.')
            if info.get('branch') is not None and info.get('branch') not in info.get('refs', {}):
                raise GovernanceError('RECOVERY_MANIFEST', 'The current branch is not in the preserved refs.')
            for name, target in info.get('symbolic_refs', {}).items():
                if name not in info.get('refs', {}) or target not in info['refs']:
                    raise GovernanceError('RECOVERY_MANIFEST', 'Symbolic refs require their selected target dependencies.')
            for oid in [info.get('head'), *[i.get('oid') for i in info.get('index', [])]]:
                if not isinstance(oid, str) or len(oid) not in (40, 64) or any(c not in '0123456789abcdef' for c in oid):
                    raise GovernanceError('RECOVERY_MANIFEST', 'Invalid Git object identity.')
            for name, oid in info.get('refs', {}).items():
                if not name.startswith('refs/') or any(c in name for c in '\0\r\n :~^?*[') or '..' in name or '@{' in name:
                    raise GovernanceError('RECOVERY_MANIFEST', 'Unsafe Git ref in recovery manifest.')
                if not isinstance(oid, str) or len(oid) not in (40, 64) or any(c not in '0123456789abcdef' for c in oid):
                    raise GovernanceError('RECOVERY_MANIFEST', 'Invalid Git object identity.')
            for item in info.get('index', []):
                validate_relative_path(Path(path).parent / 'validation-only', item.get('path'))
                if item.get('mode') not in ('100644', '100755'):
                    raise GovernanceError('RECOVERY_MANIFEST', 'Unsupported index mode.')
    if count > MAX_FILES * 4:
        raise GovernanceError('RECOVERY_BUDGET', 'Recovery manifest exceeds the selected file budget.')
    refs = list(_payload_refs(value))
    unique = {}
    for ref in refs:
        if not isinstance(ref['sha256'], str) or not SHA.fullmatch(ref['sha256']) or type(ref['size']) is not int or not 0 <= ref['size'] <= MAX_BYTES:
            raise GovernanceError('RECOVERY_MANIFEST', 'Invalid payload identity.')
        if ref['sha256'] in unique and unique[ref['sha256']] != ref['size']:
            raise GovernanceError('RECOVERY_MANIFEST', 'Contradictory content-addressed payload sizes.')
        unique[ref['sha256']] = ref['size']
    if sum(unique.values()) > MAX_BYTES * 4:
        raise GovernanceError('RECOVERY_BUDGET', 'Recovery set exceeds the aggregate byte budget.')
    return value, checksum


class ProjectRecovery(Core):
    def __init__(self, project):
        # Verification and disaster restore must work without the original state.
        self.root = normal(project)
        self.store = None
        if (self.root / '.taskcarry' / 'state.sqlite3').is_file():
            super().__init__(project)
        self.ledger = self.root / ('.taskcarry/recovery' if self.store is not None else '.taskcarry-recovery')

    def _require_store(self):
        if self.store is None:
            raise GovernanceError('RECOVERY_STATE_REQUIRED', 'Backup and writer handoff require an existing governance state.')

    def _plan_path(self, plan_id):
        return safe(self.ledger, _id(plan_id, 'Recovery plan') + '.json')

    def _load_plan(self, plan_id, kind=None):
        try:
            value, _ = read_json(self._plan_path(plan_id))
        except FileNotFoundError as exc:
            raise GovernanceError('RECOVERY_PLAN_NOT_FOUND', 'Read or create the exact recovery plan first.') from exc
        if value.get('schema') != PLAN_SCHEMA or value.get('plan_id') != plan_id or kind and value.get('kind') != kind:
            raise GovernanceError('RECOVERY_PLAN_MISMATCH', 'This plan is not compatible with the requested recovery action.')
        return value

    def recovery(self, action, destination=None, plan_id=None, manifest=None, expected_sha256=None,
                 workspaces=None, payloads=None, authorization=None, old_writer_stopped=False,
                 native_evidence=None, old_replica_id=None, collection=None, local_id=None, cursor=None, limit=20):
        allowed = {'backup_plan': {'destination', 'workspaces', 'payloads'}, 'backup_execute': {'plan_id'},
                   'verify': {'manifest', 'expected_sha256'}, 'status': {'plan_id'},
                   'restore_plan': {'manifest', 'destination', 'expected_sha256'}, 'restore_execute': {'plan_id'},
                   'activation_plan': set(), 'activate': {'plan_id', 'authorization', 'old_writer_stopped', 'native_evidence', 'old_replica_id'},
                   'history': {'collection', 'local_id', 'cursor'}}
        provided = {k for k, v in {'destination': destination, 'plan_id': plan_id, 'manifest': manifest,
                                  'expected_sha256': expected_sha256, 'workspaces': workspaces, 'payloads': payloads,
                                  'authorization': authorization, 'native_evidence': native_evidence,
                                  'old_replica_id': old_replica_id, 'collection': collection,
                                  'local_id': local_id, 'cursor': cursor}.items() if v is not None}
        if old_writer_stopped:
            provided.add('old_writer_stopped')
        if action not in allowed or provided - allowed[action]:
            raise GovernanceError('RECOVERY_ARGUMENT', 'Use only the arguments for this action; execution consumes the exact saved plan.')
        if action == 'backup_plan':
            return self._backup_plan(destination, workspaces or [], payloads or [])
        if action == 'backup_execute':
            return self._backup_execute(self._load_plan(plan_id, 'backup'))
        if action == 'verify':
            return self._verify(manifest, expected_sha256)
        if action == 'restore_plan':
            return self._restore_plan(manifest, destination, expected_sha256)
        if action == 'restore_execute':
            return self._restore_execute(self._load_plan(plan_id, 'restore'))
        if action == 'status':
            plan = self._load_plan(plan_id)
            receipt = self._plan_path(plan_id).with_suffix('.receipt.json')
            result = {'plan': plan, 'receipt': read_json(receipt)[0] if receipt.exists() else None,
                      'effect_may_exist_without_receipt': not receipt.exists(), 'status_is_read_only': True}
            if plan['kind'] == 'restore' and (Path(plan['destination']) / 'control' / '.taskcarry' / 'state.sqlite3').is_file():
                value, _ = _manifest(plan['manifest'], plan['manifest_sha256'])
                result['observed_effect'] = self._restore_effect(value, plan)
            return result
        if action in ('activation_plan', 'activate'):
            return self._activation(action, plan_id, authorization, old_writer_stopped, native_evidence, old_replica_id)
        if action == 'history':
            self._require_store()
            if type(limit) is not int or not 1 <= limit <= 100:
                raise GovernanceError('RECOVERY_ARGUMENT', 'History page size must be 1-100.')
            conditions, params = ['collection=?', 'key>?'], ['recovery_history', cursor or '']
            for field, selected in (('original_collection', collection), ('original_key', local_id)):
                if selected is not None:
                    conditions.append("json_extract(value,'$." + field + "')=?")
                    params.append(selected)
            with self.store._connect(readonly=True) as db:
                rows = db.execute('SELECT key,value FROM records WHERE ' + ' AND '.join(conditions)
                                  + ' ORDER BY key LIMIT ?', [*params, limit + 1]).fetchall()
            return {'items': [dict(json.loads(v), history_id=k) for k, v in rows[:limit]],
                    'next_cursor': rows[limit - 1][0] if len(rows) > limit else None, 'read_only': True}
        raise GovernanceError('RECOVERY_ACTION', 'Unknown project recovery action.')

    def _backup_plan(self, destination, workspaces, payloads):
        self._require_store()
        if not destination:
            raise GovernanceError('RECOVERY_ARGUMENT', 'Select an independent local recovery directory.')
        destination = normal(destination)
        disjoint(destination, self.root)
        if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
            raise GovernanceError('RECOVERY_DESTINATION_NOT_EMPTY', 'Use an absent or empty recovery directory.')
        registered = {w['name']: w for w in self.store.list('workspaces')}
        components, names, roots = [], set(), []
        for category, selections in (('workspaces', workspaces), ('payloads', payloads)):
            for spec in selections:
                name = _id(spec.get('name'), 'Recovery component')
                if name.casefold() in names:
                    raise GovernanceError('RECOVERY_ARGUMENT', 'Recovery component names must be unique.')
                names.add(name.casefold())
                raw = spec.get('path') or registered.get(name, {}).get('path')
                if not raw:
                    raise GovernanceError('WORKSPACE_UNKNOWN', 'Select an explicit source or registered workspace.', {'name': name})
                source = normal(raw)
                if not source.is_dir():
                    raise GovernanceError('RECOVERY_SOURCE_MISSING', 'The selected source directory is unavailable.')
                disjoint(destination, source)
                if any(source == p for p in roots):
                    raise GovernanceError('RECOVERY_ARGUMENT', 'A source directory can have only one recovery component.')
                roots.append(source)
                kind = spec.get('kind', 'git' if category == 'workspaces' else 'files')
                paths = spec.get('paths', [])
                if kind not in ('git', 'files') or not isinstance(paths, list) or kind == 'files' and not paths:
                    raise GovernanceError('RECOVERY_ARGUMENT', 'Plain payloads need exact file paths; Git components include tracked work by default.')
                selected = rg.inventory(source, kind, paths, spec.get('refs'))
                selected.update(name=name, target='control' if source == self.root else category + '/' + name,
                                selected_paths=paths, selected_refs=spec.get('refs'))
                components.append(selected)
        config = self.store.get('config', 'project')
        missing_artifacts = self._missing_artifacts(self.store.list('artifacts'), components)
        baseline = _baseline_recovery(self.store.get('settings', 'integration_baseline'), components, registered,
                                      self.store.get('settings', 'integration_baseline_recovery'))
        plan_id = 'backup-' + uuid.uuid4().hex
        plan = {'schema': PLAN_SCHEMA, 'plan_id': plan_id, 'kind': 'backup', 'created_at': now(),
                'source_control': str(self.root), 'destination': str(destination), 'components': components,
                'project_id': config.get('project_id') or 'project-' + uuid.uuid4().hex,
                'legacy_identity_upgrade_on_restore': not bool(config.get('project_id')),
                'registered_workspaces': registered,
                'missing_workspace_payloads': sorted(set(registered) - {c['name'] for c in components}),
                'missing_artifact_payloads': missing_artifacts,
                'integration_baseline_recovery': baseline,
                'scope': 'One coherent state snapshot and referenced objects; separately stable selected source components, not a global transaction.',
                'exclusions': ['Unselected ordinary, ignored and external files; credentials and native host configuration.',
                               'Filesystem ACLs, alternate streams, links, submodules, unsaved editor buffers and reflogs.',
                               'Live schedules, installed runtime and any offsite transport or encryption.'],
                'state_capture_time': 'First execute seals one SQLite snapshot; retries reuse that snapshot and the original selected source batch.'}
        write_json(self._plan_path(plan_id), plan)
        return plan

    @staticmethod
    def _missing_artifacts(artifacts, components):
        selected = {str(normal(Path(c['source']) / item['path'])): item.get('sha256')
                    for c in components for item in c['files'] if not item.get('missing')}
        return [{'artifact_id': a['artifact_id'], 'path': a['path'], 'sha256': a['sha256'],
                 'reason': 'Registered required artifact is outside the selected payload or its recorded bytes changed.'}
                for a in artifacts if a.get('decision') not in ('ignore', 'dismiss', 'no_backup_needed')
                and selected.get(str(normal(a['path']))) != a['sha256']]

    def _state_capture(self, media, plan, scratch):
        scratch.mkdir(parents=True, exist_ok=True)
        snapshot = scratch / 'state.sqlite3'
        # Freeze database pages under the cooperating writer lock, release before
        # copying immutable objects or building Git bundles.
        with self.store.guard(), self.store._connect(readonly=True) as db, closing(sqlite3.connect(snapshot)) as target:
            db.backup(target)
        rows = _state_rows(snapshot)
        config = next(v for c, k, v in rows if (c, k) == ('config', 'project'))
        if type(config.get('schema_version')) is not int or config['schema_version'] != 1:
            raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'Cannot export an unsupported governance state.')
        objects = {}
        # Checkpoints and preservation use Core's object store. Artifact SHA
        # values describe external files; they are not implicit copy requests.
        for ref in _state_references(rows):
            if not SHA.fullmatch(str(ref.get('sha256', ''))):
                raise GovernanceError('RECOVERY_STATE_CORRUPT', 'Invalid state object identity.')
            try:
                data = read_file_bytes(normal(self.store.directory / 'objects' / ref['sha256']), MAX_BYTES)
            except FileNotFoundError as exc:
                raise GovernanceError('RECOVERY_OBJECT_MISSING', 'A referenced governance object is absent.', ref) from exc
            if len(data) != ref['size'] or digest(data) != ref['sha256']:
                raise GovernanceError('RECOVERY_OBJECT_MISMATCH', 'A referenced governance object has changed.', ref)
            objects[ref['sha256']] = put(media, data)
        return {'schema_version': 1, 'snapshot': put(media, read_file_bytes(snapshot, MAX_BYTES)),
                'objects': sorted(objects.values(), key=lambda x: x['sha256']), 'record_count': len(rows),
                'project_id': config.get('project_id') or plan['project_id'], 'old_replica_id': config.get('replica_id'),
                'source_aliases': config.get('source_aliases', []), 'captured_at': now(),
                'registered_workspaces': {v['name']: v for c, _, v in rows if c == 'workspaces'},
                'integration_baseline': next((v for c, k, v in rows if (c, k) == ('settings', 'integration_baseline')), None),
                'integration_baseline_recovery': next((v for c, k, v in rows if (c, k) == ('settings', 'integration_baseline_recovery')), None),
                'artifacts': [v for c, _, v in rows if c == 'artifacts'],
                'accepted_history_dependencies': [{'stage_id': k, 'baseline': v['accepted_baseline'], 'commit': v['accepted_commit']}
                                                  for c, k, v in rows if c == 'stages' and v.get('accepted_baseline') and v.get('accepted_commit')],
                'stage_history_dependencies': [{'stage_id': k, 'workspace': v.get('workspace'),
                                                'commits': sorted({v[x] for x in ('base', 'commit') if v.get(x)})}
                                               for c, k, v in rows if c == 'stages']}

    def _backup_execute(self, plan):
        self._require_store()
        if str(self.root) != plan['source_control']:
            raise GovernanceError('RECOVERY_PLAN_MISMATCH', 'Backup source control differs from the saved plan.')
        media = normal(plan['destination'])
        disjoint(media, self.root)
        media.mkdir(parents=True, exist_ok=True)
        with lock(media / 'batch.lock'):
            if not (media / 'intent.json').exists() and any(p.name != 'batch.lock' for p in media.iterdir()):
                raise GovernanceError('RECOVERY_DESTINATION_CHANGED', 'Unowned files appeared at the selected backup destination; preserved for review.')
            write_json(media / 'intent.json', plan)
            manifest_path = media / 'manifest.json'
            if manifest_path.exists():
                verified = self._verify(str(manifest_path))
                if verified['set_id'] != plan['plan_id']:
                    raise GovernanceError('RECOVERY_CONFLICT', 'Existing manifest belongs to another batch.')
                if not verified['verified']:
                    raise GovernanceError('RECOVERY_VERIFY_FAILED', 'Existing recovery effects failed verification.', verified)
                result = {'plan_id': plan['plan_id'], 'manifest': str(manifest_path),
                          'manifest_sha256': verified['manifest_sha256'], 'state': 'COMPLETE',
                          'reused_original_batch': True, 'verification': verified}
                self._receipt(plan, result)
                return result
            sealed_state = media / 'state.capture.json'
            if sealed_state.exists():
                state, _ = read_json(sealed_state)
                for ref in _refs([state['snapshot'], state['objects']]):
                    get(media, ref)
            else:
                state = self._state_capture(media, plan, media / ('scratch-' + uuid.uuid4().hex))
                write_json(sealed_state, state)
            if state.get('registered_workspaces') != plan['registered_workspaces']:
                raise GovernanceError('RECOVERY_SOURCE_CHANGED', 'Workspace registration changed after planning; prepare a fresh recovery plan.')
            components = []
            for selected in plan['components']:
                sealed = media / ('component-' + selected['name'] + '.json')
                if sealed.exists():
                    component, _ = read_json(sealed)
                    comparison = copy.deepcopy(component)
                    comparison.pop('bundle', None)
                    for file in comparison['files']:
                        file.pop('object', None)
                    for item in comparison.get('git', {}).get('index', []):
                        item.pop('object', None)
                    planned = {k: v for k, v in selected.items() if k not in ('selected_paths', 'selected_refs')}
                    if comparison != planned:
                        raise GovernanceError('RECOVERY_CONFLICT', 'Sealed component no longer matches the original batch.')
                    for ref in _refs(component):
                        get(media, ref)
                else:
                    component = rg.capture(media, selected, media / ('scratch-' + uuid.uuid4().hex))
                    write_json(sealed, component)
                components.append(component)
            missing_artifacts = self._missing_artifacts(state.get('artifacts', []), components)
            baseline = _baseline_recovery(state.get('integration_baseline'), components, state['registered_workspaces'],
                                          state.get('integration_baseline_recovery'))
            missing_history, history_checks = [], {}
            history_dependencies = list(state.get('stage_history_dependencies', []))
            if baseline['status'] == 'MAPPED':
                history_dependencies.extend({'stage_id': d['stage_id'], 'workspace': baseline['component'],
                                             'commits': [d['commit']], 'role': 'accepted_baseline'}
                                            for d in state.get('accepted_history_dependencies', [])
                                            if normal(d['baseline']) == normal(state['integration_baseline']['path']))
            for dependency in history_dependencies:
                component = next((c for c in components if c['name'] == dependency['workspace'] and c['kind'] == 'git'), None)
                if component is None:
                    missing_history.append(dependency)
                    continue
                if component['name'] not in history_checks:
                    check_root = media / ('history-check-' + uuid.uuid4().hex[:12])
                    check_root.mkdir()
                    rg.git(check_root, 'init', '--quiet', '--bare', '--object-format=' + component['git']['object_format'])
                    bundle = check_root / 'history.bundle'
                    atomic(bundle, get(media, component['bundle']))
                    rg.git(check_root, 'fetch', '--quiet', '--no-tags', str(bundle), 'HEAD',
                           *['+' + ref + ':' + ref for ref in component['git']['refs']])
                    history_checks[component['name']] = check_root
                for commit in dependency['commits']:
                    # This only tests history containment in the selected roots,
                    # and never creates refs or expands the approved history scope.
                    found = rg.git(history_checks[component['name']], 'rev-parse', '--verify', commit + '^{commit}', check=False).decode('ascii').strip()
                    if found != commit:
                        missing_history.append({**dependency, 'commits': [commit]})
            disabled_host = [{'component': c['name'], 'path': row['path'],
                              'quarantine_path': c['target'] + '/' + rg.quarantine(row['path']),
                              'sha256': row['sha256'], 'reason': 'Old native host bindings/schedules must not execute on a restored replica.'}
                             for c in components for row in c['files'] if rg.host_entry(row['path']) and not row.get('missing')]
            value = {'schema': SCHEMA, 'set_id': plan['plan_id'], 'created_at': now(),
                     'source_control': plan['source_control'], 'state': state, 'components': components,
                     'registered_workspaces': plan['registered_workspaces'],
                     'missing_workspace_payloads': plan['missing_workspace_payloads'],
                     'missing_artifact_payloads': missing_artifacts, 'missing_history_dependencies': missing_history,
                     'integration_baseline_recovery': baseline,
                     'disabled_host_files': disabled_host,
                     'runtime': {'core_version': __version__, 'python_minimum': '3.11', 'recovery_schema': 1,
                                 'git_required': any(c['kind'] == 'git' for c in components),
                                 'core_package_included': False},
                     'dependencies': {'governance_state': ['state.snapshot', 'state.objects'],
                                      'workspace_bindings': [c['name'] for c in components],
                                      'core_package': 'Install a compatible trusted TaskCarry package separately; never execute a package from unknown backup media.'},
                     'scope': plan['scope'], 'exclusions': plan['exclusions'],
                     'automations_enabled': False, 'offsite_verified': False}
            candidate_manifest = media / ('manifest-' + uuid.uuid4().hex[:12] + '.partial')
            write_json(candidate_manifest, value)
            verified = self._verify(str(candidate_manifest))
            if not verified['verified']:
                raise GovernanceError('RECOVERY_VERIFY_FAILED', 'Recovery publication has incomplete payloads.', verified)
            write_json(manifest_path, value)
            result = {'plan_id': plan['plan_id'], 'manifest': str(manifest_path),
                      'manifest_sha256': verified['manifest_sha256'], 'state': 'COMPLETE',
                      'reused_original_batch': False, 'verification': verified}
            self._receipt(plan, result)
            return result

    def _receipt(self, plan, result):
        path = self._plan_path(plan['plan_id']).with_suffix('.receipt.json')
        if path.exists():
            old, _ = read_json(path)
            if old.get('manifest_sha256') != result.get('manifest_sha256') or old.get('state') != result.get('state'):
                raise GovernanceError('RECOVERY_CONFLICT', 'Existing recovery receipt conflicts with observed effects.')
        else:
            write_json(path, result)

    @staticmethod
    def _verify(manifest, expected=None):
        if not manifest:
            raise GovernanceError('RECOVERY_ARGUMENT', 'Select the recovery manifest file.')
        path = normal(manifest)
        value, checksum = _manifest(path, expected)
        failures, seen = [], set()
        for ref in _payload_refs(value):
            if ref['sha256'] in seen:
                continue
            seen.add(ref['sha256'])
            try:
                get(path.parent, ref)
            except (GovernanceError, OSError) as error:
                failures.append({'sha256': ref['sha256'], 'code': getattr(error, 'code', type(error).__name__)})
        state_verified = False
        baseline = {'status': 'UNVERIFIED', 'component': None}
        if not failures:
            rows = _state_rows(safe(path.parent, 'objects/' + value['state']['snapshot']['sha256']))
            config = next(v for c, k, v in rows if (c, k) == ('config', 'project'))
            binding = next((v for c, k, v in rows if (c, k) == ('settings', 'integration_baseline')), None)
            prior = next((v for c, k, v in rows if (c, k) == ('settings', 'integration_baseline_recovery')), None)
            baseline = _baseline_recovery(binding, value['components'], {v['name']: v for c, _, v in rows if c == 'workspaces'}, prior)
            if value.get('integration_baseline_recovery', baseline) != baseline:
                raise GovernanceError('RECOVERY_MANIFEST', 'The baseline recovery declaration differs from the actual governance snapshot.')
            if config.get('project_id') and config['project_id'] != value['state']['project_id']:
                raise GovernanceError('RECOVERY_MANIFEST', 'The manifest project identity differs from the actual state snapshot.')
            declared = {r['sha256']: r['size'] for r in value['state']['objects']}
            for ref in _state_references(rows):
                if declared.get(ref['sha256']) != ref['size']:
                    failures.append({'sha256': ref['sha256'], 'code': 'RECOVERY_STATE_REFERENCE_MISSING'})
            state_verified = not failures
        return {'verified': not failures, 'set_id': value['set_id'], 'manifest_sha256': checksum,
                'trusted_digest_supplied': expected is not None, 'objects': len(seen), 'failures': failures,
                'missing_workspace_payloads': value.get('missing_workspace_payloads', []),
                'missing_artifact_payloads': value.get('missing_artifact_payloads', []),
                'missing_history_dependencies': value.get('missing_history_dependencies', []),
                'integration_baseline_recovery': baseline,
                'disabled_host_files': value.get('disabled_host_files', []),
                'runtime': value['runtime'], 'exclusions': value['exclusions'], 'offsite_verified': False,
                'state_references_verified': state_verified,
                'complete_scope': not failures and _complete_scope(value, baseline),
                'restore_tested': False, 'writer_activated': False}

    def _restore_plan(self, manifest, destination, expected):
        verified = self._verify(manifest, expected)
        if not verified['verified']:
            raise GovernanceError('RECOVERY_VERIFY_FAILED', 'Required recovery objects are unavailable.', verified)
        value, checksum = _manifest(normal(manifest), verified['manifest_sha256'])
        if not destination:
            raise GovernanceError('RECOVERY_ARGUMENT', 'Select an independent absent or empty restore destination.')
        target = normal(destination)
        disjoint(target, normal(manifest).parent)
        disjoint(target, self.root)
        for source in [value['source_control'], *[c['source'] for c in value['components']]]:
            disjoint(target, source)
        if target.exists() and (not target.is_dir() or any(target.iterdir())):
            raise GovernanceError('RECOVERY_DESTINATION_NOT_EMPTY', 'Restore cannot replace an existing project.')
        plan_id = 'restore-' + uuid.uuid4().hex
        plan = {'schema': PLAN_SCHEMA, 'kind': 'restore', 'plan_id': plan_id, 'created_at': now(),
                'manifest': str(normal(manifest)), 'manifest_sha256': checksum, 'destination': str(target),
                'source_set_id': value['set_id'], 'replica_id': 'replica-' + uuid.uuid4().hex,
                'project_id': value['state']['project_id'], 'old_replica_id': value['state'].get('old_replica_id'),
                'bindings': [{'name': c['name'], 'source': c['source'], 'target': str(safe(target, c['target']))} for c in value['components']],
                'control': str(target / 'control'), 'writer_state': 'standby',
                'missing_workspace_payloads': value.get('missing_workspace_payloads', []),
                'missing_artifact_payloads': value.get('missing_artifact_payloads', []),
                'missing_history_dependencies': value.get('missing_history_dependencies', []),
                'integration_baseline_recovery': verified['integration_baseline_recovery'],
                'disabled_host_files': value.get('disabled_host_files', []),
                'next_step': 'Execute the exact plan, reconnect this standby copy in a native host, then explicitly review writer handoff.'}
        write_json(self._plan_path(plan_id), plan)
        return plan

    def _restore_state(self, media, value, plan, build):
        root = build / 'control'
        root.mkdir(parents=True, exist_ok=True)
        directory = root / '.taskcarry'
        directory.mkdir()
        atomic(directory / 'state.sqlite3', get(media, value['state']['snapshot']))
        for ref in value['state']['objects']:
            atomic(directory / 'objects' / ref['sha256'], get(media, ref))
        store = Store(root)
        with store.recovery_transition(), store.transaction(), store._connect() as db:
            rows = [(c, k, json.loads(v)) for c, k, v in db.execute('SELECT collection,key,value FROM records').fetchall()]
            config = store.get('config', 'project')
            old_config = copy.deepcopy(config)
            from .identification import source
            old_alias = source(value['source_control'])['source_id']
            aliases = [*config.get('source_aliases', []), old_alias]
            if config.get('replica_id'):
                aliases.append(config['replica_id'])
            inert = set(config.get('recovery_inert_plan_ids', []))
            inert_cycles = set(config.get('recovery_inert_cycle_ids', []))
            inert_runs = set(config.get('recovery_inert_run_ids', []))
            plan_collections = {'plans', 'preservation', 'connection_plans', 'identity_plans', 'workbench_plans'}
            runtime_collections = {'governance_cycles', 'cycle_reservations', 'cycle_requests', 'runs',
                                   'scan_sources', 'source_scans', 'operations'}
            for collection, key, record in rows:
                # Full original historical object is retained before changing a
                # current projection or removing an executable plan locator.
                if (collection in plan_collections | runtime_collections
                        or isinstance(record, dict) and record.get('plan_id') and collection not in ('stages', 'recovery_history')):
                    if record.get('plan_id') or collection in plan_collections:
                        inert.add(record.get('plan_id', key))
                    if collection == 'governance_cycles':
                        inert_cycles.add(record.get('cycle_id', key))
                    if collection == 'runs':
                        inert_runs.add(record.get('run_id', key))
                    _archive(store, plan['plan_id'], collection, key, record)
                    if collection == 'operations':
                        store.put(collection, key, {**record, 'historical_status': record.get('status'),
                                                   'status': 'SUPERSEDED', 'recovery_inert': True})
                    else:
                        db.execute('DELETE FROM records WHERE collection=? AND key=?', (collection, key))
            components = {c['name']: c for c in value['components']}
            old_binding = store.get('settings', 'integration_baseline')
            old_recovery_binding = store.get('settings', 'integration_baseline_recovery')
            baseline = _baseline_recovery(old_binding, value['components'],
                                          {v['name']: v for c, _, v in rows if c == 'workspaces'}, old_recovery_binding)
            if old_binding:
                _archive(store, plan['plan_id'], 'settings', 'integration_baseline', old_binding)
            if old_recovery_binding:
                _archive(store, plan['plan_id'], 'settings', 'integration_baseline_recovery', old_recovery_binding)
            if baseline['status'] == 'MAPPED':
                component = components[baseline['component']]
                target = safe(Path(plan['destination']), component['target'])
                rebound = {'path': str(target), 'common_dir': str(target / '.git'), 'branch': component['git']['branch']}
                store.put('settings', 'integration_baseline', rebound)
                store.put('settings', 'integration_baseline_recovery',
                          {**baseline, 'status': 'REBOUND', 'restore_id': plan['plan_id'], 'identity': rebound})
                for stage in store.list('stages'):
                    if (stage.get('accepted_baseline') and normal(stage['accepted_baseline']) == normal(old_binding['path'])
                            and stage.get('accepted_commit')):
                        # Only current projections move. Original acceptance,
                        # including its exact old path, remains queryable history.
                        found = rg.git(safe(build, component['target']), 'rev-parse', '--verify',
                                       stage['accepted_commit'] + '^{commit}', check=False).decode('ascii').strip()
                        if found == stage['accepted_commit']:
                            _archive(store, plan['plan_id'], 'stages', stage['stage_id'], stage)
                            store.put('stages', stage['stage_id'],
                                      {**stage, 'accepted_baseline': str(target),
                                       'recovery_original_accepted_baseline': stage['accepted_baseline']})
            elif baseline['status'] == 'REBIND_REQUIRED':
                db.execute("DELETE FROM records WHERE collection='settings' AND key='integration_baseline'")
                store.put('settings', 'integration_baseline_recovery',
                          {**baseline, 'restore_id': plan['plan_id'],
                           'next_step': 'Prepare a complete recovery set containing the original registered baseline and restore it to an independent destination.'})
            for workspace in store.list('workspaces'):
                name = workspace['name']
                component = components.get(name)
                target = safe(Path(plan['destination']), component['target'] if component else 'workspaces/' + _id(name, 'Workspace'))
                archived = copy.deepcopy(workspace)
                _archive(store, plan['plan_id'], 'workspaces', name, archived)
                workspace.update(path=str(target), recovery_original_path=archived['path'],
                                 recovery_available=component is not None,
                                 identity={'path': str(target), 'common_dir': str(target / '.git'),
                                           'branch': component.get('git', {}).get('branch') if component else None})
                store.put('workspaces', name, workspace)
            path_bindings = {str(normal(Path(c['source']) / item['path'])): str(safe(Path(plan['destination']), c['target'] + '/' + item['path']))
                             for c in value['components'] for item in c['files'] if not item.get('missing')}
            for artifact in store.list('artifacts'):
                old = copy.deepcopy(artifact)
                _archive(store, plan['plan_id'], 'artifacts', artifact['artifact_id'], old)
                artifact.update(path=path_bindings.get(str(normal(artifact['path'])), str(Path(plan['destination']) / 'unavailable' / artifact['artifact_id'])),
                                recovery_original_path=old['path'], recovery_available=str(normal(old['path'])) in path_bindings,
                                backup=None, backup_verified=False, backup_available=False)
                store.put('artifacts', artifact['artifact_id'], artifact)
            config.update(project_id=plan['project_id'], replica_id=plan['replica_id'],
                          source_aliases=list(dict.fromkeys(aliases)), recovery_writer_state='standby',
                          recovery_restore_id=plan['plan_id'], recovery_inert_plan_ids=sorted(inert),
                          recovery_inert_cycle_ids=sorted(inert_cycles), recovery_inert_run_ids=sorted(inert_runs),
                          recovery_old_replica_id=value['state'].get('old_replica_id'),
                          recovery_automation_state='disabled_pending_native_reconfiguration',
                          recovery_source_control=value['source_control'], recovery_manifest_sha256=plan['manifest_sha256'])
            _archive(store, plan['plan_id'], 'config', 'project', old_config)
            store.put('config', 'project', config)
            store.put('recovery_restores', plan['plan_id'], {'restore_id': plan['plan_id'], 'manifest_sha256': plan['manifest_sha256'],
                                                           'destination': plan['destination'], 'replica_id': plan['replica_id'],
                                                           'writer_state': 'standby', 'created_at': now()})
            store.event('project_restored_standby', {'restore_id': plan['plan_id'], 'project_id': plan['project_id'],
                                                     'replica_id': plan['replica_id'], 'old_plans_disabled': sorted(inert)})
        with store.recovery_transition():
            store.upgrade()
        return store

    def _restore_effect(self, value, plan, *, location=None, expected_state=None):
        target = normal(location or plan['destination'])
        control = Core(target / 'control')
        config = control.store.get('config', 'project')
        if (config.get('recovery_restore_id') != plan['plan_id'] or config.get('replica_id') != plan['replica_id']
                or config.get('project_id') != plan['project_id'] or config.get('recovery_manifest_sha256') != plan['manifest_sha256']):
            raise GovernanceError('RECOVERY_EFFECT_CHANGED', 'Restored governance identity does not match the plan.')
        if config.get('recovery_writer_state') == 'active':
            return {'control': str(target / 'control'), 'project_id': plan['project_id'], 'replica_id': plan['replica_id'],
                    'writer_state': 'active', 'state_advanced': True, 'state_verified': False,
                    'git_verified': False, 'replay_permitted': False,
                    'meaning': 'A separately activated replica may have new work; historical restore verification is not a current snapshot.'}
        if expected_state is None:
            prepared, _ = read_json(self._plan_path(plan['plan_id']).with_suffix('.prepared.json'))
            expected_state = prepared['state_fingerprint']
        fingerprint = _state_fingerprint(control.store)
        if fingerprint != expected_state:
            raise GovernanceError('RECOVERY_EFFECT_CHANGED', 'Restored governance records or events changed; preserved without replay.')
        for component in value['components']:
            rg.verify_effect(component, safe(target, component['target']))
        for ref in value['state']['objects']:
            data = read_file_bytes(control.store.directory / 'objects' / ref['sha256'], MAX_BYTES)
            if len(data) != ref['size'] or digest(data) != ref['sha256']:
                raise GovernanceError('RECOVERY_EFFECT_CHANGED', 'Restored governance object differs.')
        return {'control': str(target / 'control'), 'project_id': plan['project_id'], 'replica_id': plan['replica_id'],
                'writer_state': config.get('recovery_writer_state'), 'workspaces_verified': len(value['components']),
                'state_objects_verified': len(value['state']['objects']), 'state_verified': True,
                'state_fingerprint': fingerprint, 'git_verified': True,
                'complete_scope': _complete_scope(value, plan['integration_baseline_recovery']),
                'integration_baseline_recovery': control.store.get('settings', 'integration_baseline_recovery') or plan['integration_baseline_recovery'],
                'disabled_host_files': value.get('disabled_host_files', [])}

    def _restore_execute(self, plan):
        value, checksum = _manifest(plan['manifest'], plan['manifest_sha256'])
        verified = self._verify(plan['manifest'], checksum)
        if not verified['verified']:
            raise GovernanceError('RECOVERY_VERIFY_FAILED', 'Recovery input changed or became unavailable.', verified)
        target = normal(plan['destination'])
        with lock(self._plan_path(plan['plan_id']).with_suffix('.lock')):
            if target.exists() and any(target.iterdir()):
                effect = self._restore_effect(value, plan)
                if effect.get('state_advanced'):
                    return {'plan_id': plan['plan_id'], 'state': 'ADVANCED_NO_REPLAY', 'manifest_sha256': checksum,
                            'effect': effect, 'old_plans_replayed': False}
                result = {'plan_id': plan['plan_id'], 'state': 'RESTORED_STANDBY', 'manifest_sha256': checksum,
                          'effect': effect, 'recovered_existing_effect': True, 'old_plans_replayed': False,
                          'native_host_verified': False, 'writer_activated': False}
                self._receipt(plan, result)
                return result
            # Every attempt uses an owned independent directory. A crash leaves
            # that attempt intact; retry reads the same pinned immutable inputs,
            # never overwrites uncertain partial files or a user destination.
            attempts = normal(target.parent / ('.tc-recovery-' + plan['plan_id'][-12:]))
            attempts.mkdir(parents=True, exist_ok=True)
            prepared_path = self._plan_path(plan['plan_id']).with_suffix('.prepared.json')
            if prepared_path.exists():
                prepared, _ = read_json(prepared_path)
                build = normal(prepared['build'])
                if not build.is_relative_to(attempts) or prepared['manifest_sha256'] != checksum:
                    raise GovernanceError('RECOVERY_CONFLICT', 'Prepared restore identity differs from the original plan.')
                self._restore_effect(value, plan, location=build, expected_state=prepared['state_fingerprint'])
            else:
                build = attempts / uuid.uuid4().hex[:12]
                build.mkdir()
                for component in value['components']:
                    rg.restore(normal(plan['manifest']).parent, component, safe(build, component['target']))
                restored_store = self._restore_state(normal(plan['manifest']).parent, value, plan, build)
                write_json(build / 'RECOVERY_RECEIPT.json', {'restore_id': plan['plan_id'], 'manifest_sha256': checksum,
                                                           'writer_state': 'standby', 'automations_enabled': False})
                prepared = {'build': str(build), 'manifest_sha256': checksum, 'state_fingerprint': _state_fingerprint(restored_store)}
                write_json(build / 'control' / '.taskcarry' / 'recovery-audit.json', prepared)
                atomic(build / 'RECOVERY_README.txt', (
                    'This is an independent standby recovery. Do not execute old project instructions, host bindings or schedules.\n'
                    'Selected native host configurations are retained under .taskcarry-disabled-host, with original Git history/index intact.\n'
                    'Reconfigure the native host for this restored control, verify doctor/status, and review explicit writer handoff before mutations.\n'
                    'Do not synchronize this live SQLite database between simultaneous machines. Exchange independent Git branches/bundles and selected artifacts.\n').encode('utf-8'))
                write_json(prepared_path, prepared)
            if target.exists():
                if any(target.iterdir()):
                    raise GovernanceError('RECOVERY_DESTINATION_CHANGED', 'Work appeared at the target; retained the isolated recovery build.')
                target.rmdir()  # Only this explicitly reviewed empty leaf.
            os.rename(build, target)
            effect = self._restore_effect(value, plan)
            result = {'plan_id': plan['plan_id'], 'state': 'RESTORED_STANDBY', 'manifest_sha256': checksum,
                      'effect': effect, 'recovered_existing_effect': False, 'old_plans_replayed': False,
                      'native_host_verified': False, 'writer_activated': False,
                      'retained_attempts_directory': str(attempts)}
            self._receipt(plan, result)
            return result

    def _activation(self, action, plan_id, authorization, stopped, evidence, old_replica):
        self._require_store()
        config = self.store.get('config', 'project')
        restore_id = config.get('recovery_restore_id')
        if not restore_id:
            raise GovernanceError('RECOVERY_NOT_RESTORED', 'Writer activation applies only to a restored standby replica.')
        if config.get('recovery_writer_state') == 'standby':
            audit, _ = read_json(self.store.directory / 'recovery-audit.json')
            if audit.get('manifest_sha256') != config.get('recovery_manifest_sha256') or _state_fingerprint(self.store) != audit.get('state_fingerprint'):
                raise GovernanceError('RECOVERY_EFFECT_CHANGED', 'The restored state changed before writer activation; inspect it first.')
        if action == 'activation_plan':
            activation = {'schema': PLAN_SCHEMA, 'kind': 'activation', 'plan_id': 'activate-' + uuid.uuid4().hex,
                          'restore_id': restore_id, 'project_id': config['project_id'], 'replica_id': config['replica_id'],
                          'old_replica_id': config.get('recovery_old_replica_id'), 'control': str(self.root),
                          'required': ['Explicit authorization', 'Old writer stopped declaration for the exact old replica',
                                       'Native doctor/status evidence bound to this restored control and replica'],
                          'limitations': 'The engine cannot fence or independently observe a remote old writer. Supplied native evidence is a caller attestation.',
                          'automations_remain_disabled': True}
            write_json(self._plan_path(activation['plan_id']), activation)
            return activation
        plan = self._load_plan(plan_id, 'activation')
        if any(plan[key] != config.get(key) for key in ('project_id', 'replica_id')) or plan['restore_id'] != restore_id:
            raise GovernanceError('RECOVERY_PLAN_MISMATCH', 'Activation identity changed after planning.')
        if not isinstance(authorization, str) or not authorization.strip() or stopped is not True or old_replica != plan['old_replica_id']:
            raise GovernanceError('RECOVERY_HANDOFF_REQUIRED', 'Explicit authorization and an exact old-writer-stopped declaration are required.')
        if (not isinstance(evidence, dict) or evidence.get('source_id') != config['project_id']
                or evidence.get('replica_id') != config['replica_id'] or evidence.get('control') != str(self.root)
                or evidence.get('doctor') is not True or evidence.get('status') is not True or not evidence.get('evidence_ref')):
            raise GovernanceError('RECOVERY_NATIVE_EVIDENCE_REQUIRED', 'Provide native host doctor/status evidence bound to this exact restored replica.')
        receipt = {'plan_id': plan_id, 'restore_id': restore_id, 'project_id': config['project_id'],
                   'replica_id': config['replica_id'], 'old_replica_id': old_replica, 'old_writer_stopped_declared': True,
                   'authorization': authorization, 'native_evidence': evidence, 'native_evidence_independently_verified': False,
                   'old_writer_remotely_fenced': False, 'writer_activated': True, 'automations_enabled': False}
        with self.store.recovery_transition(), self.store.transaction():
            previous = self.store.get('recovery_activations', plan_id)
            if previous is not None and previous != receipt:
                raise GovernanceError('RECOVERY_CONFLICT', 'Activation receipt differs; review the existing handoff.')
            if previous is None:
                config['recovery_writer_state'] = 'active'
                self.store.put('config', 'project', config)
                self.store.put('recovery_activations', plan_id, receipt)
                self.store.event('recovery_writer_activated', {'plan_id': plan_id, 'replica_id': config['replica_id']})
        return receipt
