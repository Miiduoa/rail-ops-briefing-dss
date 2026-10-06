import unittest

from src.synthetic_kpis import generate_ops_panel, apply_whatif


class SyntheticPanelTests(unittest.TestCase):
    def test_seed_is_reproducible(self):
        a = generate_ops_panel(n_days=2, seed=7)
        b = generate_ops_panel(n_days=2, seed=7)
        self.assertTrue(a.equals(b))

    def test_invalid_lever_rejected(self):
        df = generate_ops_panel(n_days=1, seed=1)
        with self.assertRaises(ValueError):
            apply_whatif(df, add_cars=0.5)

    def test_capacity_lever_does_not_raise_crowding(self):
        df = generate_ops_panel(n_days=1, seed=1)
        adjusted = apply_whatif(df, add_cars=0.2)
        self.assertTrue((adjusted["crowding"] <= df["crowding"]).all())


if __name__ == "__main__":
    unittest.main()
