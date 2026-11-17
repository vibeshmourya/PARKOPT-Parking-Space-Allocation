"""
data_loader.py
Module for loading and verifying the Parking Birmingham dataset.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Optional, Dict, Any, Tuple
import pandas as pd


DEFAULT_DATA_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "parking_birmingham.csv"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset.csv"),
    "data/parking_birmingham.csv",
    "dataset.csv"
]

REQUIRED_COLUMNS = ["SystemCodeNumber", "Capacity", "Occupancy", "LastUpdated"]


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
        "Parking dataset file not found. Please ensure 'data/parking_birmingham.csv' "
        "or 'dataset.csv' exists in the workspace root or data folder."
    )


def load_raw_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the raw CSV dataset into a pandas DataFrame and verifies expected schema.
    """
    target_path = find_dataset_file(filepath)
    df = pd.read_csv(target_path)
    
    # Check for required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")
        
    return df


def get_dataset_metadata(df: pd.DataFrame, filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspects and extracts metadata from the dataset.
    Identifies column mapping, types, row count, and verifies non-existence
    of assumed user categories (students, faculty, etc.).
    """
    actual_path = find_dataset_file(filepath) if filepath or os.path.exists("data/parking_birmingham.csv") else "dataset.csv"
    file_size_bytes = os.path.getsize(actual_path) if os.path.exists(actual_path) else 0

    # Field mapping verification
    field_mapping = {
        "Parking Area Identifier": "SystemCodeNumber" if "SystemCodeNumber" in df.columns else None,
        "Parking Capacity": "Capacity" if "Capacity" in df.columns else None,
        "Observed Occupancy": "Occupancy" if "Occupancy" in df.columns else None,
        "Timestamp": "LastUpdated" if "LastUpdated" in df.columns else None,
    }

    # Verify absence of demographic or user class columns
    assumed_user_categories = ["Faculty", "Student", "Staff", "Visitor", "UserType", "VehicleType"]
    present_user_categories = [cat for cat in assumed_user_categories if cat.lower() in [c.lower() for c in df.columns]]

    return {
        "file_path": actual_path,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
        "total_records": len(df),
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "field_mapping": field_mapping,
        "assumed_categories_found": present_user_categories,
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
    }


if __name__ == "__main__":
    df_raw = load_raw_data()
    meta = get_dataset_metadata(df_raw)
    print("Dataset successfully loaded.")
    for k, v in meta.items():
        print(f"{k}: {v}")

