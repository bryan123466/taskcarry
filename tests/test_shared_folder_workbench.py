"""Synthetic shared-directory routing, compatibility, and effect recovery."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from taskcarry.api import invoke
from taskcarry.connection import Connection
from taskcarry.core import Core
from taskcarry.integration import Integration
from taskcarry.store import GovernanceError
from taskcarry import setup, shared_workbench as shared
from taskcarry.workbench import Workbench, canonical, digest_bytes, git_snapshot


class SharedFolderWorkbenchTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / 'validation/local/shared-folder-workbench-tests'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-', dir=parent)
        self.base = Path(self.temp.name)
        self.control = self.base / 'control'
        Core.initialize(self.control, name='Synthetic shared directory')
        self.engine = Workbench(self.control)
        self.worker = self.base / 'worker'
        self.worker.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic User')
        self.git('config', 'user.email', 'synthetic@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        (self.worker / '.gitignore').write_text('.local/\n.codex/\n.taskcarry/\n.agents/\n', encoding='utf-8')
        (self.worker / 'source.txt').write_text('committed\n', encoding='utf-8')
        self.git('add', '--', '.gitignore', 'source.txt')
        self.git('commit', '-m', 'Synthetic initial project')
        (self.worker / 'source.txt').write_text('staged\n', encoding='utf-8')
        self.git('add', '--', 'source.txt')
        (self.worker / 'source.txt').write_text('unstaged\n', encoding='utf-8')
        (self.worker / 'notes.txt').write_text('untracked notes\n', encoding='utf-8')
        (self.worker / '.codex').mkdir()
        self.config = self.worker / '.codex/config.toml'
        self.config.write_bytes(b'developer_instructions = "Keep professional guidance."\nmodel = "synthetic"\n[mcp_servers.original]\ncommand = "existing"\n')
        Integration(self.control).workspace('shared', str(self.worker))
        for task in ('software', 'algorithm'):
            self.engine.task(task, title='Original ' + task)
        self.view = self.freeze('Initial guidance')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.worker), *args],
                                       stderr=subprocess.DEVNULL, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))

    def freeze(self, text):
        return self.engine.workbench('freeze', body=text, sources=[{'source_id':'synthetic-rules', 'revision':text}])

    def target(self, thread='original-software', task='software', writes=None):
        return {'workspace':'shared', 'task_id':task, 'thread_id':thread, 'host':'codex',
                'code_assessment':{'status':'NO_CODE_DEPENDENCY', 'reason':'Synthetic navigation.'},
                'writes': writes or []}

    def install(self, directory=True):
        return setup.configure(self.control, mode='install', target=self.worker, workspace='shared',
                               **({'binding_mode':'directory'} if directory else {'task_id':'software'}))

    def plan(self, targets=None):
        return self.engine.workbench('plan', routing='shared', view_id=self.view['view_id'],
                                     targets=targets or [self.target(), self.target('original-algorithm','algorithm')])

    def execute(self, plan):
        return self.engine.workbench('execute', plan_id=plan['plan_id'])

    def consume(self, plan, target):
        evidence = self.control / (target['thread_id'] + '.json')
        evidence.write_bytes(b'{"synthetic":"reviewed fixture, not native host evidence"}\n')
        return self.engine.workbench('consume', proof={**{k:target[k] for k in ('workspace','task_id','thread_id')},
            'plan_id':plan['plan_id'], 'view_id':self.view['view_id'], 'source_id':self.engine.source()['source_id'],
            'turn_id':'synthetic-turn', 'evidence_path':evidence.name, 'evidence_sha256':digest_bytes(evidence.read_bytes()),
            'reviewer':'synthetic test', 'observed_at':'2026-01-01T00:00:00Z'})

    def another_workspace(self):
        original = self.worker
        self.worker = self.base/'another'
        self.worker.mkdir()
        try:
            self.git('init','-b','main')
            self.git('config','user.name','Synthetic User')
            self.git('config','user.email','synthetic@example.invalid')
            (self.worker/'.gitignore').write_text('.codex/\n.taskcarry/\n.agents/\n',encoding='utf-8')
            self.git('add','--','.gitignore')
            self.git('commit','-m','Another synthetic project')
            Integration(self.control).workspace('another',str(self.worker))
            return self.worker
        finally:
            self.worker = original

    def test_shared_connection_preserves_config_git_wip_and_exact_chat_routes(self):
        before = (git_snapshot(self.worker), self.git('status','--porcelain=v1'), (self.worker/'source.txt').read_bytes())
        self.install()
        connection = Connection(self.control)
        plan = connection.connect(target=str(self.worker), workspace='shared', binding_mode='directory')
        saved = connection.connect('execute', plan_id=plan['plan']['plan_id'])
        self.assertTrue(saved['file_written'])
        self.assertFalse(connection.connect('execute', plan_id=plan['plan']['plan_id'])['file_written'])
        original_servers = tomllib.loads(self.config.read_text())['mcp_servers']
        p = self.plan()
        self.assertEqual('COMPLETED', self.execute(p)['status'])
        config = tomllib.loads(self.config.read_text())
        self.assertEqual(original_servers, config['mcp_servers'])
        self.assertIn('Keep professional guidance.', config['developer_instructions'])
        self.assertNotIn('original-software', config['developer_instructions'])
        self.assertIn('never choose the first entry', config['developer_instructions'])
        router = json.loads((self.worker/shared.ROUTER).read_text())
        self.assertEqual({'original-software','original-algorithm'}, {r['thread_id'] for r in router['routes']})
        self.assertEqual([], self.engine.workbench('status', workspace='shared', thread_id='unknown-chat')['items'])
        self.assertEqual(before, (git_snapshot(self.worker), self.git('status','--porcelain=v1'), (self.worker/'source.txt').read_bytes()))

    def test_adding_chat_retains_prior_current_and_consumption(self):
        self.install()
        first = self.plan([self.target()])
        self.execute(first)
        self.consume(first,self.target())
        pointer = self.engine.workbench('status',workspace='shared',thread_id='original-software')['items'][0]
        old_bytes = Path(pointer['current_path']).read_bytes()
        self.view = self.freeze('New guidance for another chat')
        second = self.plan([self.target('review-software','software')])
        self.assertEqual('COMPLETED',self.execute(second)['status'])
        current = self.engine.workbench('status',workspace='shared',thread_id='original-software')['items'][0]
        self.assertEqual(first['plan_id'],current['plan_id'])
        self.assertEqual('REVIEWED_EVIDENCE_RECORDED',current['consumer_state'])
        self.assertFalse(current['finalization_pending'])
        self.assertEqual(old_bytes,Path(current['current_path']).read_bytes())
        self.assertEqual('SUPERSEDED',self.execute(first)['results'][0]['status'])

    def test_original_chat_task_cannot_be_rebound(self):
        self.install()
        self.execute(self.plan([self.target()]))
        before = (self.worker/shared.ROUTER).read_bytes()
        with self.assertRaises(GovernanceError) as caught:
            self.plan([self.target(task='algorithm')])
        self.assertEqual('WORKBENCH_BINDING_MISMATCH',caught.exception.code)
        self.assertEqual(before,(self.worker/shared.ROUTER).read_bytes())

    def test_legacy_original_chat_cannot_be_stolen_by_another_shared_workspace(self):
        self.install(directory=False)
        old = self.engine.workbench('plan',view_id=self.view['view_id'],targets=[self.target()])
        self.execute(old)
        other = self.another_workspace()
        setup.configure(self.control,mode='install',target=other,workspace='another',binding_mode='directory')
        target = dict(self.target(task='algorithm'),workspace='another')
        with self.assertRaises(GovernanceError) as caught:
            self.plan([target])
        self.assertEqual('WORKBENCH_BINDING_MISMATCH',caught.exception.code)
        self.assertFalse((other/shared.ROUTER).exists())
        self.assertEqual('software',self.engine.workbench('status',workspace='shared')['items'][0]['task_id'])

    def test_shared_original_chat_cannot_be_stolen_by_legacy_publication(self):
        self.install()
        self.execute(self.plan([self.target()]))
        self.another_workspace()
        target = dict(self.target(task='algorithm'),workspace='another')
        with self.assertRaises(GovernanceError) as caught:
            self.engine.workbench('plan',view_id=self.view['view_id'],targets=[target])
        self.assertEqual('WORKBENCH_BINDING_MISMATCH',caught.exception.code)

    def conflicting_plans(self):
        self.install(directory=False)
        other = self.another_workspace()
        setup.configure(self.control,mode='install',target=other,workspace='another',binding_mode='directory')
        legacy = self.engine.workbench('plan',view_id=self.view['view_id'],targets=[self.target()])
        shared_plan = self.plan([dict(self.target(task='algorithm'),workspace='another')])
        return legacy,shared_plan,other

    def test_shared_execute_rechecks_identity_claimed_after_planning(self):
        legacy,shared_plan,other = self.conflicting_plans()
        self.assertEqual('COMPLETED',self.execute(legacy)['status'])
        self.assertEqual('PARTIAL',self.execute(shared_plan)['status'])
        self.assertFalse((other/shared.ROUTER).exists())

    def test_legacy_execute_rechecks_identity_claimed_after_planning(self):
        legacy,shared_plan,other = self.conflicting_plans()
        before = self.config.read_bytes()
        self.assertEqual('COMPLETED',self.execute(shared_plan)['status'])
        self.assertEqual('PARTIAL',self.execute(legacy)['status'])
        self.assertEqual(before,self.config.read_bytes())

    def test_retained_legacy_consumption_is_historical_after_shared_upgrade(self):
        self.install(directory=False)
        legacy = self.engine.workbench('plan',view_id=self.view['view_id'],targets=[self.target()])
        self.execute(legacy)
        self.assertTrue(self.consume(legacy,self.target())['current_view'])
        old_view = self.view
        self.install()
        self.view = self.freeze('New shared current view')
        shared_plan = self.plan([self.target()])
        self.execute(shared_plan)
        self.view = old_view  # Re-present the exact original historical proof.
        historical = self.consume(legacy,self.target())
        self.assertFalse(historical['current_view'])
        self.assertEqual('REVIEWED_EVIDENCE_RECORDED',historical['consumer_state'])
        self.assertEqual(shared_plan['plan_id'],self.engine.workbench('status',workspace='shared',thread_id='original-software')['items'][0]['plan_id'])

    def test_missing_registered_chat_pointer_is_not_permission_to_rebind(self):
        self.install()
        self.execute(self.plan([self.target()]))
        pointer = self.engine.workbench('status',workspace='shared',thread_id='original-software')['items'][0]
        Path(pointer['current_path']).unlink()
        with self.assertRaises(GovernanceError):
            self.plan([self.target()])
        self.assertEqual('UNVERIFIED',self.engine.workbench('status',workspace='shared',thread_id='original-software')['items'][0]['state'])

    def test_missing_legacy_mirror_retains_identity_and_exact_old_plan_repairs_it(self):
        self.install(directory=False)
        legacy = self.engine.workbench('plan',view_id=self.view['view_id'],targets=[self.target()])
        self.execute(legacy)
        pointer = self.engine.workbench('status',workspace='shared')['items'][0]
        old = Path(pointer['current_path']).read_bytes()
        Path(pointer['current_path']).unlink()
        other = self.another_workspace()
        setup.configure(self.control,mode='install',target=other,workspace='another',binding_mode='directory')
        with self.assertRaises(GovernanceError) as caught:
            self.plan([dict(self.target(task='algorithm'),workspace='another')])
        self.assertEqual('WORKBENCH_BINDING_MISMATCH',caught.exception.code)
        self.assertEqual('COMPLETED',self.execute(legacy)['status'])
        self.assertEqual(old,Path(pointer['current_path']).read_bytes())

    def test_shared_public_contract_uses_the_existing_engine_and_tools(self):
        self.install()
        plan = invoke(self.control,'connect',{'action':'plan','target':str(self.worker),
                      'workspace':'shared','binding_mode':'directory'})
        invoke(self.control,'connect',{'action':'execute','plan_id':plan['plan']['plan_id']})
        publication = invoke(self.control,'workbench',{'action':'plan','routing':'shared',
                             'view_id':self.view['view_id'],'targets':[self.target()]})
        invoke(self.control,'workbench',{'action':'execute','plan_id':publication['plan_id']})
        result = invoke(self.control,'workbench',{'action':'status','workspace':'shared','thread_id':'original-software'})
        self.assertEqual('software',result['items'][0]['task_id'])
        from taskcarry.mcp import tools_list
        contracts = {tool['name']:tool['inputSchema']['properties'] for tool in tools_list()}
        self.assertEqual(['task','directory'],contracts['taskcarry_connect']['binding_mode']['enum'])
        self.assertIn('thread_id',contracts['taskcarry_workbench'])
        self.assertIn('routing',contracts['taskcarry_workbench'])

    def test_directory_mode_requires_explicit_workspace_and_excludes_task(self):
        for extra in ({}, {'workspace':'shared','task_id':'software'}):
            with self.assertRaises(setup.SetupError):
                setup.configure(self.control,mode='install',target=self.worker,binding_mode='directory',**extra)
        self.assertFalse((self.worker/'.taskcarry/setup-manifest.json').exists())

    def test_directory_setup_interruption_resumes_same_intent(self):
        real = setup.atomic_write
        def interrupt(path, content):
            real(path,content)
            if path.name == 'workbench.json':
                raise RuntimeError('synthetic interruption after effect')
        with patch.object(setup,'atomic_write',side_effect=interrupt):
            with self.assertRaises(RuntimeError):
                self.install()
        intent = json.loads((self.worker/'.taskcarry/setup-intent.json').read_text())
        self.assertEqual(2,intent['manifest_after']['format'])
        self.assertTrue(self.install()['resumed'])
        self.assertFalse((self.worker/'.taskcarry/setup-intent.json').exists())
        self.assertEqual('COMPLETED',self.execute(self.plan())['status'])

    def test_legacy_upgrade_preserves_bytes_and_blocks_old_plan_replay(self):
        self.install(directory=False)
        old = self.engine.workbench('plan',view_id=self.view['view_id'],targets=[self.target()])
        self.assertEqual('COMPLETED',self.execute(old)['status'])
        pointer = self.engine.workbench('status',workspace='shared')['items'][0]
        old_files = {name:(self.worker/name).read_bytes() for name in (
            '.taskcarry/setup-manifest.json','.taskcarry/workbench.json','.taskcarry/workbench.md','.codex/config.toml')}
        history = {name:p.read_bytes() for name,p in [('pointer',Path(pointer['current_path'])),('plan',Path(old['plan_path']))]}
        self.install()
        manifest = json.loads((self.worker/'.taskcarry/setup-manifest.json').read_text())
        previous = manifest['previous_setup']
        archive = self.engine.store.get(previous['collection'],previous['key'])
        self.assertEqual(canonical(archive),(self.worker/previous['path']).read_bytes())
        for name,content in old_files.items():
            self.assertEqual(content,base64.b64decode(archive['files'][name]['bytes']))
        with self.assertRaises(GovernanceError):
            self.plan([self.target('new-chat','algorithm')])
        new = self.plan()
        self.assertEqual('COMPLETED',self.execute(new)['status'])
        config,router = self.config.read_bytes(),(self.worker/shared.ROUTER).read_bytes()
        self.assertEqual('PARTIAL',self.execute(old)['status'])
        self.assertEqual((config,router),(self.config.read_bytes(),(self.worker/shared.ROUTER).read_bytes()))
        self.assertEqual(history['pointer'],Path(pointer['current_path']).read_bytes())
        self.assertEqual(history['plan'],Path(old['plan_path']).read_bytes())
        with self.assertRaises(setup.SetupError):
            self.install(directory=False)

    def test_group_effect_before_receipt_resumes_without_replaying_file_writes(self):
        self.install()
        plan = self.plan()
        real = shared.atomic_write
        def interrupt(path,content):
            real(path,content)
            if path == self.config:
                raise RuntimeError('synthetic stop after final directory effect')
        with patch.object(shared,'atomic_write',side_effect=interrupt):
            with self.assertRaises(RuntimeError):
                self.execute(plan)
        config,router = self.config.read_bytes(),(self.worker/shared.ROUTER).read_bytes()
        def only_finalize(path,content):
            self.assertNotEqual(path,self.config)
            self.assertNotEqual(path,self.worker/shared.ROUTER)
            real(path,content)
        with patch.object(shared,'atomic_write',side_effect=only_finalize):
            self.assertEqual('COMPLETED',self.execute(plan)['status'])
        self.assertEqual((config,router),(self.config.read_bytes(),(self.worker/shared.ROUTER).read_bytes()))
        self.assertEqual(2,len(self.engine.workbench('status',workspace='shared')['items']))

    def test_conversion_rejects_concurrent_manifest_change_before_archiving(self):
        self.install(directory=False)
        original = setup.preview
        path = self.worker/'.taskcarry/setup-manifest.json'
        old_binding = (self.worker/'.taskcarry/workbench.json').read_bytes()
        def change_after_preview(*args,**kwargs):
            result = original(*args,**kwargs)
            value = json.loads(path.read_text())
            value['installation_id'] = 'f' * 32
            path.write_bytes(setup.encoded(value))
            return result
        with patch.object(setup,'preview',side_effect=change_after_preview):
            with self.assertRaises(setup.SetupError) as caught:
                self.install()
        self.assertEqual('SETUP_MANIFEST_CHANGED',caught.exception.code)
        self.assertEqual('f' * 32,json.loads(path.read_text())['installation_id'])
        self.assertEqual(old_binding,(self.worker/'.taskcarry/workbench.json').read_bytes())
        self.assertEqual([],self.engine.store.list('workbench_setup_history'))
        self.assertFalse((self.worker/'.taskcarry/setup-history').exists())

    def test_completed_retry_never_overwrites_user_restored_preimage(self):
        self.install()
        before = self.config.read_bytes()
        plan = self.plan()
        self.execute(plan)
        self.config.write_bytes(before)
        result = self.execute(plan)
        self.assertEqual('PARTIAL',result['status'])
        self.assertEqual(2,len(result['results']))
        self.assertTrue(all(r['status']=='CONFLICT' for r in result['results']))
        self.assertEqual(before,self.config.read_bytes())

    def test_pending_pointer_finalization_can_resume_without_duplicate_receipts(self):
        self.install()
        plan = self.plan()
        # Instances share the same Store class but not the same object; intercept its method.
        cls = type(self.engine.store)
        original = cls.put
        def interrupt(store,collection,key,value):
            if collection == 'workbench_directory_current':
                raise RuntimeError('synthetic stop before directory finalization')
            return original(store,collection,key,value)
        with patch.object(cls,'put',new=interrupt):
            with self.assertRaises(RuntimeError):
                self.execute(plan)
        receipts = self.engine.store.list('workbench_receipts')
        self.assertEqual(2,len(receipts))
        self.assertEqual('COMPLETED',self.execute(plan)['status'])
        self.assertEqual(receipts,self.engine.store.list('workbench_receipts'))
        self.assertTrue(all(not r['finalization_pending'] for r in self.engine.workbench('status',workspace='shared')['items']))

    def test_other_control_and_workspace_alias_cannot_replace_shared_binding(self):
        self.install()
        Integration(self.control).workspace('alias',str(self.worker))
        with self.assertRaises(setup.SetupError):
            setup.configure(self.control,mode='install',target=self.worker,workspace='alias',binding_mode='directory')
        other = self.base/'other-control'
        Core.initialize(other,name='Another synthetic control')
        Integration(other).workspace('shared',str(self.worker))
        with self.assertRaises(setup.SetupError):
            setup.configure(other,mode='install',target=self.worker,workspace='shared',binding_mode='directory')

    def test_standby_rejects_shared_mutations_without_target_effects(self):
        self.install()
        plan = self.plan()
        old = self.engine.store.get('config','project')
        with self.engine.store.transaction():
            self.engine.store.put('config','project',dict(old,recovery_writer_state='standby'))
        before = {str(p.relative_to(self.worker)):p.read_bytes() for p in self.worker.rglob('*') if p.is_file() and '.git' not in p.parts}
        for operation in (lambda:self.plan(),lambda:self.execute(plan),lambda:self.install()):
            with self.assertRaises(GovernanceError) as caught:
                operation()
            self.assertEqual('RECOVERY_STANDBY',caught.exception.code)
        after = {str(p.relative_to(self.worker)):p.read_bytes() for p in self.worker.rglob('*') if p.is_file() and '.git' not in p.parts}
        self.assertEqual(before,after)


if __name__ == '__main__':
    unittest.main()
