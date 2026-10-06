"""Generate a reproducible incident-aware rail operations briefing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.briefing import apply_incident_impacts, briefing_markdown
from src.synthetic_kpis import generate_ops_panel


def load_jsonl(path: str) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON") from exc
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--incidents", default="sample/incidents.jsonl")
    parser.add_argument("--as-of", default="2026-09-14T08:30:00+08:00")
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="briefing.md")
    args = parser.parse_args()

    panel = generate_ops_panel(n_days=args.days, seed=args.seed)
    incidents = load_jsonl(args.incidents)
    scenario = apply_incident_impacts(panel, incidents, as_of=args.as_of)
    report = briefing_markdown(scenario)
    Path(args.out).write_text(report, encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
