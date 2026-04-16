from __future__ import annotations
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["categorical_frequency"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.categorical_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    crosstabs: list[dict] = []

    # Take top 3 categorical columns by cardinality (prefer lower cardinality)
    cats = sorted(ctx.categorical_cols, key=lambda c: df[c].nunique())[:3]

    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            a, b = cats[i], cats[j]
            if df[a].nunique() > 20 or df[b].nunique() > 20:
                continue
            ct = pd.crosstab(df[a], df[b], normalize="index").round(3)
            # Find the strongest association: max deviation from marginal
            marginal = df[b].value_counts(normalize=True)
            deviations = (ct - marginal).abs().max().max()
            crosstabs.append({
                "col_a": a, "col_b": b,
                "max_deviation": round(float(deviations), 4),
                "table": ct.to_dict(),
            })
            if deviations > 0.2:
                findings.append(
                    f"'{a}' and '{b}' show a strong association "
                    f"(max row deviation {deviations:.2f} from marginal distribution)."
                )

    if not findings:
        findings.append("Categorical pairs show mostly independent distributions.")

    return {
        "script": "cross_tabulation",
        "status": "ok",
        "findings": findings,
        "data": {"crosstabs": crosstabs},
        "error": None,
    }
