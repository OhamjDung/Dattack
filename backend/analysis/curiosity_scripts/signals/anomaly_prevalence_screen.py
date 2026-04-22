from __future__ import annotations
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    question_candidates = []
    technique_candidates = []

    cols = ctx.numeric_cols[:8]
    subset = df[cols].dropna()
    if len(subset) < 20:
        return {"script": "anomaly_prevalence_screen", "status": "skipped",
                "question_candidates": [], "technique_candidates": [], "data": {}}

    # Z-score based multi-dimensional screen
    z_scores = np.abs((subset - subset.mean()) / (subset.std() + 1e-9))
    row_max_z = z_scores.max(axis=1)
    anomaly_rate = float((row_max_z > 3).mean())

    if anomaly_rate > 0.03:
        question_candidates.append({
            "label": "Are you interested in finding unusual records?",
            "description": f"Roughly {anomaly_rate:.1%} of rows have at least one metric >3σ from normal — anomaly detection could surface these for review.",
            "confidence": 0.8,
        })
        technique_candidates.append({
            "label": "Multi-dimensional anomaly scoring",
            "description": "Isolation Forest across all numeric columns will assign each row an anomaly score — useful for fraud, errors, or VIP detection.",
            "confidence": 0.75,
        })

    return {
        "script": "anomaly_prevalence_screen",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"anomaly_rate": round(anomaly_rate, 4), "cols_used": cols},
    }
