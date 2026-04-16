from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["cohort_analysis", "retention_curve"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    cohorts = ctx.results.get("cohort_analysis", {}).get("data", {}).get("cohorts", [])
    retention_rates = ctx.results.get("retention_curve", {}).get("data", {}).get("retention_rates", [])
    findings: list[str] = []

    if not cohorts or not retention_rates or len(cohorts) < 2:
        return {"script": "ltv_approximation", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    metric_col = ctx.numeric_cols[0] if ctx.numeric_cols else None
    avg_metric = np.mean([c.get("avg_metric", 0) for c in cohorts if c.get("avg_metric")]) if metric_col else None

    if avg_metric is None or avg_metric == 0:
        return {"script": "ltv_approximation", "status": "skipped",
                "findings": ["No metric data available for LTV estimation."], "data": {}, "error": None}

    # Simple LTV: sum of avg_metric × retention at each period
    ltv_periods = min(len(retention_rates), 12)
    ltv = sum(avg_metric * retention_rates[i] for i in range(ltv_periods))

    findings.append(
        f"Estimated LTV over {ltv_periods} periods: {ltv:.2f} "
        f"(based on avg '{metric_col}' = {avg_metric:.2f} × retention curve)."
    )
    findings.append(
        f"Improving first-period retention by 10% would increase estimated LTV by "
        f"~{ltv * 0.1:.2f}."
    )

    return {
        "script": "ltv_approximation",
        "status": "ok",
        "findings": findings,
        "data": {
            "ltv_estimate": round(ltv, 4),
            "avg_metric_per_period": round(float(avg_metric), 4),
            "periods_used": ltv_periods,
        },
        "error": None,
    }
