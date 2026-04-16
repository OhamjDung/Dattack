from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 2 and len(ctx.datetime_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]
    findings: list[str] = []

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col)
        df_ts["_period"] = df_ts[date_col].dt.to_period("M")
    except Exception:
        return {"script": "revenue_decomposition", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    # Try to identify a volume col and a rate col
    cols = ctx.numeric_cols[:4]
    if len(cols) < 2:
        return {"script": "revenue_decomposition", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    metric_col = cols[0]
    volume_col = cols[1]

    period_agg = df_ts.groupby("_period").agg(
        metric=(metric_col, "sum"),
        volume=(volume_col, "count"),
    ).reset_index()
    period_agg["rate"] = period_agg["metric"] / period_agg["volume"].replace(0, np.nan)

    if len(period_agg) < 2:
        return {"script": "revenue_decomposition", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    first = period_agg.iloc[0]
    last = period_agg.iloc[-1]

    delta_metric = float(last["metric"] - first["metric"])
    volume_effect = float((last["volume"] - first["volume"]) * first["rate"])
    rate_effect = float((last["rate"] - first["rate"]) * first["volume"])

    total_effect = volume_effect + rate_effect
    vol_share = volume_effect / total_effect * 100 if total_effect != 0 else 0
    rate_share = rate_effect / total_effect * 100 if total_effect != 0 else 0

    findings.append(
        f"'{metric_col}' changed by {delta_metric:+.2f}: "
        f"volume effect = {volume_effect:+.2f} ({vol_share:.0f}%), "
        f"rate effect = {rate_effect:+.2f} ({rate_share:.0f}%)."
    )
    dominant = "volume-driven" if abs(vol_share) > abs(rate_share) else "rate-driven"
    findings.append(f"Change is primarily {dominant}.")

    return {
        "script": "revenue_decomposition",
        "status": "ok",
        "findings": findings,
        "data": {
            "metric_col": metric_col, "volume_col": volume_col,
            "delta_metric": round(delta_metric, 4),
            "volume_effect": round(volume_effect, 4),
            "rate_effect": round(rate_effect, 4),
        },
        "error": None,
    }
