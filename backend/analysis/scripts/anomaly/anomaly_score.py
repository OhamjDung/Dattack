from __future__ import annotations
import numpy as np
import pandas as pd
from analysis.context import AnalysisContext

DEPENDENCIES = ["field_profile", "outlier_detection"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.numeric_cols) >= 2


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    findings: list[str] = []
    cols = ctx.numeric_cols[:8]
    sub = df[cols].dropna()

    if len(sub) < 10:
        return {"script": "anomaly_score", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    try:
        from sklearn.ensemble import IsolationForest
        iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=50)
        scores = iso.fit_predict(sub)
        anomaly_count = int((scores == -1).sum())
        anomaly_rate = anomaly_count / len(sub)
        findings.append(
            f"Isolation Forest detected {anomaly_count} anomalous rows ({anomaly_rate:.1%}) "
            f"across {len(cols)} numeric features."
        )
        method = "isolation_forest"
    except ImportError:
        # Fallback: average z-score
        z = (sub - sub.mean()) / sub.std().replace(0, 1)
        avg_z = z.abs().mean(axis=1)
        anomaly_mask = avg_z > 3
        anomaly_count = int(anomaly_mask.sum())
        anomaly_rate = anomaly_count / len(sub)
        findings.append(
            f"Z-score anomaly detection: {anomaly_count} rows with avg |z| > 3 ({anomaly_rate:.1%})."
        )
        method = "zscore_average"

    return {
        "script": "anomaly_score",
        "status": "ok",
        "findings": findings,
        "data": {
            "anomaly_count": anomaly_count,
            "anomaly_rate": round(anomaly_rate, 4),
            "columns_used": cols,
            "method": method,
        },
        "error": None,
    }
