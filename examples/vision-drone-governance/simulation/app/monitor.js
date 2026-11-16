(() => {
  "use strict";

  const api = globalThis.RC8DroneSimV2;
  const byId = id => document.getElementById(id);
  const sceneSelect = byId("scene-select");
  const start = byId("start-button");
  const pause = byId("pause-button");
  const reset = byId("reset-button");
  const exportButton = byId("export-button");
  const run = byId("run-state");
  const link = byId("link-state");
  const error = byId("app-error");
  const sensor = byId("camera-pixels");
  const pixels = sensor.getContext("2d", { alpha: false, willReadFrequently: true });
  const overlay = byId("camera-overlay").getContext("2d");
  const map = byId("route-map");
  const routeContext = map.getContext("2d");
  const logRows = byId("log-rows");
  const runLabels = {
    ready: "就绪", running: "运行中", paused: "已暂停", arrived: "已到达", collision: "模拟碰撞", timeout: "达到拍数上限"
  };
  const linkLabels = { waiting: "等待帧", connected: "链路已连接", disconnected: "模拟断流" };
  const objectLabels = { wall: "墙面", column: "立柱", box: "箱体" };
  const algorithmsReady = typeof api.detectFrame === "function" && typeof api.chooseCommand === "function";
  const playbackDelayMs = 300;
  let simulation;
  let timer = null;

  for (const { id, title } of api.listScenes()) sceneSelect.add(new Option(title, id));

  const positionText = ({ x, y }) => "(" + x + ", " + y + ")";

  function showError(message) {
    error.textContent = message;
    error.hidden = message === "";
  }

  function showCamera(record) {
    overlay.clearRect(0, 0, sensor.width, sensor.height);
    const detection = record?.detection;
    const data = detection?.status === "ok" ? simulation.readFrame().frame : null;
    if (data) {
      pixels.putImageData(new ImageData(data.pixels, data.width_px, data.height_px), 0, 0);
      overlay.strokeStyle = "#91ffe0";
      overlay.lineWidth = 1;
      for (const item of detection.detections) {
        const box = item.region;
        overlay.strokeRect(
          box.x_min * sensor.width, box.y_min * sensor.height,
          (box.x_max - box.x_min) * sensor.width, (box.y_max - box.y_min) * sensor.height
        );
      }
    } else {
      pixels.fillStyle = "#182028";
      pixels.fillRect(0, 0, sensor.width, sensor.height);
    }

    const detections = detection?.detections ?? [];
    const frameLabels = { missing: "本拍缺帧", invalid: "输入帧无效", ok: detections.length ? "有效帧" : "有效空帧" };
    byId("frame-status").textContent = detection ? frameLabels[detection.status] : "等待首帧";
    byId("frame-id").textContent = detection?.frame_id ?? "—";
    byId("frame-digest").textContent = record?.frame_digest ?? "—";
    byId("detections").textContent = detections.map(({ label, cell }) =>
      objectLabels[label] + " " + positionText({ x: cell.dx, y: cell.dy })
    ).join(" · ");
  }

  function showRoute(state) {
    const ctx = routeContext;
    const margin = 12;
    const width = map.width - margin * 2;
    const height = map.height - margin * 2;
    const tileWidth = width / state.grid.width;
    const tileHeight = height / state.grid.height;
    const center = position => [
      margin + (position.x + 0.5) * tileWidth,
      margin + (position.y + 0.5) * tileHeight
    ];

    ctx.fillStyle = "#f4f7f9";
    ctx.fillRect(0, 0, map.width, map.height);
    ctx.strokeStyle = "#ccd9e3";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x <= state.grid.width; x += 1) {
      const line = margin + x * tileWidth;
      ctx.moveTo(line, margin);
      ctx.lineTo(line, margin + height);
    }
    for (let y = 0; y <= state.grid.height; y += 1) {
      const line = margin + y * tileHeight;
      ctx.moveTo(margin, line);
      ctx.lineTo(margin + width, line);
    }
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(...center(state.route[0]));
    for (const point of state.route.slice(1)) ctx.lineTo(...center(point));
    ctx.strokeStyle = "#39729d";
    ctx.lineWidth = 3;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.stroke();

    for (const [point, color, radius, filled] of [
      [state.start, "#39729d", 7, false],
      [state.goal, "#258169", 8, false],
      [state.pose, "#182e47", 4, true]
    ]) {
      ctx.beginPath();
      ctx.arc(...center(point), radius, 0, 2 * Math.PI);
      if (filled) {
        ctx.fillStyle = color;
        ctx.fill();
      } else {
        ctx.strokeStyle = color;
        ctx.stroke();
      }
    }
    byId("pose-value").textContent = "当前位置 " + positionText(state.pose);
    byId("route-text").textContent = state.route.map(positionText).join(" → ");
  }

  function showLogs(records) {
    logRows.replaceChildren();
    for (const record of records) {
      const row = logRows.insertRow();
      for (const value of [
        record.tick, record.sim_time_ms + " ms",
        record.detection.status + " · " + record.detection.detections.length,
        record.link_event ?? record.link_state,
        record.command.action + " · " + record.command.reason,
        positionText(record.pose_after), runLabels[record.run_state]
      ]) {
        row.insertCell().textContent = value;
      }
    }
  }

  function render() {
    const state = simulation.readState();
    const record = state.records.at(-1);
    run.dataset.state = state.run_state;
    run.textContent = runLabels[state.run_state];
    link.dataset.state = state.link_state;
    link.textContent = linkLabels[state.link_state];
    start.disabled = !algorithmsReady || !["ready", "paused"].includes(state.run_state);
    start.textContent = state.run_state === "paused" ? "继续" : "开始";
    pause.disabled = state.run_state !== "running";
    byId("logical-tick").textContent = record ? "拍 " + record.tick : "—";
    byId("logical-time").textContent = record ? record.sim_time_ms + " ms" : "—";
    showCamera(record);
    showRoute(state);
    showLogs(state.records);
  }

  function stopPlayback() {
    clearTimeout(timer);
    timer = null;
  }

  function playTick() {
    timer = null;
    try {
      simulation.step();
    } catch (failure) {
      simulation.pause();
      showError("推进失败。" + failure.message);
    }
    render();
    if (simulation.readState().run_state === "running") timer = setTimeout(playTick, playbackDelayMs);
  }

  function selectScene() {
    stopPlayback();
    simulation = api.createSimulation(sceneSelect.value);
    showError(algorithmsReady ? "" : "缺少本地检测或控制脚本。");
    render();
  }

  sceneSelect.addEventListener("change", selectScene);
  start.addEventListener("click", () => {
    showError("");
    simulation.start();
    playTick();
  });
  pause.addEventListener("click", () => {
    stopPlayback();
    simulation.pause();
    render();
  });
  reset.addEventListener("click", () => {
    stopPlayback();
    simulation.reset();
    showError(algorithmsReady ? "" : "缺少本地检测或控制脚本。");
    render();
  });
  exportButton.addEventListener("click", () => {
    const result = simulation.exportRun();
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2) + "\n"], { type: "application/json" }));
    const download = document.createElement("a");
    download.href = url;
    download.download = result.contract_id + "-" + result.scene_id + ".json";
    download.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  selectScene();

  if (location.hash === "#test") {
    api.testMonitor = Object.freeze({
      selectScene(id) {
        if (!Array.from(sceneSelect.options).some(option => option.value === id)) throw new RangeError("未知场景 " + id);
        sceneSelect.value = id;
        selectScene();
      },
      step(options) {
        stopPlayback();
        if (simulation.readState().run_state === "ready") simulation.start();
        const record = simulation.step(options);
        render();
        return record;
      },
      readFrame: () => simulation.readFrame(),
      readState: () => simulation.readState()
    });
  }
})();
