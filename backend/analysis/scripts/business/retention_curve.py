from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["cohort_analysis"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    cohorts = ctx.results.get("cohort_analysis", {}).get("data", {}).get("cohorts", [])
    if len(cohorts) < 3:
        return {"script": "retention_curve", "status": "skipped",
                "findings": ["Not enough cohorts for retention curve."], "data": {}, "error": None}

    findings: list[str] = []
    counts = [c["count"] for c in cohorts]
    max_count = max(counts)
    retention = [round(c / max_count, 4) for c in counts]

    drop_first = 1 - retention[1] if len(retention) > 1 else 0
    drop_total = 1 - retention[-1]

    findings.append(
        f"Retention from first to second period: {retention[1]:.1%}."
    )
    findings.append(
        f"Overall retention to final period: {retention[-1]:.1%} "
        f"({drop_total:.1%} total drop-off)."
    )

    return {
        "script": "retention_curve",
        "status": "ok",
        "findings": findings,
        "data": {
            "cohort_labels": [c["cohort"] for c in cohorts],
            "retention_rates": retention,
        },
        "error": None,
    }
