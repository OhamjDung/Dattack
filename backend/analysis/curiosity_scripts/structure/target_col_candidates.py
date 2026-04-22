from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    profile = ctx.profile
    numeric_cols = ctx.numeric_cols
    id_cols = set(ctx.id_cols)

    outcome_keywords = {"revenue", "sales", "profit", "churn", "conversion", "score",
                        "rate", "count", "amount", "value", "price", "spend", "cost",
                        "return", "mrr", "arr", "ltv", "orders", "units"}

    candidates = []
    for col in numeric_cols:
        if col in id_cols:
            continue
        col_lower = col.lower().replace("_", " ")
        keyword_match = any(kw in col_lower for kw in outcome_keywords)
        stats = profile.get(col, {})
        cv = stats.get("cv", 0) or 0
        null_rate = stats.get("null_rate", 0) or 0
        score = (1.5 if keyword_match else 0) + (min(cv, 3) / 3) - null_rate
        candidates.append((col, score, keyword_match))

    candidates.sort(key=lambda x: -x[1])
    top = candidates[:3]

    question_candidates = []
    if top:
        names = ", ".join(f"'{c[0]}'" for c in top)
        question_candidates.append({
            "label": "Which column are you trying to analyze or predict?",
            "description": f"Likely target columns based on name and variability: {names}. Knowing the target focuses all downstream analysis.",
            "confidence": 0.9,
        })

    technique_candidates = []
    if len(top) >= 2:
        technique_candidates.append({
            "label": "Feature importance analysis",
            "description": f"With a target column identified, we can rank which other columns most predict '{top[0][0]}'.",
            "confidence": 0.75,
        })

    return {
        "script": "target_col_candidates",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"candidates": [{"col": c[0], "score": round(c[1], 2), "keyword_match": c[2]} for c in top]},
    }
