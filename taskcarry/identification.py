"""Inspect a selected state location without creating SQLite journals or locks."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from .store import GovernanceError, _linked


def source(root, config=None):
    root = str(Path(root).expanduser().resolve())
    legacy = 'local-' + hashlib.sha256(os.path.normcase(root).encode('utf-8')).hexdigest()
    if config and config.get('project_id'):
        return {'source_id': config['project_id'], 'control': root,
                'identity_scope': 'persistent_project', 'replica_id': config.get('replica_id'),
                'aliases': list(dict.fromkeys([*config.get('source_aliases', []), legacy])),
                'record_identity': ['source_id', 'collection', 'local_id'],
                'writer_state': config.get('recovery_writer_state', 'active')}
    return {'source_id': legacy,
            'control': root, 'identity_scope': 'resolved_local_path',
            'record_identity': ['source_id', 'collection', 'local_id']}


def identify(project, initializing=False):
    raw = Path(project).expanduser().absolute()
    result = {'source': source(raw), 'read_only': True, 'effects_executed': False}
    def finish(state, **details):
        return {**result, 'state': state, **details}
    if any(_linked(path) for path in (raw, *raw.parents)):
        return finish('unsafe', reason='linked_project_path')
    if not raw.exists():
        return finish('absent')
    if not raw.is_dir():
        return finish('unknown', reason='project_not_directory')
    directory = raw / '.taskcarry'
    path = directory / 'state.sqlite3'
    if _linked(directory) or _linked(path):
        return finish('unsafe', reason='linked_metadata')
    if not directory.exists():
        return finish('uninitialized')
    if not directory.is_dir():
        return finish('unknown', reason='metadata_not_directory')
    if not path.exists():
        names = {item.name for item in directory.iterdir()}
        if not names or (initializing and names == {'mutation.lock'}):
            return finish('uninitialized')
        return finish('unknown', reason='unrecognized_metadata_without_database')
    if not path.is_file():
        return finish('unknown', reason='database_not_file')
    # immutable mode is deliberately used only when no WAL has pending data.
    # It cannot create -shm/-wal files. Never ignore an existing WAL and guess
    # compatibility from an older database page image.
    wal = path.with_name(path.name + '-wal')
    if _linked(wal):
        return finish('unsafe', reason='linked_journal')
    if wal.exists() and wal.stat().st_size:
        return finish('busy', reason='wal_snapshot_requires_writer_close',
                      next_step='Let the current writer close, then inspect again; do not remove its journal.')
    before = (path.stat().st_ino, path.stat().st_size, path.stat().st_mtime_ns)
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True, timeout=0)) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'records', 'events'}.issubset(tables):
                return finish('unknown', reason='not_taskcarry_tables')
            row = db.execute("SELECT value FROM records WHERE collection='config' AND key='project'").fetchone()
            if row is None:
                if db.execute('PRAGMA application_id').fetchone()[0] == 1413693785:
                    return finish('incomplete', reason='initialization_not_published')
                return finish('unknown', reason='missing_project_identity')
            config = json.loads(row[0])
            if not isinstance(config, dict) or type(config.get('schema_version')) is not int:
                return finish('corrupt', reason='invalid_project_config')
            state = 'compatible' if config['schema_version'] == 1 else 'unsupported'
            if state == 'compatible' and 'store_schema' in tables:
                projection = db.execute("SELECT version FROM store_schema WHERE name='current_records'").fetchone()
                if projection and projection[0] != 1:
                    state = 'unsupported'
            if state == 'compatible' and 'context_schema' in tables:
                context = db.execute('SELECT version FROM context_schema').fetchone()
                if context is None or context[0] != 1:
                    state = 'unsupported'
    except (sqlite3.DatabaseError, ValueError, TypeError, UnicodeError):
        return finish('corrupt', reason='unreadable_state_format')
    after = (path.stat().st_ino, path.stat().st_size, path.stat().st_mtime_ns)
    if before != after or (wal.exists() and wal.stat().st_size):
        return finish('busy', reason='source_changed_during_inspection')
    result['source'] = source(raw, config)
    return finish(state, schema_version=config['schema_version'], project_name=config.get('name'))


def require_initializable(result):
    if result['state'] in ('absent', 'uninitialized', 'compatible', 'incomplete'):
        return
    code = {'unsupported': 'SCHEMA_VERSION_UNSUPPORTED', 'unknown': 'STATE_UNRECOGNIZED',
            'corrupt': 'STATE_CORRUPT', 'unsafe': 'UNSAFE_METADATA', 'busy': 'BUSY'}[result['state']]
    raise GovernanceError(code, 'Initialization left this location unchanged; inspect the existing state before continuing.', result)
