# Event-Time Replay

Reconstruct sensor summaries from a feed that can arrive out of order. The CLI groups readings into fixed time windows, accepts delayed readings while their window is open, and records the IDs of readings that missed the cutoff.

## Run

Use Python 3.10 or newer. The project uses only the standard library.

```sh
python event_time.py
python -m unittest -v
```

The built-in demo replays eight fictional events. The 0–10 second cold-room window contains two readings with mean **5.0**. A repeated event is counted once, and one reading arrives after the window has closed. The 10–20 second dock window includes an out-of-order reading and has mean **22.0**.

## Replay a feed

Save one event object per line as JSONL. Timestamps are integer seconds and all rows are replayed in file order.

```json
{"event_id":"r1","sensor":"cold-room","timestamp":3,"value":4.0}
```

```sh
python event_time.py readings.jsonl --window 10 --lateness 4
```

The watermark is the largest accepted timestamp minus the lateness allowance. A window `[start, end)` closes when its end is at or before the watermark. The last open windows flush at the end of the feed. Repeated IDs with identical payloads are skipped. A repeated ID with changed data stops the replay.

The watermark is global, so a fast sensor can advance it for the others. This local replay keeps readings and event IDs in memory. A useful next experiment is to compare a global watermark with one per sensor using a feed with uneven arrival delays.

AI-assisted standalone portfolio project. The demonstration uses fictional readings.
