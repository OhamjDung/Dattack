from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    freq: dict[str, dict] = {}

    for col in ctx.categorical_cols:
        vc = df[col].value_counts(dropna=True)
        total = len(df[col].dropna())
        if total == 0:
            continue
        top_n = vc.head(10)
        top_share = float(vc.iloc[0] / total) if len(vc) > 0 else 0
        long_tail = int((vc < total * 0.01).sum())

        freq[col] = {
            "top_values": {str(k): int(v) for k, v in top_n.items()},
            "top_value_share": round(top_share, 4),
            "unique_count": int(df[col].nunique()),
            "long_tail_count": long_tail,
        }
        if top_share > 0.8:
            findings.append(
                f"'{col}' is dominated by '{vc.index[0]}' ({top_share:.1%} of values)."
            )
        if long_tail > 5:
            findings.append(
                f"'{col}' has {long_tail} rare values (each <1%) — consider grouping them."
            )

    if not findings:
        findings.append("Categorical columns have well-distributed values with no extreme dominance.")

    return {
        "script": "categorical_frequency",
        "status": "ok",
        "findings": findings,
        "data": {"frequency": freq},
        "error": None,
    }
