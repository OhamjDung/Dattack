from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.id_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    n_rows = len(df)
    results = []
    question_candidates = []

    for col in ctx.id_cols:
        nunique = df[col].nunique()
        ratio = nunique / n_rows
        if ratio == 1.0:
            verdict = "true unique ID"
        elif ratio > 0.95:
            verdict = "near-unique (possible transaction ID with occasional repeats)"
            question_candidates.append({
                "label": f"Does '{col}' ever repeat intentionally?",
                "description": f"'{col}' is 99%+ unique but not perfectly. Repeated values could indicate corrections, cancellations, or data errors.",
                "confidence": 0.75,
            })
        else:
            verdict = "overloaded key (entities appear multiple times)"
            question_candidates.append({
                "label": f"Is '{col}' a customer ID or transaction ID?",
                "description": f"'{col}' has {nunique:,} unique values across {n_rows:,} rows — the same entity appears ~{n_rows // nunique}x on average.",
                "confidence": 0.85,
            })
        results.append({"col": col, "unique_count": nunique, "unique_ratio": round(ratio, 3), "verdict": verdict})

    return {
        "script": "id_column_validator",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": [],
        "data": {"id_analysis": results},
    }
