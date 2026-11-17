"""
dashboard.components
Reusable UI and visualization components for the PARKOPT Streamlit application.
"""

from .sidebar import render_sidebar
from .kpi_cards import render_kpi_card, render_kpi_row
from .charts import (
    render_capacity_vs_occupancy_chart,
    render_utilization_ranking_chart,
    render_peak_vs_capacity_chart,
    render_temporal_diurnal_chart,
    render_hourly_heatmap_chart,
    render_baseline_vs_opt_chart,
    render_demand_fulfillment_chart,
    render_allocation_diff_chart,
    render_budget_sweep_chart,
    render_marginal_return_chart,
    render_satisfaction_transitions_chart,
    render_scenarios_comparison_chart
)
from .tables import render_styled_dataframe
from .downloads import render_csv_download_button, render_pdf_download_button

__all__ = [
    "render_sidebar",
    "render_kpi_card",
    "render_kpi_row",
    "render_capacity_vs_occupancy_chart",
    "render_utilization_ranking_chart",
    "render_peak_vs_capacity_chart",
    "render_temporal_diurnal_chart",
    "render_hourly_heatmap_chart",
    "render_baseline_vs_opt_chart",
    "render_demand_fulfillment_chart",
    "render_allocation_diff_chart",
    "render_budget_sweep_chart",
    "render_marginal_return_chart",
    "render_satisfaction_transitions_chart",
    "render_scenarios_comparison_chart",
    "render_styled_dataframe",
    "render_csv_download_button",
    "render_pdf_download_button"
]

