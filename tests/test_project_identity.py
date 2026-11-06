"""Portable identities and standby enforcement over observable local state."""
import json
from pathlib import Path
import tempfile
import unittest

from taskcarry.api import invoke
from taskcarry.core import Core
from taskcarry.project_identity import ProjectIdentity
from taskcarry.store import GovernanceError


class ProjectIdentityTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / 'validation/local/identity-tests'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name)
        Core.initialize(self.root)
        self.core = Core(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_new_identity_survives_location_change_with_same_lineage(self):
        import shutil
        self.core.task('draft')
        before = self.core.source()
        destination = self.root / 'isolated-copy'
        shutil.copytree(self.root / '.taskcarry', destination / '.taskcarry')
        copied = Core(destination).source()
        self.assertEqual(before['source_id'], copied['source_id'])
        self.assertNotEqual(before['control'], copied['control'])
        self.assertIn(before['aliases'][0], copied['aliases'])
        self.assertEqual(before, Core.identify(self.root)['source'])

    def test_legacy_read_is_stable_and_explicit_plan_retains_alias(self):
        config = self.core.store.get('config', 'project')
        for key in ('project_id', 'replica_id', 'source_aliases'):
            config.pop(key)
        self.core.store.put('config', 'project', config)
        old = self.core.source()
        events = self.core.store.events()
        service = ProjectIdentity(self.root)
        self.assertEqual('resolved_local_path', service.identity()['source']['identity_scope'])
        self.assertEqual(events, self.core.store.events())
        plan = service.identity('plan')
        self.assertEqual(old, self.core.source())
        result = service.identity('execute', plan_id=plan['plan_id'])
        self.assertIn(old['source_id'], result['source']['aliases'])
        self.assertTrue(service.identity('execute', plan_id=plan['plan_id'])['reused'])

    def test_legacy_plan_rejects_changed_config_without_overwrite(self):
        config = self.core.store.get('config', 'project')
        config.pop('project_id')
        self.core.store.put('config', 'project', config)
        service = ProjectIdentity(self.root)
        plan = service.identity('plan')
        config['name'] = 'Later user change'
        self.core.store.put('config', 'project', config)
        with self.assertRaises(GovernanceError) as error:
            service.identity('execute', plan_id=plan['plan_id'])
        self.assertEqual('IDENTITY_CHANGED', error.exception.code)
        self.assertEqual(config, self.core.store.get('config', 'project'))

    def test_standby_rejects_both_api_and_direct_writes_but_allows_read(self):
        config = self.core.store.get('config', 'project')
        config.update(recovery_writer_state='standby', recovery_restore_id='synthetic-restore')
        self.core.store.put('config', 'project', config)
        before = self.core.store.events()
        for call in (lambda: invoke(self.root, 'task', {'task_id': 'wrong'}),
                     lambda: self.core.task('wrong'),
                     lambda: self.core.store.put('tasks', 'wrong', {})):
            with self.assertRaises(GovernanceError) as error:
                call()
            self.assertEqual('RECOVERY_STANDBY', error.exception.code)
        self.assertEqual('standby', invoke(self.root, 'status')['source']['writer_state'])
        self.assertEqual(before, self.core.store.events())
        with self.core.store.recovery_transition():
            self.core.store.put('config', 'project', {**config, 'recovery_writer_state': 'active'})
        self.core.task('allowed')


if __name__ == '__main__':
    unittest.main()
