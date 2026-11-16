"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

if (process.argv.length !== 3) {
  throw new Error("Usage: node verify-algorithm.cjs INTERFACE_CONTRACT.json");
}

const sha256 = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const contractPath = path.resolve(process.argv[2]);
const contractBytes = fs.readFileSync(contractPath);
const contract = JSON.parse(contractBytes.toString("utf8").replace(/^\uFEFF/, ""));
assert.equal(contract.contract_id, "rc8-drone-sim-v2");
assert.equal(contract.schema_version, 2);

const context = vm.createContext({});
const files = {};
for (const name of ["detector.js", "controller.js"]) {
  const filename = path.join(__dirname, "..", "app", name);
  const bytes = fs.readFileSync(filename);
  new vm.Script(bytes.toString("utf8"), { filename }).runInContext(context);
  files[name] = { path: filename, sha256: sha256(bytes) };
}
const api = context.RC8DroneSimV2;
assert.equal(typeof api.detectFrame, "function");
assert.equal(typeof api.chooseCommand, "function");

const { camera, pixel_counterfactual: probe, world, logical_clock: clock } = contract;
const { width_px: width, height_px: height, palette_rgba: palette } = camera;
const checks = [];

function cellRect(col, row) {
  const inset = camera.obstacle_inset_px;
  return {
    x_min: col * camera.cell_width_px + inset,
    y_min: row * camera.cell_height_px + inset,
    x_max: (col + 1) * camera.cell_width_px - inset,
    y_max: (row + 1) * camera.cell_height_px - inset,
  };
}

function paint(pixels, rect, color) {
  for (let y = rect.y_min; y < rect.y_max; y += 1) {
    for (let x = rect.x_min; x < rect.x_max; x += 1) {
      pixels.set(color, (y * width + x) * 4);
    }
  }
}

function blankPixels() {
  const pixels = new Uint8ClampedArray(camera.buffer_bytes);
  paint(pixels, { x_min: 0, y_min: 0, x_max: width, y_max: height }, palette.background);
  return pixels;
}

function frameEnvelope(pixels) {
  return {
    scene_id: probe.scene_id,
    tick: probe.tick,
    sim_time_ms: probe.tick * clock.tick_ms,
    frame: {
      frame_id: probe.scene_id + ":" + probe.tick,
      width_px: width,
      height_px: height,
      pixel_format: camera.pixel_format,
      pixels,
    },
  };
}

function controlState({ pose = probe.pose, goal = probe.goal, link_state = "connected", visits = [] } = {}) {
  const visit_counts = Array(world.width_cells * world.height_cells).fill(0);
  visit_counts[pose.y * world.width_cells + pose.x] = world.initial_visit_count_at_start;
  for (const [x, y, count] of visits) visit_counts[y * world.width_cells + x] = count;
  return Object.freeze({
    link_state,
    pose: Object.freeze({ ...pose }),
    goal: Object.freeze({ ...goal }),
    visit_counts: Object.freeze(visit_counts),
  });
}

function run(envelope, state) {
  const detection = api.detectFrame(envelope);
  const command = api.chooseCommand({ ...state, detection });
  return structuredClone({ detection, command });
}

function withoutPixels({ frame, ...metadata }) {
  const { pixels, ...frameMetadata } = frame;
  return { ...metadata, frame: frameMetadata };
}

function pixelDigests(pixels) {
  let hash = 2166136261;
  for (const value of pixels) hash = Math.imul(hash ^ value, 16777619);
  return {
    byte_length: pixels.length,
    fnv1a32: (hash >>> 0).toString(16).padStart(8, "0"),
    sha256: sha256(Buffer.from(pixels)),
  };
}

function measureDifference(original, changed, rect) {
  let changedPixels = 0;
  let changedBytes = 0;
  let pixelsOutsideRect = 0;
  let pixelsWithBoxColor = 0;
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;
  for (let offset = 0; offset < original.length; offset += 4) {
    let delta = 0;
    for (let channel = 0; channel < 4; channel += 1) {
      if (original[offset + channel] !== changed[offset + channel]) delta += 1;
    }
    if (!delta) continue;
    const pixel = offset / 4;
    const x = pixel % width;
    const y = Math.floor(pixel / width);
    changedBytes += delta;
    changedPixels += 1;
    minX = Math.min(x, minX);
    minY = Math.min(y, minY);
    maxX = Math.max(x, maxX);
    maxY = Math.max(y, maxY);
    if (x < rect.x_min || x >= rect.x_max || y < rect.y_min || y >= rect.y_max) pixelsOutsideRect += 1;
    if (palette.box.every((value, channel) => value === changed[offset + channel])) pixelsWithBoxColor += 1;
  }
  return {
    changed_pixels: changedPixels,
    changed_bytes: changedBytes,
    pixels_outside_rectangle: pixelsOutsideRect,
    pixels_with_box_color: pixelsWithBoxColor,
    bounds_px: changedPixels ? { x_min: minX, y_min: minY, x_max: maxX + 1, y_max: maxY + 1 } : null,
  };
}

function expectedDetection(label, rect, cell) {
  return {
    label,
    region: {
      x_min: rect.x_min / width,
      y_min: rect.y_min / height,
      x_max: rect.x_max / width,
      y_max: rect.y_max / height,
    },
    cell,
    pixel_count: (rect.x_max - rect.x_min) * (rect.y_max - rect.y_min),
  };
}

function record(id, expected, observed, reproduce, verify) {
  try {
    verify();
    checks.push({ id, status: "PASS", expected, observed, reproduce });
  } catch (error) {
    checks.push({ id, status: "FAIL", expected, observed, reproduce, error: String(error) });
  }
}

const pixelsA = blankPixels();
const pixelsB = new Uint8ClampedArray(pixelsA);
const frontCol = camera.origin_cell.col + probe.changed.cell.dx;
const frontRow = camera.origin_cell.row + probe.changed.cell.dy;
const frontRect = cellRect(frontCol, frontRow);
paint(pixelsB, frontRect, palette.box);
const envelopeA = frameEnvelope(pixelsA);
const envelopeB = frameEnvelope(pixelsB);
const state = controlState();
const metadataA = withoutPixels(envelopeA);
const metadataB = withoutPixels(envelopeB);
const beforeA = pixelDigests(pixelsA);
const beforeB = pixelDigests(pixelsB);
const difference = measureDifference(pixelsA, pixelsB, frontRect);
const resultA = run(envelopeA, state);
const resultB = run(envelopeB, state);
const box = expectedDetection(probe.changed.label, frontRect, probe.changed.cell);
const expectedChangedBytes = box.pixel_count * palette.box.filter((value, index) => value !== palette.background[index]).length;
const expectedDifference = {
  changed_pixels: box.pixel_count,
  changed_bytes: expectedChangedBytes,
  pixels_outside_rectangle: 0,
  pixels_with_box_color: box.pixel_count,
  bounds_px: frontRect,
};
const unchangedPixels = sha256(Buffer.from(pixelsA)) === beforeA.sha256
  && sha256(Buffer.from(pixelsB)) === beforeB.sha256;
const noOtherChanges = JSON.stringify(metadataA) === JSON.stringify(metadataB);
const expectedCommand = (action, reason, frameId) => ({
  tick: probe.tick, source_frame_id: frameId, action, reason,
});

record("SIM-PIXELS", {
  same_nonpixel_input: true,
  input_pixels_unchanged_by_algorithm: true,
  difference: expectedDifference,
  a: { status: "ok", detections: [], command: expectedCommand(probe.baseline.command, "toward_goal", envelopeA.frame.frame_id) },
  b: { status: "ok", detections: [box], command: expectedCommand(probe.changed.command, "detour", envelopeB.frame.frame_id) },
}, {
  same_nonpixel_input: noOtherChanges,
  input_pixels_unchanged_by_algorithm: unchangedPixels,
  nonpixel_input: { envelope: metadataA, control: state },
  rectangle_px: frontRect,
  difference,
  a: { pixel_digests: beforeA, ...resultA },
  b: { pixel_digests: beforeB, ...resultB },
}, "Run the verification script with the contract path and inspect SIM-PIXELS. Both calls share the same control state and identical frame metadata.", () => {
  assert.deepEqual(withoutPixels(envelopeA), metadataA);
  assert.deepEqual(withoutPixels(envelopeB), metadataB);
  assert.ok(noOtherChanges && unchangedPixels);
  assert.notEqual(beforeA.sha256, beforeB.sha256);
  assert.deepEqual(difference, expectedDifference);
  assert.deepEqual(resultA.detection, {
    scene_id: envelopeA.scene_id, tick: envelopeA.tick, sim_time_ms: envelopeA.sim_time_ms,
    frame_id: envelopeA.frame.frame_id, detections: [], status: "ok", error: null,
  });
  assert.deepEqual(resultB.detection, { ...resultA.detection, detections: [box] });
  assert.deepEqual(resultA.command, expectedCommand(probe.baseline.command, "toward_goal", envelopeA.frame.frame_id));
  assert.deepEqual(resultB.command, expectedCommand(probe.changed.command, "detour", envelopeB.frame.frame_id));
});

const missingEnvelope = { ...envelopeB, frame: null };
const missingCases = [
  { link_state: "connected", reason: "frame_missing" },
  { link_state: "disconnected", reason: "link_disconnected" },
].map(({ link_state, reason }) => ({
  expected: { link_state, command: expectedCommand("HOLD", reason, null) },
  observed: { link_state, ...run(missingEnvelope, controlState({ link_state })) },
}));
const missingDetection = { ...resultA.detection, status: "missing", frame_id: null };
record("ALG-FRAME-STATES", {
  empty: { status: "ok", detections: [], frame_id: envelopeA.frame.frame_id, action: "MOVE_N" },
  missing: { detection: missingDetection, cases: missingCases.map((item) => item.expected) },
}, {
  empty: resultA,
  missing_input: { scene_id: missingEnvelope.scene_id, tick: missingEnvelope.tick, sim_time_ms: missingEnvelope.sim_time_ms, frame: null },
  missing: missingCases.map((item) => item.observed),
}, "After the box frame, send frame=null with valid tick metadata and exercise both link states. Compare with the empty valid frame.", () => {
  assert.equal(resultA.detection.status, "ok");
  assert.deepEqual(resultA.detection.detections, []);
  assert.equal(resultA.detection.frame_id, envelopeA.frame.frame_id);
  assert.equal(resultA.command.action, "MOVE_N");
  for (const { expected, observed } of missingCases) {
    assert.deepEqual(observed.detection, missingDetection);
    assert.deepEqual(observed.command, expected.command);
  }
});

const invalidCases = [
  { name: "frame_id", patch: { frame_id: "wrong:0" }, error: "frame_id" },
  { name: "width_px", patch: { width_px: width - 1 }, error: "dimensions" },
  { name: "pixel_format", patch: { pixel_format: "RGB24" }, error: "pixel_format" },
  { name: "pixel_length", patch: { pixels: pixelsB.subarray(0, pixelsB.length - 1) }, error: "76800 bytes" },
  { name: "pixel_type", patch: { pixels: new Uint8Array(pixelsB) }, error: "Uint8ClampedArray" },
].map(({ name, patch, error }) => {
  const envelope = { ...envelopeB, frame: { ...envelopeB.frame, ...patch } };
  const link_state = name === "pixel_length" ? "disconnected" : "connected";
  return {
    name,
    expected_error_fragment: error,
    input: {
      ...withoutPixels(envelope), link_state,
      pixels_type: envelope.frame.pixels.constructor.name,
      pixel_digests: pixelDigests(envelope.frame.pixels),
    },
    ...run(envelope, controlState({ link_state })),
  };
});
const invalidCommand = expectedCommand("HOLD", "invalid_frame", null);
record("SIM-INVALID", {
  status: "invalid", frame_id: null, detections: [], command: invalidCommand,
}, invalidCases, "Apply each listed frame mutation to the box frame, call both entry points, and compare the status, empty candidates and HOLD reason.", () => {
  for (const item of invalidCases) {
    assert.equal(item.detection.status, "invalid");
    assert.equal(item.detection.frame_id, null);
    assert.deepEqual(item.detection.detections, []);
    assert.ok(item.detection.error.includes(item.expected_error_fragment));
    assert.equal(item.detection.scene_id, probe.scene_id);
    assert.equal(item.detection.sim_time_ms, envelopeA.sim_time_ms);
    assert.deepEqual(item.command, invalidCommand);
  }
});

const componentPixels = blankPixels();
const componentDraws = [
  { label: "box", rect: { x_min: 80, y_min: 0, x_max: 84, y_max: 4 }, cell: { dx: 0, dy: -2 } },
  { label: "wall", rect: { x_min: 156, y_min: 0, x_max: 160, y_max: 4 }, cell: { dx: 2, dy: -2 } },
  { label: "wall", rect: { x_min: 152, y_min: 4, x_max: 156, y_max: 8 }, cell: { dx: 2, dy: -2 } },
  { label: "column", rect: { x_min: 30, y_min: 22, x_max: 34, y_max: 26 }, cell: { dx: -1, dy: -1 } },
];
for (const { label, rect } of componentDraws) paint(componentPixels, rect, palette[label]);
const filteredDraws = [
  { rect: { x_min: 0, y_min: 0, x_max: 5, y_max: 3 }, rgba: palette.box },
  { rect: { x_min: 16, y_min: 0, x_max: 20, y_max: 4 }, rgba: [...palette.wall.slice(0, 3), 254] },
  { rect: { x_min: 152, y_min: 50, x_max: 160, y_max: 51 }, rgba: palette.wall },
  { rect: { x_min: 0, y_min: 51, x_max: 8, y_max: 52 }, rgba: palette.wall },
];
for (const { rect, rgba } of filteredDraws) paint(componentPixels, rect, rgba);
const exactComponents = componentDraws.map(({ label, rect, cell }) => expectedDetection(label, rect, cell));
const components = structuredClone(api.detectFrame(frameEnvelope(componentPixels)));
record("ALG-COMPONENTS", { status: "ok", detections: exactComponents }, {
  drawn_components: componentDraws, additionally_painted_rectangles: filteredDraws,
  pixel_digests: pixelDigests(componentPixels), detection: components,
}, "Render the documented rectangles. Verify 4-connectivity across diagonal and row edges, exact RGBA, the 15/16 threshold, sorting, half-open image edges and exact cell boundaries.", () => {
  assert.equal(components.status, "ok");
  assert.deepEqual(components.detections, exactComponents);
});

function pixelsWithBoxes(cells) {
  const pixels = blankPixels();
  for (const [dx, dy] of cells) {
    const rect = cellRect(camera.origin_cell.col + dx, camera.origin_cell.row + dy);
    paint(pixels, rect, palette.box);
  }
  return pixels;
}

const controlCases = [
  { name: "reduce_before_visits", cells: [], visits: [[4, 5, 8]], action: "MOVE_N", reason: "toward_goal" },
  { name: "equal_distance_visit_count", cells: [], goal: { x: 5, y: 5 }, visits: [[4, 5, 5]], action: "MOVE_E", reason: "toward_goal" },
  { name: "north_before_east_when_tied", cells: [], goal: { x: 5, y: 5 }, action: "MOVE_N", reason: "toward_goal" },
  { name: "detour_visit_count", cells: [[0, -1]], visits: [[5, 6, 5], [4, 7, 3]], action: "MOVE_W", reason: "detour" },
  { name: "world_boundary_exclusion", cells: [[0, 1]], pose: { x: 0, y: 0 }, goal: { x: 0, y: 1 }, action: "MOVE_E", reason: "detour" },
  { name: "no_safe_neighbor", cells: [[0, -1], [1, 0], [0, 1], [-1, 0]], action: "HOLD", reason: "no_safe_neighbor" },
  { name: "at_goal", cells: [], goal: probe.pose, action: "HOLD", reason: "at_goal" },
].map(({ name, cells, pose, goal, visits, action, reason }) => {
  const envelope = frameEnvelope(pixelsWithBoxes(cells));
  const control = controlState({ pose, goal, visits });
  return {
    name,
    input: { frame: withoutPixels(envelope), control, box_cells: cells, pixel_digests: pixelDigests(envelope.frame.pixels) },
    expected: expectedCommand(action, reason, envelope.frame.frame_id),
    actual: run(envelope, control),
  };
});
record("ALG-CONTROL-ORDER", controlCases.map(({ name, expected }) => ({ name, command: expected })),
  controlCases.map(({ name, input, actual }) => ({ name, input, ...actual })),
  "Run the verification script and inspect the named cases for distance preference, visit counts, movement order, boundary exclusion and valid-frame HOLD reasons.", () => {
    for (const item of controlCases) {
      assert.equal(item.actual.detection.status, "ok");
      assert.deepEqual(item.actual.command, item.expected, item.name);
    }
  });

console.log(JSON.stringify({
  role: "algorithm",
  contract_id: contract.contract_id,
  schema_version: contract.schema_version,
  contract: { path: contractPath, byte_length: contractBytes.length, sha256: sha256(contractBytes) },
  runtime: { platform: process.platform, node: process.version, script_loader: "node:vm classic scripts" },
  signatures: ["globalThis.RC8DroneSimV2.detectFrame(frameEnvelope)", "globalThis.RC8DroneSimV2.chooseCommand(controlInput)"],
  files,
  checks,
}, null, 2));
process.exitCode = checks.some(({ status }) => status !== "PASS") ? 1 : 0;
