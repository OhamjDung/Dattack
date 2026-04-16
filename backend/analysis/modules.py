import json

MODULE_REGISTRY: dict[str, dict[str, str]] = {
    "foundation": {
        "schema_detector":     "analysis.scripts.foundation.schema_detector",
        "field_profile":       "analysis.scripts.foundation.field_profile",
        "data_quality_report": "analysis.scripts.foundation.data_quality_report",
    },
    "exploratory": {
        "distribution_analysis":   "analysis.scripts.exploratory.distribution_analysis",
        "outlier_detection":       "analysis.scripts.exploratory.outlier_detection",
        "normality_tests":         "analysis.scripts.exploratory.normality_tests",
        "correlation_matrix":      "analysis.scripts.exploratory.correlation_matrix",
        "pairwise_scatter_stats":  "analysis.scripts.exploratory.pairwise_scatter_stats",
        "multicollinearity_check": "analysis.scripts.exploratory.multicollinearity_check",
        "partial_correlation":     "analysis.scripts.exploratory.partial_correlation",
        "categorical_frequency":   "analysis.scripts.exploratory.categorical_frequency",
        "cardinality_analysis":    "analysis.scripts.exploratory.cardinality_analysis",
        "cross_tabulation":        "analysis.scripts.exploratory.cross_tabulation",
        "segment_comparison":      "analysis.scripts.exploratory.segment_comparison",
        "interaction_effects":     "analysis.scripts.exploratory.interaction_effects",
        "variance_analysis":       "analysis.scripts.exploratory.variance_analysis",
        "anova_test":              "analysis.scripts.exploratory.anova_test",
        "chi_square_test":         "analysis.scripts.exploratory.chi_square_test",
    },
    "time_series": {
        "trend_analysis":         "analysis.scripts.time_series.trend_analysis",
        "seasonality_detection":  "analysis.scripts.time_series.seasonality_detection",
        "changepoint_detection":  "analysis.scripts.time_series.changepoint_detection",
        "rolling_volatility":     "analysis.scripts.time_series.rolling_volatility",
        "peak_valley_detection":  "analysis.scripts.time_series.peak_valley_detection",
        "growth_rate_analysis":   "analysis.scripts.time_series.growth_rate_analysis",
        "lag_correlation":        "analysis.scripts.time_series.lag_correlation",
        "stationarity_test":      "analysis.scripts.time_series.stationarity_test",
        "cycle_detection":        "analysis.scripts.time_series.cycle_detection",
        "forecast_baseline":      "analysis.scripts.time_series.forecast_baseline",
        "category_drift":         "analysis.scripts.time_series.category_drift",
    },
    "ranking": {
        "percentile_ranking":  "analysis.scripts.ranking.percentile_ranking",
        "composite_score":     "analysis.scripts.ranking.composite_score",
        "top_bottom_analysis": "analysis.scripts.ranking.top_bottom_analysis",
        "tier_segmentation":   "analysis.scripts.ranking.tier_segmentation",
        "winner_loser":        "analysis.scripts.ranking.winner_loser",
    },
    "business": {
        "pareto_analysis":        "analysis.scripts.business.pareto_analysis",
        "cohort_analysis":        "analysis.scripts.business.cohort_analysis",
        "retention_curve":        "analysis.scripts.business.retention_curve",
        "ltv_approximation":      "analysis.scripts.business.ltv_approximation",
        "funnel_analysis":        "analysis.scripts.business.funnel_analysis",
        "concentration_analysis": "analysis.scripts.business.concentration_analysis",
        "revenue_decomposition":  "analysis.scripts.business.revenue_decomposition",
        "benchmark_comparison":   "analysis.scripts.business.benchmark_comparison",
    },
    "text": {
        "string_pattern_mining":    "analysis.scripts.text.string_pattern_mining",
        "edit_distance_clustering": "analysis.scripts.text.edit_distance_clustering",
        "label_co_occurrence":      "analysis.scripts.text.label_co_occurrence",
    },
    "anomaly": {
        "anomaly_score":       "analysis.scripts.anomaly.anomaly_score",
        "duplicate_detection": "analysis.scripts.anomaly.duplicate_detection",
        "missing_patterns":    "analysis.scripts.anomaly.missing_patterns",
    },
}

MODULE_SELECTION_PROMPT = """You are a data analysis planner. Select which analysis modules to activate.

Available modules:
- exploratory: distributions, outliers, correlations, statistical tests — use for understanding patterns and relationships
- time_series: trends, seasonality, forecasting, changepoints — use ONLY if a datetime column exists
- ranking: percentile ranks, composite scores, tier segmentation — use when goal involves comparing or ranking entities
- business: pareto, cohort, retention, LTV, funnel — use when data has transactions, customers, or business KPIs
- text: string pattern mining, fuzzy clustering — use ONLY if free-text or messy string columns exist
- anomaly: outlier scoring, duplicates, missing patterns — use when goal involves data quality or finding unusual rows

Dataset snapshot:
{summary}

User goal: {goal}

Return ONLY a valid JSON array of module names to activate (never include "foundation"). Max 4 modules.
Example: ["exploratory", "business", "anomaly"]"""


def build_selection_prompt(foundation_summary: dict, goal: str) -> str:
    return MODULE_SELECTION_PROMPT.format(
        summary=json.dumps(foundation_summary, indent=2, default=str),
        goal=goal,
    )
