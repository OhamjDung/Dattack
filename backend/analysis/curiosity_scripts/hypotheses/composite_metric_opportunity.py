from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile", "correlation_opportunity"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 3


def run(ctx: AnalysisContext) -> dict:
    results = ctx.results
    technique_candidates = []

    # Look for groups of moderately correlated numerics — good composite candidates
    corr_data = results.get("correlation_opportunity", {}).get("data", {}).get("top_pairs", [])
    moderate_pairs = [p for p in corr_data if 0.3 < abs(p["r"]) < 0.85]

    if moderate_pairs and len(ctx.numeric_cols) >= 4:
        cols_involved = list({p["col_a"] for p in moderate_pairs} | {p["col_b"] for p in moderate_pairs})[:4]
        technique_candidates.append({
            "label": "Composite score index",
            "description": f"Columns {cols_involved} are moderately correlated — combining them into a weighted z-score composite captures a latent construct (e.g., 'performance score', 'health index').",
            "confidence": 0.75,
        })

    return {
        "script": "composite_metric_opportunity",
        "status": "ok",
        "question_candidates": [],
        "technique_candidates": technique_candidates,
        "data": {"moderate_pairs_count": len(moderate_pairs)},
    }
