"""Project-local intake of explicit, observed chat-join receipts during a governance cycle."""
import json
from pathlib import Path, PurePosixPath

from .core import _id, digest_bytes, read_file_bytes, validate_relative_path
from .store import GovernanceError
from .workbench import Workbench


def require_join_scope(cycle):
    if 'chat-joins' not in cycle['scope']:
        raise GovernanceError('CYCLE_SCOPE_MISMATCH', 'Reserve chat-joins before handling project chat intake.')


def _receipt_error(message):
    return GovernanceError('JOIN_RECEIPT_INVALID', message)


def _is_join(observation):
    return PurePosixPath(observation['source_ref']).name == 'JOIN_RECEIPT.json'


def _observed_source_key(owner, observation):
    fields = [observation[k] for k in ('workspace', 'task_id', 'source_ref', 'source_revision')]
    return owner + ':source:' + digest_bytes(json.dumps(fields).encode())


def _same_binding(prior, item):
    if prior and (prior['workspace'], prior['task_id']) != (item['workspace'], item['task_id']):
        raise _receipt_error('The joined chat already belongs to another workspace or task; review the binding.')
    return bool(prior)


def _summary_text(value, label):
    if not isinstance(value, str) or len(value) > 8192:
        raise _receipt_error(f'Use bounded text for {label}.')
    return value


def _verified_join(engine, owner, observation):
    path = validate_relative_path(engine.root, observation['source_ref'], allow_missing=False)
    raw = read_file_bytes(path, max_bytes=256 * 1024)
    if digest_bytes(raw) != observation['source_revision']:
        raise _receipt_error('The join receipt differs from the observed SHA-256.')
    try:
        receipt = json.loads(raw)
    except (ValueError, RecursionError) as exc:
        raise _receipt_error('The join receipt is not readable JSON.') from exc
    if not isinstance(receipt, dict) or receipt.get('schema') != 'taskcarry.chat-join-receipt.v1':
        raise _receipt_error('Expected a project chat-join receipt v1.')
    project = engine.source()
    if (receipt.get('project_id') != project['source_id'] or not isinstance(receipt.get('control'), str)
            or Path(receipt['control']) != engine.root):
        raise _receipt_error('The project or control directory does not match this receiver.')
    pending = receipt.get('pending_governance')
    if not isinstance(pending, dict) or not isinstance(pending.get('owner_thread'), str):
        raise _receipt_error('The receipt must identify its original governance chat.')
    if pending['owner_thread'] != owner:
        return None
    if pending.get('status', 'pending_governance_absorption') != 'pending_governance_absorption':
        raise _receipt_error('The receipt does not request governance intake.')
    thread = _id(receipt.get('thread_id'), 'Chat ID')
    task_id = _id(receipt.get('task_id'), 'Joined task')
    workspace = _id(receipt.get('workspace'), 'Joined workspace')
    if (observation.get('task_id'), observation.get('workspace')) != (task_id, workspace):
        raise _receipt_error('The observed workspace and task must match the receipt.')
    task = engine._task(task_id)
    workbench = receipt.get('workbench')
    if not isinstance(workbench, dict):
        raise _receipt_error('A published and consumed chat entry is required.')
    cid = _id(workbench.get('consumption_id'), 'Consumption ID')
    view = _id(workbench.get('view_id'), 'View ID')
    proof = engine.store.get('workbench_consumption', cid) or {}
    expected = {'view_id': view, 'thread_id': thread, 'task_id': task_id, 'workspace': workspace}
    if any(proof.get(k) != v for k, v in expected.items()):
        raise _receipt_error('The consumption record does not match this exact chat, task and view.')
    proof_file = validate_relative_path(engine.root, proof['evidence_path'], allow_missing=False)
    if digest_bytes(read_file_bytes(proof_file)) != proof['evidence_sha256']:
        raise _receipt_error('The evidence for the consumed view has changed.')
    current = Workbench(engine.root).workbench('status', workspace=workspace, thread_id=thread)['items']
    if not any(item.get('thread_id') == thread and item.get('task_id') == task_id
               and item.get('state') == 'PUBLISHED' and not item.get('finalization_pending') for item in current):
        raise _receipt_error('The chat no longer has a verified current entry for this task.')
    progress = receipt.get('business_progress', {})
    if not isinstance(progress, dict):
        raise _receipt_error('Expected a business_progress object.')
    return {'join_id': digest_bytes(json.dumps([project['source_id'], owner, thread]).encode()), 'thread_id': thread,
            'owner': owner, 'workspace': workspace, 'task_id': task_id, 'state': task['state'],
            'responsibility': _summary_text(receipt.get('responsibility', task['title']), 'responsibility'),
            'progress': _summary_text(progress.get('progress', progress.get('draft', '')), 'progress'),
            'waiting_for': _summary_text(progress.get('waiting_for', ''), 'waiting_for'),
            'next_step': _summary_text(progress.get('next_step', task.get('next_step', '')), 'next_step'),
            'observation_id': observation['observation_id'], 'source_ref': observation['source_ref'],
            'source_revision': observation['source_revision'], 'consumption_id': cid}


def join_inbox(engine, cycle, data, limit, cursor):
    require_join_scope(cycle)
    engine._fields(data, ('queue',))
    owner = cycle['owner']
    if data['queue'] == 'pending_report':
        page = engine._page('chat_joins', prefix=owner + ':', cursor=cursor, limit=limit)
        return {'items': [row for row in page['items'] if not row.get('delivery')],
                'needs_review': [], 'next_cursor': page['next_cursor']}
    if data['queue'] != 'new':
        raise _receipt_error('Choose the new or pending_report queue.')
    page = engine._page('observations', cursor=cursor, limit=limit)
    items, needs_review = {}, []
    for observation in page['items']:
        if not _is_join(observation):
            continue
        if engine.store.get('chat_join_observations', _observed_source_key(owner, observation)):
            continue
        try:
            item = _verified_join(engine, owner, observation)
            if item:
                identity = item['join_id']
                prior = items.get(identity) or engine.store.get('chat_joins', owner + ':' + identity)
                if not _same_binding(prior, item):
                    items[identity] = item
        except (GovernanceError, OSError) as exc:
            needs_review.append({'observation_id': observation['observation_id'], 'error': str(exc)})
    return {'items': list(items.values()), 'needs_review': needs_review, 'next_cursor': page['next_cursor']}


def absorb_join(engine, cycle, data):
    require_join_scope(cycle)
    engine._fields(data, ('observation_id', 'source_revision'))
    oid = _id(data['observation_id'], 'Receipt observation ID')
    observation = engine.store.get('observations', oid)
    if not observation or not _is_join(observation) or observation['source_revision'] != data['source_revision']:
        raise _receipt_error('Read the current observed join receipt before confirming it.')
    item = _verified_join(engine, cycle['owner'], observation)
    if item is None:
        raise _receipt_error('The receipt is addressed to another governance chat.')
    key = cycle['owner'] + ':' + item['join_id']
    prior = engine.store.get('chat_joins', key)
    if not _same_binding(prior, item):
        engine.store.put('chat_joins', key, {**item, 'absorbed_in': cycle['cycle_id']})
    engine.store.put('chat_join_observations', _observed_source_key(cycle['owner'], observation),
                     {'source_revision': data['source_revision'], 'join_id': item['join_id']})
    return {'join_id': item['join_id'], 'newly_absorbed': prior is None}


def mark_joins_reported(engine, cycle, delivery):
    require_join_scope(cycle)
    ids = delivery['join_ids']
    if (not isinstance(ids, list) or not 1 <= len(ids) <= 100
            or any(not isinstance(value, str) for value in ids) or len(set(ids)) != len(ids)):
        raise _receipt_error('List the distinct join IDs included in this delivered report.')
    delivered = {field: delivery[field] for field in ('report_id', 'receipt_ref', 'delivered_at')}
    for identity in ids:
        key = cycle['owner'] + ':' + _id(identity, 'Reported join ID')
        item = engine.store.get('chat_joins', key)
        if not item or (item.get('delivery') and item['delivery'] != delivered):
            raise _receipt_error('A join is missing or was already included in another delivered report.')
        engine.store.put('chat_joins', key, {**item, 'delivery': delivered})
