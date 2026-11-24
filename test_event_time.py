import unittest

from event_time import DEMO, Reading, replay


class EventTimeTests(unittest.TestCase):
    def test_demo_accepts_out_of_order_events_and_drops_late_events(self):
        result = replay(DEMO)
        self.assertEqual(result["windows"][0], {
            "sensor": "cold-room", "start": 0, "end": 10, "count": 2, "mean": 5.0,
        })
        self.assertEqual(result["late_event_ids"], ["e"])
        self.assertEqual(result["duplicates"], 1)
        self.assertEqual(result["windows"][2]["mean"], 22.0)

    def test_watermark_closes_window_at_its_exclusive_end(self):
        events = [Reading("a", "s", 1, 1), Reading("b", "s", 14, 2),
                  Reading("c", "s", 9, 3), Reading("d", "s", 10, 4)]
        result = replay(events)
        self.assertEqual(result["late_event_ids"], ["c"])
        self.assertEqual(result["windows"][-1]["mean"], 3.0)

    def test_conflicting_replays_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            replay([Reading("a", "s", 1, 1), Reading("a", "s", 1, 2)])

    def test_invalid_numeric_inputs(self):
        with self.assertRaises(ValueError):
            Reading("a", "s", 1, float("nan"))
        with self.assertRaises(ValueError):
            replay(DEMO, window_seconds=0)


if __name__ == "__main__":
    unittest.main()
