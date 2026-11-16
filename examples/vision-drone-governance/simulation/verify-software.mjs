import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { cp, mkdir, mkdtemp, readFile, readdir, realpath, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { isDeepStrictEqual as same } from "node:util";

const pinned = {
  "INTERFACE_CONTRACT.json": "77fa7df9dc17bbc95e3a728dd45e68c420dfbabdf770c3ac5ff9c714be025130",
  "app/detector.js": "3581c1f94f780315bc29f3af19462e994aa8571c32ec6550ab16ddec9e3770a7",
  "app/controller.js": "414b781b680a9ec2025f794eaa5eae9f2944f0b149a2bb130f8a40bae9a6d967"
};

const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const expression = (fn, ...args) => "(" + fn.toString() + ")(" + args.map(value => JSON.stringify(value)).join(",") + ")";

async function waitFor(check, label, timeout = 9000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const value = await check();
    if (value) return value;
    await delay(35);
  }
  throw new Error("Timed out waiting for " + label);
}

async function openChrome(profile) {
  const executable = process.env.RC8_CHROME_PATH || process.env.RC8_TEST_CHROME || (process.platform === "win32"
    ? path.join(process.env.ProgramFiles || process.env["ProgramFiles(x86)"] || "", "Google", "Chrome", "Application", "chrome.exe")
    : process.platform === "darwin" ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" : "google-chrome");
  const child = spawn(executable, [
    "--headless=new", "--window-size=1320,1000", "--no-first-run", "--no-default-browser-check",
    "--disable-background-networking", "--disable-component-update", "--disable-extensions",
    "--disable-sync", "--no-proxy-server", "--host-resolver-rules=MAP * ~NOTFOUND",
    "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0",
    "--user-data-dir=" + profile, "about:blank"
  ], { stdio: ["ignore", "ignore", "pipe"], windowsHide: true });
  const exited = new Promise(resolve => child.once("exit", resolve));
  const requests = [];
  const exceptions = [];
  const scripts = new Map();
  const pending = new Map();
  let launchError;
  let socket;
  let requestId = 0;
  child.on("error", error => { launchError = error; });
  child.stderr.resume();

  function call(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++requestId;
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error("DevTools did not answer " + method));
      }, 7000);
      pending.set(id, response => {
        clearTimeout(timer);
        if (response.error) reject(new Error(method + ": " + response.error.message));
        else resolve(response.result);
      });
      socket.send(JSON.stringify({ id, method, params }));
    });
  }

  async function close() {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ id: ++requestId, method: "Browser.close" }));
    }
    await Promise.race([exited, delay(1700)]);
    if (child.exitCode === null && child.signalCode === null) {
      child.kill();
      await Promise.race([exited, delay(1700)]);
    }
    if (socket?.readyState === WebSocket.OPEN) socket.close();
  }

  async function evaluate(code) {
    const reply = await call("Runtime.evaluate", { expression: code, returnByValue: true, awaitPromise: true });
    if (reply.exceptionDetails) {
      throw new Error(reply.exceptionDetails.exception?.description ?? reply.exceptionDetails.text);
    }
    return reply.result.value;
  }

  async function click(id) {
    const point = await evaluate(expression(target => {
      const element = document.getElementById(target);
      if (element.disabled) throw new Error(target + " is disabled");
      element.scrollIntoView({ block: "center" });
      const rect = element.getBoundingClientRect();
      return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    }, id));
    for (const type of ["mousePressed", "mouseReleased"]) {
      await call("Input.dispatchMouseEvent", { type, ...point, button: "left", clickCount: 1 });
    }
  }

  async function navigate(url, testMode = false) {
    const result = await call("Page.navigate", { url });
    if (result.errorText) throw new Error(result.errorText);
    await waitFor(() => evaluate(expression(mode =>
      document.readyState === "complete" && location.protocol === "file:"
      && !!document.getElementById("scene-select")?.options.length
      && (!mode || !!globalThis.RC8DroneSimV2?.testMonitor), testMode)), "the packaged monitor");
  }

  try {
    const port = await waitFor(async () => {
      if (launchError) throw launchError;
      try { return (await readFile(path.join(profile, "DevToolsActivePort"), "utf8")).split(/\r?\n/)[0]; }
      catch (error) { if (error.code !== "ENOENT") throw error; return null; }
    }, "Chrome DevTools startup");
    const targets = await (await fetch("http://127.0.0.1:" + port + "/json/list")).json();
    socket = new WebSocket(targets.find(target => target.type === "page").webSocketDebuggerUrl);
    socket.addEventListener("message", event => {
      const message = JSON.parse(event.data);
      if (message.id && pending.has(message.id)) {
        const receive = pending.get(message.id);
        pending.delete(message.id);
        receive(message);
      }
      if (message.method === "Runtime.exceptionThrown") {
        const detail = message.params.exceptionDetails;
        exceptions.push(detail.exception?.description ?? detail.text);
      }
      if (message.method === "Network.requestWillBeSent") requests.push(message.params.request.url);
      if (message.method === "Debugger.scriptParsed") scripts.set(message.params.url, message.params.scriptId);
    });
    await waitFor(() => socket.readyState === WebSocket.OPEN, "the DevTools socket");
    for (const domain of ["Page", "Runtime", "Network", "Debugger"]) await call(domain + ".enable");
    return { call, evaluate, click, navigate, close, requests, exceptions, scripts };
  } catch (error) {
    await close();
    throw error;
  }
}

function readUi() {
  const get = id => document.getElementById(id);
  const text = id => get(id).textContent;
  const camera = get("camera-pixels");
  const pixels = camera.getContext("2d").getImageData(0, 0, camera.width, camera.height).data;
  const overlayPixels = get("camera-overlay").getContext("2d").getImageData(0, 0, camera.width, camera.height).data;
  let hash = 2166136261;
  for (const byte of pixels) hash = Math.imul(hash ^ byte, 16777619);
  let overlayCount = 0;
  for (let index = 3; index < overlayPixels.length; index += 4) {
    if (overlayPixels[index]) overlayCount += 1;
  }
  return {
    scene_id: get("scene-select").value,
    run_state: get("run-state").dataset.state,
    run_text: text("run-state"),
    link_state: get("link-state").dataset.state,
    tick_text: text("logical-tick"),
    logical_time: text("logical-time"),
    pose_text: text("pose-value"),
    route_text: text("route-text"),
    rows: get("log-rows").rows.length,
    frame_id: text("frame-id"),
    frame_status: text("frame-status"),
    frame_digest: text("frame-digest"),
    detections: text("detections"),
    camera_bytes: pixels.length,
    camera_digest: (hash >>> 0).toString(16).padStart(8, "0"),
    overlay_pixels: overlayCount,
    start_button: text("start-button"),
    error: get("app-error").hidden ? null : text("app-error")
  };
}

async function runScene(browser, scene, round, contractId, downloads) {
  const { evaluate, click, call } = browser;
  const snapshot = () => evaluate(expression(readUi));
  await evaluate(expression(sceneId => {
    const selector = document.getElementById("scene-select");
    selector.value = sceneId;
    selector.dispatchEvent(new Event("change", { bubbles: true }));
  }, scene.id));
  await click("reset-button");
  const reset = await snapshot();
  await click("start-button");
  const first = await snapshot();
  let pause = null;
  if (scene.id === "clear-room" && round === 1) {
    await click("pause-button");
    const entered = await snapshot();
    const before = Date.now();
    await delay(450);
    pause = { entered, held: await snapshot(), hold_wall_ms: Date.now() - before };
    await click("start-button");
  }

  await waitFor(() => evaluate('["arrived","collision","timeout"].includes(document.getElementById("run-state").dataset.state)'), scene.id + " terminal state");
  const terminal = await snapshot();
  const directory = path.join(downloads, scene.id + "-" + round);
  await mkdir(directory);
  await call("Browser.setDownloadBehavior", { behavior: "allow", downloadPath: directory });
  await click("export-button");
  const name = contractId + "-" + scene.id + ".json";
  const bytes = await waitFor(async () => {
    try { return await readFile(path.join(directory, name)); }
    catch (error) { if (error.code !== "ENOENT") throw error; return null; }
  }, name + " download");

  return { reset, first, pause, terminal, name, bytes, digest: sha256(bytes), export: JSON.parse(bytes) };
}

function readDropSteps() {
  const test = RC8DroneSimV2.testMonitor;
  test.selectScene("drop-and-recover");
  const snapshots = [];
  for (let index = 0; index < 4; index += 1) {
    const record = test.step();
    snapshots.push({
      record,
      frame_delivered: test.readFrame().frame !== null,
      visit_counts: test.readState().visit_counts,
      frame_status: document.getElementById("frame-status").textContent,
      detections_text: document.getElementById("detections").textContent
    });
  }
  return snapshots;
}


function readPixelComparison(camera, sceneId) {
  const api = RC8DroneSimV2;
  const test = api.testMonitor;
  const detect = api.detectFrame;
  const choose = api.chooseCommand;
  const inset = camera.obstacle_inset_px;
  const patch = {
    x_min: 2 * camera.cell_width_px + inset,
    y_min: camera.cell_height_px + inset,
    x_max: 3 * camera.cell_width_px - inset,
    y_max: 2 * camera.cell_height_px - inset
  };

  function run(change) {
    test.selectScene(sceneId);
    let envelope, control;
    api.detectFrame = input => { envelope = structuredClone(input); return detect(input); };
    api.chooseCommand = input => { control = structuredClone(input); return choose(input); };
    let record;
    try {
      record = test.step(change ? { replacePixels(bytes) {
        for (let y = patch.y_min; y < patch.y_max; y += 1) {
          for (let x = patch.x_min; x < patch.x_max; x += 1) {
            bytes.set(camera.palette_rgba.box, (y * camera.width_px + x) * 4);
          }
        }
        return bytes;
      } } : undefined);
    } finally {
      api.detectFrame = detect;
      api.chooseCommand = choose;
    }
    const { pixels, ...frame } = envelope.frame;
    const { detection, ...navigation } = control;
    let hash = 2166136261;
    for (const byte of pixels) hash = Math.imul(hash ^ byte, 16777619);
    return {
      pixels,
      observed: {
        record,
        frame_metadata: { scene_id: envelope.scene_id, tick: envelope.tick, sim_time_ms: envelope.sim_time_ms, ...frame },
        control_metadata: navigation,
        detector_keys: Object.keys(envelope).sort(),
        frame_keys: Object.keys(envelope.frame).sort(),
        controller_keys: Object.keys(control).sort(),
        raw_bytes: pixels.length,
        raw_digest: (hash >>> 0).toString(16).padStart(8, "0")
      }
    };
  }

  const baseline = run(false);
  const changed = run(true);
  let changedBytes = 0;
  let changedPixels = 0;
  let alphaChanges = 0;
  const bounds = { x_min: camera.width_px, y_min: camera.height_px, x_max: 0, y_max: 0 };
  for (let offset = 0; offset < baseline.pixels.length; offset += 4) {
    let different = false;
    for (let channel = 0; channel < 4; channel += 1) {
      if (baseline.pixels[offset + channel] !== changed.pixels[offset + channel]) {
        changedBytes += 1;
        if (channel === 3) alphaChanges += 1;
        different = true;
      }
    }
    if (!different) continue;
    changedPixels += 1;
    const x = offset / 4 % camera.width_px;
    const y = Math.floor(offset / 4 / camera.width_px);
    bounds.x_min = Math.min(bounds.x_min, x);
    bounds.y_min = Math.min(bounds.y_min, y);
    bounds.x_max = Math.max(bounds.x_max, x + 1);
    bounds.y_max = Math.max(bounds.y_max, y + 1);
  }

  return {
    baseline: baseline.observed, changed: changed.observed,
    changed_bytes: changedBytes, changed_pixels: changedPixels, changed_alpha_bytes: alphaChanges,
    changed_bounds_px: bounds
  };
}

function readCollisionProbe(sceneId, action) {
  const test = RC8DroneSimV2.testMonitor;
  test.selectScene(sceneId);
  const before = test.readState();
  const record = test.step({ commandOverride: { action, reason: "toward_goal" } });
  const next = test.step();
  const after = test.readState();
  return {
    record, next, route: after.route, log_rows: after.records.length,
    visit_counts_preserved: before.visit_counts.every((count, index) => count === after.visit_counts[index]),
    ui_state: document.getElementById("run-state").dataset.state,
    ui_text: document.getElementById("run-state").textContent,
    ui_rows: document.getElementById("log-rows").rows.length
  };
}

function readInvalidProbe() {
  const test = RC8DroneSimV2.testMonitor;
  test.selectScene("clear-room");
  const record = test.step({ replacePixels: bytes => bytes.slice(0, 4) });
  const input = test.readFrame();
  return {
    record,
    input: { frame_id: input.frame.frame_id, width_px: input.frame.width_px,
      height_px: input.frame.height_px, pixel_format: input.frame.pixel_format,
      bytes: Array.from(input.frame.pixels) },
    ui_status: document.getElementById("frame-status").textContent,
    ui_candidates: document.getElementById("detections").textContent
  };
}

function readTimeoutProbe(maxTicks) {
  const test = RC8DroneSimV2.testMonitor;
  test.selectScene("clear-room");
  for (let index = 0; index < maxTicks; index += 1) {
    test.step({ commandOverride: { action: "HOLD", reason: "no_safe_neighbor" } });
  }
  const state = test.readState();
  return {
    log_rows: state.records.length,
    last_tick: state.records.at(-1).tick,
    run_state: state.run_state,
    final_pose: state.pose,
    next: test.step(),
    ui_text: document.getElementById("run-state").textContent
  };
}

function sceneSummary(run) {
  const result = run.export;
  return {
    first_detection_count: result.records[0].detection.detections.length,
    actions: result.records.map(record => record.command.action),
    route: result.route,
    terminal_tick: result.records.at(-1).tick,
    terminal_state: result.run_state,
    collisions: result.records.filter(record => record.collision).length
  };
}

function alignedExport(run, scene, contract) {
  const value = run.export;
  const exportKeys = Object.keys(contract.types.Export).sort();
  const recordKeys = Object.keys(contract.types.TickRecord).sort();
  return same(Object.keys(value).sort(), exportKeys)
    && value.contract_id === contract.contract_id && value.schema_version === contract.schema_version
    && value.scene_id === scene.id && value.clock_ms === contract.logical_clock.tick_ms
    && same(value.start, scene.start) && same(value.goal, scene.goal)
    && value.records.length === run.terminal.rows
    && value.records.every((record, index) =>
      same(Object.keys(record).sort(), recordKeys)
      && record.tick === index
      && record.sim_time_ms === index * value.clock_ms
      && record.detection.tick === index && record.detection.sim_time_ms === record.sim_time_ms
      && record.detection.scene_id === scene.id
      && record.detection.frame_id === (record.detection.status === "ok" ? scene.id + ":" + index : null)
      && record.command.tick === index && record.command.source_frame_id === record.detection.frame_id
      && (record.detection.status === "ok" ? /^[a-f0-9]{8}$/.test(record.frame_digest) : record.frame_digest === null)
    )
    && !run.bytes.toString("utf8").includes('"pixels":');
}

async function verify(root, scratch) {
  const entry = path.join(scratch, "independent copy");
  const downloads = path.join(scratch, "downloads");
  await mkdir(entry);
  await mkdir(downloads);
  await cp(path.join(root, "app"), path.join(entry, "app"), { recursive: true });
  await cp(path.join(root, "INTERFACE_CONTRACT.json"), path.join(entry, "INTERFACE_CONTRACT.json"));
  const contract = JSON.parse(await readFile(path.join(entry, "INTERFACE_CONTRACT.json")));
  const names = (await readdir(path.join(entry, "app"))).sort();
  const hashes = {};
  for (const file of ["INTERFACE_CONTRACT.json", ...names.map(name => "app/" + name)]) {
    hashes[file] = sha256(await readFile(path.join(entry, file)));
  }

  const browser = await openChrome(path.join(scratch, "chrome"));
  try {
    const { call, evaluate } = browser;
    const version = await call("Browser.getVersion");
    const url = pathToFileURL(path.join(entry, "app", "index.html")).href;
    await browser.navigate(url);
    const normalTestHook = await evaluate('!!globalThis.RC8DroneSimV2.testMonitor');
    const browserScripts = {};
    for (const file of ["app/detector.js", "app/controller.js"]) {
      const scriptId = browser.scripts.get(pathToFileURL(path.join(entry, file)).href);
      browserScripts[file] = scriptId
        ? sha256((await call("Debugger.getScriptSource", { scriptId })).scriptSource)
        : null;
    }

    const runs = new Map();
    for (const scene of contract.scenes) {
      const first = await runScene(browser, scene, 1, contract.contract_id, downloads);
      const second = await runScene(browser, scene, 2, contract.contract_id, downloads);
      runs.set(scene.id, { first, second });
    }

    await browser.navigate(url + "?probe=1#test", true);
    const drop = await evaluate(expression(readDropSteps));
    const pixels = await evaluate(expression(readPixelComparison, contract.camera, contract.pixel_counterfactual.scene_id));
    const collision = await evaluate(expression(readCollisionProbe, contract.collision_probe.scene_id, contract.collision_probe.command));
    const invalid = await evaluate(expression(readInvalidProbe));
    const timeout = await evaluate(expression(readTimeoutProbe, contract.logical_clock.max_ticks));

    const checks = [];
    const add = (id, expected, observed, reproduce, passed) => {
      checks.push({ id, status: passed ? "PASS" : "FAIL", expected, observed, reproduce });
    };
    const chooseRun = "以 Chrome 从独立目录打开 app/index.html。";
    const runSceneText = name => chooseRun + "选择 " + name + "，重置，开始，等待终态并点击「导出 JSON」。";
    const testPage = "在独立测试副本中以 file: 打开 app/index.html#test，在 DevTools 使用 RC8DroneSimV2.testMonitor。";
    const algorithmFiles = Object.fromEntries(Object.keys(browserScripts).map(file => [file, {
      source_sha256_at_integration: pinned[file], packaged_sha256: hashes[file], browser_script_sha256: browserScripts[file]
    }]));
    add("SIM-PACKAGE", pinned, { file_sha256: hashes, algorithm_files: algorithmFiles },
      "原字节计算 SHA-256。通过 Chrome Debugger.getScriptSource 读取实际执行的两个经典脚本，核对源文件、包内副本和浏览器源文本。",
      Object.entries(pinned).every(([file, digest]) => hashes[file] === digest)
      && Object.values(algorithmFiles).every(file => file.browser_script_sha256 === file.packaged_sha256));

    const externalRequests = browser.requests.filter(request => /^(https?|wss?):/i.test(request));
    const localResources = [...new Set(browser.requests.filter(request => request.startsWith("file:"))
      .map(resource => path.relative(entry, fileURLToPath(resource)).split(path.sep).join("/")))].sort();
    const resets = contract.scenes.flatMap(scene => Object.values(runs.get(scene.id)).map(run => ({
      expected_scene: scene.id, ...run.reset
    })));
    const held = runs.get("clear-room").first.pause;
    const resetMatches = resets.every(reset =>
      reset.scene_id === reset.expected_scene && reset.run_state === "ready" && reset.link_state === "waiting"
      && reset.rows === 0 && reset.tick_text === "—" && reset.overlay_pixels === 0
      && reset.pose_text === "当前位置 (4, 6)" && reset.route_text === "(4, 6)" && reset.error === null
    );
    add("SIM-OFFLINE", {
      independent_copy: true, page_protocol: "file:", external_requests: [], exceptions: [],
      pause_wall_ms_at_least: 200, pause_state_stable: true, reset_state: "ready/waiting",
      normal_test_hook: false
    }, { independent_copy: true, page_protocol: await evaluate("location.protocol"),
      local_resources: localResources, external_requests: externalRequests, exceptions: browser.exceptions,
      pause: held, reset_matches: resetMatches, resets, normal_test_hook: normalTestHook },
    chooseRun + "在空房间启动后暂停，等待至少 450 ms，核对拍号与记录数，继续。重置并选择其余场景。",
    resetMatches && !normalTestHook && !externalRequests.length && !browser.exceptions.length
    && held.hold_wall_ms >= 200 && held.entered.run_state === "paused" && held.entered.start_button === "继续"
    && same(held.entered, held.held));

    for (const scene of contract.scenes) {
      const first = runs.get(scene.id).first;
      const summary = sceneSummary(first);
      const { first_blocked_cell, link_events, ...expected } = scene.expected;
      const firstRecord = first.export.records[0];
      const overlayMatches = expected.first_detection_count ? first.first.overlay_pixels > 0 : first.first.overlay_pixels === 0;
      const firstMatches = firstRecord.detection.status === "ok" && first.first.tick_text === "拍 0"
        && first.first.camera_bytes === contract.camera.buffer_bytes && first.first.camera_digest === firstRecord.frame_digest
        && first.first.frame_digest === firstRecord.frame_digest && overlayMatches;
      const common = {
        ...summary, first_record: firstRecord, first_ui: first.first, terminal_ui: first.terminal
      };
      const commonPass = same(summary, expected) && firstMatches && first.terminal.run_state === expected.terminal_state;
      if (scene.id === "clear-room") {
        add("SIM-CLEAR", { ...expected, first_detection_status: "ok", first_camera_bytes: 76800 },
          common, runSceneText(scene.id), commonPass && first.first.frame_status === "有效空帧");
      }
      if (scene.id === "fixed-obstacle") {
        const detected = firstRecord.detection.detections;
        add("SIM-DETOUR", { ...expected, first_blocked_cell, first_labels_in_order: ["wall", "column", "box"] },
          common, runSceneText(scene.id),
          commonPass && same(detected.map(item => item.label), ["wall", "column", "box"])
          && detected.some(item => item.label === "box" && same(item.cell, first_blocked_cell)));
      }
      if (scene.id === "drop-and-recover") {
        const events = Object.fromEntries(first.export.records.filter(record => record.link_event)
          .map(record => [record.link_event, record.tick]));
        const missing = drop.slice(1, 3);
        const goodMissing = missing.every((step, index) =>
          !step.frame_delivered && step.record.detection.status === "missing" && step.record.frame_digest === null
          && step.record.detection.detections.length === 0 && step.record.command.action === "HOLD"
          && step.record.command.reason === (index === 0 ? "frame_missing" : "link_disconnected")
          && same(step.record.pose_before, step.record.pose_after) && same(step.visit_counts, drop[0].visit_counts)
          && step.frame_status === "本拍缺帧" && step.detections_text === ""
        );
        add("SIM-DROP", { ...expected, link_events, missing_ticks: scene.missing_ticks,
          consecutive_unusable: [0, 1, 2, 0], missing_actions: ["HOLD", "HOLD"], recovered_frame: scene.id + ":3" },
          { ...common, link_events: events, missing_and_recovery_steps: drop },
          runSceneText(scene.id) + "按测试入口观察拍 0 至拍 3 的访问计数和画面。",
          commonPass && same(events, link_events) && goodMissing
          && same(drop.map(step => step.record.consecutive_unusable), [0, 1, 2, 0])
          && drop[1].record.link_state === "connected" && drop[2].record.link_state === "disconnected"
          && drop[3].frame_delivered && drop[3].record.detection.frame_id === scene.id + ":3"
          && drop[3].record.detection.status === "ok" && drop[3].record.link_event === "reconnected");
      }
    }

    const ab = contract.pixel_counterfactual;
    const width = contract.camera.width_px;
    const height = contract.camera.height_px;
    const expectedBox = { x_min: 66 / width, y_min: 26 / height, x_max: 94 / width, y_max: 46 / height };
    const patchBounds = { x_min: 66, y_min: 26, x_max: 94, y_max: 46 };
    const a = pixels.baseline;
    const b = pixels.changed;
    const metadataEqual = same(a.frame_metadata, b.frame_metadata) && same(a.control_metadata, b.control_metadata);
    const inputsConform = [a, b].every(sample =>
      sample.raw_bytes === contract.camera.buffer_bytes && sample.record.frame_digest === sample.raw_digest
      && same(sample.detector_keys, ["frame", "scene_id", "sim_time_ms", "tick"])
      && same(sample.frame_keys, ["frame_id", "height_px", "pixel_format", "pixels", "width_px"])
      && same(sample.controller_keys, ["detection", "goal", "link_state", "pose", "visit_counts"])
    );
    add("SIM-PIXELS", { scene_id: ab.scene_id, tick: ab.tick, pose: ab.pose, goal: ab.goal,
      metadata_equal: true, baseline: ab.baseline, changed: ab.changed,
      changed_pixels: 560, changed_bytes: 1680, changed_alpha_bytes: 0, changed_bounds_px: patchBounds,
      normalized_box: expectedBox },
      { ...pixels, metadata_equal: metadataEqual, input_keys_conform: inputsConform },
      testPage + "将同一空房间首帧的相机格 (2,1) 内缩矩形改为箱体色。比较进入交付检测器的原始字节、非像素参数和实际命令。",
      metadataEqual && inputsConform && a.raw_digest !== b.raw_digest && a.frame_metadata.tick === ab.tick
      && a.frame_metadata.frame_id === ab.scene_id + ":" + ab.tick && a.frame_metadata.sim_time_ms === 0
      && same(a.control_metadata.pose, ab.pose) && same(a.control_metadata.goal, ab.goal)
      && a.record.detection.status === "ok" && a.record.detection.detections.length === ab.baseline.detections
      && a.record.command.action === ab.baseline.command && b.record.detection.status === "ok"
      && b.record.command.action === ab.changed.command
      && same(b.record.detection.detections, [{ label: ab.changed.label, region: expectedBox, cell: ab.changed.cell, pixel_count: 560 }])
      && pixels.changed_bytes === 1680 && pixels.changed_pixels === 560 && pixels.changed_alpha_bytes === 0
      && same(pixels.changed_bounds_px, patchBounds));

    const probe = contract.collision_probe;
    add("SIM-COLLISION", { ...probe.expected, log_rows: 1, stop_after_collision: true, visit_counts_preserved: true,
      ui_text: "模拟碰撞" }, collision,
      testPage + '选择 fixed-obstacle，执行 step({commandOverride:{action:"MOVE_N",reason:"toward_goal"}})，再次调用 step。',
      same(collision.record.pose_before, probe.pose) && same(collision.record.pose_after, probe.expected.pose_after)
      && collision.record.command.action === probe.command && collision.record.run_state === "collision"
      && collision.record.collision && !collision.record.arrived && collision.next === null
      && collision.log_rows === 1 && collision.ui_rows === 1 && same(collision.route, [probe.pose])
      && collision.visit_counts_preserved && collision.ui_state === "collision" && collision.ui_text === "模拟碰撞");

    add("SIM-INVALID", { buffer_bytes: 4, frame_digest: null, status: "invalid", detections: [],
      action: "HOLD", reason: "invalid_frame", ui_status: "输入帧无效" }, invalid,
      testPage + "选择 clear-room，step({replacePixels: bytes => bytes.slice(0,4)})。",
      invalid.input.bytes.length === 4 && invalid.record.frame_digest === null
      && invalid.record.detection.status === "invalid" && invalid.record.detection.detections.length === 0
      && invalid.record.detection.frame_id === null && invalid.record.command.action === "HOLD"
      && invalid.record.command.reason === "invalid_frame" && same(invalid.record.pose_before, invalid.record.pose_after)
      && invalid.ui_status === "输入帧无效" && invalid.ui_candidates === "");

    add("SIM-TIMEOUT", { log_rows: 12, last_tick: 11, run_state: "timeout", final_pose: { x: 4, y: 6 },
      next: null, ui_text: "达到拍数上限" }, timeout,
      testPage + "从 clear-room 强制 HOLD 十二拍，再尝试推进一次。",
      timeout.log_rows === 12 && timeout.last_tick === 11 && timeout.run_state === "timeout"
      && same(timeout.final_pose, { x: 4, y: 6 }) && timeout.next === null && timeout.ui_text === "达到拍数上限");

    const exports = {};
    for (const scene of contract.scenes) {
      const { first, second } = runs.get(scene.id);
      exports[scene.id] = {
        name: first.name, bytes: first.bytes.length, sha256: [first.digest, second.digest],
        byte_identical: first.bytes.equals(second.bytes),
        contract_fields_aligned: alignedExport(first, scene, contract) && alignedExport(second, scene, contract),
        actual_export: first.export
      };
    }
    add("SIM-EXPORT", { scenes: contract.scenes.map(scene => scene.id), downloads_per_scene: 2,
      byte_identical_per_scene: true, contract_fields_aligned: true }, exports,
      chooseRun + "三个场景各从重置独立跑两轮，从界面下载六份 JSON。逐字节比较同场景两次下载并核对导出字段。",
      Object.values(exports).every(result => result.byte_identical && result.contract_fields_aligned));

    return {
      role: "software", contract_id: contract.contract_id, schema_version: contract.schema_version,
      contract_sha256: hashes["INTERFACE_CONTRACT.json"], file_sha256: hashes, algorithm_files: algorithmFiles,
      browser: { product: version.product, user_agent: version.userAgent, mode: "headless", transport: "Chrome DevTools Protocol" },
      scope: "软件研发自测", checks
    };
  } finally {
    await browser.close();
  }
}

const root = await realpath(fileURLToPath(new URL(".", import.meta.url)));
const output = path.join(root, "local");
await mkdir(output, { recursive: true });
const scratch = await realpath(await mkdtemp(path.join(output, ".rc8-browser-")));
if (path.dirname(scratch) !== await realpath(output) || !path.basename(scratch).startsWith(".rc8-browser-")) {
  throw new Error("Browser test directory is outside the package");
}
try {
  const evidence = await verify(root, scratch);
  await writeFile(path.join(output, "software-evidence.json"), JSON.stringify(evidence, null, 2) + "\n", "utf8");
  for (const check of evidence.checks) console.log(check.id, check.status);
  process.exitCode = evidence.checks.some(check => check.status !== "PASS") ? 1 : 0;
} finally {
  await rm(scratch, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 });
}
