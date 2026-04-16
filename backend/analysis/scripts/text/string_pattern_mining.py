from __future__ import annotations
import re
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["schema_detector"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.text_cols) > 0 or len(ctx.categorical_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    patterns: dict[str, dict] = {}

    target_cols = (ctx.text_cols + ctx.categorical_cols)[:5]
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\+?[\d\s\-\(\)]{7,15}",
        "url": r"https?://\S+",
        "date_string": r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}",
        "currency": r"[\$€£¥]\s?\d+[\d,.]*",
        "postal_code": r"\b\d{5}(-\d{4})?\b",
    }

    for col in target_cols:
        s = df[col].dropna().astype(str)
        col_patterns: dict[str, int] = {}
        for pname, patt in PATTERNS.items():
            matches = s.str.contains(patt, regex=True, na=False).sum()
            if matches > 0:
                col_patterns[pname] = int(matches)
        if col_patterns:
            patterns[col] = col_patterns
            for pname, count in col_patterns.items():
                pct = count / len(s)
                findings.append(
                    f"'{col}' contains {count} {pname} patterns ({pct:.1%} of values)."
                )

    if not findings:
        findings.append("No structured patterns (email, phone, URL, etc.) found in string columns.")

    return {
        "script": "string_pattern_mining",
        "status": "ok",
        "findings": findings,
        "data": {"patterns": patterns},
        "error": None,
    }
