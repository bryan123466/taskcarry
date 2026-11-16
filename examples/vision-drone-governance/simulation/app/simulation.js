(() => {
  "use strict";

  const api = globalThis.RC8DroneSimV2 ??= {};
  const config = {
    "contract_id": "rc8-drone-sim-v2",
    "schema_version": 2,
    "tick_ms": 100,
    "max_ticks": 12,
    "world": {
      "width_cells": 9,
      "height_cells": 9,
      "initial_visit_count_at_start": 1
    },
    "camera": {
      "width_px": 160,
      "height_px": 120,
      "pixel_format": "RGBA8",
      "cells_x": 5,
      "cells_y": 5,
      "cell_width_px": 32,
      "cell_height_px": 24,
      "origin_cell": {
        "col": 2,
        "row": 2
      },
      "obstacle_inset_px": 2,
      "palette_rgba": {
        "background": [
          24,
          32,
          40,
          255
        ],
        "wall": [
          96,
          112,
          128,
          255
        ],
        "column": [
          220,
          90,
          50,
          255
        ],
        "box": [
          230,
          180,
          60,
          255
        ]
      }
    },
    "offsets": {
      "MOVE_N": {
        "dx": 0,
        "dy": -1
      },
      "MOVE_E": {
        "dx": 1,
        "dy": 0
      },
      "MOVE_S": {
        "dx": 0,
        "dy": 1
      },
      "MOVE_W": {
        "dx": -1,
        "dy": 0
      },
      "HOLD": {
        "dx": 0,
        "dy": 0
      }
    },
    "reasons": [
      "toward_goal",
      "detour",
      "frame_missing",
      "link_disconnected",
      "invalid_frame",
      "no_safe_neighbor",
      "at_goal"
    ],
    "scenes": [
      {
        "id": "clear-room",
        "title": "空房间到达",
        "start": {
          "x": 4,
          "y": 6
        },
        "goal": {
          "x": 4,
          "y": 2
        },
        "obstacles": [],
        "missing_ticks": []
      },
      {
        "id": "fixed-obstacle",
        "title": "固定障碍绕行",
        "start": {
          "x": 4,
          "y": 6
        },
        "goal": {
          "x": 4,
          "y": 2
        },
        "obstacles": [
          {
            "x": 4,
            "y": 5,
            "label": "box"
          },
          {
            "x": 2,
            "y": 4,
            "label": "wall"
          },
          {
            "x": 6,
            "y": 4,
            "label": "column"
          }
        ],
        "missing_ticks": []
      },
      {
        "id": "drop-and-recover",
        "title": "缺帧等待与恢复",
        "start": {
          "x": 4,
          "y": 6
        },
        "goal": {
          "x": 4,
          "y": 2
        },
        "obstacles": [
          {
            "x": 4,
            "y": 5,
            "label": "box"
          },
          {
            "x": 2,
            "y": 4,
            "label": "wall"
          },
          {
            "x": 6,
            "y": 4,
            "label": "column"
          }
        ],
        "missing_ticks": [
          1,
          2
        ]
      }
    ]
  };

  const { world, camera } = config;
  const outside = (x, y) => x < 0 || y < 0 || x >= world.width_cells || y >= world.height_cells;
  const cellIndex = (x, y) => y * world.width_cells + x;
  const colors = Object.fromEntries(Object.entries(camera.palette_rgba).map(([label, rgba]) =>
    [label, "rgb(" + rgba.slice(0, 3).join(", ") + ")"]
  ));

  function makeCamera(occupied) {
    const canvas = document.createElement("canvas");
    canvas.width = camera.width_px;
    canvas.height = camera.height_px;
    const context = canvas.getContext("2d", { alpha: false, willReadFrequently: true });
    if (!context) throw new Error("浏览器无法创建二维相机画布。");

    return (pose, frameId) => {
      context.fillStyle = colors.background;
      context.fillRect(0, 0, canvas.width, canvas.height);
      const inset = camera.obstacle_inset_px;
      for (let row = 0; row < camera.cells_y; row += 1) {
        for (let col = 0; col < camera.cells_x; col += 1) {
          const x = pose.x + col - camera.origin_cell.col;
          const y = pose.y + row - camera.origin_cell.row;
          const label = outside(x, y) ? "wall" : occupied.get(cellIndex(x, y));
          if (!label) continue;
          context.fillStyle = colors[label];
          context.fillRect(
            col * camera.cell_width_px + inset,
            row * camera.cell_height_px + inset,
            camera.cell_width_px - 2 * inset,
            camera.cell_height_px - 2 * inset
          );
        }
      }
      return {
        frame_id: frameId,
        width_px: canvas.width,
        height_px: canvas.height,
        pixel_format: camera.pixel_format,
        pixels: context.getImageData(0, 0, canvas.width, canvas.height).data
      };
    };
  }

  function hashPixels(pixels) {
    let hash = 2166136261;
    for (const byte of pixels) hash = Math.imul(hash ^ byte, 16777619);
    return (hash >>> 0).toString(16).padStart(8, "0");
  }

  function updateLink(previous, previousCount, valid) {
    if (valid) {
      const event = previous === "waiting" ? "connected" : previous === "disconnected" ? "reconnected" : null;
      return { state: "connected", count: 0, event };
    }
    const count = previousCount + 1;
    if (count >= 2 && previous !== "disconnected") {
      return { state: "disconnected", count, event: "disconnected" };
    }
    return { state: previous, count, event: null };
  }

  function requireCommand(command, detection) {
    if (!command || command.tick !== detection.tick || command.source_frame_id !== detection.frame_id
      || !Object.hasOwn(config.offsets, command.action) || !config.reasons.includes(command.reason)) {
      throw new Error("控制命令与合同不符。");
    }
  }

  function createSimulation(sceneId) {
    const scene = config.scenes.find(candidate => candidate.id === sceneId);
    if (!scene) throw new RangeError("未知场景 " + sceneId);

    const occupied = new Map(scene.obstacles.map(({ x, y, label }) => [cellIndex(x, y), label]));
    const missingTicks = new Set(scene.missing_ticks);
    const renderCamera = makeCamera(occupied);
    let pose, visitCounts, route, records, lastEnvelope, runState, linkState, consecutiveUnusable;

    function reset() {
      pose = { ...scene.start };
      visitCounts = Array(world.width_cells * world.height_cells).fill(0);
      visitCounts[cellIndex(pose.x, pose.y)] = world.initial_visit_count_at_start;
      route = [{ ...pose }];
      records = [];
      lastEnvelope = null;
      runState = "ready";
      linkState = "waiting";
      consecutiveUnusable = 0;
    }

    function start() {
      if (runState === "ready" || runState === "paused") runState = "running";
    }

    function pause() {
      if (runState === "running") runState = "paused";
    }

    function step({ replacePixels, commandOverride } = {}) {
      if (runState !== "running") return null;
      if (typeof api.detectFrame !== "function" || typeof api.chooseCommand !== "function") {
        throw new Error("缺少检测或控制脚本。");
      }
      const tick = records.length;
      const simTime = tick * config.tick_ms;
      const frame = missingTicks.has(tick) ? null : renderCamera(pose, scene.id + ":" + tick);
      if (frame && replacePixels) {
        const pixels = replacePixels(frame.pixels.slice());
        if (!(pixels instanceof Uint8ClampedArray)) throw new TypeError("替换像素须为 Uint8ClampedArray。");
        frame.pixels = pixels.slice();
      }

      const envelope = { scene_id: scene.id, tick, sim_time_ms: simTime, frame };
      const digest = frame && hashPixels(frame.pixels);
      const detection = api.detectFrame(envelope);
      if (!detection || detection.scene_id !== scene.id || detection.tick !== tick
        || detection.sim_time_ms !== simTime || !["ok", "missing", "invalid"].includes(detection.status)
        || !Array.isArray(detection.detections)
        || detection.frame_id !== (detection.status === "ok" ? frame?.frame_id : null)) {
        throw new Error("检测结果与当前帧不匹配。");
      }

      const link = updateLink(linkState, consecutiveUnusable, detection.status === "ok");
      const chosen = api.chooseCommand({
        detection,
        link_state: link.state,
        pose: { ...pose },
        goal: { ...scene.goal },
        visit_counts: visitCounts.slice()
      });
      requireCommand(chosen, detection);
      const command = commandOverride ? { ...chosen, action: commandOverride.action, reason: commandOverride.reason } : chosen;
      if (commandOverride) requireCommand(command, detection);

      const before = { ...pose };
      let after = { ...pose };
      let collision = false;
      if (command.action !== "HOLD") {
        const { dx, dy } = config.offsets[command.action];
        const x = pose.x + dx;
        const y = pose.y + dy;
        collision = outside(x, y) || occupied.has(cellIndex(x, y));
        if (!collision) {
          after = { x, y };
          visitCounts[cellIndex(x, y)] += 1;
          route.push({ ...after });
        }
      }
      const arrived = !collision && after.x === scene.goal.x && after.y === scene.goal.y;
      if (collision) runState = "collision";
      else if (arrived) runState = "arrived";
      else if (tick + 1 >= config.max_ticks) runState = "timeout";

      pose = after;
      linkState = link.state;
      consecutiveUnusable = link.count;
      lastEnvelope = envelope;
      const record = {
        tick,
        sim_time_ms: simTime,
        frame_digest: detection.status === "ok" ? digest : null,
        pose_before: before,
        pose_after: after,
        detection,
        link_state: linkState,
        consecutive_unusable: consecutiveUnusable,
        link_event: link.event,
        command,
        run_state: runState,
        collision,
        arrived
      };
      records.push(record);
      return structuredClone(record);
    }

    function exportRun() {
      return structuredClone({
        contract_id: config.contract_id,
        schema_version: config.schema_version,
        scene_id: scene.id,
        start: scene.start,
        goal: scene.goal,
        route,
        records,
        run_state: runState,
        clock_ms: config.tick_ms
      });
    }

    function readState() {
      return {
        ...exportRun(),
        pose: { ...pose },
        visit_counts: visitCounts.slice(),
        link_state: linkState,
        consecutive_unusable: consecutiveUnusable,
        next_tick: records.length,
        grid: { width: world.width_cells, height: world.height_cells }
      };
    }

    function readFrame() {
      return structuredClone(lastEnvelope);
    }

    reset();
    return { start, pause, reset, step, readState, readFrame, exportRun };
  }

  api.createSimulation = createSimulation;
  api.listScenes = () => config.scenes.map(({ id, title }) => ({ id, title }));
})();
