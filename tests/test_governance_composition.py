"""Real on-disk rules and content-bound review, independent of host claims."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from taskcarry.core import Core
from taskcarry.governance import Governance
from taskcarry.store import GovernanceError


class GovernanceCompositionTests(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).resolve().parents[1] / 'validation' / 'local' / 'tests'
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base, prefix='composition-')
        self.root = Path(self.temp.name)
        Core.initialize(self.root)
        self.rules = self.root / 'AGENTS.md'
        self.rules.write_text('User chooses the project scope.\n', encoding='utf-8')
        self.engine = Governance(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def inspect(self):
        return self.engine.governance(rule_paths=['AGENTS.md'])

    def record(self, found, **extra):
        return self.engine.governance(mode='record', rule_paths=['AGENTS.md'], record_id='current',
                                      expected_fingerprint=found['fingerprint'],
                                      evidence_refs=['synthetic:native-review'], **extra)

    def test_inspect_preserves_rules_and_records(self):
        before = self.rules.read_bytes()
        with patch.object(self.engine.store, 'put', side_effect=AssertionError('read wrote state')):
            first, second = self.inspect(), self.inspect()
        self.assertEqual(first, second)
        self.assertEqual(self.rules.read_bytes(), before)
        self.assertFalse(first['host_loading_verified'])
        self.assertEqual(first['composition']['user_rules'][0]['origin'], 'user_project')

    def test_review_is_idempotent_and_not_host_reload(self):
        found = self.inspect()
        saved = self.record(found)
        again = self.record(found)
        self.assertFalse(saved['reused'])
        self.assertTrue(again['reused'])
        self.assertEqual(saved['review'], again['review'])
        self.assertFalse(saved['review']['host_loading_verified'])
        self.assertFalse(saved['package_upgrade_performed'])

    def test_changed_rule_rejects_old_review_and_retains_old_identity(self):
        first = self.inspect()
        self.record(first)
        self.rules.write_text('A newly confirmed user rule.\n', encoding='utf-8')
        with self.assertRaises(GovernanceError) as raised:
            self.record(first)
        self.assertEqual(raised.exception.code, 'COMPOSITION_CHANGED')
        current = self.inspect()
        with self.assertRaises(GovernanceError) as raised:
            self.record(current)
        self.assertEqual(raised.exception.code, 'REVISION_CONFLICT')
        final = self.record(current, expected_revision=1)
        self.assertEqual(final['review']['revision'], 2)
        self.assertEqual(self.engine.store.get('governance_review_history', 'current.1')['fingerprint'],
                         first['fingerprint'])

    def test_same_version_different_disk_content_has_different_identity(self):
        first = self.inspect()
        altered = dict(first['composition']['core'], source_sha256='f' * 64)
        with patch('taskcarry.governance.runtime_info', return_value={'loaded_runtime': altered}):
            second = self.inspect()
        self.assertNotEqual(first['fingerprint'], second['fingerprint'])

    def test_rule_path_cannot_capture_governance_database(self):
        with self.assertRaises(GovernanceError) as raised:
            self.engine.governance(rule_paths=['.taskcarry/state.sqlite3'])
        self.assertEqual(raised.exception.code, 'RESERVED_PATH')


if __name__ == '__main__':
    unittest.main()
