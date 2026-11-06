"""Standalone schemas for bounded governance evidence tools."""


def _string(description='', **values):
    return {'type': 'string', 'description': description, **values}


def _object(properties=None, required=()):
    return {'type': 'object', 'properties': properties or {}, 'required': list(required), 'additionalProperties': False}


def _integer(description, minimum=1, maximum=100):
    return {'type': 'integer', 'description': description, 'minimum': minimum, 'maximum': maximum}


SCHEMAS = {
    'cycle': _object({
        'action': _string(enum=['list', 'status', 'start', 'resume', 'effect_plan', 'effect_result',
                               'source', 'health', 'question_check', 'question_delivered',
                               'question_response', 'report_delivered', 'finish']),
        'cycle_id': _string('Original finite cycle identity.'),
        'owner': _string('Original owner, required for mutations and question_check.'),
        'task_id': _string('Existing task; required at start, never a new task authority.'),
        'scope': {'type': 'array', 'items': _string(), 'minItems': 1, 'maxItems': 100, 'uniqueItems': True,
                  'description': 'Exact shared resource identities, immutable for this cycle; required at start/resume.'},
        'request_id': _string('Immutable idempotency key for evidence mutations, required after start/resume.'),
        'data': {'type': 'object', 'additionalProperties': True,
                 'description': 'Action payload. effect_plan: effect_id/kind/resource/expected. effect_result: effect_id/outcome(confirmed,rejected,deferred,failed)/evidence_ref/statement. source: source_id/source_revision/phase(observed,understood,published,consumed)/evidence_ref/statement and target for published/consumed. health: dimension/status/observed_at/freshness_seconds/evidence_ref. question_check: question_id and optional local_date. question_delivered/report_delivered: question_id or report_id, receipt_ref/delivered_at/utc_offset_minutes/local_date; question may set max_distinct_dates (default 2). question_response: question_id/receipt_ref/statement. finish: state(completed,waiting)/next_step.'},
        'limit': _integer('Maximum list records per page.'), 'cursor': _string('Opaque list cursor.'),
    }, ('action',)),
    'facts': _object({
        'action': _string(enum=['get', 'list', 'history', 'record']),
        'fact_id': _string('Stable fact identity within its source; required except for list.'),
        'source_id': _string('Stable source namespace; defaults to the project logical identity.'),
        'source_revision': _string('Exact reviewed source revision; required for record.'),
        'task_id': _string('Existing task; required for record.'),
        'kind': _string(enum=['decision', 'artifact', 'relationship', 'alias', 'status']),
        'statement': _string('Retained source statement, not an implicit AI inference.'),
        'evidence': _object({'reference': _string(), 'summary': _string()}, ('reference', 'summary')),
        'judgment': _object({'statement': _string(), 'basis': _string()}, ('statement', 'basis')),
        'relations': {'type': 'array', 'maxItems': 100, 'items': _object({
            'source_id': _string(), 'fact_id': _string(), 'relation': _string()}, ('source_id', 'fact_id', 'relation'))},
        'aliases': {'type': 'array', 'items': _string(), 'maxItems': 100, 'uniqueItems': True},
        'standing': _string(enum=['current', 'superseded', 'historical', 'disputed']),
        'expected_revision': _integer('Current fact revision required when replacing content.', 1, 2147483647),
        'limit': _integer('Maximum facts or history records per page.'), 'cursor': _string('Opaque selection cursor.'),
    }, ('action',)),
    'source_scan': _object({
        'action': _string(enum=['register', 'registry', 'start', 'status', 'page']),
        'source_id': _string('Stable source namespace, not an automatically discovered project.'),
        'root': _string('Existing explicitly authorized local metadata source; required for register.'),
        'authorization_ref': _string('User or policy authorization reference for this root.'),
        'exclusions': {'type': 'array', 'items': _string(), 'maxItems': 100,
                       'description': 'Relative excluded subtrees; .git and .taskcarry are always excluded.'},
        'expected_revision': _integer('Current registration revision required for configuration changes.', 1, 2147483647),
        'scan_id': _string('Finite scan identity, required for start/status/page.'),
        'cursor': _string('Exact next_cursor returned by start/page; repeated cursors reuse the retained page.'),
        'max_entries': _integer('Processed entries per page; default 200.', 1, 1000),
        'max_directory_entries': _integer('Bounded directory name snapshot; oversized directories are incomplete.', 1, 10000),
        'max_directories': _integer('Directories per scan; default 1000.', 1, 2000),
        'max_total_entries': _integer('Entries per scan; default 100000.', 1, 100000),
    }, ('action', 'source_id')),
}

DESCRIPTIONS = {
    'cycle': 'Record finite governance cycles, actual effects, source phases and delivery receipts over existing tasks. Frozen owner/resource reservations survive interruption; ordinary calls hold OS locks only during the call. The Python cycle_session context holds real locks for a whole live process session. No effect, scheduling, delivery or acceptance is performed by this tool.',
    'facts': 'Read or retain source-qualified decisions, artifacts and relationships with immutable history and revision CAS. Source evidence and AI interpretation remain distinct; aliases do not merge sources or tasks automatically. Reads are bounded and do not change project state.',
    'source_scan': 'Register an authorized local root and enumerate metadata through repeatable bounded pages. Sources are never written and file bodies are never read. Exclusions, budgets, directory watermarks and explicit incomplete states prevent partial scans from becoming deletion claims.',
}
