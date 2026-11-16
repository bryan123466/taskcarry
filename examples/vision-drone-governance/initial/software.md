# Software discussion before TaskCarry

This is a synthetic seed note for an existing project conversation.

- Original task: `drone-software` — build a demonstration interface.
- Project idea: show a camera frame, detected obstacles and a suggested movement.
- Effective decision: retain `frame_id` as the frame identity. The initial display sketch expects `label` and `region`; region units and a stale-frame timestamp need joint review.
- Existing artifact: a proposed page with a frame panel, obstacle list and a visible event-source label.
- Unfinished position: the algorithm event contract has not been reviewed together with the software page. Do not claim a live model connection.
- Uncommitted work to preserve: notes about rejecting stale frames and showing an unavailable-data state.
- Open question: is the first milestone an indoor demonstration or an outdoor aircraft?

Continue this task when governance is introduced. Registering governance is not permission to replace the original task or overwrite the draft.
