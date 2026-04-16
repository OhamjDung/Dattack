from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["trend_analysis"]


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
        return {"script": "changepoint_detection", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    changepoints: dict[str, list] = {}

    for col in ctx.numeric_cols[:3]:
        s = df_ts[col].dropna().reset_index(drop=True)
        if len(s) < 10:
            continue
        # CUSUM-based changepoint detection
        mean = s.mean()
        cusum = (s - mean).cumsum()
        cps = []
        window = max(3, len(s) // 5)
        for i in range(window, len(s) - window):
            left_mean = s[:i].mean()
            right_mean = s[i:].mean()
            diff = abs(right_mean - left_mean) / abs(mean) if mean != 0 else 0
            if diff > 0.15:
                if not cps or i - cps[-1] > window:
                    cps.append(i)

        changepoints[col] = []
        for cp in cps[:3]:
            date_str = str(df_ts[date_col].iloc[cp])[:10]
            before_mean = float(s[:cp].mean())
            after_mean = float(s[cp:].mean())
            changepoints[col].append({
                "index": cp, "date": date_str,
                "before_mean": round(before_mean, 4),
                "after_mean": round(after_mean, 4),
                "pct_shift": round((after_mean - before_mean) / abs(before_mean) * 100, 1) if before_mean != 0 else 0,
            })
            findings.append(
                f"'{col}' has a structural change around {date_str}: "
                f"mean shifted from {before_mean:.2f} to {after_mean:.2f}."
            )

    if not findings:
        findings.append("No significant structural changepoints detected.")

    return {
        "script": "changepoint_detection",
        "status": "ok",
        "findings": findings,
        "data": {"changepoints": changepoints},
        "error": None,
    }
