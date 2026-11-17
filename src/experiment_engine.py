"""
experiment_engine.py
Optimization Experiment Engine executing multi-factor scenario matrices:
4 Demand Estimators x 3 Priority Strategies x 3 Budget Scenarios = 36 Experiment Runs.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from demand_estimation import estimate_facility_demand, DEMAND_METHODS
from exploratory_analysis import get_parking_area_statistics
from optimization_model import (
    solve_parking_allocation_lp,
    compute_priority_weights,
    compare_optimization_with_baseline
)
from baseline_allocation import compute_proportional_baseline


BUDGET_SCENARIOS = {
    "low": 0.50,       # 50% of total allocatable demand
    "medium": 0.75,    # 75% of total allocatable demand
    "high": 0.90       # 90% of total allocatable demand
}

PRIORITY_STRATEGIES = ["equal", "congestion", "custom"]


def get_default_custom_weights(facility_names: List[str]) -> List[float]:
    """
    Generates transparent, policy-driven custom weights reflecting municipal urban policy:
    - Healthcare / Emergency Facilities (e.g. Hospital NHS): Weight = 3.0
    - Core Commercial / Retail / Civic Hubs (e.g. Bull Ring, Shopping, Broad Street, BCC): Weight = 2.5
    - Major Rail / Transit Commuter Hubs (e.g. NCP, BRC): Weight = 1.8
    - Peripheral Civic / Arena Facilities (e.g. NIA, Others): Weight = 1.2
    
    Reproducible and deterministic; does not assume demographic user classes.
    """
    weights = []
    for name in facility_names:
        uname = name.upper()
        if "NHS" in uname:
            weights.append(3.0)
        elif any(k in uname for k in ["BULL RING", "SHOPPING", "BROAD STREET", "BCC"]):
            weights.append(2.5)
        elif any(k in uname for k in ["NCP", "BRC"]):
            weights.append(1.8)
        else:
            weights.append(1.2)
    return weights


def run_single_optimization_configuration(
    facility_names: List[str],
    capacities: List[int],
    demands: List[int],
    historical_utils: List[float],
    demand_method: str,
    priority_strategy: str,
    budget_scenario: str,
    custom_weights: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Executes a single end-to-end optimization experiment and its corresponding baseline.
    """
    caps = np.array(capacities, dtype=int)
    dems = np.array(demands, dtype=int)
    effective_caps = np.minimum(dems, caps)
    total_allocatable = int(effective_caps.sum())
    total_demand = int(dems.sum())
    total_capacity = int(caps.sum())

    budget_frac = BUDGET_SCENARIOS.get(budget_scenario.lower(), 0.75)
    budget = int(round(total_allocatable * budget_frac))

    start_time = time.perf_counter()

    # Solve LP
    opt_res = solve_parking_allocation_lp(
        facility_names=facility_names,
        capacities=capacities,
        demands=demands,
        budget=budget,
        priority_scenario=priority_strategy,
        weights=custom_weights,
        historical_utilizations=historical_utils
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Extract weights used
    used_weights = opt_res["allocations_df"]["PriorityWeight"].tolist()

    # Compute baseline
    base_df = compute_proportional_baseline(
        capacities=capacities,
        demands=demands,
        budget=budget,
        weights=used_weights,
        facility_names=facility_names
    )

    opt_allocs = opt_res["allocations_df"]["OptimizedAllocation"].values
    base_allocs = base_df["BaselineAllocation"].values

    opt_allocated = int(opt_allocs.sum())
    base_allocated = int(base_allocs.sum())
    opt_unmet = int(np.maximum(0, dems - opt_allocs).sum())
    base_unmet = int(np.maximum(0, dems - base_allocs).sum())

    opt_obj = opt_res["objective_value"]
    base_obj = round(float(np.sum(base_allocs * np.array(used_weights))), 2)

    obj_gain = round(opt_obj - base_obj, 2)
    obj_gain_pct = round((obj_gain / max(1.0, base_obj)) * 100.0, 2)

    # Satisfaction categories
    fully_satisfied = int(np.sum(opt_allocs == effective_caps))
    partially_satisfied = int(np.sum((opt_allocs > 0) & (opt_allocs < effective_caps)))
    zero_allocated = int(np.sum(opt_allocs == 0))

    return {
        "ConfigID": f"EXP_{demand_method.upper()}_{priority_strategy.upper()}_{budget_scenario.upper()}",
        "DemandEstimator": demand_method,
        "PriorityStrategy": priority_strategy,
        "BudgetScenario": budget_scenario,
        "BudgetFraction": budget_frac,
        "PermitBudget": budget,
        "TotalPhysicalCapacity": total_capacity,
        "TotalEstimatedDemand": total_demand,
        "TotalAllocatableDemand": total_allocatable,
        "OptimizedAllocated": opt_allocated,
        "BaselineAllocated": base_allocated,
        "BudgetUtilizationPct": round((opt_allocated / budget) * 100.0, 2) if budget > 0 else 0.0,
        "OptimizedUnmetDemand": opt_unmet,
        "BaselineUnmetDemand": base_unmet,
        "OptimizedObjective": opt_obj,
        "BaselineObjective": base_obj,
        "ObjectiveGain": obj_gain,
        "ObjectiveGainPct": obj_gain_pct,
        "FullySatisfiedCount": fully_satisfied,
        "PartiallySatisfiedCount": partially_satisfied,
        "ZeroAllocatedCount": zero_allocated,
        "SolverStatus": opt_res["solver_status"],
        "IsBudgetBinding": opt_res["is_binding"],
        "RuntimeMs": round(elapsed_ms, 2)
    }


def run_experiment_grid(
    df_clean: pd.DataFrame,
    estimators: Optional[List[str]] = None,
    priorities: Optional[List[str]] = None,
    budget_scenarios: Optional[List[str]] = None,
    output_dir: str = "outputs"
) -> pd.DataFrame:
    """
    Executes the full Cartesian product of:
    - Demand Estimators: ['mean', 'p85', 'p95', 'max'] (4)
    - Priority Strategies: ['equal', 'congestion', 'custom'] (3)
    - Budget Scenarios: ['low', 'medium', 'high'] (3)
    Total = 36 experimental runs.
    
    Exports results to 'outputs/scenario_comparison.csv'.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    estimators = estimators or DEMAND_METHODS
    priorities = priorities or PRIORITY_STRATEGIES
    budgets = budget_scenarios or list(BUDGET_SCENARIOS.keys())

    area_stats = get_parking_area_statistics(df_clean)
    facility_names = area_stats["SystemCodeNumber"].tolist()
    capacities = area_stats["Capacity"].tolist()
    historical_utils = area_stats["AvgUtilizationPct"].tolist()
    custom_weights = get_default_custom_weights(facility_names)

    experiment_records = []

    for est in estimators:
        demand_df = estimate_facility_demand(df_clean, method=est)
        # Ensure row alignment with area_stats
        merged = pd.merge(area_stats[["SystemCodeNumber"]], demand_df, on="SystemCodeNumber")
        demands = merged["EstimatedDemand"].tolist()

        for prio in priorities:
            for b_scen in budgets:
                c_weights = custom_weights if prio == "custom" else None
                rec = run_single_optimization_configuration(
                    facility_names=facility_names,
                    capacities=capacities,
                    demands=demands,
                    historical_utils=historical_utils,
                    demand_method=est,
                    priority_strategy=prio,
                    budget_scenario=b_scen,
                    custom_weights=c_weights
                )
                experiment_records.append(rec)

    results_df = pd.DataFrame(experiment_records)
    out_csv = os.path.join(output_dir, "scenario_comparison.csv")
    results_df.to_csv(out_csv, index=False)
    return results_df


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data

    raw = load_raw_data()
    clean, _ = clean_parking_data(raw)
    exp_df = run_experiment_grid(clean)

    print(f"Executed 36 optimization experiments successfully.")
    print("Sample Results (First 5 Scenarios):")
    cols = ["ConfigID", "PermitBudget", "OptimizedObjective", "BaselineObjective", "ObjectiveGainPct", "FullySatisfiedCount"]
    print(exp_df[cols].head(5).to_string(index=False))

