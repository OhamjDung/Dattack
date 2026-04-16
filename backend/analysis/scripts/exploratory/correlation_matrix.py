from __future__ import annotations
import numpy as np
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    num_df = df[ctx.numeric_cols].dropna(how="all")

    pearson = num_df.corr(method="pearson")
    spearman = num_df.corr(method="spearman")

    # Extract top pairs
    pairs: list[dict] = []
    cols = ctx.numeric_cols
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = pearson.iloc[i, j]
            if abs(r) >= 0.3:
                pairs.append({"col_a": cols[i], "col_b": cols[j], "pearson": round(float(r), 4),
                               "spearman": round(float(spearman.iloc[i, j]), 4)})

    pairs.sort(key=lambda x: abs(x["pearson"]), reverse=True)
    findings: list[str] = []
    for p in pairs[:5]:
        direction = "positively" if p["pearson"] > 0 else "negatively"
        strength = "strongly" if abs(p["pearson"]) > 0.7 else "moderately"
        findings.append(
            f"'{p['col_a']}' and '{p['col_b']}' are {strength} {direction} correlated (r={p['pearson']:.2f})."
        )

    if not findings:
        findings.append("No strong linear correlations found between numeric columns.")

    return {
        "script": "correlation_matrix",
        "status": "ok",
        "findings": findings,
        "data": {
            "pearson": pearson.round(4).to_dict(),
            "top_pairs": pairs[:20],
        },
        "error": None,
    }
