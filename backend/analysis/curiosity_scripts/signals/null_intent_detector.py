from __future__ import annotations
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return ctx.df.isna().any().any()


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    question_candidates = []
    technique_candidates = []
    flagged = []

    for col in df.columns:
        null_rate = df[col].isna().mean()
        if null_rate < 0.01:
            continue

        # Check if nulls cluster in specific rows (systematic) vs random
        null_mask = df[col].isna()
        other_numeric = [c for c in ctx.numeric_cols if c != col]

        systematic = False
        if other_numeric:
            ref = df[other_numeric[0]].notna()
            # Nulls perfectly aligned with another column's nulls = systematic
            overlap = (null_mask & ref.isna()).sum()
            if overlap > null_mask.sum() * 0.7:
                systematic = True

        pattern = "systematic (conditional on other fields)" if systematic else "distributed (possibly random or MCAR)"
        flagged.append({"col": col, "null_rate": round(null_rate, 3), "pattern": pattern})

        if null_rate > 0.1:
            question_candidates.append({
                "label": f"Why is '{col}' missing for {null_rate:.0%} of rows?",
                "description": f"Null pattern appears {pattern}. Treatment (impute, exclude, or flag) will significantly affect results.",
                "confidence": 0.85,
            })

    if flagged:
        technique_candidates.append({
            "label": "Missing value pattern analysis",
            "description": "Structured null patterns often encode business logic — co-missing analysis will reveal which fields go missing together.",
            "confidence": 0.8,
        })

    return {
        "script": "null_intent_detector",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"flagged_cols": flagged},
    }
