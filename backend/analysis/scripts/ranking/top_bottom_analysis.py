from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["percentile_ranking", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 1


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    comparisons: list[dict] = {}

    for col in ctx.numeric_cols[:3]:
        s = df[col].dropna()
        if len(s) < 10:
            continue
        p90 = float(s.quantile(0.90))
        p10 = float(s.quantile(0.10))
        top_mask = df[col] >= p90
        bot_mask = df[col] <= p10

        profile: dict[str, dict] = {}
        for other_col in ctx.numeric_cols:
            if other_col == col:
                continue
            top_mean = float(df.loc[top_mask, other_col].mean()) if top_mask.any() else None
            bot_mean = float(df.loc[bot_mask, other_col].mean()) if bot_mask.any() else None
            if top_mean is not None and bot_mean is not None and bot_mean != 0:
                ratio = top_mean / bot_mean
                profile[other_col] = {
                    "top_mean": round(top_mean, 4),
                    "bottom_mean": round(bot_mean, 4),
                    "ratio": round(ratio, 3),
                }
                if abs(ratio - 1) > 0.3:
                    direction = "higher" if ratio > 1 else "lower"
                    findings.append(
                        f"Top 10% by '{col}' have {direction} '{other_col}' "
                        f"({top_mean:.2f} vs {bot_mean:.2f}, ratio={ratio:.2f}x)."
                    )

        comparisons[col] = profile

    if not findings:
        findings.append("Top and bottom deciles show similar profiles across other numeric columns.")

    return {
        "script": "top_bottom_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"top_bottom_profiles": comparisons},
        "error": None,
    }
