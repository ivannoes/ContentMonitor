"""Focused tests for the single-call JEV evaluation in content_monitor.py.

A single Jev request per row answers the relevance filters (anti-piracy,
keyword relevance) and the triage questions (region, infrastructure,
content type) together.  Rows that fail the filters stay in the output
with empty triage columns so potential false negatives can be reviewed.
"""

import unittest
from unittest import mock

import content_monitor as cm

# url -> (isAntiPiracy noul, keywordRelevance noul)
NOUL_BY_URL = {
    "https://a/keep": (0.80, 0.90),
    "https://a/anti_border": (0.65, 0.90),
    "https://a/not_anti": (0.60, 0.90),
    "https://a/not_relevant": (0.80, 0.60),
    "https://a/other_region": (0.80, 0.90),
}

_REGION_BY_URL = {
    "https://a/other_region": "Other",
}


def _row(url: str, title: str = "T", summary: str = "S") -> dict:
    return {
        "date": "2026-01-01",
        "url": url,
        "title": title,
        "summary": summary,
        "source": "src",
        "tool": "read_feeds",
    }


class FakeJev:
    """Records calls and answers all questions in one response per row."""

    def __init__(self):
        self.calls: list[dict] = []
        self.side_effect: Exception | None = None

    def evaluate(self, state, questions):
        self.calls.append({"state": state, "questions": questions})
        if self.side_effect is not None:
            raise self.side_effect
        url = state["url"]
        noul, keyword_noul = NOUL_BY_URL.get(url, (0.0, 0.0))
        return {
            "answers": {
                "isAntiPiracy": {"noul": noul},
                "keywordRelevance": {"noul": keyword_noul},
                "infrastructure": {"choice": "IPTV"},
                "region": {"choice": _REGION_BY_URL.get(url, "Mexico")},
                "stream_content_type": {"choice": "Movies"},
            },
            "model": "j",
            "usage": {},
        }


def _only_question_ids(jev: FakeJev) -> list[str]:
    return sorted(jev.calls[0]["questions"].keys())


class JevTriageTest(unittest.TestCase):
    def test_single_call_with_all_questions_per_row(self):
        jev = FakeJev()
        rows = [_row("https://a/keep"), _row("https://a/not_anti")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            cm._jev_triage(rows)

        # Exactly one HTTP call per row (no duplicated gate + triage calls).
        self.assertEqual(len(jev.calls), 2)
        self.assertEqual(
            _only_question_ids(jev),
            [
                "infrastructure",
                "isAntiPiracy",
                "keywordRelevance",
                "region",
                "stream_content_type",
            ],
        )
        self.assertIn("keywords", jev.calls[0]["state"])

    def test_kept_row_gets_full_triage_and_local_keyword_matches(self):
        jev = FakeJev()
        rows = [_row("https://a/keep", title="IPTV pirateria en Mexico")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual(kept[0]["Es_Antipirateria"], 0.8)
        self.assertEqual(kept[0]["Region"], "Mexico")
        self.assertEqual(kept[0]["Infraestructura"], "IPTV")
        self.assertEqual(kept[0]["Tipo"], "Movies")
        self.assertIn("IPTV", kept[0]["matched_keywords"])
        self.assertEqual(len(jev.calls), 1)

    def test_keeps_non_anti_piracy_row_without_triage(self):
        jev = FakeJev()
        rows = [_row("https://a/not_anti", title="IPTV pirateria en Mexico")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual(len(kept), 1)
        drop = kept[0]
        self.assertEqual(drop["title"], "IPTV pirateria en Mexico")
        self.assertEqual(drop["Es_Antipirateria"], "")
        self.assertEqual(drop["Region"], "")
        self.assertEqual(drop["Infraestructura"], "")
        self.assertEqual(drop["Tipo"], "")
        self.assertEqual(len(jev.calls), 1)

    def test_keeps_keyword_irrelevant_row_without_triage(self):
        jev = FakeJev()
        rows = [_row("https://a/not_relevant")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["Es_Antipirateria"], "")
        self.assertEqual(kept[0]["Region"], "")

    def test_other_region_row_without_triage(self):
        jev = FakeJev()
        rows = [_row("https://a/other_region")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["Es_Antipirateria"], "")
        self.assertEqual(kept[0]["Region"], "")

    def test_threshold_is_inclusive(self):
        jev = FakeJev()
        rows = [_row("https://a/anti_border")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual(kept[0]["Es_Antipirateria"], 0.65)
        self.assertEqual(kept[0]["Infraestructura"], "IPTV")

    def test_jev_failure_keeps_row_with_empty_verdict(self):
        jev = FakeJev()
        jev.side_effect = cm.jev.JevError("boom")
        rows = [_row("https://a/keep")]
        with mock.patch.object(cm.jev, "evaluate", side_effect=jev.evaluate):
            kept = cm._jev_triage(rows)

        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["Es_Antipirateria"], "")
        self.assertEqual(kept[0]["Region"], "")
        self.assertEqual(kept[0]["Infraestructura"], "")
        self.assertEqual(kept[0]["Tipo"], "")


if __name__ == "__main__":
    unittest.main()