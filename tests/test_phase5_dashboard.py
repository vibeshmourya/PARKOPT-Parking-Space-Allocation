"""
test_phase5_dashboard.py
Comprehensive unit tests for Phase 5:
Streamlit Dashboard components, utilities, data services, optimization workflows,
formatting helpers, PDF report compilation, and page routing.
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
    format_number, format_pct, format_status_badge, format_utilization_bar
)
from dashboard.utils.state_manager import init_session_state, get_state, set_state
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


class TestDashboardFormatting(unittest.TestCase):
    """Tests for UI formatting helpers."""

    def test_format_number(self):
        self.assertEqual(format_number(21617), "21,617")
        self.assertEqual(format_number(0), "0")
        self.assertEqual(format_number(1234.56, decimals=1), "1,234.6")
        self.assertEqual(format_number(None), "N/A")

    def test_format_pct(self):
        self.assertEqual(format_pct(44.59), "44.6%")
        self.assertEqual(format_pct(100.0, decimals=0), "100%")
        self.assertEqual(format_pct(None), "N/A")

    def test_format_status_badge(self):
        badge_opt = format_status_badge("Optimal")
        self.assertIn("Optimal", badge_opt)
        self.assertIn("#047857", badge_opt) # Emerald

        badge_infeas = format_status_badge("Infeasible")
        self.assertIn("Infeasible", badge_infeas)
        self.assertIn("#B91C1C", badge_infeas) # Crimson

    def test_format_utilization_bar(self):
        bar_html = format_utilization_bar(78.9)
        self.assertIn("78.9%", bar_html)
        self.assertIn("#EF4444", bar_html) # Red for high utilization


class TestDashboardDataService(unittest.TestCase):
    """Tests for cached data services."""

    def test_load_cleaned_dataset(self):
        df_clean = load_cleaned_dataset()
        self.assertIsInstance(df_clean, pd.DataFrame)
        self.assertEqual(len(df_clean), 1000)
        self.assertEqual(df_clean["SystemCodeNumber"].nunique(), 4)
        self.assertTrue((df_clean["Occupancy_Cleaned"] >= 0).all())

    def test_load_facility_statistics(self):
        area_stats = load_facility_statistics()
        self.assertIsInstance(area_stats, pd.DataFrame)
        self.assertEqual(len(area_stats), 4)
        required_cols = ["SystemCodeNumber", "Capacity", "AvgOccupancy", "AvgUtilizationPct"]
        for col in required_cols:
            self.assertIn(col, area_stats.columns)

    def test_load_demand_estimates(self):
        demands_p95 = load_demand_estimates("p95")
        self.assertEqual(len(demands_p95), 4)
        self.assertEqual(demands_p95["EstimatedDemand"].sum(), 116)

    def test_load_temporal_data(self):
        hourly_df, day_df = load_temporal_data()
        self.assertGreaterEqual(len(hourly_df), 10)
        self.assertEqual(len(day_df), 7)

    def test_load_system_kpis(self):
        kpis = load_system_kpis()
        self.assertEqual(kpis["total_facilities"], 4)
        self.assertEqual(kpis["total_system_capacity"], 193)
        self.assertGreaterEqual(kpis["total_observations"], 1000)

    def test_load_scenario_summaries(self):
        summary_df, alloc_df = load_scenario_summaries()
        self.assertEqual(len(summary_df), 5)
        self.assertEqual(len(alloc_df), 4)

    def test_load_budget_sensitivity_data(self):
        sens_df = load_budget_sensitivity_data()
        self.assertGreaterEqual(len(sens_df), 5)
        self.assertIn("Budget", sens_df.columns)
        self.assertIn("TotalAllocated", sens_df.columns)


class TestDashboardOptimizationService(unittest.TestCase):
    """Tests for optimization workflow orchestration."""

    def setUp(self):
        self.df_clean = load_cleaned_dataset()

    def test_run_solver_workflow(self):
        budget = 87
        opt_result, comp_df, comp_summary = run_solver_workflow(
            df_clean=self.df_clean,
            budget=budget,
            demand_method="p95",
            priority_scenario="congestion"
        )
        self.assertEqual(opt_result["status"], "Optimal")
        self.assertEqual(opt_result["summary"]["total_allocated"], budget)
        self.assertEqual(len(comp_df), 4)
        self.assertGreater(comp_summary["objective_improvement"], 0)
        self.assertGreater(comp_summary["objective_improvement_pct"], 0)

    def test_compute_facility_weights_preview(self):
        preview = compute_facility_weights_preview(self.df_clean, priority_scenario="congestion")
        self.assertEqual(len(preview), 4)
        self.assertTrue((preview["PriorityWeight"] >= 1.0).all())
        self.assertTrue((preview["PriorityWeight"] <= 3.0).all())


class TestDashboardReportService(unittest.TestCase):
    """Tests for ReportLab academic PDF generator."""

    def test_generate_academic_pdf_report(self):
        df_clean = load_cleaned_dataset()
        opt_result, comp_df, comp_summary = run_solver_workflow(
            df_clean=df_clean,
            budget=87,
            demand_method="p95",
            priority_scenario="congestion"
        )
        area_stats = load_facility_statistics(df_clean)
        summary_df, _ = load_scenario_summaries()

        pdf_bytes = generate_academic_pdf_report(
            opt_result=opt_result,
            comp_df=comp_df,
            comp_summary=comp_summary,
            area_stats_df=area_stats,
            scenarios_summary_df=summary_df,
            current_demand_method="p95",
            current_priority_scenario="congestion",
            current_budget=87
        )

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 4000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


class TestDashboardCharts(unittest.TestCase):
    """Tests for interactive Plotly charts."""

    def setUp(self):
        self.df_clean = load_cleaned_dataset()
        self.area_stats = load_facility_statistics(self.df_clean)
        self.hourly_df, self.day_df = load_temporal_data(self.df_clean)
        opt_result, self.comp_df, self.comp_summary = run_solver_workflow(
            df_clean=self.df_clean,
            budget=87,
            demand_method="p95",
            priority_scenario="congestion"
        )
        self.summary_df, _ = load_scenario_summaries()
        self.sens_df = load_budget_sensitivity_data()

    def test_occupancy_charts(self):
        fig1 = render_capacity_vs_occupancy_chart(self.area_stats)
        self.assertIsInstance(fig1, go.Figure)

        fig2 = render_utilization_ranking_chart(self.area_stats)
        self.assertIsInstance(fig2, go.Figure)

        fig3 = render_peak_vs_capacity_chart(self.area_stats)
        self.assertIsInstance(fig3, go.Figure)

    def test_temporal_charts(self):
        fig4 = render_temporal_diurnal_chart(self.hourly_df, self.day_df)
        self.assertIsInstance(fig4, go.Figure)

        fig5 = render_hourly_heatmap_chart(self.df_clean)
        self.assertIsInstance(fig5, go.Figure)

    def test_optimization_charts(self):
        fig6 = render_baseline_vs_opt_chart(self.comp_df)
        self.assertIsInstance(fig6, go.Figure)

        fig7 = render_demand_fulfillment_chart(self.comp_df)
        self.assertIsInstance(fig7, go.Figure)

        fig8 = render_allocation_diff_chart(self.comp_df)
        self.assertIsInstance(fig8, go.Figure)

    def test_sensitivity_charts(self):
        fig9 = render_budget_sweep_chart(self.sens_df)
        self.assertIsInstance(fig9, go.Figure)

        fig10 = render_marginal_return_chart(self.sens_df)
        self.assertIsInstance(fig10, go.Figure)

        fig11 = render_satisfaction_transitions_chart(self.sens_df)
        self.assertIsInstance(fig11, go.Figure)

        fig12 = render_scenarios_comparison_chart(self.summary_df)
        self.assertIsInstance(fig12, go.Figure)


class TestDashboardPagesRouting(unittest.TestCase):
    """Tests that all 6 page functions are importable, callable, and define proper entrypoints."""

    def test_page_callables(self):
        pages = [
            render_overview_page,
            render_dataset_analysis_page,
            render_optimization_model_page,
            render_optimized_allocation_page,
            render_scenario_analysis_page,
            render_reports_page
        ]
        for p in pages:
            self.assertTrue(callable(p))


if __name__ == "__main__":
    unittest.main()
