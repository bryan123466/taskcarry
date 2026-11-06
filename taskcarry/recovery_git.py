"""Exact selected history plus logical index and regular-file working layers."""
import copy
import os
from pathlib import Path
import subprocess

from .core import read_file_bytes, validate_relative_path
from .store import GovernanceError
from .recovery_files import MAX_BYTES, MAX_FILE, MAX_FILES, digest, encoded, normal, put, get, mode, safe, atomic


def host_entry(path):
    name = path.casefold()
    return (name in ('.codex/config.toml', '.mcp.json', '.claude/settings.json')
            or name.startswith('.codex/automations/') and name.endswith('/automation.toml'))


def quarantine(path):
    return '.taskcarry-disabled-host/' + path


def git(root, *args, data=None, check=True):
    environment = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    try:
        result = subprocess.run(['git', '--literal-pathspecs', '-c', 'core.hooksPath=' + os.devnull,
                                 '-c', 'core.autocrlf=false', '-c', 'core.longpaths=true', '-c', 'commit.gpgSign=false', '-C', str(root), *args],
                                input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=environment, timeout=120, check=False)
    except FileNotFoundError as exc:
        raise GovernanceError('GIT_UNAVAILABLE', 'Git is required for selected Git recovery components.') from exc
    except subprocess.TimeoutExpired as exc:
        raise GovernanceError('GIT_TIMEOUT', 'The bounded recovery Git operation timed out.') from exc
    if check and result.returncode:
        raise GovernanceError('RECOVERY_GIT', 'Git recovery operation failed.',
                              {'command': args[0], 'stderr': result.stderr.decode('utf-8', 'replace')[:2000]})
    return result.stdout


def decode(data):
    try:
        return data.decode('utf-8')
    except UnicodeError as exc:
        raise GovernanceError('RECOVERY_PATH_ENCODING', 'This portable recovery supports UTF-8 Git paths.') from exc


def observe(root, requested_refs=None):
    root = normal(root)
    if normal(decode(git(root, 'rev-parse', '--show-toplevel')).strip()) != root:
        raise GovernanceError('RECOVERY_GIT_ROOT', 'Select an actual Git worktree root.')
    head = decode(git(root, 'rev-parse', '--verify', 'HEAD', check=False)).strip()
    if not head:
        raise GovernanceError('RECOVERY_GIT_UNBORN', 'Commit the initial Git baseline before history recovery; plain files can be preserved separately.')
    branch = decode(git(root, 'symbolic-ref', '--quiet', 'HEAD', check=False)).strip() or None
    all_refs, all_symbolic = {}, {}
    for line in decode(git(root, 'for-each-ref', '--format=%(refname) %(objectname) %(symref)')).splitlines():
        name, oid, symbolic = line.split(' ', 2)
        all_refs[name] = oid
        if symbolic:
            all_symbolic[name] = symbolic
    names = sorted(all_refs) if requested_refs is None else sorted(set(requested_refs))
    if len(names) > 256 or any(name != 'HEAD' and name not in all_refs for name in names):
        raise GovernanceError('RECOVERY_REFS', 'Select at most 256 existing exact refs or HEAD.')
    refs = {name: all_refs[name] for name in names if name != 'HEAD'}
    pending = list(refs)
    while pending:
        name = pending.pop()
        target = all_symbolic.get(name)
        if target and target not in refs:
            if target not in all_refs or len(refs) >= 256:
                raise GovernanceError('RECOVERY_REFS', 'Selected symbolic refs require a bounded available target chain.')
            refs[target] = all_refs[target]
            pending.append(target)
    # HEAD and its current branch are necessary dependencies, always explicit in the plan.
    if branch:
        refs[branch] = head
    entries = []
    index = git(root, 'ls-files', '--stage', '-z')
    for row in index.split(b'\0'):
        if not row:
            continue
        prefix, name = row.split(b'\t', 1)
        file_mode, oid, stage = prefix.decode('ascii').split()
        path = decode(name)
        validate_relative_path(root, path)
        if file_mode not in ('100644', '100755') or stage != '0':
            raise GovernanceError('RECOVERY_INDEX_UNSUPPORTED', 'Resolve unmerged, symlink or submodule entries before this regular-file recovery.', {'path': path})
        entries.append({'path': path, 'mode': file_mode, 'oid': oid})
    flags = git(root, 'ls-files', '-v', '-z')
    if any(row and row[:1] != b'H' for row in flags.split(b'\0')):
        raise GovernanceError('RECOVERY_INDEX_FLAGS', 'Sparse, assume-unchanged or special index flags require a separate reviewed export.')
    if len(entries) > MAX_FILES:
        raise GovernanceError('RECOVERY_BUDGET', 'The selected Git index exceeds the file-count budget.')
    unknown = [decode(x) for x in git(root, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if x]
    return {'head': head, 'branch': branch, 'refs': refs,
            'symbolic_refs': {name: target for name, target in all_symbolic.items() if name in refs},
            'excluded_refs': sorted(set(all_refs) - set(refs)), 'index': entries,
            'object_format': decode(git(root, 'rev-parse', '--show-object-format')).strip(),
            'untracked': sorted(unknown), 'index_fingerprint': digest(index)}


def files(root, paths):
    if len(paths) > MAX_FILES or len({p.casefold() for p in paths}) != len(paths):
        raise GovernanceError('RECOVERY_BUDGET', 'File selections must be bounded and case-portably unique.')
    result, total = [], 0
    for name in sorted(paths):
        path = validate_relative_path(root, name)
        if path.exists():
            data = read_file_bytes(path, MAX_FILE)
            total += len(data)
            if total > MAX_BYTES:
                raise GovernanceError('RECOVERY_BUDGET', 'Working files exceed the selected byte budget.')
            result.append({'path': name, 'sha256': digest(data), 'size': len(data), 'mode': mode(path)})
        else:
            result.append({'path': name, 'missing': True})
    return result


def inventory(root, kind, paths, refs=None):
    result = {'kind': kind, 'source': str(normal(root))}
    if kind == 'git':
        observation = observe(root, refs)
        # Index includes additions. HEAD includes staged deletions whose remaining working bytes matter.
        head_paths = [decode(x) for x in git(root, 'ls-tree', '-r', '--name-only', '-z', observation['head']).split(b'\0') if x]
        selected = sorted(set(head_paths) | {i['path'] for i in observation['index']} | set(paths))
        if any(p.split('/')[0].casefold() == '.taskcarry-disabled-host' for p in selected):
            raise GovernanceError('RECOVERY_RESERVED_PATH', 'The host-quarantine namespace must not collide with selected user files.')
        result.update(git=observation, files=files(root, selected),
                      excluded_untracked=sorted(set(observation['untracked']) - set(paths)))
    else:
        if any(p.split('/')[0].casefold() == '.taskcarry-disabled-host' for p in paths):
            raise GovernanceError('RECOVERY_RESERVED_PATH', 'The host-quarantine namespace must not collide with selected user files.')
        result['files'] = files(root, paths)
    return result


def capture(media, selected, scratch):
    root = normal(selected['source'])
    before = inventory(root, selected['kind'], selected['selected_paths'], selected.get('selected_refs'))
    expected = {k: v for k, v in selected.items() if k not in ('name', 'target', 'selected_paths', 'selected_refs')}
    if before != expected:
        raise GovernanceError('RECOVERY_SOURCE_CHANGED', 'Selected source changed since planning; prepare a fresh plan.')
    result = copy.deepcopy({k: v for k, v in selected.items() if k not in ('selected_paths', 'selected_refs')})
    for item in result['files']:
        if not item.get('missing'):
            data = read_file_bytes(validate_relative_path(root, item['path']), MAX_FILE)
            if digest(data) != item['sha256']:
                raise GovernanceError('RECOVERY_SOURCE_CHANGED', 'A selected file changed during capture.')
            item['object'] = put(media, data)
    if result['kind'] == 'git':
        for entry in result['git']['index']:
            length = int(git(root, 'cat-file', '-s', entry['oid']).strip())
            if length > MAX_FILE:
                raise GovernanceError('RECOVERY_BUDGET', 'Index blob exceeds the selected file limit.')
            entry['object'] = put(media, git(root, 'cat-file', 'blob', entry['oid']))
        scratch.mkdir(parents=True, exist_ok=True)
        bundle = scratch / 'history.bundle'
        git(root, 'bundle', 'create', str(bundle), *result['git']['refs'], 'HEAD')
        result['bundle'] = put(media, read_file_bytes(bundle, MAX_BYTES))
        git(root, 'bundle', 'verify', str(bundle))
    if inventory(root, selected['kind'], selected['selected_paths'], selected.get('selected_refs')) != expected:
        raise GovernanceError('RECOVERY_SOURCE_CHANGED', 'Source changed during capture; no component was sealed.')
    return result


def restore(media, component, destination):
    destination.mkdir(parents=True, exist_ok=False)
    if component['kind'] == 'git':
        info = component['git']
        git(destination, 'init', '--quiet', '--object-format=' + info['object_format'])
        bundle = destination / '.git' / 'recovery.bundle'
        atomic(bundle, get(media, component['bundle']))
        refspecs = ['+' + name + ':' + name for name in info['refs']]
        git(destination, 'fetch', '--quiet', '--no-tags', '--update-head-ok', str(bundle), 'HEAD', *refspecs)
        for name, target in info.get('symbolic_refs', {}).items():
            git(destination, 'symbolic-ref', name, target)
        if info['branch']:
            git(destination, 'symbolic-ref', 'HEAD', info['branch'])
        else:
            git(destination, 'update-ref', '--no-deref', 'HEAD', info['head'])
        git(destination, 'read-tree', '--empty')
        index = []
        for entry in info['index']:
            oid = decode(git(destination, 'hash-object', '-w', '--stdin', data=get(media, entry['object']))).strip()
            if oid != entry['oid']:
                raise GovernanceError('RECOVERY_GIT_OBJECT', 'Restored index object identity differs.')
            index.append((entry['mode'] + ' ' + oid + '\t' + entry['path']).encode('utf-8') + b'\0')
        git(destination, 'update-index', '-z', '--index-info', data=b''.join(index))
        bundle.unlink()
    for item in component['files']:
        path = safe(destination, quarantine(item['path']) if host_entry(item['path']) else item['path'])
        if not item.get('missing'):
            atomic(path, get(media, item['object']))
            if os.name != 'nt':
                path.chmod(0o755 if item['mode'] == '100755' else 0o644)
    verify_effect(component, destination)


def verify_effect(component, destination):
    result = files(destination, [x['path'] for x in component['files']])
    expected = [({'path': row['path'], 'missing': True} if host_entry(row['path']) else
                 {k: v for k, v in row.items() if k != 'object'}) for row in component['files']]
    if result != expected:
        raise GovernanceError('RECOVERY_EFFECT_CHANGED', 'Restored selected working bytes or modes changed; preserved without replay.')
    for row in component['files']:
        if host_entry(row['path']) and not row.get('missing'):
            quarantined = files(destination, [quarantine(row['path'])])[0]
            if {k: v for k, v in quarantined.items() if k != 'path'} != {k: v for k, v in row.items() if k not in ('path', 'object')}:
                raise GovernanceError('RECOVERY_EFFECT_CHANGED', 'A quarantined native-host configuration changed; preserved for review.')
    if component['kind'] == 'git':
        actual = observe(destination, list(component['git']['refs']))
        wanted = component['git']
        index = [{k: v for k, v in row.items() if k != 'object'} for row in wanted['index']]
        if any(actual[k] != wanted[k] for k in ('head', 'branch', 'refs', 'symbolic_refs', 'object_format')) or actual['index'] != index:
            raise GovernanceError('RECOVERY_EFFECT_CHANGED', 'Restored Git history, refs or index changed; preserved without replay.')
        git(destination, 'fsck', '--full', '--no-reflogs')
    return True
