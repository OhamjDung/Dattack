from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = [
    "schema_detector", "field_profile",
    "entity_type_guesser", "target_col_candidates",
    "column_role_classifier", "correlation_opportunity",
    "concentration_screen", "temporal_coverage_analyzer",
    "segment_variable_candidates",
]


def is_applicable(ctx: AnalysisContext) -> bool:
    return True


def run(ctx: AnalysisContext) -> dict:
    results = ctx.results
    technique_candidates = []

    has_datetime = len(ctx.datetime_cols) > 0
    has_numeric = len(ctx.numeric_cols) > 0
    has_categorical = len(ctx.categorical_cols) > 0
    has_id = len(ctx.id_cols) > 0

    # Gather signals from prior curiosity scripts
    concentration = results.get("concentration_screen", {}).get("data", {}).get("screened", [])
    top_concentration = next((s for s in concentration if s["gini"] > 0.4), None)

    growth = results.get("growth_signal_screen", {}).get("data", {}).get("growth_signals", [])
    top_growth = growth[0] if growth and abs(growth[0].get("pct_change", 0)) > 0.15 else None

    correlations = results.get("correlation_opportunity", {}).get("data", {}).get("top_pairs", [])
    top_corr = correlations[0] if correlations else None

    segments = results.get("segment_variable_candidates", {}).get("data", {}).get("strong_segments", [])
    top_segment = segments[0] if segments else None

    anomaly_rate = results.get("anomaly_prevalence_screen", {}).get("data", {}).get("anomaly_rate", 0)

    # Build ranked technique candidates
    if top_concentration:
        technique_candidates.append({
            "label": "Pareto concentration deep-dive",
            "description": f"High Gini ({top_concentration['gini']:.2f}) on '{top_concentration['col']}' — run full Pareto + HHI concentration analysis.",
            "confidence": 0.92,
        })

    if top_growth:
        direction = "growth" if top_growth["pct_change"] > 0 else "decline"
        technique_candidates.append({
            "label": f"Time series {direction} analysis",
            "description": f"Strong {direction} signal in '{top_growth['col']}' — decompose trend, seasonality, and changepoints.",
            "confidence": 0.9,
        })

    if top_corr:
        technique_candidates.append({
            "label": "Regression & causality analysis",
            "description": f"Strong correlation between '{top_corr['col_a']}' and '{top_corr['col_b']}' (r={top_corr['r']}) — run regression and partial correlation to assess causality.",
            "confidence": 0.88,
        })

    if top_segment:
        technique_candidates.append({
            "label": "Statistical segment comparison",
            "description": f"'{top_segment['segment_col']}' segments show large variance in '{top_segment['metric_col']}' — ANOVA + effect size will quantify significance.",
            "confidence": 0.87,
        })

    if has_id and has_datetime:
        technique_candidates.append({
            "label": "Cohort & retention analysis",
            "description": "Entity ID + date column enable cohort grouping — track how different cohorts behave over time.",
            "confidence": 0.82,
        })

    if anomaly_rate > 0.03:
        technique_candidates.append({
            "label": "Anomaly detection sweep",
            "description": f"~{anomaly_rate:.1%} anomalous rows detected — Isolation Forest will score every row and surface the most unusual records.",
            "confidence": 0.8,
        })

    return {
        "script": "analysis_hypothesis_builder",
        "status": "ok",
        "question_candidates": [],
        "technique_candidates": technique_candidates,
        "data": {"hypotheses_generated": len(technique_candidates)},
    }
