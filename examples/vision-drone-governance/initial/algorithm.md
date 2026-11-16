# Algorithm discussion before TaskCarry

This is a synthetic seed note for an existing project conversation.

- Original task: `drone-algorithm` — define obstacle events and evaluation cases.
- Project idea: turn images into obstacle events, later compare approaches.
- Effective decision: keep the observation separate from the display's suggested action. A bounding box is not a measured collision distance. The algorithm proposal adds `confidence` and `timestamp_ms`; neither has been reconciled with the software interface yet.
- Existing artifact: three proposed cases: clear scene, a fixed obstacle, and an old frame whose result must not be reused.
- Unfinished position: coordinate the shared event schema with software; no model has been selected, trained or evaluated.
- Deferred task: `drone-outdoor-evaluation`, paused until the first demonstration scope is agreed.
- Open question: should the first demonstration use recorded images or wholly synthetic events?

Do not turn illustrative event data into recognition-performance evidence.
