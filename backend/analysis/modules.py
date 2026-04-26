import json

CURIOSITY_MODULE_REGISTRY: dict[str, dict[str, str]] = {
    "foundation": {
        "schema_detector":     "analysis.scripts.foundation.schema_detector",
        "field_profile":       "analysis.scripts.foundation.field_profile",
        "data_quality_report": "analysis.scripts.foundation.data_quality_report",
    },
    "structure": {
        "entity_type_guesser":       "analysis.curiosity_scripts.structure.entity_type_guesser",
        "target_col_candidates":     "analysis.curiosity_scripts.structure.target_col_candidates",
        "column_role_classifier":    "analysis.curiosity_scripts.structure.column_role_classifier",
        "dataset_shape_classifier":  "analysis.curiosity_scripts.structure.dataset_shape_classifier",
        "join_key_candidates":       "analysis.curiosity_scripts.structure.join_key_candidates",
        "boolean_disguise_detector": "analysis.curiosity_scripts.structure.boolean_disguise_detector",
        "id_column_validator":       "analysis.curiosity_scripts.structure.id_column_validator",
    },
    "signals": {
        "null_intent_detector":         "analysis.curiosity_scripts.signals.null_intent_detector",
        "outlier_prevalence_screen":    "analysis.curiosity_scripts.signals.outlier_prevalence_screen",
        "correlation_opportunity":      "analysis.curiosity_scripts.signals.correlation_opportunity",
        "segment_variable_candidates":  "analysis.curiosity_scripts.signals.segment_variable_candidates",
        "temporal_coverage_analyzer":   "analysis.curiosity_scripts.signals.temporal_coverage_analyzer",
        "concentration_screen":         "analysis.curiosity_scripts.signals.concentration_screen",
        "growth_signal_screen":         "analysis.curiosity_scripts.signals.growth_signal_screen",
        "anomaly_prevalence_screen":    "analysis.curiosity_scripts.signals.anomaly_prevalence_screen",
        "cardinality_screen":           "analysis.curiosity_scripts.signals.cardinality_screen",
    },
    "hypotheses": {
        "analysis_hypothesis_builder":   "analysis.curiosity_scripts.hypotheses.analysis_hypothesis_builder",
        "missing_analysis_detector":     "analysis.curiosity_scripts.hypotheses.missing_analysis_detector",
        "composite_metric_opportunity":  "analysis.curiosity_scripts.hypotheses.composite_metric_opportunity",
        "benchmark_opportunity_detector":"analysis.curiosity_scripts.hypotheses.benchmark_opportunity_detector",
    },
}

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

MODULE_COMPUTE_COSTS: dict[str, int] = {
    "exploratory": 2,
    "time_series": 2,
    "ranking": 1,
    "business": 2,
    "text": 1,
    "anomaly": 3,
}

MODULE_SELECTION_PROMPT = """You are a data analysis planner. Select which analysis modules to activate.

Available modules and their compute costs:
- exploratory (cost 2): distributions, outliers, correlations, statistical tests — for understanding patterns and relationships
- time_series (cost 2): trends, seasonality, forecasting, changepoints — ONLY if a datetime column exists
- ranking (cost 1): percentile ranks, composite scores, tier segmentation — when goal involves comparing or ranking entities
- business (cost 2): pareto, cohort, retention, LTV, funnel — when data has transactions, customers, or business KPIs
- text (cost 1): string pattern mining, fuzzy clustering — ONLY if free-text or messy string columns exist
- anomaly (cost 3): outlier scoring, duplicates, missing patterns — when goal involves data quality or unusual rows

Total compute budget: 6 points. Select modules whose costs sum to ≤6.
Prioritize modules most relevant to the user goal. Do not include "foundation".

Dataset snapshot:
{summary}

User goal: {goal}

Return ONLY a valid JSON array of module names. Example: ["exploratory", "business", "anomaly"]"""


def build_selection_prompt(foundation_summary: dict, goal: str) -> str:
    return MODULE_SELECTION_PROMPT.format(
        summary=json.dumps(foundation_summary, indent=2, default=str),
        goal=goal,
    )
