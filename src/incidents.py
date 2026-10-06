"""Incident feed validation, deduplication and impact assumptions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

ALLOWED_TYPES = {"signal", "rolling_stock", "weather", "track", "passenger", "power"}
SEVERITIES = {"minor": 1, "moderate": 2, "major": 3}


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return dt.astimezone(timezone.utc)


def validate_incident(item: dict) -> dict:
    required = {"incident_id", "line", "kind", "severity", "reported_at", "expected_clear_at"}
    missing = sorted(required - item.keys())
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    if not str(item["incident_id"]).strip():
        raise ValueError("incident_id cannot be empty")
    if item["kind"] not in ALLOWED_TYPES:
        raise ValueError(f"unsupported kind: {item['kind']}")
    if item["severity"] not in SEVERITIES:
        raise ValueError(f"unsupported severity: {item['severity']}")

    reported = _parse_ts(item["reported_at"])
    clear = _parse_ts(item["expected_clear_at"])
    if clear < reported:
        raise ValueError("expected_clear_at cannot be before reported_at")

    normalized = dict(item)
    normalized["reported_at"] = reported.isoformat()
    normalized["expected_clear_at"] = clear.isoformat()
    return normalized


def normalize_incidents(items: Iterable[dict]) -> list[dict]:
    """Validate and deduplicate by incident_id.

    The first occurrence wins so repeated webhook/feed delivery is idempotent.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for raw in items:
        item = validate_incident(raw)
        incident_id = item["incident_id"]
        if incident_id in seen:
            continue
        seen.add(incident_id)
        out.append(item)
    return out


def active_incidents(items: Iterable[dict], as_of: str) -> list[dict]:
    now = _parse_ts(as_of)
    active: list[dict] = []
    for item in normalize_incidents(items):
        reported = _parse_ts(item["reported_at"])
        clear = _parse_ts(item["expected_clear_at"])
        if reported <= now <= clear:
            active.append(item)
    return active


def incident_impact(item: dict) -> dict:
    """Map incident severity to explicit, reviewable scenario assumptions."""
    normalized = validate_incident(item)
    level = SEVERITIES[normalized["severity"]]
    capacity_loss = {1: 0.05, 2: 0.12, 3: 0.25}[level]
    extra_delay = {1: 2.0, 2: 6.0, 3: 14.0}[level]
    risk_add = {1: 0.05, 2: 0.12, 3: 0.24}[level]
    return {
        "incident_id": normalized["incident_id"],
        "line": normalized["line"],
        "severity": normalized["severity"],
        "capacity_loss": capacity_loss,
        "extra_delay_min": extra_delay,
        "delay_risk_add": risk_add,
    }
