from __future__ import annotations
from analysis.context import AnalysisContext

DEPENDENCIES: list[str] = ["schema_detector", "field_profile"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return True


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    n_rows = len(df)
    id_cols = ctx.id_cols
    datetime_cols = ctx.datetime_cols

    question_candidates = []
    technique_candidates = []

    # Guess entity type from structure
    if id_cols:
        id_col = id_cols[0]
        nunique = df[id_col].nunique()
        if nunique == n_rows:
            guess = "one row per unique entity (entity-level data)"
        else:
            ratio = nunique / n_rows
            if ratio < 0.1:
                guess = "many rows per entity (event or transaction data)"
            else:
                guess = "mixed — some entities appear multiple times"

        question_candidates.append({
            "label": "What does each row represent?",
            "description": f"Column '{id_col}' has {nunique:,} unique values out of {n_rows:,} rows, suggesting {guess}. Confirming this shapes all downstream analysis.",
            "confidence": 0.85,
        })
    elif datetime_cols:
        question_candidates.append({
            "label": "Is this time series or snapshot data?",
            "description": f"A date column '{datetime_cols[0]}' exists but no obvious ID column. Could be time series (one row per period) or a snapshot.",
            "confidence": 0.75,
        })
    else:
        question_candidates.append({
            "label": "What does each row represent?",
            "description": f"No clear ID or date column found. Understanding the unit of observation is critical — is each row a customer, a product, a transaction?",
            "confidence": 0.9,
        })

    if datetime_cols and id_cols:
        technique_candidates.append({
            "label": "Cohort & retention analysis",
            "description": "Entity ID + date column together enable cohort grouping and retention curves.",
            "confidence": 0.8,
        })

    return {
        "script": "entity_type_guesser",
        "status": "ok",
        "question_candidates": question_candidates,
        "technique_candidates": technique_candidates,
        "data": {"id_cols": id_cols, "datetime_cols": datetime_cols, "n_rows": n_rows},
    }
