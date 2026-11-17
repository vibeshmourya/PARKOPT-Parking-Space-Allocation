"""
data_loader.py
Module for loading and verifying the Smart Parking Management Dataset.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Optional, Dict, Any, List
import pandas as pd


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

DEFAULT_DATA_PATHS = [
    os.path.join(PROJECT_ROOT, "data", "processed", "parking_sample_1500.csv"),
    os.path.join(PROJECT_ROOT, "data", "raw", "IIoT_Smart_Parking_Management.csv"),
    os.path.join(PROJECT_ROOT, "IIoT_Smart_Parking_Management.csv"),
    "data/processed/parking_sample_1500.csv",
    "data/raw/IIoT_Smart_Parking_Management.csv",
    "IIoT_Smart_Parking_Management.csv",
]

# Section capacity mapping based on physical unique parking bays observed
SECTION_CAPACITIES = {
    "Zone A": 50,
    "Zone B": 50,
    "Zone C": 49,
    "Zone D": 44,
}

REQUIRED_CORE_COLUMNS = ["Parking_Lot_Section", "Parking_Spot_ID", "Timestamp"]
STANDARDIZED_COLUMNS = ["SystemCodeNumber", "Capacity", "Occupancy", "LastUpdated"]
REQUIRED_COLUMNS = STANDARDIZED_COLUMNS


def find_dataset_file(custom_path: Optional[str] = None) -> str:
    """
    Locates the dataset file from standard paths or a custom path.
    Raises FileNotFoundError if custom_path is specified but does not exist.
    """
    if custom_path:
        if os.path.exists(custom_path):
            return custom_path
        raise FileNotFoundError(f"Specified dataset file not found: '{custom_path}'")

    for path in DEFAULT_DATA_PATHS:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        "Smart Parking dataset file not found. Please ensure "
        "'data/processed/parking_sample_1500.csv' or "
        "'data/raw/IIoT_Smart_Parking_Management.csv' exists."
    )


def load_raw_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the smart parking CSV dataset into a pandas DataFrame.
    Automatically ensures standardized operational columns exist.
    """
    target_path = find_dataset_file(filepath)
    df = pd.read_csv(target_path)

    # If loading raw CSV directly without pre-computed standard fields
    if "Capacity" not in df.columns and "Parking_Lot_Section" in df.columns:
        df["Capacity"] = df["Parking_Lot_Section"].map(SECTION_CAPACITIES).fillna(50).astype(int)

    if "Occupancy" not in df.columns:
        if "Occupancy_Rate" in df.columns and "Capacity" in df.columns:
            df["Occupancy"] = (df["Occupancy_Rate"] * df["Capacity"]).round().astype(int)
        elif "Occupancy_Status" in df.columns:
            df["Occupancy"] = (df["Occupancy_Status"].str.lower() == "occupied").astype(int)

    if "SystemCodeNumber" not in df.columns and "Parking_Lot_Section" in df.columns:
        df["SystemCodeNumber"] = df["Parking_Lot_Section"]

    if "LastUpdated" not in df.columns and "Timestamp" in df.columns:
        df["LastUpdated"] = df["Timestamp"]

    if "Spot_Global_ID" not in df.columns and "Parking_Spot_ID" in df.columns and "Parking_Lot_Section" in df.columns:
        df["Spot_Global_ID"] = (
            df["Parking_Lot_Section"] + "_Spot" + df["Parking_Spot_ID"].astype(str).str.zfill(2)
        )

    # Validate essential schema
    missing_cols = [c for c in STANDARDIZED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required operational columns: {missing_cols}")

    return df


def get_dataset_metadata(df: pd.DataFrame, filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspects and extracts metadata from the dataset.
    """
    try:
        actual_path = find_dataset_file(filepath)
    except FileNotFoundError:
        actual_path = "data/processed/parking_sample_1500.csv"

    file_size_bytes = os.path.getsize(actual_path) if os.path.exists(actual_path) else 0

    field_mapping = {
        "Parking Area Identifier": "Parking_Lot_Section / SystemCodeNumber",
        "Parking Capacity": "Capacity (Zone A: 50, B: 50, C: 49, D: 44)",
        "Observed Occupancy": "Occupancy / Occupancy_Rate",
        "Timestamp": "Timestamp / LastUpdated",
        "Spot Identifier": "Parking_Spot_ID / Spot_Global_ID",
        "Vehicle Type": "Vehicle_Type" if "Vehicle_Type" in df.columns else None,
        "User Type": "User_Type" if "User_Type" in df.columns else None,
    }

    user_categories = df["User_Type"].unique().tolist() if "User_Type" in df.columns else []
    vehicle_categories = df["Vehicle_Type"].unique().tolist() if "Vehicle_Type" in df.columns else []
    zones = df["Parking_Lot_Section"].unique().tolist() if "Parking_Lot_Section" in df.columns else []

    return {
        "file_path": actual_path,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
        "total_records": len(df),
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "field_mapping": field_mapping,
        "parking_zones": zones,
        "total_zones": len(zones),
        "total_physical_capacity": sum(SECTION_CAPACITIES.values()),
        "user_categories": user_categories,
        "vehicle_categories": vehicle_categories,
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
    }


if __name__ == "__main__":
    df_raw = load_raw_data()
    meta = get_dataset_metadata(df_raw)
    print("Dataset successfully loaded.")
    for k, v in meta.items():
        print(f"  {k}: {v}")
