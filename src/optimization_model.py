"""
optimization_model.py
Linear Programming optimization solver for Managed Parking Permit Allocation using PuLP.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import pulp

from constraints import OptimizationConstraints
from baseline_allocation import compute_proportional_baseline


PRIORITY_SCENARIOS = ["equal", "congestion", "custom"]
DEFAULT_PRIORITY_SCENARIO = "congestion"


def compute_priority_weights(
    capacities: List[int],
    demands: List[int],
    historical_utilizations: Optional[List[float]] = None,
    scenario: str = DEFAULT_PRIORITY_SCENARIO,
    custom_weights: Optional[List[float]] = None
) -> np.ndarray:
    """
    Computes priority weights (w_i) for each facility under three transparent scenarios:
    
    1. 'equal': Every facility receives an identical weight of 1.0.
       Objective becomes maximizing total permits allocated: Max Z = SUM(x_i).
       
    2. 'congestion': Priority scales with historical occupancy pressure.
       Formula: w_i = 1.0 + 2.0 * (utilization_i / max_utilization)
       Weights lie strictly in [1.0, 3.0]. High-pressure bottleneck lots receive
       weight up to 3.0, prioritizing permit relief where congestion is severe.
       
    3. 'custom': User-configured weights.
    
    No demographic categories (faculty, students, visitors) are assumed.
    """
    scenario = scenario.lower()
    n = len(capacities)
    
    if scenario == "equal":
        return np.ones(n, dtype=float)
        
    elif scenario == "congestion":
        if historical_utilizations is not None and len(historical_utilizations) == n:
            utils = np.array(historical_utilizations, dtype=float)
        else:
            # Fallback to demand/capacity ratio if historical utilization not explicitly passed
            caps = np.array(capacities, dtype=float)
            dems = np.array(demands, dtype=float)
            utils = np.where(caps > 0, dems / caps, 0.0)
            
        max_u = np.max(utils) if np.max(utils) > 0 else 1.0
        # Scaled weights between 1.0 and 3.0
        weights = 1.0 + 2.0 * (utils / max_u)
        return np.round(weights, 4)
        
    elif scenario == "custom":
        if custom_weights is None or len(custom_weights) != n:
            raise ValueError(f"Custom weights list of length {n} must be provided for scenario 'custom'.")
        c_weights = np.array(custom_weights, dtype=float)
        if (c_weights < 0).any():
            raise ValueError("Priority weights must be non-negative.")
        return np.round(c_weights, 4)
        
    else:
        raise ValueError(f"Unknown priority scenario '{scenario}'. Choose from {PRIORITY_SCENARIOS}.")


def solve_parking_allocation_lp(
    facility_names: List[str],
    capacities: List[int],
    demands: List[int],
    budget: int,
    priority_scenario: str = DEFAULT_PRIORITY_SCENARIO,
    weights: Optional[List[float]] = None,
    historical_utilizations: Optional[List[float]] = None,
    min_allocations: Optional[List[int]] = None,
    solver_time_limit: int = 30
) -> Dict[str, Any]:
    """
    Formulates and solves the Integer Linear Programming model using PuLP.
    
    Decision Variables:
        x_i: Integer number of managed parking permits allocated to facility i.
        
    Objective:
        Maximize Z = SUM(w_i * x_i)
        
    Constraints:
        1. SUM(x_i) <= B             (Permit Allocation Budget)
        2. x_i <= d_i                (Estimated Demand Bound, for each i)
        3. x_i <= C_i                (Physical Capacity Bound, for each i)
        4. x_i >= min_required_i     (Minimum Allocation, for each i)
        5. x_i in Z, x_i >= 0        (Non-negative Integers, for each i)
        
    Returns:
        Dict[str, Any]: Comprehensive result package with solver status, objective,
                        allocations, slack variables, and constraint reports.
    """
    n = len(facility_names)
    caps = np.array(capacities, dtype=int)
    dems = np.array(demands, dtype=int)
    b = int(budget)
    
    # 1. Compute priority weights
    w = compute_priority_weights(
        capacities=capacities,
        demands=demands,
        historical_utilizations=historical_utilizations,
        scenario=priority_scenario,
        custom_weights=weights
    )

    # 2. Check mathematical constraints and feasibility
    constraints_mgr = OptimizationConstraints(
        capacities=caps,
        demands=dems,
        budget=b,
        facility_names=facility_names,
        min_allocations=min_allocations
    )
    is_feasible, feas_msg = constraints_mgr.check_feasibility()
    is_binding, binding_msg = constraints_mgr.is_budget_binding()

    if not is_feasible:
        return {
            "status": "Infeasible Before Solve",
            "solver_status": "Infeasible",
            "objective_value": 0.0,
            "is_feasible": False,
            "feasibility_message": feas_msg,
            "is_binding": False,
            "binding_message": binding_msg,
            "allocations_df": pd.DataFrame(),
            "summary": {}
        }

    # 3. Formulate the PuLP Optimization Problem
    prob = pulp.LpProblem("Optimal_Parking_Permit_Allocation", pulp.LpMaximize)

    # 4. Decision Variables: x_i in Z, x_i >= 0
    # PuLP allows specifying upper bounds directly on variables as well as explicit constraints
    x_vars = {}
    for i, name in enumerate(facility_names):
        var_name = f"x_{i:02d}_{name.replace(' ', '_').replace('-', '_')}"
        lower_b = int(constraints_mgr.min_allocations[i])
        upper_b = int(min(dems[i], caps[i]))
        x_vars[i] = pulp.LpVariable(
            name=var_name,
            lowBound=lower_b,
            upBound=upper_b,
            cat=pulp.LpInteger
        )

    # 5. Objective Function: Maximize Z = SUM(w_i * x_i)
    prob += pulp.lpSum([w[i] * x_vars[i] for i in range(n)]), "Total_Weighted_Demand_Served"

    # 6. Explicit Constraints
    # A. Permit Allocation Budget Constraint: SUM(x_i) <= B
    prob += pulp.lpSum([x_vars[i] for i in range(n)]) <= b, "Total_Permit_Budget_Constraint"

    # B. Demand & Capacity Constraints are enforced via variable bounds and explicit constraints
    for i in range(n):
        prob += x_vars[i] <= dems[i], f"Demand_Bound_{i}"
        prob += x_vars[i] <= caps[i], f"Capacity_Bound_{i}"
        if constraints_mgr.min_allocations[i] > 0:
            prob += x_vars[i] >= constraints_mgr.min_allocations[i], f"Min_Allocation_Bound_{i}"

    # 7. Execute Solver
    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=solver_time_limit)
    prob.solve(solver)

    status_str = pulp.LpStatus[prob.status]
    is_optimal = (status_str == "Optimal")

    # 8. Extract Solution Values
    allocations = np.zeros(n, dtype=int)
    if is_optimal:
        for i in range(n):
            allocations[i] = int(round(pulp.value(x_vars[i])))
        obj_val = float(pulp.value(prob.objective))
    else:
        obj_val = 0.0

    total_allocated = int(allocations.sum())
    unmet_demand = np.maximum(0, dems - allocations)
    safe_caps = np.where(caps > 0, caps, 1)
    utilization_pct = np.where(caps > 0, (allocations / safe_caps) * 100.0, 0.0).round(2)
    weighted_contrib = (allocations * w).round(2)

    # Construct Results DataFrame
    results_df = pd.DataFrame({
        "Facility": facility_names,
        "Capacity": caps,
        "EstimatedDemand": dems,
        "OptimizedAllocation": allocations,
        "UnmetDemand": unmet_demand,
        "CapacityUtilizationPct": utilization_pct,
        "PriorityWeight": w.round(4),
        "WeightedContribution": weighted_contrib
    })

    # Summary metrics
    summary = {
        "solver_status": status_str,
        "is_optimal": is_optimal,
        "total_budget": b,
        "total_allocated": total_allocated,
        "budget_utilized_pct": round((total_allocated / b) * 100.0, 2) if b > 0 else 0.0,
        "total_estimated_demand": int(dems.sum()),
        "total_physical_capacity": int(caps.sum()),
        "total_unmet_demand": int(unmet_demand.sum()),
        "total_weighted_objective": round(obj_val, 2),
        "average_facility_utilization_pct": round(float(np.mean(utilization_pct)), 2),
        "is_budget_binding": is_binding,
        "budget_binding_message": binding_msg,
        "priority_scenario": priority_scenario
    }

    return {
        "status": status_str,
        "solver_status": status_str,
        "objective_value": round(obj_val, 2),
        "is_feasible": is_optimal,
        "feasibility_message": feas_msg,
        "is_binding": is_binding,
        "binding_message": binding_msg,
        "allocations_df": results_df,
        "summary": summary
    }


def compare_optimization_with_baseline(
    optimization_result: Dict[str, Any],
    baseline_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Merges optimization results and proportional baseline allocation for direct academic comparison.
    """
    opt_df = optimization_result["allocations_df"].copy()
    
    comp_df = pd.DataFrame({
        "Facility": opt_df["Facility"],
        "PhysicalCapacity": opt_df["Capacity"],
        "EstimatedDemand": opt_df["EstimatedDemand"],
        "PriorityWeight": opt_df["PriorityWeight"],
        "BaselineAllocation": baseline_df["BaselineAllocation"],
        "OptimizedAllocation": opt_df["OptimizedAllocation"],
        "AllocationDifference": opt_df["OptimizedAllocation"] - baseline_df["BaselineAllocation"],
        "BaselineUnmetDemand": baseline_df["UnmetDemand"],
        "OptimizedUnmetDemand": opt_df["UnmetDemand"],
        "UnmetDemandReduction": baseline_df["UnmetDemand"] - opt_df["UnmetDemand"],
        "BaselineUtilizationPct": baseline_df["CapacityUtilizationPct"],
        "OptimizedUtilizationPct": opt_df["CapacityUtilizationPct"],
        "BaselineWeightedContrib": baseline_df["WeightedContribution"],
        "OptimizedWeightedContrib": opt_df["WeightedContribution"]
    })

    comp_summary = {
        "total_budget": optimization_result["summary"]["total_budget"],
        "baseline_total_allocated": int(baseline_df["BaselineAllocation"].sum()),
        "optimized_total_allocated": int(opt_df["OptimizedAllocation"].sum()),
        "baseline_total_unmet_demand": int(baseline_df["UnmetDemand"].sum()),
        "optimized_total_unmet_demand": int(opt_df["UnmetDemand"].sum()),
        "baseline_objective_value": round(float(baseline_df["WeightedContribution"].sum()), 2),
        "optimized_objective_value": optimization_result["objective_value"],
        "objective_improvement": round(
            optimization_result["objective_value"] - float(baseline_df["WeightedContribution"].sum()), 2
        ),
        "objective_improvement_pct": round(
            ((optimization_result["objective_value"] - float(baseline_df["WeightedContribution"].sum())) /
             max(1.0, float(baseline_df["WeightedContribution"].sum()))) * 100.0, 2
        )
    }

    return comp_df, comp_summary


def run_and_export_phase2_model(
    df_clean: pd.DataFrame,
    demand_method: str = "p95",
    priority_scenario: str = "congestion",
    budget_fraction: float = 0.75,
    output_dir: str = "outputs"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Runs the complete Phase 2 optimization workflow on Birmingham parking facilities and exports results.
    """
    os.makedirs(output_dir, exist_ok=True)
    from demand_estimation import estimate_facility_demand
    from exploratory_analysis import get_parking_area_statistics

    # 1. Estimate Demand
    demand_df = estimate_facility_demand(df_clean, method=demand_method)
    area_stats = get_parking_area_statistics(df_clean)
    
    # Merge to ensure alignment
    merged = pd.merge(demand_df, area_stats[["SystemCodeNumber", "AvgUtilizationPct"]], on="SystemCodeNumber")
    
    names = merged["SystemCodeNumber"].tolist()
    caps = merged["Capacity"].tolist()
    dems = merged["EstimatedDemand"].tolist()
    utils = merged["AvgUtilizationPct"].tolist()
    
    # 2. Set Budget B (e.g. 75% of total allocatable demand for resource scarcity demonstration)
    allocatable = int(np.minimum(dems, caps).sum())
    budget = int(round(allocatable * budget_fraction))

    # 3. Solve LP
    opt_res = solve_parking_allocation_lp(
        facility_names=names,
        capacities=caps,
        demands=dems,
        budget=budget,
        priority_scenario=priority_scenario,
        historical_utilizations=utils
    )

    # 4. Compute Baseline
    weights = opt_res["allocations_df"]["PriorityWeight"].tolist()
    base_df = compute_proportional_baseline(
        capacities=caps,
        demands=dems,
        budget=budget,
        weights=weights,
        facility_names=names
    )

    # 5. Compare
    comp_df, comp_summary = compare_optimization_with_baseline(opt_res, base_df)

    # 6. Export outputs
    opt_csv = os.path.join(output_dir, "optimization_results.csv")
    base_csv = os.path.join(output_dir, "baseline_comparison.csv")
    opt_res["allocations_df"].to_csv(opt_csv, index=False)
    comp_df.to_csv(base_csv, index=False)

    return opt_res["allocations_df"], comp_df, comp_summary


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data

    raw = load_raw_data()
    clean, _ = clean_parking_data(raw)
    opt_df, comp_df, summary = run_and_export_phase2_model(clean)

    print("Phase 2 Optimization Model Complete.")
    print("Baseline vs Optimized Comparison Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("\nTop 5 facilities comparison:")
    print(comp_df[["Facility", "PhysicalCapacity", "EstimatedDemand", "BaselineAllocation", 
                   "OptimizedAllocation", "AllocationDifference"]].head(5).to_string())
