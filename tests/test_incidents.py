import unittest

from src.incidents import active_incidents, incident_impact, normalize_incidents


class IncidentTests(unittest.TestCase):
    def setUp(self):
        self.item = {
            "incident_id": "i-1",
            "line": "宜蘭線",
            "kind": "weather",
            "severity": "moderate",
            "reported_at": "2026-09-14T06:00:00+08:00",
            "expected_clear_at": "2026-09-14T10:00:00+08:00",
        }

    def test_duplicate_delivery_is_idempotent(self):
        self.assertEqual(len(normalize_incidents([self.item, self.item])), 1)

    def test_active_window(self):
        active = active_incidents([self.item], "2026-09-14T08:00:00+08:00")
        self.assertEqual([x["incident_id"] for x in active], ["i-1"])

    def test_timezone_is_required(self):
        bad = dict(self.item)
        bad["reported_at"] = "2026-09-14T06:00:00"
        with self.assertRaises(ValueError):
            normalize_incidents([bad])

    def test_major_has_larger_impact_than_minor(self):
        minor = dict(self.item, severity="minor")
        major = dict(self.item, severity="major")
        self.assertGreater(
            incident_impact(major)["extra_delay_min"],
            incident_impact(minor)["extra_delay_min"],
        )


if __name__ == "__main__":
    unittest.main()
