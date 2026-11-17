"""
test_phase1_data.py
Unit and validation tests for Phase 1: Data Loading, Cleaning, and Exploratory Analysis.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np

# Ensure src is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from data_loader import load_raw_data, get_dataset_metadata, REQUIRED_COLUMNS
from data_cleaning import clean_parking_data
from exploratory_analysis import (
    get_overall_system_kpis,
    get_parking_area_statistics,
    get_hourly_occupancy_trends,
    get_day_of_week_trends,
    get_top_and_bottom_utilized_areas
)


class TestPhase1DataPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.raw_df = load_raw_data()
        cls.clean_df, cls.audit = clean_parking_data(cls.raw_df)

    def test_raw_data_schema(self):
        """Verify raw data has required columns and non-empty rows."""
        for col in REQUIRED_COLUMNS:
            self.assertIn(col, self.raw_df.columns)
        self.assertEqual(len(self.raw_df), 1000)

    def test_smart_parking_categories_present(self):
        """Verify the Smart Parking dataset contains realistic user and vehicle categories."""
        meta = get_dataset_metadata(self.raw_df)
        self.assertIn("user_categories", meta)
        self.assertIn("vehicle_categories", meta)
        self.assertGreater(len(meta["user_categories"]), 0)
        self.assertGreater(len(meta["vehicle_categories"]), 0)

    def test_duplicate_removal(self):
        """Ensure deduplication verified zero duplicates or handled cleanly."""
        self.assertEqual(self.audit["exact_duplicates_removed"], 0)
        self.assertEqual(len(self.clean_df), 1000)
        self.assertFalse(self.clean_df.duplicated(subset=["SystemCodeNumber", "LastUpdated"]).any())

    def test_negative_occupancy_handled(self):
        """Ensure all negative occupancies are sanitized to >= 0."""
        self.assertEqual(self.audit["negative_occupancy_count"], 0)
        self.assertTrue((self.clean_df["Occupancy_Cleaned"] >= 0).all())

    def test_derived_columns_exist(self):
        """Verify operational columns are present and mathematically consistent."""
        expected_cols = ["Occupancy_Cleaned", "AvailableSpaces", "OccupancyRate", 
                         "EffectiveUtilization", "IsOverflow", "Date", "Hour", "DayOfWeek"]
        for c in expected_cols:
            self.assertIn(c, self.clean_df.columns)
        
        # AvailableSpaces = max(0, Capacity - Occupancy_Cleaned)
        expected_avail = (self.clean_df["Capacity"] - self.clean_df["Occupancy_Cleaned"]).clip(lower=0)
        pd.testing.assert_series_equal(self.clean_df["AvailableSpaces"], expected_avail, check_names=False)

    def test_parking_area_count_and_capacity(self):
        """Verify 4 unique parking zones and total capacity of 193 bays."""
        area_stats = get_parking_area_statistics(self.clean_df)
        self.assertEqual(len(area_stats), 4)
        self.assertEqual(area_stats["Capacity"].sum(), 193)

    def test_system_kpis(self):
        """Verify system KPI calculation and logical bounds."""
        kpis = get_overall_system_kpis(self.clean_df)
        self.assertEqual(kpis["total_parking_areas"], 4)
        self.assertEqual(kpis["total_system_capacity"], 193)
        self.assertGreater(kpis["peak_system_occupancy"], 0)
        self.assertLessEqual(kpis["peak_system_occupancy"], kpis["total_system_capacity"])
        self.assertGreater(kpis["avg_system_utilization_pct"], 0)
        self.assertLess(kpis["avg_system_utilization_pct"], 100)

    def test_hourly_trends(self):
        """Verify hourly aggregations cover the 24-hour cycle."""
        hourly = get_hourly_occupancy_trends(self.clean_df)
        self.assertEqual(len(hourly), 24)
        self.assertTrue((hourly["Hour"] >= 0).all() and (hourly["Hour"] <= 23).all())

    def test_top_and_bottom_lots(self):
        """Verify top and bottom utilized parking zones."""
        area_stats = get_parking_area_statistics(self.clean_df)
        top_lots, bottom_lots = get_top_and_bottom_utilized_areas(area_stats, 2)
        self.assertEqual(len(top_lots), 2)
        self.assertEqual(len(bottom_lots), 2)
        self.assertGreaterEqual(top_lots["AvgUtilizationPct"].min(), bottom_lots["AvgUtilizationPct"].max())


if __name__ == "__main__":
    unittest.main()
