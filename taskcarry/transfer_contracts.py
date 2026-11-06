"""Independent contracts for explicit remote and local-media transfer plans."""

SCHEMAS = {'transfer': {
    'type': 'object', 'additionalProperties': False, 'required': ['action'],
    'properties': {
        'action': {'type': 'string', 'enum': ['publish_plan', 'publish_execute', 'copy_plan', 'copy_execute', 'verify', 'status']},
        'repository': {'type': 'string', 'description': 'Exact existing Git worktree root, only for publish_plan.'},
        'remote': {'type': 'string', 'description': 'Already-configured single push remote, only for publish_plan.'},
        'ref': {'type': 'string', 'description': 'One exact refs/heads/... or new refs/tags/... destination.'},
        'commit': {'type': 'string', 'description': 'One existing commit or local revision, frozen to its exact commit object.'},
        'plan_id': {'type': 'string', 'description': 'Exact reviewed transfer plan for execution/status/verification.'},
        'manifest': {'type': 'string', 'description': 'Exact sealed local project-recovery manifest, only for copy_plan.'},
        'destination': {'type': 'string', 'description': 'Independent local media or synchronized-directory destination, only for copy_plan.'},
        'expected_sha256': {'type': 'string', 'description': 'Independently reviewed manifest SHA-256 when available.'},
    },
}}

DESCRIPTIONS = {'transfer': 'Plan and verify one exact Git ref at an already-configured endpoint, using an expected-old-ref lease and actual-effect recovery after ambiguous transport. Existing tags and unrelated refs are preserved. Copy sealed recovery sets to explicitly selected local directories with hash verification; local copies never imply cloud upload, retention or second-machine recovery.'}
