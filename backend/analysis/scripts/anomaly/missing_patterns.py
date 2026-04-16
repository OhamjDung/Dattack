from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return ctx.df.isna().any().any()


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    null_cols = [c for c in df.columns if df[c].isna().any()]

    if not null_cols:
        return {"script": "missing_patterns", "status": "ok",
                "findings": ["No missing values detected."], "data": {}, "error": None}

    # Co-missing correlation
    null_matrix = df[null_cols].isna().astype(int)
    co_missing: list[dict] = []
    for i in range(len(null_cols)):
        for j in range(i + 1, len(null_cols)):
            a, b = null_cols[i], null_cols[j]
            both_null = int((null_matrix[a] & null_matrix[b]).sum())
            if both_null > 0:
                pct = both_null / len(df)
                co_missing.append({"col_a": a, "col_b": b, "both_null_count": both_null,
                                   "pct": round(pct, 4)})
                if pct > 0.05:
                    findings.append(
                        f"'{a}' and '{b}' are missing together in {both_null} rows ({pct:.1%}) — likely same source."
                    )

    # Rows with many nulls
    row_null_counts = df.isna().sum(axis=1)
    rows_all_null = int((row_null_counts == len(df.columns)).sum())
    rows_mostly_null = int((row_null_counts >= len(df.columns) * 0.5).sum())
    if rows_mostly_null > 0:
        findings.append(f"{rows_mostly_null} rows are ≥50% null — consider dropping them.")

    if not findings:
        findings.append("Missing values appear in independent columns with no strong co-missing patterns.")

    return {
        "script": "missing_patterns",
        "status": "ok",
        "findings": findings,
        "data": {
            "null_cols": null_cols,
            "co_missing_pairs": co_missing[:10],
            "rows_mostly_null": rows_mostly_null,
        },
        "error": None,
    }
