from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector", "pareto_analysis"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]
    findings: list[str] = []

    try:
        df_c = df.copy()
        df_c[date_col] = pd.to_datetime(df_c[date_col], errors="coerce")
        df_c = df_c.dropna(subset=[date_col])
        df_c["_cohort"] = df_c[date_col].dt.to_period("M").astype(str)
    except Exception:
        return {"script": "cohort_analysis", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    cohort_counts = df_c["_cohort"].value_counts().sort_index()
    if len(cohort_counts) < 2:
        return {"script": "cohort_analysis", "status": "skipped",
                "findings": ["Not enough distinct months for cohort analysis."],
                "data": {}, "error": None}

    cohort_summary: list[dict] = []
    metric_col = ctx.numeric_cols[0] if ctx.numeric_cols else None

    for cohort, sub in df_c.groupby("_cohort"):
        entry: dict = {"cohort": str(cohort), "count": int(len(sub))}
        if metric_col:
            entry["avg_metric"] = round(float(sub[metric_col].mean()), 4)
        cohort_summary.append(entry)

    if metric_col:
        first = cohort_summary[0].get("avg_metric", 0)
        last = cohort_summary[-1].get("avg_metric", 0)
        change = (last - first) / abs(first) * 100 if first != 0 else 0
        if abs(change) > 10:
            direction = "increased" if change > 0 else "decreased"
            findings.append(
                f"Average '{metric_col}' per cohort {direction} "
                f"{abs(change):.1f}% from first to latest cohort."
            )

    largest_cohort = max(cohort_summary, key=lambda x: x["count"])
    findings.append(
        f"Largest cohort: {largest_cohort['cohort']} with {largest_cohort['count']:,} records."
    )

    return {
        "script": "cohort_analysis",
        "status": "ok",
        "findings": findings,
        "data": {"cohorts": cohort_summary, "date_col": date_col},
        "error": None,
    }
