from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    distributions: dict[str, dict] = {}

    for col in ctx.numeric_cols:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        skew = float(s.skew())
        kurt = float(s.kurtosis())
        shape = "symmetric"
        if skew > 1:
            shape = "right-skewed"
        elif skew < -1:
            shape = "left-skewed"

        distributions[col] = {
            "skewness": round(skew, 3),
            "kurtosis": round(kurt, 3),
            "shape": shape,
            "iqr": float(s.quantile(0.75) - s.quantile(0.25)),
        }

        if abs(skew) > 1.5:
            findings.append(f"'{col}' is strongly {shape} (skew={skew:.2f}) — log transform may help.")

    if not findings:
        findings.append("All numeric columns have approximately symmetric distributions.")

    return {
        "script": "distribution_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"distributions": distributions},
        "error": None,
    }
