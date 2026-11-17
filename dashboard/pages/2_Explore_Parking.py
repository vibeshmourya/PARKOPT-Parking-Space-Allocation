"""
2_Explore_Parking.py
Section 2: Parking Facilities for PARKOPT.
Allows users to search, filter, and inspect parking zones and IoT spots,
monitoring capacity, average/peak occupancy, availability, and diurnal patterns.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import streamlit as st
import pandas as pd
from dashboard.utils.formatting import (
    CUSTOM_DASHBOARD_CSS, format_number, format_pct
)
from dashboard.utils.data_service import (
    load_cleaned_dataset,
    load_facility_statistics,
    load_temporal_data
)
from dashboard.components.sidebar import render_sidebar
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.charts import (
    render_capacity_vs_occupancy_chart,
    render_facility_hourly_chart,
    render_temporal_diurnal_chart,
    render_hourly_heatmap_chart
)
from dashboard.components.tables import render_facility_summary_table


def render_explore_parking_page() -> None:
    """
    Renders Section 2: Parking Facilities.
    Provides zone search, selector, demand tier filters, 5 core metrics,
    utilization progress indicator, 2 responsive charts, spot-level inspection, and an expandable data table.
    """
    st.markdown(CUSTOM_DASHBOARD_CSS, unsafe_allow_html=True)
    render_sidebar()

    # 1. Header
    st.markdown(
        """<div class="hero-card">
<h1 class="hero-title">Smart Parking Zones Explorer</h1>
<div class="hero-subtitle">Zone Capacity, Observed Occupancy & Sensor Metrics</div>
<p class="hero-desc">Investigate historical parking patterns across Smart Parking zones (Zone A, B, C, D) and individual sensor bays. Identify congested bottleneck locations and underutilized capacity across 24 operating hours.</p>
</div>""",
        unsafe_allow_html=True
    )

    # 2. Load Data
    with st.spinner("Loading facility records..."):
        df_clean = load_cleaned_dataset()
        area_stats = load_facility_statistics(df_clean)
        hourly_df, day_df = load_temporal_data(df_clean)

    all_facilities = sorted(area_stats["SystemCodeNumber"].unique().tolist())

    # 3. Search & Filter Controls
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        selected_facility = st.selectbox(
            "Select Parking Zone to Inspect:",
            options=["All Zones"] + all_facilities,
            index=0,
            help="Select a specific Smart Parking zone to view detailed operational metrics."
        )
    with col_filter:
        demand_tier_filter = st.selectbox(
            "Filter by Demand Level:",
            options=["All Tiers", "High Demand (≥ 65%)", "Moderate Demand (40–65%)", "Low Demand (< 40%)"],
            index=0
        )

    # Filter statistics dataframe by demand tier
    filtered_stats = area_stats.copy()
    if demand_tier_filter == "High Demand (≥ 65%)":
        filtered_stats = filtered_stats[filtered_stats["AvgUtilizationPct"] >= 65.0]
    elif demand_tier_filter == "Moderate Demand (40–65%)":
        filtered_stats = filtered_stats[(filtered_stats["AvgUtilizationPct"] >= 40.0) & (filtered_stats["AvgUtilizationPct"] < 65.0)]
    elif demand_tier_filter == "Low Demand (< 40%)":
        filtered_stats = filtered_stats[filtered_stats["AvgUtilizationPct"] < 40.0]

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 4. Five Core Metrics & Utilization Indicator
    if selected_facility != "All Zones":
        fac_row = area_stats[area_stats["SystemCodeNumber"] == selected_facility].iloc[0]
        f_cap = int(fac_row["Capacity"])
        f_occ = float(fac_row["AvgOccupancy"])
        f_peak = int(fac_row["MaxOccupancy"])
        f_avail = max(0, f_cap - int(round(f_occ)))
        f_util = float(fac_row["AvgUtilizationPct"])

        # Display 5 core metrics using native Streamlit metric cards
        kpi_metrics = [
            {"label": "Physical Capacity", "value": f"{format_number(f_cap)} bays", "subtext": selected_facility, "border_left_color": "#2563EB"},
            {"label": "Average Occupancy", "value": f"{format_number(f_occ, decimals=1)} cars", "subtext": "Historical mean", "border_left_color": "#0F172A"},
            {"label": "Peak Occupancy", "value": f"{format_number(f_peak)} cars", "subtext": "Highest recorded", "border_left_color": "#EF4444" if f_peak > f_cap else "#F59E0B"},
            {"label": "Available Spaces", "value": f"{format_number(f_avail)} bays", "subtext": "Buffer capacity", "border_left_color": "#10B981"},
            {"label": "Utilization Rate", "value": format_pct(f_util), "subtext": "Occupancy share", "border_left_color": "#7E22CE"}
        ]
        render_kpi_row(kpi_metrics)

        # Easy-to-understand utilization indicator
        tier_label = "High Pressure (≥ 65%)" if f_util >= 65.0 else ("Moderate Demand (40–65%)" if f_util >= 40.0 else "Low Demand (< 40%)")
        tier_color = "#EF4444" if f_util >= 65.0 else ("#F59E0B" if f_util >= 40.0 else "#2563EB")

        with st.container(border=True):
            st.markdown(
                f"""<div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; color: #0F172A; margin-bottom: 6px;">
<span>Utilization Status: <b>{f_util:.1f}%</b></span>
<span style="color: {tier_color};">Category: {tier_label}</span>
</div>
<div style="background-color: #E2E8F0; border-radius: 6px; width: 100%; height: 10px; overflow: hidden;">
<div style="background-color: {tier_color}; width: {min(100.0, f_util):.1f}%; height: 100%;"></div>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #64748B; margin-top: 4px;">
<span>0% (Empty)</span>
<span>40% (Moderate Threshold)</span>
<span>65% (High Pressure Threshold)</span>
<span>100% (Full)</span>
</div>""",
                unsafe_allow_html=True
            )
    else:
        # System Aggregated Metrics across all 4 zones
        sys_cap = int(area_stats["Capacity"].sum())
        sys_avg_occ = float(area_stats["AvgOccupancy"].sum())
        sys_peak_occ = int(area_stats["MaxOccupancy"].sum())
        sys_avail = max(0, sys_cap - int(round(sys_avg_occ)))
        sys_util = (sys_avg_occ / sys_cap) * 100.0 if sys_cap > 0 else 0.0

        render_kpi_row([
            {"label": "Total Capacity", "value": f"{format_number(sys_cap)} bays", "subtext": "4 Smart Zones", "border_left_color": "#2563EB"},
            {"label": "Average Occupied", "value": f"{format_number(sys_avg_occ, decimals=0)} cars", "subtext": "System average", "border_left_color": "#0F172A"},
            {"label": "Peak Occupancy", "value": f"{format_number(sys_peak_occ)} cars", "subtext": "Sum of zone peaks", "border_left_color": "#F59E0B"},
            {"label": "Available Spaces", "value": f"{format_number(sys_avail)} bays", "subtext": "System buffer", "border_left_color": "#10B981"},
            {"label": "Average Utilization", "value": format_pct(sys_util), "subtext": "Overall utilization", "border_left_color": "#7E22CE"}
        ])

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 5. Two Primary Responsive Charts
    st.subheader("Zone Capacity & Hourly Occupancy Patterns")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Chart 1: Capacity vs Average Occupancy
        chart_data = filtered_stats if selected_facility == "All Zones" else area_stats[area_stats["SystemCodeNumber"] == selected_facility]
        fig_cap = render_capacity_vs_occupancy_chart(chart_data)
        st.plotly_chart(fig_cap, use_container_width=True)

    with chart_col2:
        # Chart 2: Historical Hourly Occupancy Trend
        target_code = selected_facility if selected_facility != "All Zones" else None
        fig_hourly = render_facility_hourly_chart(df_clean, target_code)
        st.plotly_chart(fig_hourly, use_container_width=True)

    # 6. Detailed Records Hidden Under Expandable Section
    with st.expander("📋 View Full Zone Dataset (4 Zones · 193 Sensor Bays)", expanded=False):
        st.caption("Complete table of monitored Smart Parking zones with physical capacity and historical statistics:")
        render_facility_summary_table(area_stats)
        csv_bytes = area_stats.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Zone Statistics (CSV)",
            data=csv_bytes,
            file_name="parking_zone_statistics.csv",
            mime="text/csv"
        )

    # 7. Advanced Analysis Expander
    with st.expander("📈 Advanced Diurnal & Heatmap Analysis", expanded=False):
        fig_diurnal = render_temporal_diurnal_chart(hourly_df, day_df)
        st.plotly_chart(fig_diurnal, use_container_width=True)

        fig_heat = render_hourly_heatmap_chart(df_clean)
        st.plotly_chart(fig_heat, use_container_width=True)


if __name__ == "__main__":
    render_explore_parking_page()
