from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["stationarity_test", "trend_analysis", "seasonality_detection"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    except Exception:
        return {"script": "forecast_baseline", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    forecasts: dict[str, dict] = {}

    for col in ctx.numeric_cols[:3]:
        s = df_ts[col].dropna().reset_index(drop=True)
        if len(s) < 6:
            continue
        n = len(s)
        train = s[:int(n * 0.8)]
        test = s[int(n * 0.8):]
        horizon = len(test)

        # Naive: last value repeated
        naive_pred = np.full(horizon, float(train.iloc[-1]))
        # Moving average
        ma_pred = np.full(horizon, float(train.tail(min(5, len(train))).mean()))
        # Exponential smoothing (alpha=0.3)
        alpha = 0.3
        exp_val = float(train.iloc[0])
        for v in train:
            exp_val = alpha * float(v) + (1 - alpha) * exp_val
        exp_pred = np.full(horizon, exp_val)

        actual = test.values
        def mape(pred):
            mask = actual != 0
            return float(np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask]))) * 100 if mask.any() else None

        forecasts[col] = {
            "naive_mape": round(mape(naive_pred), 2) if mape(naive_pred) else None,
            "moving_avg_mape": round(mape(ma_pred), 2) if mape(ma_pred) else None,
            "exp_smoothing_mape": round(mape(exp_pred), 2) if mape(exp_pred) else None,
            "next_period_forecast": round(exp_val, 4),
        }
        best = min(
            [("naive", mape(naive_pred)), ("moving average", mape(ma_pred)), ("exp smoothing", mape(exp_pred))],
            key=lambda x: x[1] if x[1] is not None else float("inf")
        )
        findings.append(
            f"'{col}' baseline forecast: best method is {best[0]} "
            f"(MAPE={best[1]:.1f}%). Next-period estimate: {exp_val:.2f}."
        )

    return {
        "script": "forecast_baseline",
        "status": "ok",
        "findings": findings,
        "data": {"forecasts": forecasts},
        "error": None,
    }
