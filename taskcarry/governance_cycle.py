"""Bounded governance evidence, resource reservations and read-only inventories.

The host supplies reviewed evidence; this module does not read chat history,
execute scheduled work, or turn a report into task/business acceptance. A durable
reservation survives process exit. Only ``cycle_session`` holds a real OS lock
between calls, and it releases that lock on exit, including exceptional exit.
"""
from __future__ import annotations

from contextlib import contextmanager, ExitStack
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path, PurePosixPath
import stat
import threading

from .core import Core, _id, digest_bytes
from .store import GovernanceError, _linked, now


def _hash(value):
    return digest_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(',', ':'), allow_nan=False).encode('utf-8'))


def _text(value, name, maximum=2048):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\0' in value:
        raise GovernanceError('INVALID_EVIDENCE', f'{name} must be nonempty text of at most {maximum} characters.')
    return value


def _integer(value, name, low=1, high=1000):
    if type(value) is not int or not low <= value <= high:
        raise GovernanceError('INVALID_BUDGET', f'{name} must be an integer from {low} to {high}.')
    return value


def _record(value, schema):
    if value is not None and (not isinstance(value, dict) or value.get('schema') != schema):
        raise GovernanceError('SCHEMA_VERSION_UNSUPPORTED', 'Use a compatible toolkit for this evidence record.',
                              {'expected_schema': schema})
    return value


def _stamp(value, name):
    _text(value, name, 128)
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.utcoffset() is None:
            raise ValueError('Timezone required')
        return result
    except ValueError as exc:
        raise GovernanceError('INVALID_TIME', f'{name} needs an ISO timestamp with a timezone.') from exc


def _scope(values):
    if not isinstance(values, list) or not 1 <= len(values) <= 100:
        raise GovernanceError('INVALID_SCOPE', 'Declare between 1 and 100 exact resource identities.')
    values = [_text(value, 'Resource identity', 256) for value in values]
    if len(set(values)) != len(values):
        raise GovernanceError('INVALID_SCOPE', 'Resource identities must be unique.')
    return sorted(values)


@contextmanager
def _os_lock(directory, resource):
    path = directory / ('cycle-' + _hash(resource) + '.lock')
    if _linked(directory) or _linked(path):
        raise GovernanceError('UNSAFE_METADATA', 'A cycle lock cannot traverse a link.')
    handle = open(path, 'a+b')
    held = False
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise GovernanceError('CYCLE_BUSY', 'A live process holds this cycle resource lock.',
                                  {'resource': resource}) from exc
        held = True
        yield
    finally:
        try:
            if held:
                handle.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_UN)
        finally:
            handle.close()


class GovernanceCycle(Core):
    """Evidence over existing tasks, without a second task state machine."""

    def __init__(self, project):
        super().__init__(project)
        self._cycle_local = threading.local()

    @contextmanager
    def _resource_guard(self, cycle_id, owner, scope):
        active = getattr(self._cycle_local, 'session', None)
        if active is not None:
            if active != (cycle_id, owner, scope):
                raise GovernanceError('CYCLE_SESSION_MISMATCH', 'This live session belongs to another exact cycle, owner or scope.')
            yield
            return
        with ExitStack() as stack:
            for resource in scope:
                stack.enter_context(_os_lock(self.store.directory, resource))
            yield

    @contextmanager
    def cycle_session(self, cycle_id, owner, scope, task_id=None, resume=False):
        """Hold real resource locks for a live host process, not a database lock.

        An unfinished reservation survives EOF/crash; another process must use
        the same cycle/owner/scope to resume. There is no TTL lock stealing.
        ``finish`` closes the reservation, but OS locks last until context exit.
        """
        cycle_id, owner, scope = _id(cycle_id, 'Cycle ID'), _id(owner, 'Owner'), _scope(scope)
        if getattr(self._cycle_local, 'session', None) is not None:
            raise GovernanceError('CYCLE_SESSION_MISMATCH', 'Nested cycle sessions are not supported.')
        with self._resource_guard(cycle_id, owner, scope):
            self._cycle_local.session = (cycle_id, owner, scope)
            try:
                self.cycle('resume' if resume else 'start', cycle_id=cycle_id,
                           owner=owner, scope=scope, task_id=task_id)
                yield self
            finally:
                self._cycle_local.session = None

    def _read(self, collection, key, schema):
        return _record(self.store.get(collection, key), schema)

    def _page(self, collection, prefix='', cursor=None, limit=20):
        _integer(limit, 'Limit', 1, 100)
        if cursor is not None:
            _text(cursor, 'Cursor', 1024)
            if not cursor.startswith(prefix):
                raise GovernanceError('INVALID_CURSOR', 'The cursor belongs to another selection.')
        with self.store._connect(readonly=True) as db:
            rows = db.execute('SELECT key,value FROM records WHERE collection=? AND key>=? AND key<? '
                              'AND key>? ORDER BY key LIMIT ?',
                              (collection, prefix, prefix + '\U0010ffff', cursor or '', limit + 1)).fetchall()
        return {'items': [json.loads(value) for _, value in rows[:limit]],
                'next_cursor': rows[limit - 1][0] if len(rows) > limit else None}

    def _cycle_status(self, value):
        result = dict(value)
        result['lock'] = {'durable_reservation': value['state'] != 'completed',
                          'os_lock_held_by_this_session': getattr(self._cycle_local, 'session', None) ==
                          (value['cycle_id'], value['owner'], value['scope']),
                          'meaning': 'Ordinary calls hold OS locks only during that call; use cycle_session for a whole live process session.'}
        current = datetime.now(timezone.utc)
        result['health'] = {}
        for name, health in value.get('health', {}).items():
            age = (current - _stamp(health['observed_at'], 'Observed time')).total_seconds()
            result['health'][name] = {**health, 'age_seconds': age,
                                      'effective_status': health['status'] if 0 <= age <= health['freshness_seconds'] else 'unknown'}
        return result

    def cycle(self, action, cycle_id=None, owner=None, task_id=None, scope=None,
              request_id=None, data=None, limit=20, cursor=None):
        """Start/resume a finite reserved cycle or record reviewed effects/receipts.

        Mutation payloads are supplied in ``data``; ``request_id`` is an immutable
        idempotency key scoped to the cycle. This method never executes an effect.
        """
        if action == 'list':
            page = self._page('governance_cycles', cursor=cursor, limit=limit)
            page['items'] = [self._cycle_status(_record(item, 'taskcarry.cycle.v1')) for item in page['items']]
            return page
        cycle_id = _id(cycle_id, 'Cycle ID')
        if action not in ('status', 'question_check') and cycle_id in (
                self.store.get('config', 'project') or {}).get('recovery_inert_cycle_ids', []):
            raise GovernanceError('RESTORED_RUN_INERT', 'Historical cycles cannot be replayed on a recovered replica.')
        record = self._read('governance_cycles', cycle_id, 'taskcarry.cycle.v1')
        if action == 'status':
            if record is None:
                raise GovernanceError('CYCLE_NOT_FOUND', 'Start this cycle before reading it.')
            return {'cycle': self._cycle_status(record)}
        owner = _id(owner, 'Owner')
        if action in ('start', 'resume'):
            declared = _scope(scope)
            if action == 'start':
                task_id = _id(task_id, 'Task ID')
            with self._resource_guard(cycle_id, owner, declared), self.store.transaction():
                record = self._read('governance_cycles', cycle_id, 'taskcarry.cycle.v1')
                if record:
                    if record['owner'] != owner or record['scope'] != declared or (task_id is not None and record['task_id'] != task_id):
                        raise GovernanceError('CYCLE_ID_CONFLICT', 'Resume requires the original owner, task and exact resource scope.')
                    return {'cycle': self._cycle_status(record), 'reused': True}
                if action == 'resume':
                    raise GovernanceError('CYCLE_NOT_FOUND', 'No retained cycle exists to resume.')
                self._task(task_id)
                for resource in declared:
                    prior = self._read('cycle_reservations', _hash(resource), 'taskcarry.cycle_reservation.v1')
                    if prior and prior.get('state', 'reserved') != 'released' and prior['cycle_id'] != cycle_id:
                        raise GovernanceError('CYCLE_RESERVED', 'An unfinished cycle retains this resource; inspect and resume it.', prior)
                record = {'schema': 'taskcarry.cycle.v1', 'cycle_id': cycle_id, 'owner': owner,
                          'task_id': task_id, 'scope': declared, 'state': 'active', 'created_at': now(),
                          'effects': {}, 'sources': {}, 'health': {}, 'questions': {}, 'reports': {}, 'revision': 1}
                for resource in declared:
                    self.store.put('cycle_reservations', _hash(resource), {'schema': 'taskcarry.cycle_reservation.v1',
                                   'resource': resource, 'cycle_id': cycle_id, 'owner': owner, 'task_id': task_id, 'state': 'reserved'})
                self.store.put('governance_cycles', cycle_id, record)
                self.store.event('cycle_started', {'cycle_id': cycle_id, 'owner': owner, 'task_id': task_id, 'scope': declared})
                return {'cycle': self._cycle_status(record), 'reused': False}
        if record is None:
            raise GovernanceError('CYCLE_NOT_FOUND', 'Start this cycle before recording evidence.')
        if owner != record['owner']:
            raise GovernanceError('CYCLE_OWNER_MISMATCH', 'Continue using the original cycle owner.')
        if task_id is not None and task_id != record['task_id']:
            raise GovernanceError('CYCLE_ID_CONFLICT', 'A cycle cannot move to another task.')
        if scope is not None and _scope(scope) != record['scope']:
            raise GovernanceError('CYCLE_ID_CONFLICT', 'A cycle cannot change its declared resources.')
        data = {} if data is None else data
        if not isinstance(data, dict) or len(json.dumps(data, allow_nan=False)) > 65536:
            raise GovernanceError('INVALID_EVIDENCE', 'Cycle payload must be an object of at most 64 KiB.')
        if action == 'question_check':
            return self._question_check(data)
        request_id = _id(request_id, 'Request ID')
        request_key = cycle_id + ':' + request_id
        fingerprint = _hash({'action': action, 'owner': owner, 'data': data})
        with self._resource_guard(cycle_id, owner, record['scope']), self.store.transaction():
            record = self._read('governance_cycles', cycle_id, 'taskcarry.cycle.v1')
            previous = self._read('cycle_requests', request_key, 'taskcarry.cycle_request.v1')
            if previous:
                if previous['fingerprint'] != fingerprint:
                    raise GovernanceError('IDEMPOTENCY_CONFLICT', 'An idempotency key cannot describe a different effect or receipt.')
                return {'cycle': self._cycle_status(record), 'receipt': previous, 'reused': True}
            if record['state'] == 'completed':
                raise GovernanceError('CYCLE_CLOSED', 'A completed cycle cannot accept new mutations.')
            outcome = self._cycle_apply(record, action, data)
            record['revision'] += 1
            record['updated_at'] = now()
            receipt = {'schema': 'taskcarry.cycle_request.v1', 'cycle_id': cycle_id,
                       'request_id': request_id, 'fingerprint': fingerprint, 'action': action,
                       'cycle_revision': record['revision'], 'recorded_at': now(), 'result': outcome}
            self.store.put('governance_cycles', cycle_id, record)
            self.store.put('cycle_requests', request_key, receipt)
            self.store.event('cycle_evidence_recorded', {'cycle_id': cycle_id, 'request_id': request_id,
                             'action': action, 'revision': record['revision'], 'task_id': record['task_id']})
            return {'cycle': self._cycle_status(record), 'receipt': receipt, 'reused': False}

    @staticmethod
    def _fields(data, required, optional=()):
        if set(data) - set(required) - set(optional) or set(required) - set(data):
            raise GovernanceError('INVALID_EVIDENCE', 'Payload fields do not match this action.',
                                  {'required': list(required), 'optional': list(optional)})

    @staticmethod
    def _bounded(mapping, key, maximum=100):
        if key not in mapping and len(mapping) >= maximum:
            raise GovernanceError('CYCLE_CAPACITY', 'Close this finite cycle before adding further distinct evidence.')

    def _cycle_apply(self, record, action, data):
        if action == 'effect_plan':
            self._fields(data, ('effect_id', 'kind', 'resource', 'expected'))
            identity = _id(data['effect_id'], 'Effect ID')
            _text(data['kind'], 'Effect kind', 100)
            _text(data['expected'], 'Expected observable outcome', 8192)
            if data['resource'] not in record['scope']:
                raise GovernanceError('CYCLE_SCOPE_MISMATCH', 'The effect resource is outside the frozen cycle scope.')
            self._bounded(record['effects'], identity)
            existing = record['effects'].get(identity)
            if existing and existing['plan'] != data:
                raise GovernanceError('EFFECT_CONFLICT', 'A planned effect cannot be redefined.')
            record['effects'].setdefault(identity, {'plan': data, 'outcome': 'pending'})
            return record['effects'][identity]
        if action == 'effect_result':
            self._fields(data, ('effect_id', 'outcome', 'evidence_ref', 'statement'))
            identity = _id(data['effect_id'], 'Effect ID')
            effect = record['effects'].get(identity)
            if effect is None:
                raise GovernanceError('EFFECT_NOT_PLANNED', 'Record the expected effect before its result.')
            if data['outcome'] not in ('confirmed', 'rejected', 'deferred', 'failed'):
                raise GovernanceError('INVALID_EVIDENCE', 'Unsupported effect outcome.')
            _text(data['evidence_ref'], 'Evidence reference')
            _text(data['statement'], 'Verified effect statement', 8192)
            if effect['outcome'] in ('confirmed', 'rejected') and effect.get('result') != data:
                raise GovernanceError('EFFECT_TERMINAL', 'A terminal effect receipt cannot be rewritten.')
            effect.update(outcome=data['outcome'], result=data)
            return effect
        if action == 'source':
            self._fields(data, ('source_id', 'source_revision', 'phase', 'evidence_ref', 'statement'), ('target',))
            for name in ('source_id', 'source_revision'):
                _text(data[name], name, 512)
            _text(data['evidence_ref'], 'Evidence reference')
            _text(data['statement'], 'Source interpretation', 8192)
            phases = ('observed', 'understood', 'published', 'consumed')
            if data['phase'] not in phases:
                raise GovernanceError('INVALID_EVIDENCE', 'Unsupported source phase.')
            if data['phase'] in ('published', 'consumed'):
                _text(data.get('target'), 'Exact target')
            elif 'target' in data:
                raise GovernanceError('INVALID_EVIDENCE', 'Observed and understood phases do not name a delivery target.')
            identity = _hash([data['source_id'], data['source_revision']])
            self._bounded(record['sources'], identity)
            source = record['sources'].setdefault(identity, {'source_id': data['source_id'],
                                        'source_revision': data['source_revision'], 'phases': {}})
            target_key = data['phase'] + (':' + data['target'] if 'target' in data else '')
            index = phases.index(data['phase'])
            predecessor = phases[index - 1] + (':' + data['target'] if data['phase'] == 'consumed' else '') if index else None
            if predecessor and predecessor not in source['phases']:
                raise GovernanceError('SOURCE_PHASE_MISSING', 'Record the preceding source phase for this exact revision and target.')
            self._bounded(source['phases'], target_key)
            prior = source['phases'].get(target_key)
            if prior and prior != data:
                raise GovernanceError('SOURCE_PHASE_CONFLICT', 'Source evidence is immutable for each revision, phase and target.')
            source['phases'][target_key] = data
            return source
        if action == 'health':
            self._fields(data, ('dimension', 'status', 'observed_at', 'freshness_seconds', 'evidence_ref'))
            dimension = _text(data['dimension'], 'Health dimension', 128)
            _text(data['evidence_ref'], 'Evidence reference')
            if data['status'] not in ('healthy', 'degraded', 'failed', 'unknown'):
                raise GovernanceError('INVALID_EVIDENCE', 'Unsupported health status.')
            timestamp = _stamp(data['observed_at'], 'Observation time')
            if timestamp > datetime.now(timezone.utc) + timedelta(minutes=5):
                raise GovernanceError('INVALID_TIME', 'A health observation cannot be in the future.')
            _integer(data['freshness_seconds'], 'Freshness seconds', 1, 2678400)
            self._bounded(record['health'], dimension)
            prior = record['health'].get(dimension)
            if prior and timestamp < _stamp(prior['observed_at'], 'Previous observation time'):
                raise GovernanceError('HEALTH_STALE_WRITE', 'An older observation cannot replace a newer health observation.')
            record['health'][dimension] = data
            return data
        if action in ('question_delivered', 'report_delivered', 'question_response'):
            return self._delivery(record, action, data)
        if action == 'finish':
            self._fields(data, ('state', 'next_step'))
            if data['state'] not in ('completed', 'waiting'):
                raise GovernanceError('INVALID_EVIDENCE', 'Finish state must be completed or waiting.')
            _text(data['next_step'], 'Next step', 8192)
            unresolved = [key for key, effect in record['effects'].items() if effect['outcome'] not in ('confirmed', 'rejected')]
            if data['state'] == 'completed' and unresolved:
                raise GovernanceError('CYCLE_EFFECTS_PENDING', 'Verify actual effects before completing this cycle.', {'effects': unresolved})
            record.update(data)
            if data['state'] == 'completed':
                for resource in record['scope']:
                    prior = self._read('cycle_reservations', _hash(resource), 'taskcarry.cycle_reservation.v1')
                    if not prior or prior['cycle_id'] != record['cycle_id']:
                        raise GovernanceError('CYCLE_RESERVATION_CHANGED', 'A reserved resource changed unexpectedly.')
                    self.store.put('cycle_reservations', _hash(resource), {**prior, 'state': 'released', 'released_at': now()})
            return {'state': record['state'], 'next_step': record['next_step'], 'unresolved_effects': unresolved,
                    'meaning': 'Cycle evidence closeout; existing task and business acceptance are unchanged.'}
        raise GovernanceError('INVALID_ACTION', 'Unknown cycle action.')

    def _question_check(self, data):
        self._fields(data, ('question_id',), ('local_date',))
        identity = _text(data['question_id'], 'Question ID', 512)
        record = self._read('cycle_questions', _hash(identity), 'taskcarry.question.v1')
        if record is None:
            return {'question_id': identity, 'answered': False, 'distinct_dates': [], 'stop_proactive': False}
        return {**record, 'stop_proactive': record['answered'] or len(record['distinct_dates']) >= record['max_distinct_dates'],
                'already_delivered_on_date': data.get('local_date') in record['distinct_dates']}

    def _delivery(self, cycle, action, data):
        question = action != 'report_delivered'
        name = 'question_id' if question else 'report_id'
        identity = _text(data.get(name), name, 512)
        if action == 'question_response':
            self._fields(data, (name, 'receipt_ref', 'statement'))
            _text(data['receipt_ref'], 'Actual response receipt')
            _text(data['statement'], 'Response statement', 8192)
            record = self._read('cycle_questions', _hash(identity), 'taskcarry.question.v1')
            if record is None:
                raise GovernanceError('QUESTION_NOT_FOUND', 'Record the delivered question before its response.')
            if record.get('response') and record['response'] != data:
                raise GovernanceError('RECEIPT_CONFLICT', 'The retained response receipt cannot be replaced.')
            record.update(answered=True, response=data)
            self.store.put('cycle_questions', _hash(identity), record)
            return record
        self._fields(data, (name, 'receipt_ref', 'delivered_at', 'utc_offset_minutes', 'local_date'),
                     ('max_distinct_dates',) if question else ())
        _text(data['receipt_ref'], 'Actual native delivery receipt')
        delivered = _stamp(data['delivered_at'], 'Delivered time')
        offset = _integer(data['utc_offset_minutes'], 'UTC offset minutes', -720, 840)
        if delivered > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise GovernanceError('INVALID_TIME', 'A delivery receipt cannot claim a future delivery.')
        actual_date = delivered.astimezone(timezone(timedelta(minutes=offset))).date().isoformat()
        if data['local_date'] != actual_date:
            raise GovernanceError('DELIVERY_DATE_MISMATCH', 'Use the actual delivery date in the declared timezone.')
        delivery_key = _hash([name, identity, data['receipt_ref']])
        prior_delivery = self._read('cycle_deliveries', delivery_key, 'taskcarry.delivery.v1')
        delivery_body = {key: value for key, value in data.items() if key != 'max_distinct_dates'}
        if prior_delivery and prior_delivery['delivery'] != delivery_body:
            raise GovernanceError('RECEIPT_CONFLICT', 'An actual delivery receipt cannot be assigned another date or content.')
        if prior_delivery is None:
            self.store.put('cycle_deliveries', delivery_key, {'schema': 'taskcarry.delivery.v1', 'delivery': delivery_body})
        if question:
            maximum = _integer(data.get('max_distinct_dates', 2), 'Maximum distinct dates', 1, 10)
            key = _hash(identity)
            record = self._read('cycle_questions', key, 'taskcarry.question.v1') or {
                'schema': 'taskcarry.question.v1', 'question_id': identity, 'distinct_dates': [],
                'max_distinct_dates': maximum, 'answered': False}
            if maximum != record['max_distinct_dates']:
                raise GovernanceError('QUESTION_POLICY_CHANGED', 'A question cannot silently reset its reminder policy.')
            dates = sorted(set(record['distinct_dates'] + [actual_date]))
            if len(dates) > 100:
                raise GovernanceError('QUESTION_CAPACITY', 'Question date history has reached its explicit bound.')
            record.update(distinct_dates=dates, last_delivery=data,
                          over_limit=len(dates) > maximum,
                          stop_proactive=record['answered'] or len(dates) >= maximum)
            self.store.put('cycle_questions', key, record)
            self._bounded(cycle['questions'], identity)
            cycle['questions'][identity] = {'local_date': actual_date, 'receipt_ref': data['receipt_ref']}
            return record
        key = _hash([identity, actual_date])
        prior = self._read('cycle_reports', key, 'taskcarry.report.v1')
        if prior and prior['delivery'] != data:
            raise GovernanceError('REPORT_ALREADY_DELIVERED', 'This report already has a retained receipt on that date.', prior)
        record = prior or {'schema': 'taskcarry.report.v1', 'report_id': identity, 'local_date': actual_date, 'delivery': data}
        self.store.put('cycle_reports', key, record)
        self._bounded(cycle['reports'], key)
        cycle['reports'][key] = record
        return record

    def facts(self, action, fact_id=None, source_id=None, source_revision=None,
              task_id=None, kind=None, statement=None, evidence=None, judgment=None,
              relations=None, aliases=None, standing='current', expected_revision=None,
              limit=20, cursor=None):
        """Source-qualified facts with immutable history and revision CAS.

        Evidence is the host's source reference; judgment is separately labelled
        interpretation. Neither becomes an independently verified observation.
        """
        source_id = self.source()['source_id'] if source_id is None else _text(source_id, 'Source ID', 512)
        if action == 'list':
            page = self._page('governance_facts', _hash(source_id) + ':', cursor, limit)
            page['items'] = [_record(item, 'taskcarry.fact.v1') for item in page['items']]
            return page
        fact_id = _id(fact_id, 'Fact ID')
        key = _hash(source_id) + ':' + fact_id
        prior = self._read('governance_facts', key, 'taskcarry.fact.v1')
        if action == 'history':
            page = self._page('governance_fact_history', key + ':', cursor, limit)
            page['items'] = [_record(item, 'taskcarry.fact.v1') for item in page['items']]
            return page
        if action == 'get':
            if prior is None:
                raise GovernanceError('FACT_NOT_FOUND', 'No fact exists for this source-qualified identity.')
            return {'fact': prior}
        if action != 'record':
            raise GovernanceError('INVALID_ACTION', 'Unknown facts action.')
        task_id = _id(task_id, 'Task ID')
        _text(source_revision, 'Source revision', 512)
        _text(statement, 'Source statement', 8192)
        if kind not in ('decision', 'artifact', 'relationship', 'alias', 'status'):
            raise GovernanceError('INVALID_EVIDENCE', 'Unsupported fact kind.')
        if standing not in ('current', 'superseded', 'historical', 'disputed'):
            raise GovernanceError('INVALID_EVIDENCE', 'Unsupported current standing.')
        if not isinstance(evidence, dict) or set(evidence) != {'reference', 'summary'}:
            raise GovernanceError('INVALID_EVIDENCE', 'Evidence requires an exact reference and source summary.')
        _text(evidence['reference'], 'Source evidence reference')
        _text(evidence['summary'], 'Source evidence summary', 8192)
        if judgment is not None:
            if not isinstance(judgment, dict) or set(judgment) != {'statement', 'basis'}:
                raise GovernanceError('INVALID_EVIDENCE', 'Judgment requires a separate statement and basis.')
            _text(judgment['statement'], 'AI judgment', 8192)
            _text(judgment['basis'], 'Judgment basis', 8192)
        if expected_revision is not None:
            _integer(expected_revision, 'Expected revision', 1, 2147483647)
        relations = [] if relations is None else relations
        aliases = [] if aliases is None else aliases
        if not isinstance(relations, list) or len(relations) > 100 or not isinstance(aliases, list) or len(aliases) > 100:
            raise GovernanceError('INVALID_RELATION', 'Facts support at most 100 explicit relations and aliases.')
        normalized = []
        for relation in relations:
            if not isinstance(relation, dict) or set(relation) != {'source_id', 'fact_id', 'relation'}:
                raise GovernanceError('INVALID_RELATION', 'Relations require source_id, fact_id and relation.')
            normalized.append({'source_id': _text(relation['source_id'], 'Related source', 512),
                               'fact_id': _id(relation['fact_id'], 'Related fact'),
                               'relation': _text(relation['relation'], 'Relation', 128)})
        if len({_hash(value) for value in normalized}) != len(normalized):
            raise GovernanceError('INVALID_RELATION', 'Relationships must be unique.')
        aliases = sorted(_text(value, 'Alias', 512) for value in aliases)
        if len(set(aliases)) != len(aliases):
            raise GovernanceError('INVALID_RELATION', 'Aliases must be unique.')
        body = {'source_id': source_id, 'fact_id': fact_id, 'source_revision': source_revision,
                'task_id': task_id, 'kind': kind, 'statement': statement, 'evidence': evidence,
                'judgment': judgment, 'relations': sorted(normalized, key=_hash), 'aliases': aliases, 'standing': standing}
        fingerprint = _hash(body)
        with self.store.transaction():
            self._task(task_id)
            prior = self._read('governance_facts', key, 'taskcarry.fact.v1')
            if prior and (prior['task_id'] != task_id or prior['kind'] != kind):
                raise GovernanceError('FACT_ID_CONFLICT', 'A fact identity cannot change task or kind.')
            if prior and prior['fingerprint'] == fingerprint:
                return {'fact': prior, 'reused': True}
            if expected_revision != (prior['revision'] if prior else None):
                raise GovernanceError('FACT_CHANGED', 'Reread the current fact before replacing its revision.',
                                      {'current_revision': prior['revision'] if prior else None})
            for relation in normalized:
                related = self._read('governance_facts', _hash(relation['source_id']) + ':' + relation['fact_id'], 'taskcarry.fact.v1')
                if related is None:
                    raise GovernanceError('RELATED_FACT_NOT_FOUND', 'Register the source-qualified related fact first.', relation)
            record = {'schema': 'taskcarry.fact.v1', **body, 'revision': prior['revision'] + 1 if prior else 1,
                      'fingerprint': fingerprint, 'recorded_at': now(), 'host_reviewed': True,
                      'meaning': 'Retained source evidence and separately labelled interpretation; no independent source verification or authorization.'}
            self.store.put('governance_facts', key, record)
            self.store.put('governance_fact_history', key + ':' + str(record['revision']).zfill(10), record)
            self.store.event('governance_fact_recorded', {'source_id': source_id, 'fact_id': fact_id,
                             'task_id': task_id, 'revision': record['revision'], 'fingerprint': fingerprint})
            return {'fact': record, 'reused': False}

    @staticmethod
    def _source_root(value):
        _text(value, 'Authorized root', 4096)
        path = Path(value).expanduser().absolute()
        if any(_linked(item) for item in (path, *path.parents)) or not path.is_dir():
            raise GovernanceError('SOURCE_UNAVAILABLE', 'The authorized source root must be an existing directory without links.')
        return path.resolve()

    @staticmethod
    def _exclusions(values):
        if not isinstance(values, list) or len(values) > 100:
            raise GovernanceError('INVALID_SCOPE', 'At most 100 excluded subtrees may be declared.')
        result = {'.git', '.taskcarry'}
        for value in values:
            _text(value, 'Excluded subtree', 1024)
            path = PurePosixPath(value)
            if '\\' in value or ':' in value or path.is_absolute() or any(part in ('.', '..') for part in value.split('/')):
                raise GovernanceError('INVALID_SCOPE', 'Exclusions must be safe relative subtree paths using forward slashes.')
            result.add(path.as_posix().rstrip('/'))
        return sorted(result)

    @staticmethod
    def _watermark(path):
        info = path.stat(follow_symlinks=False)
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400 or not stat.S_ISDIR(info.st_mode):
            raise GovernanceError('SOURCE_CHANGED', 'A source directory became a link or non-directory.')
        return [info.st_dev, info.st_ino, info.st_mtime_ns]

    def _scan_summary(self, record):
        return {key: value for key, value in record.items() if key not in ('stack', 'watermarks')}

    def source_scan(self, action, source_id, root=None, authorization_ref=None,
                    exclusions=None, expected_revision=None, scan_id=None,
                    cursor=None, max_entries=200, max_directory_entries=10000,
                    max_directories=1000, max_total_entries=100000):
        """Register an authorized metadata source, then page a frozen scan plan.

        Metadata only: no file bodies, network calls or source writes. Each
        directory listing is bounded and frozen before paging. Directory changes
        invalidate continuation; oversized directories produce an incomplete
        inventory, never a deletion claim. File metadata observations occur over
        a time window and are explicitly not an atomic filesystem snapshot.
        """
        source_id = _text(source_id, 'Source ID', 512)
        key = _hash(source_id)
        registry = self._read('scan_sources', key, 'taskcarry.scan_source.v1')
        if action == 'register':
            authorized = self._source_root(root)
            if authorized == self.root or authorized in self.root.parents:
                raise GovernanceError('SOURCE_OUTPUT_OVERLAP', 'Keep governance output outside the read-only source root.')
            excluded = self._exclusions([] if exclusions is None else exclusions)
            _text(authorization_ref, 'Root authorization reference')
            if expected_revision is not None:
                _integer(expected_revision, 'Expected source revision', 1, 2147483647)
            body = {'source_id': source_id, 'root': str(authorized), 'exclusions': excluded,
                    'authorization_ref': authorization_ref}
            fingerprint = _hash(body)
            with self.store.transaction():
                registry = self._read('scan_sources', key, 'taskcarry.scan_source.v1')
                if registry and registry['fingerprint'] == fingerprint:
                    return {'source': registry, 'reused': True}
                if expected_revision != (registry['revision'] if registry else None):
                    raise GovernanceError('SOURCE_REGISTRY_CHANGED', 'Reread the authorized source before replacing its configuration.')
                registry = {'schema': 'taskcarry.scan_source.v1', **body, 'fingerprint': fingerprint,
                            'revision': registry['revision'] + 1 if registry else 1, 'recorded_at': now()}
                self.store.put('scan_sources', key, registry)
                self.store.event('scan_source_registered', {'source_id': source_id, 'revision': registry['revision'],
                                                          'fingerprint': fingerprint})
                return {'source': registry, 'reused': False}
        if registry is None:
            raise GovernanceError('SOURCE_NOT_REGISTERED', 'Register an explicitly authorized root before scanning.')
        if action == 'registry':
            return {'source': registry}
        scan_id = _id(scan_id, 'Scan ID')
        scan_key = key + ':' + scan_id
        if action == 'start':
            _integer(max_entries, 'Entries per page', 1, 1000)
            _integer(max_directory_entries, 'Entries per directory', 1, 10000)
            _integer(max_directories, 'Directories per scan', 1, 2000)
            _integer(max_total_entries, 'Entries per scan', 1, 100000)
            budget = {'max_entries': max_entries, 'max_directory_entries': max_directory_entries,
                      'max_directories': max_directories, 'max_total_entries': max_total_entries}
            plan = {'source_revision': registry['revision'], 'source_fingerprint': registry['fingerprint'], 'budgets': budget}
            with self.store.transaction():
                prior = self._read('source_scans', scan_key, 'taskcarry.source_scan.v1')
                if prior:
                    if prior['plan'] != plan:
                        raise GovernanceError('SCAN_ID_CONFLICT', 'A scan ID retains its original source and budgets.')
                    return {'scan': self._scan_summary(prior), 'reused': True}
                source_root = self._source_root(registry['root'])
                record = {'schema': 'taskcarry.source_scan.v1', 'source_id': source_id, 'scan_id': scan_id,
                          'source': registry, 'plan': plan, 'state': 'scanning', 'started_at': now(),
                          'next_cursor': scan_id + ':0000000000', 'pages': 0, 'entries_seen': 0,
                          'files_seen': 0, 'directories_seen': 0, 'errors': [], 'skipped_count': 0,
                          'stack': [{'path': '', 'entries': None, 'index': 0}],
                          'watermarks': {'': self._watermark(source_root)},
                          'enumeration_complete': False, 'metadata_only': True,
                          'missing_assessment': 'unknown_until_complete_and_never_deletion_proof',
                          'meaning': 'Metadata observations over a time window, not atomic content identity, user intent, or source deletion proof.'}
                self.store.put('source_scans', scan_key, record)
                self.store.event('source_scan_started', {'source_id': source_id, 'scan_id': scan_id, 'plan': plan})
                return {'scan': self._scan_summary(record), 'reused': False}
        record = self._read('source_scans', scan_key, 'taskcarry.source_scan.v1')
        if record is None:
            raise GovernanceError('SCAN_NOT_FOUND', 'Start this source scan before reading or continuing it.')
        if action == 'status':
            return {'scan': self._scan_summary(record)}
        if action != 'page':
            raise GovernanceError('INVALID_ACTION', 'Unknown source_scan action.')
        _text(cursor, 'Scan continuation cursor', 128)
        if not cursor.startswith(scan_id + ':'):
            raise GovernanceError('SCAN_CURSOR_INVALID', 'This cursor belongs to another scan.')
        page_key = key + ':' + cursor
        with self.store.transaction():
            prior = self._read('source_scan_pages', page_key, 'taskcarry.source_scan_page.v1')
            if prior:
                return {'page': prior, 'reused': True}
            record = self._read('source_scans', scan_key, 'taskcarry.source_scan.v1')
            if cursor != record['next_cursor'] or record['state'] != 'scanning':
                raise GovernanceError('SCAN_CURSOR_INVALID', 'Continue the exact retained cursor or start a new scan.')
            page = self._scan_page(record, cursor)
            self.store.put('source_scan_pages', page_key, page)
            self.store.put('source_scans', scan_key, record)
            self.store.event('source_scan_page_recorded', {'source_id': source_id, 'scan_id': scan_id,
                             'cursor': cursor, 'revision': page['revision'], 'state': record['state']})
            return {'page': page, 'reused': False}

    def _scan_page(self, record, cursor):
        source = record['source']
        root = Path(source['root'])
        budget = record['plan']['budgets']
        items, skipped, errors = [], [], []
        processed, listed = 0, 0

        def fail(path, reason):
            error = {'path': path, 'reason': reason}
            errors.append(error)
            record['errors'].append(error)

        def checked_path(relative):
            current = root
            if any(_linked(item) for item in (root, *root.parents)):
                raise GovernanceError('SOURCE_CHANGED', 'The source root or its ancestor became a link.')
            for part in PurePosixPath(relative).parts:
                current = current / part
                if _linked(current):
                    raise GovernanceError('SOURCE_CHANGED', 'A source ancestor became a link.')
            return current

        def stable_watermarks():
            for relative, watermark in record['watermarks'].items():
                if self._watermark(checked_path(relative)) != watermark:
                    raise GovernanceError('SOURCE_CHANGED', 'A directory changed during scan paging.', {'path': relative})

        try:
            stable_watermarks()
            while record['stack'] and processed < budget['max_entries']:
                if record['entries_seen'] >= budget['max_total_entries']:
                    fail('', 'total_entry_budget')
                    record['stack'] = []
                    break
                node = record['stack'][-1]
                current = checked_path(node['path'])
                if node['entries'] is None:
                    if record['directories_seen'] >= budget['max_directories']:
                        fail(node['path'], 'directory_budget')
                        record['stack'].pop()
                        continue
                    record['directories_seen'] += 1
                    before = self._watermark(current)
                    names = []
                    try:
                        with os.scandir(current) as iterator:
                            for entry in iterator:
                                listed += 1
                                if len(names) >= budget['max_directory_entries']:
                                    fail(node['path'], 'directory_entry_budget')
                                    names = None
                                    break
                                names.append(entry.name)
                    except OSError as exc:
                        fail(node['path'], type(exc).__name__)
                        names = None
                    after = self._watermark(current)
                    if before != after:
                        raise GovernanceError('SOURCE_CHANGED', 'A directory changed while its names were frozen.')
                    record['watermarks'][node['path']] = after
                    if names is None:
                        record['stack'].pop()
                        continue
                    node['entries'] = sorted(names)
                if node['index'] >= len(node['entries']):
                    record['stack'].pop()
                    continue
                name = node['entries'][node['index']]
                node['index'] += 1
                relative = (PurePosixPath(node['path']) / name).as_posix()
                processed += 1
                record['entries_seen'] += 1
                folded = relative.casefold()
                excluded = any(folded == item.casefold() or folded.startswith(item.casefold() + '/') for item in source['exclusions'])
                # Metadata directory names are excluded at every depth.
                if excluded or name.casefold() in ('.git', '.taskcarry'):
                    skipped.append({'path': relative, 'reason': 'policy_excluded'})
                    continue
                try:
                    path = current / name
                    info = path.stat(follow_symlinks=False)
                    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                        skipped.append({'path': relative, 'reason': 'link'})
                    elif stat.S_ISDIR(info.st_mode):
                        if len(record['stack']) >= 128:
                            fail(relative, 'directory_depth_budget')
                        else:
                            record['stack'].append({'path': relative, 'entries': None, 'index': 0})
                        items.append({'path': relative, 'kind': 'directory'})
                    elif stat.S_ISREG(info.st_mode):
                        items.append({'path': relative, 'kind': 'file', 'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns})
                        record['files_seen'] += 1
                    else:
                        skipped.append({'path': relative, 'reason': 'nonregular'})
                except OSError as exc:
                    fail(relative, type(exc).__name__)
            stable_watermarks()
        except (GovernanceError, OSError) as exc:
            fail('', exc.code if isinstance(exc, GovernanceError) else type(exc).__name__)
            record['state'] = 'invalidated'
            record['stack'] = []
        record['pages'] += 1
        record['skipped_count'] += len(skipped)
        if not record['stack']:
            if record['state'] != 'invalidated':
                record['state'] = 'incomplete' if record['errors'] else 'complete'
            record['enumeration_complete'] = record['state'] == 'complete'
            record['next_cursor'] = None
            record['finished_at'] = now()
            record['missing_assessment'] = ('not_observed_is_not_deletion_proof' if record['enumeration_complete'] else 'unknown_due_to_incomplete_scan')
        else:
            record['next_cursor'] = record['scan_id'] + ':' + str(record['pages']).zfill(10)
        body = {'source_id': record['source_id'], 'scan_id': record['scan_id'], 'cursor': cursor,
                'items': items, 'skipped': skipped, 'errors': errors, 'entries_processed': processed,
                'directory_entries_listed': listed, 'next_cursor': record['next_cursor'], 'state': record['state'],
                'enumeration_complete': record['enumeration_complete'], 'metadata_only': True,
                'missing_assessment': record['missing_assessment']}
        return {'schema': 'taskcarry.source_scan_page.v1', **body, 'revision': _hash(body), 'observed_at': now()}
