from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "categorical_frequency"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    n = len(df)
    findings: list[str] = []
    cardinality: dict[str, dict] = {}

    for col in ctx.categorical_cols:
        unique = int(df[col].nunique())
        ratio = unique / max(n, 1)
        label = "binary" if unique == 2 else \
                "low" if unique <= 10 else \
                "medium" if unique <= 50 else \
                "high" if ratio < 0.5 else \
                "near-unique"
        cardinality[col] = {"unique_count": unique, "cardinality_ratio": round(ratio, 4), "label": label}
        if label == "near-unique":
            findings.append(f"'{col}' is near-unique ({unique} values) — likely an ID, not a feature.")
        elif label == "high":
            findings.append(f"'{col}' has high cardinality ({unique} values) — one-hot encoding will be expensive.")

    if not findings:
        findings.append("All categorical columns have manageable cardinality for analysis.")

    return {
        "script": "cardinality_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"cardinality": cardinality},
        "error": None,
    }
