from __future__ import annotations
import numpy as np
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return True


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    column_stats: dict[str, dict] = {}
    findings: list[str] = []

    for col in ctx.numeric_cols:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        null_rate = float(df[col].isna().mean())
        stats = {
            "mean": _safe(s.mean()), "std": _safe(s.std()),
            "min": _safe(s.min()), "max": _safe(s.max()),
            "p25": _safe(s.quantile(0.25)), "p50": _safe(s.quantile(0.50)),
            "p75": _safe(s.quantile(0.75)),
            "null_rate": null_rate,
            "unique_count": int(df[col].nunique()),
            "range": _safe(s.max() - s.min()),
            "cv": _safe(s.std() / s.mean()) if s.mean() != 0 else None,
        }
        column_stats[col] = stats
        if null_rate > 0.1:
            findings.append(f"'{col}' has {null_rate:.1%} missing values.")
        if stats["cv"] is not None and abs(stats["cv"]) > 1.5:
            findings.append(f"'{col}' has high variability (CV={stats['cv']:.2f}).")

    for col in ctx.categorical_cols:
        s = df[col].dropna()
        vc = s.value_counts()
        null_rate = float(df[col].isna().mean())
        stats = {
            "top_value": str(vc.index[0]) if len(vc) > 0 else None,
            "top_freq": float(vc.iloc[0] / len(s)) if len(vc) > 0 else None,
            "unique_count": int(df[col].nunique()),
            "null_rate": null_rate,
        }
        column_stats[col] = stats
        if stats["unique_count"] == 1:
            findings.append(f"'{col}' has only one unique value — no variance.")

    if not findings:
        findings.append("All numeric fields have low null rates and reasonable distributions.")

    return {
        "script": "field_profile",
        "status": "ok",
        "findings": findings,
        "data": {"column_stats": column_stats},
        "error": None,
    }


def _safe(val) -> float | None:
    try:
        v = float(val)
        return None if (v != v) else v  # NaN check
    except Exception:
        return None
