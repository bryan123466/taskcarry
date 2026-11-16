"use strict";

const assert = require("node:assert/strict");
const { createHash } = require("node:crypto");
const { readFileSync, readdirSync, mkdirSync, writeFileSync } = require("node:fs");
const { dirname, join, relative, resolve, sep } = require("node:path");
const vm = require("node:vm");

const caseRoot = resolve(__dirname, "..");
const frozenAppPath = join(caseRoot, "app");
const intakePath = join(caseRoot, "case-manifest.json");
const expectedContractSha = "77fa7df9dc17bbc95e3a728dd45e68c420dfbabdf770c3ac5ff9c714be025130";
const expectedDetectorSha = "3581c1f94f780315bc29f3af19462e994aa8571c32ec6550ab16ddec9e3770a7";

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function readFileRecord(path) {
  const data = readFileSync(path);
  return { data, evidence: { path: relative(caseRoot, path).split(sep).join("/"), bytes: data.length, sha256: sha256(data) } };
}

function readInputs() {
  const contract = readFileRecord(join(caseRoot, "INTERFACE_CONTRACT.json"));
  const algorithmDetector = readFileRecord(join(frozenAppPath, "detector.js"));
  const intake = readFileRecord(intakePath);
  const entries = readdirSync(frozenAppPath, { recursive: true, withFileTypes: true });
  assert(entries.every((entry) => entry.isFile() || entry.isDirectory()), "Unexpected file type in frozen app");
  const appFiles = entries.filter((entry) => entry.isFile())
    .map((entry) => relative(frozenAppPath, join(entry.parentPath, entry.name)).split(sep).join("/"))
    .sort();
  const frozenFiles = Object.fromEntries(appFiles.map((name) => [
    "app/" + name,
    readFileRecord(join(frozenAppPath, name)),
  ]));
  return {
    contract,
    algorithmDetector,
    intake,
    frozenFiles,
    evidence: {
      contract: contract.evidence,
      algorithm_detector: algorithmDetector.evidence,
      freeze_manifest: intake.evidence,
      freeze_manifest_field: "files",
      frozen_app_path: "app",
      frozen_app_files: Object.fromEntries(
        Object.entries(frozenFiles).map(([name, file]) => [name, file.evidence]),
      ),
    },
  };
}

function verifyFrozenInputs(inputs) {
  assert.equal(inputs.contract.evidence.sha256, expectedContractSha, "Contract SHA-256");
  assert.equal(inputs.algorithmDetector.evidence.sha256, expectedDetectorSha, "Algorithm detector SHA-256");

  const manifest = Object.fromEntries(JSON.parse(inputs.intake.data.toString("utf8")).files.map(item => [item.path, item]));
  const appNames = Object.keys(manifest).filter((name) => name.startsWith("app/")).sort();
  assert.deepEqual(Object.keys(inputs.frozenFiles).sort(), appNames, "Frozen app file paths");
  assert.equal(inputs.contract.evidence.bytes, manifest["INTERFACE_CONTRACT.json"].bytes);
  assert.equal(inputs.contract.evidence.sha256, manifest["INTERFACE_CONTRACT.json"].sha256);
  for (const name of appNames) {
    const { bytes, sha256: digest } = inputs.frozenFiles[name].evidence;
    assert.equal(bytes, manifest[name].bytes, name + " byte length");
    assert.equal(digest, manifest[name].sha256, name + " SHA-256");
  }
  assert(inputs.algorithmDetector.data.equals(inputs.frozenFiles["app/detector.js"].data), "Detector bytes differ");
}

// This function is evaluated in the same VM realm as detectFrame.
function buildEnvelope(metadata, camera, baseBox, extraPixel) {
  const { frame_id, ...clock } = metadata;
  const { width_px, height_px, pixel_format, palette_rgba } = camera;
  const pixels = new Uint8ClampedArray(width_px * height_px * 4);
  for (let offset = 0; offset < pixels.length; offset += 4) {
    pixels.set(palette_rgba.background, offset);
  }
  for (let y = baseBox.y_min; y < baseBox.y_max; y += 1) {
    for (let x = baseBox.x_min; x < baseBox.x_max; x += 1) {
      pixels.set(palette_rgba.box, (y * width_px + x) * 4);
    }
  }
  if (extraPixel) {
    pixels.set(palette_rgba.box, (extraPixel.y * width_px + extraPixel.x) * 4);
  }
  return { ...clock, frame: { frame_id, width_px, height_px, pixel_format, pixels } };
}

function changedPixels(reference, bytes, width) {
  assert.equal(reference.length, bytes.length);
  const changes = [];
  for (let offset = 0; offset < bytes.length; offset += 4) {
    if (bytes.readUInt32LE(offset) === reference.readUInt32LE(offset)) continue;
    const pixel = offset / 4;
    changes.push({
      x: pixel % width,
      y: Math.floor(pixel / width),
      before_rgba: Array.from(reference.subarray(offset, offset + 4)),
      after_rgba: Array.from(bytes.subarray(offset, offset + 4)),
    });
  }
  return changes;
}

function countPixels(bytes, rgba) {
  const target = Buffer.from(rgba).readUInt32LE(0);
  let count = 0;
  for (let offset = 0; offset < bytes.length; offset += 4) {
    if (bytes.readUInt32LE(offset) === target) count += 1;
  }
  return count;
}

function fnv1a32(bytes) {
  let hash = 2166136261;
  for (const byte of bytes) hash = Math.imul(hash ^ byte, 16777619);
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function run() {
  const before = readInputs();
  verifyFrozenInputs(before);
  const contract = JSON.parse(before.contract.data.toString("utf8"));
  const camera = contract.camera;
  const metadata = { scene_id: "clear-room", tick: 0, sim_time_ms: 0, frame_id: "clear-room:0" };
  const baseBox = { x_min: 64, x_max: 67, y_min: 32, y_max: 37 };
  assert.equal(contract.contract_id, "rc8-drone-sim-v2");
  assert(contract.scenes.some((scene) => scene.id === metadata.scene_id), "Unknown test scene");
  assert.deepEqual(
    [camera.width_px, camera.height_px, camera.pixel_format, camera.buffer_bytes, camera.minimum_component_pixels],
    [160, 120, "RGBA8", 76800, 16],
  );

  const cases = [
    { id: "A", extraPixel: null, boxPixels: 15, detections: [] },
    {
      id: "B",
      extraPixel: { x: 67, y: 36 },
      boxPixels: 16,
      detections: [{
        label: "box",
        region: { x_min: 64 / 160, y_min: 32 / 120, x_max: 68 / 160, y_max: 37 / 120 },
        cell: { dx: 0, dy: -1 },
        pixel_count: 16,
      }],
    },
    { id: "C", extraPixel: { x: 67, y: 37 }, boxPixels: 16, detections: [] },
  ];

  const context = vm.createContext({ metadata, camera, baseBox });
  const frozenDetector = before.frozenFiles["app/detector.js"];
  const vmOptions = { timeout: 5000 };
  new vm.Script(frozenDetector.data.toString("utf8"), { filename: frozenDetector.evidence.path })
    .runInContext(context, vmOptions);
  const makeEnvelope = new vm.Script("(" + buildEnvelope.toString() + ")(metadata, camera, baseBox, extraPixel)");
  const detect = new vm.Script("globalThis.RC8DroneSimV2.detectFrame(envelope)");
  const frames = [];
  let reference;

  for (const test of cases) {
    context.extraPixel = test.extraPixel;
    const envelope = makeEnvelope.runInContext(context, vmOptions);
    context.envelope = envelope;
    const input = Buffer.from(envelope.frame.pixels);
    if (test.id === "A") reference = input;
    const expected = { ...metadata, status: "ok", detections: test.detections, error: null };
    const differences = changedPixels(reference, input, camera.width_px);
    const boxPixels = countPixels(input, camera.palette_rgba.box);
    const expectedDifferences = test.extraPixel ? [{
      ...test.extraPixel,
      before_rgba: camera.palette_rgba.background,
      after_rgba: camera.palette_rgba.box,
    }] : [];
    let actual = null;
    let failure = null;
    try {
      actual = structuredClone(detect.runInContext(context, vmOptions)) ?? null;
      assert.equal(input.length, camera.buffer_bytes, "RGBA byte length");
      assert.equal(boxPixels, test.boxPixels, "Box-colored pixels");
      assert.deepEqual(differences, expectedDifferences, "Measured RGBA changes from A");
      assert(input.equals(Buffer.from(envelope.frame.pixels)), "Detector mutated the input pixels");
      assert.deepEqual(actual, expected, "DetectionResult");
    } catch (error) {
      failure = error.message;
    }

    frames.push({
      id: test.id,
      expected_box_pixels: test.boxPixels,
      actual_box_pixels: boxPixels,
      raw_rgba: { bytes: input.length, sha256: sha256(input), fnv1a32: fnv1a32(input) },
      changed_pixels_from_A: differences,
      expected,
      actual,
      passed: failure === null,
      failure,
    });
  }

  let after = null;
  let integrityFailure = null;
  try {
    const current = readInputs();
    after = current.evidence;
    verifyFrozenInputs(current);
    assert.deepEqual(after, before.evidence, "Before/after input file digests");
  } catch (error) {
    integrityFailure = error.message;
  }
  return {
    exercise: "16-pixel minimum for a 4-connected synthetic box component",
    result: frames.every((frame) => frame.passed) && integrityFailure === null ? "PASS" : "FAIL",
    node_version: process.version,
    node_platform: process.platform,
    detector_invocation: "node:vm classic script, globalThis.RC8DroneSimV2.detectFrame",
    fixture: {
      ...metadata,
      width_px: camera.width_px,
      height_px: camera.height_px,
      pixel_format: camera.pixel_format,
      background_rgba: camera.palette_rgba.background,
      box_rgba: camera.palette_rgba.box,
      base_box_half_open_px: baseBox,
    },
    frames,
    file_integrity: {
      before: before.evidence,
      after,
      matches_frozen_manifest_before_and_after: integrityFailure === null,
      detector_matches_reviewed_sha256: integrityFailure === null,
      failure: integrityFailure,
    },
  };
}

try {
  const result = run();
  const output = join(__dirname, "local");
  mkdirSync(output, { recursive: true });
  writeFileSync(join(output, "boundary-evidence.json"), JSON.stringify(result, null, 2) + "\n", "utf8");
  process.stdout.write(JSON.stringify({ result: result.result, frames: result.frames.map(frame => ({ id: frame.id, passed: frame.passed })), evidence: "continuity/local/boundary-evidence.json" }) + "\n");
  process.exitCode = result.result === "PASS" ? 0 : 1;
} catch (error) {
  process.stdout.write(JSON.stringify({ result: "FAIL", setup_failure: error.message }, null, 2) + "\n");
  process.exitCode = 1;
}
