"""
test_end_to_end.py
Phase 6: End-to-End Integration Pipeline Test Suite.
Validates the complete 12-stage Operations Research and analytics workflow from raw dataset to academic PDF.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import tempfile
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

for p in [PROJECT_ROOT, SRC_DIR, DASHBOARD_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from data_loader import load_raw_data
from data_cleaning import clean_parking_data
from exploratory_analysis import (
    get_parking_area_statistics,
    get_hourly_occupancy_trends,
    get_day_of_week_trends,
    get_overall_system_kpis
)
from demand_estimation import estimate_facility_demand
from baseline_allocation import compute_proportional_baseline
from optimization_model import (
    solve_parking_allocation_lp,
    compute_priority_weights,
    compare_optimization_with_baseline
)
from scenario_analysis import run_all_optimization_scenarios
from sensitivity_analysis import run_budget_sensitivity_analysis
from dashboard.utils.data_service import (
    load_cleaned_dataset,
    load_facility_statistics,
    load_demand_estimates,
    load_temporal_data,
    load_system_kpis,
    load_scenario_summaries,
    load_budget_sensitivity_data
)
from dashboard.utils.optimization_service import run_solver_workflow
from dashboard.utils.report_service import generate_academic_pdf_report
from dashboard.components.charts import (
    render_capacity_vs_occupancy_chart,
    render_baseline_vs_opt_chart,
    render_budget_sweep_chart
)


class TestCompleteEndToEndPipeline(unittest.TestCase):
    """Executes and verifies data flow across the complete 12-stage pipeline."""

    def test_complete_12_stage_pipeline(self):
        # -------------------------------------------------------------
        # Stage 1: Load Raw Dataset
        # -------------------------------------------------------------
        df_raw = load_raw_data()
        self.assertIsInstance(df_raw, pd.DataFrame)
        self.assertEqual(len(df_raw), 1000)
        for col in ["SystemCodeNumber", "Capacity", "Occupancy", "LastUpdated"]:
            self.assertIn(col, df_raw.columns)

        # -------------------------------------------------------------
        # Stage 2: Clean and Preprocess Records
        # -------------------------------------------------------------
        df_clean, report = clean_parking_data(df_raw)
        self.assertEqual(len(df_clean), 1000)
        self.assertEqual(report["key_duplicates_removed"], 0)
        self.assertEqual(report["negative_occupancy_count"], 0)
        self.assertTrue((df_clean["Occupancy_Cleaned"] >= 0).all())

        # -------------------------------------------------------------
        # Stage 3: Generate Exploratory Analysis Outputs
        # -------------------------------------------------------------
        area_stats = get_parking_area_statistics(df_clean)
        hourly_df = get_hourly_occupancy_trends(df_clean)
        day_df = get_day_of_week_trends(df_clean)
        kpis = get_overall_system_kpis(df_clean)

        self.assertEqual(len(area_stats), 4)
        self.assertEqual(len(day_df), 7)
        self.assertEqual(kpis["total_system_capacity"], 193)
        self.assertEqual(kpis["total_parking_areas"], 4)

        # -------------------------------------------------------------
        # Stage 4: Estimate Parking Demand (All 4 Methods)
        # -------------------------------------------------------------
        dem_mean = estimate_facility_demand(df_clean, method="mean")
        dem_p85 = estimate_facility_demand(df_clean, method="p85")
        dem_p95 = estimate_facility_demand(df_clean, method="p95")
        dem_max = estimate_facility_demand(df_clean, method="max")

        tot_mean = int(dem_mean["EstimatedDemand"].sum())
        tot_p85 = int(dem_p85["EstimatedDemand"].sum())
        tot_p95 = int(dem_p95["EstimatedDemand"].sum())
        tot_max = int(dem_max["EstimatedDemand"].sum())

        # Verify strict monotonic demand hierarchy
        self.assertLessEqual(tot_mean, tot_p85)
        self.assertLessEqual(tot_p85, tot_p95)
        self.assertLessEqual(tot_p95, tot_max)
        self.assertEqual(tot_p95, 116)

        # -------------------------------------------------------------
        # Stage 5 & 6: Solve LP Optimization & Proportional Baseline
        # -------------------------------------------------------------
        budget = 87 # ~75% of P95 demand
        opt_res, comp_df, comp_summary = run_solver_workflow(
            df_clean=df_clean,
            budget=budget,
            demand_method="p95",
            priority_scenario="congestion"
        )

        self.assertEqual(opt_res["status"], "Optimal")
        self.assertEqual(comp_summary["optimized_total_allocated"], budget)
        self.assertGreater(comp_summary["objective_improvement"], 0)
        self.assertGreater(comp_summary["objective_improvement_pct"], 0)

        # -------------------------------------------------------------
        # Stage 7: Canonical Scenarios Evaluation
        # -------------------------------------------------------------
        summary_scen, alloc_scen = load_scenario_summaries()
        self.assertEqual(len(summary_scen), 5)
        self.assertEqual(len(alloc_scen), 4)

        # -------------------------------------------------------------
        # Stage 8: Budget Sensitivity Analysis Sweep
        # -------------------------------------------------------------
        sens_df = load_budget_sensitivity_data()
        self.assertGreaterEqual(len(sens_df), 5)
        self.assertIn("Budget", sens_df.columns)
        self.assertIn("TotalAllocated", sens_df.columns)

        # -------------------------------------------------------------
        # Stage 9: Generate Interactive Visualizations
        # -------------------------------------------------------------
        fig_cap = render_capacity_vs_occupancy_chart(area_stats)
        fig_base = render_baseline_vs_opt_chart(comp_df)
        fig_sweep = render_budget_sweep_chart(sens_df)

        self.assertIsNotNone(fig_cap)
        self.assertIsNotNone(fig_base)
        self.assertIsNotNone(fig_sweep)

        # -------------------------------------------------------------
        # Stage 10: Streamlit Data Service Cache Verification
        # -------------------------------------------------------------
        cached_df = load_cleaned_dataset()
        self.assertEqual(len(cached_df), 1000)
        cached_kpis = load_system_kpis()
        self.assertEqual(cached_kpis["total_facilities"], 4)

        # -------------------------------------------------------------
        # Stage 11: Exported CSV Files Verification
        # -------------------------------------------------------------
        expected_csvs = [
            "parking_area_statistics.csv",
            "demand_estimates.csv",
            "baseline_comparison.csv",
            "optimization_results.csv",
            "budget_sensitivity.csv",
            "scenario_analysis_summary.csv",
            "scenario_facility_allocations.csv",
            "hourly_occupancy_trends.csv",
            "day_of_week_trends.csv"
        ]
        for fname in expected_csvs:
            fpath = os.path.join(OUTPUTS_DIR, fname)
            self.assertTrue(os.path.exists(fpath), f"Missing CSV: {fname}")
            self.assertGreater(os.path.getsize(fpath), 0, f"Empty CSV: {fname}")

        # -------------------------------------------------------------
        # Stage 12: Generate Academic PDF Report
        # -------------------------------------------------------------
        pdf_bytes = generate_academic_pdf_report(
            opt_result=opt_res,
            comp_df=comp_df,
            comp_summary=comp_summary,
            area_stats_df=area_stats,
            scenarios_summary_df=summary_scen,
            current_demand_method="p95",
            current_priority_scenario="congestion",
            current_budget=budget
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 5000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()

