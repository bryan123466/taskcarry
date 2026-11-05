"""Independent failure-boundary review using synthetic state and child processes."""
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest import mock

from taskcarry.codex_host import _Process
from taskcarry.core import Core
from taskcarry.store import GovernanceError
from taskcarry.updates import Updates, build_release_manifest, validate_manifest


class IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / 'validation/local/independent-review'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name)
        Core.initialize(self.root / 'control')
        self.core = Core(self.root / 'control')

    def tearDown(self):
        self.temp.cleanup()

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_future_context_schema_initialization_refuses_without_file_effects(self):
        with sqlite3.connect(self.core.store.path) as db:
            db.execute('UPDATE context_schema SET version=999')
        db.close()
        before = self.snapshot()
        self.assertEqual('unsupported', Core.identify(self.core.root)['state'])
        with self.assertRaises(GovernanceError) as error:
            Core.initialize(self.core.root)
        self.assertEqual('SCHEMA_VERSION_UNSUPPORTED', error.exception.code)
        self.assertEqual(before, self.snapshot())

    def test_unrelated_task_changes_do_not_invalidate_scoped_page(self):
        self.core.task('selected')
        self.core.task('unrelated')
        for i in range(3):
            self.core.store.put('observations', 'evidence-' + str(i),
                                {'observation_id': 'evidence-' + str(i), 'task_id': 'selected', 'summary': 'Synthetic'})
        first = self.core.context('selected', limit=1)
        self.core.task('unrelated', title='Changed unrelated task')
        second = self.core.context('selected', limit=1, cursor=first['next_cursor'])
        self.assertEqual(first['fingerprint'], second['fingerprint'])
        self.assertNotEqual(first['items'][0]['local_id'], second['items'][0]['local_id'])
        self.assertLessEqual(second['storage']['loaded_records'], second['storage']['payload_read_bound'])

    def test_malformed_asset_name_returns_unverified_not_unhandled_exception(self):
        engine = Updates(self.core.root)
        engine.update_source(current_version='0.2.0rc6')
        release = {'tag_name': 'v0.2.0rc7', 'draft': False, 'prerelease': True,
                   'assets': [{'name': ['invalid', 'asset']}]}
        with mock.patch('taskcarry.updates._fetch_json', return_value=([release], 'synthetic')):
            result = engine.update_check()
        self.assertEqual('UNVERIFIED', result['status'])
        self.assertEqual('UPDATE_METADATA_INVALID', result['error']['code'])

    def test_manifest_protocol_versions_require_integers_not_booleans(self):
        for field in ('schema', 'state_schema'):
            with self.subTest(field=field):
                manifest = build_release_manifest('0.2.0rc7', 'a' * 40,
                    [{'name': 'product.zip', 'sha256': 'b' * 64, 'size': 1}])
                target = manifest if field == 'schema' else manifest['compatibility']
                target[field] = True
                with self.assertRaises(GovernanceError) as error:
                    validate_manifest(manifest)
                self.assertEqual('UPDATE_METADATA_INVALID', error.exception.code)

    @unittest.skipUnless(os.name == 'nt', 'Windows anonymous pipe backpressure regression')
    def test_host_send_observes_deadline_when_child_stops_reading_input(self):
        child = _Process([sys.executable, '-c', 'import time; time.sleep(15)'],
                         self.root, dict(os.environ), 1, 16384)
        done = threading.Event()
        outcome = []
        def send():
            try:
                # This is a permitted cursor length in the real list contract.
                child.send({'method': 'thread/list', 'id': 2, 'params': {'cursor': 'x' * 8192}})
                outcome.append('sent')
            except GovernanceError as error:
                outcome.append(error.code)
            finally:
                done.set()
        sender = threading.Thread(target=send, daemon=True)
        sender.start()
        timely = done.wait(2)
        try:
            self.assertTrue(timely, 'stdin write exceeded the operation deadline')
            self.assertEqual(['HOST_TIMEOUT'], outcome)
        finally:
            if child.process.poll() is None:
                child.process.kill()
            child.process.wait(timeout=3)
            sender.join(timeout=3)
            child.close()


if __name__ == '__main__':
    unittest.main()
