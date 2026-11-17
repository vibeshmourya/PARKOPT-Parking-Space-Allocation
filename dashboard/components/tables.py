"""
tables.py
Clean, formatted interactive and styled table components for PARKOPT Streamlit application.
"""

from typing import List, Optional
import pandas as pd
import streamlit as st
from dashboard.utils.formatting import format_number, format_pct, format_utilization_bar


def render_styled_dataframe(
    df: pd.DataFrame,
    columns_config: Optional[dict] = None,
    use_container_width: bool = True,
    height: Optional[int] = None
) -> None:
    """
    Renders an interactive DataFrame using Streamlit's native st.dataframe with custom formatting.
    """
    st.dataframe(
        df,
        column_config=columns_config,
        use_container_width=use_container_width,
        height=height,
        hide_index=True
    )


def render_facility_summary_table(area_stats_df: pd.DataFrame) -> None:
    """
    Renders a formatted facility summary table with progress bars and badges.
    """
    display_df = area_stats_df.copy()
    if "MaxOccupancy" in display_df.columns and "PeakOccupancy" not in display_df.columns:
        display_df["PeakOccupancy"] = display_df["MaxOccupancy"]
    if "AvgAvailable" in display_df.columns and "AvgAvailability" not in display_df.columns:
        display_df["AvgAvailability"] = display_df["AvgAvailable"]
    
    # Configure columns for modern presentation
    column_config = {
        "SystemCodeNumber": st.column_config.TextColumn("Facility ID", width="medium"),
        "Capacity": st.column_config.NumberColumn("Physical Capacity", format="%d bays"),
        "AvgOccupancy": st.column_config.NumberColumn("Avg Occupancy", format="%.1f cars"),
        "PeakOccupancy": st.column_config.NumberColumn("Peak Occupancy", format="%d cars"),
        "AvgUtilizationPct": st.column_config.ProgressColumn(
            "Avg Utilization",
            help="Average historical utilization percentage",
            format="%.1f%%",
            min_value=0,
            max_value=100
        ),
        "OverflowCount": st.column_config.NumberColumn("Overflow Events", format="%d"),
        "AvgAvailability": st.column_config.NumberColumn("Avg Available", format="%.1f bays")
    }

    cols_to_show = [
        "SystemCodeNumber", "Capacity", "AvgOccupancy", "PeakOccupancy",
        "AvgUtilizationPct", "OverflowCount", "AvgAvailability"
    ]
    cols_present = [c for c in cols_to_show if c in display_df.columns]
    
    render_styled_dataframe(display_df[cols_present], columns_config=column_config, height=520)


def render_allocation_comparison_table(comp_df: pd.DataFrame) -> None:
    """
    Renders allocation results comparing Baseline vs PuLP LP Optimization.
    """
    df = comp_df.copy()
    
    column_config = {
        "Facility": st.column_config.TextColumn("Facility", width="medium"),
        "PhysicalCapacity": st.column_config.NumberColumn("Capacity", format="%d"),
        "EstimatedDemand": st.column_config.NumberColumn("Demand (d_i)", format="%d"),
        "PriorityWeight": st.column_config.NumberColumn("Weight (w_i)", format="%.2f"),
        "BaselineAllocation": st.column_config.NumberColumn("Baseline (x_base)", format="%d"),
        "OptimizedAllocation": st.column_config.NumberColumn("PuLP LP (x_opt)", format="%d"),
        "AllocationDifference": st.column_config.NumberColumn("Reallocation (Δ)", format="%+d"),
        "OptimizedUnmetDemand": st.column_config.NumberColumn("Unmet Demand", format="%d"),
        "OptimizedUtilizationPct": st.column_config.ProgressColumn(
            "Cap Utilization",
            format="%.1f%%",
            min_value=0,
            max_value=100
        )
    }

    cols_to_show = [
        "Facility", "PhysicalCapacity", "EstimatedDemand", "PriorityWeight",
        "BaselineAllocation", "OptimizedAllocation", "AllocationDifference",
        "OptimizedUnmetDemand", "OptimizedUtilizationPct"
    ]
    cols_present = [c for c in cols_to_show if c in df.columns]
    
    render_styled_dataframe(df[cols_present], columns_config=column_config, height=600)


def render_simple_results_table(comp_df: pd.DataFrame) -> None:
    """
    Renders clean, simplified summary table requested for Section 4:
    Columns: Parking Facility | Estimated Demand | Recommended Allocation | Unmet Demand
    """
    df = comp_df.copy()
    
    column_config = {
        "Facility": st.column_config.TextColumn("Parking Facility", width="medium"),
        "EstimatedDemand": st.column_config.NumberColumn("Estimated Demand", format="%d permits"),
        "OptimizedAllocation": st.column_config.NumberColumn("Recommended Allocation", format="%d permits"),
        "OptimizedUnmetDemand": st.column_config.NumberColumn("Unmet Demand", format="%d permits")
    }

    cols = ["Facility", "EstimatedDemand", "OptimizedAllocation", "OptimizedUnmetDemand"]
    cols_present = [c for c in cols if c in df.columns]
    
    render_styled_dataframe(df[cols_present], columns_config=column_config, height=450)

