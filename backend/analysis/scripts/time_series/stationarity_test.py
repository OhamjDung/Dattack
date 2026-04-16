from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]
    findings: list[str] = []
    results: dict[str, dict] = {}

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col)
    except Exception:
        return {"script": "stationarity_test", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    for col in ctx.numeric_cols[:4]:
        series = df_ts[col].dropna()
        if len(series) < 8:
            continue
        # Simple rolling mean variance test (ADF alternative without statsmodels)
        half = len(series) // 2
        mean_diff = abs(series[:half].mean() - series[half:].mean())
        std_diff = abs(series[:half].std() - series[half:].std())
        mean_cv = mean_diff / abs(series.mean()) if series.mean() != 0 else 0
        is_stationary = mean_cv < 0.1 and std_diff / max(series.std(), 1e-9) < 0.3
        results[col] = {
            "likely_stationary": is_stationary,
            "mean_shift_ratio": round(float(mean_cv), 4),
        }
        if not is_stationary:
            findings.append(
                f"'{col}' shows signs of non-stationarity (mean shift ratio={mean_cv:.2f}) — differencing may help."
            )

    if not findings:
        findings.append("Time series columns appear approximately stationary.")

    return {
        "script": "stationarity_test",
        "status": "ok",
        "findings": findings,
        "data": {"stationarity": results, "date_col": date_col},
        "error": None,
    }
