"""
exploratory_analysis.py
Exploratory Data Analysis (EDA) module for Smart Parking Management data.
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

    # Individual observation metrics
    mean_obs_occupancy = float(df_clean["Occupancy_Cleaned"].mean())
    median_obs_occupancy = float(df_clean["Occupancy_Cleaned"].median())
    peak_obs_occupancy = int(df_clean["Occupancy_Cleaned"].max())
    peak_system_time = str(df_clean.loc[df_clean["Occupancy_Cleaned"].idxmax(), "LastUpdated"])
    mean_obs_available = float(df_clean["AvailableSpaces"].mean())
    mean_obs_utilization = float(df_clean["OccupancyRate"].mean())
    peak_obs_utilization = float(df_clean["OccupancyRate"].max())

    return {
        "total_parking_areas": total_lots,
        "total_system_capacity": total_capacity,
        "avg_system_occupancy": round(mean_obs_occupancy, 1),
        "median_system_occupancy": round(median_obs_occupancy, 1),
        "peak_system_occupancy": peak_obs_occupancy,
        "peak_system_timestamp": peak_system_time,
        "avg_system_utilization_pct": round(mean_obs_utilization, 2),
        "peak_system_utilization_pct": round(peak_obs_utilization, 2),
        "mean_observation_occupancy": round(mean_obs_occupancy, 1),
        "mean_observation_available": round(mean_obs_available, 1),
        "mean_observation_utilization_pct": round(mean_obs_utilization, 2),
        "date_start": str(df_clean["Date"].min()),
        "date_end": str(df_clean["Date"].max()),
        "total_days_observed": int(df_clean["Date"].nunique()),
    }


def get_parking_area_statistics(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates occupancy metrics by parking area (Zone A, B, C, D).
    Classifies areas into High (>65%), Moderate (40-65%), and Low (<40%) demand tiers.
    """
    stats = (
        df_clean.groupby("SystemCodeNumber")
        .agg(
            Capacity=("Capacity", "first"),
            RecordCount=("Occupancy_Cleaned", "count"),
            AvgOccupancy=("Occupancy_Cleaned", "mean"),
            MedianOccupancy=("Occupancy_Cleaned", "median"),
            StdOccupancy=("Occupancy_Cleaned", "std"),
            MaxOccupancy=("Occupancy_Cleaned", "max"),
            MinOccupancy=("Occupancy_Cleaned", "min"),
            AvgAvailable=("AvailableSpaces", "mean"),
            OverflowCount=("IsOverflow", "sum"),
        )
        .reset_index()
    )

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
    float_cols = [
        "AvgOccupancy",
        "MedianOccupancy",
        "StdOccupancy",
        "AvgAvailable",
        "AvgUtilizationPct",
        "PeakUtilizationPct",
    ]
    stats[float_cols] = stats[float_cols].round(2)

    return stats


def get_hourly_occupancy_trends(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates occupancy statistics across hours of the day (0 to 23).
    """
    hourly = (
        df_clean.groupby("Hour")
        .agg(
            AvgOccupancy=("Occupancy_Cleaned", "mean"),
            MedianOccupancy=("Occupancy_Cleaned", "median"),
            MinOccupancy=("Occupancy_Cleaned", "min"),
            MaxOccupancy=("Occupancy_Cleaned", "max"),
            AvgUtilizationPct=("OccupancyRate", "mean"),
            RecordCount=("Occupancy_Cleaned", "count"),
        )
        .reset_index()
    )

    hourly[["AvgOccupancy", "MedianOccupancy", "AvgUtilizationPct"]] = hourly[
        ["AvgOccupancy", "MedianOccupancy", "AvgUtilizationPct"]
    ].round(2)
    return hourly


def get_day_of_week_trends(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates occupancy statistics by day of the week.
    """
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    dow = (
        df_clean.groupby("DayOfWeek")
        .agg(
            AvgOccupancy=("Occupancy_Cleaned", "mean"),
            MedianOccupancy=("Occupancy_Cleaned", "median"),
            AvgUtilizationPct=("OccupancyRate", "mean"),
            RecordCount=("Occupancy_Cleaned", "count"),
        )
        .reindex(day_order)
        .reset_index()
    )

    dow[["AvgOccupancy", "MedianOccupancy", "AvgUtilizationPct"]] = dow[
        ["AvgOccupancy", "MedianOccupancy", "AvgUtilizationPct"]
    ].round(2)
    return dow


def get_vehicle_type_distribution(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Distribution of vehicle types in smart parking events.
    """
    if "Vehicle_Type" not in df_clean.columns:
        return pd.DataFrame()
    dist = (
        df_clean.groupby("Vehicle_Type")
        .agg(
            Count=("SystemCodeNumber", "count"),
            AvgDuration=("Parking_Duration", "mean") if "Parking_Duration" in df_clean.columns else ("SystemCodeNumber", "count"),
            OccupiedSpots=("IsOccupiedSpot", "sum") if "IsOccupiedSpot" in df_clean.columns else ("SystemCodeNumber", "count"),
        )
        .reset_index()
    )
    dist["Percentage"] = (dist["Count"] / len(df_clean) * 100).round(2)
    return dist


def get_user_type_distribution(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Distribution of user categories (Registered, Visitor, Staff).
    """
    if "User_Type" not in df_clean.columns:
        return pd.DataFrame()
    dist = (
        df_clean.groupby("User_Type")
        .agg(
            Count=("SystemCodeNumber", "count"),
            AvgPayment=("Payment_Amount", "mean") if "Payment_Amount" in df_clean.columns else ("SystemCodeNumber", "count"),
        )
        .reset_index()
    )
    dist["Percentage"] = (dist["Count"] / len(df_clean) * 100).round(2)
    return dist


def get_top_and_bottom_utilized_areas(
    area_stats_df: pd.DataFrame, top_n: int = 2
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns top N highest utilized and bottom N lowest utilized parking areas.
    """
    n = min(top_n, len(area_stats_df))
    top_lots = area_stats_df.head(n).copy()
    bottom_lots = area_stats_df.tail(n).copy().iloc[::-1]
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
        "day_of_week_csv": dow_path,
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

    print("\n--- PARKING AREA STATISTICS ---")
    print(area_stats[["SystemCodeNumber", "Capacity", "AvgOccupancy", "AvgUtilizationPct", "DemandCategory"]].to_string())

    print("\nSummary CSV files generated in outputs directory:")
    for k, v in files.items():
        print(f"  {k}: {v}")
