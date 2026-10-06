"""Incident-aware briefing functions."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd

from .incidents import active_incidents, incident_impact


def apply_incident_impacts(df: pd.DataFrame, incidents: list[dict], as_of: str) -> pd.DataFrame:
    """Apply active incident assumptions to matching lines."""
    out = df.copy()
    active = active_incidents(incidents, as_of)
    by_line: dict[str, list[dict]] = defaultdict(list)
    for item in active:
        by_line[item["line"]].append(incident_impact(item))

    out["active_incidents"] = 0
    for line, impacts in by_line.items():
        mask = out["line"] == line
        if not mask.any():
            continue
        capacity_loss = min(sum(i["capacity_loss"] for i in impacts), 0.50)
        extra_delay = sum(i["extra_delay_min"] for i in impacts)
        risk_add = min(sum(i["delay_risk_add"] for i in impacts), 0.50)

        out.loc[mask, "active_incidents"] = len(impacts)
        out.loc[mask, "crowding"] = (
            out.loc[mask, "crowding"] / max(1.0 - capacity_loss, 0.50)
        ).clip(0.05, 0.99)
        out.loc[mask, "avg_delay_min"] = (
            out.loc[mask, "avg_delay_min"] + extra_delay
        ).clip(0, 90)
        out.loc[mask, "delay_risk"] = (
            out.loc[mask, "delay_risk"] + risk_add
        ).clip(0.02, 0.99)
        out.loc[mask, "otp"] = (
            out.loc[mask, "otp"] - 0.35 * risk_add
        ).clip(0.40, 0.99)

    for col in ["crowding", "delay_risk", "otp"]:
        out[col] = out[col].round(3)
    out["avg_delay_min"] = out["avg_delay_min"].round(1)
    return out


def briefing_recommendations(df: pd.DataFrame, top_n: int = 5) -> list[dict]:
    """Rank latest-day line/peak cells and attach transparent actions."""
    latest = df[df["date"] == df["date"].max()].copy()
    if latest.empty:
        return []

    if "active_incidents" not in latest:
        latest["active_incidents"] = 0

    latest["score"] = (
        0.45 * latest["delay_risk"]
        + 0.35 * latest["crowding"]
        + 0.10 * (1.0 - latest["otp"])
        + 0.10 * (latest["active_incidents"].clip(0, 2) / 2.0)
    )
    focus = latest.sort_values(["score", "avg_delay_min"], ascending=False).head(top_n)

    recs: list[dict] = []
    for _, row in focus.iterrows():
        actions: list[str] = []
        if row["active_incidents"] > 0:
            actions.append("先確認事件處置狀態與預估恢復時間")
        if row["crowding"] >= 0.78:
            actions.append("評估尖峰疏運、月台分流或運能調整")
        if row["delay_risk"] >= 0.45:
            actions.append("預留調度緩衝並追蹤瓶頸區段")
        if row["otp"] < 0.85 or row["avg_delay_min"] >= 12:
            actions.append("提前更新延誤與轉乘資訊")
        if not actions:
            actions.append("維持常態監控")

        recs.append(
            {
                "line": row["line"],
                "peak": row["peak"],
                "priority_score": round(float(row["score"]), 3),
                "delay_risk": round(float(row["delay_risk"]), 3),
                "crowding": round(float(row["crowding"]), 3),
                "otp": round(float(row["otp"]), 3),
                "avg_delay_min": round(float(row["avg_delay_min"]), 1),
                "active_incidents": int(row["active_incidents"]),
                "actions": "；".join(actions),
            }
        )
    return recs


def briefing_markdown(df: pd.DataFrame, top_n: int = 5) -> str:
    rows = briefing_recommendations(df, top_n=top_n)
    if not rows:
        return "# Rail Ops Briefing\n\nNo data.\n"

    lines = ["# Rail Ops Briefing", "", "| Rank | Line / slot | Risk | Crowding | OTP | Delay | Incidents |", "|---:|---|---:|---:|---:|---:|---:|"]
    for idx, row in enumerate(rows, 1):
        lines.append(
            f"| {idx} | {row['line']} / {row['peak']} | "
            f"{row['delay_risk']:.1%} | {row['crowding']:.1%} | "
            f"{row['otp']:.1%} | {row['avg_delay_min']:.1f} min | "
            f"{row['active_incidents']} |"
        )
    lines.extend(["", "## Actions", ""])
    for row in rows:
        lines.append(f"- **{row['line']} / {row['peak']}** — {row['actions']}")
    lines.extend(
        [
            "",
            "> Scenario model only. KPI and incident impacts are synthetic assumptions, not official railway operational estimates.",
            "",
        ]
    )
    return "\n".join(lines)
