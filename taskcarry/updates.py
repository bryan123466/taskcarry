"""Official release discovery and explicit, host-reviewed adoption decisions.

Network reads never install packages or change local state. Saved assessments
are not installation or host-loading receipts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

from . import __version__
from .core import Core
from .maintenance import _revision
from .store import GovernanceError, now


REPOSITORY = 'bryan123466/taskcarry'
RELEASES_URL = 'https://github.com/' + REPOSITORY + '/releases'
API_ROOT = 'https://api.github.com/repos/' + REPOSITORY
MANIFEST_NAME = 'taskcarry-release.json'
MAX_RESPONSE = 2 * 1024 * 1024
VERSION = re.compile(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:rc([1-9][0-9]*))?$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
COMMIT = re.compile(r'^[0-9a-f]{40}$')
DECISIONS = ('prioritize', 'plan', 'keep', 'wait', 'reject')


def _fingerprint(value):
    try:
        data = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                          allow_nan=False).encode('utf-8')
    except (ValueError, TypeError) as exc:
        raise GovernanceError('UPDATE_METADATA_INVALID', 'Update records require finite JSON data.') from exc
    if len(data) > MAX_RESPONSE:
        raise GovernanceError('UPDATE_OUTPUT_LIMIT', 'Update record exceeds its byte limit.')
    return hashlib.sha256(data).hexdigest()


def _version(value):
    match = VERSION.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise GovernanceError('UPDATE_METADATA_INVALID', 'Expected a release version such as 1.2.3 or 1.2.3rc1.')
    major, minor, patch, rc = match.groups()
    return int(major), int(minor), int(patch), 1 if rc is None else 0, int(rc or 0)


def _artifacts(value):
    if not isinstance(value, list) or len(value) > 20:
        raise GovernanceError('UPDATE_METADATA_INVALID', 'Expected at most 20 explicit artifacts.')
    names = set()
    result = []
    for item in value:
        if not isinstance(item, dict):
            raise GovernanceError('UPDATE_METADATA_INVALID', 'Artifact metadata must be an object.')
        name, digest, size = item.get('name'), item.get('sha256'), item.get('size')
        if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}', name)
                or PurePosixPath(name).name != name or name in names or name == MANIFEST_NAME
                or not isinstance(digest, str) or not SHA256.fullmatch(digest)
                or isinstance(size, bool) or not isinstance(size, int) or size < 0):
            raise GovernanceError('UPDATE_METADATA_INVALID', 'Artifact name, size or SHA-256 is invalid.')
        names.add(name)
        result.append({'name': name, 'sha256': digest, 'size': size})
    return sorted(result, key=lambda item: item['name'])


def build_release_manifest(version, source_commit, artifacts, required_actions=None,
                           python_min='3.11', state_schema=1):
    """Build after final packages; the manifest deliberately excludes itself."""
    parsed = _version(version)
    if not isinstance(source_commit, str) or not COMMIT.fullmatch(source_commit):
        raise GovernanceError('UPDATE_METADATA_INVALID', 'source_commit must be a full Git SHA.')
    files = _artifacts(artifacts)
    if not files:
        raise GovernanceError('UPDATE_METADATA_INVALID', 'A release manifest needs final artifacts.')
    actions = [] if required_actions is None else required_actions
    if (not isinstance(actions, list) or len(actions) > 20
            or any(not isinstance(item, str) or not item.strip() or len(item) > 2000 for item in actions)):
        raise GovernanceError('UPDATE_METADATA_INVALID', 'required_actions must contain bounded text.')
    if (not isinstance(python_min, str) or not re.fullmatch(r'3\.[0-9]+', python_min)
            or type(state_schema) is not int or state_schema != 1):
        raise GovernanceError('UPDATE_METADATA_INVALID', 'Unsupported compatibility metadata.')
    return {'schema': 1, 'repository': REPOSITORY, 'version': version,
            'channel': 'stable' if parsed[3] else 'rc', 'source_commit': source_commit,
            'artifacts': files, 'compatibility': {'python_min': python_min, 'state_schema': state_schema},
            'required_actions': actions, 'release_url': RELEASES_URL + '/tag/v' + version}


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or type(manifest.get('schema')) is not int or manifest['schema'] != 1:
        raise GovernanceError('UPDATE_METADATA_INVALID', 'Unsupported release manifest schema.')
    compat = manifest.get('compatibility')
    if not isinstance(compat, dict):
        raise GovernanceError('UPDATE_METADATA_INVALID', 'Missing compatibility metadata.')
    expected = build_release_manifest(manifest.get('version'), manifest.get('source_commit'),
                                      manifest.get('artifacts'), manifest.get('required_actions'),
                                      compat.get('python_min'), compat.get('state_schema'))
    if manifest != expected:
        raise GovernanceError('UPDATE_METADATA_INVALID', 'Release manifest fields or canonical identity do not match.')
    return expected


class _Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        _allowed_url(newurl)
        return super().redirect_request(request, fp, code, message, headers, newurl)


def _allowed_url(url):
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise GovernanceError('UPDATE_SOURCE_REJECTED', 'The response has an invalid release URL.') from exc
    if (parsed.scheme != 'https' or parsed.username or parsed.password or port not in (None, 443)
            or parsed.hostname not in ('api.github.com', 'github.com', 'release-assets.githubusercontent.com',
                                       'objects.githubusercontent.com')):
        raise GovernanceError('UPDATE_SOURCE_REJECTED', 'The response redirected outside the official release hosts.')


def _fetch_json(url, timeout=10):
    _allowed_url(url)
    request = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json',
                                                   'User-Agent': 'TaskCarry-release-check/1'})
    opener = urllib.request.build_opener(_Redirect())
    with opener.open(request, timeout=timeout) as response:
        _allowed_url(response.geturl())
        deadline = time.monotonic() + timeout
        chunks, total = [], 0
        while True:
            if time.monotonic() >= deadline:
                raise GovernanceError('UPDATE_TIMEOUT', 'Official release response exceeded its time limit.')
            block = response.read1(min(65536, MAX_RESPONSE + 1 - total))
            if not block:
                break
            total += len(block)
            if total > MAX_RESPONSE:
                raise GovernanceError('UPDATE_OUTPUT_LIMIT', 'Official release response exceeded its byte limit.')
            chunks.append(block)
        content = b''.join(chunks)
    try:
        return json.loads(content), hashlib.sha256(content).hexdigest()
    except (UnicodeDecodeError, ValueError) as exc:
        raise GovernanceError('UPDATE_METADATA_INVALID', 'Official release response is not valid JSON.') from exc


class Updates(Core):
    def update_source(self, channel='rc', current_version=None, current_artifacts=None,
                      method_refs=None, maintenance='review', expected_revision=None):
        if channel not in ('rc', 'stable') or maintenance not in ('review', 'authorized_maintenance'):
            raise GovernanceError('INVALID_ARGUMENT', 'Select rc/stable and review/authorized_maintenance.')
        version = current_version or __version__
        _version(version)
        artifacts = _artifacts(current_artifacts or [])
        refs = method_refs or []
        if (not isinstance(refs, list) or len(refs) > 30
                or any(not isinstance(ref, str) or not ref.strip() or len(ref) > 2000 for ref in refs)):
            raise GovernanceError('INVALID_ARGUMENT', 'method_refs must be bounded evidence references.')
        body = {'repository': REPOSITORY, 'release_source': RELEASES_URL, 'channel': channel,
                'current_version': version, 'current_artifacts': artifacts, 'method_refs': refs,
                'current_identity_scope': 'host_reviewed_reference', 'maintenance': maintenance,
                'automatic_install': False}
        with self.store.transaction():
            old = self.store.get('update_sources', 'official')
            if old and all(old.get(key) == value for key, value in body.items()):
                return {'source': old, 'reused': True}
            revision = _revision(expected_revision, old)
            record = dict(body, revision=revision, updated_at=now(),
                          created_at=old['created_at'] if old else now())
            self.store.put('update_sources', 'official', record)
            self.store.put('update_sources_history', 'official.' + str(revision), record)
            self.store.event('update_source_recorded', record)
        return {'source': record, 'reused': False}

    def _candidate(self, release):
        version = release['tag_name'][1:]
        assets = release.get('assets')
        if not isinstance(assets, list) or len(assets) > 30:
            raise GovernanceError('UPDATE_METADATA_INVALID', 'Release assets are missing or oversized.')
        if any(not isinstance(item, dict) or not isinstance(item.get('name'), str)
               or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}', item['name']) for item in assets):
            raise GovernanceError('UPDATE_METADATA_INVALID', 'Release assets contain invalid names.')
        by_name = {item['name']: item for item in assets}
        if len(by_name) != len(assets):
            raise GovernanceError('UPDATE_METADATA_INVALID', 'Release assets contain duplicate names.')
        asset = by_name.get(MANIFEST_NAME)
        if asset is None:
            return {'version': version, 'release_url': RELEASES_URL + '/tag/v' + version,
                    'status': 'LEGACY_REVIEW_REQUIRED', 'reason': 'No structured release manifest.',
                    'identity_verified': False}
        url = RELEASES_URL + '/download/v' + version + '/' + MANIFEST_NAME
        if asset.get('browser_download_url') != url:
            raise GovernanceError('UPDATE_METADATA_INVALID', 'Manifest download URL does not match the release.')
        manifest, digest = _fetch_json(url)
        if asset.get('digest') != 'sha256:' + digest:
            raise GovernanceError('UPDATE_IDENTITY_MISMATCH', 'Manifest bytes do not match the release asset digest.')
        manifest = validate_manifest(manifest)
        if manifest['version'] != version or release.get('prerelease') != (manifest['channel'] == 'rc'):
            raise GovernanceError('UPDATE_IDENTITY_MISMATCH', 'Release channel/version differs from its manifest.')
        # Pin a tag to its actual commit, resolving annotated tags once, never
        # treating target_commitish (which may be a moving branch) as a SHA.
        reference, _ = _fetch_json(API_ROOT + '/git/ref/tags/v' + version)
        obj = reference.get('object', {}) if isinstance(reference, dict) else {}
        if not isinstance(obj, dict):
            raise GovernanceError('UPDATE_METADATA_INVALID', 'Release tag object must be an object.')
        if obj.get('type') == 'tag' and isinstance(obj.get('sha'), str) and COMMIT.fullmatch(obj['sha']):
            tag, _ = _fetch_json(API_ROOT + '/git/tags/' + obj['sha'])
            obj = tag.get('object', {}) if isinstance(tag, dict) else {}
        if not isinstance(obj, dict):
            raise GovernanceError('UPDATE_METADATA_INVALID', 'Annotated tag object must be an object.')
        if obj.get('type') != 'commit' or obj.get('sha') != manifest['source_commit']:
            raise GovernanceError('UPDATE_IDENTITY_MISMATCH', 'Release tag does not resolve to the manifest commit.')
        for file in manifest['artifacts']:
            published = by_name.get(file['name'], {})
            expected_url = RELEASES_URL + '/download/v' + version + '/' + file['name']
            if (published.get('digest') != 'sha256:' + file['sha256'] or published.get('size') != file['size']
                    or published.get('browser_download_url') != expected_url):
                raise GovernanceError('UPDATE_IDENTITY_MISMATCH', 'Release artifact metadata disagrees with the manifest.',
                                      {'artifact': file['name']})
        return {'version': version, 'release_url': manifest['release_url'], 'status': 'CANDIDATE',
                'manifest': manifest, 'manifest_sha256': digest, 'identity': _fingerprint(manifest),
                'identity_verified': True, 'verification_scope': 'official_manifest_tag_and_asset_metadata',
                'artifact_bytes_downloaded': False, 'installation_performed': False}

    def update_check(self, channel=None):
        source = self.store.get('update_sources', 'official')
        if source is None:
            raise GovernanceError('UPDATE_SOURCE_MISSING', 'Register the official source and current identity first.')
        channel = channel or source['channel']
        if channel not in ('rc', 'stable'):
            raise GovernanceError('INVALID_ARGUMENT', 'channel must be rc or stable.')
        result = {'repository': REPOSITORY, 'release_source': RELEASES_URL, 'channel': channel,
                  'source_revision': source['revision'], 'current_version': source['current_version'],
                  'current_artifacts': source['current_artifacts'], 'checked_at': now(),
                  'network_read_only': True, 'local_state_written': False, 'installation_performed': False,
                  'coverage': {'release_limit': 40, 'pages_max': 2, 'complete': False}, 'candidate': None}
        try:
            releases = []
            for page in (1, 2):
                values, _ = _fetch_json(API_ROOT + '/releases?per_page=20&page=' + str(page))
                if not isinstance(values, list) or len(values) > 20:
                    raise GovernanceError('UPDATE_METADATA_INVALID', 'Invalid release-list page.')
                releases.extend(values)
                if len(values) < 20:
                    result['coverage']['complete'] = True
                    break
            choices = []
            for release in releases:
                if not isinstance(release, dict) or release.get('draft') is not False:
                    continue
                tag = release.get('tag_name', '')
                if not isinstance(tag, str) or not tag.startswith('v') or not VERSION.fullmatch(tag[1:]):
                    continue
                key = _version(tag[1:])
                if not isinstance(release.get('prerelease'), bool) or release['prerelease'] != (key[3] == 0):
                    raise GovernanceError('UPDATE_METADATA_INVALID', 'Release tag and prerelease flag disagree.')
                if channel == 'stable' and release['prerelease']:
                    continue
                choices.append((key, release))
            if not choices:
                result.update(status='NO_RELEASE_IN_WINDOW', latest_verified=False)
            else:
                key, release = max(choices, key=lambda item: item[0])
                if key < _version(source['current_version']):
                    result.update(status='NO_NEWER_RELEASE_IN_WINDOW', latest_verified=False)
                else:
                    candidate = self._candidate(release)
                    result['candidate'] = candidate
                    result['status'] = candidate['status']
                    result['latest_verified'] = result['coverage']['complete'] and candidate['identity_verified']
                    if candidate['identity_verified'] and key == _version(source['current_version']):
                        expected = {item['name']: item for item in candidate['manifest']['artifacts']}
                        if not source['current_artifacts']:
                            result['status'] = 'CURRENT_IDENTITY_INCOMPLETE'
                        elif all(expected.get(item['name']) == item for item in source['current_artifacts']):
                            result['status'] = 'CURRENT_MATCHES'
                        else:
                            result['status'] = 'SAME_VERSION_CONFLICT'
        except (GovernanceError, urllib.error.URLError, OSError, TimeoutError, socket.timeout) as exc:
            result.update(status='UNVERIFIED', latest_verified=False,
                          error={'code': getattr(exc, 'code', 'UPDATE_NETWORK_UNAVAILABLE'), 'message': str(exc),
                                 'details': getattr(exc, 'details', None)})
        result['fingerprint'] = _fingerprint({key: value for key, value in result.items()
                                              if key not in ('checked_at', 'fingerprint')})
        return result

    def update_assess(self, check, decision, reason, evidence_refs=None, expected_revision=None):
        if not isinstance(check, dict) or check.get('repository') != REPOSITORY:
            raise GovernanceError('INVALID_ARGUMENT', 'Provide an official update-check result.')
        if (check.get('candidate') is not None and not isinstance(check['candidate'], dict)):
            raise GovernanceError('UPDATE_METADATA_INVALID', 'The checked candidate must be an object or null.')
        candidate = check.get('candidate') or {}
        if candidate.get('identity_verified') is True:
            manifest = validate_manifest(candidate.get('manifest'))
            if candidate.get('identity') != _fingerprint(manifest) or candidate.get('version') != manifest['version']:
                raise GovernanceError('UPDATE_IDENTITY_MISMATCH', 'The checked candidate identity does not match its manifest.')
        calculated = _fingerprint({key: value for key, value in check.items() if key not in ('checked_at', 'fingerprint')})
        if check.get('fingerprint') != calculated:
            raise GovernanceError('UPDATE_CHECK_CHANGED', 'Check content no longer matches its fingerprint.')
        if decision not in DECISIONS or not isinstance(reason, str) or not reason.strip() or len(reason) > 4000:
            raise GovernanceError('INVALID_ARGUMENT', 'Supply a supported decision and bounded reason.')
        if decision in ('prioritize', 'plan') and (check.get('status') not in ('CANDIDATE', 'CURRENT_MATCHES')
                or not (check.get('candidate') or {}).get('identity_verified')):
            raise GovernanceError('UPDATE_REVIEW_REQUIRED', 'Resolve the missing or conflicting identity before planning adoption.')
        refs = evidence_refs or []
        if (not isinstance(refs, list) or len(refs) > 30
                or any(not isinstance(ref, str) or not ref.strip() or len(ref) > 2000 for ref in refs)):
            raise GovernanceError('INVALID_ARGUMENT', 'evidence_refs must be bounded references.')
        body = {'check_fingerprint': calculated, 'check': {k: v for k, v in check.items() if k != 'checked_at'},
                'decision': decision, 'reason': reason, 'evidence_refs': refs,
                'evidence_scope': 'host_reviewed_reference', 'installation_performed': False,
                'host_loading_verified': False}
        with self.store.transaction():
            source = self.store.get('update_sources', 'official')
            if not source or source['revision'] != check.get('source_revision'):
                raise GovernanceError('UPDATE_SOURCE_CHANGED', 'The registered source changed; check again.')
            old = self.store.get('update_assessments', calculated)
            if old and all(old.get(key) == value for key, value in body.items()):
                return {'assessment': old, 'reused': True}
            candidate = check.get('candidate') or {}
            if candidate.get('identity_verified'):
                key = candidate['version']
                previous = self.store.get('update_release_identities', key)
                if previous and previous['identity'] != candidate['identity']:
                    raise GovernanceError('UPDATE_IDENTITY_CONFLICT', 'The same release version now has different content.',
                                          {'previous_identity': previous['identity'], 'candidate_identity': candidate['identity']})
                if previous is None:
                    self.store.put('update_release_identities', key, candidate)
            revision = _revision(expected_revision, old)
            record = dict(body, revision=revision, updated_at=now(), created_at=old['created_at'] if old else now())
            self.store.put('update_assessments', calculated, record)
            self.store.put('update_assessments_history', calculated + '.' + str(revision), record)
            self.store.event('update_assessed', record)
        return {'assessment': record, 'reused': False}
