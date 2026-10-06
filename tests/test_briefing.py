import unittest

from src.briefing import apply_incident_impacts, briefing_markdown, briefing_recommendations
from src.synthetic_kpis import generate_ops_panel


class BriefingTests(unittest.TestCase):
    def setUp(self):
        self.panel = generate_ops_panel(n_days=14, seed=42)
        self.incidents = [
            {
                "incident_id": "i-1",
                "line": "西部幹線北段",
                "kind": "signal",
                "severity": "major",
                "reported_at": "2026-09-14T07:00:00+08:00",
                "expected_clear_at": "2026-09-14T10:00:00+08:00",
            }
        ]

    def test_active_incident_changes_only_matching_line(self):
        out = apply_incident_impacts(
            self.panel, self.incidents, "2026-09-14T08:00:00+08:00"
        )
        affected = out[out["line"] == "西部幹線北段"]
        unaffected = out[out["line"] == "屏東線"]
        self.assertGreater(affected["active_incidents"].max(), 0)
        self.assertEqual(unaffected["active_incidents"].max(), 0)

    def test_briefing_has_ranked_rows(self):
        out = apply_incident_impacts(
            self.panel, self.incidents, "2026-09-14T08:00:00+08:00"
        )
        rows = briefing_recommendations(out, top_n=3)
        self.assertEqual(len(rows), 3)
        self.assertGreaterEqual(rows[0]["priority_score"], rows[-1]["priority_score"])

    def test_markdown_contains_scope_note(self):
        out = apply_incident_impacts(
            self.panel, self.incidents, "2026-09-14T08:00:00+08:00"
        )
        report = briefing_markdown(out)
        self.assertIn("Scenario model only", report)


if __name__ == "__main__":
    unittest.main()
