"""Recompute the hardware observations for the pinned indoor replay fixture."""

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path


REPLAY_VERSION = "rc8-indoor-replay-v1"
FIXTURE_SHA256 = "2c5e0a9157c0bc0ce7a2f4681f3faeb1e8693e19f144b72b0b066e1386198b17"
RUN_COMMAND = r"python -I -B -X utf8 .\verify_hardware_replay.py"
QUEUE_FRAMES_ASSUMED = 3


def comparison(check_id, expected, observed, method):
    return {
        "id": check_id,
        "status": "PASS" if expected == observed else "FAIL",
        "expected": expected,
        "observed": observed,
        "reproduce": f"{RUN_COMMAND}。{method}",
    }


def pending(check_id, expected, method):
    return {
        "id": check_id,
        "status": "PENDING",
        "expected": expected,
        "observed": None,
        "reproduce": method,
    }


def frame_metadata(ticks):
    frame_ids = []
    processing_statuses = []
    event_counts = []
    empty_ticks = []
    problems = []
    seen = set()

    for tick in ticks:
        frame = tick["frame"]
        if frame is None:
            frame_ids.append(None)
            processing_statuses.append(None)
            event_counts.append(None)
            continue

        frame_id = frame["frame_id"]
        processing_status = frame["processing_status"]
        events = frame["events"]
        frame_ids.append(frame_id)
        processing_statuses.append(processing_status)
        event_counts.append(len(events))
        if frame_id in seen:
            problems.append(f"重复帧号 {frame_id}")
        seen.add(frame_id)
        if processing_status == "ok" and not events:
            empty_ticks.append(tick["tick"])
        for event in events:
            if event["frame_id"] != frame_id or event["timestamp_ms"] != tick["timestamp_ms"]:
                problems.append(f"{frame_id} 的事件帧号或时间未对齐")
            box = event["region"]
            if not (0 <= box["x_min"] < box["x_max"] <= 1 and 0 <= box["y_min"] < box["y_max"] <= 1):
                problems.append(f"{frame_id} 的事件框超出整帧归一化坐标约定")

    return {
        "frame_id_by_tick": frame_ids,
        "processing_status_by_tick": processing_statuses,
        "candidate_count_by_tick": event_counts,
        "received_total": sum(frame_id is not None for frame_id in frame_ids),
        "empty_frame_ticks": empty_ticks,
        "candidate_total": sum(count for count in event_counts if count is not None),
        "metadata_problems": problems,
    }


def replay_link(ticks, link):
    state = link["initial_state"]
    miss_limit = link["disconnect_after_missed_ticks"]
    missed = 0
    missing_ticks = []
    miss_counts = []
    states = []
    transitions = []

    for tick in ticks:
        index = tick["tick"]
        frame = tick["frame"]
        transition = None
        if frame is None:
            missing_ticks.append(index)
            missed += 1
            if missed >= miss_limit and state != "disconnected":
                state = "disconnected"
                transition = "disconnected"
        else:
            if frame["processing_status"] != "ok":
                raise ValueError(f"第 {index} 拍处理失败，超出本输入的回放状态范围")
            missed = 0
            transition = {"waiting": "connected", "disconnected": "reconnected"}.get(state)
            state = "connected"

        if transition is not None:
            transitions.append({"tick": index, "event": transition})
        miss_counts.append(missed)
        states.append(state)

    return {
        "link_configuration": link,
        "missing_ticks": missing_ticks,
        "consecutive_misses_by_tick": miss_counts,
        "link_state_by_tick": states,
        "transitions": transitions,
    }


def main():
    fixture_path = Path(__file__).with_name(f"{REPLAY_VERSION}.json")
    fixture_bytes = fixture_path.read_bytes()
    digest = sha256(fixture_bytes).hexdigest()
    if digest != FIXTURE_SHA256:
        raise SystemExit(f"输入字节校验失败。预期 {FIXTURE_SHA256}，实得 {digest}")

    fixture = json.loads(fixture_bytes)
    profile = fixture["input_profile"]
    ticks = fixture["ticks"]
    fps = profile["nominal_fps"]
    rounded_ms = [int(Fraction(index * 1000, fps) + Fraction(1, 2)) for index in range(len(ticks))]

    if profile["pixel_format"] != "RGB24":
        raise SystemExit(f"输入像素格式超出本核算范围：{profile['pixel_format']}")
    row_bytes = profile["width_px"] * 3
    frame_bytes = row_bytes * profile["height_px"]

    protocol_times = [0, 67, 133, 200, 267, 333]
    checks = [
        comparison(
            "fixture_identity",
            {"replay_version": REPLAY_VERSION, "sha256": FIXTURE_SHA256, "source": "synthetic"},
            {"replay_version": fixture["replay_version"], "sha256": digest, "source": fixture["source"]},
            "在 JSON 解码前对原始字节计算 SHA-256，再核对版本和来源。",
        ),
        comparison(
            "input_profile",
            {"width_px": 640, "height_px": 480, "pixel_format": "RGB24", "nominal_fps": 15},
            profile,
            "读取 input_profile 四个字段并与共用协议比对。",
        ),
        comparison(
            "replay_clock",
            {"tick_indices": list(range(6)), "computed_ms": protocol_times, "fixture_ms": protocol_times},
            {
                "tick_indices": [tick["tick"] for tick in ticks],
                "computed_ms": rounded_ms,
                "fixture_ms": [tick["timestamp_ms"] for tick in ticks],
            },
            "从索引 0 开始逐拍用精确分数计算 floor(tick × 1000 / 15 + 0.5)，对照 JSON 和协议。",
        ),
        comparison(
            "frame_delivery",
            {
                "frame_id_by_tick": ["indoor-000", "indoor-001", "indoor-002", None, None, "indoor-005"],
                "processing_status_by_tick": ["ok", "ok", "ok", None, None, "ok"],
                "candidate_count_by_tick": [1, 2, 0, None, None, 1],
                "received_total": 4,
                "empty_frame_ticks": [2],
                "candidate_total": 4,
                "metadata_problems": [],
            },
            frame_metadata(ticks),
            "逐拍读取 frame、processing_status 和 events。核对帧号唯一性、事件归帧、时间及整帧归一化框。",
        ),
        comparison(
            "link_replay",
            {
                "link_configuration": {"initial_state": "waiting", "disconnect_after_missed_ticks": 2},
                "missing_ticks": [3, 4],
                "consecutive_misses_by_tick": [0, 0, 0, 1, 2, 0],
                "link_state_by_tick": ["connected"] * 4 + ["disconnected", "connected"],
                "transitions": [
                    {"tick": 0, "event": "connected"},
                    {"tick": 4, "event": "disconnected"},
                    {"tick": 5, "event": "reconnected"},
                ],
            },
            replay_link(ticks, fixture["link"]),
            "以 frame=null 累加连续缺帧数，以 processing_status=ok 的帧清零并更新模拟链路。",
        ),
        comparison(
            "resource_arithmetic",
            {"row_bytes": 1920, "frame_bytes": 921600, "nominal_bytes_per_s": 13824000,
             "assumed_queue_frames": 3, "assumed_queue_raw_bytes": 2764800},
            {"row_bytes": row_bytes, "frame_bytes": frame_bytes, "nominal_bytes_per_s": frame_bytes * fps,
             "assumed_queue_frames": QUEUE_FRAMES_ASSUMED, "assumed_queue_raw_bytes": frame_bytes * QUEUE_FRAMES_ASSUMED},
            "按 RGB24 每像素 3 字节和紧密行排列核算行、帧与名义流量，等待队列按原 3 帧假设计算。",
        ),
        pending(
            "capture_time_and_latency",
            "源帧交付时的 capture_time、时钟和单位约定，以及可与监控端同基准计算的延迟记录。",
            "待接口确认后在入等待队列前记录采集时刻，并按帧匹配同基准的监控接收或显示打点。",
        ),
        pending(
            "hardware_measurement",
            "实际帧载荷和设备的持续吞吐、处理耗时、CPU 占用与峰值内存记录。",
            "需有真实采集和处理链路的测量记录。当前回放提供帧元数据与预置事件。",
        ),
        pending(
            "buffer_behavior",
            "实际缓冲峰值、队列停留和过载处置记录。等待队列深度暂按 3 帧假设。",
            "待对接处理链路后逐帧记录入队、出队和丢弃事件，再核对积压与过载行为。",
        ),
    ]
    evidence = {
        "role": "hardware",
        "replay_version": fixture["replay_version"],
        "fixture_sha256": digest,
        "checks": checks,
    }
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return int(any(check["status"] == "FAIL" for check in checks))


if __name__ == "__main__":
    raise SystemExit(main())
