from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["field_profile", "percentile_ranking"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    benchmarks: dict[str, dict] = {}

    id_col = ctx.id_cols[0] if ctx.id_cols else None
    cat_col = next((c for c in ctx.categorical_cols if df[c].nunique() < 100), None)

    for col in ctx.numeric_cols[:3]:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        mean = float(s.mean())
        std = float(s.std())
        z_scores = (s - mean) / std if std > 0 else pd.Series([0.0] * len(s))
        outlier_high = df[z_scores > 2]
        outlier_low = df[z_scores < -2]
        benchmarks[col] = {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "above_2std_count": int(len(outlier_high)),
            "below_2std_count": int(len(outlier_low)),
        }
        if len(outlier_high) > 0:
            findings.append(
                f"'{col}': {len(outlier_high)} rows are >2σ above mean ({mean:.2f}) — notable high performers."
            )
        if len(outlier_low) > 0:
            findings.append(
                f"'{col}': {len(outlier_low)} rows are >2σ below mean — notable underperformers."
            )

    if not findings:
        findings.append("All entities perform within 2 standard deviations of the mean.")

    return {
        "script": "benchmark_comparison",
        "status": "ok",
        "findings": findings,
        "data": {"benchmarks": benchmarks},
        "error": None,
    }
