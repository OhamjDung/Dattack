from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0 or len(ctx.id_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    n_rows = len(df)
    candidates = []

    join_keywords = {"id", "code", "key", "ref", "num", "no", "number", "sku", "uuid"}

    for col in list(ctx.id_cols) + ctx.categorical_cols:
        col_lower = col.lower().replace("_", " ")
        is_keyword = any(kw in col_lower for kw in join_keywords)
        nunique = df[col].nunique()
        ratio = nunique / n_rows

        if is_keyword and 0.01 < ratio < 0.95:
            candidates.append({"col": col, "unique_count": nunique, "unique_ratio": round(ratio, 3)})

    question_candidates = []
    if candidates:
        col_names = ", ".join(f"'{c['col']}'" for c in candidates[:3])
        question_candidates.append({
            "label": "Do you have related tables to join?",
            "description": f"Columns {col_names} look like foreign keys — joining additional datasets could unlock richer analysis.",
            "confidence": 0.65,
        })

    return {
        "script": "join_key_candidates",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": [],
        "data": {"candidates": candidates[:5]},
    }
