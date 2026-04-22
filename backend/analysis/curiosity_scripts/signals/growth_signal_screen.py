from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df.copy()
    date_col = ctx.datetime_cols[0]
    technique_candidates = []
    growth_signals = []

    try:
        df["__date__"] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=["__date__"]).sort_values("__date__")
    except Exception:
        return {"script": "growth_signal_screen", "status": "skipped",
                "question_candidates": [], "technique_candidates": [], "data": {}}

    n = len(df)
    if n < 10:
        return {"script": "growth_signal_screen", "status": "skipped",
                "question_candidates": [], "technique_candidates": [], "data": {}}

    quarter = n // 4
    early = df.iloc[:quarter]
    late = df.iloc[-quarter:]

    for col in ctx.numeric_cols[:5]:
        early_mean = early[col].mean()
        late_mean = late[col].mean()
        if early_mean == 0 or pd.isna(early_mean) or pd.isna(late_mean):
            continue
        pct_change = (late_mean - early_mean) / abs(early_mean)
        growth_signals.append({"col": col, "pct_change": round(float(pct_change), 3),
                                "early_mean": round(float(early_mean), 2), "late_mean": round(float(late_mean), 2)})

    growth_signals.sort(key=lambda x: -abs(x["pct_change"]))

    if growth_signals and abs(growth_signals[0]["pct_change"]) > 0.1:
        g = growth_signals[0]
        direction = "grew" if g["pct_change"] > 0 else "declined"
        technique_candidates.append({
            "label": f"Trend analysis on '{g['col']}'",
            "description": f"'{g['col']}' {direction} {abs(g['pct_change']):.0%} from early to late period. Trend decomposition will confirm direction and significance.",
            "confidence": 0.85,
        })

    return {
        "script": "growth_signal_screen",
        "status": "ok",
        "question_candidates": [],
        "technique_candidates": technique_candidates,
        "data": {"growth_signals": growth_signals},
    }
