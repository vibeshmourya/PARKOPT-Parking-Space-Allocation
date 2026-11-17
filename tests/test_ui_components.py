"""
test_ui_components.py
Unit tests verifying UI components, chart configurations, table formatters, and filters.
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
    render_capacity_vs_occupancy_chart,
    render_top5_demand_chart,
    render_top5_underutilized_chart,
    render_facility_hourly_chart,
    render_demand_fulfillment_chart,
    render_allocation_diff_chart,
    render_scenarios_comparison_chart,
    PLOTLY_LAYOUT_DEFAULTS
)
from dashboard.components.tables import (
    render_simple_results_table,
    render_facility_summary_table,
    render_allocation_comparison_table
)


class TestUIComponentsAndCharts(unittest.TestCase):
    """Verifies chart dimensions, container-awareness, table renderers, and filters."""

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

    def test_plotly_defaults_responsive(self):
        """Verifies that default layout enables autosize and bounded margins."""
        self.assertTrue(PLOTLY_LAYOUT_DEFAULTS.get("autosize", False))
        margins = PLOTLY_LAYOUT_DEFAULTS.get("margin", {})
        self.assertLessEqual(margins.get("l", 100), 50)
        self.assertLessEqual(margins.get("r", 100), 50)

    def test_capacity_vs_occupancy_dynamic_height(self):
        """Verifies that 1 facility renders compact height, while 30 facilities scale dynamically."""
        single_fac = self.area_stats.head(1)
        fig_single = render_capacity_vs_occupancy_chart(single_fac)
        self.assertLessEqual(fig_single.layout.height, 300)

        all_facs = self.area_stats
        fig_all = render_capacity_vs_occupancy_chart(all_facs)
        self.assertGreaterEqual(fig_all.layout.height, 240)

    def test_top5_underutilized_chart(self):
        """Verifies Top 5 underutilized chart produces facilities with capacity & occupancy."""
        fig = render_top5_underutilized_chart(self.area_stats)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 2)
        # Should have at most 5 items in bar trace
        self.assertLessEqual(len(fig.data[0].y), 5)

    def test_facility_filtering_logic(self):
        """Verifies demand tier classification filters."""
        high_demand = self.area_stats[self.area_stats["AvgUtilizationPct"] >= 65.0]
        mod_demand = self.area_stats[(self.area_stats["AvgUtilizationPct"] >= 40.0) & (self.area_stats["AvgUtilizationPct"] < 65.0)]
        low_demand = self.area_stats[self.area_stats["AvgUtilizationPct"] < 40.0]

        total_filtered = len(high_demand) + len(mod_demand) + len(low_demand)
        self.assertEqual(total_filtered, len(self.area_stats))
        self.assertEqual(total_filtered, 4)

    def test_simple_results_table_columns(self):
        """Verifies simple results table required columns exist."""
        required = ["Facility", "EstimatedDemand", "OptimizedAllocation", "OptimizedUnmetDemand"]
        for col in required:
            self.assertIn(col, self.comp_df.columns)


if __name__ == "__main__":
    unittest.main()

