"""Synthetic restore effects, receipt recovery, and preservation of later work."""
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from taskcarry import core as module
from taskcarry.core import Core, git
from taskcarry.store import GovernanceError


class RestoreRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='taskcarry-restore-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.project = self.root / 'control'
        self.author = self.root / 'author'
        self.author.mkdir()
        self.destination = self.root / 'restored'
        Core.initialize(self.project, 'Synthetic restore recovery')
        self.core = Core(self.project)
        self.core.task('draft', state='paused')
        (self.author / 'first.bin').write_bytes(b'\x00saved\xff\r\n')
        (self.author / 'nested').mkdir()
        (self.author / 'nested' / 'notes.txt').write_text('合成记录\n', encoding='utf-8')

    def capture(self):
        return self.core.checkpoint('draft', self.author, ['first.bin', 'nested/notes.txt'], 'Continue review')

    def git_capture(self):
        git(self.author, 'init', '--quiet')
        git(self.author, 'config', 'user.name', 'Synthetic Author')
        git(self.author, 'config', 'user.email', 'author@example.invalid')
        git(self.author, 'add', '--', 'first.bin', 'nested/notes.txt')
        git(self.author, 'commit', '--quiet', '-m', 'Synthetic baseline')
        (self.author / 'first.bin').write_bytes(b'\x00staged\xff\n')
        git(self.author, 'add', '--', 'first.bin')
        (self.author / 'first.bin').write_bytes(b'\x00worktree\xfe\r\n')
        (self.author / 'nested' / 'notes.txt').unlink()
        return self.capture()

    def operation(self):
        operations = self.core.store.list('operations')
        self.assertEqual(1, len(operations))
        self.assertEqual(operations[0], self.core.store.get('operations', operations[0]['operation_id']))
        return operations[0]

    def restored_events(self):
        return [e for e in self.core.store.events() if e['kind'] == 'checkpoint_restored']

    def interrupt_receipt(self, checkpoint):
        original = self.core.store.event

        def fail(kind, payload):
            if kind == 'checkpoint_restored':
                raise OSError('Synthetic restore receipt interruption')
            return original(kind, payload)

        with mock.patch.object(self.core.store, 'event', side_effect=fail):
            with self.assertRaises(OSError):
                self.core.restore(checkpoint['checkpoint_id'], self.destination)
        operation = self.operation()
        self.assertEqual('EFFECT_APPLIED', operation['status'])
        self.assertEqual([], self.restored_events())
        self.assertIsNone(self.core.store.get('restore_receipts', operation['operation_id']))
        self.assertEqual(1, self.core.agenda()['counts']['operations'])
        return operation

    def assert_review(self, checkpoint, code='RESTORE_REVIEW_REQUIRED'):
        operation = self.operation()
        events = self.core.store.events()
        with self.assertRaises(GovernanceError) as failure:
            Core(self.project).restore(checkpoint['checkpoint_id'], self.destination)
        self.assertEqual(code, failure.exception.code)
        self.assertEqual(operation, self.operation())
        self.assertEqual(events, self.core.store.events())

    def test_plain_event_failure_recovers_only_receipt_without_git_or_file_writes(self):
        checkpoint = self.capture()
        task = self.core.store.get('tasks', 'draft')
        operation = self.interrupt_receipt(checkpoint)
        (self.author / 'first.bin').write_bytes(b'New source work is retained')
        before = (self.destination / 'first.bin').stat().st_mtime_ns
        original_open = Path.open

        def readonly(path, mode='r', *args, **kwargs):
            if path.is_relative_to(self.destination) and any(flag in mode for flag in 'wax+'):
                raise AssertionError('Receipt recovery tried to write destination')
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(Path, 'open', new=readonly), mock.patch.object(module, 'git', side_effect=AssertionError('Plain restore needs no Git')):
            result = Core(self.project).restore(checkpoint['checkpoint_id'], self.destination)
            repeated = Core(self.project).restore(checkpoint['checkpoint_id'], self.destination)
        self.assertTrue(result['restored'])
        self.assertTrue(repeated['reused'])
        self.assertEqual(operation['operation_id'], result['operation_id'])
        self.assertEqual(before, (self.destination / 'first.bin').stat().st_mtime_ns)
        self.assertEqual(b'New source work is retained', (self.author / 'first.bin').read_bytes())
        self.assertEqual(task, self.core.store.get('tasks', 'draft'))
        self.assertEqual(1, len(self.restored_events()))
        self.assertEqual('COMPLETED', self.operation()['status'])
        self.assertEqual(0, self.core.agenda()['counts']['operations'])
        self.assertTrue(self.core.store.get('restore_receipts', result['operation_id'])['verified'])

    def test_git_event_failure_recovers_without_replaying_git_and_preserves_layers(self):
        checkpoint = self.git_capture()
        source_index = git(self.author, 'ls-files', '--stage', '-z').stdout
        operation = self.interrupt_receipt(checkpoint)
        head = git(self.destination, 'rev-parse', 'HEAD').stdout
        index = (self.destination / '.git' / 'index').read_bytes()
        original = module.git

        def read_git(root, *args, **kwargs):
            self.assertIn(args[0], ('rev-parse', 'ls-files', 'ls-tree', 'cat-file'))
            return original(root, *args, **kwargs)

        with mock.patch.object(module, 'git', side_effect=read_git):
            restored = Core(self.project).restore(checkpoint['checkpoint_id'], self.destination)
        self.assertEqual(operation['operation_id'], restored['operation_id'])
        self.assertEqual(head, git(self.destination, 'rev-parse', 'HEAD').stdout)
        self.assertEqual(index, (self.destination / '.git' / 'index').read_bytes())
        self.assertEqual(source_index, git(self.destination, 'ls-files', '--stage', '-z').stdout)
        self.assertEqual(source_index, git(self.author, 'ls-files', '--stage', '-z').stdout)
        self.assertEqual(b'\x00worktree\xfe\r\n', (self.destination / 'first.bin').read_bytes())
        self.assertFalse((self.destination / 'nested' / 'notes.txt').exists())
        self.assertEqual(1, len(self.restored_events()))

    def test_changed_restored_file_is_preserved_without_receipt(self):
        checkpoint = self.capture()
        self.interrupt_receipt(checkpoint)
        (self.destination / 'first.bin').write_bytes(b'New destination work')
        self.assert_review(checkpoint)
        self.assertEqual(b'New destination work', (self.destination / 'first.bin').read_bytes())

    def test_extra_file_or_empty_directory_is_preserved(self):
        checkpoint = self.capture()
        self.interrupt_receipt(checkpoint)
        extra = self.destination / 'extra.txt'
        extra.write_bytes(b'Independent user note')
        self.assert_review(checkpoint)
        self.assertEqual(b'Independent user note', extra.read_bytes())
        extra.unlink()
        extra.mkdir()
        self.assert_review(checkpoint)
        self.assertTrue(extra.is_dir())

    def test_replaced_destination_with_identical_content_is_not_adopted(self):
        checkpoint = self.capture()
        self.interrupt_receipt(checkpoint)
        retained = self.root / 'retained-first-destination'
        self.destination.rename(retained)
        shutil.copytree(retained, self.destination)
        self.assert_review(checkpoint)
        self.assertEqual((retained / 'first.bin').read_bytes(), (self.destination / 'first.bin').read_bytes())

    def test_user_git_head_change_is_preserved_even_when_tree_is_identical(self):
        checkpoint = self.git_capture()
        self.interrupt_receipt(checkpoint)
        # commit-tree avoids consuming the deliberately staged saved index.
        tree = git(self.destination, 'rev-parse', 'HEAD^{tree}').stdout.decode().strip()
        head = git(self.destination, 'rev-parse', 'HEAD').stdout.decode().strip()
        newer = git(self.destination, 'commit-tree', tree, '-p', head, input_bytes=b'Synthetic later commit').stdout.decode().strip()
        git(self.destination, 'update-ref', 'HEAD', newer)
        self.assert_review(checkpoint)
        self.assertEqual(newer, git(self.destination, 'rev-parse', 'HEAD').stdout.decode().strip())

    def test_user_git_index_change_is_preserved(self):
        checkpoint = self.git_capture()
        self.interrupt_receipt(checkpoint)
        git(self.destination, 'add', '--', 'first.bin')
        index = (self.destination / '.git' / 'index').read_bytes()
        self.assert_review(checkpoint)
        self.assertEqual(index, (self.destination / '.git' / 'index').read_bytes())

    def test_user_git_config_change_is_preserved(self):
        checkpoint = self.git_capture()
        self.interrupt_receipt(checkpoint)
        git(self.destination, 'config', 'synthetic.note', 'retain this setting')
        config = (self.destination / '.git' / 'config').read_bytes()
        self.assert_review(checkpoint)
        self.assertEqual(config, (self.destination / '.git' / 'config').read_bytes())

    def test_extra_git_metadata_is_preserved_and_rejected_before_git_commands(self):
        checkpoint = self.git_capture()
        self.interrupt_receipt(checkpoint)
        extra = self.destination / '.git' / 'hooks' / 'synthetic-user-hook'
        extra.parent.mkdir(exist_ok=True)
        extra.write_bytes(b'Synthetic user metadata to preserve')
        with mock.patch.object(module, 'git', side_effect=AssertionError('Changed metadata must be checked before invoking Git')):
            self.assert_review(checkpoint)
        self.assertEqual(b'Synthetic user metadata to preserve', extra.read_bytes())

    def test_partial_file_effect_is_visible_and_never_replayed(self):
        checkpoint = self.capture()
        original = Path.open

        def interrupt(path, mode='r', *args, **kwargs):
            if path == self.destination / 'nested' / 'notes.txt' and mode == 'xb':
                raise OSError('Synthetic second-file interruption')
            return original(path, mode, *args, **kwargs)

        with mock.patch.object(Path, 'open', new=interrupt):
            with self.assertRaises(OSError):
                self.core.restore(checkpoint['checkpoint_id'], self.destination)
        self.assertEqual('APPLYING', self.operation()['status'])
        self.assertEqual('UNKNOWN', self.operation()['effect_state'])
        first = (self.destination / 'first.bin').read_bytes()
        self.assert_review(checkpoint)
        self.assertEqual(first, (self.destination / 'first.bin').read_bytes())
        self.assertFalse((self.destination / 'nested' / 'notes.txt').exists())

    def test_unknown_complete_effect_without_durable_fingerprint_is_not_replayed(self):
        checkpoint = self.capture()
        original = self.core.store.put

        def interrupt(collection, key, value):
            if collection == 'operations' and value.get('status') == 'EFFECT_APPLIED':
                raise OSError('Synthetic effect-journal interruption')
            return original(collection, key, value)

        with mock.patch.object(self.core.store, 'put', side_effect=interrupt):
            with self.assertRaises(OSError):
                self.core.restore(checkpoint['checkpoint_id'], self.destination)
        self.assertEqual('APPLYING', self.operation()['status'])
        self.assertTrue((self.destination / 'nested' / 'notes.txt').exists())
        self.assert_review(checkpoint)

    def test_intent_failure_has_no_filesystem_effect(self):
        checkpoint = self.capture()
        with mock.patch.object(self.core.store, 'put', side_effect=OSError('Synthetic intent failure')):
            with self.assertRaises(OSError):
                self.core.restore(checkpoint['checkpoint_id'], self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual([], self.core.store.list('operations'))

    def test_prepared_intent_without_effect_can_continue(self):
        checkpoint = self.capture()
        original = self.core.store.put

        def interrupt(collection, key, value):
            if collection == 'operations' and value.get('status') == 'APPLYING':
                raise OSError('Synthetic interruption before effect')
            return original(collection, key, value)

        with mock.patch.object(self.core.store, 'put', side_effect=interrupt):
            with self.assertRaises(OSError):
                self.core.restore(checkpoint['checkpoint_id'], self.destination)
        self.assertEqual('PREPARED', self.operation()['status'])
        self.assertFalse(self.destination.exists())
        self.assertTrue(Core(self.project).restore(checkpoint['checkpoint_id'], self.destination)['restored'])
        self.assertEqual(1, len(self.core.store.list('operations')))

    def test_unknown_operation_protocol_is_rejected_even_after_completion(self):
        checkpoint = self.capture()
        self.core.restore(checkpoint['checkpoint_id'], self.destination)
        original = self.operation()
        for field, value in (('restore_protocol', 999), ('operation_protocol', 999), ('restore_protocol', True)):
            with self.subTest(field=field, value=value):
                self.core.store.put('operations', original['operation_id'], {**original, field: value})
                self.assert_review(checkpoint, 'OPERATION_PROTOCOL_UNSUPPORTED')
        self.core.store.put('operations', original['operation_id'], original)

    def test_changed_checkpoint_cannot_reuse_existing_restore(self):
        checkpoint = self.capture()
        self.interrupt_receipt(checkpoint)
        self.core.store.put('checkpoints', checkpoint['checkpoint_id'], {**checkpoint, 'next_step': 'Changed source record'})
        self.assert_review(checkpoint)

    def test_legacy_checkpoint_and_plain_restore_without_git(self):
        checkpoint = self.capture()
        checkpoint.pop('total_layer_bytes')
        self.core.store.put('checkpoints', checkpoint['checkpoint_id'], checkpoint)
        with mock.patch.dict(os.environ, {'PATH': ''}):
            result = self.core.restore(checkpoint['checkpoint_id'], self.destination)
        self.assertTrue(result['restored'])
        self.assertFalse(result['synthetic_git_baseline'])

    def test_existing_target_without_intent_is_not_claimed_even_if_bytes_match(self):
        checkpoint = self.capture()
        shutil.copytree(self.author, self.destination)
        with self.assertRaises(GovernanceError) as failure:
            self.core.restore(checkpoint['checkpoint_id'], self.destination)
        self.assertEqual('RESTORE_NOT_EMPTY', failure.exception.code)
        self.assertEqual([], self.core.store.list('operations'))
        self.assertEqual([], self.restored_events())

    def test_missing_or_changed_completed_receipt_is_not_silently_recreated(self):
        checkpoint = self.capture()
        result = self.core.restore(checkpoint['checkpoint_id'], self.destination)
        receipt = self.core.store.get('restore_receipts', result['operation_id'])
        self.core.store.put('restore_receipts', result['operation_id'], {**receipt, 'effect_sha256': 'different'})
        self.assert_review(checkpoint)


if __name__ == '__main__':
    unittest.main()
