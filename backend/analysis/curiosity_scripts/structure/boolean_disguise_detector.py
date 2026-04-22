from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0 or len(ctx.categorical_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    disguised = []

    for col in ctx.numeric_cols:
        vals = df[col].dropna().unique()
        if set(vals).issubset({0, 1, 0.0, 1.0}):
            disguised.append({"col": col, "as": "numeric 0/1"})

    bool_strings = {
        frozenset({"yes", "no"}), frozenset({"y", "n"}),
        frozenset({"true", "false"}), frozenset({"1", "0"}),
        frozenset({"active", "inactive"}), frozenset({"pass", "fail"}),
    }
    for col in ctx.categorical_cols:
        vals = set(str(v).lower().strip() for v in df[col].dropna().unique())
        if vals in bool_strings:
            disguised.append({"col": col, "as": f"string {vals}"})

    technique_candidates = []
    if disguised:
        col_names = ", ".join(f"'{d['col']}'" for d in disguised)
        technique_candidates.append({
            "label": "Binary segment comparison",
            "description": f"Columns {col_names} are binary flags — comparing all metrics across their two groups will reveal meaningful differences.",
            "confidence": 0.85,
        })

    return {
        "script": "boolean_disguise_detector",
        "status": "ok",
        "question_candidates": [],
        "technique_candidates": technique_candidates,
        "data": {"disguised_boolean_cols": disguised},
    }
