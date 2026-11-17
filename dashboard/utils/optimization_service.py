"""
optimization_service.py
Optimization orchestration service for the PARKOPT Streamlit application.
Interfaces with Phase 2 PuLP solver, baseline models, and constraint validators.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from demand_estimation import estimate_facility_demand
from exploratory_analysis import get_parking_area_statistics
from optimization_model import (
    solve_parking_allocation_lp,
    compute_priority_weights,
    compare_optimization_with_baseline
)
from baseline_allocation import compute_proportional_baseline
from constraints import OptimizationConstraints


def run_solver_workflow(
    df_clean: pd.DataFrame,
    budget: int,
    demand_method: str = "p95",
    priority_scenario: str = "congestion",
    custom_weights: Optional[List[float]] = None,
    min_allocations: Optional[List[int]] = None
) -> Tuple[Dict[str, Any], pd.DataFrame, Dict[str, Any]]:
    """
    Executes the complete optimization pipeline for given parameters:
    1. Demand estimation (Mean, P85, P95, or Max).
    2. Facility capacity and historical utilization extraction.
    3. PuLP Integer Linear Programming solve.
    4. Proportional Baseline comparison.
    
    Returns:
        (optimization_result, comparison_df, comparison_summary)
    """
    start_time = time.time()
    
    # 1. Demand & Capacity extraction
    demand_df = estimate_facility_demand(df_clean, method=demand_method)
    area_stats = get_parking_area_statistics(df_clean)
    
    # Align rows strictly by SystemCodeNumber
    merged = pd.merge(
        demand_df,
        area_stats[["SystemCodeNumber", "AvgUtilizationPct"]],
        on="SystemCodeNumber",
        how="inner"
    )
    
    facility_names = merged["SystemCodeNumber"].tolist()
    capacities = merged["Capacity"].astype(int).tolist()
    demands = merged["EstimatedDemand"].astype(int).tolist()
    historical_utils = merged["AvgUtilizationPct"].astype(float).tolist()
    
    # 2. PuLP ILP Solve
    opt_result = solve_parking_allocation_lp(
        facility_names=facility_names,
        capacities=capacities,
        demands=demands,
        budget=int(budget),
        priority_scenario=priority_scenario,
        weights=custom_weights,
        historical_utilizations=historical_utils,
        min_allocations=min_allocations
    )
    
    # 3. Proportional Baseline Calculation
    weights = opt_result["allocations_df"]["PriorityWeight"].tolist()
    baseline_df = compute_proportional_baseline(
        capacities=capacities,
        demands=demands,
        budget=int(budget),
        weights=weights,
        facility_names=facility_names
    )
    
    # 4. Comparative Evaluation
    comp_df, comp_summary = compare_optimization_with_baseline(opt_result, baseline_df)
    
    elapsed = time.time() - start_time
    opt_result["elapsed_seconds"] = round(elapsed, 4)
    
    return opt_result, comp_df, comp_summary


def compute_facility_weights_preview(
    df_clean: pd.DataFrame,
    priority_scenario: str = "congestion",
    custom_weights: Optional[List[float]] = None
) -> pd.DataFrame:
    """
    Returns a preview table of facility priority weights under selected scenario.
    """
    area_stats = get_parking_area_statistics(df_clean)
    capacities = area_stats["Capacity"].tolist()
    demands = area_stats["AvgOccupancy"].round().astype(int).tolist()
    utils = area_stats["AvgUtilizationPct"].tolist()
    
    weights = compute_priority_weights(
        capacities=capacities,
        demands=demands,
        historical_utilizations=utils,
        scenario=priority_scenario,
        custom_weights=custom_weights
    )
    
    df_preview = pd.DataFrame({
        "Facility": area_stats["SystemCodeNumber"],
        "Capacity": capacities,
        "UtilizationPct": utils,
        "PriorityWeight": weights
    })
    return df_preview
