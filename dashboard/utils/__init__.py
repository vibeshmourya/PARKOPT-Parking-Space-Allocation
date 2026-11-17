"""
dashboard.utils
Utility package for PARKOPT Streamlit Dashboard.
Provides data access services, optimization orchestration, PDF report generation,
session state management, and formatting helpers.
"""

from .formatting import format_number, format_pct, format_status_badge
from .state_manager import init_session_state, get_state, set_state
from .data_service import (
    load_cleaned_dataset,
    load_facility_statistics,
    load_demand_estimates,
    load_temporal_data,
    load_scenario_summaries,
    load_budget_sensitivity_data
)
from .optimization_service import run_solver_workflow
from .report_service import generate_academic_pdf_report

__all__ = [
    "format_number",
    "format_pct",
    "format_status_badge",
    "init_session_state",
    "get_state",
    "set_state",
    "load_cleaned_dataset",
    "load_facility_statistics",
    "load_demand_estimates",
    "load_temporal_data",
    "load_scenario_summaries",
    "load_budget_sensitivity_data",
    "run_solver_workflow",
    "generate_academic_pdf_report"
]

