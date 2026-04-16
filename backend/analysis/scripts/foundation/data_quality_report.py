from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return True


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []

    null_rates = {col: float(df[col].isna().mean()) for col in df.columns}
    overall_null = float(df.isna().mean().mean())
    cols_with_nulls = [c for c, r in null_rates.items() if r > 0]
    high_null_cols = [c for c, r in null_rates.items() if r > 0.2]

    dup_count = int(df.duplicated().sum())
    dup_rate = dup_count / max(len(df), 1)

    type_issues: list[str] = []
    for col in ctx.categorical_cols:
        sample = df[col].dropna().astype(str)
        lower_counts = sample.str.lower().value_counts()
        orig_counts = sample.value_counts()
        if len(lower_counts) < len(orig_counts):
            type_issues.append(f"'{col}' has case inconsistencies (e.g. 'Yes' vs 'yes').")

    if overall_null > 0.05:
        findings.append(f"Overall null rate is {overall_null:.1%} across all columns.")
    if high_null_cols:
        findings.append(f"Columns with >20% nulls: {', '.join(high_null_cols)}.")
    if dup_rate > 0.01:
        findings.append(f"{dup_count:,} duplicate rows detected ({dup_rate:.1%} of dataset).")
    if type_issues:
        findings.extend(type_issues[:3])
    if not findings:
        findings.append("Data quality looks clean — low nulls, no duplicates, consistent types.")

    return {
        "script": "data_quality_report",
        "status": "ok",
        "findings": findings,
        "data": {
            "overall_null_rate": overall_null,
            "columns_with_nulls": cols_with_nulls,
            "high_null_cols": high_null_cols,
            "null_rates": null_rates,
            "duplicate_count": dup_count,
            "duplicate_rate": dup_rate,
            "type_issues": type_issues,
            "row_count": len(df),
            "col_count": len(df.columns),
        },
        "error": None,
    }
