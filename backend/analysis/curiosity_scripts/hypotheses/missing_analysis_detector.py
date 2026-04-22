from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = [
    "schema_detector", "field_profile", "column_role_classifier",
    "entity_type_guesser", "target_col_candidates",
]


def is_applicable(ctx: AnalysisContext) -> bool:
    return True


def run(ctx: AnalysisContext) -> dict:
    results = ctx.results
    question_candidates = []

    # What target column is unknown?
    target_data = results.get("target_col_candidates", {}).get("data", {}).get("candidates", [])
    if len(target_data) > 1:
        names = [c["col"] for c in target_data[:3]]
        question_candidates.append({
            "label": "Which metric should we optimize or predict?",
            "description": f"Multiple outcome candidates found: {names}. Picking the primary target focuses the analysis and prevents scattered findings.",
            "confidence": 0.9,
        })

    # Is there a benchmark or comparison period?
    has_datetime = len(ctx.datetime_cols) > 0
    if has_datetime:
        question_candidates.append({
            "label": "Is there a target period or baseline to compare against?",
            "description": "Time series analysis is more actionable with a defined baseline (e.g., 'compare Q1 vs Q2' or 'before vs after campaign launch').",
            "confidence": 0.75,
        })

    # Are there external data sources?
    question_candidates.append({
        "label": "Is there external context we should factor in?",
        "description": "External events (market shifts, campaigns, policy changes) often explain anomalies or trend breaks. Knowing them prevents false conclusions.",
        "confidence": 0.65,
    })

    return {
        "script": "missing_analysis_detector",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": [],
        "data": {},
    }
