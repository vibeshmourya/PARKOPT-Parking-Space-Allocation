"""
data_service.py
Data access and caching service for the PARKOPT Streamlit application.
Loads and caches verified datasets and analytical summaries from Phase 1-4.
"""

import os
import sys
import tempfile
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
import streamlit as st

# Prevent matplotlib cache dir warning
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

# Ensure project root and src/ are in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

for path in [PROJECT_ROOT, SRC_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from data_loader import load_raw_data
from data_cleaning import clean_parking_data
from exploratory_analysis import (
    get_parking_area_statistics,
    get_hourly_occupancy_trends,
    get_day_of_week_trends,
    get_overall_system_kpis
)
from demand_estimation import estimate_facility_demand


@st.cache_data(show_spinner="Loading Birmingham Parking Dataset...")
def load_cleaned_dataset() -> pd.DataFrame:
    """
    Loads raw CSV data and runs verified cleaning pipeline.
    Caches in memory for rapid interactive response across all pages.
    """
    # Prefer existing dataset.csv in data/ or root
    csv_candidates = [
        os.path.join(DATA_DIR, "parking_birmingham.csv"),
        os.path.join(DATA_DIR, "dataset.csv"),
        os.path.join(PROJECT_ROOT, "dataset.csv"),
        os.path.join(PROJECT_ROOT, "data", "parking_birmingham.csv")
    ]
    data_path = None
    for c in csv_candidates:
        if os.path.exists(c):
            data_path = c
            break

    df_raw = load_raw_data(data_path)
    res = clean_parking_data(df_raw)
    if isinstance(res, tuple):
        df_clean = res[0]
    else:
        df_clean = res
    return df_clean


@st.cache_data(show_spinner="Computing Facility Statistics...")
def load_facility_statistics(df_clean: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Returns facility statistics across all 30 parking areas.
    Uses outputs/parking_area_statistics.csv if present, or calculates from cleaned data.
    """
    stats_csv = os.path.join(OUTPUTS_DIR, "parking_area_statistics.csv")
    if os.path.exists(stats_csv):
        try:
            return pd.read_csv(stats_csv)
        except Exception:
            pass

    if df_clean is None:
        df_clean = load_cleaned_dataset()
    return get_parking_area_statistics(df_clean)


@st.cache_data(show_spinner="Loading Demand Estimates...")
def load_demand_estimates(method: str = "p95", df_clean: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Computes or retrieves demand estimates for all 30 facilities.
    """
    if df_clean is None:
        df_clean = load_cleaned_dataset()
    return estimate_facility_demand(df_clean, method=method)


@st.cache_data(show_spinner="Computing Temporal Trends...")
def load_temporal_data(df_clean: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns hourly trends and day-of-week trends DataFrames.
    """
    hourly_csv = os.path.join(OUTPUTS_DIR, "hourly_occupancy_trends.csv")
    day_csv = os.path.join(OUTPUTS_DIR, "day_of_week_trends.csv")
    
    if os.path.exists(hourly_csv) and os.path.exists(day_csv):
        try:
            h_df = pd.read_csv(hourly_csv)
            d_df = pd.read_csv(day_csv)
            return h_df, d_df
        except Exception:
            pass

    if df_clean is None:
        df_clean = load_cleaned_dataset()
    h_df = get_hourly_occupancy_trends(df_clean)
    d_df = get_day_of_week_trends(df_clean)
    return h_df, d_df


@st.cache_data(show_spinner="Loading System KPIs...")
def load_system_kpis(df_clean: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Calculates overall system KPIs: Total capacity, records, system utilization, etc.
    """
    if df_clean is None:
        df_clean = load_cleaned_dataset()
    raw_kpis = get_overall_system_kpis(df_clean)
    kpis = dict(raw_kpis)
    kpis["total_facilities"] = raw_kpis.get("total_parking_areas", 30)
    kpis["total_observations"] = len(df_clean)
    kpis["overall_mean_utilization_pct"] = raw_kpis.get("avg_system_utilization_pct", 44.59)
    return kpis


@st.cache_data(show_spinner="Loading Scenario Summaries...")
def load_scenario_summaries() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads precomputed canonical scenarios comparison summary and facility allocations.
    """
    summary_csv = os.path.join(OUTPUTS_DIR, "scenario_analysis_summary.csv")
    alloc_csv = os.path.join(OUTPUTS_DIR, "scenario_facility_allocations.csv")

    if os.path.exists(summary_csv) and os.path.exists(alloc_csv):
        summary_df = pd.read_csv(summary_csv)
        alloc_df = pd.read_csv(alloc_csv)
    else:
        from scenario_analysis import run_all_optimization_scenarios
        df_clean = load_cleaned_dataset()
        summary_df, alloc_df = run_all_optimization_scenarios(df_clean)

    # Standardize column names for flexible access
    col_map = {
        "BudgetPermits": "Budget",
        "TotalUnmetDemand": "UnmetDemand",
        "WeightedObjective": "ObjectiveValue"
    }
    for old_col, new_col in col_map.items():
        if old_col in summary_df.columns and new_col not in summary_df.columns:
            summary_df[new_col] = summary_df[old_col]

    return summary_df, alloc_df


@st.cache_data(show_spinner="Loading Sensitivity Data...")
def load_budget_sensitivity_data() -> pd.DataFrame:
    """
    Loads precomputed budget sensitivity sweep data.
    """
    sens_csv = os.path.join(OUTPUTS_DIR, "budget_sensitivity.csv")
    if os.path.exists(sens_csv):
        sens_df = pd.read_csv(sens_csv)
    else:
        from sensitivity_analysis import run_budget_sensitivity_analysis
        df_clean = load_cleaned_dataset()
        sens_df = run_budget_sensitivity_analysis(df_clean)

    # Standardize column aliases
    col_map = {
        "BudgetPermits": "Budget",
        "OptimizedAllocated": "TotalAllocated",
        "OptimizedUnmetDemand": "UnmetDemand",
        "OptimizedObjective": "ObjectiveValue",
        "FullySatisfiedFacilities": "FullySatisfiedCount",
        "PartiallySatisfiedFacilities": "PartiallySatisfiedCount",
        "ZeroAllocationFacilities": "ZeroAllocationCount",
        "MarginalValuePerPermit": "MarginalGain"
    }
    for old_col, new_col in col_map.items():
        if old_col in sens_df.columns and new_col not in sens_df.columns:
            sens_df[new_col] = sens_df[old_col]

    return sens_df
