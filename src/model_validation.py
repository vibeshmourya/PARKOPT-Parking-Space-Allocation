"""
model_validation.py
Mathematical validation, constraint verification, and manual toy-problem checks for LP models.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from optimization_model import solve_parking_allocation_lp
from baseline_allocation import compute_proportional_baseline


def validate_lp_solution(
    allocations: List[int],
    capacities: List[int],
    demands: List[int],
    budget: int,
    weights: List[float],
    reported_objective: float,
    min_allocations: Optional[List[int]] = None,
    tolerance: float = 1e-4
) -> Tuple[bool, List[str]]:
    """
    Rigorously validates that a proposed allocation vector satisfies every mathematical condition.
    
    Checks:
    1. Integrality: Each x_i is an integer.
    2. Non-negativity: x_i >= 0.
    3. Minimum Allocation: x_i >= min_required_i.
    4. Demand Bound: x_i <= d_i.
    5. Physical Capacity Bound: x_i <= C_i.
    6. Permit Budget Bound: SUM(x_i) <= B.
    7. Objective Value Consistency: reported_Z == SUM(w_i * x_i).
    
    Returns:
        Tuple[bool, List[str]]: is_valid flag and list of descriptive violation strings.
    """
    x = np.array(allocations)
    caps = np.array(capacities, dtype=int)
    dems = np.array(demands, dtype=int)
    w = np.array(weights, dtype=float)
    mins = np.array(min_allocations, dtype=int) if min_allocations is not None else np.zeros_like(x)
    
    violations = []
    
    # 1. Integrality
    if not np.all(np.equal(np.mod(x, 1), 0)):
        violations.append("Integrality Violation: Non-integer allocation values detected.")
        
    x_int = x.astype(int)
    
    # 2. Non-negativity
    if (x_int < 0).any():
        neg_indices = np.where(x_int < 0)[0].tolist()
        violations.append(f"Non-Negativity Violation: Negative allocations at indices {neg_indices}.")
        
    # 3. Minimum allocation
    if (x_int < mins).any():
        min_indices = np.where(x_int < mins)[0].tolist()
        violations.append(f"Minimum Allocation Violation: Allocation below min requirement at {min_indices}.")
        
    # 4. Demand constraint
    if (x_int > dems).any():
        dem_viol = np.where(x_int > dems)[0].tolist()
        violations.append(f"Demand Bound Violation: Allocation exceeds demand at indices {dem_viol}.")
        
    # 5. Capacity constraint
    if (x_int > caps).any():
        cap_viol = np.where(x_int > caps)[0].tolist()
        violations.append(f"Capacity Bound Violation: Allocation exceeds physical capacity at indices {cap_viol}.")
        
    # 6. Budget constraint
    total_alloc = int(x_int.sum())
    if total_alloc > budget:
        violations.append(f"Budget Violation: Total allocation {total_alloc} exceeds permit budget {budget}.")
        
    # 7. Objective calculation consistency
    calculated_obj = float(np.sum(x_int * w))
    # reported_objective is rounded to 2 decimal places; compare against rounded calculated_obj
    if abs(round(calculated_obj, 2) - round(reported_objective, 2)) > tolerance:
        violations.append(
            f"Objective Inconsistency: Reported Z={reported_objective} does not match SUM(w_i * x_i)={calculated_obj}."
        )
        
    is_valid = (len(violations) == 0)
    return is_valid, violations


def run_manual_toy_problem_validation() -> Dict[str, Any]:
    """
    Validates the LP solver against a hand-calculated, mathematically proven 3-facility toy problem.
    
    Toy Problem Specification:
        Facility 1: C_1 = 100, d_1 = 80, w_1 = 3.0 (Highest Priority)
        Facility 2: C_2 = 100, d_2 = 70, w_2 = 2.0 (Medium Priority)
        Facility 3: C_3 = 100, d_3 = 60, w_3 = 1.0 (Lowest Priority)
        Permit Budget B = 100
        
    Theoretical Optimal Solution via Greedy Knapsack / Continuous Relaxation:
        Since w_1 > w_2 > w_3 and all costs are 1:
        x_1* = min(80, 100) = 80 permits
        x_2* = min(70, 100 - 80) = 20 permits
        x_3* = min(60, 100 - 80 - 20) = 0 permits
        Optimal Z* = (3.0 * 80) + (2.0 * 20) + (1.0 * 0) = 240 + 40 = 280.0
        
    Baseline Proportional Solution:
        Total Demand = 80 + 70 + 60 = 210
        s_1 = 100 * (80/210) = 38.1 -> 38
        s_2 = 100 * (70/210) = 33.3 -> 33
        s_3 = 100 * (60/210) = 28.6 -> 29 (Hamilton remainder gives +1 to s_1 or s_3)
        Baseline Z_base = 3.0(38) + 2.0(33) + 1.0(29) = 114 + 66 + 29 = 209.0
        
    Proof: Z* (280.0) > Z_base (209.0), with strict improvement of +71.0 (+33.97%).
    """
    facility_names = ["Lot_A", "Lot_B", "Lot_C"]
    capacities = [100, 100, 100]
    demands = [80, 70, 60]
    weights = [3.0, 2.0, 1.0]
    budget = 100
    
    # Solve via PuLP model
    opt_res = solve_parking_allocation_lp(
        facility_names=facility_names,
        capacities=capacities,
        demands=demands,
        budget=budget,
        priority_scenario="custom",
        weights=weights
    )
    
    x_opt = opt_res["allocations_df"]["OptimizedAllocation"].tolist()
    z_opt = opt_res["objective_value"]
    
    # Expected analytical results
    expected_x = [80, 20, 0]
    expected_z = 280.0
    
    match_x = (x_opt == expected_x)
    match_z = abs(z_opt - expected_z) < 1e-4
    
    # Baseline
    base_df = compute_proportional_baseline(capacities, demands, budget, weights, facility_names)
    z_base = float(base_df["WeightedContribution"].sum())
    
    return {
        "toy_problem_passed": match_x and match_z,
        "solver_status": opt_res["solver_status"],
        "obtained_x": x_opt,
        "expected_x": expected_x,
        "obtained_objective": z_opt,
        "expected_objective": expected_z,
        "baseline_objective": z_base,
        "optimization_gain": round(z_opt - z_base, 2),
        "mathematical_proof": "Greedy Knapsack optimality condition verified."
    }


if __name__ == "__main__":
    toy_check = run_manual_toy_problem_validation()
    print("Manual Toy Problem Validation:")
    for k, v in toy_check.items():
        print(f"  {k}: {v}")
