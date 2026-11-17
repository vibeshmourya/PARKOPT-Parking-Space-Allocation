"""
test_ui_redesign.py
Unit tests verifying the PARKOPT UI/UX Redesign:
- 4-section navigation architecture
- New chart renderers (Top 5 high-demand, utilization distribution, facility hourly curve)
- Clean results table
- Backward-compatibility aliases and page callables
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import tempfile
import warnings
import pandas as pd
import plotly.graph_objects as go

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")

for p in [PROJECT_ROOT, SRC_DIR, DASHBOARD_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dashboard.utils.data_service import (
    load_cleaned_dataset,
    load_facility_statistics
)
from dashboard.utils.optimization_service import run_solver_workflow
from dashboard.components.charts import (
    render_top5_demand_chart,
    render_utilization_distribution_chart,
    render_facility_hourly_chart,
    render_demand_vs_recommended_chart,
    render_reallocation_shifts_chart
)
from dashboard.pages import (
    render_dashboard_page,
    render_explore_parking_page,
    render_optimize_allocation_page,
    render_results_and_reports_page,
    render_overview_page,
    render_dataset_analysis_page,
    render_optimization_model_page,
    render_optimized_allocation_page
)


class TestUIRedesignArchitecture(unittest.TestCase):
    """Verifies that all redesigned 4 pages and aliases exist and are callable."""

    def test_new_page_callables(self):
        pages = [
            render_dashboard_page,
            render_explore_parking_page,
            render_optimize_allocation_page,
            render_results_and_reports_page
        ]
        for page_fn in pages:
            self.assertTrue(callable(page_fn), f"{page_fn} must be callable")

    def test_legacy_aliases_compatibility(self):
        self.assertEqual(render_overview_page, render_dashboard_page)
        self.assertEqual(render_dataset_analysis_page, render_explore_parking_page)
        self.assertEqual(render_optimization_model_page, render_optimize_allocation_page)
        self.assertEqual(render_optimized_allocation_page, render_results_and_reports_page)


class TestRedesignedCharts(unittest.TestCase):
    """Verifies output figures of newly designed clean charts."""

    @classmethod
    def setUpClass(cls):
        cls.df_clean = load_cleaned_dataset()
        cls.area_stats = load_facility_statistics(cls.df_clean)
        cls.opt_result, cls.comp_df, cls.comp_summary = run_solver_workflow(
            df_clean=cls.df_clean,
            budget=87,
            demand_method="p95",
            priority_scenario="congestion"
        )

    def test_top5_demand_chart(self):
        fig = render_top5_demand_chart(self.area_stats)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 2) # Capacity trace + Avg Occupancy trace

    def test_utilization_distribution_chart(self):
        fig = render_utilization_distribution_chart(self.area_stats)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 1)
        # Sum of tier counts should be 4 facilities
        total_facilities_in_chart = sum(fig.data[0].y)
        self.assertEqual(total_facilities_in_chart, 4)

    def test_facility_hourly_chart_system(self):
        fig_sys = render_facility_hourly_chart(self.df_clean, facility_code=None)
        self.assertIsInstance(fig_sys, go.Figure)
        self.assertIn("Hourly Parking Demand Pattern", fig_sys.layout.title.text)

    def test_facility_hourly_chart_single_facility(self):
        sample_facility = self.area_stats.iloc[0]["SystemCodeNumber"]
        fig_fac = render_facility_hourly_chart(self.df_clean, facility_code=sample_facility)
        self.assertIsInstance(fig_fac, go.Figure)
        self.assertIn(sample_facility, fig_fac.layout.title.text)

    def test_demand_vs_recommended_chart(self):
        fig = render_demand_vs_recommended_chart(self.comp_df)
        self.assertIsInstance(fig, go.Figure)

    def test_reallocation_shifts_chart(self):
        fig = render_reallocation_shifts_chart(self.comp_df)
        self.assertIsInstance(fig, go.Figure)


if __name__ == "__main__":
    unittest.main()

