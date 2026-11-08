"""Bounded portable byte storage, atomic records and exclusive batch locks."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import uuid

from .core import _linked, read_file_bytes
from .store import GovernanceError

MAX_BYTES = 512 * 1024 * 1024
MAX_FILE = 64 * 1024 * 1024
MAX_FILES = 4096
SHA = re.compile(r'^[0-9a-f]{64}$')


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normal(value):
    p = Path(value).expanduser().absolute()
    if any(_linked(part) for part in (p, *p.parents)):
        raise GovernanceError('RECOVERY_UNSAFE_PATH', 'Linked or reparse paths are not recovery inputs or destinations.')
    return p.resolve()


def relative(value):
    if not isinstance(value, str) or not value:
        raise GovernanceError('RECOVERY_UNSAFE_PATH', 'Use an exact relative file path.')
    p = PurePosixPath(value)
    if (value != p.as_posix() or p.is_absolute() or any(c in value for c in '\\:\0\r\n<>"|?*')
            or any(x in ('.', '..') or x.endswith((' ', '.'))
                   or re.fullmatch(r'(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', x, re.I) for x in p.parts)):
        raise GovernanceError('RECOVERY_UNSAFE_PATH', 'Recovery paths must be portable, relative and traversal-free.')
    return p


def safe(root, name):
    root = normal(root)
    result = normal(root.joinpath(*relative(name).parts))
    if not result.is_relative_to(root):
        raise GovernanceError('RECOVERY_UNSAFE_PATH', 'Recovery path escaped its root.')
    return result


def disjoint(a, b):
    a, b = normal(a), normal(b)
    if a.is_relative_to(b) or b.is_relative_to(a):
        raise GovernanceError('RECOVERY_NOT_INDEPENDENT', 'Recovery media and targets must be independent of their sources.')


def read_json(path, limit=64 * 1024 * 1024):
    data = read_file_bytes(normal(path), limit)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise GovernanceError('RECOVERY_MANIFEST', 'Duplicate JSON member.')
            result[key] = value
        return result
    try:
        value = json.loads(data, object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as exc:
        raise GovernanceError('RECOVERY_MANIFEST', 'Recovery metadata is not valid JSON.') from exc
    return value, digest(data)


def atomic(path, data, *, replace=False):
    path = normal(path)
    if path.exists() and not replace:
        if read_file_bytes(path, max(MAX_FILE, len(data))) != data:
            raise GovernanceError('RECOVERY_CONFLICT', 'Existing immutable recovery bytes differ; preserved for review.', {'path': str(path)})
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.partial')
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists() and not replace:
        if read_file_bytes(path, max(MAX_FILE, len(data))) != data:
            raise GovernanceError('RECOVERY_CONFLICT', 'Concurrent immutable recovery publication differs.')
        temporary.unlink()
        return
    # All cooperating publishers own the batch lock. No partial final file is visible.
    os.replace(temporary, path)


def write_json(path, value, *, replace=False):
    atomic(path, encoded(value), replace=replace)


@contextmanager
def lock(path):
    path = normal(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        stream.seek(0, 2)
        if not stream.tell():
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise GovernanceError('RECOVERY_BUSY', 'This recovery batch is in use.') from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def put(media, data):
    if len(data) > MAX_BYTES:
        raise GovernanceError('RECOVERY_BUDGET', 'Recovery payload exceeds the bounded byte limit.')
    checksum = digest(data)
    atomic(safe(media, 'objects/' + checksum), data)
    return {'sha256': checksum, 'size': len(data)}


def get(media, ref):
    if (not isinstance(ref, dict) or not isinstance(ref.get('sha256'), str) or not SHA.fullmatch(ref['sha256'])
            or type(ref.get('size')) is not int or not 0 <= ref['size'] <= MAX_BYTES):
        raise GovernanceError('RECOVERY_MANIFEST', 'Invalid recovery object reference.')
    path = safe(media, 'objects/' + ref['sha256'])
    try:
        data = read_file_bytes(path, MAX_BYTES)
    except FileNotFoundError as exc:
        raise GovernanceError('RECOVERY_OBJECT_MISSING', 'A required recovery object is missing.', ref) from exc
    if len(data) != ref['size'] or digest(data) != ref['sha256']:
        raise GovernanceError('RECOVERY_OBJECT_MISMATCH', 'A required recovery object has different bytes.', ref)
    return data


def mode(path):
    return '100755' if os.name != 'nt' and path.stat().st_mode & stat.S_IXUSR else '100644'
