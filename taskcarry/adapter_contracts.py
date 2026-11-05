"""Bounded contracts for optional host and official-release adapters."""

SCHEMAS = {
    "codex": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "capabilities",
                    "list",
                    "read"
                ]
            },
            "executable": {
                "type": "string"
            },
            "codex_home": {
                "type": "string"
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50
            },
            "cursor": {
                "type": "string"
            },
            "archived": {
                "type": "boolean"
            },
            "thread_id": {
                "type": "string"
            },
            "timeout": {
                "type": "integer",
                "minimum": 1,
                "maximum": 60
            },
            "max_bytes": {
                "type": "integer",
                "minimum": 1024,
                "maximum": 2097152
            }
        },
        "required": [
            "action",
            "executable"
        ],
        "additionalProperties": False
    },
    "update_source": {
        "type": "object",
        "properties": {
            "channel": {
                "type": "string",
                "enum": [
                    "rc",
                    "stable"
                ]
            },
            "current_version": {
                "type": "string"
            },
            "current_artifacts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "sha256": {
                            "type": "string"
                        },
                        "size": {
                            "type": "integer",
                            "minimum": 0
                        }
                    },
                    "required": [
                        "name",
                        "sha256",
                        "size"
                    ],
                    "additionalProperties": False
                },
                "maxItems": 20
            },
            "method_refs": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "maxItems": 30
            },
            "maintenance": {
                "type": "string",
                "enum": [
                    "review",
                    "authorized_maintenance"
                ]
            },
            "expected_revision": {
                "type": "integer",
                "minimum": 0
            }
        },
        "required": [],
        "additionalProperties": False
    },
    "update_check": {
        "type": "object",
        "properties": {
            "channel": {
                "type": "string",
                "enum": [
                    "rc",
                    "stable"
                ]
            }
        },
        "required": [],
        "additionalProperties": False
    },
    "update_assess": {
        "type": "object",
        "properties": {
            "check": {
                "type": "object",
                "additionalProperties": True,
                "description": "Unmodified update_check object; validated fingerprint and source revision by engine."
            },
            "decision": {
                "type": "string",
                "enum": [
                    "prioritize",
                    "plan",
                    "keep",
                    "wait",
                    "reject"
                ]
            },
            "reason": {
                "type": "string"
            },
            "evidence_refs": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "maxItems": 30
            },
            "expected_revision": {
                "type": "integer",
                "minimum": 0
            }
        },
        "required": [
            "check",
            "decision",
            "reason"
        ],
        "additionalProperties": False
    }
}
