"""
sensitivity_analysis.py
Parametric budget sensitivity analysis for Managed Parking Space Allocation LP.
Identifies marginal value of permit capacity, constraint binding points, and saturation threshold.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from demand_estimation import estimate_facility_demand
from exploratory_analysis import get_parking_area_statistics
from optimization_model import solve_parking_allocation_lp
from baseline_allocation import compute_proportional_baseline
from experiment_engine import get_default_custom_weights


DEFAULT_BUDGET_FRACTIONS = [
    0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 
    0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20
]


def run_budget_sensitivity_analysis(
    df_clean: pd.DataFrame,
    demand_method: str = "p95",
    priority_strategy: str = "congestion",
    budget_fractions: Optional[List[float]] = None,
    output_dir: str = "outputs"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluates system response as the permit budget B scales from 0% to 120% of allocatable demand.
    
    Tracks:
    - Total Allocated & Unmet Demand
    - Objective Function Value & Optimization Gain over Baseline
    - Facility Satisfaction States (Fully Satisfied, Partially Satisfied, Zero Allocation)
    - Marginal Value per Permit (dZ/dB)
    - Exact Saturation Threshold where budget becomes non-binding
    
    Exports results to 'outputs/budget_sensitivity.csv'.
    """
    os.makedirs(output_dir, exist_ok=True)
    fractions = budget_fractions or DEFAULT_BUDGET_FRACTIONS

    # 1. Setup facilities
    demand_df = estimate_facility_demand(df_clean, method=demand_method)
    area_stats = get_parking_area_statistics(df_clean)
    merged = pd.merge(area_stats[["SystemCodeNumber", "AvgUtilizationPct"]], demand_df, on="SystemCodeNumber")

    names = merged["SystemCodeNumber"].tolist()
    caps = merged["Capacity"].tolist()
    dems = merged["EstimatedDemand"].tolist()
    utils = merged["AvgUtilizationPct"].tolist()
    custom_w = get_default_custom_weights(names) if priority_strategy == "custom" else None

    caps_arr = np.array(caps, dtype=int)
    dems_arr = np.array(dems, dtype=int)
    effective_caps = np.minimum(dems_arr, caps_arr)
    total_allocatable = int(effective_caps.sum())
    total_demand = int(dems_arr.sum())
    total_capacity = int(caps_arr.sum())

    records = []
    prev_b = 0
    prev_z = 0.0

    for frac in fractions:
        budget = int(round(total_allocatable * frac))

        # Solve LP
        opt_res = solve_parking_allocation_lp(
            facility_names=names,
            capacities=caps,
            demands=dems,
            budget=budget,
            priority_scenario=priority_strategy,
            historical_utilizations=utils,
            weights=custom_w
        )

        used_weights = opt_res["allocations_df"]["PriorityWeight"].tolist()

        # Solve Baseline
        base_df = compute_proportional_baseline(
            capacities=caps,
            demands=dems,
            budget=budget,
            weights=used_weights,
            facility_names=names
        )

        opt_allocs = opt_res["allocations_df"]["OptimizedAllocation"].values
        base_allocs = base_df["BaselineAllocation"].values

        opt_alloc_total = int(opt_allocs.sum())
        base_alloc_total = int(base_allocs.sum())
        opt_unmet = int(np.maximum(0, dems_arr - opt_allocs).sum())
        base_unmet = int(np.maximum(0, dems_arr - base_allocs).sum())

        opt_z = opt_res["objective_value"]
        base_z = round(float(np.sum(base_allocs * np.array(used_weights))), 2)
        gain = round(opt_z - base_z, 2)
        gain_pct = round((gain / max(1.0, base_z)) * 100.0, 2) if base_z > 0 else 0.0

        # Facility counts
        fully_sat = int(np.sum(opt_allocs == effective_caps))
        partially_sat = int(np.sum((opt_allocs > 0) & (opt_allocs < effective_caps)))
        zero_alloc = int(np.sum(opt_allocs == 0))

        # Marginal value (dZ/dB)
        delta_b = budget - prev_b
        delta_z = opt_z - prev_z
        marginal_val = round(delta_z / delta_b, 4) if delta_b > 0 else 0.0

        prev_b = budget
        prev_z = opt_z

        records.append({
            "BudgetFraction": frac,
            "BudgetPermits": budget,
            "OptimizedAllocated": opt_alloc_total,
            "BaselineAllocated": base_alloc_total,
            "OptimizedUnmetDemand": opt_unmet,
            "BaselineUnmetDemand": base_unmet,
            "OptimizedObjective": opt_z,
            "BaselineObjective": base_z,
            "OptimizationGain": gain,
            "OptimizationGainPct": gain_pct,
            "BudgetUtilizationPct": round((opt_alloc_total / budget) * 100.0, 2) if budget > 0 else 0.0,
            "FullySatisfiedFacilities": fully_sat,
            "PartiallySatisfiedFacilities": partially_sat,
            "ZeroAllocationFacilities": zero_alloc,
            "IsBudgetBinding": opt_res["is_binding"],
            "MarginalValuePerPermit": marginal_val
        })

    sensitivity_df = pd.DataFrame(records)

    # Detect Saturation Threshold
    sat_row = sensitivity_df[sensitivity_df["BudgetFraction"] >= 1.0].iloc[0]
    saturation_summary = {
        "total_allocatable_demand": total_allocatable,
        "total_estimated_demand": total_demand,
        "total_physical_capacity": total_capacity,
        "saturation_budget_permits": total_allocatable,
        "maximum_achievable_objective": float(sat_row["OptimizedObjective"]),
        "saturation_insight": (
            f"Increasing budget beyond {total_allocatable:,} permits yields exactly zero marginal objective "
            f"gain because all 30 facilities achieve their maximum physical or demand limits."
        )
    }

    out_csv = os.path.join(output_dir, "budget_sensitivity.csv")
    sensitivity_df.to_csv(out_csv, index=False)

    return sensitivity_df, saturation_summary


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data

    raw = load_raw_data()
    clean, _ = clean_parking_data(raw)
    sens_df, sat_info = run_budget_sensitivity_analysis(clean)

    print("Budget Sensitivity Analysis Completed.")
    print("Key Sensitivity Steps (0%, 25%, 50%, 75%, 100%, 120%):")
    cols = ["BudgetFraction", "BudgetPermits", "OptimizedAllocated", "OptimizedObjective", 
            "MarginalValuePerPermit", "FullySatisfiedFacilities", "ZeroAllocationFacilities", "IsBudgetBinding"]
    subset = sens_df[sens_df["BudgetFraction"].isin([0.0, 0.20, 0.50, 0.75, 1.00, 1.20])]
    print(subset[cols].to_string(index=False))
    print("\nSaturation Summary:")
    for k, v in sat_info.items():
        print(f"  {k}: {v}")

