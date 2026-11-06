"""Planned exact local Git preservation, with a recoverable ref/index journal.

No remote transport, implicit repository creation, staging sweep or author
fabrication. Selected staged changes require a separate user-reviewed workflow.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

from .core import Core, _id, _linked, digest_bytes, read_file_bytes, validate_relative_path
from .gitops import repo, identity, pathsafe
from .store import GovernanceError, now
from .path_batches import path_batches


def _git(root, *args, data=None, index=None, author=None, check=True):
    environment = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    environment.update(GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    if index:
        environment['GIT_INDEX_FILE'] = str(index)
    if author:
        environment.update(GIT_AUTHOR_NAME=author['name'], GIT_AUTHOR_EMAIL=author['email'],
                           GIT_COMMITTER_NAME=author['name'], GIT_COMMITTER_EMAIL=author['email'])
    try:
        result = subprocess.run(['git', '--literal-pathspecs', '-c', 'core.hooksPath=' + os.devnull,
                                 '-c', 'commit.gpgsign=false', '-c', 'core.autocrlf=false',
                                 '-C', str(root), *map(str, args)], input=data, env=environment,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, shell=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GovernanceError('GIT_UNAVAILABLE', str(error)) from error
    if check and result.returncode:
        raise GovernanceError('PRESERVE_GIT_FAILED', result.stderr.decode('utf-8', 'replace'), {'args': args})
    return result


def _head(root):
    result = _git(root, 'rev-parse', '--verify', 'HEAD', check=False)
    return result.stdout.decode().strip() if result.returncode == 0 else None


def _index(root):
    path = Path(_git(root, 'rev-parse', '--path-format=absolute', '--git-path', 'index').stdout.decode().strip())
    if _linked(path) or _linked(path.parent):
        raise GovernanceError('UNSAFE_METADATA', 'The Git index cannot traverse a link.')
    return path


def _bytes(path):
    return read_file_bytes(path) if path.exists() else None


def _hash(data):
    return digest_bytes(data) if data is not None else None


def _fingerprint(value):
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


class Preservation(Core):
    def _author(self, root):
        result = {}
        for field in ('name', 'email'):
            value = _git(root, 'config', '--get', 'user.' + field, check=False).stdout.decode('utf-8').strip()
            if not value or len(value) > 512 or any(c in value for c in '\n\r\0<>'):
                raise GovernanceError('GIT_AUTHOR_REQUIRED', 'Set a verified repository-local Git author before saving.', {'field': field})
            result[field] = value
        return result

    def _capture(self, root, paths):
        files, total = [], 0
        for path in paths:
            pathsafe(path)
            source = validate_relative_path(root, path)
            if any(p.casefold() in ('runtime', 'toolkit', 'downloads', '.venv', 'node_modules', '__pycache__')
                   for p in Path(path).parts):
                raise GovernanceError('PRESERVE_EXCLUDED', 'Runtime/download/dependency trees are not governance records.')
            if _git(root, 'check-ignore', '-q', '--', path, check=False).returncode == 0:
                raise GovernanceError('PRESERVE_IGNORED', 'An ignored path requires a separate reviewed workflow.', {'path': path})
            data = read_file_bytes(source) if source.exists() else None
            if data is None and not _git(root, 'ls-files', '--error-unmatch', '--', path, check=False).returncode == 0:
                raise GovernanceError('MISSING_FILE', 'The selected file has no content or tracked deletion.', {'path': path})
            total += len(data) if data is not None else 0
            if total > 128 * 1024 * 1024:
                raise GovernanceError('PRESERVE_TOO_LARGE', 'Split the selection or use external artifact references.')
            files.append({'path': path, 'sha256': _hash(data), 'size': len(data) if data is not None else 0,
                          'mode': ('100755' if source.exists() and source.stat().st_mode & stat.S_IXUSR else '100644')})
        return files

    def _selection_clean(self, root, head, paths):
        # A saved stage has distinct intent from unstaged working content. Do not
        # silently consume it, even if only the same selected path is involved.
        for selected in path_batches(paths):
            if head:
                different = _git(root, 'diff', '--cached', '--quiet', head, '--', *selected, check=False)
                if different.returncode == 1:
                    raise GovernanceError('PRESERVE_SELECTED_STAGED', 'Preserve or explicitly deliver selected staged work separately.')
                if different.returncode:
                    raise GovernanceError('PRESERVE_GIT_FAILED', different.stderr.decode('utf-8', 'replace'))
            elif _git(root, 'ls-files', '--stage', '-z', '--', *selected).stdout:
                raise GovernanceError('PRESERVE_SELECTED_STAGED', 'Selected files are already staged.')
            for line in _git(root, 'ls-files', '-v', '-z', '--', *selected).stdout.split(b'\0'):
                if line and not line.startswith(b'H '):
                    raise GovernanceError('PRESERVE_INDEX_FLAGS', 'Selected skip-worktree/assume-unchanged paths need review.')

    def preserve(self, action='plan', repository=None, paths=None, message=None, plan_id=None):
        if action not in ('plan', 'execute', 'status'):
            raise GovernanceError('PRESERVE_ACTION', 'Use plan, execute or status.')
        if action in ('execute', 'status'):
            if any(value is not None for value in (repository, paths, message)):
                raise GovernanceError('PRESERVE_ARGUMENT', 'Use the exact saved plan without new repository, paths or message.')
            plan_id = _id(plan_id, 'Preservation plan')
            record = self.store.get('preservation', plan_id)
            if not record:
                raise GovernanceError('PRESERVE_UNKNOWN', 'Create a preservation plan first.')
            if action == 'status':
                return {**record, 'effects_verified_now': False,
                        'meaning': 'Durable local save receipt; not remote backup, business acceptance or current HEAD verification.'}
            return self._execute(record)
        if plan_id is not None:
            raise GovernanceError('PRESERVE_ARGUMENT', 'A new plan does not accept an existing plan ID.')
        if (not isinstance(paths, list) or not 1 <= len(paths) <= 500
                or any(not isinstance(p, str) for p in paths)
                or len({p.casefold() for p in paths}) != len(paths)):
            raise GovernanceError('EXACT_PATHS_REQUIRED', 'Select 1-500 unique explicit relative files.')
        if not isinstance(message, str) or not message.strip() or len(message) > 2048 or '\0' in message:
            raise GovernanceError('PRESERVE_MESSAGE', 'Provide a bounded commit message.')
        if not isinstance(repository, str) or not repository.strip():
            raise GovernanceError('PRESERVE_REPOSITORY', 'Select an existing repository root.')
        root = repo(repository)
        files = self._capture(root, sorted(paths))
        head, index_bytes = _head(root), _bytes(_index(root))
        self._selection_clean(root, head, paths)
        body = {'repository': str(root), 'identity': identity(root), 'head': head, 'files': files,
                'index_sha256': _hash(index_bytes), 'author': self._author(root), 'message': message}
        pid = 'save-' + _fingerprint(body)[:24]
        with self.store.transaction():
            old = self.store.get('preservation', pid)
            if old:
                return {**old, 'reused': True}
            record = {**body, 'plan_id': pid, 'state': 'PLANNED', 'created_at': now(),
                      'scope': 'selected_local_files', 'remote_backup': False, 'delivery': False}
            self.store.put('preservation', pid, record)
            self.store.event('preservation_planned', {'plan_id': pid, 'paths': paths})
        return record

    def _prepare(self, record, root, before):
        # Git plumbing uses a private index, raw bytes and no hooks/filters. The
        # actual staged file bytes and attributes are never silently normalized.
        scratch = self.store.directory / 'preservation-scratch'
        scratch.mkdir(exist_ok=True)
        if _linked(scratch):
            raise GovernanceError('UNSAFE_METADATA', 'Scratch storage cannot be a link.')
        with tempfile.TemporaryDirectory(prefix='save-', dir=scratch) as temporary:
            candidate_index = Path(temporary) / 'candidate-index'
            _git(root, 'read-tree', record['head'] or '--empty', index=candidate_index)
            entries = []
            oid_length = len(_git(root, 'hash-object', '--stdin', data=b'').stdout.strip())
            for item in record['files']:
                path = item['path']
                if item['sha256'] is None:
                    entries.append('0 ' + '0' * oid_length + '\t' + path + '\0')
                    continue
                data = read_file_bytes(validate_relative_path(root, path, allow_missing=False))
                if digest_bytes(data) != item['sha256']:
                    raise GovernanceError('PRESERVE_CHANGED', 'Selected content changed after planning.')
                oid = _git(root, 'hash-object', '-w', '--stdin', data=data).stdout.decode().strip()
                entries.append(item['mode'] + ' ' + oid + '\t' + path + '\0')
            payload = ''.join(entries).encode('utf-8')
            _git(root, 'update-index', '-z', '--index-info', data=payload, index=candidate_index)
            tree = _git(root, 'write-tree', index=candidate_index).stdout.decode().strip()
            prior_tree = (_git(root, 'rev-parse', record['head'] + '^{tree}').stdout.decode().strip()
                          if record['head'] else None)
            if tree == prior_tree:
                return {**record, 'state': 'COMPLETED', 'commit': record['head'], 'changed': False,
                        'completed_at': now()}
            args = ['commit-tree', tree]
            if record['head']:
                args += ['-p', record['head']]
            candidate = _git(root, *args, data=(record['message'] + '\n').encode(), author=record['author']).stdout.decode().strip()
            after_index = Path(temporary) / 'after-index'
            if before is None:
                _git(root, 'read-tree', '--empty', index=after_index)
            else:
                after_index.write_bytes(before)
            _git(root, 'update-index', '-z', '--index-info', data=payload, index=after_index)
            return {**record, 'state': 'PREPARED', 'candidate': candidate, 'tree': tree,
                    'index_before': self._snapshot(before) if before is not None else None,
                    'index_after': self._snapshot(read_file_bytes(after_index)), 'changed': True,
                    'content_policy': 'exact_raw_bytes_without_clean_filters'}

    def _publish(self, record):
        with self.store.transaction():
            self.store.put('preservation', record['plan_id'], record)
            self.store.event('preservation_completed', {'plan_id': record['plan_id'],
                                                       'commit': record['commit'], 'changed': record['changed']})
        return record

    def _execute(self, original):
        with self.store.guard():
            record = self.store.get('preservation', original['plan_id'])
            if record['state'] == 'COMPLETED':
                return {**record, 'reused': True}
            root = repo(record['repository'])
            if identity(root) != record['identity']:
                raise GovernanceError('PRESERVE_CHANGED', 'The repository identity changed; inspect actual effects.')
            index = _index(root)
            lock = Path(str(index) + '.lock')
            if _linked(lock):
                raise GovernanceError('UNSAFE_METADATA', 'The index lock cannot be a link.')
            try:
                handle = lock.open('xb')
            except FileExistsError as error:
                raise GovernanceError('PRESERVE_BUSY', 'Git index is locked; do not delete another operation lock.') from error
            try:
                before, current = _bytes(index), _head(root)
                if record['state'] == 'PLANNED':
                    if current != record['head'] or _hash(before) != record['index_sha256']:
                        raise GovernanceError('PRESERVE_CHANGED', 'HEAD or index changed; prepare a fresh plan.')
                    if self._author(root) != record['author'] or self._capture(root, [f['path'] for f in record['files']]) != record['files']:
                        raise GovernanceError('PRESERVE_CHANGED', 'Author or selected files changed; prepare a fresh plan.')
                    record = self._prepare(record, root, before)
                    if record['state'] == 'COMPLETED':
                        return self._publish(record)
                    # This journal is durable before the first visible Git effect.
                    self.store.put('preservation', record['plan_id'], record)
                original_index = self._snapshot_bytes(record['index_before']) if record['index_before'] else None
                final_index = self._snapshot_bytes(record['index_after'])
                if before not in (original_index, final_index):
                    raise GovernanceError('PRESERVE_REVIEW_REQUIRED', 'The index differs from both recorded states; preserve it and review.')
                candidate = record['candidate']
                if current == record['head']:
                    if before != original_index or self._capture(root, [f['path'] for f in record['files']]) != record['files']:
                        raise GovernanceError('PRESERVE_CHANGED', 'Source changed before commit; do not replay the plan.')
                    expected = record['head'] or ('0' * len(candidate))
                    _git(root, 'update-ref', record['identity']['branch'], candidate, expected)
                elif current != candidate:
                    raise GovernanceError('PRESERVE_REVIEW_REQUIRED', 'HEAD is neither the old nor prepared commit; no automatic replay.')
                # Only selected entries differ. Unrelated staged entries, file
                # bytes and all unstaged work remain exactly as before.
                handle.write(final_index)
                handle.flush()
                os.fsync(handle.fileno())
                handle.close()
                os.replace(lock, index)
                if _head(root) != candidate or _bytes(index) != final_index:
                    raise GovernanceError('PRESERVE_REVIEW_REQUIRED', 'Effects changed before receipt finalization.')
                return self._publish({**record, 'state': 'COMPLETED', 'commit': candidate, 'completed_at': now()})
            finally:
                handle.close()
                if lock.exists():
                    lock.unlink()
