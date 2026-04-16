from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["categorical_frequency"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    co_occurrences: list[dict] = {}

    cats = [c for c in ctx.categorical_cols if df[c].nunique() <= 30][:3]
    if len(cats) < 2:
        return {"script": "label_co_occurrence", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    pairs: list[dict] = []
    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            a, b = cats[i], cats[j]
            combo = df.groupby([a, b]).size().reset_index(name="count")
            combo["pct"] = combo["count"] / len(df)
            top = combo.nlargest(3, "count")
            for _, row in top.iterrows():
                if row["pct"] > 0.05:
                    pairs.append({
                        "col_a": a, "val_a": str(row[a]),
                        "col_b": b, "val_b": str(row[b]),
                        "count": int(row["count"]),
                        "pct": round(float(row["pct"]), 4),
                    })
                    findings.append(
                        f"'{a}'='{row[a]}' co-occurs with '{b}'='{row[b]}' "
                        f"in {row['pct']:.1%} of rows."
                    )

    if not findings:
        findings.append("No dominant label co-occurrence patterns found.")

    return {
        "script": "label_co_occurrence",
        "status": "ok",
        "findings": findings[:8],
        "data": {"co_occurrences": pairs[:20]},
        "error": None,
    }
