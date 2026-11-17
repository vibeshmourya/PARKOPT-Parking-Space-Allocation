"""
demand_estimation.py
Estimates parking demand across Birmingham parking facilities using empirical observations.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np


DEMAND_METHODS = ["mean", "p85", "p95", "max"]
DEFAULT_DEMAND_METHOD = "p95"


def estimate_facility_demand(
    df_clean: pd.DataFrame,
    method: str = DEFAULT_DEMAND_METHOD
) -> pd.DataFrame:
    """
    Calculates estimated demand (d_i) for each of the 30 parking facilities.
    
    Supported Estimation Methods:
    1. 'mean': Historical arithmetic mean occupancy (baseline average demand).
    2. 'p85': 85th percentile occupancy (recurrent high-demand baseline).
    3. 'p95': 95th percentile occupancy (standard robust peak demand, default).
    4. 'max': Maximum observed occupancy (stress-test peak demand).
    
    Mathematical Handling:
    - Retains cleaned non-negative observations (O >= 0).
    - Retains observed overflow values (O > C) to avoid artificially truncating
      observed demand pressure.
    - Estimates are rounded to nearest non-negative integer for integer LP.
    - Notes right-censoring: Facilities that frequently cap out at 100% capacity
      likely experience unobserved latent demand (spillover drivers turned away).
    
    Returns:
        pd.DataFrame: Columns ['SystemCodeNumber', 'Capacity', 'EstimatedDemand', 
                              'MeanDemand', 'P85Demand', 'P95Demand', 'MaxDemand', 
                              'EstimationMethod', 'DemandPressureRatio']
    """
    method = method.lower()
    if method not in DEMAND_METHODS:
        raise ValueError(f"Unknown demand estimation method '{method}'. Choose from {DEMAND_METHODS}.")

    # Group by facility
    agg_df = df_clean.groupby("SystemCodeNumber").agg(
        Capacity=("Capacity", "first"),
        Mean=("Occupancy_Cleaned", "mean"),
        P85=("Occupancy_Cleaned", lambda x: float(np.percentile(x, 85))),
        P95=("Occupancy_Cleaned", lambda x: float(np.percentile(x, 95))),
        Max=("Occupancy_Cleaned", "max"),
        RecordCount=("Occupancy_Cleaned", "count"),
        OverflowCount=("IsOverflow", "sum")
    ).reset_index()

    # Round estimates to integer demand for LP models
    agg_df["MeanDemand"] = agg_df["Mean"].round().astype(int)
    agg_df["P85Demand"] = agg_df["P85"].round().astype(int)
    agg_df["P95Demand"] = agg_df["P95"].round().astype(int)
    agg_df["MaxDemand"] = agg_df["Max"].astype(int)

    # Select target method demand
    method_col_map = {
        "mean": "MeanDemand",
        "p85": "P85Demand",
        "p95": "P95Demand",
        "max": "MaxDemand"
    }
    agg_df["EstimatedDemand"] = agg_df[method_col_map[method]]
    agg_df["EstimationMethod"] = method
    
    # Demand pressure ratio = EstimatedDemand / Capacity
    agg_df["DemandPressureRatio"] = (agg_df["EstimatedDemand"] / agg_df["Capacity"]).round(4)
    
    # Sort descending by demand pressure
    agg_df = agg_df.sort_values(by="DemandPressureRatio", ascending=False).reset_index(drop=True)
    
    return agg_df


def export_demand_estimates(
    df_clean: pd.DataFrame,
    output_dir: str = "outputs"
) -> str:
    """
    Generates all four demand estimation variants and saves to CSV.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "demand_estimates.csv")
    
    demand_df = estimate_facility_demand(df_clean, method=DEFAULT_DEMAND_METHOD)
    demand_df.to_csv(out_path, index=False)
    return out_path


def get_demand_summary_statistics(demand_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes system-wide totals across all demand estimation methods.
    """
    total_cap = int(demand_df["Capacity"].sum())
    total_mean = int(demand_df["MeanDemand"].sum())
    total_p85 = int(demand_df["P85Demand"].sum())
    total_p95 = int(demand_df["P95Demand"].sum())
    total_max = int(demand_df["MaxDemand"].sum())
    
    # Effective allocatable demand: sum of min(d_i, C_i)
    allocatable_p95 = int(np.minimum(demand_df["P95Demand"], demand_df["Capacity"]).sum())
    
    return {
        "total_physical_capacity": total_cap,
        "total_mean_demand": total_mean,
        "total_p85_demand": total_p85,
        "total_p95_demand": total_p95,
        "total_max_demand": total_max,
        "total_allocatable_p95_demand": allocatable_p95,
        "p95_vs_capacity_ratio": round(total_p95 / total_cap, 4)
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data
    
    raw = load_raw_data()
    clean, _ = clean_parking_data(raw)
    
    demands = estimate_facility_demand(clean, method="p95")
    summary = get_demand_summary_statistics(demands)
    out_file = export_demand_estimates(clean)
    
    print("Demand Estimation Module Ready.")
    print("Demand Summary Statistics:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"Exported demand estimates to: {out_file}")

