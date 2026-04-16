from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "distribution_analysis"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    results: dict[str, dict] = {}

    for col in ctx.numeric_cols:
        s = df[col].dropna()
        if len(s) < 8:
            continue
        sample = s if len(s) <= 5000 else s.sample(5000, random_state=42)
        try:
            stat, p = stats.normaltest(sample)
            is_normal = p > 0.05
            results[col] = {
                "test": "D'Agostino-Pearson",
                "statistic": round(float(stat), 4),
                "p_value": round(float(p), 6),
                "is_normal": is_normal,
            }
            if not is_normal and p < 0.001:
                findings.append(f"'{col}' is significantly non-normal (p={p:.4f}) — use non-parametric tests.")
        except Exception:
            pass

    normal_cols = [c for c, v in results.items() if v.get("is_normal")]
    if normal_cols:
        findings.append(f"Columns that pass normality: {', '.join(normal_cols)}.")
    if not findings:
        findings.append("Most columns deviate from normality — non-parametric methods recommended.")

    return {
        "script": "normality_tests",
        "status": "ok",
        "findings": findings,
        "data": {"normality": results},
        "error": None,
    }
