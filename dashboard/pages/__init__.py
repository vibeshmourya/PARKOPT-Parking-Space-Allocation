"""
dashboard.pages
Package for the multi-page Streamlit application PARKOPT.
Exports the 4 modern redesigned page renderers and backward-compatibility aliases.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import importlib

# 4 Redesigned Pages
p1 = importlib.import_module("dashboard.pages.1_Dashboard")
p2 = importlib.import_module("dashboard.pages.2_Explore_Parking")
p3 = importlib.import_module("dashboard.pages.3_Optimize_Allocation")
p4 = importlib.import_module("dashboard.pages.4_Results_and_Reports")

render_dashboard_page = p1.render_dashboard_page
render_explore_parking_page = p2.render_explore_parking_page
render_optimize_allocation_page = p3.render_optimize_allocation_page
render_results_and_reports_page = p4.render_results_and_reports_page

# Functional Aliases matching Workflow Titles
render_parking_facilities_page = render_explore_parking_page
render_optimization_page = render_optimize_allocation_page
render_results_page = render_results_and_reports_page

# Backward Compatibility Aliases for Phase 5 & 6 Test Suites
render_overview_page = render_dashboard_page
render_dataset_analysis_page = render_explore_parking_page
render_optimization_model_page = render_optimize_allocation_page
render_optimized_allocation_page = render_results_and_reports_page
render_scenario_analysis_page = render_results_and_reports_page
render_reports_page = render_results_and_reports_page

__all__ = [
    # Modern 4-Section Architecture
    "render_dashboard_page",
    "render_explore_parking_page",
    "render_parking_facilities_page",
    "render_optimize_allocation_page",
    "render_optimization_page",
    "render_results_and_reports_page",
    "render_results_page",
    # Legacy Page Aliases
    "render_overview_page",
    "render_dataset_analysis_page",
    "render_optimization_model_page",
    "render_optimized_allocation_page",
    "render_scenario_analysis_page",
    "render_reports_page"
]
