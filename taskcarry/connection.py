"""Plan and merge only a generated project MCP block, retaining other settings."""
from __future__ import annotations

import json
from pathlib import Path
import tomllib

from .core import Core, _id, digest_bytes, read_file_bytes
from .setup import atomic_write, check_binding, project_root, read_manifest, safe_target, workbench_binding
from .store import GovernanceError, now


class Connection(Core):
    def _materials(self, root, binding, fragment):
        if safe_target(root, '.taskcarry/setup-intent.json').exists():
            raise GovernanceError('CONNECTION_SETUP_PENDING', 'Finish the existing setup intent before connecting.')
        manifest = read_manifest(root)
        if not manifest.get('server_name'):
            raise GovernanceError('CONNECTION_SETUP_REQUIRED', 'Install and verify setup materials before connecting.')
        check_binding(manifest, None, binding)
        if manifest.get('binding') != binding:
            raise GovernanceError('CONNECTION_BINDING_CHANGED', 'Install setup materials with this exact workbench binding before connecting.')
        if manifest['files'].get('.taskcarry/codex.mcp.toml') != digest_bytes(fragment):
            raise GovernanceError('CONNECTION_FRAGMENT_CHANGED', 'Regenerate or review the modified setup fragment.')
        return manifest

    def _target(self, target, workspace, task_id):
        root = project_root(target or self.root)
        if root == Path.home().resolve() or root.name.casefold() == '.codex':
            raise GovernanceError('PROJECT_CONFIG_REQUIRED', 'Select a project directory, not user-level configuration.')
        if target is not None:
            workbench_binding(self.root, root, workspace, task_id)
        elif workspace is not None or task_id is not None:
            raise GovernanceError('INVALID_ARGUMENT', 'Workbench identity requires its explicit target.')
        return root

    def _merge(self, root, before, fragment, server):
        try:
            config = tomllib.loads(before.decode('utf-8-sig')) if before else {}
            requested = tomllib.loads(fragment.decode('utf-8'))['mcp_servers'][server]
        except (UnicodeError, ValueError, KeyError) as exc:
            raise GovernanceError('CONNECTION_CONFIG_INVALID', 'Preserve the existing file and review its TOML syntax.') from exc
        if not isinstance(config.get('mcp_servers', {}), dict):
            raise GovernanceError('CONNECTION_CONFIG_INVALID', 'mcp_servers must be a TOML table.')
        existing = config.get('mcp_servers', {}).get(server)
        if existing == requested:
            return before
        if existing is None:
            merged = before + (b'\n' if before and not before.endswith(b'\n') else b'') + fragment
        else:
            previous = self.store.get('connections', digest_bytes(str(root).encode()))
            old = (previous or {}).get('fragment', '').encode('utf-8')
            if not old or before.count(old) != 1 or (previous or {}).get('server') != server:
                raise GovernanceError('CONNECTION_CONFLICT', 'The existing service differs from the generated block. '
                                      'Preserve it and review the specific configuration conflict.', {'server': server})
            merged = before.replace(old, fragment, 1)
        try:
            parsed = tomllib.loads(merged.decode('utf-8-sig'))
        except (ValueError, UnicodeError) as exc:
            raise GovernanceError('CONNECTION_CONFLICT', 'This TOML layout cannot accept the generated block additively; '
                                  'preserve the file and review its table layout.') from exc
        check = dict(config)
        check['mcp_servers'] = {**config.get('mcp_servers', {}), server: requested}
        if parsed != check:
            raise GovernanceError('CONNECTION_CONFLICT', 'The merge would change unrelated configuration.')
        return merged

    def connect(self, action='plan', target=None, workspace=None, task_id=None, plan_id=None):
        if action not in ('plan', 'execute', 'status'):
            raise GovernanceError('INVALID_ARGUMENT', 'Use plan, execute or status.')
        if action == 'plan':
            if plan_id is not None:
                raise GovernanceError('INVALID_ARGUMENT', 'A new plan does not take a plan ID.')
            root = self._target(target, workspace, task_id)
            fragment = read_file_bytes(safe_target(root, '.taskcarry/codex.mcp.toml'), max_bytes=65536)
            binding = {'control': str(self.root), 'target': str(root), 'workspace': workspace, 'task_id': task_id} if target is not None else None
            manifest = self._materials(root, binding, fragment)
            server = manifest['server_name']
            try:
                command = tomllib.loads(fragment.decode('utf-8'))['mcp_servers'][server]
                args = command['args']
                if args[:3] != ['-I', '-X', 'utf8'] or args[-3:] != ['--project', str(self.root), 'mcp']:
                    raise ValueError('Incorrect launch binding')
            except (KeyError, TypeError, ValueError, UnicodeError) as exc:
                raise GovernanceError('CONNECTION_BINDING_CHANGED', 'The fragment must isolate the selected package and bind this control.') from exc
            destination = safe_target(root, '.codex/config.toml')
            before = read_file_bytes(destination, max_bytes=1024*1024) if destination.exists() else b''
            with self.store.transaction():
                merged = self._merge(root, before, fragment, server)
                body = {'target': str(root), 'workspace': workspace, 'task_id': task_id,
                        'server': server, 'before': digest_bytes(before), 'after': digest_bytes(merged),
                        'fragment': fragment.decode('utf-8'), 'existed': destination.exists()}
                key = 'connection-' + digest_bytes(json.dumps(body, sort_keys=True).encode())[:24]
                prior = self.store.get('connection_plans', key)
                if prior is None:
                    prior = dict(body, plan_id=key, state='PLANNED', created_at=now())
                    self.store.put('connection_plans', key, prior)
                    self.store.event('connection_planned', {'plan_id': key, 'target': str(root)})
            return self._result(prior)
        if any(value is not None for value in (target, workspace, task_id)):
            raise GovernanceError('INVALID_ARGUMENT', 'Execute the exact saved plan without new target arguments.')
        key = _id(plan_id, 'Connection plan ID')
        with self.store.guard():
            plan = self.store.get('connection_plans', key)
            if not plan:
                raise GovernanceError('PLAN_NOT_FOUND', 'Read an existing connection plan first.')
            if action == 'status':
                return self._result(plan)
            root = self._target(plan['target'] if plan['workspace'] is not None else None,
                                plan['workspace'], plan['task_id'])
            if str(root) != plan['target']:
                raise GovernanceError('CONNECTION_BINDING_CHANGED', 'The saved target binding changed.')
            destination = safe_target(root, '.codex/config.toml')
            current = read_file_bytes(destination, max_bytes=1024*1024) if destination.exists() else b''
            digest = digest_bytes(current)
            if digest == plan['after']:
                written = False
            elif digest == plan['before'] and destination.exists() == plan['existed'] and plan['state'] != 'COMPLETED':
                fragment = plan['fragment'].encode('utf-8')
                live = read_file_bytes(safe_target(root, '.taskcarry/codex.mcp.toml'), max_bytes=65536)
                if live != fragment:
                    raise GovernanceError('CONNECTION_FRAGMENT_CHANGED', 'The setup changed after planning.')
                binding = ({'control': str(self.root), 'target': str(root), 'workspace': plan['workspace'],
                            'task_id': plan['task_id']} if plan['workspace'] is not None else None)
                manifest = self._materials(root, binding, live)
                if manifest['server_name'] != plan['server']:
                    raise GovernanceError('CONNECTION_BINDING_CHANGED', 'The setup service changed after planning.')
                merged = self._merge(root, current, fragment, plan['server'])
                if digest_bytes(merged) != plan['after']:
                    raise GovernanceError('CONNECTION_CONFLICT', 'The planned merge is no longer reproducible.')
                with self.store.transaction():
                    self.store.put('connection_plans', key, dict(plan, state='PREPARED'))
                latest = read_file_bytes(destination, max_bytes=1024*1024) if destination.exists() else b''
                if latest != current or destination.exists() != plan['existed']:
                    raise GovernanceError('CONNECTION_CONFIG_CHANGED', 'The target changed before writing; preserve it.')
                atomic_write(destination, merged)
                written = True
            else:
                raise GovernanceError('CONNECTION_CONFIG_CHANGED', 'Preserve later user edits and prepare a new reviewed plan.')
            if digest_bytes(read_file_bytes(destination, max_bytes=1024*1024)) != plan['after']:
                raise GovernanceError('CONNECTION_CONFIG_CHANGED', 'The target changed while verifying the merge.')
            with self.store.transaction():
                if plan['state'] != 'COMPLETED':
                    plan = dict(plan, state='COMPLETED', completed_at=now())
                    self.store.put('connection_plans', key, plan)
                    self.store.put('connections', digest_bytes(str(root).encode()), plan)
                    self.store.event('connection_saved', {'plan_id': key, 'sha256': plan['after']})
            return dict(self._result(plan), file_written=written)

    @staticmethod
    def _result(plan):
        # Never return unrelated existing configuration, which can contain secrets.
        return {'plan': {k: v for k, v in plan.items() if k != 'fragment'},
                'host_loading_verified': False, 'native_acceptance_verified': False,
                'next_step': 'Trust/reload the target project if required, then call native doctor/status in that window.'}
