from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "cardinality_screen"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    question_candidates = []
    technique_candidates = []

    control_keywords = {"control", "baseline", "benchmark", "reference", "standard",
                        "default", "organic", "untreated", "before", "pre"}

    for col in ctx.categorical_cols:
        vals = [str(v).lower() for v in df[col].dropna().unique()]
        matches = [v for v in vals if any(kw in v for kw in control_keywords)]
        if matches:
            question_candidates.append({
                "label": f"Is '{col}' a treatment/control split?",
                "description": f"Values like {matches[:2]} in '{col}' suggest an experimental or before/after structure — A/B or pre/post analysis would be appropriate.",
                "confidence": 0.85,
            })
            technique_candidates.append({
                "label": "A/B or pre/post comparison",
                "description": f"Segment by '{col}' to compare outcome metrics between groups — statistical significance testing (t-test, Mann-Whitney) will validate differences.",
                "confidence": 0.85,
            })
            break

    if not question_candidates:
        # Check for natural benchmark (e.g., industry avg column, target column)
        target_keywords = {"target", "goal", "budget", "plan", "forecast", "expected"}
        for col in ctx.numeric_cols:
            if any(kw in col.lower() for kw in target_keywords):
                technique_candidates.append({
                    "label": f"Actuals vs target analysis on '{col}'",
                    "description": f"'{col}' looks like a benchmark or target — comparing actuals against it will reveal over/under-performance.",
                    "confidence": 0.8,
                })
                break

    return {
        "script": "benchmark_opportunity_detector",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {},
    }
