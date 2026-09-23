"""Focused tests for the two-phase, row-by-row JEV triage in content_monitor.py."""

import unittest
from unittest import mock

import content_monitor as cm

NOUL_BY_URL = {
    "https://a/keep": 0.80,
    "https://a/border": 0.65,
    "https://a/drop": 0.64,
}


def _row(url: str) -> dict:
    return {
        "date": "2026-01-01",
        "url": url,
        "title": "T",
        "summary": "S",
        "source": "src",
        "matched_keywords": "pirateria",
        "tool": "read_feeds",
    }


class FakeJev:
    """Records calls and answers the gate, then the triage, per row."""

    def __init__(self):
        self.calls: list[dict] = []
        self.gate_side_effect: Exception | None = None

    def evaluate(self, state, questions):
        self.calls.append({"state": state, "questions": questions})
        if "isAntiPiracy" in questions:
            if self.gate_side_effect is not None:
                raise self.gate_side_effect
            return {
                "answers": {
                    "isAntiPiracy": {"noul": NOUL_BY_URL.get(state["url"], 0.0)}
                },
                "model": "j",
                "usage": {},
            }
        return {
            "answers": {
                "region": {"choice": "Mexico"},
                "infrastructure": {"choice": "IPTV"},
                "stream_content_type": {"choice": "Movies"},
            },
            "model": "j",
            "usage": {},
        }


class JevTriageTest(unittest.TestCase):
    def test_discards_rows_below_threshold(self):
        jev = FakeJev()
        rows = [_row("https://a/drop"), _row("https://a/keep")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual([r["url"] for r in kept], ["https://a/keep"])
        # One gate call per row plus one triage call for the kept row.
        self.assertEqual(len(jev.calls), 3)
        self.assertEqual(
            sum("isAntiPiracy" not in c["questions"] for c in jev.calls), 1
        )

    def test_kept_row_gets_full_triage(self):
        jev = FakeJev()
        rows = [_row("https://a/keep")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual(kept[0]["Es_Antipirateria"], 0.8)
        self.assertEqual(kept[0]["Region"], "Mexico")
        self.assertEqual(kept[0]["Infraestructura"], "IPTV")
        self.assertEqual(kept[0]["Tipo"], "Movies")
        self.assertEqual(len(jev.calls), 2)
        self.assertNotIn("isAntiPiracy", jev.calls[1]["questions"])

    def test_threshold_is_inclusive(self):
        jev = FakeJev()
        rows = [_row("https://a/border"), _row("https://a/drop")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual([r["url"] for r in kept], ["https://a/border"])
        self.assertEqual(kept[0]["Es_Antipirateria"], 0.65)

    def test_gate_failure_keeps_row_with_empty_verdict(self):
        jev = FakeJev()
        jev.gate_side_effect = cm.jev.JevError("boom")
        rows = [_row("https://a/keep")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["Es_Antipirateria"], "")
        self.assertEqual(kept[0]["Region"], "")
        self.assertEqual(kept[0]["Infraestructura"], "")
        self.assertEqual(kept[0]["Tipo"], "")

    def test_triage_failure_keeps_row_with_empty_columns(self):
        original = FakeJev().evaluate

        def failing_triage(state, questions):
            if "isAntiPiracy" in questions:
                return original(state, questions)
            raise cm.jev.JevError("triage boom")

        rows = [_row("https://a/keep")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=failing_triage):
            kept = cm._jev_triage(rows)

        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["Es_Antipirateria"], 0.8)
        self.assertEqual(kept[0]["Infraestructura"], "")
        self.assertEqual(kept[0]["Region"], "")


if __name__ == "__main__":
    unittest.main()