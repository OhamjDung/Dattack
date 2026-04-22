from __future__ import annotations
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def _gini(values) -> float:
    arr = np.sort(np.abs(values))
    n = len(arr)
    if n == 0 or arr.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * (idx * arr).sum() / (n * arr.sum())) - (n + 1) / n)


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    technique_candidates = []
    screened = []

    for col in ctx.numeric_cols[:5]:
        series = df[col].dropna()
        if len(series) < 10 or (series < 0).any():
            continue
        g = _gini(series.values)
        screened.append({"col": col, "gini": round(g, 3)})

    screened.sort(key=lambda x: -x["gini"])
    high = [s for s in screened if s["gini"] > 0.4]

    if high:
        col = high[0]["col"]
        g = high[0]["gini"]
        technique_candidates.append({
            "label": f"Pareto / concentration analysis on '{col}'",
            "description": f"'{col}' has a Gini coefficient of {g:.2f} (high concentration) — likely a 80/20 pattern where a few entities drive most of the value.",
            "confidence": 0.88,
        })

    return {
        "script": "concentration_screen",
        "status": "ok",
        "question_candidates": [],
        "technique_candidates": technique_candidates,
        "data": {"screened": screened},
    }
