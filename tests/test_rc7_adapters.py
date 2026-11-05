"""Synthetic process and official-release fixtures; no real account history."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error

from taskcarry.core import Core
from taskcarry.store import GovernanceError
from taskcarry import codex_host
from taskcarry.updates import (Updates, build_release_manifest, validate_manifest,
                               MANIFEST_NAME, RELEASES_URL, API_ROOT, _fingerprint, _fetch_json, _allowed_url)


SCRATCH = Path(__file__).resolve().parents[1] / 'validation' / 'local' / 'adapter-tests'
FAKE = r'''
import json, os, sys, time
from pathlib import Path
home = Path(os.environ['CODEX_HOME'])
mode = (home / 'mode').read_text()
if '--version' in sys.argv:
    print('codex-cli ' + ('0.1.0' if mode == 'old' else '0.166.0-alpha.6'), flush=True)
    raise SystemExit()
for line in sys.stdin:
    message = json.loads(line)
    with (home / 'calls').open('a') as out: out.write(json.dumps(message) + '\n')
    if 'id' not in message: continue
    method, params = message['method'], message['params']
    if mode == 'hang': time.sleep(10)
    if mode == 'oversize': print('x' * 20000, flush=True); continue
    if mode == 'stderr': sys.stderr.write('x' * 20000); sys.stderr.flush(); continue
    if mode == 'malformed': print('broken', flush=True); continue
    if method == 'initialize': result = {'userAgent': 'synthetic'}
    elif method == 'thread/list':
        result = {'data': [{'id': 't1', 'name': 'Synthetic booking', 'cwd': str(home)}], 'nextCursor': 'page2'}
    elif method == 'thread/read': result = {'thread': {'id': params['threadId'], 'name': 'Synthetic booking'}}
    elif method == 'thread/turns/list':
        if mode == 'unsupported':
            print(json.dumps({'id': message['id'], 'error': {'code': -32601, 'message': 'unsupported'}}), flush=True)
            continue
        result = {'data': [{'id': 'turn1', 'items': [{'text': 'Synthetic requirement'}]}], 'nextCursor': None}
    print(json.dumps({'id': message['id'], 'result': result}), flush=True)
'''


class AdapterFixture(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def code(self, expected, call):
        with self.assertRaises(GovernanceError) as error:
            call()
        self.assertEqual(expected, error.exception.code)
        return error.exception


class CodexAdapterTests(AdapterFixture):
    def setUp(self):
        super().setUp()
        self.script = self.root / 'fake_codex.py'
        self.script.write_text(FAKE, encoding='utf-8')
        (self.root / 'mode').write_text('normal')
        original = codex_host._Process

        def process(command, *args):
            return original([sys.executable, str(self.script), *command[1:]], *args)

        self.patch = mock.patch.object(codex_host, '_Process', side_effect=process)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.host = codex_host.CodexHost(sys.executable, str(self.root), timeout=2, max_bytes=8192)

    def test_handshake_page_scope_and_no_mutating_method(self):
        result = self.host.list_threads(limit=1, cursor='opaque', archived=True)
        self.assertEqual('page2', result['page']['nextCursor'])
        self.assertTrue(result['host_startup_may_write_caches'])
        calls = [json.loads(line) for line in (self.root / 'calls').read_text().splitlines()]
        self.assertEqual(['initialize', 'initialized', 'thread/list'], [item['method'] for item in calls])
        self.assertIs(True, calls[-1]['params']['useStateDbOnly'])
        self.assertTrue(calls[-1]['params']['archived'])
        self.assertEqual('opaque', calls[-1]['params']['cursor'])

    def test_read_paginates_without_resuming(self):
        result = self.host.read_thread('t1', limit=1)
        self.assertEqual('Synthetic requirement', result['page']['data'][0]['items'][0]['text'])
        self.assertTrue(result['full_history_read'])
        result = self.host.read_thread('t1', cursor='older')
        self.assertFalse(result['full_history_read'])
        calls = [json.loads(line) for line in (self.root / 'calls').read_text().splitlines()]
        self.assertTrue(all(item['method'] in codex_host.METHODS | {'initialized'} for item in calls))
        self.assertFalse(next(item for item in calls if item['method'] == 'thread/read')['params']['includeTurns'])

    def test_capability_handshake_is_not_history_verification(self):
        result = self.host.capabilities()
        self.assertFalse(result['history_read_verified'])
        self.assertFalse(result['agent_turn_started'])

    def test_old_version_refused_before_history_server(self):
        (self.root / 'mode').write_text('old')
        self.code('HOST_VERSION_UNVERIFIED', self.host.list_threads)
        self.assertFalse((self.root / 'calls').exists())

    def test_timeout_output_invalid_protocol_and_original_error(self):
        for mode, expected in [('hang', 'HOST_TIMEOUT'), ('oversize', 'HOST_OUTPUT_LIMIT'),
                               ('stderr', 'HOST_OUTPUT_LIMIT'), ('malformed', 'HOST_PROTOCOL_ERROR')]:
            with self.subTest(mode=mode):
                (self.root / 'mode').write_text(mode)
                self.code(expected, self.host.capabilities)
        (self.root / 'mode').write_text('unsupported')
        error = self.code('HOST_REQUEST_FAILED', lambda: self.host.read_thread('t1'))
        self.assertEqual(-32601, error.details['original_error']['code'])

    def test_argument_bounds_and_method_allowlist(self):
        self.code('INVALID_ARGUMENT', lambda: self.host.list_threads(limit=0))
        self.code('INVALID_ARGUMENT', lambda: self.host.list_threads(limit=True))
        self.code('INVALID_ARGUMENT', lambda: self.host.read_thread(''))
        self.code('HOST_METHOD_FORBIDDEN', lambda: self.host._request(None, 'turn/start', {}, 1))


class UpdateTests(AdapterFixture):
    def setUp(self):
        super().setUp()
        Core.initialize(self.root / 'control', 'Synthetic release governance')
        self.engine = Updates(self.root / 'control')
        self.engine.update_source(current_version='0.2.0rc6')
        self.manifest = build_release_manifest('0.2.0rc7', 'a' * 40,
            [{'name': 'taskcarry-0.2.0rc7-product.zip', 'sha256': 'b' * 64, 'size': 100}])
        self.digest = hashlib.sha256(json.dumps(self.manifest).encode()).hexdigest()
        base = RELEASES_URL + '/download/v0.2.0rc7/'
        self.release = {'tag_name': 'v0.2.0rc7', 'draft': False, 'prerelease': True,
                        'assets': [{'name': MANIFEST_NAME, 'digest': 'sha256:' + self.digest,
                                    'browser_download_url': base + MANIFEST_NAME},
                                   {'name': self.manifest['artifacts'][0]['name'], 'size': 100,
                                    'digest': 'sha256:' + 'b' * 64,
                                    'browser_download_url': base + self.manifest['artifacts'][0]['name']}]}
        self.responses = {API_ROOT + '/releases?per_page=20&page=1': ([self.release], 'unused'),
                          base + MANIFEST_NAME: (self.manifest, self.digest),
                          API_ROOT + '/git/ref/tags/v0.2.0rc7': ({'object': {'type': 'commit', 'sha': 'a' * 40}}, '')}
        self.patch = mock.patch('taskcarry.updates._fetch_json', side_effect=lambda url: self.responses[url])
        self.fetch = self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_readonly_check_and_explicit_idempotent_assessment(self):
        before = self.engine.store.events()
        check = self.engine.update_check()
        self.assertEqual('CANDIDATE', check['status'])
        self.assertFalse(check['candidate']['artifact_bytes_downloaded'])
        self.assertEqual(before, self.engine.store.events())
        assessed = self.engine.update_assess(check, 'plan', 'Useful update', ['test:verified'])
        after = self.engine.store.events()
        again = self.engine.update_check()
        self.assertEqual(check['fingerprint'], again['fingerprint'])
        self.assertTrue(self.engine.update_assess(again, 'plan', 'Useful update', ['test:verified'])['reused'])
        self.assertEqual(after, self.engine.store.events())
        self.assertFalse(assessed['assessment']['installation_performed'])
        self.assertFalse(assessed['assessment']['host_loading_verified'])

    def test_stable_channel_does_not_promote_rc(self):
        self.assertEqual('NO_RELEASE_IN_WINDOW', self.engine.update_check('stable')['status'])

    def test_offline_does_not_claim_latest_and_wait_can_be_saved(self):
        self.fetch.side_effect = urllib.error.URLError('synthetic offline')
        check = self.engine.update_check()
        self.assertEqual('UNVERIFIED', check['status'])
        self.assertFalse(check['latest_verified'])
        self.engine.update_assess(check, 'wait', 'Network unavailable')
        self.code('UPDATE_REVIEW_REQUIRED', lambda: self.engine.update_assess(check, 'plan', 'Unsafe'))

    def test_tampered_asset_manifest_and_tag_are_unverified(self):
        for location in ('manifest', 'asset', 'tag'):
            with self.subTest(location=location):
                if location == 'manifest': self.release['assets'][0]['digest'] = 'sha256:' + 'c' * 64
                if location == 'asset': self.release['assets'][1]['size'] = 101
                if location == 'tag': self.responses[API_ROOT + '/git/ref/tags/v0.2.0rc7'] = ({'object': {'type': 'commit', 'sha': 'c' * 40}}, '')
                result = self.engine.update_check()
                self.assertEqual('UNVERIFIED', result['status'])
                self.assertEqual('UPDATE_IDENTITY_MISMATCH', result['error']['code'])
                self.release['assets'][0]['digest'] = 'sha256:' + self.digest
                self.release['assets'][1]['size'] = 100

    def test_current_exact_subset_identity_and_same_version_conflict(self):
        self.engine.update_source(current_version='0.2.0rc7', current_artifacts=self.manifest['artifacts'], expected_revision=1)
        self.assertEqual('CURRENT_MATCHES', self.engine.update_check()['status'])
        wrong = [dict(self.manifest['artifacts'][0], sha256='f' * 64)]
        self.engine.update_source(current_version='0.2.0rc7', current_artifacts=wrong, expected_revision=2)
        self.assertEqual('SAME_VERSION_CONFLICT', self.engine.update_check()['status'])

    def test_same_version_new_manifest_keeps_original_identity(self):
        first = self.engine.update_check()
        self.engine.update_assess(first, 'plan', 'First candidate')
        self.manifest['required_actions'] = ['Changed release contents']
        new_digest = hashlib.sha256(json.dumps(self.manifest).encode()).hexdigest()
        self.responses[RELEASES_URL + '/download/v0.2.0rc7/' + MANIFEST_NAME] = (self.manifest, new_digest)
        self.release['assets'][0]['digest'] = 'sha256:' + new_digest
        changed = self.engine.update_check()
        self.code('UPDATE_IDENTITY_CONFLICT', lambda: self.engine.update_assess(changed, 'plan', 'Changed candidate'))
        self.assertEqual(first['candidate']['identity'], self.engine.store.get('update_release_identities', '0.2.0rc7')['identity'])

    def test_stale_source_and_check_tampering(self):
        check = self.engine.update_check()
        self.engine.update_source(channel='stable', current_version='0.2.0rc6', expected_revision=1)
        self.code('UPDATE_SOURCE_CHANGED', lambda: self.engine.update_assess(check, 'wait', 'Stale'))
        check['status'] = 'CURRENT_MATCHES'
        self.code('UPDATE_CHECK_CHANGED', lambda: self.engine.update_assess(check, 'wait', 'Changed'))

    def test_assessment_rejects_malformed_candidate_and_nonfinite_json(self):
        check = self.engine.update_check()
        check['candidate'] = []
        self.code('UPDATE_METADATA_INVALID', lambda: self.engine.update_assess(check, 'wait', 'Malformed'))
        check['candidate'] = None
        check['unexpected'] = float('nan')
        self.code('UPDATE_METADATA_INVALID', lambda: self.engine.update_assess(check, 'wait', 'Malformed'))

    def test_malformed_tag_object_is_unverified(self):
        self.responses[API_ROOT + '/git/ref/tags/v0.2.0rc7'] = ({'object': []}, '')
        result = self.engine.update_check()
        self.assertEqual('UNVERIFIED', result['status'])
        self.assertEqual('UPDATE_METADATA_INVALID', result['error']['code'])

    def test_legacy_release_and_bounded_search(self):
        self.release['assets'] = []
        self.assertEqual('LEGACY_REVIEW_REQUIRED', self.engine.update_check()['status'])
        self.responses[API_ROOT + '/releases?per_page=20&page=1'] = ([dict(self.release, draft=True)] * 20, '')
        self.responses[API_ROOT + '/releases?per_page=20&page=2'] = ([dict(self.release, draft=True)] * 20, '')
        self.fetch.reset_mock()
        result = self.engine.update_check()
        self.assertEqual(2, self.fetch.call_count)
        self.assertFalse(result['coverage']['complete'])
        self.assertFalse(result['latest_verified'])

    def test_source_cas_and_no_empty_history(self):
        before = self.engine.store.events()
        self.assertTrue(self.engine.update_source(current_version='0.2.0rc6')['reused'])
        self.assertEqual(before, self.engine.store.events())
        self.code('REVISION_CONFLICT', lambda: self.engine.update_source(channel='stable'))

    def test_manifest_rejects_self_reference_bad_hash_and_unknown_fields(self):
        self.assertEqual(self.manifest, validate_manifest(self.manifest))
        self.code('UPDATE_METADATA_INVALID', lambda: build_release_manifest('0.2.0rc7', 'a' * 40,
            [{'name': MANIFEST_NAME, 'size': 1, 'sha256': 'b' * 64}]))
        self.code('UPDATE_METADATA_INVALID', lambda: validate_manifest(dict(self.manifest, unexpected=True)))

    def test_annotated_tag_is_resolved_to_commit(self):
        self.responses[API_ROOT + '/git/ref/tags/v0.2.0rc7'] = ({'object': {'type': 'tag', 'sha': 'd' * 40}}, '')
        self.responses[API_ROOT + '/git/tags/' + 'd' * 40] = ({'object': {'type': 'commit', 'sha': 'a' * 40}}, '')
        self.assertEqual('CANDIDATE', self.engine.update_check()['status'])


class NetworkBoundsTests(AdapterFixture):
    def test_unapproved_redirect_and_oversized_reply(self):
        self.code('UPDATE_SOURCE_REJECTED', lambda: _allowed_url('https://example.invalid/manifest'))
        self.code('UPDATE_SOURCE_REJECTED', lambda: _allowed_url('https://user:secret@github.com/x'))
        response = io.BytesIO(b'x' * (2 * 1024 * 1024 + 1))
        response.geturl = lambda: API_ROOT + '/releases'
        opener = mock.Mock()
        opener.open.return_value = response
        with mock.patch('urllib.request.build_opener', return_value=opener):
            self.code('UPDATE_OUTPUT_LIMIT', lambda: _fetch_json(API_ROOT + '/releases'))

    def test_malformed_json_is_rejected(self):
        response = io.BytesIO(b'not JSON')
        response.geturl = lambda: API_ROOT + '/releases'
        opener = mock.Mock()
        opener.open.return_value = response
        with mock.patch('urllib.request.build_opener', return_value=opener):
            self.code('UPDATE_METADATA_INVALID', lambda: _fetch_json(API_ROOT + '/releases'))


if __name__ == '__main__':
    unittest.main()
