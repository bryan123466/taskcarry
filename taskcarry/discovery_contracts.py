"""Metadata-only, pre-initialization discovery contracts."""


def obj(properties, required=()):
    return {'type': 'object', 'properties': properties, 'required': list(required),
            'additionalProperties': False}


TEXT = {'type': 'string'}
CURSOR = {'type': ['string', 'null']}
MEMBER = obj({'source_id': TEXT, 'thread_id': TEXT}, ['source_id', 'thread_id'])
THREAD = obj({'thread_id': TEXT, 'title': TEXT, 'cwd': TEXT}, ['thread_id', 'title'])
PAGE = obj({'cursor': CURSOR, 'next_cursor': CURSOR, 'receipt_ref': TEXT,
            'threads': {'type': 'array', 'maxItems': 100, 'items': THREAD}},
           ['cursor', 'next_cursor', 'receipt_ref', 'threads'])
SOURCE = obj({'source_id': TEXT, 'label': TEXT,
              'archive_scope': {'type': 'string', 'enum': ['active', 'archived', 'unknown']},
              'coverage': {'type': 'string', 'enum': ['partial', 'exhausted', 'unavailable', 'unknown']},
              'pages': {'type': 'array', 'maxItems': 50, 'items': PAGE}},
             ['source_id', 'label', 'archive_scope', 'coverage', 'pages'])
CANDIDATE = obj({'candidate_id': TEXT, 'label': TEXT, 'reason': TEXT,
                 'members': {'type': 'array', 'minItems': 1, 'maxItems': 100, 'items': MEMBER}},
                ['candidate_id', 'label', 'reason', 'members'])
LINK = obj({'onboarding_id': TEXT, 'scope_fingerprint': TEXT, 'selection_fingerprint': TEXT,
            'windows': {'type': 'array', 'minItems': 1, 'maxItems': 100, 'items': obj({
                'source_id': TEXT, 'thread_id': TEXT, 'window_thread_id': TEXT, 'source_ref': TEXT},
                ['source_id', 'thread_id', 'window_thread_id', 'source_ref'])}},
           ['onboarding_id', 'scope_fingerprint', 'selection_fingerprint', 'windows'])
DRAFT = obj({'sources': {'type': 'array', 'maxItems': 20, 'items': SOURCE},
             'candidates': {'type': 'array', 'maxItems': 100, 'items': CANDIDATE},
             'selection': obj({'candidate_id': TEXT, 'confirmation_ref': TEXT},
                              ['candidate_id', 'confirmation_ref']),
             'onboarding': LINK}, ['sources', 'candidates'])
ROOT_IDENTITY = obj({'device': TEXT, 'inode': TEXT}, ['device', 'inode'])
STATE_BINDING = {'type': ['object', 'null'], 'additionalProperties': True}
SELECTION_GUARD = {**obj({'selection_fingerprint': TEXT, 'confirmation_ref': TEXT, 'root': TEXT,
                         'root_identity': ROOT_IDENTITY, 'state_binding': STATE_BINDING},
                        ['selection_fingerprint', 'confirmation_ref', 'root', 'root_identity', 'state_binding']),
                   'type': ['object', 'null']}
PLAN = obj({'format': {'type': 'integer', 'enum': [1]}, 'root': TEXT,
            'root_identity': ROOT_IDENTITY, 'state_binding': STATE_BINDING,
            'discovery_id': TEXT, 'expected_revision': {'type': 'integer', 'minimum': 0, 'maximum': 4095},
            'expected_fingerprint': CURSOR, 'draft': DRAFT, 'selection_fingerprint': CURSOR,
            'selection_guard': SELECTION_GUARD,
            'plan_id': TEXT},
           ['format', 'root', 'root_identity', 'state_binding', 'discovery_id', 'expected_revision',
            'expected_fingerprint', 'draft', 'selection_fingerprint', 'selection_guard', 'plan_id'])
SCHEMAS = {'discovery': obj({'discovery_id': TEXT,
                           'action': {'type': 'string', 'enum': ['status', 'plan', 'execute']},
                           'expected_revision': {'type': 'integer', 'minimum': 0, 'maximum': 4095},
                           'draft': DRAFT, 'plan': PLAN}, ['discovery_id'])}
DESCRIPTIONS = {'discovery': 'Read, plan or execute a bounded metadata-only discovery draft before control initialization. AI proposes projects; recorded user selection binds later onboarding. Does not scan chats, read bodies, initialize, activate or prove acceptance.'}
