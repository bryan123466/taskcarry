"""New public actions use the same engine and retain evidence distinctions."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from taskcarry.api import invoke
from taskcarry.mcp import Server
from taskcarry.setup import configure


class ExtendedInterfaceTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / 'validation/local/tests'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch, prefix='extended-interface-')
        self.root = Path(self.temp.name)
        self.server = Server(self.root)
        self.server.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2025-11-25', 'capabilities': {},
            'clientInfo': {'name': 'synthetic-extended-interface', 'version': '1'}}})

    def tearDown(self):
        self.temp.cleanup()

    def call(self, operation, **args):
        response = self.server.handle({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                                      'params': {'name': 'taskcarry_' + operation, 'arguments': args}})
        self.assertNotIn('error', response, response)
        body = response['result']['structuredContent']
        self.assertTrue(body['ok'], body)
        return body['result']

    def test_identify_works_before_initialization_through_all_surfaces(self):
        expected = invoke(self.root, 'identify')
        self.assertEqual(expected, self.call('identify'))
        result = subprocess.run([sys.executable, '-m', 'taskcarry', '--project', str(self.root), 'identify'],
                                cwd=Path(__file__).resolve().parents[1], text=True,
                                encoding='utf-8', capture_output=True, timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(expected, json.loads(result.stdout)['result'])
        self.assertFalse((self.root / '.taskcarry').exists())

    def test_plain_observation_and_task_context_retain_source_and_revision(self):
        invoke(self.root, 'init')
        self.call('task', task_id='guide', title='Synthetic guide')
        self.call('observe', observation_id='source', workspace=None, task_id='guide',
                  source_ref='synthetic:prior-chat', source_revision='one', summary='Keep human approval')
        first = self.call('context', task_id='guide', limit=1)
        self.assertEqual('Keep human approval', first['items'][0]['record']['summary'])
        self.assertEqual(first['source']['source_id'], first['items'][0]['source_id'])
        second = self.call('context', task_id='guide', limit=1, previous_fingerprint=first['fingerprint'])
        self.assertFalse(second['changed'])
        self.assertFalse(second['effects_executed'])
        self.assertEqual([], self.call('status')['stages'])

    def test_connect_writes_project_config_but_cannot_claim_native_acceptance(self):
        invoke(self.root, 'init')
        configure(self.root, mode='install')
        plan = self.call('connect')['plan']
        self.assertFalse((self.root / '.codex/config.toml').exists())
        saved = self.call('connect', action='execute', plan_id=plan['plan_id'])
        self.assertTrue((self.root / '.codex/config.toml').is_file())
        self.assertFalse(saved['native_acceptance_verified'])
        self.assertFalse(saved['host_loading_verified'])

    def test_check_and_assess_do_not_install_or_claim_latest_when_offline(self):
        import urllib.error
        invoke(self.root, 'init')
        self.call('update_source', channel='rc')
        with patch('taskcarry.updates._fetch_json', side_effect=urllib.error.URLError('synthetic offline')):
            check = self.call('update_check')
        self.assertEqual('UNVERIFIED', check['status'])
        self.assertFalse(check['latest_verified'])
        assessed = self.call('update_assess', check=check, decision='wait', reason='Retry when connected')
        self.assertFalse(assessed['assessment']['installation_performed'])
        self.assertTrue(self.call('update_assess', check=check, decision='wait', reason='Retry when connected')['reused'])

    def test_onboarding_returns_specific_pending_items_and_schedule_is_only_a_plan(self):
        invoke(self.root, 'init')
        scope = {'governance_thread': 'synthetic-governance', 'channel': 'rc',
                 'schedule': {'time': '09:00', 'timezone': 'UTC'},
                 'windows': [{'thread_id': 'synthetic-history', 'mode': 'reference',
                              'source_ref': 'synthetic:history', 'responsibility': 'Prior decisions'}]}
        started = self.call('onboarding', onboarding_id='first-use', action='start', scope=scope)
        self.assertFalse(started['standard_ready'])
        self.assertIn('local_git', started['pending'])
        plan = self.call('schedule_plan', onboarding_id='first-use')
        self.assertFalse(plan['execute'])
        self.assertEqual('synthetic-governance', plan['thread_id'])
        self.assertIn('releases', plan['prompt'])

    def test_governance_review_retains_user_rules_without_installing(self):
        invoke(self.root, 'init')
        (self.root / 'AGENTS.md').write_text('Synthetic confirmed user rules', encoding='utf-8')
        found = self.call('governance', rule_paths=['AGENTS.md'])
        result = self.call('governance', mode='record', rule_paths=['AGENTS.md'], record_id='rules',
                           expected_fingerprint=found['fingerprint'], evidence_refs=['synthetic:review'])
        self.assertEqual(found['fingerprint'], result['review']['fingerprint'])
        self.assertFalse(result['host_loading_verified'])
        self.assertFalse(result['package_upgrade_performed'])


if __name__ == '__main__':
    unittest.main()
