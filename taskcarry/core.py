"""Project-local task memory, exact checkpoints and conditional experience.

Records describe saved evidence, never business acceptance or model internals.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess
import uuid

from .store import Store, GovernanceError, now, TERMINAL_STATES

MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_CHECKPOINT_BYTES = 128 * 1024 * 1024
MAX_PATHS = 500
CURRENT_COLLECTIONS = ('tasks', 'stages', 'operations', 'workspaces', 'artifacts', 'checkpoints')


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _linked(path):
    if path.is_symlink():
        return True
    try:
        return bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)
    except FileNotFoundError:
        return False


def validate_relative_path(root, value, allow_missing=True):
    if not isinstance(value, str) or not value or '\x00' in value or '\\' in value:
        raise GovernanceError('UNSAFE_PATH', 'Use an explicit relative path with forward slashes.')
    relative = PurePosixPath(value)
    if relative.is_absolute() or PureWindowsPath(value).drive or any(p in ('..', '.') for p in value.split('/')):
        raise GovernanceError('UNSAFE_PATH', 'Absolute paths and parent traversal are not allowed.')
    for part in relative.parts:
        low = part.casefold()
        if re.fullmatch(r'(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', low):
            raise GovernanceError('UNSAFE_PATH', 'Reserved device filenames are not portable file paths.')
        if low in ('.git', '.taskcarry') or ':' in part or part.endswith((' ', '.')):
            raise GovernanceError('RESERVED_PATH', 'Repository and governance metadata cannot be captured.')
        if (low in ('.env', 'credentials', 'credentials.json', 'id_rsa', 'id_ed25519')
                or low.startswith('.env.') and low not in ('.env.example', '.env.sample', '.env.template')
                or low.endswith(('.pfx', '.p12', '.key', '.pem'))):
            raise GovernanceError('SECRET_PATH', 'This filename may contain credentials; it is excluded by default.')
    root = Path(root).resolve()
    candidate = root.joinpath(*relative.parts)
    check = root
    for part in relative.parts:
        check = check / part
        if _linked(check):
            raise GovernanceError('SYMLINK_PATH', 'Symbolic links and junctions cannot be captured.')
    if not candidate.resolve().is_relative_to(root):
        raise GovernanceError('UNSAFE_PATH', 'The path resolves outside its workspace.')
    if candidate.exists() and not candidate.is_file():
        raise GovernanceError('NOT_FILE', 'Checkpoint paths must name individual regular files.')
    if not allow_missing and not candidate.is_file():
        raise GovernanceError('MISSING_FILE', 'The requested file does not exist.', {'path': value})
    return candidate


def read_file_bytes(path, max_bytes=MAX_FILE_BYTES):
    path = Path(path)
    if _linked(path):
        raise GovernanceError('SYMLINK_PATH', 'Symbolic links and junctions are not supported.')
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise GovernanceError('NOT_FILE', 'Only regular files can be read.')
    if before.st_size > max_bytes:
        raise GovernanceError('FILE_TOO_LARGE', 'Use an artifact reference for files exceeding the snapshot limit.')
    with path.open('rb') as stream:
        content = stream.read(max_bytes + 1)
    after = path.stat()
    if len(content) > max_bytes or (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise GovernanceError('SOURCE_CHANGED', 'The file changed during capture; no checkpoint was published.')
    return content


def git(root, *args, input_bytes=None, check=True):
    environment = os.environ.copy()
    for key in list(environment):
        if key.startswith('GIT_'):
            environment.pop(key)
    environment.update(GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0', GIT_CONFIG_NOSYSTEM='1')
    try:
        result = subprocess.run(['git', '--literal-pathspecs', '-c', 'core.hooksPath=' + os.devnull, '-c', 'core.autocrlf=false', '-c', 'commit.gpgSign=false', '-C', str(root), *args],
                                input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=environment, timeout=60, check=False)
    except FileNotFoundError as exc:
        raise GovernanceError('GIT_UNAVAILABLE', 'Git is required for this operation.') from exc
    except subprocess.TimeoutExpired as exc:
        raise GovernanceError('GIT_TIMEOUT', 'The bounded Git operation timed out.') from exc
    if check and result.returncode:
        raise GovernanceError('GIT_ERROR', 'Git could not complete the operation.',
                              {'command': args[0] if args else '', 'stderr': result.stderr.decode('utf-8', 'replace')[:2000]})
    return result


def _id(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', value):
        raise GovernanceError('INVALID_ID', f'{label} must be 1-100 ASCII letters, digits, dots, underscores or hyphens.')
    return value


def _checkpoint_uses_git(workspace):
    """Plain files need no Git; repository-shaped paths require verification.

    Inspect ancestors as well as the selected directory so a missing or broken
    Git executable cannot silently discard a repository's HEAD/index layers.
    lstat preserves dangling markers and propagates unreadable metadata instead
    of treating either as proof that this is a plain directory.
    """
    def present(path):
        try:
            path.lstat()
        except FileNotFoundError:
            return False
        return True

    try:
        for parent in (workspace, *workspace.parents):
            if present(parent / '.git'):
                break
            head = present(parent / 'HEAD')
            objects = present(parent / 'objects')
            refs = present(parent / 'refs') or present(parent / 'packed-refs')
            common = present(parent / 'commondir')
            # Include split metadata and damaged bare repositories without HEAD.
            if (head and (objects or refs or common)) or (objects and refs):
                break
        else:
            return False
    except OSError as exc:
        raise GovernanceError('GIT_WORKSPACE_UNVERIFIED',
                              'Could not inspect the workspace Git boundary.') from exc

    try:
        result = git(workspace, 'rev-parse', '--is-inside-work-tree')
    except OSError as exc:
        raise GovernanceError('GIT_UNAVAILABLE', 'Git could not be executed for this workspace.') from exc
    if result.stdout.strip() != b'true':
        raise GovernanceError('GIT_WORKSPACE_ROOT', 'Use a Git working tree root, not repository metadata.')
    return True


class Core:
    def __init__(self, project):
        self.store = Store(project)
        self.root = self.store.root
        config = self.store.get('config', 'project')
        if not config or config.get('schema_version') != 1:
            raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'Use a compatible toolkit version for this project state.')

    @classmethod
    def initialize(cls, project, name='TaskCarry project'):
        store = Store(project, create=True)
        with store.transaction():
            config = store.get('config', 'project')
            if config is not None and config.get('schema_version') != 1:
                raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'Initialization cannot downgrade existing project state.')
            if config is None:
                config = {'name': name, 'schema_version': 1, 'created_at': now(), 'synthetic': False}
                store.put('config', 'project', config)
                store.put('experience', 'receipt-recovery-v1', {
                    'rule_id': 'receipt-recovery-v1', 'code': 'EFFECT_PRESENT_RECEIPT_MISSING',
                    'operation': 'reconcile', 'action': 'verify_and_finalize', 'task_id': None,
                    'version': '1', 'enabled': True, 'updated_at': now()})
                store.event('project_initialized', {'name': name})
        return {'initialized': True, 'project': str(store.root), 'config': config}

    def _task(self, task_id):
        task = self.store.get('tasks', _id(task_id, 'Task ID'))
        if task is None:
            raise GovernanceError('TASK_NOT_FOUND', 'Create the task before capturing or delivering work.', {'task_id': task_id})
        return task

    def task(self, task_id, title=None, workstream=None, state=None):
        task_id = _id(task_id, 'Task ID')
        if state is not None and state not in ('active', 'paused', 'waiting', 'complete'):
            raise GovernanceError('INVALID_STATE', 'Task state must be active, paused, waiting or complete.')
        with self.store.transaction():
            previous = self.store.get('tasks', task_id)
            result = dict(previous or {'task_id': task_id, 'title': title or task_id, 'workstream': workstream or task_id,
                                       'state': 'active', 'created_at': now()})
            for key, value in (('title', title), ('workstream', workstream), ('state', state)):
                if value is not None:
                    result[key] = value
            if result != previous:
                result['updated_at'] = now()
                self.store.put('tasks', task_id, result)
                self.store.event('task_changed', result)
            return result

    def status(self):
        supporting = ('observations', 'runs', 'issues', 'fixes')
        records = self.store.snapshot(CURRENT_COLLECTIONS + supporting)
        result = self._current_view(records)
        result['continuity'] = {name: records[name] for name in supporting}
        result['storage'] = self.store.storage_status()
        return result

    def upgrade(self):
        """Opt in to the indexed agenda without rewriting project evidence."""
        return self.store.upgrade()

    @staticmethod
    def _current_view(records):
        tasks, stages, operations, workspaces = (records[x] for x in ('tasks', 'stages', 'operations', 'workspaces'))
        terminal = TERMINAL_STATES
        pending_stages = [s for s in stages if str(s.get('state', s.get('status', 'queued'))).lower() not in terminal]
        # Submission validates cumulative ancestry. Project that declaration here
        # without pretending that the older stage already has a terminal receipt.
        stage_index = {s.get('stage_id'): s for s in stages if s.get('stage_id')}
        covered_pending = {}
        for successor in stages:
            if (str(successor.get('status', successor.get('state', ''))).lower() not in ('queued', 'conflict')
                    or successor.get('relation') != 'cumulative'
                    or not successor.get('task_id') or not successor.get('workspace')
                    or not successor.get('stage_id')):
                continue
            remaining, visited = list(successor.get('supersedes', [])), {successor['stage_id']}
            while remaining:
                old_id = remaining.pop()
                if old_id in visited:
                    continue
                visited.add(old_id)
                old = stage_index.get(old_id)
                if not old or old.get('task_id') != successor['task_id'] or old.get('workspace') != successor['workspace']:
                    continue
                if str(old.get('status', old.get('state', ''))).lower() == 'queued':
                    covered_pending[old_id] = successor['stage_id']
                if old.get('relation') == 'cumulative':
                    remaining.extend(old.get('supersedes', []))
        pending_stages = [s for s in pending_stages if s.get('stage_id') not in covered_pending]
        pending_operations = [o for o in operations if str(o.get('state', o.get('status', 'pending'))).lower() not in terminal]
        artifacts = records['artifacts']
        return {'tasks': tasks, 'stages': stages, 'operations': operations, 'workspaces': workspaces,
                'actionable': {'stages': pending_stages, 'operations': pending_operations,
                               'artifacts': [a for a in artifacts if a.get('decision') not in ('ignore', 'dismiss', 'no_backup_needed') and not a.get('backup_verified')]},
                'retained_task_state': [t for t in tasks if t['state'] in ('paused', 'waiting')],
                'covered_pending_stages': [{'stage_id': sid, 'awaiting_successor': successor}
                                           for sid, successor in sorted(covered_pending.items())],
                'checkpoints': records['checkpoints'], 'artifacts': artifacts,
                'history_counts': {'terminal_stages': sum(str(s.get('state', s.get('status', 'queued'))).lower() in terminal for s in stages),
                                   'terminal_operations': len(operations) - len(pending_operations)},
                'meaning': 'Task state and checkpoint retention do not create a delivery obligation or imply business acceptance.'}

    def agenda(self, limit=20, previous_fingerprint=None, cursor=None):
        """Select a page of recorded current work; never execute or acknowledge it.

        The limit bounds returned items. Indexed projects load current records
        and their linked dependencies, not unrelated terminal history. Cursor
        state is returned rather than written into the governance database.
        """
        if type(limit) is not int or not 1 <= limit <= 100:
            raise GovernanceError('INVALID_ARGUMENT', 'Agenda limit must be an integer from 1 to 100.')
        if previous_fingerprint is not None and (
                not isinstance(previous_fingerprint, str)
                or not re.fullmatch(r'[0-9a-f]{64}', previous_fingerprint)):
            raise GovernanceError('INVALID_ARGUMENT', 'The previous agenda fingerprint must be a SHA-256 value.')
        cursor_data = None
        if cursor is not None:
            try:
                if not isinstance(cursor, str) or not 1 <= len(cursor) <= 1024:
                    raise ValueError('Invalid cursor size')
                raw = base64.b64decode(cursor + '=' * (-len(cursor) % 4), altchars=b'-_', validate=True)
                cursor_data = json.loads(raw)
                if (not isinstance(cursor_data, dict)
                        or set(cursor_data) != {'version', 'offset', 'fingerprint'}
                        or type(cursor_data['version']) is not int or cursor_data['version'] != 1
                        or type(cursor_data['offset']) is not int or cursor_data['offset'] < 1
                        or not isinstance(cursor_data['fingerprint'], str)
                        or not re.fullmatch(r'[0-9a-f]{64}', cursor_data['fingerprint'])):
                    raise ValueError('Invalid cursor contents')
            except (ValueError, TypeError, UnicodeError) as exc:
                raise GovernanceError('AGENDA_CURSOR_INVALID', 'Use an unchanged next_cursor from an agenda result.') from exc

        records = self.store.snapshot_current()
        plans = {plan.get('plan_id'): plan for plan in records['plans']}
        current = self._current_view(records)
        current['actionable']['issues'] = [r for r in records['issues'] if r.get('state') != 'resolved']
        current['actionable']['runs'] = [r for r in records['runs'] if r.get('state') != 'COMPLETED']
        # Observation timestamps are not new work; evidence, outcomes and inputs are.
        def content(record):
            return {key: value for key, value in record.items()
                    if key not in {'created_at', 'updated_at', 'accepted_at', 'completed_at'}}

        def fingerprint(value):
            return digest_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                           separators=(',', ':'), allow_nan=False).encode('utf-8'))

        items, inputs = [], []
        selected_stages, referenced_workspaces = set(), set()
        kinds = (('operation', 'operations', 'operation_id'),
                 ('stage', 'stages', 'stage_id'), ('artifact', 'artifacts', 'artifact_id'),
                 ('issue', 'issues', 'issue_id'), ('run', 'runs', 'run_id'))
        for kind, collection, id_key in kinds:
            for record in sorted(current['actionable'][collection], key=lambda value: value.get(id_key, '')):
                record_id = record.get(id_key)
                if not isinstance(record_id, str) or not record_id:
                    raise GovernanceError('STATE_RECORD_INVALID', 'An actionable record has no stable identity.',
                                          {'collection': collection})
                state = str(record.get('state', record.get('status', 'recorded')))
                operation = record.get('kind') if kind == 'operation' else 'reconcile' if kind == 'stage' else 'artifact'
                code = record.get('code')
                # A recorded effect may justify inspecting this recovery rule;
                # only the original executor can verify the actual Git effect.
                if not code and operation == 'reconcile' and state.upper() == 'EFFECT_APPLIED' and record.get('candidate'):
                    code = 'EFFECT_PRESENT_RECEIPT_MISSING'
                matches = self._experience_matches(records['experience'], code, operation, record.get('task_id')) if code else []
                suggestions = []
                for rule in matches:
                    suggestion = {**content(rule), 'requires_current_evidence': True,
                                  'execution': 'candidate_only'}
                    if rule['action'] == 'refresh_plan':
                        # A new plan is a proposal, never permission to replay an
                        # effect. Derive its arguments from the original plan.
                        plan = plans.get(record.get('plan_id'), {})
                        if (kind == 'operation' and not record.get('candidate')
                                and not record.get('stash')
                                and record.get('effect_state') == 'NOT_APPLIED'
                                and plan.get('kind') == operation
                                and operation in {'adopt', 'reconcile'}):
                            fields = ('workspace', 'baseline') if operation == 'adopt' else ('baseline',)
                            if all(isinstance(plan.get(key), str) and plan[key] for key in fields):
                                args = {key: plan[key] for key in fields}
                                if operation == 'reconcile':
                                    args['limit'] = plan.get('selection', {}).get('limit', 20)
                                suggestion['plan_request'] = {'action': operation,
                                                              'arguments': {**args, 'execute': False}}
                                suggestion['execution'] = 'proposal_only'
                                suggestion['requires_new_plan_review'] = True
                    suggestions.append(suggestion)
                item_input = {'record': content(record), 'experience_candidates': suggestions}
                inputs.append({'kind': kind, 'id': record_id, **item_input})
                item = {'kind': kind, 'id': kind + ':' + record_id, 'record_id': record_id,
                        'task_id': record.get('task_id'), 'workspace': record.get('workspace'),
                        'state': state, 'code': code, 'input_fingerprint': fingerprint(item_input),
                        'experience_candidates': suggestions}
                if kind == 'operation':
                    item['next_step'] = 'Inspect the original operation and verify actual effects before continuing its missing step.'
                    if record.get('stage_id'):
                        selected_stages.add(record['stage_id'])
                elif kind == 'stage':
                    item['next_step'] = 'Review the frozen delivery and its current reconciliation plan.'
                    selected_stages.add(record_id)
                elif kind == 'artifact':
                    item['next_step'] = 'Review the retained artifact relationship, decision and backup evidence.'
                elif kind == 'issue':
                    item['next_step'] = 'Review this recorded condition and its resolution evidence; an issue record never replaces an operation receipt.'
                else:
                    item['next_step'] = 'Inspect the frozen run selection and continue only its unfinished operations or receipt.'
                items.append(item)
                referenced_workspaces.update(record[name] for name in ('workspace', 'baseline')
                                             if isinstance(record.get(name), str))

        # A received predecessor may affect the next delta. Include only such
        # dependencies, not unrelated completed history, in the current fingerprint.
        stage_index = {stage.get('stage_id'): stage for stage in current['stages']}
        dependencies, remaining = {}, list(selected_stages)
        while remaining:
            stage_id = remaining.pop()
            if stage_id in dependencies or stage_id not in stage_index:
                continue
            stage = stage_index[stage_id]
            dependencies[stage_id] = content(stage)
            referenced_workspaces.update(stage[name] for name in ('workspace', 'accepted_baseline')
                                         if isinstance(stage.get(name), str))
            remaining.extend(stage.get('supersedes', []))
        active_tasks = [content(task) for task in current['tasks'] if task.get('state') != 'complete']
        workspace_inputs = [content(workspace) for workspace in current['workspaces']
                            if workspace.get('name') in referenced_workspaces
                            or workspace.get('path') in referenced_workspaces]
        input_fingerprint = fingerprint({'project': str(self.root), 'items': inputs,
                                         'tasks': active_tasks, 'workspaces': workspace_inputs,
                                         'stage_dependencies': dependencies,
                                         'run_dependencies': {
                                             'observations': [o for o in records['observations'] if o.get('observation_id') in
                                                              {key for r in current['actionable']['runs'] for key in r.get('observation_ids', [])}],
                                             'stages': [s for s in records['stages'] if s.get('stage_id') in
                                                        {key for r in current['actionable']['runs'] for key in r.get('stage_ids', [])}],
                                             'operations': [o for o in records['operations'] if o.get('operation_id') in
                                                            {key for r in current['actionable']['runs'] for key in r.get('operation_ids', [])}]}})
        if cursor_data and cursor_data['fingerprint'] != input_fingerprint:
            raise GovernanceError('AGENDA_CURSOR_STALE', 'Recorded work changed; read a fresh first page.',
                                  {'current_fingerprint': input_fingerprint})
        offset = cursor_data['offset'] if cursor_data else 0
        if cursor_data and offset >= len(items):
            raise GovernanceError('AGENDA_CURSOR_INVALID', 'The cursor offset is outside the current agenda.')
        page = items[offset:offset + limit]
        end = offset + len(page)
        next_cursor = None
        if end < len(items):
            next_cursor = base64.urlsafe_b64encode(json.dumps(
                {'version': 1, 'offset': end, 'fingerprint': input_fingerprint},
                sort_keys=True, separators=(',', ':'),
            ).encode('utf-8')).decode('ascii').rstrip('=')
        counts = {collection: len(current['actionable'][collection]) for _, collection, _ in kinds}
        counts.update(retained_tasks=len(current['retained_task_state']),
                      covered_stages=len(current['covered_pending_stages']))
        return {'items': page, 'counts': counts, 'total': len(items), 'returned': len(page),
                'offset': offset, 'truncated': len(items) - end, 'next_cursor': next_cursor,
                'fingerprint': input_fingerprint,
                'storage': records['_storage'],
                'changed': previous_fingerprint is None or previous_fingerprint != input_fingerprint,
                'selection_only': True, 'effects_executed': False, 'project_complete': None,
                'meaning': 'This is a bounded selection of recorded work, not an execution, retry, acknowledgment or proof of project completion. Verify live conditions before acting.'}

    def _snapshot(self, data):
        digest = digest_bytes(data)
        directory = self.store.directory / 'objects'
        if _linked(directory):
            raise GovernanceError('UNSAFE_METADATA', 'Snapshot storage cannot be a symbolic link.')
        directory.mkdir(exist_ok=True)
        target = directory / digest
        if target.exists():
            if digest_bytes(read_file_bytes(target)) != digest:
                raise GovernanceError('SNAPSHOT_CORRUPT', 'An existing immutable snapshot failed verification.')
        else:
            try:
                with target.open('xb') as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            except FileExistsError:
                if digest_bytes(read_file_bytes(target)) != digest:
                    raise GovernanceError('SNAPSHOT_CORRUPT', 'A concurrent snapshot failed verification.')
        return {'sha256': digest, 'size': len(data)}

    def _blob(self, workspace, oid, mode):
        if mode not in ('100644', '100755'):
            raise GovernanceError('UNSUPPORTED_GIT_ENTRY', 'Links, submodules, directories and unmerged entries are not checkpoint files.')
        size = int(git(workspace, 'cat-file', '-s', oid).stdout.strip())
        if size > MAX_FILE_BYTES:
            raise GovernanceError('FILE_TOO_LARGE', 'A Git blob exceeds the checkpoint file limit.')
        data = git(workspace, 'cat-file', 'blob', oid).stdout
        return {**self._snapshot(data), 'mode': mode, 'git_oid': oid}

    def checkpoint(self, task_id, workspace, paths, next_step, decision='', paused=False):
        if (not isinstance(paths, list) or not paths or len(paths) > MAX_PATHS
                or any(not isinstance(p, str) for p in paths)
                or len({p.casefold() for p in paths}) != len(paths)):
            raise GovernanceError('INVALID_PATHS', 'Provide 1-500 unique explicit file paths.')
        raw_workspace = Path(workspace).expanduser().absolute()
        if any(_linked(p) for p in (raw_workspace, *raw_workspace.parents)):
            raise GovernanceError('SYMLINK_PATH', 'Workspace cannot traverse symbolic links or junctions.')
        workspace = raw_workspace.resolve()
        if not workspace.is_dir():
            raise GovernanceError('MISSING_WORKSPACE', 'The source workspace does not exist.')
        for path in paths:
            validate_relative_path(workspace, path)
        with self.store.guard():
            task = self._task(task_id)
            is_git = _checkpoint_uses_git(workspace)
            if is_git and Path(git(workspace, 'rev-parse', '--show-toplevel').stdout.decode().strip()).resolve() != workspace:
                raise GovernanceError('GIT_WORKSPACE_ROOT', 'Use the Git worktree root and paths relative to that root.')
            head = git(workspace, 'rev-parse', '--verify', 'HEAD', check=False).stdout.decode().strip() if is_git else None
            index_before = git(workspace, 'ls-files', '--stage', '-z', '--', *paths).stdout if is_git else b''
            files, total = [], 0
            index = {}
            for entry in index_before.split(b'\x00'):
                if not entry:
                    continue
                metadata, encoded_path = entry.split(b'\t', 1)
                mode, oid, stage = metadata.decode().split()
                if stage != '0':
                    raise GovernanceError('UNMERGED_INDEX', 'Resolve or separately preserve merge-conflict stages before checkpointing.')
                index[encoded_path.decode('utf-8')] = (mode, oid)
            for path in paths:
                source = validate_relative_path(workspace, path)
                record = {'path': path, 'head': None, 'index': None, 'worktree': None}
                if is_git and head:
                    entry = git(workspace, 'ls-tree', '-z', head, '--', path).stdout.rstrip(b'\x00')
                    if entry:
                        meta, _ = entry.split(b'\t', 1)
                        mode, kind, oid = meta.decode().split()
                        record['head'] = self._blob(workspace, oid, mode)
                if path in index:
                    mode, oid = index[path]
                    record['index'] = self._blob(workspace, oid, mode)
                if source.exists():
                    data = read_file_bytes(source)
                    record['worktree'] = {**self._snapshot(data), 'mode': '100755' if source.stat().st_mode & stat.S_IXUSR else '100644'}
                if all(record[layer] is None for layer in ('head', 'index', 'worktree')):
                    raise GovernanceError('MISSING_FILE', 'A selected path has no Git or filesystem content.', {'path': path})
                total += sum(record[layer]['size'] for layer in ('head', 'index', 'worktree') if record[layer])
                if total > MAX_CHECKPOINT_BYTES:
                    raise GovernanceError('CHECKPOINT_TOO_LARGE', 'The checkpoint exceeds its total snapshot limit.')
                files.append(record)
            if is_git:
                if index_before != git(workspace, 'ls-files', '--stage', '-z', '--', *paths).stdout or head != git(workspace, 'rev-parse', '--verify', 'HEAD', check=False).stdout.decode().strip():
                    raise GovernanceError('SOURCE_CHANGED', 'Git HEAD or selected index entries changed during capture.')
            for record in files:
                source = validate_relative_path(workspace, record['path'])
                frozen = record['worktree']
                if (source.exists() != (frozen is not None)) or (frozen and digest_bytes(read_file_bytes(source)) != frozen['sha256']):
                    raise GovernanceError('SOURCE_CHANGED', 'A selected worktree file changed during capture.')
            if not is_git and _checkpoint_uses_git(workspace):
                raise GovernanceError('SOURCE_CHANGED', 'The plain workspace became a Git repository during capture.')
            checkpoint_id = 'cp-' + uuid.uuid4().hex
            result = {'checkpoint_id': checkpoint_id, 'task_id': task_id, 'workspace': str(workspace),
                      'git': is_git, 'original_head': head or None, 'files': files, 'next_step': next_step,
                      'decision': decision, 'created_at': now(), 'scope': 'selected_files_only',
                      'delivery': False, 'total_layer_bytes': total}
            # Immutable objects may exist before publication, but the checkpoint,
            # task pointer and its evidence event become visible together.
            with self.store.transaction():
                self.store.put('checkpoints', checkpoint_id, result)
                task.update(latest_checkpoint=checkpoint_id, next_step=next_step, updated_at=now())
                if paused:
                    task['state'] = 'paused'
                self.store.put('tasks', task_id, task)
                self.store.event('checkpoint_saved', {'checkpoint_id': checkpoint_id, 'task_id': task_id})
            return result

    def _snapshot_bytes(self, reference):
        digest = reference.get('sha256', '')
        if not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise GovernanceError('SNAPSHOT_CORRUPT', 'Invalid snapshot object identity.')
        source = self.store.directory / 'objects' / digest
        if _linked(source.parent) or _linked(source) or not source.is_file():
            raise GovernanceError('SNAPSHOT_CORRUPT', 'Snapshot object is missing or unsafe.')
        data = read_file_bytes(source)
        if digest_bytes(data) != digest or len(data) != reference['size']:
            raise GovernanceError('SNAPSHOT_CORRUPT', 'Snapshot digest or size verification failed.')
        return data

    @staticmethod
    def _restore_digest(value):
        return digest_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                       separators=(',', ':'), allow_nan=False).encode('utf-8'))

    @staticmethod
    def _restore_directory_identity(destination):
        if _linked(destination):
            raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'The restore destination became a link.')
        info = destination.stat()
        if not stat.S_ISDIR(info.st_mode):
            raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'The restore destination is not a directory.')
        return {'device': info.st_dev, 'inode': info.st_ino,
                'birthtime_ns': getattr(info, 'st_birthtime_ns', None)}

    @staticmethod
    def _restore_metadata(metadata):
        """Bounded evidence for the newly created repository, without links."""
        records, total, pending = {}, 0, [metadata]
        while pending:
            directory = pending.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    relative = path.relative_to(metadata).as_posix()
                    if _linked(path):
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git metadata contains a link.')
                    if entry.is_dir(follow_symlinks=False):
                        records[relative] = {'directory': True}
                        pending.append(path)
                    else:
                        content = read_file_bytes(path, max_bytes=MAX_CHECKPOINT_BYTES)
                        total += len(content)
                        records[relative] = {'sha256': digest_bytes(content), 'size': len(content),
                                             'mode': stat.S_IMODE(path.stat().st_mode)}
                    if len(records) > MAX_PATHS * 8 or total > MAX_CHECKPOINT_BYTES * 2:
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git metadata exceeds verification limits.')
        return records

    def _restore_effect(self, checkpoint, destination, expected_git=None):
        """Read exact restored layers, including absence, without repairing them."""
        expected = {record['path']: record['worktree'] for record in checkpoint['files']
                    if record['worktree'] is not None}
        directories = {str(parent) for path in expected for parent in PurePosixPath(path).parents
                       if str(parent) != '.'}
        files, seen_directories, pending = {}, set(), [destination]
        while pending:
            directory = pending.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    relative = path.relative_to(destination).as_posix()
                    if _linked(path):
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'A restored path became a link.', {'path': relative})
                    if relative == '.git' and checkpoint['git']:
                        if not entry.is_dir(follow_symlinks=False):
                            raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git metadata was replaced.')
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if relative not in directories:
                            raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'An extra directory exists in the restored workspace.', {'path': relative})
                        seen_directories.add(relative)
                        pending.append(path)
                        continue
                    if relative not in expected:
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'An extra path exists in the restored workspace.', {'path': relative})
                    content = read_file_bytes(path)
                    reference = expected[relative]
                    mode = '100755' if path.stat().st_mode & stat.S_IXUSR else '100644'
                    if (digest_bytes(content) != reference['sha256'] or len(content) != reference['size']
                            or os.name != 'nt' and mode != reference['mode']):
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored file content or mode changed.', {'path': relative})
                    files[relative] = {'sha256': digest_bytes(content), 'size': len(content), 'mode': mode}
        if set(files) != set(expected) or seen_directories != directories:
            raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored files or directories are missing.')
        result = {'directory_identity': self._restore_directory_identity(destination),
                  'files': files, 'directories': sorted(seen_directories), 'git': None}
        if checkpoint['git']:
            metadata = destination / '.git'
            metadata_identity = self._restore_directory_identity(metadata)
            metadata_files = self._restore_metadata(metadata)
            if expected_git is not None and (metadata_identity != expected_git.get('metadata_identity')
                                            or metadata_files != expected_git.get('metadata_files')):
                raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git metadata changed; no Git commands executed.')
            if (Path(git(destination, 'rev-parse', '--show-toplevel').stdout.decode().strip()).resolve() != destination
                    or Path(git(destination, 'rev-parse', '--absolute-git-dir').stdout.decode().strip()).resolve() != metadata):
                raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git repository identity changed.')
            if (metadata / 'commondir').exists() or _linked(metadata / 'commondir'):
                raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git metadata was redirected.')
            head = git(destination, 'rev-parse', '--verify', 'HEAD').stdout.decode().strip()
            index = git(destination, 'ls-files', '--stage', '-z').stdout
            tree = git(destination, 'ls-tree', '-r', '-z', '--full-tree', 'HEAD').stdout
            for layer, entries in (('head', tree), ('index', index)):
                wanted = {record['path']: record[layer] for record in checkpoint['files'] if record[layer] is not None}
                actual = {}
                for entry in entries.split(b'\0'):
                    if not entry:
                        continue
                    fields, name = entry.split(b'\t', 1)
                    fields = fields.decode().split()
                    mode, oid = (fields[0], fields[2]) if layer == 'head' else (fields[0], fields[1])
                    relative = name.decode('utf-8')
                    if (relative not in wanted or mode != wanted[relative]['mode']
                            or layer == 'index' and fields[2] != '0' or relative in actual):
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git layer differs from its checkpoint.')
                    size = int(git(destination, 'cat-file', '-s', oid).stdout.strip())
                    if size != wanted[relative]['size'] or size > MAX_FILE_BYTES:
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git blob size changed.')
                    if digest_bytes(git(destination, 'cat-file', 'blob', oid).stdout) != wanted[relative]['sha256']:
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Restored Git blob content changed.')
                    actual[relative] = oid
                if set(actual) != set(wanted):
                    raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'A restored Git layer has missing paths.')
            result['git'] = {'head': head, 'index_entries_sha256': digest_bytes(index),
                             'index_file_sha256': digest_bytes(read_file_bytes(metadata / 'index')),
                             'head_file_sha256': digest_bytes(read_file_bytes(metadata / 'HEAD')),
                             'config_sha256': digest_bytes(read_file_bytes(metadata / 'config')),
                             'metadata_identity': metadata_identity, 'metadata_files': metadata_files}
        return result

    def _restore_finalize(self, checkpoint, destination, operation):
        """A known complete effect permits receipt publication, never replay."""
        oid = operation['operation_id']
        try:
            actual = self._restore_effect(checkpoint, destination, operation.get('effect_fingerprint', {}).get('git'))
        except (OSError, GovernanceError) as exc:
            raise GovernanceError('RESTORE_REVIEW_REQUIRED',
                                  'The recorded restore effect cannot be verified; destination preserved.',
                                  {'operation_id': oid, 'reason': getattr(exc, 'code', type(exc).__name__)}) from exc
        if (actual != operation.get('effect_fingerprint')
                or self._restore_digest(actual) != operation.get('effect_sha256')
                or actual['directory_identity'] != operation.get('destination_identity')):
            raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'The restored destination changed; no effects replayed.',
                                  {'operation_id': oid})
        result = {'checkpoint_id': operation['checkpoint_id'], 'destination': str(destination), 'restored': True,
                  'synthetic_git_baseline': checkpoint['git'], 'original_head': checkpoint['original_head'],
                  'scope': 'selected_files_only', 'original_workspace_modified': False, 'operation_id': oid}
        receipt = {'operation_id': oid, 'checkpoint_id': operation['checkpoint_id'], 'destination': str(destination),
                   'checkpoint_sha256': operation['checkpoint_sha256'],
                   'effect_sha256': operation['effect_sha256'], 'verified': True, 'result': result}
        if operation['status'] == 'COMPLETED':
            if self.store.get('restore_receipts', oid) != receipt:
                raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'The completed restore receipt is inconsistent.', {'operation_id': oid})
            return {**result, 'reused': True}
        with self.store.transaction():
            self.store.put('operations', oid, {**operation, 'status': 'COMPLETED', 'effect_state': 'VERIFIED', 'completed_at': now()})
            self.store.put('restore_receipts', oid, receipt)
            self.store.event('checkpoint_restored', result)
        return {**result, 'reused': False}

    def restore(self, checkpoint_id, destination):
        with self.store.guard():
            checkpoint = self.store.get('checkpoints', checkpoint_id)
            if checkpoint is None:
                raise GovernanceError('CHECKPOINT_NOT_FOUND', 'The checkpoint does not exist.')
            raw = Path(destination).expanduser().absolute()
            for ancestor in (raw, *raw.parents):
                if _linked(ancestor):
                    raise GovernanceError('SYMLINK_PATH', 'Restore destination cannot traverse symbolic links or junctions.')
            destination = raw.resolve()
            source = Path(checkpoint['workspace']).resolve()
            if destination == self.root or destination.is_relative_to(self.root) or self.root.is_relative_to(destination) or destination == source or destination.is_relative_to(source) or source.is_relative_to(destination):
                raise GovernanceError('RESTORE_NOT_INDEPENDENT', 'Restore into an independent directory outside source and governance workspaces.')
            checkpoint_hash = self._restore_digest(checkpoint)
            oid = 'restore-' + self._restore_digest([checkpoint_id, os.path.normcase(str(destination))])[:24]
            operation = self.store.get('operations', oid)
            if operation is not None:
                if any(type(operation.get(key)) is not int or operation[key] != 1
                       for key in ('operation_protocol', 'restore_protocol')):
                    raise GovernanceError('OPERATION_PROTOCOL_UNSUPPORTED', 'Use a compatible toolkit for this restore operation.')
                if (operation.get('kind') != 'restore' or operation.get('checkpoint_sha256') != checkpoint_hash
                        or operation.get('checkpoint_id') != checkpoint_id or operation.get('destination') != str(destination)):
                    raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'The restore intent no longer matches its input.', {'operation_id': oid})
                if operation.get('status') in ('EFFECT_APPLIED', 'COMPLETED'):
                    return self._restore_finalize(checkpoint, destination, operation)
                if operation.get('status') != 'PREPARED' or operation.get('effect_state') != 'NOT_APPLIED':
                    raise GovernanceError('RESTORE_REVIEW_REQUIRED',
                                          'An interrupted restore has uncertain or partial effects; inspect the retained destination. No effects replayed.',
                                          {'operation_id': oid, 'destination': str(destination), 'status': operation.get('status')})
            if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
                raise GovernanceError('RESTORE_NOT_EMPTY', 'Restore destination must be absent or empty.')
            # Validate every object before creating or writing the destination.
            contents = {}
            if (not isinstance(checkpoint.get('files'), list) or not 1 <= len(checkpoint['files']) <= MAX_PATHS
                    or type(checkpoint.get('git')) is not bool):
                raise GovernanceError('CHECKPOINT_CORRUPT', 'Restore requires a bounded checkpoint file manifest.')
            paths, total = set(), 0
            for record in checkpoint['files']:
                validate_relative_path(destination, record['path'])
                if record['path'].casefold() in paths:
                    raise GovernanceError('CHECKPOINT_CORRUPT', 'Checkpoint file paths must be unique.')
                paths.add(record['path'].casefold())
                for layer in ('head', 'index', 'worktree'):
                    if record[layer]:
                        if record[layer].get('mode') not in ('100644', '100755'):
                            raise GovernanceError('CHECKPOINT_CORRUPT', 'Checkpoint layers must be regular files.')
                        contents[(record['path'], layer)] = self._snapshot_bytes(record[layer])
                        total += len(contents[(record['path'], layer)])
                        if total > MAX_CHECKPOINT_BYTES:
                            raise GovernanceError('CHECKPOINT_TOO_LARGE', 'The restore exceeds the checkpoint byte limit.')
            if operation is None:
                operation = {'operation_id': oid, 'kind': 'restore', 'operation_protocol': 1, 'restore_protocol': 1,
                             'task_id': checkpoint['task_id'], 'checkpoint_id': checkpoint_id,
                             'checkpoint_sha256': checkpoint_hash, 'destination': str(destination),
                             'status': 'PREPARED', 'effect_state': 'NOT_APPLIED', 'created_at': now()}
                self.store.put('operations', oid, operation)
            operation = {**operation, 'status': 'APPLYING', 'effect_state': 'UNKNOWN'}
            self.store.put('operations', oid, operation)
            destination.mkdir(parents=True, exist_ok=True)
            operation['destination_identity'] = self._restore_directory_identity(destination)
            self.store.put('operations', oid, operation)
            if any(destination.iterdir()):
                raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'Work appeared at the restore destination; it was preserved.', {'operation_id': oid})
            if checkpoint['git']:
                git(destination, 'init', '--quiet')
                git(destination, 'config', 'user.name', 'TaskCarry synthetic restore')
                git(destination, 'config', 'user.email', 'restore@example.invalid')
                for record in checkpoint['files']:
                    if record['head']:
                        data = contents[(record['path'], 'head')]
                        blob_oid = git(destination, 'hash-object', '-w', '--stdin', input_bytes=data).stdout.decode().strip()
                        git(destination, 'update-index', '--add', '--cacheinfo', record['head']['mode'], blob_oid, record['path'])
                git(destination, 'commit', '--allow-empty', '--quiet', '-m',
                    'TaskCarry synthetic restore baseline; original HEAD: ' + str(checkpoint['original_head']))
                for record in checkpoint['files']:
                    if record['index']:
                        blob_oid = git(destination, 'hash-object', '-w', '--stdin', input_bytes=contents[(record['path'], 'index')]).stdout.decode().strip()
                        git(destination, 'update-index', '--add', '--cacheinfo', record['index']['mode'], blob_oid, record['path'])
                    else:
                        git(destination, 'update-index', '--force-remove', '--', record['path'])
            for record in checkpoint['files']:
                if record['worktree']:
                    if self._restore_directory_identity(destination) != operation['destination_identity']:
                        raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'The restore destination was replaced.')
                    target = validate_relative_path(destination, record['path'])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open('xb') as stream:
                        stream.write(contents[(record['path'], 'worktree')])
                        stream.flush()
                        os.fsync(stream.fileno())
                    if os.name != 'nt':
                        target.chmod(0o755 if record['worktree']['mode'] == '100755' else 0o644)
            fingerprint = self._restore_effect(checkpoint, destination)
            if fingerprint['directory_identity'] != operation['destination_identity']:
                raise GovernanceError('RESTORE_REVIEW_REQUIRED', 'The restore destination was replaced.')
            operation.update(status='EFFECT_APPLIED', effect_state='VERIFIED', effect_fingerprint=fingerprint,
                             effect_sha256=self._restore_digest(fingerprint))
            self.store.put('operations', oid, operation)
            return self._restore_finalize(checkpoint, destination, operation)

    def artifact(self, task_id, path, role='input', backup=None, decision=None):
        if decision not in (None, 'ignore', 'dismiss', 'no_backup_needed', 'retain'):
            raise GovernanceError('INVALID_DECISION', 'Artifact decision must be ignore, dismiss, no_backup_needed or retain.')
        self._task(task_id)
        raw = Path(path).expanduser().absolute()
        if any(part.casefold() in ('.git', '.taskcarry') for part in raw.parts):
            raise GovernanceError('RESERVED_PATH', 'Git and governance metadata cannot become artifacts.')
        # Artifact reads are explicitly named, but metadata/secret/link exclusions still apply.
        for ancestor in (raw, *raw.parents):
            if _linked(ancestor):
                raise GovernanceError('SYMLINK_PATH', 'Artifact paths cannot traverse symbolic links or junctions.')
        validate_relative_path(raw.parent, raw.name, allow_missing=False)
        digest = hashlib.sha256()
        before = raw.stat()
        with raw.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        after = raw.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise GovernanceError('SOURCE_CHANGED', 'The artifact changed during hashing.')
        checksum = digest.hexdigest()
        artifact_id = 'ar-' + digest_bytes((task_id + '\x00' + str(raw.resolve())).encode())[:32]
        old = self.store.get('artifacts', artifact_id)
        if backup is None and old and old['sha256'] == checksum:
            backup = old.get('backup')
        verified = False
        backup_path = None
        if backup is not None:
            backup_path = Path(backup).expanduser().absolute()
            if backup_path.resolve() == raw.resolve() or backup_path.exists() and os.path.samefile(backup_path, raw):
                raise GovernanceError('BACKUP_NOT_INDEPENDENT', 'The original file is not an independent backup.')
            for ancestor in (backup_path, *backup_path.parents):
                if _linked(ancestor):
                    raise GovernanceError('SYMLINK_PATH', 'Backup paths cannot traverse symbolic links or junctions.')
            validate_relative_path(backup_path.parent, backup_path.name, allow_missing=True)
            if backup_path.is_file():
                backup_stat = backup_path.stat()
                backup_digest = hashlib.sha256()
                with backup_path.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        backup_digest.update(block)
                backup_after = backup_path.stat()
                verified = (backup_digest.hexdigest() == checksum and backup_stat.st_size == before.st_size
                            and (backup_stat.st_size, backup_stat.st_mtime_ns) == (backup_after.st_size, backup_after.st_mtime_ns))
        with self.store.transaction():
            old = self.store.get('artifacts', artifact_id)
            same = old and old['sha256'] == checksum
            result = {'artifact_id': artifact_id, 'task_id': task_id, 'path': str(raw.resolve()), 'role': role,
                      'sha256': checksum, 'size': before.st_size, 'decision': decision if decision is not None else old.get('decision') if same else None,
                      'backup': str(backup_path) if backup_path else None, 'backup_verified': verified,
                      'backup_available': bool(backup_path and backup_path.is_file()),
                      'updated_at': now(), 'content_changed': bool(old and not same)}
            self.store.put('artifacts', artifact_id, result)
            self.store.event('artifact_observed', result)
            return result

    def experience(self, rule_id, code, operation, action, task_id=None, version='1', enabled=True):
        rule_id = _id(rule_id, 'Rule ID')
        if action not in ('verify_and_finalize', 'refresh_plan'):
            raise GovernanceError('UNSUPPORTED_EXPERIENCE_ACTION', 'Experience may only select a defined recovery action, never arbitrary code.')
        if task_id:
            self._task(task_id)
        if not isinstance(enabled, bool):
            raise GovernanceError('INVALID_EXPERIENCE', 'Experience enabled must be a boolean.')
        result = {'rule_id': rule_id, 'code': code, 'operation': operation, 'action': action,
                  'task_id': task_id, 'version': str(version), 'enabled': enabled, 'updated_at': now()}
        with self.store.transaction():
            self.store.put('experience', rule_id, result)
            self.store.event('experience_registered', result)
        return result

    def match_experience(self, code, operation, task_id=None):
        matches = self._experience_matches(self.store.list('experience'), code, operation, task_id)
        return {'matches': matches, 'code': code, 'operation': operation, 'task_id': task_id,
                'execution': 'A match is a candidate action; the executor must verify current evidence before applying it.'}

    @staticmethod
    def _experience_matches(rules, code, operation, task_id):
        return [r for r in rules if r['enabled'] and r['version'] == '1'
                   and r['code'] == code and r['operation'] == operation and r['task_id'] in (None, task_id)]
