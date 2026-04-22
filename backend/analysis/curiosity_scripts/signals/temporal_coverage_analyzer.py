from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]
    question_candidates = []
    technique_candidates = []

    try:
        dates = pd.to_datetime(df[date_col], errors="coerce").dropna().sort_values()
    except Exception:
        return {"script": "temporal_coverage_analyzer", "status": "skipped",
                "question_candidates": [], "technique_candidates": [], "data": {}}

    if len(dates) < 2:
        return {"script": "temporal_coverage_analyzer", "status": "skipped",
                "question_candidates": [], "technique_candidates": [], "data": {}}

    date_min = dates.iloc[0].date()
    date_max = dates.iloc[-1].date()
    span_days = (date_max - date_min).days

    diffs = dates.diff().dropna()
    median_diff = diffs.median()
    if median_diff.days <= 1:
        granularity = "daily"
    elif median_diff.days <= 8:
        granularity = "weekly"
    elif median_diff.days <= 32:
        granularity = "monthly"
    else:
        granularity = "irregular"

    gaps = diffs[diffs > median_diff * 3]
    has_gaps = len(gaps) > 0

    technique_candidates.append({
        "label": "Trend & seasonality analysis",
        "description": f"Data spans {date_min} to {date_max} ({span_days} days) at {granularity} granularity — enough for trend and seasonal pattern detection.",
        "confidence": 0.9,
    })

    if has_gaps:
        question_candidates.append({
            "label": "Are there data gaps intentional?",
            "description": f"Found {len(gaps)} periods with unusually large time gaps in '{date_col}'. Could indicate missing data, seasonal pauses, or system outages.",
            "confidence": 0.8,
        })

    return {
        "script": "temporal_coverage_analyzer",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {
            "date_col": date_col,
            "date_min": str(date_min),
            "date_max": str(date_max),
            "span_days": span_days,
            "granularity": granularity,
            "gap_count": len(gaps),
        },
    }
