"""
test_backend_functionality.py
Comprehensive unit tests for the data ingestion, cleaning, demand estimation,
and edge-case error handling across the backend pipeline.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import tempfile
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

for p in [PROJECT_ROOT, SRC_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from data_loader import load_raw_data, find_dataset_file, REQUIRED_COLUMNS
from data_cleaning import clean_parking_data
from exploratory_analysis import get_parking_area_statistics, get_overall_system_kpis
from demand_estimation import estimate_facility_demand, get_demand_summary_statistics


class TestBackendFunctionality(unittest.TestCase):
    """Verifies dataset processing, cleaning, demand models, and error handling."""

    def test_raw_data_loading_and_schema(self):
        df_raw = load_raw_data()
        self.assertIsInstance(df_raw, pd.DataFrame)
        self.assertEqual(len(df_raw), 1000)
        for col in REQUIRED_COLUMNS:
            self.assertIn(col, df_raw.columns)

    def test_missing_file_handling(self):
        with self.assertRaises(FileNotFoundError):
            load_raw_data("non_existent_path_parking.csv")

    def test_data_cleaning_and_deduplication(self):
        df_raw = load_raw_data()
        df_clean, audit = clean_parking_data(df_raw)
        
        # Verify deduplication
        self.assertEqual(audit["raw_record_count"], 1000)
        self.assertEqual(audit["key_duplicates_removed"], 0)
        self.assertEqual(len(df_clean), 1000)
        
        # Verify negative occupancy clipped
        self.assertTrue((df_clean["Occupancy_Cleaned"] >= 0).all())
        self.assertEqual(audit["negative_occupancy_count"], 0)
        
        # Verify datetime decomposition
        for col in ["Date", "Hour", "DayOfWeek", "IsWeekend"]:
            self.assertIn(col, df_clean.columns)

    def test_demand_estimators_hierarchy(self):
        df_raw = load_raw_data()
        df_clean, _ = clean_parking_data(df_raw)
        
        d_mean = estimate_facility_demand(df_clean, method="mean")
        d_p85 = estimate_facility_demand(df_clean, method="p85")
        d_p95 = estimate_facility_demand(df_clean, method="p95")
        d_max = estimate_facility_demand(df_clean, method="max")
        
        total_mean = d_mean["EstimatedDemand"].sum()
        total_p85 = d_p85["EstimatedDemand"].sum()
        total_p95 = d_p95["EstimatedDemand"].sum()
        total_max = d_max["EstimatedDemand"].sum()
        
        # Monotonicity: Mean <= P85 <= P95 <= Max
        self.assertLessEqual(total_mean, total_p85)
        self.assertLessEqual(total_p85, total_p95)
        self.assertLessEqual(total_p95, total_max)

    def test_empty_dataframe_handling(self):
        empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        clean_df, audit = clean_parking_data(empty_df)
        self.assertEqual(len(clean_df), 0)
        self.assertEqual(audit["cleaned_record_count"], 0)


if __name__ == "__main__":
    unittest.main()
