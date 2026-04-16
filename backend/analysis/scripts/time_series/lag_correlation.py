from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["stationarity_test", "correlation_matrix"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    except Exception:
        return {"script": "lag_correlation", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    lag_results: list[dict] = []
    cols = ctx.numeric_cols[:4]
    max_lag = min(12, len(df_ts) // 4)

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            a, b = cols[i], cols[j]
            best_lag, best_r = 0, 0.0
            for lag in range(1, max_lag + 1):
                r = float(df_ts[a].corr(df_ts[b].shift(lag)))
                if abs(r) > abs(best_r):
                    best_lag, best_r = lag, r
            if abs(best_r) > 0.3:
                lag_results.append({"col_a": a, "col_b": b, "best_lag": best_lag, "r": round(best_r, 4)})
                dir_ = "positively" if best_r > 0 else "negatively"
                findings.append(
                    f"'{a}' {dir_} predicts '{b}' with a lag of {best_lag} period(s) (r={best_r:.2f})."
                )

    if not findings:
        findings.append("No significant lagged correlations found between numeric columns.")

    return {
        "script": "lag_correlation",
        "status": "ok",
        "findings": findings,
        "data": {"lag_correlations": lag_results, "max_lag_tested": max_lag},
        "error": None,
    }
