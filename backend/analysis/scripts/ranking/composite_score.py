from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["percentile_ranking", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    cols = ctx.numeric_cols[:6]
    sub = df[cols].dropna()
    if len(sub) < 4:
        return {"script": "composite_score", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    # Z-score each column then average
    z_scores = (sub - sub.mean()) / sub.std().replace(0, 1)
    composite = z_scores.mean(axis=1)

    top_pct = float(composite.quantile(0.90))
    bot_pct = float(composite.quantile(0.10))
    top_count = int((composite >= top_pct).sum())

    findings.append(
        f"Composite score built from {len(cols)} numeric features. "
        f"Top 10% threshold = {top_pct:.2f} ({top_count} rows). "
        f"Score spread: {composite.min():.2f} to {composite.max():.2f}."
    )

    return {
        "script": "composite_score",
        "status": "ok",
        "findings": findings,
        "data": {
            "columns_used": cols,
            "p90_threshold": round(top_pct, 4),
            "p10_threshold": round(bot_pct, 4),
            "top_10pct_count": top_count,
            "score_range": [round(float(composite.min()), 4), round(float(composite.max()), 4)],
        },
        "error": None,
    }
