from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    ranks: dict[str, dict] = {}

    for col in ctx.numeric_cols[:6]:
        s = df[col].dropna()
        pct = s.rank(pct=True)
        top10_threshold = float(s.quantile(0.90))
        bottom10_threshold = float(s.quantile(0.10))
        ranks[col] = {
            "p90_threshold": round(top10_threshold, 4),
            "p10_threshold": round(bottom10_threshold, 4),
            "top_10pct_count": int((s >= top10_threshold).sum()),
            "bottom_10pct_count": int((s <= bottom10_threshold).sum()),
        }

    findings.append(
        f"Percentile ranks computed for {len(ranks)} numeric columns. "
        f"Top/bottom 10% thresholds stored for downstream analysis."
    )

    return {
        "script": "percentile_ranking",
        "status": "ok",
        "findings": findings,
        "data": {"ranks": ranks},
        "error": None,
    }
