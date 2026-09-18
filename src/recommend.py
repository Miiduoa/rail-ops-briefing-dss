"""Rule-based briefing recommendations (transparent, not ML)."""

from __future__ import annotations

import pandas as pd


def briefing_recommendations(df: pd.DataFrame, top_n: int = 5) -> list[dict]:
    """Produce actionable briefing bullets from KPI thresholds."""
    latest = df[df["date"] == df["date"].max()].copy()
    latest["score"] = 0.55 * latest["delay_risk"] + 0.45 * latest["crowding"]
    focus = latest.sort_values("score", ascending=False).head(top_n)

    recs: list[dict] = []
    for _, r in focus.iterrows():
        actions: list[str] = []
        if r["crowding"] >= 0.75:
            actions.append("尖峰加掛／疏運班次，或引導離峰優惠分流")
        if r["delay_risk"] >= 0.45:
            actions.append("加大調度緩衝、優先處理瓶頸交會／會車")
        if r["otp"] < 0.85:
            actions.append("啟動準點率加強監控與車次銜接檢查")
        if r["avg_delay_min"] >= 12:
            actions.append("旅客資訊加強（延誤廣播／轉乘提示）")
        if not actions:
            actions.append("維持常態監控，關注天氣與臨時施工")

        recs.append(
            {
                "line": r["line"],
                "peak": r["peak"],
                "delay_risk": r["delay_risk"],
                "crowding": r["crowding"],
                "otp": r["otp"],
                "actions": "；".join(actions),
            }
        )
    return recs
