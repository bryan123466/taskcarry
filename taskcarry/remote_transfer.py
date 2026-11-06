"""Planned single-ref Git exchange and verified local recovery-media copying.

Remote repositories and authentication must already be configured by the user.
Copy receipts describe local bytes only: they never claim a cloud provider has
uploaded, retained or downloaded them. A transfer is not governance adoption.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
import uuid

from .core import Core, _id, digest_bytes, read_file_bytes
from .store import GovernanceError, now
from .recovery_files import atomic, disjoint, lock, normal, safe, MAX_BYTES


PLAN_SCHEMA = 'taskcarry.transfer-plan.v1'
RECEIPT_SCHEMA = 'taskcarry.transfer-receipt.v1'


def _hash(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return digest_bytes(value)


def _git(root, *args, check=True):
    environment = {name: value for name, value in os.environ.items() if not name.startswith('GIT_')}
    environment.update(GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    try:
        result = subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull,
                                 '-c', 'push.followTags=false', '-c', 'push.recurseSubmodules=no',
                                 '-C', str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=environment, timeout=120, shell=False,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GovernanceError('TRANSFER_TRANSPORT_UNKNOWN', 'The Git command did not provide a reliable completion result.',
                              {'exception': type(exc).__name__}) from exc
    if check and result.returncode:
        raise GovernanceError('TRANSFER_GIT_FAILED', 'Git transport or repository inspection failed.',
                              {'command': args[0], 'returncode': result.returncode,
                               'stderr': result.stderr.decode('utf-8', 'replace')[:2000]})
    return result


def _out(root, *args):
    return _git(root, *args).stdout.decode('utf-8', 'strict').strip()


def _repository(value):
    if not isinstance(value, str) or not value.strip():
        raise GovernanceError('TRANSFER_ARGUMENT', 'Select an existing exact Git worktree root.')
    root = normal(value)
    if normal(_out(root, 'rev-parse', '--show-toplevel')) != root:
        raise GovernanceError('TRANSFER_REPOSITORY', 'Select the exact Git worktree root.')
    return root


def _identity(root):
    return {'path': str(root), 'git_dir': str(normal(_out(root, 'rev-parse', '--path-format=absolute', '--git-dir'))),
            'common_dir': str(normal(_out(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')))}


def _snapshot(root):
    index = normal(_out(root, 'rev-parse', '--path-format=absolute', '--git-path', 'index'))
    raw_index = read_file_bytes(index) if index.exists() else None
    status = _git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all').stdout
    # Untracked bytes are never transported by Git push. Preserve their local
    # size/mtime identity without reading credentials or other unrelated bodies.
    untracked = {}
    for value in _git(root, 'ls-files', '--others', '--exclude-standard', '-z').stdout.split(b'\0'):
        if value:
            relative = value.decode('utf-8', 'strict')
            path = root / relative
            info = path.lstat()
            untracked[relative] = [info.st_size, info.st_mtime_ns, info.st_mode]
    return {'head': _out(root, 'rev-parse', '--verify', 'HEAD'),
            'branch': _git(root, 'symbolic-ref', '--quiet', 'HEAD', check=False).stdout.decode('utf-8').strip() or None,
            'index_sha256': _hash(raw_index) if raw_index is not None else None,
            'status_sha256': _hash(status), 'untracked_metadata': untracked,
            'work_diff_sha256': _hash(_git(root, 'diff', '--binary', '--no-ext-diff', '--no-textconv', '--').stdout)}


def _remote_url(root, name):
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', name):
        raise GovernanceError('TRANSFER_REMOTE', 'Select one already-configured remote name.')
    urls = _out(root, 'remote', 'get-url', '--push', '--all', name).splitlines()
    if len(urls) != 1:
        raise GovernanceError('TRANSFER_REMOTE', 'A transfer must target exactly one configured push URL.')
    url = urls[0]
    if not url or url.startswith('-') or any(character in url for character in '\0\r\n') or '::' in url:
        raise GovernanceError('TRANSFER_REMOTE', 'This remote transport syntax is not supported.')
    parsed = urlsplit(url)
    if parsed.password is not None or parsed.query or parsed.fragment or (parsed.scheme in ('http', 'https') and parsed.username is not None):
        raise GovernanceError('TRANSFER_REMOTE_CREDENTIALS', 'Use the host credential mechanism instead of credentials or tokens embedded in a remote URL.')
    if '://' in url and parsed.scheme not in ('http', 'https', 'ssh', 'git', 'file'):
        raise GovernanceError('TRANSFER_REMOTE', 'Use an existing Git SSH, HTTPS or local file remote.')
    # Resolve local paths now; a later cwd must not redirect the target.
    if '://' not in url and (':' not in url or re.match(r'^[A-Za-z]:[\\/]', url)):
        local = Path(url)
        url = str(normal(local if local.is_absolute() else root / local))
    return url


def _remote_ref(root, url, ref):
    output = _out(root, 'ls-remote', '--refs', url, ref)
    rows = [line.split('\t', 1) for line in output.splitlines() if line]
    if not rows:
        return None
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != ref or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', rows[0][0]):
        raise GovernanceError('TRANSFER_REMOTE_RESPONSE', 'The remote did not return one exact requested ref.')
    return rows[0][0]


class RemoteTransfer(Core):
    def transfer(self, action, repository=None, remote=None, ref=None, commit=None,
                 plan_id=None, manifest=None, destination=None, expected_sha256=None):
        """Plan/execute one Git ref or a sealed recovery set; verify real effects."""
        if action == 'publish_plan':
            if any(value is not None for value in (plan_id, manifest, destination, expected_sha256)):
                raise GovernanceError('TRANSFER_ARGUMENT', 'A Git publication plan accepts repository, remote, ref and commit only.')
            return self._publish_plan(repository, remote, ref, commit)
        if action == 'copy_plan':
            if any(value is not None for value in (repository, remote, ref, commit, plan_id)):
                raise GovernanceError('TRANSFER_ARGUMENT', 'A recovery copy plan accepts manifest, destination and expected_sha256 only.')
            return self._copy_plan(manifest, destination, expected_sha256)
        if any(value is not None for value in (repository, remote, ref, commit, manifest, destination, expected_sha256)):
            raise GovernanceError('TRANSFER_ARGUMENT', 'Use the exact frozen plan without replacement targets or inputs.')
        plan = self._plan(plan_id)
        if action == 'status':
            return {'plan': plan, 'receipt': self._receipt(plan_id), 'effects_verified_now': False}
        if action == 'verify':
            return self._verify(plan)
        if action not in ('publish_execute', 'copy_execute') or plan['kind'] != action.split('_')[0]:
            raise GovernanceError('TRANSFER_ACTION', 'Choose the execution action matching this plan.')
        self.store.assert_writable()
        config = self.store.get('config', 'project') or {}
        if plan['plan_id'] in config.get('recovery_inert_plan_ids', []):
            raise GovernanceError('RESTORED_PLAN_INERT', 'Historical transfer plans require a new local plan after recovery.')
        resource = plan['repository'] + '\0' + plan['url'] + '\0' + plan['ref'] if plan['kind'] == 'publish' else os.path.normcase(plan['destination'])
        with lock(self.store.directory / ('transfer-' + _hash(resource) + '.lock')):
            return self._publish_execute(plan) if plan['kind'] == 'publish' else self._copy_execute(plan)

    def _plan(self, plan_id):
        plan_id = _id(plan_id, 'Transfer plan ID')
        plan = self.store.get('transfer_plans', plan_id)
        if plan is None:
            raise GovernanceError('TRANSFER_PLAN_NOT_FOUND', 'Create and review a transfer plan first.')
        if plan.get('schema') != PLAN_SCHEMA or plan.get('plan_id') != plan_id:
            raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'Use a compatible transfer plan reader.')
        fingerprint = _hash({key: value for key, value in plan.items() if key != 'fingerprint'})
        if plan.get('fingerprint') != fingerprint:
            raise GovernanceError('TRANSFER_PLAN_CHANGED', 'The stored transfer plan differs from its frozen content.')
        return plan

    def _receipt(self, plan_id):
        receipt = self.store.get('transfer_receipts', plan_id)
        if receipt is not None and receipt.get('schema') != RECEIPT_SCHEMA:
            raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'Use a compatible transfer receipt reader.')
        return receipt

    def _save_plan(self, kind, body):
        plan_id = 'transfer-' + uuid.uuid4().hex
        plan = {'schema': PLAN_SCHEMA, 'plan_id': plan_id, 'kind': kind, 'created_at': now(), **body}
        plan['fingerprint'] = _hash(plan)
        with self.store.transaction():
            self.store.put('transfer_plans', plan_id, plan)
            self.store.event('transfer_planned', {'plan_id': plan_id, 'kind': kind, 'fingerprint': plan['fingerprint']})
        return {'plan': plan, 'execute_required': True, 'effects_applied': False}

    def _publish_plan(self, repository, remote, ref, selected):
        self.store.assert_writable()
        root = _repository(repository)
        if (not isinstance(ref, str) or not ref.startswith(('refs/heads/', 'refs/tags/'))
                or _git(root, 'check-ref-format', ref, check=False).returncode):
            raise GovernanceError('TRANSFER_REF', 'Select one exact refs/heads/... or refs/tags/... destination.')
        if not isinstance(selected, str) or not selected or selected.startswith('-') or len(selected) > 256:
            raise GovernanceError('TRANSFER_COMMIT', 'Select one exact existing commit or local revision.')
        before = _snapshot(root)
        selected_oid = _out(root, 'rev-parse', '--verify', '--end-of-options', selected + '^{commit}')
        url = _remote_url(root, remote)
        old = _remote_ref(root, url, ref)
        if old and old != selected_oid:
            if ref.startswith('refs/tags/'):
                raise GovernanceError('TRANSFER_TAG_CONFLICT', 'Existing tags are immutable; select a new tag or retain the conflict.')
            ancestry = _git(root, 'merge-base', '--is-ancestor', old, selected_oid, check=False)
            if ancestry.returncode:
                raise GovernanceError('TRANSFER_NOT_FAST_FORWARD', 'The destination history is not a verified ancestor of this commit; inspect or import it before planning.')
        if _snapshot(root) != before:
            raise GovernanceError('TRANSFER_SOURCE_CHANGED', 'Repository state changed while the publication plan was read.')
        return self._save_plan('publish', {'repository': str(root), 'repository_identity': _identity(root),
                               'remote': remote, 'url': url, 'ref': ref, 'commit': selected_oid,
                               'expected_old_ref': old, 'worktree': before,
                               'meaning': 'One exact commit/ref and its reachable history; uncommitted files are not uploaded. Public or private content review remains a host responsibility.'})

    def _publish_observe(self, plan):
        root = _repository(plan['repository'])
        if _identity(root) != plan['repository_identity'] or _remote_url(root, plan['remote']) != plan['url']:
            raise GovernanceError('TRANSFER_TARGET_CHANGED', 'Repository identity or configured remote URL changed after the plan.')
        actual = _remote_ref(root, plan['url'], plan['ref'])
        return {'verified': actual == plan['commit'], 'actual_ref': actual, 'expected_ref': plan['commit'],
                'ref': plan['ref'], 'kind': 'git_ref', 'offsite_recovery_verified': False,
                'meaning': 'The selected ref was read from its configured Git endpoint; full project recovery and cloud retention are separate evidence.'}

    def _publish_execute(self, plan):
        prior = self._receipt(plan['plan_id'])
        root = _repository(plan['repository'])
        before = _snapshot(root)
        observed = self._publish_observe(plan)
        if observed['verified']:
            if _snapshot(root) != before:
                raise GovernanceError('TRANSFER_WORKTREE_CHANGED', 'Concurrent local changes were observed while verifying the existing effect.', observed)
            return self._finish(plan, observed, prior, effect_reused=True, worktree_unchanged=True)
        if prior:
            raise GovernanceError('TRANSFER_EFFECT_CHANGED', 'The remote no longer matches the retained completed receipt.', observed)
        if observed['actual_ref'] != plan['expected_old_ref']:
            raise GovernanceError('TRANSFER_REMOTE_CHANGED', 'The destination ref changed after planning; preserve it and prepare a new plan.', observed)
        if before != plan['worktree']:
            raise GovernanceError('TRANSFER_SOURCE_CHANGED', 'Local HEAD, index or working state changed after planning; prepare a new plan.')
        # An immutable operation journal precedes the external effect. A crashed
        # call may therefore be resumed by checking the actual remote first.
        self._started(plan)
        transport = None
        try:
            result = _git(root, 'push', '--porcelain', '--no-follow-tags', '--recurse-submodules=no',
                          '--force-with-lease=' + plan['ref'] + ':' + (plan['expected_old_ref'] or ''),
                          plan['url'], plan['commit'] + ':' + plan['ref'], check=False)
            if result.returncode:
                transport = {'returncode': result.returncode, 'stderr': result.stderr.decode('utf-8', 'replace')[:2000]}
        except GovernanceError as exc:
            transport = {'code': exc.code, 'details': exc.details}
        try:
            observed = self._publish_observe(plan)
        except GovernanceError as exc:
            raise GovernanceError('TRANSFER_EFFECT_UNKNOWN', 'Transmission ended without a verifiable remote result; retry this exact plan to inspect its actual effect first.',
                                  {'plan_id': plan['plan_id'], 'transport': transport, 'verification_code': exc.code}) from exc
        unchanged = _snapshot(root) == before
        if not unchanged:
            raise GovernanceError('TRANSFER_WORKTREE_CHANGED', 'Concurrent local changes were observed; no reset was attempted.',
                                  {'remote_effect': observed, 'transport': transport})
        if not observed['verified']:
            raise GovernanceError('TRANSFER_NOT_APPLIED', 'The exact ref has not been verified at its destination; retain this plan and inspect the evidence.',
                                  {'remote_effect': observed, 'transport': transport})
        return self._finish(plan, observed, prior, effect_reused=False, worktree_unchanged=True,
                            transport_warning=transport)

    def _started(self, plan):
        with self.store.transaction():
            previous = self.store.get('transfer_attempts', plan['plan_id'])
            if previous and previous.get('schema') != 'taskcarry.transfer-attempt.v1':
                raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'Use a compatible transfer attempt reader.')
            value = previous or {'schema': 'taskcarry.transfer-attempt.v1', 'plan_id': plan['plan_id'],
                                 'fingerprint': plan['fingerprint'], 'started_at': now(), 'state': 'effect_may_exist'}
            if previous is None:
                self.store.put('transfer_attempts', plan['plan_id'], value)
                self.store.event('transfer_started', {'plan_id': plan['plan_id'], 'kind': plan['kind']})

    def _finish(self, plan, observed, prior, **details):
        if prior:
            return {'receipt': prior, 'reused': True, 'observed_effect': observed}
        receipt = {'schema': RECEIPT_SCHEMA, 'plan_id': plan['plan_id'], 'kind': plan['kind'],
                   'fingerprint': plan['fingerprint'], 'state': 'VERIFIED', 'verified_at': now(),
                   'observed_effect': observed, **details}
        with self.store.transaction():
            self.store.put('transfer_receipts', plan['plan_id'], receipt)
            self.store.event('transfer_verified', {'plan_id': plan['plan_id'], 'kind': plan['kind'],
                                                 'fingerprint': plan['fingerprint']})
        return {'receipt': receipt, 'reused': False, 'observed_effect': observed}

    def _copy_plan(self, manifest, destination, expected):
        from .project_recovery import ProjectRecovery, _manifest, _payload_refs
        self.store.assert_writable()
        if not isinstance(manifest, str) or not isinstance(destination, str):
            raise GovernanceError('TRANSFER_ARGUMENT', 'Select the exact recovery manifest and an independent local destination.')
        source = normal(manifest)
        target = normal(destination)
        disjoint(source.parent, target)
        disjoint(self.root, target)
        verified = ProjectRecovery._verify(str(source), expected)
        if not verified['verified']:
            raise GovernanceError('TRANSFER_SOURCE_INCOMPLETE', 'Verify all selected recovery objects before copying.', verified)
        value, checksum = _manifest(source, verified['manifest_sha256'])
        objects = {item['sha256']: item['size'] for item in _payload_refs(value)}
        files = [{'path': 'objects/' + sha, 'sha256': sha, 'size': size} for sha, size in sorted(objects.items())]
        files.append({'path': 'manifest.json', 'sha256': checksum, 'size': source.stat().st_size})
        if target.exists() and not target.is_dir():
            raise GovernanceError('TRANSFER_DESTINATION_CONFLICT', 'The copy destination must be a directory.')
        self._copy_observe_files(target, files, require_complete=False)
        return self._save_plan('copy', {'manifest': str(source), 'manifest_sha256': checksum,
                               'destination': str(target), 'set_id': value['set_id'], 'files': files,
                               'meaning': 'Copy only this sealed recovery manifest and its selected objects to a local directory. No cloud synchronization or remote retention is asserted.'})

    @staticmethod
    def _copy_observe_files(target, files, require_complete):
        missing = []
        for item in files:
            path = safe(target, item['path'])
            if not path.exists():
                missing.append(item['path'])
                continue
            data = read_file_bytes(path, MAX_BYTES)
            if len(data) != item['size'] or _hash(data) != item['sha256']:
                raise GovernanceError('TRANSFER_DESTINATION_CONFLICT', 'Different existing destination bytes were preserved.', {'path': item['path']})
        return {'verified': not missing, 'missing': missing, 'files': len(files),
                'kind': 'local_recovery_copy', 'local_copy_verified': not missing,
                'cloud_upload_verified': False, 'cloud_download_verified': False,
                'offsite_recovery_verified': False,
                'meaning': 'Verified local copied bytes only; provider upload, remote retention and a second-machine restore require separate evidence.'}

    def _copy_execute(self, plan):
        from .project_recovery import ProjectRecovery
        prior = self._receipt(plan['plan_id'])
        target = normal(plan['destination'])
        observed = self._copy_observe_files(target, plan['files'], require_complete=False)
        if observed['verified']:
            verified = ProjectRecovery._verify(str(target / 'manifest.json'), plan['manifest_sha256'])
            if not verified['verified']:
                raise GovernanceError('TRANSFER_DESTINATION_INCOMPLETE', 'The copied recovery set failed structural verification.', verified)
            return self._finish(plan, observed, prior, effect_reused=True)
        if prior:
            raise GovernanceError('TRANSFER_EFFECT_CHANGED', 'The retained copy receipt no longer matches complete local bytes.', observed)
        # Check the entire source before making any additional destination files.
        verified = ProjectRecovery._verify(plan['manifest'], plan['manifest_sha256'])
        if not verified['verified']:
            raise GovernanceError('TRANSFER_SOURCE_INCOMPLETE', 'The original recovery set is no longer complete.', verified)
        self._started(plan)
        source = normal(plan['manifest'])
        for item in plan['files']:
            path = source if item['path'] == 'manifest.json' else safe(source.parent, item['path'])
            data = read_file_bytes(path, MAX_BYTES)
            if len(data) != item['size'] or _hash(data) != item['sha256']:
                raise GovernanceError('TRANSFER_SOURCE_CHANGED', 'A frozen recovery file changed before its copy.', {'path': item['path']})
            # Objects first, manifest last. Partial transfers are resumable and
            # cannot expose a manifest before all selected payloads are present.
            atomic(safe(target, item['path']), data)
        observed = self._copy_observe_files(target, plan['files'], require_complete=True)
        verified = ProjectRecovery._verify(str(target / 'manifest.json'), plan['manifest_sha256'])
        if not observed['verified'] or not verified['verified']:
            raise GovernanceError('TRANSFER_DESTINATION_INCOMPLETE', 'Read-back verification did not confirm the complete local copy.', observed)
        return self._finish(plan, observed, prior, effect_reused=False)

    def _verify(self, plan):
        if plan['kind'] == 'publish':
            return {'plan_id': plan['plan_id'], **self._publish_observe(plan)}
        from .project_recovery import ProjectRecovery
        observed = self._copy_observe_files(normal(plan['destination']), plan['files'], require_complete=True)
        if observed['verified']:
            structural = ProjectRecovery._verify(str(Path(plan['destination']) / 'manifest.json'), plan['manifest_sha256'])
            observed['verified'] = structural['verified']
            observed['state_references_verified'] = structural['state_references_verified']
        return {'plan_id': plan['plan_id'], **observed}
