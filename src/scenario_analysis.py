"""
scenario_analysis.py
Scenario Analysis Module implementing the 5 core Operations Research scenarios:
1. Existing Allocation Baseline
2. Demand-Based Optimization
3. Priority-Based Optimization
4. Capacity Reduction Scenario (Simulated Infrastructure Stress)
5. Peak Demand Scenario (Extreme Event Stress)
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


SCENARIO_NAMES = [
    "1. Existing Baseline",
    "2. Demand-Based Optimization",
    "3. Priority-Based Optimization",
    "4. Capacity Reduction Scenario",
    "5. Peak Demand Scenario"
]


def run_all_optimization_scenarios(
    df_clean: pd.DataFrame,
    base_budget_fraction: float = 0.75,
    reduction_factor: float = 0.25,
    output_dir: str = "outputs"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Executes the 5 canonical optimization scenarios:
    
    Scenario 1: Existing Baseline
       Proportional allocation under standard 95th percentile demand.
       
    Scenario 2: Demand-Based Optimization
       PuLP LP with Equal Priority (w_i = 1.0). Maximizes volume of served demand.
       
    Scenario 3: Priority-Based Optimization
       PuLP LP with Congestion Priority (w_i in [1.0, 3.0]). Targets saturated lots.
       
    Scenario 4: Capacity Reduction Scenario
       Simulates an urban maintenance / roadworks / closure event where permit budget
       is reduced by reduction_factor (default: 25% budget contraction).
       
    Scenario 5: Peak Demand Scenario
       Optimizes under Maximum Observed Demand (d_i = max O_i) stress test.
       
    Returns:
       Tuple[summary_df, facility_allocations_df, scenario_details_dict]
       Exports to 'outputs/scenario_analysis_summary.csv' and 'outputs/scenario_facility_allocations.csv'.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Base inputs
    area_stats = get_parking_area_statistics(df_clean)
    names = area_stats["SystemCodeNumber"].tolist()
    caps = area_stats["Capacity"].tolist()
    utils = area_stats["AvgUtilizationPct"].tolist()
    n = len(names)

    # Demands
    d_p95_df = estimate_facility_demand(df_clean, method="p95")
    d_max_df = estimate_facility_demand(df_clean, method="max")
    
    merged_p95 = pd.merge(area_stats[["SystemCodeNumber"]], d_p95_df, on="SystemCodeNumber")
    merged_max = pd.merge(area_stats[["SystemCodeNumber"]], d_max_df, on="SystemCodeNumber")

    dems_p95 = merged_p95["EstimatedDemand"].tolist()
    dems_max = merged_max["EstimatedDemand"].tolist()

    allocatable_p95 = int(np.minimum(dems_p95, caps).sum())
    allocatable_max = int(np.minimum(dems_max, caps).sum())

    # Standard budget
    std_budget = int(round(allocatable_p95 * base_budget_fraction))
    reduced_budget = int(round(std_budget * (1.0 - reduction_factor)))

    scenario_summaries = []
    facility_alloc_dict = {"Facility": names, "Capacity": caps}

    # --- Scenario 1: Existing Allocation Baseline ---
    # Baseline uses congestion weights to evaluate fair comparative weighted value
    cong_weights_arr = pd.Series(utils).apply(lambda u: 1.0 + 2.0 * (u / max(utils))).round(4).tolist()
    base_res = compute_proportional_baseline(
        capacities=caps,
        demands=dems_p95,
        budget=std_budget,
        weights=cong_weights_arr,
        facility_names=names
    )
    alloc_s1 = base_res["BaselineAllocation"].values
    unmet_s1 = base_res["UnmetDemand"].values
    obj_s1 = round(float(base_res["WeightedContribution"].sum()), 2)
    facility_alloc_dict["Scenario1_Baseline"] = alloc_s1

    scenario_summaries.append({
        "ScenarioID": "SCEN_01",
        "ScenarioName": "1. Existing Baseline",
        "DemandEstimator": "95th Percentile",
        "PriorityStrategy": "Proportional Demand Share",
        "BudgetPermits": std_budget,
        "TotalAllocated": int(alloc_s1.sum()),
        "BudgetUtilizationPct": round((int(alloc_s1.sum()) / std_budget) * 100.0, 2),
        "TotalUnmetDemand": int(unmet_s1.sum()),
        "WeightedObjective": obj_s1,
        "FullySatisfiedLots": int(np.sum(alloc_s1 == np.minimum(dems_p95, caps))),
        "PartiallySatisfiedLots": int(np.sum((alloc_s1 > 0) & (alloc_s1 < np.minimum(dems_p95, caps)))),
        "ZeroAllocationLots": int(np.sum(alloc_s1 == 0)),
        "AvgUtilizationPct": round(float(np.mean(base_res["CapacityUtilizationPct"])), 2),
        "Description": "Administrative proportional distribution without mathematical optimization."
    })

    # --- Scenario 2: Demand-Based Optimization ---
    opt_s2 = solve_parking_allocation_lp(
        facility_names=names,
        capacities=caps,
        demands=dems_p95,
        budget=std_budget,
        priority_scenario="equal"
    )
    alloc_s2 = opt_s2["allocations_df"]["OptimizedAllocation"].values
    unmet_s2 = opt_s2["allocations_df"]["UnmetDemand"].values
    # Evaluate S2 on congestion weights to enable cross-scenario comparison
    obj_s2_weighted = round(float(np.sum(alloc_s2 * np.array(cong_weights_arr))), 2)
    facility_alloc_dict["Scenario2_DemandOptimized"] = alloc_s2

    scenario_summaries.append({
        "ScenarioID": "SCEN_02",
        "ScenarioName": "2. Demand-Based Optimization",
        "DemandEstimator": "95th Percentile",
        "PriorityStrategy": "Equal Priority (w=1.0)",
        "BudgetPermits": std_budget,
        "TotalAllocated": int(alloc_s2.sum()),
        "BudgetUtilizationPct": 100.0,
        "TotalUnmetDemand": int(unmet_s2.sum()),
        "WeightedObjective": obj_s2_weighted,
        "FullySatisfiedLots": int(np.sum(alloc_s2 == np.minimum(dems_p95, caps))),
        "PartiallySatisfiedLots": int(np.sum((alloc_s2 > 0) & (alloc_s2 < np.minimum(dems_p95, caps)))),
        "ZeroAllocationLots": int(np.sum(alloc_s2 == 0)),
        "AvgUtilizationPct": round(float(np.mean(opt_s2["allocations_df"]["CapacityUtilizationPct"])), 2),
        "Description": "Pure demand-volume maximization with equal weights across all facilities."
    })

    # --- Scenario 3: Priority-Based Optimization ---
    opt_s3 = solve_parking_allocation_lp(
        facility_names=names,
        capacities=caps,
        demands=dems_p95,
        budget=std_budget,
        priority_scenario="congestion",
        historical_utilizations=utils
    )
    alloc_s3 = opt_s3["allocations_df"]["OptimizedAllocation"].values
    unmet_s3 = opt_s3["allocations_df"]["UnmetDemand"].values
    obj_s3 = opt_s3["objective_value"]
    facility_alloc_dict["Scenario3_PriorityOptimized"] = alloc_s3

    scenario_summaries.append({
        "ScenarioID": "SCEN_03",
        "ScenarioName": "3. Priority-Based Optimization",
        "DemandEstimator": "95th Percentile",
        "PriorityStrategy": "Congestion-Sensitive Priority",
        "BudgetPermits": std_budget,
        "TotalAllocated": int(alloc_s3.sum()),
        "BudgetUtilizationPct": 100.0,
        "TotalUnmetDemand": int(unmet_s3.sum()),
        "WeightedObjective": obj_s3,
        "FullySatisfiedLots": int(np.sum(alloc_s3 == np.minimum(dems_p95, caps))),
        "PartiallySatisfiedLots": int(np.sum((alloc_s3 > 0) & (alloc_s3 < np.minimum(dems_p95, caps)))),
        "ZeroAllocationLots": int(np.sum(alloc_s3 == 0)),
        "AvgUtilizationPct": round(float(np.mean(opt_s3["allocations_df"]["CapacityUtilizationPct"])), 2),
        "Description": "Mathematical optimization directing scarce permits to congested bottleneck lots."
    })

    # --- Scenario 4: Capacity Reduction Scenario ---
    opt_s4 = solve_parking_allocation_lp(
        facility_names=names,
        capacities=caps,
        demands=dems_p95,
        budget=reduced_budget,
        priority_scenario="congestion",
        historical_utilizations=utils
    )
    alloc_s4 = opt_s4["allocations_df"]["OptimizedAllocation"].values
    unmet_s4 = opt_s4["allocations_df"]["UnmetDemand"].values
    obj_s4 = opt_s4["objective_value"]
    facility_alloc_dict["Scenario4_CapacityReduction"] = alloc_s4

    scenario_summaries.append({
        "ScenarioID": "SCEN_04",
        "ScenarioName": "4. Capacity Reduction Scenario",
        "DemandEstimator": "95th Percentile",
        "PriorityStrategy": "Congestion Priority (-25% Budget)",
        "BudgetPermits": reduced_budget,
        "TotalAllocated": int(alloc_s4.sum()),
        "BudgetUtilizationPct": 100.0,
        "TotalUnmetDemand": int(unmet_s4.sum()),
        "WeightedObjective": obj_s4,
        "FullySatisfiedLots": int(np.sum(alloc_s4 == np.minimum(dems_p95, caps))),
        "PartiallySatisfiedLots": int(np.sum((alloc_s4 > 0) & (alloc_s4 < np.minimum(dems_p95, caps)))),
        "ZeroAllocationLots": int(np.sum(alloc_s4 == 0)),
        "AvgUtilizationPct": round(float(np.mean(opt_s4["allocations_df"]["CapacityUtilizationPct"])), 2),
        "Description": "Stress tests 25% permit budget reduction to model municipal closures/maintenance."
    })

    # --- Scenario 5: Peak Demand Scenario ---
    opt_s5 = solve_parking_allocation_lp(
        facility_names=names,
        capacities=caps,
        demands=dems_max,
        budget=std_budget,
        priority_scenario="congestion",
        historical_utilizations=utils
    )
    alloc_s5 = opt_s5["allocations_df"]["OptimizedAllocation"].values
    unmet_s5 = opt_s5["allocations_df"]["UnmetDemand"].values
    obj_s5 = opt_s5["objective_value"]
    facility_alloc_dict["Scenario5_PeakDemand"] = alloc_s5

    scenario_summaries.append({
        "ScenarioID": "SCEN_05",
        "ScenarioName": "5. Peak Demand Scenario",
        "DemandEstimator": "Maximum Observed Demand",
        "PriorityStrategy": "Congestion Priority (Max Demand)",
        "BudgetPermits": std_budget,
        "TotalAllocated": int(alloc_s5.sum()),
        "BudgetUtilizationPct": 100.0,
        "TotalUnmetDemand": int(unmet_s5.sum()),
        "WeightedObjective": obj_s5,
        "FullySatisfiedLots": int(np.sum(alloc_s5 == np.minimum(dems_max, caps))),
        "PartiallySatisfiedLots": int(np.sum((alloc_s5 > 0) & (alloc_s5 < np.minimum(dems_max, caps)))),
        "ZeroAllocationLots": int(np.sum(alloc_s5 == 0)),
        "AvgUtilizationPct": round(float(np.mean(opt_s5["allocations_df"]["CapacityUtilizationPct"])), 2),
        "Description": "Stress tests system against historical peak overflow and maximum recorded vehicle arrivals."
    })

    summary_df = pd.DataFrame(scenario_summaries)
    facility_df = pd.DataFrame(facility_alloc_dict)

    # Save to CSV
    summary_csv = os.path.join(output_dir, "scenario_analysis_summary.csv")
    facility_csv = os.path.join(output_dir, "scenario_facility_allocations.csv")
    summary_df.to_csv(summary_csv, index=False)
    facility_df.to_csv(facility_csv, index=False)

    return summary_df, facility_df, {
        "standard_budget": std_budget,
        "reduced_budget": reduced_budget,
        "reduction_percentage": reduction_factor * 100.0,
        "allocatable_p95": allocatable_p95,
        "allocatable_max": allocatable_max
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data

    raw = load_raw_data()
    clean, _ = clean_parking_data(raw)
    sum_df, fac_df, meta = run_all_optimization_scenarios(clean)

    print("5 Scenarios Successfully Executed.")
    cols = ["ScenarioName", "BudgetPermits", "TotalAllocated", "TotalUnmetDemand", 
            "WeightedObjective", "FullySatisfiedLots", "ZeroAllocationLots"]
    print(sum_df[cols].to_string(index=False))

