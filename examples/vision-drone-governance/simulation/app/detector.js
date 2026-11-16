(() => {
  "use strict";

  const WIDTH = 160;
  const HEIGHT = 120;
  const PIXEL_COUNT = WIDTH * HEIGHT;
  const BYTES_PER_PIXEL = 4;
  const TICK_MS = 100;
  const GRID_SIZE = 5;
  const GRID_ORIGIN = 2;
  const MIN_COMPONENT_PIXELS = 16;
  const SCENE_IDS = new Set(["clear-room", "fixed-obstacle", "drop-and-recover"]);
  const CLASSES = [
    { label: "wall", rgba: [96, 112, 128, 255] },
    { label: "column", rgba: [220, 90, 50, 255] },
    { label: "box", rgba: [230, 180, 60, 255] },
  ];

  function rgbaKey(red, green, blue, alpha) {
    return ((red << 24) | (green << 16) | (blue << 8) | alpha) >>> 0;
  }

  const classByColor = new Map(
    CLASSES.map(({ rgba }, index) => [rgbaKey(...rgba), index + 1]),
  );

  function isPixelBuffer(pixels) {
    return ArrayBuffer.isView(pixels)
      && Object.prototype.toString.call(pixels) === "[object Uint8ClampedArray]"
      && pixels.length === PIXEL_COUNT * BYTES_PER_PIXEL;
  }

  function collectComponent(classIds, stack, start, classId) {
    let stackSize = 0;
    let count = 0;
    let minX = WIDTH;
    let minY = HEIGHT;
    let maxX = 0;
    let maxY = 0;

    function pushMatching(index) {
      if (classIds[index] === classId) {
        classIds[index] = 0;
        stack[stackSize++] = index;
      }
    }

    pushMatching(start);
    while (stackSize > 0) {
      const index = stack[--stackSize];
      const x = index % WIDTH;
      const y = Math.floor(index / WIDTH);
      count += 1;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);

      if (x > 0) pushMatching(index - 1);
      if (x + 1 < WIDTH) pushMatching(index + 1);
      if (y > 0) pushMatching(index - WIDTH);
      if (y + 1 < HEIGHT) pushMatching(index + WIDTH);
    }

    if (count < MIN_COMPONENT_PIXELS) return null;

    const endX = maxX + 1;
    const endY = maxY + 1;
    // Project the same half-open box center in pixel units to preserve exact grid boundaries.
    const col = Math.floor(GRID_SIZE * (minX + endX) / (2 * WIDTH));
    const row = Math.floor(GRID_SIZE * (minY + endY) / (2 * HEIGHT));
    return {
      label: CLASSES[classId - 1].label,
      region: {
        x_min: minX / WIDTH,
        y_min: minY / HEIGHT,
        x_max: endX / WIDTH,
        y_max: endY / HEIGHT,
      },
      cell: { dx: col - GRID_ORIGIN, dy: row - GRID_ORIGIN },
      pixel_count: count,
    };
  }

  function detectPixels(pixels) {
    const classIds = new Uint8Array(PIXEL_COUNT);
    for (let index = 0; index < PIXEL_COUNT; index += 1) {
      const offset = index * BYTES_PER_PIXEL;
      const color = rgbaKey(pixels[offset], pixels[offset + 1], pixels[offset + 2], pixels[offset + 3]);
      classIds[index] = classByColor.get(color) ?? 0;
    }

    const stack = new Uint16Array(PIXEL_COUNT);
    const detections = [];
    for (let index = 0; index < PIXEL_COUNT; index += 1) {
      const classId = classIds[index];
      if (classId === 0) continue;
      const detection = collectComponent(classIds, stack, index, classId);
      if (detection) detections.push(detection);
    }
    detections.sort((a, b) => (
      a.region.y_min - b.region.y_min
      || a.region.x_min - b.region.x_min
      || Number(a.label > b.label) - Number(a.label < b.label)
    ));
    return detections;
  }

  function detectFrame(frameEnvelope) {
    const { scene_id, tick, sim_time_ms, frame } = frameEnvelope ?? {};
    const emptyResult = {
      scene_id: scene_id ?? null,
      tick: tick ?? null,
      sim_time_ms: sim_time_ms ?? null,
      frame_id: null,
      detections: [],
    };
    const invalid = (error) => ({ ...emptyResult, status: "invalid", error });

    if (!SCENE_IDS.has(scene_id)) return invalid("scene_id must name a contract scene.");
    if (!Number.isSafeInteger(tick) || tick < 0) return invalid("tick must be a nonnegative integer.");
    if (!Number.isSafeInteger(sim_time_ms) || sim_time_ms !== tick * TICK_MS) {
      return invalid("sim_time_ms must be tick × 100.");
    }
    if (frame === null) return { ...emptyResult, status: "missing", error: null };
    if (!frame || frame.frame_id !== `${scene_id}:${tick}`) {
      return invalid("frame_id must match scene_id and tick.");
    }
    if (frame.width_px !== WIDTH || frame.height_px !== HEIGHT) {
      return invalid("Frame dimensions must be 160 × 120 pixels.");
    }
    if (frame.pixel_format !== "RGBA8") return invalid("pixel_format must be RGBA8.");
    if (!isPixelBuffer(frame.pixels)) {
      return invalid("pixels must be a Uint8ClampedArray containing 76800 bytes.");
    }

    return {
      ...emptyResult,
      frame_id: frame.frame_id,
      status: "ok",
      detections: detectPixels(frame.pixels),
      error: null,
    };
  }

  globalThis.RC8DroneSimV2 ??= {};
  globalThis.RC8DroneSimV2.detectFrame = detectFrame;
})();
