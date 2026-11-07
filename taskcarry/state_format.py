"""Shared read-only recognition of supported persistent governance formats.

The program version is not the database schema version. Original schema-1
databases have SQLite's default application_id=0; recognizing them must not
stamp, migrate or rewrite their evidence. The marker alone proves no origin.
Callers own safe connection handling and any full integrity verification.
"""
import json

APPLICATION_ID = 1413693785
STATE_SCHEMA = 1
INDEX_SCHEMA = 1


def inspect_state(db):
    """Inspect structure/config/index versions without writes or new journals."""
    application_id = db.execute('PRAGMA application_id').fetchone()[0]
    if application_id not in (0, APPLICATION_ID):
        return {'state': 'unknown', 'reason': 'foreign_application_id'}
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    layouts = {
        'records': ({'collection', 'key', 'value'}, ['collection', 'key']),
        'events': ({'sequence', 'created_at', 'kind', 'payload'}, ['sequence']),
    }
    for table, (required, primary_key) in layouts.items():
        if table not in tables:
            return {'state': 'unknown', 'reason': 'not_taskcarry_tables'}
        columns = list(db.execute('PRAGMA table_info(' + table + ')'))
        keys = [row[1] for row in sorted(columns, key=lambda row: row[5]) if row[5]]
        if not required.issubset({row[1] for row in columns}) or keys != primary_key:
            return {'state': 'unknown', 'reason': 'not_taskcarry_table_layout'}
    row = db.execute("SELECT value FROM records WHERE collection='config' AND key='project'").fetchone()
    if row is None:
        return ({'state': 'incomplete', 'reason': 'initialization_not_published'}
                if application_id == APPLICATION_ID else
                {'state': 'unknown', 'reason': 'missing_project_identity'})
    config = json.loads(row[0])
    if not isinstance(config, dict) or type(config.get('schema_version')) is not int:
        return {'state': 'corrupt', 'reason': 'invalid_project_config'}
    if config['schema_version'] != STATE_SCHEMA:
        return {'state': 'unsupported', 'reason': 'state_schema_version', 'config': config}
    for table in ('store_schema', 'context_schema'):
        if table in tables:
            versions = [row[0] for row in db.execute('SELECT version FROM ' + table)]
            if (table == 'context_schema' and not versions) or any(version != INDEX_SCHEMA for version in versions):
                return {'state': 'unsupported', 'reason': 'index_schema_version', 'config': config}
    return {'state': 'compatible', 'config': config}
