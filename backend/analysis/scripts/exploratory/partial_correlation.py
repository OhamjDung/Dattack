from __future__ import annotations
import numpy as np
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["correlation_matrix"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 3


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    cols = ctx.numeric_cols[:10]  # cap for performance
    num_df = df[cols].dropna()
    if len(num_df) < 4:
        return {"script": "partial_correlation", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    try:
        corr = num_df.corr().values
        inv = np.linalg.pinv(corr)
        d = np.sqrt(np.diag(inv))
        partial = -inv / np.outer(d, d)
        np.fill_diagonal(partial, 1.0)
    except Exception as e:
        return {"script": "partial_correlation", "status": "error",
                "findings": [], "data": {}, "error": str(e)}

    pairs: list[dict] = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = float(partial[i, j])
            if abs(r) >= 0.2:
                pairs.append({"col_a": cols[i], "col_b": cols[j], "partial_r": round(r, 4)})

    pairs.sort(key=lambda x: abs(x["partial_r"]), reverse=True)
    findings: list[str] = []
    for p in pairs[:4]:
        dir_ = "positive" if p["partial_r"] > 0 else "negative"
        findings.append(
            f"'{p['col_a']}' and '{p['col_b']}' have a {dir_} partial correlation "
            f"(r={p['partial_r']:.2f}) controlling for all other variables."
        )
    if not findings:
        findings.append("No notable partial correlations found after controlling for other variables.")

    return {
        "script": "partial_correlation",
        "status": "ok",
        "findings": findings,
        "data": {"top_partial_pairs": pairs[:15]},
        "error": None,
    }
