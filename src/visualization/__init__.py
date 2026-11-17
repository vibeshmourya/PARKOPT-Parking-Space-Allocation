"""
__init__.py
Visualization package for Optimal Parking Space Allocation Using Linear Programming.
Exposes modular chart generators for Occupancy, Temporal, Optimization, and Sensitivity analyses.
"""

import os
from typing import Dict, Any, Optional
import pandas as pd

from .visualization_utils import (
    COLOR_PRIMARY_BLUE, COLOR_SECONDARY_BLUE, COLOR_EMERALD, COLOR_CRIMSON,
    COLOR_AMBER, COLOR_SLATE, COLOR_LIGHT_GRAY, COLOR_SALMON, COLOR_TEAL,
    PLOTLY_TEMPLATE, save_static_and_interactive, validate_required_columns
)
from .occupancy_charts import (
    plot_capacity_vs_average_occupancy,
    plot_parking_utilization_ranking,
    plot_peak_occupancy_and_overflow,
    plot_parking_availability,
    generate_all_occupancy_charts
)
from .temporal_charts import (
    plot_hourly_occupancy_trend,
    plot_day_of_week_analysis,
    plot_hourly_utilization_heatmap,
    plot_facility_demand_by_period_heatmap,
    generate_all_temporal_charts
)
from .optimization_charts import (
    plot_baseline_vs_optimized_allocation,
    plot_demand_vs_optimized_allocation,
    plot_allocation_distribution,
    plot_facility_allocation_changes,
    plot_priority_strategy_comparison,
    plot_demand_estimator_comparison,
    generate_all_optimization_charts
)
from .sensitivity_charts import (
    plot_budget_vs_objective_and_unmet,
    plot_budget_utilization_and_marginal_returns,
    plot_facility_satisfaction_transitions,
    plot_budget_scenarios_allocation_shifts,
    generate_all_sensitivity_charts
)
from .analytical_insights import compute_analytical_insights


def run_full_visualization_pipeline(
    df_clean: Optional[pd.DataFrame] = None,
    base_output_dir: str = "outputs/visualizations"
) -> Dict[str, Any]:
    """
    Executes the complete Phase 4 visualization and analytical insights pipeline.
    Generates all PNG static charts, Plotly interactive HTML files, and Markdown insight reports.
    
    Subdirectories created:
      - outputs/visualizations/occupancy/
      - outputs/visualizations/temporal/
      - outputs/visualizations/optimization/
      - outputs/visualizations/sensitivity/
      - outputs/visualizations/insights/
    """
    if df_clean is None:
        import sys
        # Lazy load raw data and clean
        from data_loader import load_raw_data
        from data_cleaning import clean_parking_data
        raw = load_raw_data()
        df_clean, _ = clean_parking_data(raw)

    occ_dir = os.path.join(base_output_dir, "occupancy")
    temp_dir = os.path.join(base_output_dir, "temporal")
    opt_dir = os.path.join(base_output_dir, "optimization")
    sens_dir = os.path.join(base_output_dir, "sensitivity")
    ins_dir = os.path.join(base_output_dir, "insights")

    # 1. Occupancy Suite
    occ_res = generate_all_occupancy_charts(df_clean, output_dir=occ_dir)

    # 2. Temporal Suite
    temp_res = generate_all_temporal_charts(df_clean, output_dir=temp_dir)

    # 3. Optimization Suite
    opt_res = generate_all_optimization_charts(output_dir=opt_dir)

    # 4. Sensitivity Suite
    sens_res = generate_all_sensitivity_charts(output_dir=sens_dir)

    # 5. Analytical Insights
    insights = compute_analytical_insights(output_dir=ins_dir)

    return {
        "occupancy_charts": occ_res,
        "temporal_charts": temp_res,
        "optimization_charts": opt_res,
        "sensitivity_charts": sens_res,
        "analytical_insights": insights
    }

