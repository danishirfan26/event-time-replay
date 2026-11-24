"""Replay sensor readings with event-time windows and a lateness allowance."""

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Reading:
    event_id: str
    sensor: str
    timestamp: int
    value: float

    def __post_init__(self):
        if not all(isinstance(item, str) and item.strip()
                   for item in (self.event_id, self.sensor)):
            raise ValueError("Event ID and sensor must be nonempty strings")
        if type(self.timestamp) is not int or self.timestamp < 0:
            raise ValueError("Timestamp must be a nonnegative integer")
        if type(self.value) not in (int, float) or not math.isfinite(self.value):
            raise ValueError("Value must be a finite number")


DEMO = (
    Reading("a", "cold-room", 3, 4.0),
    Reading("b", "cold-room", 12, 8.0),
    Reading("c", "cold-room", 8, 6.0),
    Reading("c", "cold-room", 8, 6.0),
    Reading("d", "dock", 17, 23.0),
    Reading("e", "cold-room", 9, 99.0),
    Reading("f", "dock", 10, 21.0),
    Reading("g", "cold-room", 20, 5.0),
)


def read_jsonl(path):
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if line.strip():
                try:
                    yield Reading(**json.loads(line))
                except (TypeError, ValueError, OverflowError) as error:
                    raise ValueError(f"Line {line_number}: {error}") from error


def replay(readings, window_seconds=10, allowed_lateness=4):
    if type(window_seconds) is not int or window_seconds < 1:
        raise ValueError("Window size must be a positive integer")
    if type(allowed_lateness) is not int or allowed_lateness < 0:
        raise ValueError("Allowed lateness must be a nonnegative integer")

    seen = {}
    active = {}
    closed = []
    late = []
    duplicates = 0
    latest = 0

    def close(keys):
        for start, sensor in sorted(keys):
            values = active.pop((start, sensor))
            closed.append({
                "sensor": sensor, "start": start, "end": start + window_seconds,
                "count": len(values), "mean": round(math.fsum(values) / len(values), 3),
            })

    for reading in readings:
        previous = seen.get(reading.event_id)
        if previous is not None:
            if previous != reading:
                raise ValueError(f"Conflicting payload for event {reading.event_id!r}")
            duplicates += 1
            continue
        seen[reading.event_id] = reading
        start = reading.timestamp // window_seconds * window_seconds
        if start + window_seconds <= latest - allowed_lateness:
            late.append(reading.event_id)
            continue

        active.setdefault((start, reading.sensor), []).append(reading.value)
        latest = max(latest, reading.timestamp)
        watermark = latest - allowed_lateness
        close([key for key in active if key[0] + window_seconds <= watermark])

    close(list(active))
    return {"windows": closed, "late_event_ids": late, "duplicates": duplicates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", help="JSONL file. Omit for the demo.")
    parser.add_argument("--window", type=int, default=10)
    parser.add_argument("--lateness", type=int, default=4)
    args = parser.parse_args()
    try:
        readings = read_jsonl(args.input) if args.input else DEMO
        result = replay(readings, args.window, args.lateness)
    except (OSError, ValueError, OverflowError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
