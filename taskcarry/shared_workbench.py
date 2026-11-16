"""Explicit shared-directory navigation; legacy v1 objects remain immutable."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from .core import _id, digest_bytes, validate_relative_path
from .store import GovernanceError, now
from .workbench import (Workbench, MAX_PLAN_BYTES, _hash, _links, _read, atomic_write,
                        canonical, codex_instructions, fail, git_snapshot, immutable,
                        managed_section, private_target)

ROUTER = '.codex/taskcarry-routing.json'
PLAN = 'taskcarry.workbench.plan.v2'


def archive_setup(root, control, manifest_sha256):
    """Record exact managed preimages before explicit directory-mode conversion."""
    values = {}
    for name in ('.taskcarry/setup-manifest.json', '.taskcarry/workbench.json', '.taskcarry/workbench.md', '.codex/config.toml'):
        content = _read(root / name, MAX_PLAN_BYTES)
        if content is not None:
            values[name] = {'sha256': digest_bytes(content), 'bytes': base64.b64encode(content).decode()}
    saved_manifest = values.get('.taskcarry/setup-manifest.json', {})
    if saved_manifest.get('sha256') != manifest_sha256:
        fail('The original setup changed before its preimage was saved.', 'SETUP_MANIFEST_CHANGED')
    manifest = json.loads(base64.b64decode(saved_manifest['bytes']))
    for name in ('.taskcarry/workbench.json', '.taskcarry/workbench.md'):
        if values.get(name, {}).get('sha256') != manifest['files'].get(name):
            fail('The original binding changed before conversion; preserve it.', 'SETUP_CONFLICT')
    record = {'schema': 'taskcarry.setup.preimage.v1', 'files': values}
    body = canonical(record)
    if len(body) > MAX_PLAN_BYTES:
        fail('Setup preimage exceeds the bounded history limit.')
    key = digest_bytes(body)
    engine = Workbench(control)
    with engine.store.transaction():
        engine._object('workbench_setup_history', key, record)
    immutable(root / '.taskcarry' / 'setup-history' / (key + '.json'), body)
    return {'sha256': key, 'path': '.taskcarry/setup-history/' + key + '.json',
            'collection': 'workbench_setup_history', 'key': key}


def chat_key(thread_id):
    _id(thread_id, 'Thread ID')
    return digest_bytes(canonical({'thread_id': thread_id}))


def assert_chat_identity(engine, thread_id, workspace, task_id):
    """Current entries own identity; historical receipts are only search indexes."""
    current = SharedWorkbench(engine.root)._chat_pointer(thread_id)
    if current and (current['workspace'], current['task_id']) != (workspace, task_id):
        fail('Retain the original chat workspace and task.', 'WORKBENCH_BINDING_MISMATCH')
    with engine.store._connect(readonly=True) as db:
        rows = db.execute("""SELECT DISTINCT json_extract(value,'$.workspace') FROM records
            WHERE collection='workbench_receipts' AND json_extract(value,'$.schema')='taskcarry.workbench.receipt.v1'
              AND json_extract(value,'$.thread_id')=? LIMIT 101""", (thread_id,)).fetchall()
    if len(rows) > 100:
        fail('Review this chat\'s bounded legacy workspace history before publication.')
    for (name,) in rows:
        receipt = legacy_current_receipt(engine, _id(name, 'Workspace'))
        if (receipt and receipt['thread_id'] == thread_id
                and (receipt['workspace'], receipt['task_id']) != (workspace, task_id)):
            fail('Another current legacy entry owns this original chat; retain its task and workspace.',
                 'WORKBENCH_BINDING_MISMATCH')


def legacy_current_receipt(engine, workspace):
    pointer = engine._pointer(workspace)
    if pointer is None:
        # Missing mirrors are not an implicit release of the original identity.
        # The exact old plan may still repair its own missing finalization.
        pointer = engine.store.get('workbench_current', workspace)
    if pointer is None:
        return None
    receipt = engine.store.get('workbench_receipts', pointer.get('receipt_id', ''))
    fields = ('workspace', 'task_id', 'plan_id', 'view_id', 'source_id')
    if (pointer.get('schema') != 'taskcarry.workbench.current.v1' or not receipt
            or pointer.get('workspace') != workspace or pointer.get('source_id') not in engine._source_ids()
            or any(pointer.get(k) != receipt.get(k) for k in fields)):
        fail('Retain the unresolved legacy current record for review.')
    return receipt


class SharedWorkbench(Workbench):
    def _directory_binding(self, workspace, task_id=None):
        from .integration import Integration
        from .setup import read_manifest, workbench_binding
        if task_id is not None:
            self._task(task_id)
        root = _links(Integration(self.root)._ws(_id(workspace, 'Workspace')))
        expected = workbench_binding(self.root, root, workspace, None, binding_mode='directory')
        manifest = read_manifest(root)
        if manifest.get('format') != 2 or manifest.get('binding') != expected:
            fail('Preview and install explicit directory-mode connection materials first.', 'SHARED_SETUP_REQUIRED')
        raw = _read(root / '.taskcarry/workbench.json')
        try:
            value = json.loads(raw) if raw is not None else {}
        except ValueError:
            value = {}
        if (any(value.get(k) != v for k, v in expected.items())
                or value.get('format') != 2
                or manifest['files'].get('.taskcarry/workbench.json') != _hash(raw)):
            fail('The shared directory materials changed; retain and review them.', 'WORKBENCH_BINDING_MISMATCH')
        return root

    def _directory_id(self, root):
        return digest_bytes(os.path.normcase(str(root)).encode())

    def _directory_current(self, root):
        return self.store.get('workbench_directory_current', self._directory_id(root))

    def _router(self, root, current):
        raw = _read(private_target(root, ROUTER))
        if current is None:
            if raw is not None:
                fail('An unmanaged shared router already exists; retain it for review.')
            return {'schema': 'taskcarry.workbench.router.v2', 'source_id': self.source()['source_id'],
                    'control': str(self.root), 'root': str(root), 'routes': []}
        if raw is None or _hash(raw) != current['router_sha256']:
            fail('The shared directory router changed; inspect actual effects before planning.')
        try:
            value = json.loads(raw)
        except ValueError:
            fail('Invalid shared directory router.')
        if (raw != canonical(value) or value.get('schema') != 'taskcarry.workbench.router.v2'
                or value.get('control') != str(self.root) or value.get('root') != str(root)
                or value.get('source_id') not in self._source_ids()):
            fail('Shared directory router belongs to another source or location.')
        return value

    def _chat_pointer(self, thread_id):
        key = chat_key(thread_id)
        raw = _read(self._path('chats', key + '.json'))
        if raw is None:
            if self.store.get('workbench_chat_current', key) is not None:
                fail('The registered chat current file is missing; review it before publishing.')
            return None
        try:
            pointer = json.loads(raw)
            receipt = self.store.get('workbench_receipts', pointer['receipt_id'])
            fields = ('workspace', 'task_id', 'thread_id', 'plan_id', 'view_id', 'source_id', 'binding_id')
            if (raw != canonical(pointer) or pointer.get('schema') != 'taskcarry.workbench.current.v2'
                    or pointer.get('thread_id') != thread_id or pointer.get('binding_id') != key
                    or pointer.get('source_id') not in self._source_ids() or not receipt
                    or any(pointer.get(k) != receipt.get(k) for k in fields)):
                fail('Shared chat pointer does not match its immutable receipt.')
            return pointer
        except (ValueError, KeyError, TypeError) as exc:
            fail('Shared chat pointer is invalid: ' + str(exc))

    def _shared_instructions(self, root):
        return ('Read the TaskCarry shared-directory routing index at ' + str(root / ROUTER) + '.\n'
                'Use only your original chat ID verified by the host or your explicit activation card.\n'
                'Select its exact route, then read that current entry and view; retain its original task and workspace.\n'
                'If the current chat ID is unknown or has no exact route, report the missing binding; never choose the first entry, another chat or a task by title.\n'
                'The shared MCP connection uses control ' + str(self.root) + '. It does not select a task.\n'
                'Check the selected task and latest checkpoint through Core. Keep your responsibility, history and WIP.\n'
                'Publication alone is not consumption, native host loading, code adoption or business acceptance.')

    def plan_shared(self, view_id, targets):
        self.store.assert_writable()
        self._view(view_id)
        if not isinstance(targets, list) or not 1 <= len(targets) <= 24:
            fail('Plan requires 1-24 explicit chat bindings.', 'INVALID_ARGUMENT')
        groups, rows, seen = {}, [], set()
        with self.store.guard():
            for target in targets:
                allowed = {'workspace', 'task_id', 'thread_id', 'source_id', 'host', 'code_assessment', 'writes'}
                if not isinstance(target, dict) or set(target) - allowed:
                    fail('Unsupported shared target fields.', 'INVALID_ARGUMENT')
                workspace, task_id, tid = (target.get(k) for k in ('workspace', 'task_id', 'thread_id'))
                key = chat_key(tid)
                if key in seen:
                    fail('Each original chat can occur only once in a plan.', 'INVALID_ARGUMENT')
                seen.add(key)
                root = self._directory_binding(workspace, task_id)
                assert_chat_identity(self, tid, workspace, task_id)
                if target.get('source_id', self.source()['source_id']) not in self._source_ids():
                    fail('Chat belongs to another governance source.', 'WORKBENCH_SOURCE_MISMATCH')
                prior = self._chat_pointer(tid)
                if prior and any(prior[k] != target[k] for k in ('workspace', 'task_id', 'thread_id')):
                    fail('Retain the original chat task and workspace; publication cannot rebind it.', 'WORKBENCH_BINDING_MISMATCH')
                legacy = self._pointer(workspace)
                if legacy:
                    old = self.store.get('workbench_receipts', legacy['receipt_id'])
                    if old['thread_id'] == tid and old['task_id'] != task_id:
                        fail('Retain the original legacy chat task.', 'WORKBENCH_BINDING_MISMATCH')
                assessment = target.get('code_assessment')
                if (not isinstance(assessment, dict) or set(assessment) != {'status', 'reason'}
                        or assessment['status'] not in {'NO_CODE_DEPENDENCY', 'ALREADY_CONTAINS', 'SEPARATE_CODE_PLAN_REQUIRED'}
                        or not isinstance(assessment['reason'], str) or not 1 <= len(assessment['reason'].strip()) <= 2000):
                    fail('Each chat needs a bounded code-dependency assessment.', 'INVALID_ARGUMENT')
                host = target.get('host', 'codex')
                if host not in ('codex', 'none'):
                    fail('Unsupported host.', 'INVALID_ARGUMENT')
                did = self._directory_id(root)
                if did not in groups:
                    current = self._directory_current(root)
                    router = self._router(root, current)
                    groups[did] = {'directory_id': did, 'root': str(root), 'workspace': workspace,
                                   'previous': current, 'router': router, 'git': git_snapshot(root), 'writes': [], 'codex': False}
                group = groups[did]
                if group['workspace'] != workspace:
                    fail('Use one registered workspace per shared directory; do not alias the same root.')
                group['codex'] = group['codex'] or host == 'codex'
                route = {'thread_id': tid, 'task_id': task_id, 'workspace': workspace, 'binding_id': key,
                         'current_path': str(self._path('chats', key + '.json'))}
                old_route = next((r for r in group['router']['routes'] if r['thread_id'] == tid), None)
                if old_route and old_route != route:
                    fail('Existing original-chat routing identity differs.', 'WORKBENCH_BINDING_MISMATCH')
                if old_route is None:
                    group['router']['routes'].append(route)
                if len(group['router']['routes']) > 100:
                    fail('Shared directory routing is bounded to 100 chats.', 'INVALID_ARGUMENT')
                row = {**route, 'source_id': self.source()['source_id'], 'root': str(root), 'host': host,
                       'directory_id': did, 'previous': prior, 'code_assessment': assessment, 'writes': []}
                specs = target.get('writes', [])
                if not isinstance(specs, list) or len(specs) > 16:
                    fail('At most 16 explicit private writes per chat.', 'INVALID_ARGUMENT')
                paths = set()
                for spec in specs:
                    if not isinstance(spec, dict) or set(spec) - {'path', 'mode', 'section_id', 'text', 'expected_sha256'}:
                        fail('Unsupported write fields.', 'INVALID_ARGUMENT')
                    rel = spec.get('path')
                    path = private_target(root, rel)
                    if rel.casefold() in {'.codex/config.toml', ROUTER.casefold(), *paths}:
                        fail('A shared target cannot replace its router/config or duplicate a path.', 'INVALID_ARGUMENT')
                    paths.add(rel.casefold())
                    old, body = _read(path), spec.get('text')
                    if not isinstance(body, str) or len(body.encode()) > 256 * 1024:
                        fail('Navigation text must be bounded.', 'INVALID_ARGUMENT')
                    mode = spec.get('mode', 'managed_section')
                    if mode == 'managed_section':
                        new = managed_section(old, spec.get('section_id', 'navigation'), body)
                    elif mode == 'exact' and 'expected_sha256' in spec and spec['expected_sha256'] == _hash(old):
                        new = body.encode()
                    else:
                        fail('Exact writes need the actual expected hash.')
                    write = self._write_record(rel, old, new)
                    existing = next((w for w in group['writes'] if w['path'].casefold() == rel.casefold()), None)
                    if existing is not None and existing != write:
                        fail('Two chats propose conflicting bytes for the same directory file.')
                    if existing is None:
                        group['writes'].append(write)
                    row['writes'].append({'path': rel, 'sha256': write['after']})
                rows.append(row)
            for group in groups.values():
                root = Path(group['root'])
                original = legacy_current_receipt(self, group['workspace'])
                if group['previous'] is None and original:
                    if not any(r['thread_id'] == original['thread_id'] and r['task_id'] == original['task_id']
                               for r in group['router']['routes']):
                        fail('Include the existing original chat in the first shared publication; retain its task and history.',
                             'WORKBENCH_BINDING_MISMATCH')
                group['router']['routes'].sort(key=lambda r: r['thread_id'])
                router_path = private_target(root, ROUTER)
                group['writes'].append(self._write_record(ROUTER, _read(router_path), canonical(group['router'])))
                # Once enabled, future host-neutral publication must not remove the existing adapter.
                if group['codex'] or (group['previous'] or {}).get('codex'):
                    group['codex'] = True
                    path = private_target(root, '.codex/config.toml')
                    old = _read(path)
                    group['writes'].append(self._write_record('.codex/config.toml', old,
                                                              codex_instructions(old, self._shared_instructions(root))))
                del group['router']
            plan = {'schema': PLAN, 'source': self.source(), 'view_id': view_id,
                    'targets': rows, 'directories': list(groups.values())}
            if len(canonical(plan)) > MAX_PLAN_BYTES:
                fail('Split this shared plan into bounded batches.', 'INVALID_ARGUMENT')
            pid = digest_bytes(canonical(plan))
            with self.store.transaction():
                self._object('workbench_plans', pid, plan)
            immutable(self._path('plans', pid + '.json'), canonical(plan))
        return {'plan_id': pid, 'view_id': view_id, 'routing': 'shared', 'effects_executed': False,
                'targets': [{k: r[k] for k in ('workspace', 'task_id', 'thread_id', 'binding_id')} for r in rows],
                'directories': [{'root': g['root'], 'writes': [{k:v for k,v in w.items() if k != 'content'} for w in g['writes']]} for g in groups.values()],
                'plan_path': str(self._path('plans', pid + '.json'))}

    def _shared_plan(self, pid):
        self._sha(pid, 'Plan ID')
        plan = self.store.get('workbench_plans', pid)
        if not plan or plan.get('schema') != PLAN or digest_bytes(canonical(plan)) != pid:
            fail('Shared plan is missing, changed or unsupported.')
        if not self._same_local_source(plan['source']):
            fail('Shared plan belongs to another control/replica; make a new local plan.')
        return plan

    def execute_shared(self, pid):
        results = []
        self.store.assert_writable()
        with self.store.guard():
            plan = self._shared_plan(pid)
            self._view(plan['view_id'])
            for group in plan['directories']:
                rows = [r for r in plan['targets'] if r['directory_id'] == group['directory_id']]
                directory_results = []
                try:
                    root = self._directory_binding(group['workspace'])
                    if str(root) != group['root']:
                        fail('The workspace location changed.')
                    before = self._directory_current(root)
                    expected = {'schema': 'taskcarry.workbench.directory.v2', 'directory_id': group['directory_id'],
                                'source_id': self.source()['source_id'], 'workspace': group['workspace'], 'root': str(root),
                                'plan_id': pid, 'codex': group['codex'],
                                'router_sha256': next(w['after'] for w in group['writes'] if w['path'] == ROUTER),
                                'config_sha256': next((w['after'] for w in group['writes'] if w['path'] == '.codex/config.toml'), None)}
                    if before not in (group['previous'], expected):
                        results.extend({'workspace': r['workspace'], 'thread_id': r['thread_id'], 'status': 'SUPERSEDED'} for r in rows)
                        continue
                    if git_snapshot(root) != group['git']:
                        fail('Git identity, HEAD or index changed after planning; retain WIP and re-plan.')
                    for row in rows:
                        self._task(row['task_id'])
                        assert_chat_identity(self, row['thread_id'], row['workspace'], row['task_id'])
                        pointer = self._chat_pointer(row['thread_id'])
                        if pointer != row['previous'] and (pointer or {}).get('plan_id') != pid:
                            fail('A chat acquired a newer publication; keep it and re-plan.')
                    acknowledged = before == expected or any(self.store.get('workbench_receipts', pid + '.' + r['binding_id']) for r in rows)
                    for write in group['writes']:
                        allowed = (write['after'],) if acknowledged else (write['before'], write['after'])
                        if _hash(_read(private_target(root, write['path']))) not in allowed:
                            fail('A shared target changed; preserve it and re-plan: ' + write['path'])
                    for write in group['writes']:
                        path = private_target(root, write['path'])
                        actual = _hash(_read(path))
                        if actual == write['after']:
                            continue
                        if actual != write['before']:
                            fail('A shared target changed during publication.')
                        atomic_write(path, base64.b64decode(write['content'], validate=True))
                    if (git_snapshot(root) != group['git'] or any(_hash(_read(private_target(root, w['path']))) != w['after'] for w in group['writes'])):
                        fail('Verify partial actual effects before resuming.')
                    for row in rows:
                        receipt_id = pid + '.' + row['binding_id']
                        pointer = {'schema': 'taskcarry.workbench.current.v2', 'plan_id': pid, 'view_id': plan['view_id'],
                                   'receipt_id': receipt_id, **{k: row[k] for k in ('workspace','task_id','thread_id','source_id','binding_id')}}
                        receipt = self.store.get('workbench_receipts', receipt_id)
                        if receipt is None:
                            receipt = {**pointer, 'schema': 'taskcarry.workbench.receipt.v2', 'status': 'PUBLISHED',
                                       'directory_id': group['directory_id'], 'root': str(root), 'writes': row['writes'],
                                       'published_at': now(), 'code_assessment': row['code_assessment'],
                                       'git_before': group['git'], 'git_after': group['git'], 'consumer_state': 'NOT_VERIFIED'}
                            with self.store.transaction():
                                self._object('workbench_receipts', receipt_id, receipt)
                        immutable(self._path('receipts', receipt_id + '.json'), canonical(receipt))
                        atomic_write(self._path('chats', row['binding_id'] + '.json'), canonical(pointer))
                        with self.store.transaction():
                            self.store.put('workbench_chat_current', row['binding_id'], pointer)
                        directory_results.append({'workspace': row['workspace'], 'thread_id': row['thread_id'], 'task_id': row['task_id'],
                                        'status': 'PUBLISHED', 'receipt_id': receipt_id, 'view_id': plan['view_id'], 'consumer_state': 'NOT_VERIFIED'})
                    with self.store.transaction():
                        self.store.put('workbench_directory_current', group['directory_id'], expected)
                        self.store.event('shared_workbench_published', expected)
                    results.extend(directory_results)
                except (GovernanceError, OSError, ValueError) as exc:
                    results.extend({'workspace': r['workspace'], 'thread_id': r['thread_id'], 'status': 'CONFLICT',
                                    'code': getattr(exc, 'code', type(exc).__name__), 'error': str(exc)[:1000]} for r in rows)
        return {'plan_id': pid, 'routing': 'shared', 'results': results,
                'status': 'COMPLETED' if all(r['status'] == 'PUBLISHED' for r in results) else 'PARTIAL', 'business_accepted': False}

    def consume_shared(self, proof):
        self.store.assert_writable()
        keys = {'workspace','plan_id','view_id','task_id','source_id','thread_id','turn_id','evidence_path','evidence_sha256','reviewer','observed_at'}
        if not isinstance(proof, dict) or set(proof) != keys or any(not isinstance(v,str) or not v.strip() or len(v)>1000 for v in proof.values()):
            fail('Provide exact bounded original-chat consumption evidence.', 'INVALID_ARGUMENT')
        with self.store.guard():
            plan = self._shared_plan(proof['plan_id'])
            key = chat_key(proof['thread_id'])
            row = next((r for r in plan['targets'] if r['binding_id'] == key and r['workspace'] == proof['workspace']), None)
            rid = proof['plan_id'] + '.' + key
            receipt = self.store.get('workbench_receipts', rid)
            if not row or not receipt or any(proof[k] != receipt[k] for k in ('workspace','view_id','task_id','source_id','thread_id')):
                fail('Consumption must match this exact published chat, task and view.')
            evidence = validate_relative_path(self.root, proof['evidence_path'], allow_missing=False)
            if _hash(_read(evidence)) != self._sha(proof['evidence_sha256'], 'Evidence hash'):
                fail('Reviewed evidence is missing or changed.')
            record = {'schema': 'taskcarry.workbench.consumption.v2', **proof, 'receipt_id': rid,
                      'meaning': 'Caller-reviewed evidence; not independently verified native loading.'}
            cid = digest_bytes(canonical(record))
            with self.store.transaction():
                self._object('workbench_consumption', cid, record)
                self.store.put('workbench_consumed', rid, {'consumption_id': cid})
            immutable(self._path('consumption', cid + '.json'), canonical(record))
        return {'consumption_id': cid, 'receipt_id': rid, 'consumer_state': 'REVIEWED_EVIDENCE_RECORDED',
                'current_view': (self._chat_pointer(proof['thread_id']) or {}).get('plan_id') == proof['plan_id'], 'native_acceptance_verified': False}

    def _shared_item(self, pointer):
        tid, workspace = pointer['thread_id'], pointer['workspace']
        if self._chat_pointer(tid) != pointer:
            fail('Current shared pointer finalization needs review.')
        root = self._directory_binding(workspace, pointer['task_id'])
        plan = self._shared_plan(pointer['plan_id'])
        row = next(r for r in plan['targets'] if r['thread_id'] == tid)
        if row['root'] != str(root):
            fail('The original work directory moved.')
        directory = self._directory_current(root)
        group = next(g for g in plan['directories'] if g['directory_id'] == row['directory_id'])
        pending = directory is None or directory == group['previous']
        router = self._router(root, directory)
        route = next((r for r in router['routes'] if r['thread_id'] == tid), None)
        matches = (route is not None and all(route[k] == pointer[k] for k in ('workspace','task_id','thread_id','binding_id'))
                   and all(_hash(_read(private_target(root,w['path']))) == w['sha256'] for w in row['writes']))
        if directory and directory.get('codex'):
            raw = _read(private_target(root, '.codex/config.toml'))
            matches = matches and _hash(raw) == directory['config_sha256']
        chosen = self.store.get('workbench_consumed', pointer['receipt_id'], {})
        evidence = self.store.get('workbench_consumption', chosen.get('consumption_id',''))
        consumed = 'NOT_VERIFIED'
        if evidence:
            path = validate_relative_path(self.root, evidence['evidence_path'])
            consumed = 'REVIEWED_EVIDENCE_RECORDED' if _hash(_read(path)) == evidence['evidence_sha256'] else 'EVIDENCE_CHANGED_OR_MISSING'
        return {**pointer, 'state': 'PUBLISHED' if matches else 'ENTRY_CHANGED', 'consumer_state': consumed,
                'consumption_id': chosen.get('consumption_id'), 'finalization_pending': pending,
                'source_freshness': self._freshness(self._view(pointer['view_id'])),
                'view_path': str(self._path('views',pointer['view_id'],'view.md')),
                'current_path': str(self._path('chats',pointer['binding_id']+'.json')), 'native_acceptance_verified': False}

    def status_shared(self, workspace=None, thread_id=None, limit=20, cursor=None):
        if type(limit) is not int or not 1 <= limit <= 100 or (cursor is not None and (not isinstance(cursor,str) or len(cursor)>256)):
            fail('Use a bounded shared status page.', 'INVALID_ARGUMENT')
        if workspace is not None:
            _id(workspace, 'Workspace')
        if thread_id is not None:
            chat_key(thread_id)
        with self.store._connect(readonly=True) as db:
            # Union retained v1 workspaces and v2 chat pointers; avoid double counting a shared directory.
            sql = """SELECT locator, kind, value FROM (
              SELECT 'c:'||key AS locator, 'chat' AS kind, value FROM records WHERE collection='workbench_chat_current'
              UNION ALL
              SELECT 'w:'||key, 'legacy', value FROM records w WHERE collection='workspaces'
                AND NOT EXISTS (SELECT 1 FROM records d WHERE d.collection='workbench_directory_current'
                  AND json_extract(d.value,'$.workspace')=w.key)
            ) WHERE locator>? AND (? IS NULL OR (kind='chat' AND json_extract(value,'$.workspace')=?)
                    OR (kind='legacy' AND json_extract(value,'$.name')=?))
              AND (? IS NULL OR kind='legacy' OR json_extract(value,'$.thread_id')=?)
              ORDER BY locator LIMIT ?"""
            rows = db.execute(sql,(cursor or '',workspace,workspace,workspace,thread_id,thread_id,limit+1)).fetchall()
        result = []
        for locator, kind, raw in rows[:limit]:
            value = json.loads(raw)
            if kind == 'legacy':
                old = super()._status(value['name'], 1, None)['items']
                result.extend(r for r in old if thread_id is None or r.get('thread_id') == thread_id)
                continue
            try:
                result.append(self._shared_item(value))
            except (GovernanceError,OSError,ValueError,KeyError,StopIteration) as exc:
                result.append({**value, 'state':'UNVERIFIED', 'error':str(exc)[:1000]})
        return {'source': self.source(), 'items': result, 'next_cursor': rows[limit-1][0] if len(rows)>limit else None,
                'read_only': True, 'routing':'shared', 'meaning':'Exact chat routing; no task is inferred from directory or list order.'}
