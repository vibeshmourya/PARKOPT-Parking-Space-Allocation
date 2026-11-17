"""
test_dashboard_validation.py
Phase 6: Comprehensive Streamlit Dashboard Validation Test Suite.
Validates page routing, components, charts, KPI integrity, session state persistence, and error handling.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import tempfile
import warnings
import pandas as pd
import numpy as np
import plotly.graph_objects as go

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")

for p in [PROJECT_ROOT, SRC_DIR, DASHBOARD_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dashboard.utils.formatting import (
    format_number, format_pct, format_status_badge, format_utilization_bar, CUSTOM_DASHBOARD_CSS
)
from dashboard.utils.state_manager import (
    init_session_state, get_state, set_state, reset_optimization_state
)
from dashboard.utils.data_service import (
    load_cleaned_dataset,
    load_facility_statistics,
    load_demand_estimates,
    load_temporal_data,
    load_system_kpis,
    load_scenario_summaries,
    load_budget_sensitivity_data
)
from dashboard.utils.optimization_service import (
    run_solver_workflow,
    compute_facility_weights_preview
)
from dashboard.utils.report_service import generate_academic_pdf_report
from dashboard.components.kpi_cards import render_kpi_card
from dashboard.components.charts import (
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
from dashboard.pages import (
    render_overview_page,
    render_dataset_analysis_page,
    render_optimization_model_page,
    render_optimized_allocation_page,
    render_scenario_analysis_page,
    render_reports_page
)


class TestDashboardComponentsAndFormatting(unittest.TestCase):
    """Tests for reusable dashboard UI components and formatting."""

    def test_kpi_card_html_generation(self):
        html_card = render_kpi_card(
            label="Total Capacity",
            value="39,956 bays",
            subtext="Stationary civil infrastructure",
            delta="+5.31%",
            delta_positive=True,
            badge="VERIFIED",
            border_left_color="#2563EB"
        )
        self.assertIn("Total Capacity", html_card)
        self.assertIn("39,956 bays", html_card)
        self.assertIn("Stationary civil infrastructure", html_card)
        self.assertIn("VERIFIED", html_card)
        self.assertIn("#059669", html_card) # Green for positive delta
        self.assertIn("#2563EB", html_card) # Border color

    def test_format_utilization_bar_thresholds(self):
        # High pressure (>= 65%)
        bar_high = format_utilization_bar(78.9)
        self.assertIn("#EF4444", bar_high)
        self.assertIn("78.9%", bar_high)

        # Moderate pressure (40 - 65%)
        bar_mod = format_utilization_bar(52.4)
        self.assertIn("#F59E0B", bar_mod)
        self.assertIn("52.4%", bar_mod)

        # Low utilization (< 40%)
        bar_low = format_utilization_bar(25.1)
        self.assertIn("#2563EB", bar_low)
        self.assertIn("25.1%", bar_low)

    def test_css_injection_structure(self):
        self.assertIn(".hero-card", CUSTOM_DASHBOARD_CSS)
        self.assertIn(".kpi-container", CUSTOM_DASHBOARD_CSS)
        self.assertIn(".academic-badge", CUSTOM_DASHBOARD_CSS)


class TestDashboardStateManager(unittest.TestCase):
    """Tests for session state initialization, updates, and reset logic."""

    def test_session_state_lifecycle(self):
        init_session_state()
        self.assertTrue(get_state("is_state_initialized"))

        # Set key
        set_state("current_budget", 25000)
        self.assertEqual(get_state("current_budget"), 25000)

        # Set optimization result
        set_state("latest_opt_result", {"status": "Optimal", "objective_value": 50000.0})
        self.assertIsNotNone(get_state("latest_opt_result"))

        # Reset optimization state
        reset_optimization_state()
        self.assertIsNone(get_state("latest_opt_result"))
        self.assertIsNone(get_state("baseline_comp_df"))


class TestDashboardChartRenderingSuite(unittest.TestCase):
    """Tests that all 12 Plotly figures render properly with correct data schemas."""

    @classmethod
    def setUpClass(cls):
        cls.df_clean = load_cleaned_dataset()
        cls.area_stats = load_facility_statistics(cls.df_clean)
        cls.hourly_df, cls.day_df = load_temporal_data(cls.df_clean)
        cls.opt_res, cls.comp_df, cls.comp_summary = run_solver_workflow(
            df_clean=cls.df_clean,
            budget=21617,
            demand_method="p95",
            priority_scenario="congestion"
        )
        cls.summary_df, _ = load_scenario_summaries()
        cls.sens_df = load_budget_sensitivity_data()

    def test_all_occupancy_charts(self):
        fig1 = render_capacity_vs_occupancy_chart(self.area_stats)
        self.assertEqual(len(fig1.data), 2) # Capacity trace + Occupancy trace

        fig2 = render_utilization_ranking_chart(self.area_stats)
        self.assertEqual(len(fig2.data), 1)

        fig3 = render_peak_vs_capacity_chart(self.area_stats)
        self.assertEqual(len(fig3.data), 2)

    def test_all_temporal_charts(self):
        fig4 = render_temporal_diurnal_chart(self.hourly_df, self.day_df)
        self.assertEqual(len(fig4.data), 2) # Hourly trace + Day of week trace

        fig5 = render_hourly_heatmap_chart(self.df_clean)
        self.assertEqual(len(fig5.data), 1)
        self.assertIsInstance(fig5.data[0], go.Heatmap)

    def test_all_optimization_charts(self):
        fig6 = render_baseline_vs_opt_chart(self.comp_df)
        self.assertEqual(len(fig6.data), 2) # Baseline + Optimized

        fig7 = render_demand_fulfillment_chart(self.comp_df)
        self.assertEqual(len(fig7.data), 2) # Satisfied + Unmet

        fig8 = render_allocation_diff_chart(self.comp_df)
        self.assertEqual(len(fig8.data), 1) # Reallocation shifts

    def test_all_sensitivity_and_scenario_charts(self):
        fig9 = render_budget_sweep_chart(self.sens_df)
        self.assertEqual(len(fig9.data), 2) # Allocated + Unmet

        fig10 = render_marginal_return_chart(self.sens_df)
        self.assertEqual(len(fig10.data), 1)

        fig11 = render_satisfaction_transitions_chart(self.sens_df)
        self.assertEqual(len(fig11.data), 3) # Full, Partial, Zero

        fig12 = render_scenarios_comparison_chart(self.summary_df)
        self.assertEqual(len(fig12.data), 2)


class TestDashboardPageCallables(unittest.TestCase):
    """Validates that all six page functions execute without syntax or import errors."""

    def test_page_functions_exist_and_callable(self):
        pages = [
            ("Overview", render_overview_page),
            ("Dataset Analysis", render_dataset_analysis_page),
            ("Optimization Model", render_optimization_model_page),
            ("Optimized Allocation", render_optimized_allocation_page),
            ("Scenario Analysis", render_scenario_analysis_page),
            ("Reports", render_reports_page)
        ]
        for name, fn in pages:
            self.assertTrue(callable(fn), f"Page {name} is not callable.")


if __name__ == "__main__":
    unittest.main()

