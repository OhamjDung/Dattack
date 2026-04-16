from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    pareto: dict[str, dict] = {}

    for col in ctx.numeric_cols[:3]:
        s = df[col].dropna()
        s = s[s > 0]
        if len(s) < 4:
            continue
        sorted_s = s.sort_values(ascending=False).reset_index(drop=True)
        cumsum = sorted_s.cumsum()
        total = float(sorted_s.sum())
        pct_at_20 = int(len(sorted_s) * 0.2)
        top20_share = float(cumsum.iloc[pct_at_20 - 1] / total) if pct_at_20 > 0 else 0
        pct_rows_for_80 = float((cumsum <= total * 0.8).sum() / len(sorted_s))

        pareto[col] = {
            "top_20pct_share": round(top20_share, 4),
            "pct_rows_for_80pct": round(pct_rows_for_80, 4),
            "gini": _gini(sorted_s.values),
        }
        if top20_share > 0.6:
            findings.append(
                f"'{col}' follows a Pareto pattern: top 20% of rows account for "
                f"{top20_share:.1%} of total."
            )

    if not findings:
        findings.append("Metric distributions are relatively equal — no strong Pareto concentration.")

    return {
        "script": "pareto_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"pareto": pareto},
        "error": None,
    }


def _gini(values) -> float:
    import numpy as np
    n = len(values)
    if n == 0:
        return 0.0
    sorted_v = np.sort(values)
    cumsum = np.cumsum(sorted_v)
    return float((2 * np.sum((np.arange(1, n+1)) * sorted_v) - (n + 1) * cumsum[-1]) / (n * cumsum[-1]))
