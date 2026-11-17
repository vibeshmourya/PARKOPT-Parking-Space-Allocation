"""
temporal_charts.py
Visualizations for Diurnal, Weekly, and Heatmap Spatiotemporal Parking Dynamics.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .visualization_utils import (
    COLOR_PRIMARY_BLUE, COLOR_SECONDARY_BLUE, COLOR_EMERALD, COLOR_CRIMSON,
    COLOR_AMBER, COLOR_SLATE, COLOR_LIGHT_GRAY, COLOR_SALMON, COLOR_TEAL,
    PLOTLY_TEMPLATE, validate_required_columns, save_static_and_interactive
)


def plot_hourly_occupancy_trend(
    hourly_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/temporal"
) -> Dict[str, str]:
    """
    Visualization 4A: Diurnal Occupancy Curve (07:00 - 16:30).
    Annotates morning demand build-up, midday peak window, and afternoon departure clearance.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        hourly_df,
        ["Hour", "AvgOccupancy", "AvgUtilizationPct", "MaxOccupancy", "MinOccupancy"],
        "Hourly Occupancy Trend"
    )

    # --- 1. Matplotlib Static Plot ---
    fig_mpl, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hourly_df["Hour"], hourly_df["AvgOccupancy"], color=COLOR_PRIMARY_BLUE,
            marker="o", linewidth=2.8, label="Mean Vehicle Occupancy")
    ax.fill_between(hourly_df["Hour"], hourly_df["MinOccupancy"], hourly_df["MaxOccupancy"],
                    color=COLOR_PRIMARY_BLUE, alpha=0.12, label="Observed Min-Max Range")
    
    # Highlight core peak window: 11:00 to 14:00
    ax.axvspan(11, 14, color=COLOR_AMBER, alpha=0.15, label="Core Peak Window (11:00 – 14:00)")
    
    # Annotate phases
    ax.annotate("Morning Surge\n(Commuter Inflow)", xy=(8.5, 360), xytext=(7.5, 550),
                arrowprops=dict(facecolor=COLOR_PRIMARY_BLUE, arrowstyle="->", lw=1.2),
                fontsize=8.5, fontweight="bold", color=COLOR_PRIMARY_BLUE)
    ax.annotate("System Peak\n(~800 veh/carpark)", xy=(13.5, 800), xytext=(12.0, 950),
                arrowprops=dict(facecolor=COLOR_CRIMSON, arrowstyle="->", lw=1.2),
                fontsize=8.5, fontweight="bold", color=COLOR_CRIMSON)
    ax.annotate("Afternoon Clearance\n(Departure Outflow)", xy=(15.5, 700), xytext=(14.8, 450),
                arrowprops=dict(facecolor=COLOR_SLATE, arrowstyle="->", lw=1.2),
                fontsize=8.5, fontweight="bold", color=COLOR_SLATE)

    ax.set_xticks(hourly_df["Hour"])
    ax.set_xticklabels([f"{h:02d}:00" for h in hourly_df["Hour"]], fontsize=9)
    ax.set_xlabel("Hour of the Day", fontsize=10, fontweight="bold")
    ax.set_ylabel("Average Vehicle Occupancy", fontsize=10, fontweight="bold")
    ax.set_title("Figure 4A: Diurnal Parking Demand Profile & Operating Day Phases", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="upper left", frameon=True, facecolor="white")
    ax.grid(True, linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive Plot ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Scatter(
        x=[f"{h:02d}:00" for h in hourly_df["Hour"]],
        y=hourly_df["AvgOccupancy"],
        mode="lines+markers",
        name="Mean Occupancy",
        line=dict(color=COLOR_PRIMARY_BLUE, width=3),
        marker=dict(size=8, color=COLOR_PRIMARY_BLUE),
        hovertemplate="Hour: %{x}<br>Mean Occupancy: %{y:.1f} vehicles<extra></extra>"
    ))
    fig_plotly.add_vrect(
        x0="11:00", x1="14:00",
        fillcolor="rgba(245, 158, 11, 0.15)",
        layer="below", line_width=0,
        annotation_text="Core Peak Window (11:00 - 14:00)",
        annotation_position="top left"
    )
    fig_plotly.update_layout(
        title="<b>Diurnal Hourly Occupancy Curve (Birmingham Parking Network)</b>",
        xaxis_title="Time of Day",
        yaxis_title="Vehicles Parked",
        height=450
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "hourly_occupancy_trend", output_dir)


def plot_day_of_week_analysis(
    dow_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/temporal"
) -> Dict[str, str]:
    """
    Visualization 4B: Day of Week Occupancy and Utilization Comparison (Monday to Sunday).
    Generates both PNG and HTML.
    """
    validate_required_columns(
        dow_df,
        ["DayOfWeek", "AvgOccupancy", "AvgUtilizationPct"],
        "Day-of-Week Analysis"
    )

    # --- 1. Matplotlib Static Plot ---
    fig_mpl, ax1 = plt.subplots(figsize=(9, 4.8))
    ax2 = ax1.twinx()

    x_pos = np.arange(len(dow_df))
    bars = ax1.bar(x_pos, dow_df["AvgOccupancy"], color=COLOR_TEAL, width=0.5, label="Average Occupancy")
    line = ax2.plot(x_pos, dow_df["AvgUtilizationPct"], color=COLOR_CRIMSON, marker="s",
                    linewidth=2.2, label="Average Utilization (%)")

    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(dow_df["DayOfWeek"], fontsize=9)
    ax1.set_xlabel("Day of the Week", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Average Vehicle Occupancy", color=COLOR_TEAL, fontsize=10, fontweight="bold")
    ax2.set_ylabel("Average Utilization Rate (%)", color=COLOR_CRIMSON, fontsize=10, fontweight="bold")
    ax1.set_title("Figure 4B: Weekly Parking Demand Pattern (Monday – Sunday)", fontsize=11, fontweight="bold", pad=12)
    ax1.grid(True, axis="y", linestyle="--", alpha=0.5)

    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper right", frameon=True, facecolor="white")

    # --- 2. Plotly Interactive Plot ---
    fig_plotly = make_subplots(specs=[[{"secondary_y": True}]])
    fig_plotly.add_trace(
        go.Bar(
            x=dow_df["DayOfWeek"],
            y=dow_df["AvgOccupancy"],
            name="Mean Occupancy",
            marker_color=COLOR_TEAL,
            hovertemplate="Day: %{x}<br>Occupancy: %{y:,.1f}<extra></extra>"
        ),
        secondary_y=False
    )
    fig_plotly.add_trace(
        go.Scatter(
            x=dow_df["DayOfWeek"],
            y=dow_df["AvgUtilizationPct"],
            name="Mean Utilization (%)",
            mode="lines+markers",
            line=dict(color=COLOR_CRIMSON, width=2.5),
            marker=dict(size=8),
            hovertemplate="Day: %{x}<br>Utilization: %{y:.2f}%<extra></extra>"
        ),
        secondary_y=True
    )
    fig_plotly.update_layout(
        title="<b>Day-of-Week Occupancy & Capacity Utilization Profile</b>",
        xaxis_title="Day of Week",
        height=450,
        **PLOTLY_TEMPLATE["layout"]
    )
    fig_plotly.update_yaxes(title_text="Average Vehicles Parked", secondary_y=False)
    fig_plotly.update_yaxes(title_text="Average Utilization Rate (%)", secondary_y=True)

    return save_static_and_interactive(fig_mpl, fig_plotly, "day_of_week_analysis", output_dir)


def plot_hourly_utilization_heatmap(
    df_clean: pd.DataFrame,
    output_dir: str = "outputs/visualizations/temporal"
) -> Dict[str, str]:
    """
    Visualization 4C: Spatiotemporal 2D Heatmap (30 Facilities vs. 10 Operating Hours).
    Cell color reflects average hourly capacity utilization percentage (U_i,h).
    Generates both PNG and HTML.
    """
    # Create pivot table: rows = facilities, cols = hours, values = mean OccupancyRate
    pivot = df_clean.groupby(["SystemCodeNumber", "Hour"])["OccupancyRate"].mean().unstack().round(1)
    
    # Sort facilities by descending peak hourly utilization to bring bottlenecks to top
    sorted_facilities = pivot.max(axis=1).sort_values(ascending=False).index
    pivot = pivot.loc[sorted_facilities]

    # --- 1. Matplotlib / Seaborn Static Heatmap ---
    fig_mpl, ax = plt.subplots(figsize=(11, 10))
    sns.heatmap(
        pivot,
        cmap="YlOrRd",
        annot=True,
        fmt=".0f",
        cbar_kws={"label": "Capacity Utilization (%)"},
        linewidths=0.5,
        linecolor="#E2E8F0",
        ax=ax
    )
    ax.set_title("Figure 4C: Hourly Parking Facility Utilization Heatmap (07:00 – 16:00)\n(Sorted by Peak Demand Pressure)", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel("Hour of the Day", fontsize=10, fontweight="bold")
    ax.set_ylabel("Parking Facility", fontsize=10, fontweight="bold")
    ax.set_xticklabels([f"{h:02d}:00" for h in pivot.columns], fontsize=9)
    plt.yticks(rotation=0, fontsize=8)

    # --- 2. Plotly Interactive Heatmap ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in pivot.columns],
        y=pivot.index.tolist(),
        colorscale="YlOrRd",
        colorbar=dict(title="Utilization (%)"),
        hovertemplate="Facility: <b>%{y}</b><br>Time: <b>%{x}</b><br>Utilization: <b>%{z:.1f}%</b><extra></extra>"
    ))
    fig_plotly.update_layout(
        title="<b>Spatiotemporal Facility Utilization Heatmap (Facility vs. Hour)</b>",
        xaxis_title="Time of Day",
        yaxis_title="Parking Facility",
        height=850
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "hourly_utilization_heatmap", output_dir)


def plot_facility_demand_by_period_heatmap(
    df_clean: pd.DataFrame,
    output_dir: str = "outputs/visualizations/temporal"
) -> Dict[str, str]:
    """
    Visualization 4D: Facility Demand across Operational Day Periods:
    1. Morning Surge (07:00 - 10:00)
    2. Midday Peak (11:00 - 14:00)
    3. Afternoon Departure (15:00 - 16:30)
    Generates both PNG and HTML.
    """
    df = df_clean.copy()
    
    def assign_period(hour: int) -> str:
        if hour <= 10:
            return "1. Morning Surge (07-10)"
        elif hour <= 14:
            return "2. Midday Peak (11-14)"
        else:
            return "3. Late Afternoon (15-16)"

    df["DayPeriod"] = df["Hour"].apply(assign_period)
    period_pivot = df.groupby(["SystemCodeNumber", "DayPeriod"])["OccupancyRate"].mean().unstack().round(1)
    
    # Sort by Midday Peak utilization
    period_pivot = period_pivot.sort_values(by="2. Midday Peak (11-14)", ascending=False)

    # --- 1. Matplotlib Static ---
    fig_mpl, ax = plt.subplots(figsize=(8.5, 9.5))
    sns.heatmap(
        period_pivot,
        cmap="mako_r",
        annot=True,
        fmt=".1f",
        cbar_kws={"label": "Period Utilization (%)"},
        linewidths=0.6,
        linecolor="#CBD5E1",
        ax=ax
    )
    ax.set_title("Figure 4D: Facility Utilization Across Daily Operational Periods", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel("Operational Period", fontsize=10, fontweight="bold")
    ax.set_ylabel("Parking Facility", fontsize=10, fontweight="bold")
    plt.yticks(rotation=0, fontsize=8)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Heatmap(
        z=period_pivot.values,
        x=period_pivot.columns.tolist(),
        y=period_pivot.index.tolist(),
        colorscale="Viridis_r",
        colorbar=dict(title="Utilization (%)"),
        hovertemplate="Facility: <b>%{y}</b><br>Period: <b>%{x}</b><br>Utilization: <b>%{z:.1f}%</b><extra></extra>"
    ))
    fig_plotly.update_layout(
        title="<b>Facility Demand Heatmap by Operational Daily Period</b>",
        xaxis_title="Operational Period",
        yaxis_title="Parking Facility",
        height=800
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "facility_period_demand_heatmap", output_dir)


def generate_all_temporal_charts(
    df_clean: pd.DataFrame,
    output_dir: str = "outputs/visualizations/temporal"
) -> Dict[str, Dict[str, str]]:
    """
    Executes the complete Temporal Demand Analysis visualization suite (4A, 4B, 4C, 4D).
    """
    from exploratory_analysis import get_hourly_occupancy_trends, get_day_of_week_trends
    hourly_df = get_hourly_occupancy_trends(df_clean)
    dow_df = get_day_of_week_trends(df_clean)

    results = {
        "hourly_trend": plot_hourly_occupancy_trend(hourly_df, output_dir),
        "day_of_week": plot_day_of_week_analysis(dow_df, output_dir),
        "hourly_heatmap": plot_hourly_utilization_heatmap(df_clean, output_dir),
        "period_heatmap": plot_facility_demand_by_period_heatmap(df_clean, output_dir)
    }
    return results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data

    raw = load_raw_data()
    clean, _ = clean_parking_data(raw)
    res = generate_all_temporal_charts(clean)
    print("Temporal Charts Generated:")
    for k, v in res.items():
        print(f"  {k}: PNG -> {v['png']}, HTML -> {v['html']}")
