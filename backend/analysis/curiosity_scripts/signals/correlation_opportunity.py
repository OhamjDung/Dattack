from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    numeric = ctx.numeric_cols
    technique_candidates = []
    top_pairs = []

    subset = df[numeric].dropna()
    if len(subset) < 5:
        return {"script": "correlation_opportunity", "status": "skipped",
                "question_candidates": [], "technique_candidates": [], "data": {}}

    corr = subset.corr(method="pearson")
    seen = set()
    for col_a in numeric:
        for col_b in numeric:
            if col_a >= col_b or (col_a, col_b) in seen:
                continue
            seen.add((col_a, col_b))
            r = corr.loc[col_a, col_b] if col_a in corr.index and col_b in corr.columns else 0
            if abs(r) > 0.5:
                top_pairs.append({"col_a": col_a, "col_b": col_b, "r": round(float(r), 3)})

    top_pairs.sort(key=lambda x: -abs(x["r"]))
    top_pairs = top_pairs[:5]

    if top_pairs:
        best = top_pairs[0]
        direction = "positive" if best["r"] > 0 else "negative"
        technique_candidates.append({
            "label": f"Correlation deep-dive: {best['col_a']} vs {best['col_b']}",
            "description": f"Strong {direction} correlation (r={best['r']}) detected. Regression analysis will quantify the relationship and identify confounders.",
            "confidence": 0.9,
        })

    if len(top_pairs) >= 3:
        technique_candidates.append({
            "label": "Full correlation matrix",
            "description": f"Found {len(top_pairs)} strong pairs — a correlation heatmap will reveal the full dependency structure.",
            "confidence": 0.85,
        })

    return {
        "script": "correlation_opportunity",
        "status": "ok",
        "question_candidates": [],
        "technique_candidates": technique_candidates,
        "data": {"top_pairs": top_pairs},
    }
