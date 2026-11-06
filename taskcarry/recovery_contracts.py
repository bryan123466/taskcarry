"""Recovery contracts kept independent of the shared dispatcher."""

def obj(properties, required=()):
    return {'type': 'object', 'properties': properties, 'required': list(required), 'additionalProperties': False}


TEXT = {'type': 'string'}
TEXTS = {'type': 'array', 'items': TEXT, 'maxItems': 4096, 'uniqueItems': True}
SOURCE = obj({'name': TEXT, 'path': TEXT, 'kind': {'type': 'string', 'enum': ['git', 'files']},
              'paths': TEXTS, 'refs': TEXTS}, ['name'])
SCHEMAS = {'recovery': obj({
    'action': {'type': 'string', 'enum': ['backup_plan', 'backup_execute', 'verify', 'status', 'history',
                                          'restore_plan', 'restore_execute', 'activation_plan', 'activate']},
    'destination': TEXT, 'plan_id': TEXT, 'manifest': TEXT, 'expected_sha256': TEXT,
    'workspaces': {'type': 'array', 'items': SOURCE, 'maxItems': 100},
    'payloads': {'type': 'array', 'items': SOURCE, 'maxItems': 100},
    'authorization': TEXT, 'old_writer_stopped': {'type': 'boolean'},
    'native_evidence': obj({'source_id': TEXT, 'replica_id': TEXT, 'control': TEXT,
                            'doctor': {'type': 'boolean'}, 'status': {'type': 'boolean'},
                            'evidence_ref': TEXT}, ['source_id', 'replica_id', 'control', 'doctor', 'status', 'evidence_ref']),
    'old_replica_id': TEXT,
    'collection': TEXT, 'local_id': TEXT, 'cursor': TEXT,
    'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100},
}, ['action'])}
DESCRIPTIONS = {'recovery': 'Plan, capture and verify a selected portable recovery set; restore real Git history, index, WIP and governance state into an independent standby copy. Writer activation is a separate explicit handoff, never multiwriter database synchronization.'}
