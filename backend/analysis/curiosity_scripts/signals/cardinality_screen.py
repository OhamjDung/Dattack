from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    n_rows = len(df)
    question_candidates = []
    technique_candidates = []
    results = []

    for col in ctx.categorical_cols:
        nunique = df[col].nunique()
        ratio = nunique / n_rows
        if ratio > 0.8:
            label = "near-unique (likely an ID)"
            question_candidates.append({
                "label": f"Is '{col}' actually a category or an identifier?",
                "description": f"'{col}' has {nunique:,} unique values ({ratio:.0%} of rows) — it behaves like an ID, not a useful segment. Should it be excluded from categorical analysis?",
                "confidence": 0.85,
            })
        elif nunique == 1:
            label = "constant (no variation)"
        elif nunique <= 10:
            label = "low cardinality (good for segmentation)"
            technique_candidates.append({
                "label": f"Segment by '{col}'",
                "description": f"'{col}' has only {nunique} values — ideal for comparing metrics across groups.",
                "confidence": 0.8,
            })
        else:
            label = "medium cardinality"

        results.append({"col": col, "unique_count": nunique, "unique_ratio": round(ratio, 3), "label": label})

    return {
        "script": "cardinality_screen",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"cardinality": results},
    }
