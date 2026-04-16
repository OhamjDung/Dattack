from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["segment_comparison", "correlation_matrix"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0 and len(ctx.numeric_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    interactions: list[dict] = []

    seg_col = ctx.results.get("segment_comparison", {}).get("data", {}).get("segment_col")
    if not seg_col:
        return {"script": "interaction_effects", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    top_pairs = ctx.results.get("correlation_matrix", {}).get("data", {}).get("top_pairs", [])
    for pair in top_pairs[:4]:
        a, b = pair["col_a"], pair["col_b"]
        group_corrs: dict[str, float] = {}
        for grp, sub in df.groupby(seg_col):
            sub_clean = sub[[a, b]].dropna()
            if len(sub_clean) < 5:
                continue
            r = float(sub_clean[a].corr(sub_clean[b]))
            group_corrs[str(grp)] = round(r, 3)

        if not group_corrs:
            continue
        values = list(group_corrs.values())
        spread = max(values) - min(values)
        interactions.append({
            "col_a": a, "col_b": b, "segment_col": seg_col,
            "group_correlations": group_corrs, "spread": round(spread, 3),
        })
        if spread > 0.3:
            findings.append(
                f"The '{a}'↔'{b}' correlation differs across '{seg_col}' groups "
                f"(spread={spread:.2f}) — interaction effect present."
            )

    if not findings:
        findings.append("No notable interaction effects found between numeric pairs across segments.")

    return {
        "script": "interaction_effects",
        "status": "ok",
        "findings": findings,
        "data": {"interactions": interactions},
        "error": None,
    }
