from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    tiers: dict[str, dict] = {}

    for col in ctx.numeric_cols[:4]:
        s = df[col].dropna()
        if len(s) < 6:
            continue
        low_thresh = float(s.quantile(0.33))
        high_thresh = float(s.quantile(0.67))
        low_count = int((s < low_thresh).sum())
        mid_count = int(((s >= low_thresh) & (s < high_thresh)).sum())
        high_count = int((s >= high_thresh).sum())
        n = len(s)
        tiers[col] = {
            "low_threshold": round(low_thresh, 4),
            "high_threshold": round(high_thresh, 4),
            "low_count": low_count, "low_pct": round(low_count / n, 3),
            "mid_count": mid_count, "mid_pct": round(mid_count / n, 3),
            "high_count": high_count, "high_pct": round(high_count / n, 3),
        }

    if tiers:
        findings.append(f"Tier segmentation (Low/Mid/High) computed for {len(tiers)} numeric columns.")

    return {
        "script": "tier_segmentation",
        "status": "ok",
        "findings": findings,
        "data": {"tiers": tiers},
        "error": None,
    }
