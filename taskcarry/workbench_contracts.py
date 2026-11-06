"""Public schemas for versioned workbench navigation (no engine imports)."""


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


TEXT = {"type": "string"}
SOURCE = obj({"source_id": TEXT, "revision": TEXT, "collection": TEXT,
              "local_id": TEXT, "path": TEXT}, ("source_id", "revision"))
WRITE = obj({"path": TEXT, "mode": {"type": "string", "enum": ["managed_section", "exact"]},
             "section_id": TEXT, "text": TEXT,
             "expected_sha256": {"type": ["string", "null"]}}, ("path", "text"))
TARGET = obj({"workspace": TEXT, "task_id": TEXT, "thread_id": TEXT, "source_id": TEXT,
              "host": {"type": "string", "enum": ["codex", "none"]},
              "code_assessment": obj({"status": {"type": "string", "enum": ["NO_CODE_DEPENDENCY", "ALREADY_CONTAINS", "SEPARATE_CODE_PLAN_REQUIRED"]},
                                      "reason": TEXT}, ("status", "reason")),
              "writes": {"type": "array", "items": WRITE, "maxItems": 16}},
             ("workspace", "task_id", "thread_id", "code_assessment"))
PROOF = obj({"workspace": TEXT, "plan_id": TEXT, "view_id": TEXT, "task_id": TEXT,
             "source_id": TEXT, "thread_id": TEXT, "turn_id": TEXT, "evidence_path": TEXT,
             "evidence_sha256": TEXT, "reviewer": TEXT, "observed_at": TEXT},
            ("workspace", "plan_id", "view_id", "task_id", "source_id", "thread_id", "turn_id",
             "evidence_path", "evidence_sha256", "reviewer", "observed_at"))
SCHEMAS = {"workbench": obj({
    "action": {"type": "string", "enum": ["freeze", "plan", "execute", "status", "consume"]},
    "body": TEXT, "sources": {"type": "array", "items": SOURCE, "minItems": 1, "maxItems": 50}, "view_id": TEXT,
    "targets": {"type": "array", "items": TARGET, "minItems": 1, "maxItems": 24}, "plan_id": TEXT, "workspace": TEXT,
    "proof": PROOF, "limit": {"type": "integer", "minimum": 1, "maximum": 100}, "cursor": TEXT}, ("action",))}
DESCRIPTIONS = {"workbench": "Freeze navigation and explicit source revisions; plan then publish private workbench entries without changing Git, tasks or professional instructions. Read current publication and separate reviewed-consumption evidence, or record that evidence. Generated entries do not prove host loading or business acceptance."}
