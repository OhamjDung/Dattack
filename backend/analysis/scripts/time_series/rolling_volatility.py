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
    volatility: dict[str, dict] = {}

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    except Exception:
        return {"script": "rolling_volatility", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    window = max(5, len(df_ts) // 10)

    for col in ctx.numeric_cols[:4]:
        s = df_ts[col].dropna()
        if len(s) < window * 2:
            continue
        rolling_std = s.rolling(window).std().dropna()
        cv = rolling_std / abs(s.rolling(window).mean().dropna())
        max_vol_idx = int(rolling_std.idxmax())
        min_vol_idx = int(rolling_std.idxmin())
        volatility[col] = {
            "mean_rolling_std": round(float(rolling_std.mean()), 4),
            "max_rolling_std": round(float(rolling_std.max()), 4),
            "vol_ratio": round(float(rolling_std.max() / max(rolling_std.min(), 1e-9)), 2),
        }
        vol_ratio = volatility[col]["vol_ratio"]
        if vol_ratio > 2.0:
            findings.append(
                f"'{col}' has periods of high volatility (max/min std ratio={vol_ratio:.1f}x) — unstable periods exist."
            )

    if not findings:
        findings.append("Rolling volatility is relatively stable across the time series.")

    return {
        "script": "rolling_volatility",
        "status": "ok",
        "findings": findings,
        "data": {"volatility": volatility, "window": window},
        "error": None,
    }
