from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.df.columns) > 0


def run(ctx: AnalysisContext) -> dict:
    schema = ctx.schema
    roles: dict[str, str] = {}

    for col_name, col in schema.items():
        t = col.inferred_type
        if t == "id_col":
            roles[col_name] = "identifier"
        elif t == "datetime":
            roles[col_name] = "time axis"
        elif t == "numeric":
            roles[col_name] = "metric"
        elif t == "categorical":
            roles[col_name] = "dimension"
        elif t == "text":
            roles[col_name] = "free text"
        else:
            roles[col_name] = "unknown"

    unknown = [c for c, r in roles.items() if r == "unknown"]
    metrics = [c for c, r in roles.items() if r == "metric"]
    dims = [c for c, r in roles.items() if r == "dimension"]

    question_candidates = []
    technique_candidates = []

    if unknown:
        question_candidates.append({
            "label": f"What is the role of {unknown[0]!r}?",
            "description": f"Column(s) {unknown} could not be automatically classified. Knowing their purpose helps select the right analyses.",
            "confidence": 0.8,
        })

    if metrics and dims:
        technique_candidates.append({
            "label": "Segment analysis",
            "description": f"Found {len(metrics)} metric(s) and {len(dims)} dimension(s) — comparing metrics across segments is a natural fit.",
            "confidence": 0.85,
        })

    return {
        "script": "column_role_classifier",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"roles": roles},
    }
