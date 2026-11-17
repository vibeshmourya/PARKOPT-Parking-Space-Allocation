"""
test_phase3_experiments.py
Unit tests and mathematical robustness verification for Phase 3:
Experiment Engine, Sensitivity Analysis, Comparison Analysis, and Robustness/Edge Cases.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from data_loader import load_raw_data
from data_cleaning import clean_parking_data
from demand_estimation import estimate_facility_demand
from optimization_model import solve_parking_allocation_lp, compute_priority_weights
from experiment_engine import (
    run_experiment_grid,
    run_single_optimization_configuration,
    get_default_custom_weights
)
from sensitivity_analysis import run_budget_sensitivity_analysis
from comparison_analysis import (
    generate_demand_estimator_comparison,
    generate_priority_strategy_comparison
)


class TestPhase3Experiments(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        raw = load_raw_data()
        cls.clean_df, _ = clean_parking_data(raw)
        cls.demands_df = estimate_facility_demand(cls.clean_df, method="p95")
        cls.facility_names = cls.demands_df["SystemCodeNumber"].tolist()
        cls.capacities = cls.demands_df["Capacity"].tolist()
        cls.demands = cls.demands_df["EstimatedDemand"].tolist()
        cls.n = len(cls.facility_names)
        cls.allocatable_p95 = int(np.minimum(cls.demands, cls.capacities).sum())

    def test_experiment_grid_execution(self):
        """Verify experiment engine runs full 36-scenario grid with all optimal solutions."""
        exp_df = run_experiment_grid(
            self.clean_df,
            estimators=["mean", "p85", "p95", "max"],
            priorities=["equal", "congestion", "custom"],
            budget_scenarios=["low", "medium", "high"],
            output_dir="outputs"
        )
        self.assertEqual(len(exp_df), 36)
        self.assertTrue((exp_df["SolverStatus"] == "Optimal").all())
        # Budget utilization should be 100% since budget <= allocatable demand
        self.assertTrue((exp_df["BudgetUtilizationPct"] == 100.0).all())
        # Optimized objective must be >= baseline objective
        self.assertTrue((exp_df["ObjectiveGain"] >= -1e-4).all())

    def test_budget_sensitivity_monotonicity(self):
        """Verify that total allocated permits and objective value increase monotonically with budget."""
        sens_df, sat_info = run_budget_sensitivity_analysis(
            self.clean_df,
            demand_method="p95",
            priority_strategy="congestion",
            budget_fractions=[0.0, 0.25, 0.50, 0.75, 1.00],
            output_dir="outputs"
        )
        self.assertEqual(len(sens_df), 5)
        
        allocs = sens_df["OptimizedAllocated"].tolist()
        objs = sens_df["OptimizedObjective"].tolist()
        
        # Check monotonic non-decreasing
        for i in range(len(allocs) - 1):
            self.assertLessEqual(allocs[i], allocs[i+1])
            self.assertLessEqual(objs[i], objs[i+1])

    def test_budget_saturation_point(self):
        """Verify that beyond 100% allocatable demand, objective gains cease (marginal value = 0)."""
        sens_df, sat_info = run_budget_sensitivity_analysis(
            self.clean_df,
            demand_method="p95",
            priority_strategy="congestion",
            budget_fractions=[1.00, 1.10, 1.20],
            output_dir="outputs"
        )
        self.assertEqual(sat_info["saturation_budget_permits"], self.allocatable_p95)
        
        # At and beyond saturation, allocations should equal total allocatable demand
        for _, row in sens_df.iterrows():
            self.assertEqual(row["OptimizedAllocated"], self.allocatable_p95)
            self.assertEqual(row["FullySatisfiedFacilities"], self.n)
            self.assertEqual(row["ZeroAllocationFacilities"], 0)
            
        # Marginal value beyond 1.0 must be 0
        self.assertEqual(sens_df.iloc[1]["MarginalValuePerPermit"], 0.0)
        self.assertEqual(sens_df.iloc[2]["MarginalValuePerPermit"], 0.0)

    def test_estimator_comparison(self):
        """Verify estimator comparison across all 4 demand methods."""
        comp_df, summary = generate_demand_estimator_comparison(self.clean_df, output_dir="outputs")
        self.assertEqual(len(comp_df), 4)
        
        # Totals hierarchy: Mean <= P85 <= P95 <= Max
        self.assertLessEqual(summary["total_mean_demand"], summary["total_p85_demand"])
        self.assertLessEqual(summary["total_p85_demand"], summary["total_p95_demand"])
        self.assertLessEqual(summary["total_p95_demand"], summary["total_max_demand"])
        
        # Saturated facilities non-decreasing
        self.assertLessEqual(summary["saturated_facilities_mean"], summary["saturated_facilities_p85"])
        self.assertLessEqual(summary["saturated_facilities_p85"], summary["saturated_facilities_p95"])
        self.assertLessEqual(summary["saturated_facilities_p95"], summary["saturated_facilities_max"])

    def test_priority_strategy_comparison(self):
        """Verify priority comparison produces distinct weight vectors and valid solutions."""
        prio_df, summary = generate_priority_strategy_comparison(self.clean_df, output_dir="outputs")
        self.assertEqual(len(prio_df), 4)
        self.assertGreater(summary["objective_congestion"], 0)
        self.assertGreater(summary["objective_equal"], 0)
        self.assertGreater(summary["objective_custom"], 0)

    # --- Robustness and Edge Case Tests ---

    def test_edge_case_zero_budget(self):
        """Test with B = 0."""
        res = solve_parking_allocation_lp(
            facility_names=self.facility_names,
            capacities=self.capacities,
            demands=self.demands,
            budget=0,
            priority_scenario="equal"
        )
        self.assertEqual(res["solver_status"], "Optimal")
        self.assertEqual(res["objective_value"], 0.0)
        allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
        self.assertEqual(allocs, [0] * len(self.facility_names))

    def test_edge_case_very_small_budget(self):
        """Test with B = 5 permits."""
        weights = [1.0, 5.0, 2.0]
        res = solve_parking_allocation_lp(
            facility_names=["LotA", "LotB", "LotC"],
            capacities=[100, 100, 100],
            demands=[50, 50, 50],
            budget=5,
            priority_scenario="custom",
            weights=weights
        )
        self.assertEqual(res["solver_status"], "Optimal")
        allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
        # LotB has highest weight (5.0), so all 5 permits must go to LotB
        self.assertEqual(allocs, [0, 5, 0])
        self.assertEqual(res["objective_value"], 25.0)

    def test_edge_case_excess_budget_non_binding(self):
        """Test with budget far exceeding demand."""
        excess_budget = self.allocatable_p95 + 10000
        res = solve_parking_allocation_lp(
            facility_names=self.facility_names,
            capacities=self.capacities,
            demands=self.demands,
            budget=excess_budget,
            priority_scenario="equal"
        )
        self.assertEqual(res["solver_status"], "Optimal")
        self.assertFalse(res["is_binding"])
        allocs = res["allocations_df"]["OptimizedAllocation"].values
        expected = np.minimum(self.demands, self.capacities)
        np.testing.assert_array_equal(allocs, expected)

    def test_edge_case_zero_capacity_facility(self):
        """Test facility with C_i = 0."""
        res = solve_parking_allocation_lp(
            facility_names=["LotNormal", "LotZeroCap"],
            capacities=[100, 0],
            demands=[50, 50],
            budget=60,
            priority_scenario="equal"
        )
        self.assertEqual(res["solver_status"], "Optimal")
        allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
        self.assertEqual(allocs[1], 0)  # Zero-capacity lot must receive 0
        self.assertEqual(allocs[0], 50) # Normal lot capped at its demand (50)

    def test_edge_case_zero_demand_facility(self):
        """Test facility with d_i = 0."""
        res = solve_parking_allocation_lp(
            facility_names=["LotNormal", "LotZeroDem"],
            capacities=[100, 100],
            demands=[50, 0],
            budget=60,
            priority_scenario="equal"
        )
        self.assertEqual(res["solver_status"], "Optimal")
        allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
        self.assertEqual(allocs[1], 0)  # Zero-demand lot must receive 0
        self.assertEqual(allocs[0], 50)

    def test_edge_case_extreme_priority_weights(self):
        """Test extreme weights (e.g. w_i = 10,000)."""
        res = solve_parking_allocation_lp(
            facility_names=["LotLow", "LotMega"],
            capacities=[100, 100],
            demands=[50, 50],
            budget=40,
            priority_scenario="custom",
            weights=[1.0, 10000.0]
        )
        self.assertEqual(res["solver_status"], "Optimal")
        allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
        self.assertEqual(allocs, [0, 40])
        self.assertEqual(res["objective_value"], 400000.0)

    def test_edge_case_infeasible_minimum_allocation(self):
        """Test infeasible minimum requirements."""
        res = solve_parking_allocation_lp(
            facility_names=["LotA", "LotB"],
            capacities=[100, 100],
            demands=[50, 50],
            budget=40,
            priority_scenario="equal",
            min_allocations=[30, 30]  # Sum is 60 > budget 40
        )
        self.assertFalse(res["is_feasible"])
        self.assertIn("Infeasible", res["solver_status"])

    def test_edge_case_negative_priority_rejected(self):
        """Test that negative priority weights are rejected."""
        with self.assertRaises(ValueError):
            compute_priority_weights([100], [50], scenario="custom", custom_weights=[-1.0])


if __name__ == "__main__":
    unittest.main()

