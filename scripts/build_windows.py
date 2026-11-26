"""Add pinned Windows runtimes to an already source-verified product ZIP.

Supply the two upstream archives in --runtime-dir. No download or installation
occurs here. Upstream licenses remain in the archive alongside each runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from taskcarry import __version__
from taskcarry.updates import build_release_manifest, validate_manifest

RUNTIME = 'TaskCarry/toolkit/runtime/'
ASSETS = {
    'python-3.14.9-embed-amd64.zip': ('python', '3c01d7cfc666f746a6f064f60fb2156ab0ec464d3d738ab796371a46a9bb24a2',
        'https://www.python.org/downloads/release/python-3149/'),
    'MinGit-2.56.1-64-bit.zip': ('git', '4a92850b6e917da4fd010669b614b55dccf5b0ec333a534cc4be4700dfefdafd',
        'https://github.com/git-for-windows/git/releases/tag/v2.56.1.windows.1'),
}
BOOTSTRAP = '''"""Start TaskCarry with the Git shipped next to this interpreter."""
from pathlib import Path
import os
import sys

def main():
    git_dir = Path(sys.executable).resolve().parents[1] / "git" / "cmd"
    if not (git_dir / "git.exe").is_file():
        raise SystemExit("Bundled Git is missing. Extract the complete Windows ZIP again.")
    system = Path(os.environ["SystemRoot"])
    os.environ["PATH"] = os.pathsep.join(str(path) for path in (git_dir, system / "System32", system))
    os.environ["NoDefaultCurrentDirectoryInExePath"] = "1"
    for name in ("PYTHONHOME", "PYTHONPATH", "GIT_EXEC_PATH"):
        os.environ.pop(name, None)
    from taskcarry.cli import main as run
    return run()

if __name__ == "__main__":
    raise SystemExit(main())
'''

GUIDE = '''# Windows x64

在 AI 工具中打开解压后的 TaskCarry 文件夹，按 [START_HERE](START_HERE.md) 建立管家对话。本包内含 Python 与 MinGit；如果管家提示缺少 Git、Python 或登录工具，安装缺少的工具后继续。

Open the extracted TaskCarry folder in your AI app and follow [START_HERE](START_HERE.md). Python and MinGit are included. If the manager reports a missing Git, Python or sign-in tool, install it and continue.

在 AI 工具中開啟解壓縮後的 TaskCarry 資料夾，依 [START_HERE](START_HERE.md) 建立管家對話。套件內含 Python 與 MinGit；如果管家提示缺少 Git、Python 或登入工具，安裝缺少的工具後繼續。

## CLI

`taskcarry.cmd --project "<project directory>" status`

## MCP · stdio

| Command | Arguments |
| --- | --- |
| Absolute path to `toolkit/runtime/python/python.exe` | `-I`, `-B`, `-X`, `utf8`, `-m`, `taskcarry_portable`, `--project`, absolute project directory, `mcp` |

每项参数单独填写。优先使用本包入口以加载随附 Git。移动文件夹后更新 MCP 中的绝对路径；私有仓库仍使用自己的账号登录。

Enter each argument separately. Use this entrypoint to load bundled Git. After moving the folder, update absolute paths in MCP. Sign in to private repositories with your own account.

各項參數分開填寫。優先使用本套件入口以載入隨附 Git。移動資料夾後更新 MCP 中的絕對路徑；私有儲存庫仍使用自己的帳號登入。

## Third-party notices / 第三方说明 / 第三方說明

TaskCarry code is MIT licensed. The bundled distributions retain their own
licenses, copyright notices and included components:

- [CPython 3.14.9 and source](https://www.python.org/downloads/release/python-3149/): PSF License and included notices in `toolkit/runtime/python/LICENSE.txt`.
- [MinGit 2.56.1 and corresponding release sources](https://github.com/git-for-windows/git/releases/tag/v2.56.1.windows.1): GPLv2 and component licenses, retained in `toolkit/runtime/git/LICENSE.txt` and its accompanying files. [Exact Git for Windows source tree](https://github.com/git-for-windows/git/tree/v2.56.1.windows.1).

The Python path file adds `../site-packages`; the upstream archives are otherwise
retained unchanged. `WINDOWS_MANIFEST.json` records upstream hashes, source
commit, wheel hash and every included file. This distribution does not install
system-wide Python, Git or AI account credentials.
'''

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def insert(members, name, data):
    key = PurePosixPath(name)
    if (not name.startswith('TaskCarry/') or '\\' in name or ':' in name
            or '..' in key.parts or key.as_posix() != name or name in members):
        raise ValueError('Unsafe or duplicate archive member: ' + name)
    members[name] = data

def unpack(members, archive, prefix, embedded=False):
    with ZipFile(archive) as zipped:
        for item in zipped.infolist():
            if item.is_dir():
                continue
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError('Symlink in input archive')
            data = zipped.read(item)
            if embedded and item.filename == 'python314._pth':
                data = data.rstrip() + b'\r\n../site-packages\r\n'
            insert(members, prefix + item.filename, data)

def launcher(arguments):
    return ('@echo off\r\nsetlocal DisableDelayedExpansion\r\n'
            '"%~dp0toolkit\\runtime\\python\\python.exe" -I -B -X utf8 -m taskcarry_portable '
            + arguments + '\r\nexit /b %errorlevel%\r\n').encode('ascii')

def build(product_dir, runtime_dir):
    product_dir, runtime_dir = Path(product_dir).resolve(), Path(runtime_dir).resolve()
    release = validate_manifest(json.loads((product_dir / 'taskcarry-release.json').read_text(encoding='utf-8')))
    if release['version'] != __version__:
        raise ValueError('Product version differs from this builder')
    product = product_dir / f'taskcarry-{__version__}-product.zip'
    wheel = product_dir / f'taskcarry-{__version__}-py3-none-any.whl'
    pins = {row['name']: row for row in release['artifacts']}
    for path in (product, wheel):
        if digest(path.read_bytes()) != pins[path.name]['sha256'] or path.stat().st_size != pins[path.name]['size']:
            raise ValueError('Product input changed: ' + path.name)
    for name, (_, expected, _) in ASSETS.items():
        if digest((runtime_dir / name).read_bytes()) != expected:
            raise ValueError('Upstream runtime hash differs: ' + name)
    output = product_dir / f'TaskCarry-{__version__}-Windows-x64.zip'
    if output.exists():
        raise ValueError('Use a new artifact directory; output already exists')
    members = {}
    unpack(members, product, '')
    unpack(members, wheel, RUNTIME + 'site-packages/')
    for name, (folder, _, _) in ASSETS.items():
        unpack(members, runtime_dir / name, RUNTIME + folder + '/', embedded=folder == 'python')
    insert(members, RUNTIME + 'site-packages/taskcarry_portable.py', BOOTSTRAP.encode('utf-8'))
    insert(members, 'TaskCarry/taskcarry.cmd', launcher('%*'))
    insert(members, 'TaskCarry/taskcarry-mcp.cmd', launcher('--project "%~1" mcp'))
    insert(members, 'TaskCarry/WINDOWS.md', GUIDE.encode('utf-8'))
    entry = 'TaskCarry/START_HERE.md'
    members[entry] = members[entry].replace(b'# TaskCarry\n',
        b'# TaskCarry\n\n[Windows x64: bundled tools](WINDOWS.md)\n', 1)
    manifest_path = f'TaskCarry/toolkit/taskcarry-{__version__}/RELEASE_MANIFEST.json'
    manifest = json.loads(members[manifest_path])
    if manifest['source_commit'] != release['source_commit']:
        raise ValueError('Product source pin differs')
    manifest['first_use_entry'].update(sha256=digest(members[entry]), bytes=len(members[entry]))
    members[manifest_path] = encoded(manifest)
    windows_manifest = {'target': 'Windows x64', 'version': __version__, 'source_commit': release['source_commit'],
        'wheel_sha256': digest(wheel.read_bytes()),
        'upstream': [{'artifact': n, 'sha256': v[1], 'source': v[2]} for n, v in ASSETS.items()],
        'python_layout_change': 'append ../site-packages to python314._pth',
        'files': {name: digest(data) for name, data in sorted(members.items())}}
    insert(members, 'TaskCarry/WINDOWS_MANIFEST.json', encoded(windows_manifest))
    if len({name.casefold() for name in members}) != len(members):
        raise ValueError('Case-colliding archive members')
    for license_name in ('python/LICENSE.txt', 'git/LICENSE.txt'):
        if RUNTIME + license_name not in members:
            raise ValueError('Required upstream license is missing')
    with ZipFile(output, 'x', compression=ZIP_DEFLATED) as zipped:
        for name, data in sorted(members.items()):
            item = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            item.compress_type = ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            zipped.writestr(item, data, compresslevel=4)
    with ZipFile(output) as zipped:
        if sorted(zipped.namelist()) != sorted(members) or any(zipped.read(n) != d for n, d in members.items()):
            raise ValueError('Written archive differs')
    release['artifacts'].append({'name': output.name, 'sha256': digest(output.read_bytes()), 'size': output.stat().st_size})
    release = build_release_manifest(__version__, release['source_commit'], release['artifacts'], release['required_actions'])
    release_path = product_dir / 'taskcarry-release.json'
    release_path.write_bytes(encoded(release))
    assets = [product_dir / row['name'] for row in release['artifacts']] + [release_path]
    (product_dir / 'SHA256SUMS.txt').write_text(''.join(digest(p.read_bytes()) + '  ' + p.name + '\n' for p in assets), encoding='ascii')
    return {'archive': output.name, 'bytes': output.stat().st_size, 'sha256': digest(output.read_bytes()),
            'source_commit': release['source_commit'], 'files': len(members), 'upstream': windows_manifest['upstream']}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product-dir', required=True)
    parser.add_argument('--runtime-dir', required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.product_dir, args.runtime_dir), indent=2))
