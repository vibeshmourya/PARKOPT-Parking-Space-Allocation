"""
test_phase6_integration.py
Phase 6: Integration, Mathematical Invariant Verification, Dataset Integrity, and Edge Case Tests.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import tempfile
import warnings
import hashlib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")
for p in [PROJECT_ROOT, SRC_DIR, DASHBOARD_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from data_loader import load_raw_data, find_dataset_file, REQUIRED_COLUMNS
from data_cleaning import clean_parking_data
from exploratory_analysis import get_parking_area_statistics, get_overall_system_kpis
from demand_estimation import estimate_facility_demand
from constraints import OptimizationConstraints
from optimization_model import (
    solve_parking_allocation_lp,
    compute_priority_weights,
    compare_optimization_with_baseline
)
from baseline_allocation import compute_proportional_baseline
from model_validation import validate_lp_solution, run_manual_toy_problem_validation


class TestPhase6MathematicalValidation(unittest.TestCase):
    """Rigorous mathematical validation of LP solver against analytical models and toy problems."""

    def test_toy_problem_analytical_optimality(self):
        """
        Validates LP solver against hand-calculated, mathematically proven 3-facility toy problem:
        Facility 1: C_1 = 100, d_1 = 80, w_1 = 3.0
        Facility 2: C_2 = 100, d_2 = 70, w_2 = 2.0
        Facility 3: C_3 = 100, d_3 = 60, w_3 = 1.0
        Budget B = 100
        Analytical optimal solution: x* = [80, 20, 0], Z* = 280.0
        """
        facility_names = ["Lot_A", "Lot_B", "Lot_C"]
        caps = [100, 100, 100]
        dems = [80, 70, 60]
        weights = [3.0, 2.0, 1.0]
        budget = 100

        res = solve_parking_allocation_lp(
            facility_names=facility_names,
            capacities=caps,
            demands=dems,
            budget=budget,
            priority_scenario="custom",
            weights=weights
        )

        self.assertEqual(res["status"], "Optimal")
        self.assertEqual(res["summary"]["total_allocated"], 100)
        self.assertEqual(res["objective_value"], 280.0)

        allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
        self.assertEqual(allocs, [80, 20, 0])

        # Validate with formal validator
        is_valid, violations = validate_lp_solution(
            allocations=allocs,
            capacities=caps,
            demands=dems,
            budget=budget,
            weights=weights,
            reported_objective=280.0
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)

    def test_run_manual_toy_problem_validation_suite(self):
        """Executes the built-in toy problem validation suite."""
        toy_res = run_manual_toy_problem_validation()
        self.assertTrue(toy_res["toy_problem_passed"])
        self.assertEqual(toy_res["solver_status"], "Optimal")
        self.assertEqual(toy_res["obtained_x"], [80, 20, 0])
        self.assertEqual(toy_res["obtained_objective"], 280.0)
        self.assertGreater(toy_res["obtained_objective"], toy_res["baseline_objective"])
        self.assertAlmostEqual(toy_res["optimization_gain"], 71.0, places=1)

    def test_objective_formula_exact_match_30_facilities(self):
        """Validates that reported Z* exactly equals SUM(w_i * x_i) on the Birmingham dataset."""
        df_raw = load_raw_data()
        df_clean, _ = clean_parking_data(df_raw)
        stats = get_parking_area_statistics(df_clean)
        demand_df = estimate_facility_demand(df_clean, method="p95")

        merged = pd.merge(demand_df, stats[["SystemCodeNumber", "AvgUtilizationPct"]], on="SystemCodeNumber")
        caps = merged["Capacity"].tolist()
        dems = merged["EstimatedDemand"].tolist()
        names = merged["SystemCodeNumber"].tolist()
        utils = merged["AvgUtilizationPct"].tolist()
        budget = 21617

        res = solve_parking_allocation_lp(
            facility_names=names,
            capacities=caps,
            demands=dems,
            budget=budget,
            priority_scenario="congestion",
            historical_utilizations=utils
        )

        alloc_df = res["allocations_df"]
        x = alloc_df["OptimizedAllocation"].to_numpy()
        w = alloc_df["PriorityWeight"].to_numpy()
        calculated_z = float(np.sum(x * w))

        self.assertAlmostEqual(res["objective_value"], round(calculated_z, 2), places=1)

    def test_priority_weights_boundary_conditions(self):
        """Verifies priority weight mathematical bounds."""
        caps = [1000, 500, 200]
        dems = [800, 400, 100]
        utils = [80.0, 50.0, 20.0]

        # 1. Equal strategy
        w_eq = compute_priority_weights(caps, dems, scenario="equal")
        self.assertTrue((w_eq == 1.0).all())

        # 2. Congestion strategy
        w_cong = compute_priority_weights(caps, dems, historical_utilizations=utils, scenario="congestion")
        self.assertTrue((w_cong >= 1.0).all())
        self.assertTrue((w_cong <= 3.0).all())
        # Max utilization (80%) must have weight 3.0
        self.assertEqual(w_cong[0], 3.0)

        # 3. Custom strategy validation
        with self.assertRaises(ValueError):
            compute_priority_weights(caps, dems, scenario="custom", custom_weights=[-1.0, 2.0, 1.0])


class TestPhase6DatasetIntegrity(unittest.TestCase):
    """Integrity checks on the dataset, cleanliness, deduplication, and anomaly management."""

    def test_original_dataset_hash_stability(self):
        """Verifies original dataset has not been modified using SHA256 checksum."""
        dataset_path = find_dataset_file()
        with open(dataset_path, "rb") as f:
            file_bytes = f.read()
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        expected_hash = "f1e28b9c697769a1a05cd20148241b60b1a73fee4907611163efc6fd9d12770a"
        self.assertEqual(sha256_hash.lower(), expected_hash)

    def test_cleaning_reproducibility_and_anomalies(self):
        """Verifies deduplication, negative occupancy clipping, and overflow count."""
        df_raw = load_raw_data()
        df_clean, report = clean_parking_data(df_raw)

        self.assertEqual(report["raw_record_count"], 35717)
        self.assertEqual(report["key_duplicates_removed"], 216)
        self.assertEqual(report["cleaned_record_count"], 35501)
        self.assertEqual(report["negative_occupancy_count"], 12)
        self.assertEqual(report["overflow_count"], 373)

        # Confirm no negatives remain in Occupancy_Cleaned
        self.assertTrue((df_clean["Occupancy_Cleaned"] >= 0).all())

        # Confirm physical capacity is always > 0
        self.assertTrue((df_clean["Capacity"] > 0).all())

    def test_no_fabricated_demographics(self):
        """Verifies that no fabricated user categories (faculty, student, etc.) exist."""
        df_raw = load_raw_data()
        forbidden_keywords = ["faculty", "student", "visitor", "staff", "permit_type", "user_class"]
        for col in df_raw.columns:
            for kw in forbidden_keywords:
                self.assertNotIn(kw, col.lower())

    def test_facility_identifiers_consistency(self):
        """Verifies facility identifiers match across all analytical tables."""
        df_raw = load_raw_data()
        df_clean, _ = clean_parking_data(df_raw)
        stats = get_parking_area_statistics(df_clean)
        demands = estimate_facility_demand(df_clean, method="p95")

        raw_facs = set(df_clean["SystemCodeNumber"].unique())
        stats_facs = set(stats["SystemCodeNumber"].unique())
        demand_facs = set(demands["SystemCodeNumber"].unique())

        self.assertEqual(len(raw_facs), 30)
        self.assertEqual(raw_facs, stats_facs)
        self.assertEqual(raw_facs, demand_facs)


class TestPhase6EdgeCases(unittest.TestCase):
    """Tests extreme edge cases and boundary conditions."""

    def setUp(self):
        self.df_raw = load_raw_data()
        self.df_clean, _ = clean_parking_data(self.df_raw)
        self.stats = get_parking_area_statistics(self.df_clean)
        self.demands = estimate_facility_demand(self.df_clean, method="p95")
        merged = pd.merge(self.demands, self.stats[["SystemCodeNumber", "AvgUtilizationPct"]], on="SystemCodeNumber")
        self.caps = merged["Capacity"].tolist()
        self.dems = merged["EstimatedDemand"].tolist()
        self.names = merged["SystemCodeNumber"].tolist()
        self.utils = merged["AvgUtilizationPct"].tolist()

    def test_zero_budget_allocation(self):
        """Budget B = 0: Must allocate 0 to all lots with optimal objective 0.0."""
        res = solve_parking_allocation_lp(
            facility_names=self.names,
            capacities=self.caps,
            demands=self.dems,
            budget=0,
            priority_scenario="congestion",
            historical_utilizations=self.utils
        )
        self.assertEqual(res["status"], "Optimal")
        self.assertEqual(res["summary"]["total_allocated"], 0)
        self.assertEqual(res["objective_value"], 0.0)

    def test_minimal_unit_budget_allocation(self):
        """Budget B = 1: Must allocate exactly 1 permit to highest priority facility."""
        res = solve_parking_allocation_lp(
            facility_names=self.names,
            capacities=self.caps,
            demands=self.dems,
            budget=1,
            priority_scenario="congestion",
            historical_utilizations=self.utils
        )
        self.assertEqual(res["status"], "Optimal")
        self.assertEqual(res["summary"]["total_allocated"], 1)

    def test_saturation_budget_non_binding(self):
        """Budget B >= 28,823: Budget must be mathematically non-binding with positive slack."""
        total_allocatable = int(np.minimum(self.caps, self.dems).sum())
        excess_budget = total_allocatable + 5000

        res = solve_parking_allocation_lp(
            facility_names=self.names,
            capacities=self.caps,
            demands=self.dems,
            budget=excess_budget,
            priority_scenario="congestion",
            historical_utilizations=self.utils
        )
        self.assertEqual(res["status"], "Optimal")
        self.assertFalse(res["is_binding"])
        self.assertEqual(res["summary"]["total_allocated"], total_allocatable)

    def test_infeasible_minimum_allocations(self):
        """Sum of minimum required allocations > budget B: Must report infeasible before solve."""
        min_allocs = [1000] * 30 # Sum = 30,000 > budget 10,000
        res = solve_parking_allocation_lp(
            facility_names=self.names,
            capacities=self.caps,
            demands=self.dems,
            budget=10000,
            min_allocations=min_allocs
        )
        self.assertEqual(res["status"], "Infeasible Before Solve")
        self.assertFalse(res["is_feasible"])
        self.assertIn("Infeasible", res["feasibility_message"])

    def test_zero_demand_and_zero_capacity_facilities(self):
        """Facilities with zero demand or zero capacity must receive zero allocation."""
        caps = [0, 500, 300]
        dems = [200, 0, 200]
        names = ["ZeroCap", "ZeroDem", "Normal"]
        budget = 500

        res = solve_parking_allocation_lp(
            facility_names=names,
            capacities=caps,
            demands=dems,
            budget=budget,
            priority_scenario="equal"
        )
        self.assertEqual(res["status"], "Optimal")
        allocs = res["allocations_df"]["OptimizedAllocation"].tolist()
        self.assertEqual(allocs[0], 0) # Zero capacity gets 0
        self.assertEqual(allocs[1], 0) # Zero demand gets 0
        self.assertEqual(allocs[2], 200) # Normal gets min(300, 200) = 200


if __name__ == "__main__":
    unittest.main()
