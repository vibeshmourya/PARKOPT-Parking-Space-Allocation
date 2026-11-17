"""
data_cleaning.py
Data preprocessing, cleaning, anomaly handling, and operational metrics calculation.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def clean_parking_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw parking data, handles anomalies, and calculates operational metrics.
    
    Cleaning Steps:
    1. Duplicate Detection & Removal: Deduplicates records on (SystemCodeNumber, LastUpdated).
    2. Missing Value Check: Verifies non-null counts.
    3. Anomaly Handling:
       - Negative Occupancy: Sensor calibration errors (clamped to 0).
       - Occupancy > Capacity: Real-world overflow / sensor drift (documented, retained in demand).
    4. DateTime Parsing: Decomposes LastUpdated into Date, Time, Hour, DayOfWeek, IsWeekend.
    5. Operational Fields:
       - Occupancy_Cleaned: Non-negative occupancy.
       - AvailableSpaces: Max(0, Capacity - Occupancy_Cleaned).
       - OccupancyRate: (Occupancy_Cleaned / Capacity) * 100.
       - EffectiveUtilization: Min(100.0, OccupancyRate).
       - IsOverflow: Boolean indicator for Occupancy > Capacity.
    
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Cleaned DataFrame and Audit Report dictionary.
    """
    raw_count = len(df)
    
    # 1. Duplicate detection
    exact_duplicates = int(df.duplicated().sum())
    key_duplicates = int(df.duplicated(subset=["SystemCodeNumber", "LastUpdated"]).sum())
    df_clean = df.drop_duplicates(subset=["SystemCodeNumber", "LastUpdated"]).copy()
    post_dedup_count = len(df_clean)
    
    # 2. Missing value check
    missing_summary = df_clean.isnull().sum().to_dict()
    
    # 3. Anomaly detection before cleaning
    negative_occ_mask = df_clean["Occupancy"] < 0
    negative_occ_count = int(negative_occ_mask.sum())
    negative_occ_samples = df_clean[negative_occ_mask][["SystemCodeNumber", "Occupancy", "LastUpdated"]].head(5).to_dict(orient="records")
    
    overflow_mask = df_clean["Occupancy"] > df_clean["Capacity"]
    overflow_count = int(overflow_mask.sum())
    overflow_samples = df_clean[overflow_mask][["SystemCodeNumber", "Capacity", "Occupancy", "LastUpdated"]].head(5).to_dict(orient="records")
    
    # Capacity consistency per parking area
    cap_consistency = df_clean.groupby("SystemCodeNumber")["Capacity"].nunique()
    inconsistent_capacities = cap_consistency[cap_consistency > 1].to_dict()
    
    # 4. Clean occupancy & add derived operational metrics
    df_clean["Occupancy_Raw"] = df_clean["Occupancy"]
    df_clean["Occupancy_Cleaned"] = df_clean["Occupancy"].clip(lower=0)
    df_clean["AvailableSpaces"] = (df_clean["Capacity"] - df_clean["Occupancy_Cleaned"]).clip(lower=0)
    df_clean["OccupancyRate"] = (df_clean["Occupancy_Cleaned"] / df_clean["Capacity"]) * 100.0
    df_clean["EffectiveUtilization"] = df_clean["OccupancyRate"].clip(upper=100.0)
    df_clean["IsOverflow"] = overflow_mask
    
    # 5. DateTime parsing
    df_clean["LastUpdated_dt"] = pd.to_datetime(df_clean["LastUpdated"])
    df_clean["Date"] = df_clean["LastUpdated_dt"].dt.date
    df_clean["DateStr"] = df_clean["LastUpdated_dt"].dt.strftime("%Y-%m-%d")
    df_clean["Hour"] = df_clean["LastUpdated_dt"].dt.hour
    df_clean["TimeStr"] = df_clean["LastUpdated_dt"].dt.strftime("%H:%M:%S")
    df_clean["DayOfWeek"] = df_clean["LastUpdated_dt"].dt.day_name()
    df_clean["DayOfWeekNum"] = df_clean["LastUpdated_dt"].dt.dayofweek  # 0=Monday, 6=Sunday
    df_clean["IsWeekend"] = df_clean["DayOfWeekNum"].isin([5, 6])
    
    # Audit summary
    audit_report = {
        "raw_record_count": raw_count,
        "exact_duplicates_removed": exact_duplicates,
        "key_duplicates_removed": key_duplicates,
        "cleaned_record_count": post_dedup_count,
        "missing_values": missing_summary,
        "negative_occupancy_count": negative_occ_count,
        "negative_occupancy_action": "Clipped to 0 (sensor recalibration anomaly)",
        "negative_occupancy_samples": negative_occ_samples,
        "overflow_count": overflow_count,
        "overflow_percentage": round((overflow_count / post_dedup_count) * 100, 2) if post_dedup_count > 0 else 0.0,
        "overflow_action": "Retained as unconstrained observed demand pressure; effective utilization capped at 100%",
        "overflow_samples": overflow_samples,
        "inconsistent_capacities": inconsistent_capacities,
        "date_range_start": str(df_clean["LastUpdated_dt"].min()),
        "date_range_end": str(df_clean["LastUpdated_dt"].max()),
        "total_days_spanned": df_clean["Date"].nunique()
    }
    
    return df_clean, audit_report


if __name__ == "__main__":
    from data_loader import load_raw_data
    df = load_raw_data()
    clean_df, audit = clean_parking_data(df)
    print("Data cleaning completed successfully.")
    print("Audit Report:")
    for k, v in audit.items():
        print(f"  {k}: {v}")

