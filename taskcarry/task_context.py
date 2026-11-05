"""Task-scoped, paginated context with bounded payload reads and no receipts."""
import base64
import json
import re

from .core import _id, digest_bytes
from .store import GovernanceError

COLLECTIONS = ('observations', 'stages', 'operations', 'artifacts', 'issues', 'fixes', 'runs')
MAX_RECORD_BYTES = 16384


def _hash(value):
    return digest_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(',', ':'), allow_nan=False).encode('utf-8'))


def _selection(values, label):
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > 50:
        raise GovernanceError('INVALID_ARGUMENT', label + ' must contain at most 50 exact identities.')
    result = [_id(item, label) for item in values]
    if len(result) != len(set(result)):
        raise GovernanceError('INVALID_ARGUMENT', label + ' cannot contain duplicates.')
    return sorted(result)


def read_context(core, task_id, limit, cursor, previous_fingerprint, issue_ids, fix_ids):
    task_id = _id(task_id, 'Task ID')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise GovernanceError('INVALID_ARGUMENT', 'Context limit must be an integer from 1 to 100.')
    if previous_fingerprint is not None and (not isinstance(previous_fingerprint, str)
            or not re.fullmatch('[0-9a-f]{64}', previous_fingerprint)):
        raise GovernanceError('INVALID_ARGUMENT', 'Use a SHA-256 previous fingerprint.')
    issue_ids, fix_ids = _selection(issue_ids, 'issue_ids'), _selection(fix_ids, 'fix_ids')
    source = core.source()
    selection = _hash({'source': source, 'task_id': task_id, 'issue_ids': issue_ids, 'fix_ids': fix_ids})
    decoded = None
    if cursor is not None:
        try:
            if not isinstance(cursor, str) or not 1 <= len(cursor) <= 2048:
                raise ValueError()
            decoded = json.loads(base64.b64decode(cursor + '=' * (-len(cursor) % 4), altchars=b'-_', validate=True))
            if (set(decoded) != {'version', 'selection', 'fingerprint', 'after'}
                    or type(decoded['version']) is not int or decoded['version'] != 1
                    or decoded['selection'] != selection
                    or not isinstance(decoded['fingerprint'], str)
                    or not re.fullmatch('[0-9a-f]{64}', decoded['fingerprint'])
                    or not isinstance(decoded['after'], list) or len(decoded['after']) != 2
                    or decoded['after'][0] not in COLLECTIONS
                    or not isinstance(decoded['after'][1], str) or len(decoded['after'][1]) > 256):
                raise ValueError()
        except (ValueError, TypeError, KeyError, UnicodeError):
            raise GovernanceError('CONTEXT_CURSOR_INVALID', 'Use the returned cursor with the same source, task and selections.')

    missing, loaded = [], 0
    with core.store._connect(readonly=True) as db:
        if (not core.store._projection_ready(db) or core.store._projection_dirty(db)
                or not core.store._context_ready(db)):
            raise GovernanceError('CONTEXT_INDEX_REQUIRED', 'Run the explicit upgrade action, then retry context; this read changed nothing.')

        def load(collection, key):
            nonlocal loaded
            row = db.execute('''SELECT length(CAST(value AS BLOB)),
                CASE WHEN length(CAST(value AS BLOB))<=? THEN value ELSE NULL END
                FROM records WHERE collection=? AND key=?''', (MAX_RECORD_BYTES, collection, key)).fetchone()
            if row is None:
                missing.append({'collection': collection, 'local_id': key, 'reason': 'record_missing'})
                return None
            loaded += 1
            if row[1] is None:
                missing.append({'collection': collection, 'local_id': key, 'reason': 'record_exceeds_context_limit',
                                'bytes': row[0]})
                return {'payload_omitted': True, 'bytes': row[0]}
            return json.loads(row[1])

        task = load('tasks', task_id)
        if task is None:
            raise GovernanceError('TASK_NOT_FOUND', 'Create or select an existing task before reading its context.')
        # Fetch only small scalar pointers when a task's large prose is omitted.
        pointer = db.execute("SELECT json_extract(value,'$.latest_checkpoint') FROM records WHERE collection='tasks' AND key=?",
                             (task_id,)).fetchone()[0]
        latest = load('checkpoints', pointer) if isinstance(pointer, str) else None
        if latest and not latest.get('payload_omitted') and latest.get('task_id') != task_id:
            missing.append({'collection': 'checkpoints', 'local_id': pointer, 'reason': 'task_scope_mismatch'})
            latest = None
        selected, selected_revisions = [], []
        for collection, identities in (('issues', issue_ids), ('fixes', fix_ids)):
            for key in identities:
                data = load(collection, key)
                selected_revisions.append(db.execute('SELECT revision FROM context_record_revisions WHERE collection=? AND key=?',
                                                     (collection, key)).fetchone())
                selected.append({'source_id': source['source_id'], 'collection': collection, 'local_id': key,
                                 'selection_basis': 'explicit_caller_reference', 'record': data})
        revision = db.execute('SELECT revision FROM context_revisions WHERE task_id=?', (task_id,)).fetchone()
        generation = db.execute('SELECT generation FROM context_schema').fetchone()[0]
        fingerprint = _hash({'selection': selection, 'generation': generation,
                             'revision': revision[0] if revision else 0, 'selected': selected,
                             'selected_revisions': selected_revisions})
        if decoded and decoded['fingerprint'] != fingerprint:
            raise GovernanceError('CONTEXT_CURSOR_STALE', 'Task evidence changed; read a fresh first page.',
                                  {'current_fingerprint': fingerprint})
        after = decoded['after'] if decoded else ['', '']
        marks = ','.join('?' for _ in COLLECTIONS)
        rows = db.execute('''SELECT c.collection,c.key,length(CAST(r.value AS BLOB)),
            CASE WHEN length(CAST(r.value AS BLOB))<=? THEN r.value ELSE NULL END
            FROM current_records AS c INDEXED BY current_records_task
            JOIN records AS r ON r.collection=c.collection AND r.key=c.key
            WHERE c.task_id=? AND c.collection IN (''' + marks + ''')
            AND (c.collection,c.key)>(?,?) ORDER BY c.collection,c.key LIMIT ?''',
            (MAX_RECORD_BYTES, task_id, *COLLECTIONS, *after, limit + 1)).fetchall()
        total = db.execute('SELECT count(*) FROM current_records INDEXED BY current_records_task '
                           'WHERE task_id=? AND collection IN (' + marks + ')', (task_id, *COLLECTIONS)).fetchone()[0]
        page = []
        for collection, key, size, payload in rows[:limit]:
            data = json.loads(payload) if payload is not None else {'payload_omitted': True, 'bytes': size}
            if payload is None:
                missing.append({'collection': collection, 'local_id': key, 'reason': 'record_exceeds_context_limit', 'bytes': size})
            page.append({'source_id': source['source_id'], 'collection': collection, 'local_id': key, 'record': data})
        loaded += len(rows)
        next_cursor = None
        if len(rows) > limit:
            next_cursor = base64.urlsafe_b64encode(json.dumps({'version': 1, 'selection': selection,
                'fingerprint': fingerprint, 'after': [page[-1]['collection'], page[-1]['local_id']]},
                separators=(',', ':')).encode('utf-8')).decode('ascii').rstrip('=')
    return {'source': source, 'task_id': task_id, 'task': task, 'latest_checkpoint': latest,
            'items': page, 'selected_references': selected, 'missing': missing, 'total': total,
            'returned': len(page), 'has_more': next_cursor is not None, 'next_cursor': next_cursor,
            'fingerprint': fingerprint, 'changed': previous_fingerprint != fingerprint,
            'storage': {'mode': 'indexed_task_context_v1', 'loaded_records': loaded,
                        'max_record_bytes': MAX_RECORD_BYTES, 'payload_read_bound': limit + 103},
            'coverage': {'task_records': list(COLLECTIONS), 'checkpoint': 'latest_only',
                         'issues_and_fixes': 'task-scoped or explicitly selected; unscoped project records are not inferred',
                         'history': 'observation revisions are current; prior revisions and events are not scanned',
                         'external_effects_reverified': False},
            'read_only': True, 'effects_executed': False, 'project_complete': None}
