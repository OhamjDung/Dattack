from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    technique_candidates = []
    question_candidates = []
    strong_segments = []

    metric_col = ctx.numeric_cols[0]
    metric_series = df[metric_col].dropna()
    overall_std = metric_series.std()
    if overall_std == 0:
        return {"script": "segment_variable_candidates", "status": "skipped",
                "question_candidates": [], "technique_candidates": [], "data": {}}

    for cat_col in ctx.categorical_cols[:5]:
        n_unique = df[cat_col].nunique()
        if n_unique < 2 or n_unique > 20:
            continue

        group_means = df.groupby(cat_col)[metric_col].mean()
        spread = (group_means.max() - group_means.min()) / (metric_series.mean() or 1)

        if spread > 0.2:
            strong_segments.append({
                "segment_col": cat_col,
                "metric_col": metric_col,
                "n_groups": n_unique,
                "relative_spread": round(float(spread), 3),
            })

    if strong_segments:
        best = strong_segments[0]
        technique_candidates.append({
            "label": f"Segment analysis by '{best['segment_col']}'",
            "description": f"'{best['segment_col']}' groups show {best['relative_spread']:.0%} spread in '{best['metric_col']}' — a strong segmentation variable.",
            "confidence": 0.88,
        })

    if len(ctx.categorical_cols) > 5:
        question_candidates.append({
            "label": "Which dimensions matter most for your analysis?",
            "description": f"Found {len(ctx.categorical_cols)} categorical columns. Knowing which segments are business-relevant focuses the analysis.",
            "confidence": 0.7,
        })

    return {
        "script": "segment_variable_candidates",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"strong_segments": strong_segments},
    }
