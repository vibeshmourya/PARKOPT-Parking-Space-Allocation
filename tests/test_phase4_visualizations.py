"""
test_phase4_visualizations.py
Comprehensive unit tests for Phase 4:
Visualizations (Occupancy, Temporal, Optimization, Sensitivity),
Analytical Insights, Data Validation, and Edge Case Handling.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from data_loader import load_raw_data
from data_cleaning import clean_parking_data
from visualization.visualization_utils import validate_required_columns
from visualization.occupancy_charts import generate_all_occupancy_charts, plot_capacity_vs_average_occupancy
from visualization.temporal_charts import generate_all_temporal_charts, plot_hourly_occupancy_trend
from visualization.optimization_charts import generate_all_optimization_charts, plot_baseline_vs_optimized_allocation
from visualization.sensitivity_charts import generate_all_sensitivity_charts, plot_budget_vs_objective_and_unmet
from visualization.analytical_insights import compute_analytical_insights
from scenario_analysis import run_all_optimization_scenarios


class TestPhase4Visualizations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        raw = load_raw_data()
        cls.clean_df, _ = clean_parking_data(raw)
        cls.test_out_dir = "outputs/visualizations_test"
        os.makedirs(cls.test_out_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # Clean up test output directory
        if os.path.exists(cls.test_out_dir):
            import shutil
            shutil.rmtree(cls.test_out_dir)

    def test_required_input_files_exist(self):
        """Verify that all prerequisite CSV datasets exist in outputs/."""
        expected_csvs = [
            "outputs/parking_area_statistics.csv",
            "outputs/hourly_occupancy_trends.csv",
            "outputs/day_of_week_trends.csv",
            "outputs/baseline_comparison.csv",
            "outputs/priority_comparison.csv",
            "outputs/estimator_comparison.csv",
            "outputs/budget_sensitivity.csv",
            "outputs/scenario_comparison.csv"
        ]
        for path in expected_csvs:
            self.assertTrue(os.path.exists(path), f"Missing prerequisite file: {path}")

    def test_occupancy_charts_generation(self):
        """Verify all 4 occupancy charts generate PNG and HTML files."""
        out_sub = os.path.join(self.test_out_dir, "occupancy")
        res = generate_all_occupancy_charts(self.clean_df, output_dir=out_sub)
        self.assertEqual(len(res), 4)
        for chart_name, paths in res.items():
            self.assertTrue(os.path.exists(paths["png"]), f"Missing PNG for {chart_name}")
            self.assertTrue(os.path.exists(paths["html"]), f"Missing HTML for {chart_name}")
            self.assertGreater(os.path.getsize(paths["png"]), 20000, f"PNG too small for {chart_name}")
            self.assertGreater(os.path.getsize(paths["html"]), 5000, f"HTML too small for {chart_name}")

    def test_temporal_charts_generation(self):
        """Verify all 4 temporal charts generate PNG and HTML files."""
        out_sub = os.path.join(self.test_out_dir, "temporal")
        res = generate_all_temporal_charts(self.clean_df, output_dir=out_sub)
        self.assertEqual(len(res), 4)
        for chart_name, paths in res.items():
            self.assertTrue(os.path.exists(paths["png"]), f"Missing PNG for {chart_name}")
            self.assertTrue(os.path.exists(paths["html"]), f"Missing HTML for {chart_name}")

    def test_optimization_charts_generation(self):
        """Verify all 6 optimization result charts generate PNG and HTML files."""
        out_sub = os.path.join(self.test_out_dir, "optimization")
        res = generate_all_optimization_charts(output_dir=out_sub)
        self.assertEqual(len(res), 6)
        for chart_name, paths in res.items():
            self.assertTrue(os.path.exists(paths["png"]), f"Missing PNG for {chart_name}")
            self.assertTrue(os.path.exists(paths["html"]), f"Missing HTML for {chart_name}")

    def test_sensitivity_charts_generation(self):
        """Verify all 4 sensitivity charts generate PNG and HTML files."""
        out_sub = os.path.join(self.test_out_dir, "sensitivity")
        res = generate_all_sensitivity_charts(output_dir=out_sub)
        self.assertEqual(len(res), 4)
        for chart_name, paths in res.items():
            self.assertTrue(os.path.exists(paths["png"]), f"Missing PNG for {chart_name}")
            self.assertTrue(os.path.exists(paths["html"]), f"Missing HTML for {chart_name}")

    def test_analytical_insights_accuracy(self):
        """Verify analytical insights match underlying data values."""
        out_sub = os.path.join(self.test_out_dir, "insights")
        insights = compute_analytical_insights(output_dir=out_sub)
        
        # Verify markdown report written
        report_file = os.path.join(out_sub, "analytical_insights_report.md")
        self.assertTrue(os.path.exists(report_file))
        self.assertGreater(os.path.getsize(report_file), 1000)

        # Verify values
        stats_df = pd.read_csv("outputs/parking_area_statistics.csv")
        highest_lot = stats_df.sort_values(by="AvgUtilizationPct", ascending=False).iloc[0]["SystemCodeNumber"]
        self.assertEqual(insights["highest_utilization_facility"]["name"], highest_lot)
        self.assertEqual(len(insights["top_five_high_demand"]), 5)
        self.assertEqual(len(insights["top_five_underutilized"]), 5)
        self.assertGreater(insights["total_overflow_facilities_count"], 0)

    def test_empty_dataframe_validation(self):
        """Verify that passing an empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame()
        with self.assertRaises(ValueError):
            validate_required_columns(empty_df, ["SystemCodeNumber"], "TestEmpty")

    def test_missing_columns_validation(self):
        """Verify that missing columns raise descriptive ValueError."""
        bad_df = pd.DataFrame({"WrongColumn": [1, 2, 3]})
        with self.assertRaises(ValueError):
            validate_required_columns(bad_df, ["Capacity", "AvgOccupancy"], "TestMissing")

    def test_zero_capacity_facility_handling(self):
        """Verify that zero-capacity facility in data does not cause ZeroDivisionError."""
        stats_copy = pd.read_csv("outputs/parking_area_statistics.csv").head(5).copy()
        stats_copy.loc[0, "Capacity"] = 0
        stats_copy.loc[0, "AvgUtilizationPct"] = 0.0
        # Plot function should execute safely
        out_sub = os.path.join(self.test_out_dir, "zero_cap")
        res = plot_capacity_vs_average_occupancy(stats_copy, output_dir=out_sub)
        self.assertTrue(os.path.exists(res["png"]))

    def test_allocation_totals_consistency(self):
        """Verify that allocation totals in charts match optimization results."""
        comp_df = pd.read_csv("outputs/baseline_comparison.csv")
        total_base = comp_df["BaselineAllocation"].sum()
        total_opt = comp_df["OptimizedAllocation"].sum()
        # In baseline_comparison.csv, budget was 21,617
        self.assertEqual(total_base, 21617)
        self.assertEqual(total_opt, 21617)

    def test_canonical_scenarios_execution(self):
        """Verify that the 5 canonical scenarios produce valid summary results."""
        sum_df, fac_df, meta = run_all_optimization_scenarios(self.clean_df, output_dir=self.test_out_dir)
        self.assertEqual(len(sum_df), 5)
        self.assertEqual(len(fac_df), 30)
        # All scenarios should allocate full budget
        for _, row in sum_df.iterrows():
            self.assertEqual(row["TotalAllocated"], row["BudgetPermits"])


if __name__ == "__main__":
    unittest.main()
