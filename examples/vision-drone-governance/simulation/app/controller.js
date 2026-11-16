(() => {
  "use strict";

  const WORLD_WIDTH = 9;
  const WORLD_HEIGHT = 9;
  const MOVES = [
    { action: "MOVE_N", dx: 0, dy: -1 },
    { action: "MOVE_E", dx: 1, dy: 0 },
    { action: "MOVE_S", dx: 0, dy: 1 },
    { action: "MOVE_W", dx: -1, dy: 0 },
  ];

  function chooseCommand({ detection, link_state, pose, goal, visit_counts }) {
    const command = (action, reason) => ({
      tick: detection.tick,
      source_frame_id: detection.frame_id ?? null,
      action,
      reason,
    });

    if (detection.status === "missing") {
      return command("HOLD", link_state === "disconnected" ? "link_disconnected" : "frame_missing");
    }
    if (detection.status !== "ok") return command("HOLD", "invalid_frame");

    const currentDistance = Math.abs(pose.x - goal.x) + Math.abs(pose.y - goal.y);
    if (currentDistance === 0) return command("HOLD", "at_goal");

    const occupied = new Set(detection.detections.map(({ cell }) => `${cell.dx},${cell.dy}`));
    const neighbors = [];
    for (const [order, { action, dx, dy }] of MOVES.entries()) {
      const x = pose.x + dx;
      const y = pose.y + dy;
      if (x < 0 || x >= WORLD_WIDTH || y < 0 || y >= WORLD_HEIGHT) continue;
      if (occupied.has(`${dx},${dy}`)) continue;

      neighbors.push({
        action,
        order,
        distance: Math.abs(x - goal.x) + Math.abs(y - goal.y),
        visits: visit_counts[y * WORLD_WIDTH + x],
      });
    }
    if (neighbors.length === 0) return command("HOLD", "no_safe_neighbor");

    const reducing = neighbors.filter((neighbor) => neighbor.distance < currentDistance);
    if (reducing.length > 0) {
      reducing.sort((a, b) => a.distance - b.distance || a.visits - b.visits || a.order - b.order);
      return command(reducing[0].action, "toward_goal");
    }

    neighbors.sort((a, b) => a.visits - b.visits || a.distance - b.distance || a.order - b.order);
    return command(neighbors[0].action, "detour");
  }

  globalThis.RC8DroneSimV2 ??= {};
  globalThis.RC8DroneSimV2.chooseCommand = chooseCommand;
})();
