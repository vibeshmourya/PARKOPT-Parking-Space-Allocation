"""
exploratory_analysis.py
Exploratory Data Analysis (EDA) module for Birmingham Parking data.
Aggregates occupancy, calculates utilization metrics, and detects demand patterns.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def get_overall_system_kpis(df_clean: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes system-level Key Performance Indicators (KPIs).
    """
    # Unique lot capacities
    lot_capacities = df_clean.groupby("SystemCodeNumber")["Capacity"].first()
    total_capacity = int(lot_capacities.sum())
    total_lots = int(df_clean["SystemCodeNumber"].nunique())
    
    # Snapshot system-wide occupancy (sum of lots at each timestamp)
    snapshot_agg = df_clean.groupby("LastUpdated")["Occupancy_Cleaned"].sum()
    peak_system_occupancy = int(snapshot_agg.max())
    peak_system_time = str(snapshot_agg.idxmax())
    avg_system_occupancy = float(snapshot_agg.mean())
    median_system_occupancy = float(snapshot_agg.median())
    
    # System utilization
    avg_system_utilization = (avg_system_occupancy / total_capacity) * 100.0 if total_capacity > 0 else 0.0
    peak_system_utilization = (peak_system_occupancy / total_capacity) * 100.0 if total_capacity > 0 else 0.0
    
    # Individual observation metrics
    mean_obs_occupancy = float(df_clean["Occupancy_Cleaned"].mean())
    mean_obs_available = float(df_clean["AvailableSpaces"].mean())
    mean_obs_utilization = float(df_clean["OccupancyRate"].mean())
    
    return {
        "total_parking_areas": total_lots,
        "total_system_capacity": total_capacity,
        "avg_system_occupancy": round(avg_system_occupancy, 1),
        "median_system_occupancy": round(median_system_occupancy, 1),
        "peak_system_occupancy": peak_system_occupancy,
        "peak_system_timestamp": peak_system_time,
        "avg_system_utilization_pct": round(avg_system_utilization, 2),
        "peak_system_utilization_pct": round(peak_system_utilization, 2),
        "mean_observation_occupancy": round(mean_obs_occupancy, 1),
        "mean_observation_available": round(mean_obs_available, 1),
        "mean_observation_utilization_pct": round(mean_obs_utilization, 2),
        "date_start": str(df_clean["Date"].min()),
        "date_end": str(df_clean["Date"].max()),
        "total_days_observed": int(df_clean["Date"].nunique())
    }


def get_parking_area_statistics(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates occupancy metrics by parking area.
    Classifies areas into High (>65%), Moderate (40-65%), and Low (<40%) demand tiers.
    """
    stats = df_clean.groupby("SystemCodeNumber").agg(
        Capacity=("Capacity", "first"),
        RecordCount=("Occupancy_Cleaned", "count"),
        AvgOccupancy=("Occupancy_Cleaned", "mean"),
        MedianOccupancy=("Occupancy_Cleaned", "median"),
        StdOccupancy=("Occupancy_Cleaned", "std"),
        MaxOccupancy=("Occupancy_Cleaned", "max"),
        MinOccupancy=("Occupancy_Cleaned", "min"),
        AvgAvailable=("AvailableSpaces", "mean"),
        OverflowCount=("IsOverflow", "sum")
    ).reset_index()

    # Derived metrics
    stats["AvgUtilizationPct"] = (stats["AvgOccupancy"] / stats["Capacity"]) * 100.0
    stats["PeakUtilizationPct"] = (stats["MaxOccupancy"] / stats["Capacity"]) * 100.0
    stats["StdOccupancy"] = stats["StdOccupancy"].fillna(0.0)
    
    # Demand Classification based on average utilization
    def classify_demand(util: float) -> str:
        if util >= 65.0:
            return "High Demand (Severe Pressure)"
        elif util >= 40.0:
            return "Moderate Demand (Normal Operations)"
        else:
            return "Low Demand (Chronic Underutilization)"
            
    stats["DemandCategory"] = stats["AvgUtilizationPct"].apply(classify_demand)
    
    # Sort descending by average utilization
    stats = stats.sort_values(by="AvgUtilizationPct", ascending=False).reset_index(drop=True)
    
    # Round numerical columns
    float_cols = ["AvgOccupancy", "MedianOccupancy", "StdOccupancy", "AvgAvailable", 
                  "AvgUtilizationPct", "PeakUtilizationPct"]
    stats[float_cols] = stats[float_cols].round(2)
    
    return stats


def get_hourly_occupancy_trends(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates occupancy statistics across hours of the day (07:00 - 16:00).
    """
    hourly = df_clean.groupby("Hour").agg(
        AvgOccupancy=("Occupancy_Cleaned", "mean"),
        MedianOccupancy=("Occupancy_Cleaned", "median"),
        MinOccupancy=("Occupancy_Cleaned", "min"),
        MaxOccupancy=("Occupancy_Cleaned", "max"),
        AvgUtilizationPct=("OccupancyRate", "mean"),
        RecordCount=("Occupancy_Cleaned", "count")
    ).reset_index()
    
    hourly[["AvgOccupancy", "MedianOccupancy", "AvgUtilizationPct"]] = (
        hourly[["AvgOccupancy", "MedianOccupancy", "AvgUtilizationPct"]].round(2)
    )
    return hourly


def get_day_of_week_trends(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates occupancy statistics by day of the week.
    """
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    dow = df_clean.groupby("DayOfWeek").agg(
        AvgOccupancy=("Occupancy_Cleaned", "mean"),
        MedianOccupancy=("Occupancy_Cleaned", "median"),
        AvgUtilizationPct=("OccupancyRate", "mean"),
        RecordCount=("Occupancy_Cleaned", "count")
    ).reindex(day_order).reset_index()
    
    dow[["AvgOccupancy", "MedianOccupancy", "AvgUtilizationPct"]] = (
        dow[["AvgOccupancy", "MedianOccupancy", "AvgUtilizationPct"]].round(2)
    )
    return dow


def get_top_and_bottom_utilized_areas(
    area_stats_df: pd.DataFrame, top_n: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns top N highest utilized (overloaded) and bottom N lowest utilized (underutilized) parking areas.
    """
    top_lots = area_stats_df.head(top_n).copy()
    bottom_lots = area_stats_df.tail(top_n).copy().iloc[::-1]  # reverse to show lowest first
    return top_lots, bottom_lots


def generate_eda_summary_tables(df_clean: pd.DataFrame, output_dir: str = "outputs") -> Dict[str, str]:
    """
    Exports summary tables to CSV in the output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    area_stats = get_parking_area_statistics(df_clean)
    hourly_trends = get_hourly_occupancy_trends(df_clean)
    dow_trends = get_day_of_week_trends(df_clean)
    
    area_stats_path = os.path.join(output_dir, "parking_area_statistics.csv")
    hourly_path = os.path.join(output_dir, "hourly_occupancy_trends.csv")
    dow_path = os.path.join(output_dir, "day_of_week_trends.csv")
    
    area_stats.to_csv(area_stats_path, index=False)
    hourly_trends.to_csv(hourly_path, index=False)
    dow_trends.to_csv(dow_path, index=False)
    
    return {
        "area_statistics_csv": area_stats_path,
        "hourly_trends_csv": hourly_path,
        "day_of_week_csv": dow_path
    }


if __name__ == "__main__":
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data
    
    df_raw = load_raw_data()
    df_clean, audit = clean_parking_data(df_raw)
    
    kpis = get_overall_system_kpis(df_clean)
    area_stats = get_parking_area_statistics(df_clean)
    top_lots, bottom_lots = get_top_and_bottom_utilized_areas(area_stats)
    files = generate_eda_summary_tables(df_clean)
    
    print("\n--- OVERALL SYSTEM KPIS ---")
    for k, v in kpis.items():
        print(f"{k}: {v}")
        
    print("\n--- TOP 5 HIGHEST UTILIZED LOTS ---")
    print(top_lots[["SystemCodeNumber", "Capacity", "AvgOccupancy", "AvgUtilizationPct", "DemandCategory"]].to_string())
    
    print("\n--- TOP 5 LOWEST UTILIZED LOTS ---")
    print(bottom_lots[["SystemCodeNumber", "Capacity", "AvgOccupancy", "AvgUtilizationPct", "DemandCategory"]].to_string())
    
    print("\nSummary CSV files generated in outputs directory:")
    for k, v in files.items():
        print(f"  {k}: {v}")

