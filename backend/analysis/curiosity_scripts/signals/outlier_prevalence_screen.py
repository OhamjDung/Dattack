from __future__ import annotations
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    question_candidates = []
    technique_candidates = []
    screened = []

    for col in ctx.numeric_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        mean, std = series.mean(), series.std()
        if std == 0:
            continue
        z = np.abs((series - mean) / std)
        extreme_pct = (z > 3).mean()
        screened.append({"col": col, "extreme_pct": round(float(extreme_pct), 3)})

        if extreme_pct > 0.02:
            question_candidates.append({
                "label": f"Are extreme values in '{col}' real or errors?",
                "description": f"{extreme_pct:.1%} of '{col}' values are >3σ from the mean. These could be genuine outliers (VIP customers, error codes) or data quality issues.",
                "confidence": 0.85,
            })

    high_outlier_cols = [s["col"] for s in screened if s["extreme_pct"] > 0.02]
    if high_outlier_cols:
        technique_candidates.append({
            "label": "Outlier investigation",
            "description": f"Columns {high_outlier_cols} have notable extreme values — IQR + z-score analysis will characterize them.",
            "confidence": 0.8,
        })

    return {
        "script": "outlier_prevalence_screen",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"screened": screened},
    }
