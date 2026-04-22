from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return True


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    n_rows, n_cols = df.shape
    ratio = n_cols / max(n_rows, 1)

    question_candidates = []
    technique_candidates = []

    if ratio > 0.5:
        shape = "wide"
        question_candidates.append({
            "label": "Is this pre-aggregated summary data?",
            "description": f"Dataset has {n_rows} rows and {n_cols} columns (wide). This often means one row per entity with many attributes — confirm it's not a pivot/aggregate table.",
            "confidence": 0.75,
        })
        technique_candidates.append({
            "label": "Multicollinearity check",
            "description": "Wide datasets often have redundant columns — multicollinearity detection will flag near-duplicates.",
            "confidence": 0.7,
        })
    else:
        shape = "long"
        technique_candidates.append({
            "label": "Aggregation & grouping analysis",
            "description": f"Tall dataset ({n_rows:,} rows, {n_cols} cols) — aggregating by key dimensions will surface patterns.",
            "confidence": 0.8,
        })

    return {
        "script": "dataset_shape_classifier",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"shape": shape, "n_rows": n_rows, "n_cols": n_cols, "col_row_ratio": round(ratio, 3)},
    }
