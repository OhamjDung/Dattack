from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats
from analysis.context import AnalysisContext

DEPENDENCIES = ["correlation_matrix"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    top_pairs = ctx.results.get("correlation_matrix", {}).get("data", {}).get("top_pairs", [])
    findings: list[str] = []
    stats_out: list[dict] = []

    for pair in top_pairs[:10]:
        a, b = pair["col_a"], pair["col_b"]
        sub = df[[a, b]].dropna()
        if len(sub) < 4:
            continue
        slope, intercept, r, p, se = stats.linregress(sub[a], sub[b])
        r2 = r ** 2
        stats_out.append({
            "col_a": a, "col_b": b,
            "r2": round(r2, 4), "p_value": round(p, 6),
            "slope": round(slope, 6), "intercept": round(intercept, 4),
        })
        if p < 0.01 and r2 > 0.1:
            findings.append(
                f"'{a}' explains {r2:.1%} of variance in '{b}' (p={p:.4f}, slope={slope:.4f})."
            )

    if not findings:
        findings.append("No statistically significant pairwise linear relationships found.")

    return {
        "script": "pairwise_scatter_stats",
        "status": "ok",
        "findings": findings,
        "data": {"regressions": stats_out},
        "error": None,
    }
