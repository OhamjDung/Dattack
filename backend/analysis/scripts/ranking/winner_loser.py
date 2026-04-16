from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["growth_rate_analysis"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]
    findings: list[str] = []

    growth = ctx.results.get("growth_rate_analysis", {}).get("data", {}).get("growth", {})
    if not growth:
        return {"script": "winner_loser", "status": "skipped",
                "findings": ["No growth data available."], "data": {}, "error": None}

    ranked = sorted(growth.items(), key=lambda x: x[1].get("total_pct_change", 0), reverse=True)
    winners = [(c, v) for c, v in ranked if v.get("total_pct_change", 0) > 0]
    losers = [(c, v) for c, v in ranked if v.get("total_pct_change", 0) < 0]

    for col, stats in winners[:2]:
        findings.append(f"WINNER: '{col}' grew {stats['total_pct_change']:.1f}% over the period.")
    for col, stats in losers[-2:]:
        findings.append(f"LOSER: '{col}' declined {abs(stats['total_pct_change']):.1f}% over the period.")

    if not findings:
        findings.append("No clear winners or losers — all columns showed minimal change.")

    return {
        "script": "winner_loser",
        "status": "ok",
        "findings": findings,
        "data": {"ranked": [{"col": c, **v} for c, v in ranked]},
        "error": None,
    }
