from __future__ import annotations
import numpy as np
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    outliers: dict[str, dict] = {}

    for col in ctx.numeric_cols:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        iqr_mask = (s < lower) | (s > upper)
        iqr_count = int(iqr_mask.sum())

        mean, std = s.mean(), s.std()
        z_mask = ((s - mean).abs() / std) > 3 if std > 0 else pd.Series([False] * len(s))
        z_count = int(z_mask.sum())

        outliers[col] = {
            "iqr_outlier_count": iqr_count,
            "iqr_outlier_pct": round(iqr_count / len(s), 4),
            "zscore_outlier_count": z_count,
            "lower_fence": float(lower),
            "upper_fence": float(upper),
        }
        if iqr_count > 0:
            pct = iqr_count / len(s)
            findings.append(
                f"'{col}' has {iqr_count} outliers ({pct:.1%}) beyond IQR fences "
                f"[{lower:.2f}, {upper:.2f}]."
            )

    if not findings:
        findings.append("No significant outliers detected in numeric columns.")

    return {
        "script": "outlier_detection",
        "status": "ok",
        "findings": findings,
        "data": {"outliers": outliers},
        "error": None,
    }
