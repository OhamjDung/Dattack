from __future__ import annotations
import pandas as pd
import numpy as np
from analysis.context import AnalysisContext

DEPENDENCIES = ["stationarity_test"]


def is_applicable(ctx: AnalysisContext) -> bool:
    return len(ctx.datetime_cols) > 0 and len(ctx.numeric_cols) > 0


def run(ctx: AnalysisContext) -> dict:
    df = ctx.df
    date_col = ctx.datetime_cols[0]

    try:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    except Exception:
        return {"script": "cycle_detection", "status": "skipped",
                "findings": [], "data": {}, "error": None}

    findings: list[str] = []
    cycles: dict[str, dict] = {}

    for col in ctx.numeric_cols[:3]:
        s = df_ts[col].dropna()
        if len(s) < 8:
            continue
        # FFT-based dominant frequency detection
        detrended = s - s.rolling(min(5, len(s)//2), min_periods=1).mean().fillna(s)
        fft_vals = np.fft.rfft(detrended.fillna(0).values)
        freqs = np.fft.rfftfreq(len(detrended))
        magnitudes = np.abs(fft_vals)
        # Ignore DC (index 0)
        if len(magnitudes) > 1:
            dominant_idx = int(np.argmax(magnitudes[1:]) + 1)
            dominant_freq = float(freqs[dominant_idx])
            dominant_period = round(1 / dominant_freq) if dominant_freq > 0 else None
            cycles[col] = {
                "dominant_period": dominant_period,
                "dominant_freq": round(dominant_freq, 4),
                "magnitude": round(float(magnitudes[dominant_idx]), 4),
            }
            if dominant_period and 2 <= dominant_period <= len(s) // 2:
                findings.append(
                    f"'{col}' has a dominant cycle of ~{dominant_period} periods (FFT analysis)."
                )

    if not findings:
        findings.append("No strong cyclic patterns detected via FFT.")

    return {
        "script": "cycle_detection",
        "status": "ok",
        "findings": findings,
        "data": {"cycles": cycles},
        "error": None,
    }
