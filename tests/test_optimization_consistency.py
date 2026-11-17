"""
test_optimization_consistency.py
Unit tests verifying mathematical consistency, constraint satisfaction,
and solver correctness for the Linear Programming model and 5 canonical scenarios.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import tempfile
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

for p in [PROJECT_ROOT, SRC_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from data_loader import load_raw_data
from data_cleaning import clean_parking_data
from exploratory_analysis import get_parking_area_statistics
from demand_estimation import estimate_facility_demand
from optimization_model import solve_parking_allocation_lp, compare_optimization_with_baseline
from baseline_allocation import compute_proportional_baseline
from scenario_analysis import run_all_optimization_scenarios


class TestOptimizationConsistency(unittest.TestCase):
    """Verifies mathematical correctness and constraint satisfaction of the LP solver."""

    @classmethod
    def setUpClass(cls):
        df_raw = load_raw_data()
        cls.df_clean, _ = clean_parking_data(df_raw)
        cls.area_stats = get_parking_area_statistics(cls.df_clean)
        cls.demand_p95 = estimate_facility_demand(cls.df_clean, method="p95")
        
        merged = pd.merge(cls.area_stats[["SystemCodeNumber", "AvgUtilizationPct"]], cls.demand_p95, on="SystemCodeNumber")
        cls.names = merged["SystemCodeNumber"].tolist()
        cls.caps = merged["Capacity"].tolist()
        cls.dems = merged["EstimatedDemand"].tolist()
        cls.utils = merged["AvgUtilizationPct"].tolist()
        cls.budget = 87

    def test_lp_constraints_satisfaction(self):
        """Verifies that optimal allocations satisfy all 5 LP constraints."""
        opt_res = solve_parking_allocation_lp(
            facility_names=self.names,
            capacities=self.caps,
            demands=self.dems,
            budget=self.budget,
            priority_scenario="congestion",
            historical_utilizations=self.utils
        )
        self.assertEqual(opt_res["status"], "Optimal")
        
        allocs = opt_res["allocations_df"]["OptimizedAllocation"].values
        caps_arr = np.array(self.caps)
        dems_arr = np.array(self.dems)
        
        # 1. Total budget constraint
        self.assertLessEqual(int(allocs.sum()), self.budget)
        
        # 2. Physical capacity bounds
        self.assertTrue((allocs <= caps_arr).all(), "Allocations must not exceed physical capacity")
        
        # 3. Demand bounds
        self.assertTrue((allocs <= dems_arr).all(), "Allocations must not exceed estimated demand")
        
        # 4. Non-negativity
        self.assertTrue((allocs >= 0).all(), "Allocations must be non-negative")
        
        # 5. Integrality
        self.assertTrue(np.all(allocs == np.round(allocs)), "Allocations must be strictly integer")

    def test_optimization_dominates_proportional_baseline(self):
        """Verifies that LP objective Z* is strictly greater than or equal to baseline Z."""
        opt_res = solve_parking_allocation_lp(
            facility_names=self.names,
            capacities=self.caps,
            demands=self.dems,
            budget=self.budget,
            priority_scenario="congestion",
            historical_utilizations=self.utils
        )
        weights = opt_res["allocations_df"]["PriorityWeight"].tolist()
        base_df = compute_proportional_baseline(
            capacities=self.caps,
            demands=self.dems,
            budget=self.budget,
            weights=weights,
            facility_names=self.names
        )
        comp_df, comp_summary = compare_optimization_with_baseline(opt_res, base_df)
        
        self.assertGreater(comp_summary["optimized_objective_value"], comp_summary["baseline_objective_value"])
        self.assertGreater(comp_summary["objective_improvement"], 0)

    def test_all_five_scenarios_execution(self):
        """Verifies that all 5 canonical scenarios execute and return valid results."""
        summary_df, fac_df, meta = run_all_optimization_scenarios(self.df_clean)
        self.assertEqual(len(summary_df), 5)
        self.assertEqual(len(fac_df), 4)
        
        expected_scenarios = [
            "1. Existing Baseline",
            "2. Demand-Based Optimization",
            "3. Priority-Based Optimization",
            "4. Capacity Reduction Scenario",
            "5. Peak Demand Scenario"
        ]
        for name in expected_scenarios:
            self.assertIn(name, summary_df["ScenarioName"].tolist())


if __name__ == "__main__":
    unittest.main()

