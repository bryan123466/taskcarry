"""Validate the pinned RC8 indoor replay and print the observed ticks as JSON."""

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path


REPLAY_VERSION = "rc8-indoor-replay-v1"
FIXTURE_SHA256 = "2c5e0a9157c0bc0ce7a2f4681f3faeb1e8693e19f144b72b0b066e1386198b17"
INPUT_PROFILE = {"width_px": 640, "height_px": 480, "pixel_format": "RGB24", "nominal_fps": 15}
LABELS = {"wall": "墙面", "column": "立柱", "box": "箱体"}
EVENT_KEYS = {"frame_id", "label", "region", "confidence", "timestamp_ms"}
REGION_KEYS = ("x_min", "y_min", "x_max", "y_max")
LEFT_BOUNDARY = Fraction(1, 3)
RIGHT_BOUNDARY = Fraction(2, 3)


class ReplayError(ValueError):
    """An input or a verification probe failed."""


def require_fields(value, required, location, *, exact=False):
    if not isinstance(value, dict):
        raise ReplayError(f"{location} must be an object")
    missing = required - value.keys()
    if missing:
        raise ReplayError(f"{location} is missing {', '.join(sorted(missing))}")
    if exact and value.keys() != required:
        extras = value.keys() - required
        raise ReplayError(f"{location} has unexpected fields {', '.join(sorted(extras))}")
    return value


def unit_number(value, location):
    # JSON fractional numbers are parsed as Fractions, so these types are finite.
    if type(value) not in (int, Fraction) or not 0 <= value <= 1:
        raise ReplayError(f"{location} must be a finite number in [0, 1]")
    return value


def display_zone(center_x):
    if center_x < LEFT_BOUNDARY:
        return "left"
    if center_x < RIGHT_BOUNDARY:
        return "center"
    return "right"


def validate_event(event, frame_id, timestamp_ms, location):
    event = require_fields(event, EVENT_KEYS, location, exact=True)
    if event["frame_id"] != frame_id:
        raise ReplayError(f"{location}.frame_id must match {frame_id!r}")
    if type(event["timestamp_ms"]) is not int or event["timestamp_ms"] != timestamp_ms:
        raise ReplayError(f"{location}.timestamp_ms must match {timestamp_ms}")
    label = event["label"]
    if not isinstance(label, str) or label not in LABELS:
        raise ReplayError(f"{location}.label must be wall, column, or box")
    confidence = unit_number(event["confidence"], f"{location}.confidence")
    raw_region = require_fields(event["region"], set(REGION_KEYS), f"{location}.region", exact=True)
    region = {axis: unit_number(raw_region[axis], f"{location}.region.{axis}") for axis in REGION_KEYS}
    if region["x_min"] >= region["x_max"] or region["y_min"] >= region["y_max"]:
        raise ReplayError(f"{location}.region must have positive width and height")
    center_x = (Fraction(region["x_min"]) + region["x_max"]) / 2
    return {
        "frame_id": event["frame_id"],
        "timestamp_ms": event["timestamp_ms"],
        "label": label,
        "confidence": float(confidence),
        "region": {axis: float(region[axis]) for axis in REGION_KEYS},
        "center_x": str(center_x),
        "display_zone": display_zone(center_x),
    }


def rounded_timestamp_ms(tick, nominal_fps):
    # Compute floor(tick * 1000 / fps + 1/2) for each tick using integers.
    return (2 * tick * 1000 + nominal_fps) // (2 * nominal_fps)


def validate_ticks(ticks, nominal_fps):
    if not isinstance(ticks, list) or not ticks:
        raise ReplayError("ticks must be a nonempty array")

    seen_frame_ids = set()
    observations = []
    for index, tick in enumerate(ticks):
        location = f"ticks[{index}]"
        tick = require_fields(tick, {"tick", "timestamp_ms", "frame"}, location)
        if type(tick["tick"]) is not int or tick["tick"] != index:
            raise ReplayError(f"{location}.tick must equal {index}")
        timestamp_ms = rounded_timestamp_ms(index, nominal_fps)
        if type(tick["timestamp_ms"]) is not int or tick["timestamp_ms"] != timestamp_ms:
            raise ReplayError(f"{location}.timestamp_ms must equal {timestamp_ms}")

        frame = tick["frame"]
        if frame is not None:
            frame_location = f"{location}.frame"
            frame = require_fields(frame, {"frame_id", "processing_status", "events"}, frame_location)
            frame_id = frame["frame_id"]
            if not isinstance(frame_id, str) or not frame_id:
                raise ReplayError(f"{frame_location}.frame_id must be a nonempty string")
            if frame_id in seen_frame_ids:
                raise ReplayError(f"{frame_location}.frame_id repeats {frame_id!r}")
            seen_frame_ids.add(frame_id)
            if frame["processing_status"] != "ok" or not isinstance(frame["events"], list):
                raise ReplayError(f"{frame_location} must have processing_status 'ok' and an events array")
            events = [
                validate_event(event, frame_id, timestamp_ms, f"{frame_location}.events[{event_index}]")
                for event_index, event in enumerate(frame["events"])
            ]
            frame = {"frame_id": frame_id, "processing_status": frame["processing_status"], "events": events}
        observations.append({"tick": tick["tick"], "timestamp_ms": tick["timestamp_ms"], "frame": frame})

    return observations


def verify_in_memory():
    seed = {
        "frame_id": "probe-000",
        "timestamp_ms": 0,
        "label": "wall",
        "confidence": Fraction(1, 2),
        "region": {"x_min": Fraction(1, 4), "y_min": 0, "x_max": Fraction(3, 4), "y_max": 1},
    }
    boundary_results = []
    for x_min, x_max, expected_center, expected_zone in (
        (0, Fraction(2, 3), "1/3", "center"),
        (Fraction(1, 3), 1, "2/3", "right"),
    ):
        region = {**seed["region"], "x_min": x_min, "x_max": x_max}
        event = validate_event({**seed, "region": region}, "probe-000", 0, "boundary_event")
        if event["center_x"] != expected_center or event["display_zone"] != expected_zone:
            raise ReplayError(f"boundary at {expected_center} did not map to {expected_zone}")
        boundary_results.append({
            "x_min": str(x_min),
            "x_max": str(x_max),
            "center_x": event["center_x"],
            "display_zone": event["display_zone"],
        })

    invalid_results = []
    zero_width = {**seed["region"], "x_max": seed["region"]["x_min"]}
    for field, value, description in (
        ("frame_id", "probe-other", "probe-other in parent frame probe-000"),
        ("timestamp_ms", 1, "1 ms in the 0 ms tick"),
        ("label", "barrier", "barrier"),
        ("confidence", float("inf"), "float('inf')"),
        ("region", zero_width, "x_min = x_max = 1/4"),
    ):
        try:
            validate_event({**seed, field: value}, "probe-000", 0, "invalid_event")
        except ReplayError as error:
            if not str(error).startswith(f"invalid_event.{field} "):
                raise
            invalid_results.append({
                "field": field,
                "injected_value": description,
                "rejected": True,
                "error": str(error),
            })
        else:
            raise ReplayError(f"the invalid {field} probe was accepted")

    return {"region_boundaries": boundary_results, "invalid_events": invalid_results}


def reject_nonfinite_json(token):
    raise ReplayError(f"JSON token {token!r} is not a finite number")


def inspect_fixture(path):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != FIXTURE_SHA256:
        raise ReplayError(f"fixture SHA-256 is {digest}, expected {FIXTURE_SHA256}")
    data = json.loads(raw.decode("utf-8"), parse_float=Fraction, parse_constant=reject_nonfinite_json)
    required = {"replay_version", "source", "scenario", "input_profile", "labels", "ticks"}
    data = require_fields(data, required, "replay")
    if data["replay_version"] != REPLAY_VERSION:
        raise ReplayError(f"replay_version must equal {REPLAY_VERSION!r}")
    if data["source"] != "synthetic" or data["scenario"] != "indoor_fixed_obstacles":
        raise ReplayError("the replay must describe synthetic indoor fixed obstacles")
    profile = require_fields(data["input_profile"], set(INPUT_PROFILE), "input_profile")
    if any(
        type(profile[key]) is not type(expected) or profile[key] != expected
        for key, expected in INPUT_PROFILE.items()
    ):
        raise ReplayError("input_profile must specify 640 × 480 RGB24 and nominal 15 fps")
    if data["labels"] != LABELS:
        raise ReplayError("labels must match the wall, column, and box dictionary")

    ticks = validate_ticks(data["ticks"], profile["nominal_fps"])
    received_frames = [tick["frame"] for tick in ticks if tick["frame"] is not None]
    events = [event for frame in received_frames for event in frame["events"]]
    return {
        "replay_version": data["replay_version"],
        "fixture_sha256": digest,
        "fixture_bytes": len(raw),
        "input_profile": {key: profile[key] for key in INPUT_PROFILE},
        "counts": {
            "ticks": len(ticks),
            "received_frames": len(received_frames),
            "candidate_events": len(events),
            "empty_frames": sum(not frame["events"] for frame in received_frames),
            "missing_ticks": len(ticks) - len(received_frames),
        },
        "ticks": ticks,
        "in_memory_probes": verify_in_memory(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="Path to the original RC8 indoor replay JSON bytes")
    args = parser.parse_args()
    try:
        report = inspect_fixture(args.fixture)
    except (OSError, ValueError) as error:
        print(f"Replay validation failed. {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
