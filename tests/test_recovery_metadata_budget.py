"""Bounded path metadata, frozen legacy plans and real selected Git recovery."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from taskcarry.core import Core
from taskcarry.integration import Integration
from taskcarry.project_recovery import ProjectRecovery
from taskcarry import recovery_git as rg
from taskcarry.recovery_files import digest, encoded, read_json
from taskcarry.store import GovernanceError


class MetadataFixture(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).resolve().parents[1] / 'validation' / 'local'
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='metadata-budget-', dir=base)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()


class MetadataBudgetTests(MetadataFixture):
    def inventory(self, names):
        observation = {'head': 'a' * 40, 'branch': 'refs/heads/main', 'refs': {},
                       'symbolic_refs': {}, 'index': [], 'object_format': 'sha1',
                       'untracked': names}
        with mock.patch.object(rg, 'observe', side_effect=lambda *a, **k: copy.deepcopy(observation)), \
                mock.patch.object(rg, 'git', return_value=b''), \
                mock.patch.object(rg, 'files', return_value=[]):
            return rg.inventory(self.root, 'git', ['chosen.txt'])

    def test_legacy_metadata_above_old_limit_uses_finite_new_bound(self):
        path = self.root / 'legacy.json'
        path.write_text(json.dumps({'padding': 'x' * (17 * 1024 * 1024)}), encoding='utf-8')
        with self.assertRaises(GovernanceError) as result:
            read_json(path, limit=16 * 1024 * 1024)
        self.assertEqual('FILE_TOO_LARGE', result.exception.code)
        self.assertEqual(17 * 1024 * 1024, len(read_json(path)[0]['padding']))

    def test_more_than_64_mib_is_rejected_before_reading(self):
        path = self.root / 'oversize.json'
        with path.open('wb') as stream:
            stream.seek(64 * 1024 * 1024)
            stream.write(b'x')
        with self.assertRaises(GovernanceError) as result:
            read_json(path)
        self.assertEqual('FILE_TOO_LARGE', result.exception.code)

    def test_large_unselected_lists_have_bounded_examples_and_full_digest(self):
        names = ['chosen.txt'] + ['long-reference/' + str(i).zfill(6) + 'x' * 160 for i in range(10000)]
        result = self.inventory(names)
        self.assertEqual(1000, len(result['git']['untracked']))
        self.assertEqual(10001, result['git']['untracked_count'])
        self.assertTrue(result['git']['untracked_listing_truncated'])
        self.assertEqual(digest(encoded(names)), result['git']['untracked_sha256'])
        self.assertEqual(10000, result['excluded_untracked_count'])
        self.assertEqual(digest(encoded(names[1:])), result['excluded_untracked_sha256'])
        self.assertTrue(result['excluded_untracked_listing_truncated'])
        self.assertLess(len(encoded(result)), 1024 * 1024)

    def test_change_beyond_examples_changes_full_source_digest(self):
        names = ['path/' + str(i).zfill(6) for i in range(2000)]
        first, second = self.inventory(names), self.inventory(names[:-1] + ['path/zzzzzz'])
        self.assertEqual(first['git']['untracked'], second['git']['untracked'])
        self.assertEqual(first['excluded_untracked'], second['excluded_untracked'])
        self.assertNotEqual(first['git']['untracked_sha256'], second['git']['untracked_sha256'])
        self.assertNotEqual(first['excluded_untracked_sha256'], second['excluded_untracked_sha256'])

    def test_small_inventory_keeps_existing_shape(self):
        result = self.inventory(['chosen.txt', 'unselected.txt'])
        self.assertEqual(['chosen.txt', 'unselected.txt'], result['git']['untracked'])
        self.assertNotIn('untracked_sha256', result['git'])
        self.assertEqual(['unselected.txt'], result['excluded_untracked'])
        self.assertNotIn('excluded_untracked_count', result)


@unittest.skipUnless(shutil.which('git'), 'Selected Git recovery requires Git')
class MetadataRecoveryTests(MetadataFixture):
    def setUp(self):
        super().setUp()
        self.control = self.root / 'brain'
        Core.initialize(self.control, 'Synthetic USB acquisition firmware')
        self.core = Core(self.control)
        self.core.task('usb-buffer', 'Verify USB ring buffer overflow handling')
        self.repo = self.root / 'firmware'
        self.repo.mkdir()
        rg.git(self.repo, 'init', '--quiet', '-b', 'main')
        rg.git(self.repo, 'config', 'user.name', 'Synthetic Engineer')
        rg.git(self.repo, 'config', 'user.email', 'engineer@example.invalid')
        (self.repo / 'ring.txt').write_bytes(b'committed baseline\n')
        rg.git(self.repo, 'add', 'ring.txt')
        rg.git(self.repo, 'commit', '-qm', 'Initial synthetic firmware')
        (self.repo / 'ring.txt').write_bytes(b'staged threshold\n')
        rg.git(self.repo, 'add', 'ring.txt')
        (self.repo / 'ring.txt').write_bytes(b'unstaged overflow fix\n')
        (self.repo / 'chosen.txt').write_bytes(b'selected USB capture notes\n')
        (self.repo / 'unselected.txt').write_bytes(b'unselected local trace\n')
        Integration(self.control).workspace('firmware', self.repo)
        self.core.checkpoint('usb-buffer', str(self.repo), ['ring.txt', 'chosen.txt'],
                             'Verify ring buffer under sustained USB traffic')
        self.recovery = ProjectRecovery(self.control)
        self.before = self.source_state()

    def source_state(self):
        return {'head': rg.git(self.repo, 'rev-parse', 'HEAD'),
                'index': (self.repo / '.git' / 'index').read_bytes(),
                'status': rg.git(self.repo, 'status', '--porcelain=v1', '-z'),
                'files': {p.name: p.read_bytes() for p in self.repo.glob('*.txt')}}

    def many_names(self, count=45000):
        # Only excluded-name observation is synthetic. Selected files, index,
        # history, backup objects, verification and restore use real Git/files.
        return ['traces/' + str(i).zfill(6) + '/' + 'usb-frame-' * 20 for i in range(count)]

    def observation(self, names):
        observe = rg.observe

        def selected(root, refs=None):
            value = observe(root, refs)
            if Path(root).resolve() == self.repo.resolve():
                value['untracked'] = sorted(set(value['untracked']) | set(names))
            return value

        return mock.patch.object(rg, 'observe', side_effect=selected)

    def plan(self):
        return self.recovery.recovery('backup_plan', destination=str(self.root / 'media'),
                                      workspaces=[{'name': 'firmware', 'paths': ['chosen.txt']}])

    def assert_restored(self, plan, result):
        self.assertEqual(plan['plan_id'], result['plan_id'])
        self.assertTrue(result['verification']['verified'])
        self.assertTrue(result['verification']['complete_scope'])
        fresh = ProjectRecovery(self.root / 'restore-controller')
        restore = fresh.recovery('restore_plan', manifest=result['manifest'],
                                 expected_sha256=result['manifest_sha256'],
                                 destination=str(self.root / 'restored'))
        effect = fresh.recovery('restore_execute', plan_id=restore['plan_id'])['effect']
        repo = self.root / 'restored' / 'workspaces' / 'firmware'
        self.assertEqual(self.before['head'], rg.git(repo, 'rev-parse', 'HEAD'))
        self.assertEqual(b'staged threshold\n', rg.git(repo, 'show', ':ring.txt'))
        self.assertEqual(b'unstaged overflow fix\n', (repo / 'ring.txt').read_bytes())
        self.assertEqual(b'selected USB capture notes\n', (repo / 'chosen.txt').read_bytes())
        self.assertFalse((repo / 'unselected.txt').exists())
        self.assertFalse((repo / 'traces').exists())
        self.assertEqual('standby', Core(effect['control']).source()['writer_state'])
        self.assertEqual(self.before, self.source_state())

    def test_many_unselected_names_do_not_block_selected_backup_and_restore(self):
        with self.observation(self.many_names()):
            plan = self.plan()
            original = self.recovery._plan_path(plan['plan_id']).read_bytes()
            # On the old implementation this exact execute raises FILE_TOO_LARGE
            # even though planning succeeded; no new API argument is involved.
            result = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
            self.assertLess(len(original), 1024 * 1024)
            self.assertEqual(45002, plan['components'][0]['git']['untracked_count'])
            self.assertEqual(original, self.recovery._plan_path(plan['plan_id']).read_bytes())
            self.assert_restored(plan, result)

    def test_frozen_legacy_plan_above_16_mib_resumes_without_rewriting(self):
        inventory = rg.inventory

        def legacy(*args, **kwargs):
            return inventory(*args, **kwargs, compact=False)

        with self.observation(self.many_names()):
            with mock.patch.object(rg, 'inventory', side_effect=legacy):
                plan = self.plan()
            path = self.recovery._plan_path(plan['plan_id'])
            original = path.read_bytes()
            self.assertGreater(len(original), 16 * 1024 * 1024)
            self.assertLess(len(original), 64 * 1024 * 1024)
            result = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
            self.assertEqual(original, path.read_bytes())
            component = read_json(Path(result['manifest']))[0]['components'][0]
            self.assertEqual(45002, len(component['git']['untracked']))
            self.assertNotIn('untracked_sha256', component['git'])
            self.assert_restored(plan, result)
            again = self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
            self.assertTrue(again['reused_original_batch'])
            self.assertEqual(result['manifest_sha256'], again['manifest_sha256'])
            self.assertEqual(original, path.read_bytes())

    def test_tail_drift_before_capture_rejects_without_final_manifest(self):
        names = self.many_names(1500)
        with self.observation(names):
            plan = self.plan()
            original = self.recovery._plan_path(plan['plan_id']).read_bytes()
            names[-1] += '-changed'
            with self.assertRaises(GovernanceError) as result:
                self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertEqual('RECOVERY_SOURCE_CHANGED', result.exception.code)
        self.assertFalse((self.root / 'media' / 'manifest.json').exists())
        self.assertTrue((self.root / 'media' / 'intent.json').is_file())
        self.assertEqual(original, self.recovery._plan_path(plan['plan_id']).read_bytes())
        self.assertEqual(self.before, self.source_state())

    def test_tail_drift_during_capture_rejects_before_sealing_component(self):
        names = self.many_names(1500)
        with self.observation(names):
            plan = self.plan()
            git = rg.git

            def during_capture(root, *args, **kwargs):
                value = git(root, *args, **kwargs)
                if args[:2] == ('bundle', 'create'):
                    names[-1] += '-changed'
                return value

            with mock.patch.object(rg, 'git', side_effect=during_capture):
                with self.assertRaises(GovernanceError) as result:
                    self.recovery.recovery('backup_execute', plan_id=plan['plan_id'])
        self.assertEqual('RECOVERY_SOURCE_CHANGED', result.exception.code)
        self.assertFalse((self.root / 'media' / 'manifest.json').exists())
        self.assertFalse((self.root / 'media' / 'component-firmware.json').exists())
        self.assertEqual(self.before, self.source_state())


if __name__ == '__main__':
    unittest.main(verbosity=2)
