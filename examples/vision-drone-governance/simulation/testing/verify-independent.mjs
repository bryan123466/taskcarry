import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, readdir, realpath, writeFile } from "node:fs/promises";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { openChrome, waitFor } from "./chrome.mjs";

const testing = path.dirname(fileURLToPath(import.meta.url));
const algorithmEntries = ["detector.js", "controller.js"];
const requiredAppEntries = ["index.html", "styles.css", "simulation.js", "monitor.js", ...algorithmEntries];
const scenarioChecks = {
  "clear-room": "SIM-CLEAR",
  "fixed-obstacle": "SIM-DETOUR",
  "drop-and-recover": "SIM-DROP"
};
const requiredIds = ["SIM-OFFLINE", ...Object.values(scenarioChecks), "SIM-PIXELS",
  "SIM-COLLISION", "SIM-INVALID", "SIM-TIMEOUT", "SIM-EXPORT"];
const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const decodeJSON = bytes => JSON.parse(bytes.toString("utf8").replace(/^\uFEFF/, ""));
const saveJSON = (file, object) => writeFile(file, JSON.stringify(object, null, 2) + "\n");

class Pending extends Error {}

async function readPinned(file, expected) {
  assert(path.isAbsolute(file), "需要绝对路径 " + file);
  assert.match(expected ?? "", /^[\da-f]{64}$/, "缺少交付 SHA-256 " + file);
  const actual = await readFile(file);
  assert.equal(sha256(actual), expected, "交付文件摘要不符 " + file);
  return actual;
}

async function listFiles(root, prefix = "") {
  const names = [];
  for (const entry of await readdir(path.join(root, prefix), { withFileTypes: true })) {
    const relative = prefix ? prefix + "/" + entry.name : entry.name;
    if (entry.isDirectory()) names.push(...await listFiles(root, relative));
    else if (entry.isFile()) names.push(relative);
    else throw new Error("应用目录含非普通文件 " + relative);
  }
  return names.sort();
}

async function readDelivery(handoff) {
  assert(path.isAbsolute(handoff.app_directory), "交付 app 路径应为绝对路径");
  const source = await realpath(handoff.app_directory);
  const contractBytes = await readPinned(path.join(testing, "..", "INTERFACE_CONTRACT.json"), handoff.contract_sha256);
  const contract = decodeJSON(contractBytes);
  assert.equal(contract.contract_id, "rc8-drone-sim-v2");
  assert.equal(contract.schema_version, 2);
  assert.deepEqual(contract.scenes.map(scene => scene.id).sort(), Object.keys(scenarioChecks).sort());
  const packagedContract = path.join(source, "..", "INTERFACE_CONTRACT.json");
  assert.deepEqual(await readPinned(packagedContract, handoff.contract_sha256), contractBytes);

  const evidence = await Promise.all(["software_evidence", "algorithm_evidence"].map(async name => {
    const entry = handoff[name];
    assert(entry?.path, "缺少交付证据 " + name);
    return readPinned(entry.path, entry.sha256);
  }));
  const [software, algorithm] = evidence.map(decodeJSON);
  assert.equal(software.contract_id, contract.contract_id);
  assert.equal(software.contract_sha256, handoff.contract_sha256);
  assert.equal(algorithm.contract_id, contract.contract_id);
  assert.equal(algorithm.contract.sha256, handoff.contract_sha256);

  const entries = await listFiles(source);
  assert.deepEqual(entries, Object.keys(handoff.app_sha256).sort(), "实际文件清单与交付清单不符");
  assert.deepEqual(software.file_sha256, {
    "INTERFACE_CONTRACT.json": handoff.contract_sha256,
    ...Object.fromEntries(entries.map(name => ["app/" + name, handoff.app_sha256[name]]))
  }, "软件自测清单所指文件");
  for (const name of requiredAppEntries) assert(entries.includes(name), "交付包缺文件 " + name);
  for (const name of algorithmEntries) {
    const pinned = handoff.app_sha256[name];
    const integrated = software.algorithm_files["app/" + name];
    assert.equal(pinned, algorithm.files[name].sha256, "集成算法摘要不符 " + name);
    for (const field of ["source_sha256_at_integration", "packaged_sha256", "browser_script_sha256"]) {
      assert.equal(integrated[field], pinned, "软件集成记录 " + name + " " + field);
    }
    await readPinned(algorithm.files[name].path, pinned);
  }
  const files = new Map(await Promise.all(entries.map(async name => [
    name, await readPinned(path.join(source, name), handoff.app_sha256[name])
  ])));
  const supporting = new Map([["software-evidence.json", evidence[0]]]);
  for (const name of ["SOFTWARE_RUN.md", "verify-software.mjs"]) {
    supporting.set(name, await readPinned(path.join(source, "..", name), handoff.supporting_sha256[name]));
  }
  return { contract, contractBytes, files, source, supporting };
}

async function makeCopy(dir, delivery) {
  const copy = path.join(dir, "app");
  for (const [name, bytes] of delivery.files) {
    const file = path.join(copy, name);
    await mkdir(path.dirname(file), { recursive: true });
    await writeFile(file, bytes, { flag: "wx" });
    assert.deepEqual(await readFile(file), bytes, "独立目录副本摘要不符 " + name);
  }
  await writeFile(path.join(dir, "INTERFACE_CONTRACT.json"), delivery.contractBytes, { flag: "wx" });
  for (const [name, bytes] of delivery.supporting) await writeFile(path.join(dir, name), bytes, { flag: "wx" });
  return copy;
}

function fnv1a(bytes) {
  let hash = 2166136261;
  for (const byte of bytes) hash = Math.imul(hash ^ byte, 16777619);
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function validateRun(log, scene, contract) {
  const { expected } = scene;
  const { logical_clock: clock, enum: enums } = contract;
  assert.equal(log.contract_id, contract.contract_id);
  assert.equal(log.schema_version, contract.schema_version);
  assert.equal(log.clock_ms, clock.tick_ms);
  assert.equal(log.scene_id, scene.id);
  assert.deepEqual(log.start, scene.start);
  assert.deepEqual(log.goal, scene.goal);
  assert.equal(log.run_state, expected.terminal_state);
  assert.deepEqual(log.route, expected.route, "场景轨迹");
  assert.equal(log.records.length, expected.terminal_tick + 1);
  assert.deepEqual(log.records.map(record => record.command.action), expected.actions);
  assert.equal(log.records.filter(record => record.collision === true).length, expected.collisions);
  assert.equal(log.records[0].detection.detections.length, expected.first_detection_count);
  let pose = scene.start;
  for (const [tick, record] of log.records.entries()) {
    const { detection, command } = record;
    assert.equal(record.tick, tick);
    assert.equal(record.sim_time_ms, tick * clock.tick_ms);
    assert.equal(detection.scene_id, scene.id);
    assert.equal(detection.tick, tick);
    assert.equal(detection.sim_time_ms, record.sim_time_ms);
    const present = !scene.missing_ticks.includes(tick);
    assert.equal(detection.status, present ? "ok" : "missing");
    assert.equal(detection.frame_id, present ? scene.id + ":" + tick : null);
    assert.equal(detection.error, null);
    if (present) assert.match(record.frame_digest, /^[\da-f]{8}$/);
    else {
      assert.equal(record.frame_digest, null);
      assert.deepEqual(detection.detections, []);
    }
    assert(Array.isArray(detection.detections));
    assert(!JSON.stringify(record).includes('"pixels":'), "导出包含原始像素");
    assert.equal(command.tick, tick);
    assert.equal(command.source_frame_id, detection.frame_id);
    assert(enums.reason.includes(command.reason));
    assert(enums.link_state.includes(record.link_state));
    assert.deepEqual(record.pose_before, pose);
    const { dx, dy } = contract.movement.offsets[command.action];
    pose = { x: pose.x + dx, y: pose.y + dy };
    assert.deepEqual(record.pose_after, pose);
    const last = tick === expected.terminal_tick;
    assert.equal(record.run_state, last ? expected.terminal_state : "running");
    assert.equal(record.arrived, last);
    assert.equal(record.collision, false);
  }
  assert.deepEqual(pose, scene.goal);
  if (expected.link_events) {
    const events = Object.fromEntries(log.records.filter(r => r.link_event !== null).map(r => [r.link_event, r.tick]));
    assert.deepEqual(events, expected.link_events);
  }
}

function rectangle(camera, col, row) {
  const { cell_width_px: w, cell_height_px: h, obstacle_inset_px: margin } = camera;
  return { x0: col * w + margin, y0: row * h + margin, x1: (col + 1) * w - margin, y1: (row + 1) * h - margin };
}

function expectedDetection(camera, label, dx, dy) {
  const rect = rectangle(camera, camera.origin_cell.col + dx, camera.origin_cell.row + dy);
  return {
    label,
    region: {
      x_min: rect.x0 / camera.width_px, y_min: rect.y0 / camera.height_px,
      x_max: rect.x1 / camera.width_px, y_max: rect.y1 / camera.height_px
    },
    cell: { dx, dy },
    pixel_count: (rect.x1 - rect.x0) * (rect.y1 - rect.y0)
  };
}

function checkPixelDifference(baseline, changed, rectangle, camera) {
  assert.equal(baseline.length, camera.buffer_bytes);
  assert.equal(changed.length, camera.buffer_bytes);
  let pixels = 0;
  let changedBytes = 0;
  for (let y = 0; y < camera.height_px; y++) {
    for (let x = 0; x < camera.width_px; x++) {
      const start = (y * camera.width_px + x) * 4;
      const isBox = x >= rectangle.x0 && x < rectangle.x1 && y >= rectangle.y0 && y < rectangle.y1;
      const expected = isBox ? camera.palette_rgba.box : camera.palette_rgba.background;
      let difference = false;
      for (let channel = 0; channel < 4; channel++) {
        assert.equal(baseline[start + channel], camera.palette_rgba.background[channel], "A 必须是无障碍的首帧");
        assert.equal(changed[start + channel], expected[channel], "B 只能改变合同规定的前方矩形");
        if (baseline[start + channel] !== changed[start + channel]) {
          difference = true;
          changedBytes++;
        }
      }
      if (difference) pixels++;
    }
  }
  assert.equal(pixels, (rectangle.x1 - rectangle.x0) * (rectangle.y1 - rectangle.y0));
  assert(changedBytes > 0);
  return { changed_pixels: pixels, changed_bytes: changedBytes, changed_rectangle: rectangle };
}

function browserActions(chrome, out, copy, contract) {
  const mainUrl = pathToFileURL(path.join(copy, "index.html")).href;
  const output = name => path.join(out, name);

  async function ui() {
    return chrome.evaluate(() => {
      const get = id => document.getElementById(id);
      if (!get("run-state") || !get("scene-select").options.length) return null;
      return {
        url: location.href, scene_id: get("scene-select").value,
        scenes: Array.from(get("scene-select").options, option => option.value),
        state: get("run-state").dataset.state, link: get("link-state").dataset.state,
        state_label: get("run-state").textContent, tick: get("logical-tick").textContent,
        time: get("logical-time").textContent, log_rows: get("log-rows").rows.length,
        pose_label: get("pose-value").textContent, start_disabled: get("start-button").disabled,
        frame_status: get("frame-status").textContent, detections_text: get("detections").textContent,
        error: get("app-error").hidden ? null : get("app-error").textContent
      };
    });
  }

  async function open(testMode = false) {
    await chrome.send("Page.navigate", { url: "about:blank" });
    const url = testMode ? mainUrl + "#test" : mainUrl;
    const nav = await chrome.send("Page.navigate", { url });
    assert(!nav.errorText, nav.errorText);
    return waitFor(async () => {
      try {
        const state = await ui();
        return state?.url === url && state;
      } catch (error) {
        if (!/execution context|Cannot find context/i.test(error.message)) throw error;
        return null;
      }
    }, "应用本地入口");
  }

  async function click(id) {
    await chrome.evaluate(buttonId => {
      const button = document.getElementById(buttonId);
      if (!button || button.disabled) throw new Error("无法操作按钮 " + buttonId);
      button.click();
    }, id);
  }

  async function select(id) {
    await chrome.evaluate(sceneId => {
      const select = document.getElementById("scene-select");
      select.value = sceneId;
      if (select.value !== sceneId) throw new Error("缺失场景 " + sceneId);
      select.dispatchEvent(new Event("change", { bubbles: true }));
    }, id);
  }

  function assertReset(state, scene) {
    assert.equal(state.scene_id, scene.id);
    assert.equal(state.state, "ready");
    assert.equal(state.link, "waiting");
    assert.equal(state.tick, "—");
    assert.equal(state.log_rows, 0);
    assert(state.pose_label.includes("(" + scene.start.x + ", " + scene.start.y + ")"), "重置后应显示场景起点");
    assert.equal(state.error, null);
  }

  async function play(scene, label) {
    await select(scene.id);
    await click("reset-button");
    assertReset(await ui(), scene);
    return startAndExport(scene.id, label);
  }

  async function startAndExport(sceneId, label) {
    await click("start-button");
    const terminal = await waitFor(async () => {
      const state = await ui();
      if (state.error) throw new Error(state.error);
      return ["arrived", "collision", "timeout"].includes(state.state) && state;
    }, sceneId + " 播放终态");
    const download = await exportLog(sceneId, label);
    return { ...download, terminal };
  }

  async function exportLog(sceneId, label) {
    const directory = output(label);
    await mkdir(directory);
    await chrome.send("Browser.setDownloadBehavior", { behavior: "allow", downloadPath: directory });
    await click("export-button");
    const filename = contract.contract_id + "-" + sceneId + ".json";
    const bytes = await waitFor(async () => {
      try { return await readFile(path.join(directory, filename)); }
      catch (error) { if (error.code !== "ENOENT") throw error; return null; }
    }, sceneId + " 实际浏览器下载");
    return { path: label + "/" + filename, sha256: sha256(bytes), log: decodeJSON(bytes) };
  }

  async function testAvailable() {
    return chrome.evaluate(() => {
      const test = globalThis.RC8DroneSimV2?.testMonitor;
      return Boolean(test && ["selectScene", "step", "readState", "readFrame"].every(name => typeof test[name] === "function"));
    });
  }

  return { ui, open, click, select, assertReset, play, startAndExport, exportLog, testAvailable };
}

async function firstFrame(chrome, sceneId, change) {
  const { pixels_b64, ...result } = await chrome.evaluate((id, pixelChange) => {
    const api = globalThis.RC8DroneSimV2;
    const test = api.testMonitor;
    test.selectScene(id);
    const before = test.readState();
    const originalDetect = api.detectFrame;
    const originalChoose = api.chooseCommand;
    let envelope;
    let controlInput;
    let pixels;
    api.detectFrame = input => {
      const { frame, ...metadata } = input;
      const { pixels: rgba, ...header } = frame;
      pixels = rgba.slice();
      envelope = { ...metadata, frame: { ...header, byte_length: rgba.length } };
      return originalDetect.call(api, input);
    };
    api.chooseCommand = input => {
      controlInput = structuredClone(input);
      return originalChoose.call(api, input);
    };
    try {
      const record = test.step(pixelChange ? {
        replacePixels(bytes) {
          const { x0, y0, x1, y1 } = pixelChange.rectangle;
          for (let y = y0; y < y1; y++) {
            for (let x = x0; x < x1; x++) bytes.set(pixelChange.rgba, (y * pixelChange.width + x) * 4);
          }
          return bytes;
        }
      } : undefined);
      if (!record || !pixels || !envelope || !controlInput) throw new Error("测试入口缺少实际算法调用证据");
      const retained = test.readFrame();
      const bitmap = document.getElementById("camera-pixels");
      const visible = bitmap.getContext("2d").getImageData(0, 0, bitmap.width, bitmap.height).data;
      function encode(bytes) {
        let text = "";
        for (let offset = 0; offset < bytes.length; offset += 4096) text += String.fromCharCode(...bytes.subarray(offset, offset + 4096));
        return btoa(text);
      }
      return {
        before, envelope, controlInput, record,
        pixels_b64: encode(pixels),
        canvas_matches_delivered: encode(visible) === encode(pixels),
        retained_frame_matches_delivered: encode(retained.frame.pixels) === encode(pixels)
      };
    } finally {
      api.detectFrame = originalDetect;
      api.chooseCommand = originalChoose;
    }
  }, sceneId, change);
  return { ...result, bytes: Buffer.from(pixels_b64, "base64") };
}

async function runChecks(chrome, output, copy, contract) {
  const actions = browserActions(chrome, output, copy, contract);
  const data = {};
  const checks = [];
  const artifacts = name => path.join(output, name);
  const settleMs = Math.max(750, 3 * contract.logical_clock.tick_ms);
  const sceneFor = id => contract.scenes.find(scene => scene.id === id);
  const clear = sceneFor("clear-room");
  const camera = contract.camera;
  const browserExports = {};

  async function check(id, expected, reproduce, run) {
    const row = { id, status: "PENDING", expected, reproduce };
    checks.push(row);
    try {
      row.observed = await run();
      row.status = "PASS";
    } catch (error) {
      row.status = error instanceof Pending ? "PENDING" : "FAIL";
      row.observed = { message: error.message };
    }
    console.log(id + " " + row.status + (row.observed.message ? " " + row.observed.message : ""));
  }

  await actions.open();
  let offlineFailure;
  try {
    const first = await actions.ui();
    assert.deepEqual(first.scenes, contract.scenes.map(scene => scene.id));
    assert.equal(new URL(first.url).protocol, "file:");
    for (const scene of contract.scenes) {
      await actions.select(scene.id);
      actions.assertReset(await actions.ui(), scene);
    }
    const pauseScene = sceneFor("drop-and-recover");
    await actions.select(pauseScene.id);
    await actions.click("start-button");
    const started = await actions.ui();
    assert.equal(started.state, "running");
    assert(started.log_rows >= 1, "启动后应生成逐拍记录");
    await actions.click("pause-button");
    const paused = await actions.ui();
    assert.equal(paused.state, "paused");
    await chrome.screenshot(artifacts("paused.png"));
    const start = performance.now();
    await delay(settleMs);
    const pausedLater = await actions.ui();
    const pauseWaitMs = Math.round(performance.now() - start);
    assert.deepEqual(pausedLater, paused, "暂停期间界面拍号、位置和日志应保持");
    await actions.click("start-button");
    const resumed = await actions.ui();
    assert.equal(resumed.log_rows, paused.log_rows + 1, "继续后应推进到下一拍");
    assert.equal(resumed.tick, "拍 " + paused.log_rows);
    await actions.click("reset-button");
    const reset = await actions.ui();
    actions.assertReset(reset, pauseScene);
    data.offline_controls = { first, started, paused, paused_later: pausedLater, resumed, reset,
      pause_wait_ms: pauseWaitMs };
  } catch (error) {
    offlineFailure = error;
  }

  for (const scene of contract.scenes) {
    browserExports[scene.id] = [];
    for (const repeat of [1, 2]) {
      try {
        browserExports[scene.id].push(await actions.play(scene, "round-" + repeat + "-" + scene.id));
      } catch (error) {
        browserExports[scene.id].push({ error: error.message });
      }
    }
  }
  data.browser_exports = browserExports;
  data.normal_browser_activity = structuredClone(chrome.activity);
  await saveJSON(artifacts("browser-exports.json"), browserExports);
  await saveJSON(artifacts("browser-activity.json"), data.normal_browser_activity);

  await check("SIM-OFFLINE", { protocol: "file:", scenes: contract.scenes.map(scene => scene.id),
    pause_min_ms: 2 * contract.logical_clock.tick_ms, local_only: true, exceptions: 0 },
  "打开独立副本入口，通过场景菜单和按钮启动、暂停、继续及重置。", async () => {
    if (offlineFailure) throw offlineFailure;
    const activity = data.normal_browser_activity;
    assert.deepEqual(activity.external, [], "页面不应尝试外部请求");
    assert.deepEqual(activity.exceptions, [], "页面运行异常");
    for (const request of activity.requests) {
      const url = new URL(request.url);
      if (["blob:", "about:", "data:"].includes(url.protocol)) continue;
      assert.equal(url.protocol, "file:", "页面资源应来自独立副本");
      const relative = path.relative(copy, fileURLToPath(url));
      assert(relative && !relative.startsWith("..") && !path.isAbsolute(relative), "页面资源越出独立副本");
    }
    const failures = activity.failures.filter(row => !(row.url?.startsWith("blob:") && row.error === "net::ERR_ABORTED"));
    assert.deepEqual(failures, [], "页面资源读取失败");
    return { ...data.offline_controls, requests: activity.requests.length, external_requests: 0, exceptions: 0,
      screenshots: ["paused.png"] };
  });

  let testHookProblem;
  try {
    await actions.open(true);
    if (!await actions.testAvailable()) testHookProblem = "最终包 #test 页面缺少 testMonitor 的验收入口";
  } catch (error) {
    testHookProblem = error.message;
  }
  function requireHook() {
    if (testHookProblem) throw new Pending(testHookProblem);
  }

  for (const scene of contract.scenes) {
    const id = scenarioChecks[scene.id];
    await check(id, scene.expected, "场景菜单选中 " + scene.id + " 后重置、启动并导出，必要时逐拍读取 #test。",
      async () => {
        const trace = browserExports[scene.id][0];
        if (trace.error) throw new Error(trace.error);
        validateRun(trace.log, scene, contract);
        assert.equal(trace.terminal.log_rows, trace.log.records.length);
        const observed = { export_path: trace.path, export_sha256: trace.sha256,
          terminal: trace.log.run_state, terminal_tick: trace.log.records.at(-1).tick,
          actions: trace.log.records.map(record => record.command.action),
          route: trace.log.route, collisions: trace.log.records.filter(record => record.collision).length,
          first_record: trace.log.records[0] };
        if (id === "SIM-DETOUR") {
          requireHook();
          const { bytes, ...first } = await firstFrame(chrome, scene.id, null);
          const expected = scene.obstacles.map(obstacle => expectedDetection(camera, obstacle.label,
            obstacle.x - scene.start.x, obstacle.y - scene.start.y))
            .sort((a, b) => a.region.y_min - b.region.y_min || a.region.x_min - b.region.x_min);
          for (const obstacle of expected) {
            const col = camera.origin_cell.col + obstacle.cell.dx;
            const row = camera.origin_cell.row + obstacle.cell.dy;
            const rect = rectangle(camera, col, row);
            const offset = (rect.y0 * camera.width_px + rect.x0) * 4;
            assert.deepEqual([...bytes.subarray(offset, offset + 4)], camera.palette_rgba[obstacle.label]);
          }
          assert.equal(bytes.length, camera.buffer_bytes);
          assert.deepEqual(first.record.detection.detections, expected);
          assert.deepEqual(first.record, trace.log.records[0]);
          assert.equal(fnv1a(bytes), first.record.frame_digest);
          assert(first.canvas_matches_delivered && first.retained_frame_matches_delivered);
          await writeFile(artifacts("detour-first.rgba"), bytes);
          await chrome.screenshot(artifacts("detour-first.png"));
          observed.frame = { file: "detour-first.rgba", sha256: sha256(bytes), frame_digest: fnv1a(bytes),
            screenshot: "detour-first.png", ...first };
        }
        if (id === "SIM-DROP") {
          requireHook();
          const samples = await chrome.evaluate(sceneId => {
            const api = globalThis.RC8DroneSimV2;
            const test = api.testMonitor;
            test.selectScene(sceneId);
            return Array.from({ length: 4 }, () => {
              const record = test.step();
              const envelope = test.readFrame();
              return { record, visits: test.readState().visit_counts,
                frame: envelope.frame && { id: envelope.frame.frame_id, byte_length: envelope.frame.pixels.length },
                repeated_detection: api.detectFrame(envelope),
                frame_status: document.getElementById("frame-status").textContent,
                detections_text: document.getElementById("detections").textContent };
            });
          }, scene.id);
          observed.first_steps = samples;
          await saveJSON(artifacts("drop-first-steps.json"), samples);
          assert.deepEqual(samples.map(s => s.record), trace.log.records.slice(0, 4));
          assert.deepEqual(samples.map(s => s.repeated_detection), samples.map(s => s.record.detection));
          assert.deepEqual(samples.map(s => s.record.consecutive_unusable), [0, 1, 2, 0]);
          assert.deepEqual(samples.map(s => s.record.link_state), ["connected", "connected", "disconnected", "connected"]);
          assert.deepEqual(samples.map(s => s.record.link_event), ["connected", null, "disconnected", "reconnected"]);
          for (const missed of samples.slice(1, 3)) {
            assert.equal(missed.frame, null);
            assert.equal(missed.detections_text, "");
            assert.match(missed.frame_status, /缺帧/);
            assert.equal(missed.record.command.action, "HOLD");
            assert.deepEqual(missed.record.pose_after, missed.record.pose_before);
            assert.deepEqual(missed.visits, samples[0].visits);
          }
          assert.deepEqual(samples.slice(1, 3).map(s => s.record.command.reason), ["frame_missing", "link_disconnected"]);
          assert.deepEqual(samples[3].frame, { id: scene.id + ":3", byte_length: camera.buffer_bytes });
          assert.equal(samples[3].record.command.source_frame_id, samples[3].frame.id);
          assert.equal(samples[3].record.detection.status, "ok");
        }
        return observed;
      });
  }

  await check("SIM-PIXELS", contract.pixel_counterfactual,
    "在 #test 重置同一个 clear-room，各推进首拍。通过 replacePixels 仅改变前方矩形并核对算法实际入参。",
    async () => {
      requireHook();
      const expected = contract.pixel_counterfactual;
      const { dx, dy } = expected.changed.cell;
      const region = rectangle(camera, camera.origin_cell.col + dx, camera.origin_cell.row + dy);
      const { bytes: a, ...baseline } = await firstFrame(chrome, expected.scene_id, null);
      const { bytes: b, ...changed } = await firstFrame(chrome, expected.scene_id,
        { rectangle: region, rgba: camera.palette_rgba.box, width: camera.width_px });
      const aDigest = fnv1a(a);
      const bDigest = fnv1a(b);
      await writeFile(artifacts("pixel-A.rgba"), a);
      await writeFile(artifacts("pixel-B.rgba"), b);
      await chrome.screenshot(artifacts("pixel-B.png"));

      const { detection: aDetection, ...aControls } = baseline.controlInput;
      const { detection: bDetection, ...bControls } = changed.controlInput;
      assert.deepEqual(baseline.envelope, changed.envelope);
      assert.deepEqual(aControls, bControls);
      assert.deepEqual(baseline.before, changed.before);
      assert.deepEqual(Object.keys(aControls).sort(), ["goal", "link_state", "pose", "visit_counts"]);
      assert.deepEqual(baseline.envelope, { scene_id: expected.scene_id, tick: expected.tick,
        sim_time_ms: expected.tick * contract.logical_clock.tick_ms,
        frame: { frame_id: expected.scene_id + ":" + expected.tick, width_px: camera.width_px,
          height_px: camera.height_px, pixel_format: camera.pixel_format, byte_length: camera.buffer_bytes } });
      const visitCounts = Array(contract.world.width_cells * contract.world.height_cells).fill(0);
      visitCounts[expected.pose.y * contract.world.width_cells + expected.pose.x] = contract.world.initial_visit_count_at_start;
      assert.deepEqual(aControls, { goal: expected.goal, pose: expected.pose, link_state: "connected", visit_counts: visitCounts });
      const difference = checkPixelDifference(a, b, region, camera);
      assert.notEqual(aDigest, bDigest);
      assert.equal(aDigest, baseline.record.frame_digest);
      assert.equal(bDigest, changed.record.frame_digest);
      assert.deepEqual(aDetection, baseline.record.detection);
      assert.deepEqual(bDetection, changed.record.detection);
      assert.equal(aDetection.status, "ok");
      assert.deepEqual(aDetection.detections, []);
      assert.equal(baseline.record.command.action, expected.baseline.command);
      assert.equal(bDetection.status, "ok");
      assert.deepEqual(bDetection.detections, [expectedDetection(camera, expected.changed.label, dx, dy)]);
      assert.equal(changed.record.command.action, expected.changed.command);
      assert(baseline.canvas_matches_delivered && changed.canvas_matches_delivered);
      assert(baseline.retained_frame_matches_delivered && changed.retained_frame_matches_delivered);
      const observed = { ...difference, screenshot: "pixel-B.png",
        baseline: { sha256: sha256(a), fnv1a: aDigest, file: "pixel-A.rgba", ...baseline },
        changed: { sha256: sha256(b), fnv1a: bDigest, file: "pixel-B.rgba", ...changed } };
      await saveJSON(artifacts("pixel-ab.json"), observed);
      return observed;
    }
  );

  async function observeStop(sceneId, label) {
    const before = await actions.ui();
    await delay(settleMs);
    const after = await actions.ui();
    const afterStep = await chrome.evaluate(() => globalThis.RC8DroneSimV2.testMonitor.step());
    const afterRetry = await actions.ui();
    const downloaded = await actions.exportLog(sceneId, label);
    assert.deepEqual(after, before, "终态等待后拍号及日志应保持");
    assert.equal(afterStep, null, "终态测试推进须拒绝追加记录");
    assert.deepEqual(afterRetry, before);
    assert.equal(before.start_disabled, true, "终态按钮应停止推进");
    return { before, after, after_step: afterStep, wait_ms: settleMs, downloaded };
  }

  await check("SIM-COLLISION", contract.collision_probe,
    "在 #test 选择固定障碍，使用合同的 commandOverride 驱动仿真器并验证实际终态、日志及再推进。",
    async () => {
      requireHook();
      const probe = contract.collision_probe;
      const record = await chrome.evaluate(({ scene_id, command }) => {
        const test = globalThis.RC8DroneSimV2.testMonitor;
        test.selectScene(scene_id);
        return test.step({ commandOverride: { action: command, reason: "toward_goal" } });
      }, probe);
      await chrome.screenshot(artifacts("collision.png"));
      assert.deepEqual(record.pose_before, probe.pose);
      assert.deepEqual(record.pose_after, probe.expected.pose_after);
      assert.equal(record.command.action, probe.command);
      assert.equal(record.run_state, probe.expected.run_state);
      assert.equal(record.collision, probe.expected.collision);
      assert.equal(record.arrived, false);
      const end = await observeStop(probe.scene_id, "collision-export");
      assert.equal(end.before.state, "collision");
      assert.match(end.before.state_label, /碰撞/);
      assert.deepEqual(end.downloaded.log.records, [record]);
      assert.deepEqual(end.downloaded.log.route, [probe.pose]);
      return { record, screenshot: "collision.png", ...end };
    }
  );

  await check("SIM-INVALID", { status: "invalid", detections: [], action: "HOLD", reason: "invalid_frame" },
    "从同一首帧派生坏宽度、坏长度和坏帧号，调用原检测与控制。通过 #test 推进坏长度帧查看界面。",
    async () => {
      requireHook();
      const samples = await chrome.evaluate(sceneId => {
        const api = globalThis.RC8DroneSimV2;
        const test = api.testMonitor;
        test.selectScene(sceneId);
        const initial = test.readState();
        test.step();
        const frame = test.readFrame();
        const inputs = [
          ["width", { ...frame.frame, width_px: frame.frame.width_px - 1 }],
          ["length", { ...frame.frame, pixels: frame.frame.pixels.slice(1) }],
          ["frame_id", { ...frame.frame, frame_id: "invalid:" + frame.tick }]
        ];
        const cases = inputs.map(([id, data]) => {
          const detection = api.detectFrame({ ...frame, frame: data });
          const command = api.chooseCommand({ detection, link_state: "connected",
            pose: initial.pose, goal: initial.goal, visit_counts: initial.visit_counts });
          const { pixels, ...input } = data;
          return { id, input: { ...input, byte_length: pixels.length }, detection, command };
        });
        test.selectScene(sceneId);
        const record = test.step({ replacePixels: pixels => pixels.slice(1) });
        return { cases, record };
      }, clear.id);
      for (const sample of samples.cases) {
        assert.equal(sample.detection.status, "invalid");
        assert.equal(sample.detection.frame_id, null);
        assert.deepEqual(sample.detection.detections, []);
        assert.equal(typeof sample.detection.error, "string");
        assert.equal(sample.command.action, "HOLD");
        assert.equal(sample.command.reason, "invalid_frame");
      }
      const ui = await actions.ui();
      assert.equal(samples.record.detection.status, "invalid");
      assert.equal(samples.record.frame_digest, null);
      assert.equal(samples.record.command.reason, "invalid_frame");
      assert.deepEqual(samples.record.pose_after, samples.record.pose_before);
      assert.match(ui.frame_status, /无效/);
      assert.equal(ui.detections_text, "");
      await chrome.screenshot(artifacts("invalid.png"));
      return { ...samples, ui, screenshot: "invalid.png" };
    }
  );

  await check("SIM-TIMEOUT", { records: contract.logical_clock.max_ticks,
    last_tick: contract.logical_clock.max_ticks - 1, delivered_frame: null, action: "HOLD", final: "timeout" },
    "用 #test 逐拍触发，在原 detectFrame 的调用边界将每拍 envelope.frame 置为 null。恢复入口后通过原控件重置并重跑。",
    async () => {
      requireHook();
      const count = contract.logical_clock.max_ticks;
      const { inputs, state } = await chrome.evaluate((id, maximum) => {
        const api = globalThis.RC8DroneSimV2;
        const test = api.testMonitor;
        const detect = api.detectFrame;
        const inputs = [];
        test.selectScene(id);
        api.detectFrame = incoming => {
          const delivered = { ...incoming, frame: null };
          inputs.push({ original_frame_id: incoming.frame?.frame_id ?? null,
            original_pixel_bytes: incoming.frame?.pixels.length ?? 0, delivered });
          return detect.call(api, delivered);
        };
        try {
          for (let i = 0; i < maximum; i++) test.step();
          return { inputs, state: test.readState() };
        } finally {
          api.detectFrame = detect;
        }
      }, clear.id, count);
      await chrome.screenshot(artifacts("timeout.png"));
      await saveJSON(artifacts("timeout-inputs.json"), { inputs, state });
      assert.equal(inputs.length, count);
      assert.equal(state.records.length, count);
      assert.equal(state.next_tick, count);
      assert.equal(state.run_state, "timeout");
      assert.deepEqual(state.route, [clear.start]);
      for (const [i, record] of state.records.entries()) {
        assert.deepEqual(inputs[i].delivered, { scene_id: clear.id, tick: i,
          sim_time_ms: i * contract.logical_clock.tick_ms, frame: null });
        assert.equal(record.tick, i);
        assert.equal(record.sim_time_ms, inputs[i].delivered.sim_time_ms);
        assert.equal(record.detection.status, "missing");
        assert.equal(record.detection.frame_id, null);
        assert.equal(record.frame_digest, null);
        assert.equal(record.consecutive_unusable, i + 1);
        assert.equal(record.command.action, "HOLD");
        assert.equal(record.command.reason, i > 0 ? "link_disconnected" : "frame_missing");
        assert.deepEqual(record.pose_after, clear.start);
        assert.equal(record.arrived, false);
        assert.equal(record.collision, false);
        assert.equal(record.run_state, i === count - 1 ? "timeout" : "running");
      }
      const stopped = await observeStop(clear.id, "timeout-export");
      assert.equal(stopped.before.state, "timeout");
      assert.equal(stopped.before.log_rows, count);
      assert.deepEqual(stopped.downloaded.log.records, state.records);
      await actions.click("reset-button");
      const reset = await actions.ui();
      actions.assertReset(reset, clear);
      const recovered = await actions.startAndExport(clear.id, "timeout-reset-replay");
      validateRun(recovered.log, clear, contract);
      return { input_path: "timeout-inputs.json", inputs, stopped, reset, replay: recovered,
        screenshot: "timeout.png" };
    }
  );

  await check("SIM-EXPORT", { rounds_per_scene: 2, stable: ["schema", "ticks", "digests", "actions", "route", "terminal"] },
    "正常 file: 页面中，各场景重置后运行两次，点击导出并比较实际下载。",
    async () => {
      return contract.scenes.map(scene => {
        const [first, second] = browserExports[scene.id];
        if (first.error || second.error) throw new Error(scene.id + " " + (first.error ?? second.error));
        validateRun(first.log, scene, contract);
        validateRun(second.log, scene, contract);
        assert.deepEqual(second.log, first.log, scene.id + " 两轮导出不一致");
        return { scene_id: scene.id, record_count: first.log.records.length, both_exports: [first.path, second.path],
          sha256: [first.sha256, second.sha256], byte_identical: first.sha256 === second.sha256 };
      });
    }
  );
  return { checks, data };
}

async function main(manifest) {
  const handoffBytes = await readFile(path.resolve(manifest));
  const handoff = decodeJSON(handoffBytes);
  const delivery = await readDelivery(handoff);
  const output = path.join(testing, "local");
  await mkdir(output, { recursive: true });
  const run = await mkdtemp(path.join(output, "run-"));
  console.log("独立证据目录 " + run);
  const packageDirectory = path.join(run, "package");
  const copy = await makeCopy(packageDirectory, delivery);
  await writeFile(path.join(run, "input-handoff.json"), handoffBytes, { flag: "wx" });
  const evidence = {
    contract_id: delivery.contract.contract_id, schema_version: delivery.contract.schema_version,
    started_at: new Date().toISOString(),
    environment: { node: process.version, platform: process.platform, arch: process.arch },
    source_app: delivery.source, isolated_app: copy,
    package_sha256: {
      "INTERFACE_CONTRACT.json": handoff.contract_sha256,
      ...Object.fromEntries(Object.entries(handoff.app_sha256).map(([name, hash]) => ["app/" + name, hash])),
      ...handoff.supporting_sha256, "software-evidence.json": handoff.software_evidence.sha256
    },
    algorithm_evidence: handoff.algorithm_evidence, checks: []
  };
  let chrome;
  try {
    chrome = await openChrome(run);
    evidence.environment.chrome = chrome.version;
    const { checks, data } = await runChecks(chrome, run, copy, delivery.contract);
    evidence.checks = checks;
    evidence.raw_browser_activity = data.normal_browser_activity;
  } catch (error) {
    evidence.run_error = error.stack;
    console.error(error.stack);
  } finally {
    if (chrome) {
      await saveJSON(path.join(run, "browser-activity-complete.json"), chrome.activity);
      try { await chrome.close(); } catch (error) { evidence.chrome_cleanup_error = error.message; }
    }
  }
  for (const id of requiredIds) {
    if (!evidence.checks.some(row => row.id === id)) {
      evidence.checks.push({ id, status: "PENDING", observed: { message: evidence.run_error ?? "本次未执行" } });
    }
  }
  evidence.completed_at = new Date().toISOString();
  await saveJSON(path.join(run, "run-evidence.json"), evidence);
  if (evidence.checks.some(row => row.status !== "PASS")) process.exitCode = 1;
}

const manifest = process.argv[2];
if (!manifest || manifest === "--help") {
  console.log("用法 node verify-independent.mjs <由最终交付记录生成的 handoff.json>");
  if (!manifest) process.exitCode = 2;
} else {
  main(manifest).catch(error => {
    console.error(error.stack);
    process.exitCode = 1;
  });
}
