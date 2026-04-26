from __future__ import annotations
import json
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ColumnSchema:
    name: str
    inferred_type: str  # "datetime" | "numeric" | "categorical" | "text" | "id_col" | "boolean"
    pandas_dtype: str
    sample_values: list[Any]


@dataclass
class AnalysisContext:
    df: pd.DataFrame
    goal: str
    target_col: Optional[str] = None

    schema: dict[str, ColumnSchema] = field(default_factory=dict)
    profile: dict[str, dict] = field(default_factory=dict)
    quality: dict = field(default_factory=dict)
    results: dict[str, dict] = field(default_factory=dict)

    datetime_cols: list[str] = field(default_factory=list)
    numeric_cols: list[str] = field(default_factory=list)
    categorical_cols: list[str] = field(default_factory=list)
    text_cols: list[str] = field(default_factory=list)
    id_cols: list[str] = field(default_factory=list)

    active_modules: list[str] = field(default_factory=list)

    abort: bool = False
    abort_reason: str = ""

    def to_gemini_summary(self) -> dict:
        return {
            "goal": self.goal,
            "target_col": self.target_col,
            "shape": {"rows": len(self.df), "cols": len(self.df.columns)},
            "columns": {
                name: {
                    "inferred_type": col.inferred_type,
                    "pandas_dtype": col.pandas_dtype,
                    "sample_values": [str(v) for v in col.sample_values],
                }
                for name, col in self.schema.items()
            },
            "profile": self.profile,
            "quality": self.quality,
        }

    def to_gemini_synthesis_input(self, max_findings: int = 5) -> dict:
        return {
            "goal": self.goal,
            "target_col": self.target_col,
            "shape": {"rows": len(self.df), "cols": len(self.df.columns)},
            "active_modules": self.active_modules,
            "quality_summary": self.quality,
            "script_findings": {
                name: result["findings"][:max_findings]
                for name, result in self.results.items()
                if result.get("status") == "ok" and result.get("findings")
            },
        }
