"""
comparison_analysis.py
Comparative analysis of Demand Estimation Methods and Priority Strategies.
Evaluates facility-level allocation shifts, objective variations, and saturation impacts.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from demand_estimation import estimate_facility_demand
from exploratory_analysis import get_parking_area_statistics
from optimization_model import solve_parking_allocation_lp, compute_priority_weights
from experiment_engine import get_default_custom_weights


def generate_demand_estimator_comparison(
    df_clean: pd.DataFrame,
    fixed_budget: Optional[int] = None,
    output_dir: str = "outputs"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compares the 4 demand estimators (Mean, P85, P95, Max) across all 30 facilities.
    
    Calculates:
    - Capacity vs. Demand for each method
    - Capacity Saturation Flags (d_i >= C_i)
    - Spread metrics (P95 - Mean, Max - P95)
    - LP Allocation response under a standardized municipal budget
    
    Exports results to 'outputs/estimator_comparison.csv'.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Gather estimates
    d_mean = estimate_facility_demand(df_clean, method="mean")
    d_p85 = estimate_facility_demand(df_clean, method="p85")
    d_p95 = estimate_facility_demand(df_clean, method="p95")
    d_max = estimate_facility_demand(df_clean, method="max")
    
    area_stats = get_parking_area_statistics(df_clean)

    # Merge on SystemCodeNumber
    comp = pd.merge(
        area_stats[["SystemCodeNumber", "Capacity", "AvgUtilizationPct", "OverflowCount"]],
        d_mean[["SystemCodeNumber", "MeanDemand"]],
        on="SystemCodeNumber"
    )
    comp = pd.merge(comp, d_p85[["SystemCodeNumber", "P85Demand"]], on="SystemCodeNumber")
    comp = pd.merge(comp, d_p95[["SystemCodeNumber", "P95Demand"]], on="SystemCodeNumber")
    comp = pd.merge(comp, d_max[["SystemCodeNumber", "MaxDemand"]], on="SystemCodeNumber")

    # Saturation indicators (d_i >= C_i)
    comp["IsSaturated_Mean"] = comp["MeanDemand"] >= comp["Capacity"]
    comp["IsSaturated_P85"] = comp["P85Demand"] >= comp["Capacity"]
    comp["IsSaturated_P95"] = comp["P95Demand"] >= comp["Capacity"]
    comp["IsSaturated_Max"] = comp["MaxDemand"] >= comp["Capacity"]

    # Demand Spreads
    comp["PeakSpread_P95_vs_Mean"] = comp["P95Demand"] - comp["MeanDemand"]
    comp["StressSpread_Max_vs_P95"] = comp["MaxDemand"] - comp["P95Demand"]

    # Standard budget for allocation comparison (e.g. 75% of P95 allocatable demand)
    allocatable_p95 = int(np.minimum(comp["P95Demand"], comp["Capacity"]).sum())
    b_val = fixed_budget if fixed_budget is not None else int(round(allocatable_p95 * 0.75))

    names = comp["SystemCodeNumber"].tolist()
    caps = comp["Capacity"].tolist()
    utils = comp["AvgUtilizationPct"].tolist()

    # Solve LP under each estimator with the same budget and Congestion Priority
    for method, col_name in [("mean", "MeanDemand"), ("p85", "P85Demand"), 
                             ("p95", "P95Demand"), ("max", "MaxDemand")]:
        d_list = comp[col_name].tolist()
        res = solve_parking_allocation_lp(
            facility_names=names,
            capacities=caps,
            demands=d_list,
            budget=b_val,
            priority_scenario="congestion",
            historical_utilizations=utils
        )
        comp[f"Allocated_{method.upper()}"] = res["allocations_df"]["OptimizedAllocation"]

    # Summary Statistics
    summary = {
        "total_capacity": int(comp["Capacity"].sum()),
        "total_mean_demand": int(comp["MeanDemand"].sum()),
        "total_p85_demand": int(comp["P85Demand"].sum()),
        "total_p95_demand": int(comp["P95Demand"].sum()),
        "total_max_demand": int(comp["MaxDemand"].sum()),
        "saturated_facilities_mean": int(comp["IsSaturated_Mean"].sum()),
        "saturated_facilities_p85": int(comp["IsSaturated_P85"].sum()),
        "saturated_facilities_p95": int(comp["IsSaturated_P95"].sum()),
        "saturated_facilities_max": int(comp["IsSaturated_Max"].sum()),
        "standard_comparison_budget": b_val
    }

    out_csv = os.path.join(output_dir, "estimator_comparison.csv")
    comp.to_csv(out_csv, index=False)
    return comp, summary


def generate_priority_strategy_comparison(
    df_clean: pd.DataFrame,
    demand_method: str = "p95",
    budget_fraction: float = 0.75,
    output_dir: str = "outputs"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compares the 3 priority strategies (Equal, Congestion, Custom) under identical demand and budget.
    
    Evaluates:
    - Strategic permit reallocation across facilities
    - Shifts between central congested lots and peripheral lots
    - Objective function values achieved under each policy
    
    Exports results to 'outputs/priority_comparison.csv'.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    demand_df = estimate_facility_demand(df_clean, method=demand_method)
    area_stats = get_parking_area_statistics(df_clean)
    merged = pd.merge(area_stats[["SystemCodeNumber", "AvgUtilizationPct"]], demand_df, on="SystemCodeNumber")

    names = merged["SystemCodeNumber"].tolist()
    caps = merged["Capacity"].tolist()
    dems = merged["EstimatedDemand"].tolist()
    utils = merged["AvgUtilizationPct"].tolist()
    custom_w = get_default_custom_weights(names)

    allocatable = int(np.minimum(dems, caps).sum())
    budget = int(round(allocatable * budget_fraction))

    # 1. Equal Priority
    res_equal = solve_parking_allocation_lp(
        facility_names=names,
        capacities=caps,
        demands=dems,
        budget=budget,
        priority_scenario="equal"
    )

    # 2. Congestion Priority
    res_cong = solve_parking_allocation_lp(
        facility_names=names,
        capacities=caps,
        demands=dems,
        budget=budget,
        priority_scenario="congestion",
        historical_utilizations=utils
    )

    # 3. Custom Policy Priority
    res_cust = solve_parking_allocation_lp(
        facility_names=names,
        capacities=caps,
        demands=dems,
        budget=budget,
        priority_scenario="custom",
        weights=custom_w
    )

    df_eq = res_equal["allocations_df"]
    df_cg = res_cong["allocations_df"]
    df_cu = res_cust["allocations_df"]

    comp_prio = pd.DataFrame({
        "Facility": names,
        "Capacity": caps,
        "EstimatedDemand": dems,
        "HistoricalUtilizationPct": np.round(utils, 2),
        "Weight_Equal": df_eq["PriorityWeight"],
        "Weight_Congestion": df_cg["PriorityWeight"],
        "Weight_Custom": df_cu["PriorityWeight"],
        "Alloc_Equal": df_eq["OptimizedAllocation"],
        "Alloc_Congestion": df_cg["OptimizedAllocation"],
        "Alloc_Custom": df_cu["OptimizedAllocation"],
        "Shift_Congestion_vs_Equal": df_cg["OptimizedAllocation"] - df_eq["OptimizedAllocation"],
        "Shift_Custom_vs_Congestion": df_cu["OptimizedAllocation"] - df_cg["OptimizedAllocation"],
        "UnmetDemand_Congestion": df_cg["UnmetDemand"],
        "UnmetDemand_Equal": df_eq["UnmetDemand"]
    })

    summary = {
        "budget": budget,
        "objective_equal": res_equal["objective_value"],
        "objective_congestion": res_cong["objective_value"],
        "objective_custom": res_cust["objective_value"],
        "top_beneficiary_congestion": comp_prio.sort_values(by="Shift_Congestion_vs_Equal", ascending=False).iloc[0]["Facility"],
        "max_permits_gained_congestion": int(comp_prio["Shift_Congestion_vs_Equal"].max()),
        "top_donor_congestion": comp_prio.sort_values(by="Shift_Congestion_vs_Equal", ascending=True).iloc[0]["Facility"],
        "max_permits_donated_congestion": int(comp_prio["Shift_Congestion_vs_Equal"].min())
    }

    out_csv = os.path.join(output_dir, "priority_comparison.csv")
    comp_prio.to_csv(out_csv, index=False)
    return comp_prio, summary


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data

    raw = load_raw_data()
    clean, _ = clean_parking_data(raw)
    
    est_comp, est_sum = generate_demand_estimator_comparison(clean)
    prio_comp, prio_sum = generate_priority_strategy_comparison(clean)

    print("Demand Estimators Comparison Completed.")
    print("Saturated Facilities by Method:", 
          f"Mean: {est_sum['saturated_facilities_mean']}, P85: {est_sum['saturated_facilities_p85']}, "
          f"P95: {est_sum['saturated_facilities_p95']}, Max: {est_sum['saturated_facilities_max']}")

    print("\nPriority Strategy Comparison Summary:")
    for k, v in prio_sum.items():
        print(f"  {k}: {v}")

