"""Synthetic rail operations KPI generator and scenario levers."""

from __future__ import annotations

import numpy as np
import pandas as pd

LINES = ["西部幹線北段", "西部幹線中段", "西部幹線南段", "宜蘭線", "屏東線"]
PEAKS = ["尖峰上班", "尖峰下班", "離峰"]

# Explicit mapping instead of Python's randomized hash(), so the same seed is
# reproducible across processes and CI runs.
LINE_BIAS = {
    "西部幹線北段": 0.6,
    "西部幹線中段": 0.4,
    "西部幹線南段": 0.5,
    "宜蘭線": 0.2,
    "屏東線": 0.3,
}


def generate_ops_panel(
    n_days: int = 14,
    seed: int = 42,
    start: str = "2026-09-01",
) -> pd.DataFrame:
    """Return a deterministic synthetic date × line × peak KPI panel."""
    if n_days < 1:
        raise ValueError("n_days must be >= 1")

    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start, periods=n_days, freq="D")
    rows: list[dict] = []

    for d in dates:
        weekend = int(d.dayofweek >= 5)
        for line in LINES:
            line_bias = LINE_BIAS[line]
            for peak in PEAKS:
                peak_mult = {"尖峰上班": 1.25, "尖峰下班": 1.35, "離峰": 0.70}[peak]
                base_riders = 800 + 200 * line_bias
                ridership = int(
                    rng.normal(base_riders * peak_mult * (1.08 if weekend else 1.0), 80)
                )
                ridership = max(ridership, 50)

                capacity = 1200
                crowding = min(1.0, ridership / capacity + rng.uniform(-0.05, 0.08))
                crowding = float(np.clip(crowding, 0.05, 0.99))

                weather = float(rng.uniform(0, 0.35))
                delay_risk = float(
                    np.clip(
                        0.15 * crowding
                        + 0.40 * weather
                        + 0.08 * weekend
                        + rng.normal(0, 0.05),
                        0.02,
                        0.95,
                    )
                )

                otp = float(
                    np.clip(0.96 - 0.35 * delay_risk + rng.normal(0, 0.02), 0.55, 0.99)
                )
                avg_delay_min = float(
                    np.clip(2 + 25 * delay_risk + rng.normal(0, 1.5), 0, 45)
                )

                rows.append(
                    {
                        "date": d.date().isoformat(),
                        "line": line,
                        "peak": peak,
                        "ridership": ridership,
                        "crowding": round(crowding, 3),
                        "delay_risk": round(delay_risk, 3),
                        "otp": round(otp, 3),
                        "avg_delay_min": round(avg_delay_min, 1),
                        "weekend": weekend,
                    }
                )

    return pd.DataFrame(rows)


def apply_whatif(
    df: pd.DataFrame,
    add_cars: float = 0.0,
    dispatch_buffer_min: float = 0.0,
    demand_shift: float = 0.0,
) -> pd.DataFrame:
    """Apply transparent scenario levers to a copy of the KPI panel."""
    if add_cars < 0 or add_cars > 0.30:
        raise ValueError("add_cars must be between 0 and 0.30")
    if dispatch_buffer_min < 0 or dispatch_buffer_min > 10:
        raise ValueError("dispatch_buffer_min must be between 0 and 10")
    if demand_shift < 0 or demand_shift > 0.20:
        raise ValueError("demand_shift must be between 0 and 0.20")

    out = df.copy()
    cap_factor = 1.0 + add_cars
    out["crowding"] = (out["crowding"] / cap_factor).clip(0.05, 0.99)

    if demand_shift:
        peak_mask = out["peak"].isin(["尖峰上班", "尖峰下班"])
        out.loc[peak_mask, "ridership"] = (
            out.loc[peak_mask, "ridership"] * (1.0 - demand_shift)
        ).astype(int)

        off_mask = out["peak"] == "離峰"
        out.loc[off_mask, "ridership"] = (
            out.loc[off_mask, "ridership"] * (1.0 + 0.5 * demand_shift)
        ).astype(int)
        out["crowding"] = (out["ridership"] / 1200.0).clip(0.05, 0.99)

    buffer_effect = dispatch_buffer_min / 10.0 * 0.25
    out["delay_risk"] = (
        out["delay_risk"] * (1.0 - buffer_effect) - 0.10 * (cap_factor - 1.0)
    ).clip(0.02, 0.95)
    out["otp"] = (0.96 - 0.35 * out["delay_risk"]).clip(0.55, 0.99)
    out["avg_delay_min"] = (2 + 25 * out["delay_risk"]).clip(0, 45).round(1)

    out["crowding"] = out["crowding"].round(3)
    out["delay_risk"] = out["delay_risk"].round(3)
    out["otp"] = out["otp"].round(3)
    return out
