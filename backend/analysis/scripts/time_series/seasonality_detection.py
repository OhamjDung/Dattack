from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["stationarity_test", "trend_analysis"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col)
    except Exception:
        return {"script": "seasonality_detection", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    seasonality: dict[str, dict] = {}

    df_ts["_month"] = df_ts[date_col].dt.month
    df_ts["_dow"] = df_ts[date_col].dt.dayofweek

    for col in ctx.numeric_cols[:3]:
        if df_ts[col].isna().all():
            continue
        # Monthly pattern
        monthly = df_ts.groupby("_month")[col].mean()
        if len(monthly) >= 4:
            monthly_cv = float(monthly.std() / abs(monthly.mean())) if monthly.mean() != 0 else 0
            peak_month = int(monthly.idxmax())
            trough_month = int(monthly.idxmin())
            seasonality[col] = {
                "monthly_cv": round(monthly_cv, 4),
                "peak_month": peak_month,
                "trough_month": trough_month,
                "monthly_means": {int(k): round(float(v), 4) for k, v in monthly.items()},
            }
            if monthly_cv > 0.1:
                import calendar
                findings.append(
                    f"'{col}' shows monthly seasonality (CV={monthly_cv:.2f}): "
                    f"peak in {calendar.month_abbr[peak_month]}, "
                    f"trough in {calendar.month_abbr[trough_month]}."
                )

    if not findings:
        findings.append("No clear monthly seasonality detected.")

    return {
        "script": "seasonality_detection",
        "status": "ok",
        "findings": findings,
        "data": {"seasonality": seasonality},
        "error": None,
    }
