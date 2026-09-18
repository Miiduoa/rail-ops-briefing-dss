"""Synthetic rail / ops KPI panel generator (seeded)."""

from __future__ import annotations

import numpy as np
import pandas as pd

LINES = ["西部幹線北段", "西部幹線中段", "西部幹線南段", "宜蘭線", "屏東線"]
PEAKS = ["尖峰上班", "尖峰下班", "離峰"]


def generate_ops_panel(
    n_days: int = 14,
    seed: int = 42,
    start: str = "2026-09-01",
) -> pd.DataFrame:
    """Daily × line × peak-slot KPIs: delay risk, crowding proxy, ridership."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start, periods=n_days, freq="D")
    rows: list[dict] = []

    for d in dates:
        weekend = int(d.dayofweek >= 5)
        for line in LINES:
            line_bias = hash(line) % 7 / 10.0  # stable per-line offset
            for peak in PEAKS:
                peak_mult = {"尖峰上班": 1.25, "尖峰下班": 1.35, "離峰": 0.7}[peak]
                base_riders = 800 + 200 * line_bias
                ridership = int(rng.normal(base_riders * peak_mult * (1.1 if weekend else 1.0), 80))
                ridership = max(ridership, 50)

                # crowding proxy 0–1
                capacity = 1200
                crowding = min(1.0, ridership / capacity + rng.uniform(-0.05, 0.08))
                crowding = float(np.clip(crowding, 0.05, 0.99))

                # delay risk: weather + crowding + weekend maintenance noise
                weather = float(rng.uniform(0, 0.35))
                delay_risk = float(
                    np.clip(
                        0.15 * crowding + 0.4 * weather + 0.08 * weekend + rng.normal(0, 0.05),
                        0.02,
                        0.95,
                    )
                )

                otp = float(np.clip(0.96 - 0.35 * delay_risk + rng.normal(0, 0.02), 0.55, 0.99))
                avg_delay_min = float(np.clip(2 + 25 * delay_risk + rng.normal(0, 1.5), 0, 45))

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
    """Rule-based what-if levers on a copy of the panel.

    - add_cars: fraction of extra capacity (0–0.3) → lowers crowding
    - dispatch_buffer_min: extra recovery minutes (0–10) → lowers delay risk
    - demand_shift: fraction of demand moved off-peak (-0.2–0.2 on peak slots)
    """
    out = df.copy()
    cap_factor = 1.0 + max(0.0, add_cars)
    out["crowding"] = (out["crowding"] / cap_factor).clip(0.05, 0.99)

    if demand_shift != 0:
        peak_mask = out["peak"].isin(["尖峰上班", "尖峰下班"])
        out.loc[peak_mask, "ridership"] = (
            out.loc[peak_mask, "ridership"] * (1.0 - demand_shift)
        ).astype(int)
        off = out["peak"] == "離峰"
        out.loc[off, "ridership"] = (
            out.loc[off, "ridership"] * (1.0 + 0.5 * abs(demand_shift))
        ).astype(int)
        out["crowding"] = (out["ridership"] / 1200.0).clip(0.05, 0.99)

    buffer_effect = min(dispatch_buffer_min, 10.0) / 10.0 * 0.25
    out["delay_risk"] = (out["delay_risk"] * (1.0 - buffer_effect) - 0.1 * (cap_factor - 1)).clip(
        0.02, 0.95
    )
    out["otp"] = (0.96 - 0.35 * out["delay_risk"]).clip(0.55, 0.99)
    out["avg_delay_min"] = (2 + 25 * out["delay_risk"]).clip(0, 45).round(1)
    out["crowding"] = out["crowding"].round(3)
    out["delay_risk"] = out["delay_risk"].round(3)
    out["otp"] = out["otp"].round(3)
    return out
