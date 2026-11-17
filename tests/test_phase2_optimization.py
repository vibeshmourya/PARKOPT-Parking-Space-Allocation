"""
test_phase2_optimization.py
Comprehensive unit tests and mathematical validation for Phase 2:
Demand estimation, constraint enforcement, PuLP LP solver, baseline comparison, and toy proof.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from data_loader import load_raw_data
from data_cleaning import clean_parking_data
from demand_estimation import estimate_facility_demand, get_demand_summary_statistics
from constraints import OptimizationConstraints
from baseline_allocation import compute_proportional_baseline
from optimization_model import (
    compute_priority_weights,
    solve_parking_allocation_lp,
    compare_optimization_with_baseline
)
from model_validation import validate_lp_solution, run_manual_toy_problem_validation


class TestPhase2Optimization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        raw = load_raw_data()
        cls.clean_df, _ = clean_parking_data(raw)
        cls.demands_df = estimate_facility_demand(cls.clean_df, method="p95")
        cls.facility_names = cls.demands_df["SystemCodeNumber"].tolist()
        cls.capacities = cls.demands_df["Capacity"].tolist()
        cls.demands = cls.demands_df["EstimatedDemand"].tolist()
        cls.n = len(cls.facility_names)
        cls.total_allocatable = int(np.minimum(cls.demands, cls.capacities).sum())

    def test_demand_estimation_monotonicity(self):
        """Verify that Mean <= P85 <= P95 <= Max demand for every facility."""
        d_df = self.demands_df
        for _, row in d_df.iterrows():
            self.assertLessEqual(row["MeanDemand"], row["P85Demand"] + 1e-4)
            self.assertLessEqual(row["P85Demand"], row["P95Demand"] + 1e-4)
            self.assertLessEqual(row["P95Demand"], row["MaxDemand"] + 1e-4)

    def test_equal_priority_weights(self):
        """Verify that equal priority assigns 1.0 to all facilities."""
        w = compute_priority_weights(self.capacities, self.demands, scenario="equal")
        self.assertEqual(len(w), self.n)
        self.assertTrue((w == 1.0).all())

    def test_congestion_priority_weights_range(self):
        """Verify that congestion priority weights are within [1.0, 3.0]."""
        w = compute_priority_weights(self.capacities, self.demands, scenario="congestion")
        self.assertEqual(len(w), self.n)
        self.assertTrue((w >= 1.0).all())
        self.assertTrue((w <= 3.0).all())

    def test_manual_toy_problem_optimality(self):
        """Verify that the PuLP solver solves the 3-facility toy problem with theoretical optimality."""
        toy_res = run_manual_toy_problem_validation()
        self.assertTrue(toy_res["toy_problem_passed"])
        self.assertEqual(toy_res["obtained_x"], [80, 20, 0])
        self.assertAlmostEqual(toy_res["obtained_objective"], 280.0, places=4)
        self.assertGreater(toy_res["obtained_objective"], toy_res["baseline_objective"])

    def test_lp_solver_optimal_medium_budget(self):
        """Verify that the solver returns Optimal status and satisfies all constraints under medium budget."""
        budget = int(round(self.total_allocatable * 0.75))
        res = solve_parking_allocation_lp(
            facility_names=self.facility_names,
            capacities=self.capacities,
            demands=self.demands,
            budget=budget,
            priority_scenario="congestion"
        )
        self.assertEqual(res["solver_status"], "Optimal")
        self.assertTrue(res["is_feasible"])
        self.assertTrue(res["is_binding"])

        # Validate with independent validator
        allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
        weights = res["allocations_df"]["PriorityWeight"].tolist()
        is_valid, violations = validate_lp_solution(
            allocations=allocs,
            capacities=self.capacities,
            demands=self.demands,
            budget=budget,
            weights=weights,
            reported_objective=res["objective_value"]
        )
        self.assertTrue(is_valid, f"Violations detected: {violations}")

    def test_lp_solver_low_and_high_budgets(self):
        """Verify solver under low (50%) and high (90%) budget scenarios."""
        for frac in [0.50, 0.90]:
            budget = int(round(self.total_allocatable * frac))
            res = solve_parking_allocation_lp(
                facility_names=self.facility_names,
                capacities=self.capacities,
                demands=self.demands,
                budget=budget,
                priority_scenario="congestion"
            )
            self.assertEqual(res["solver_status"], "Optimal")
            allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
            weights = res["allocations_df"]["PriorityWeight"].tolist()
            is_valid, violations = validate_lp_solution(
                allocations=allocs,
                capacities=self.capacities,
                demands=self.demands,
                budget=budget,
                weights=weights,
                reported_objective=res["objective_value"]
            )
            self.assertTrue(is_valid, f"Violations for fraction {frac}: {violations}")

    def test_lp_solver_equal_priority_solution(self):
        """Verify that under equal priority (w_i=1), total allocation equals the budget."""
        budget = int(round(self.total_allocatable * 0.75))
        res = solve_parking_allocation_lp(
            facility_names=self.facility_names,
            capacities=self.capacities,
            demands=self.demands,
            budget=budget,
            priority_scenario="equal"
        )
        self.assertEqual(res["solver_status"], "Optimal")
        total_alloc = res["allocations_df"]["OptimizedAllocation"].sum()
        self.assertEqual(total_alloc, budget)
        self.assertAlmostEqual(res["objective_value"], float(budget), places=2)

    def test_non_binding_budget_handling(self):
        """Verify that when B >= total allocatable demand, non-binding status is detected."""
        excess_budget = self.total_allocatable + 5000
        res = solve_parking_allocation_lp(
            facility_names=self.facility_names,
            capacities=self.capacities,
            demands=self.demands,
            budget=excess_budget,
            priority_scenario="congestion"
        )
        self.assertEqual(res["solver_status"], "Optimal")
        self.assertFalse(res["is_binding"])
        # Each lot receives min(d_i, C_i)
        allocs = res["allocations_df"]["OptimizedAllocation"].values
        expected = np.minimum(self.demands, self.capacities)
        np.testing.assert_array_equal(allocs, expected)

    def test_infeasible_scenario_handling(self):
        """Verify that impossible minimum allocation constraints trigger Infeasible status."""
        # Impose min allocations that exceed budget
        impossible_mins = [5000] * self.n  # sum is 150,000, far exceeds budget 10,000
        res = solve_parking_allocation_lp(
            facility_names=self.facility_names,
            capacities=self.capacities,
            demands=self.demands,
            budget=10000,
            priority_scenario="equal",
            min_allocations=impossible_mins
        )
        self.assertFalse(res["is_feasible"])
        self.assertIn("Infeasible", res["solver_status"])

    def test_baseline_comparison_optimality_gain(self):
        """Verify that optimized allocation achieves >= objective value compared to baseline."""
        budget = int(round(self.total_allocatable * 0.75))
        res = solve_parking_allocation_lp(
            facility_names=self.facility_names,
            capacities=self.capacities,
            demands=self.demands,
            budget=budget,
            priority_scenario="congestion"
        )
        weights = res["allocations_df"]["PriorityWeight"].tolist()
        base_df = compute_proportional_baseline(
            capacities=self.capacities,
            demands=self.demands,
            budget=budget,
            weights=weights,
            facility_names=self.facility_names
        )
        comp_df, comp_summary = compare_optimization_with_baseline(res, base_df)

        # Baseline and optimized both respect budget
        self.assertEqual(comp_summary["baseline_total_allocated"], budget)
        self.assertEqual(comp_summary["optimized_total_allocated"], budget)

        # Optimized objective must be strictly greater than or equal to baseline
        self.assertGreaterEqual(
            comp_summary["optimized_objective_value"],
            comp_summary["baseline_objective_value"]
        )


if __name__ == "__main__":
    unittest.main()
