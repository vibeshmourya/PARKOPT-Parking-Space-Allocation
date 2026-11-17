"""
occupancy_charts.py
Visualizations for Parking Occupancy, Capacity, Utilization, and Availability Analysis.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go

from .visualization_utils import (
    COLOR_PRIMARY_BLUE, COLOR_SECONDARY_BLUE, COLOR_EMERALD, COLOR_CRIMSON,
    COLOR_AMBER, COLOR_SLATE, COLOR_LIGHT_GRAY, COLOR_SALMON, COLOR_TEAL,
    PLOTLY_TEMPLATE, validate_required_columns, save_static_and_interactive
)


def plot_capacity_vs_average_occupancy(
    area_stats_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/occupancy"
) -> Dict[str, str]:
    """
    Visualization 3A: Capacity vs. Average Occupancy across all 30 facilities.
    Highlights high-demand facilities (Utilization >= 65%).
    Generates both PNG and HTML.
    """
    validate_required_columns(
        area_stats_df,
        ["SystemCodeNumber", "Capacity", "AvgOccupancy", "AvgUtilizationPct"],
        "Capacity vs. Average Occupancy"
    )
    df = area_stats_df.sort_values(by="Capacity", ascending=True).copy()

    # --- 1. Matplotlib / Seaborn Static Plot ---
    fig_mpl, ax = plt.subplots(figsize=(11, 8.5))
    y_pos = np.arange(len(df))
    bar_height = 0.38

    ax.barh(y_pos - bar_height / 2, df["Capacity"], height=bar_height, label="Physical Capacity", color="#CBD5E1")
    
    # Highlight high-demand facilities with deep red/navy
    colors = [COLOR_CRIMSON if u >= 65.0 else COLOR_PRIMARY_BLUE for u in df["AvgUtilizationPct"]]
    ax.barh(y_pos + bar_height / 2, df["AvgOccupancy"], height=bar_height, label="Average Occupancy", color=colors)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["SystemCodeNumber"], fontsize=8)
    ax.set_xlabel("Number of Parking Spaces / Bays", fontsize=10, fontweight="bold")
    ax.set_title("Parking Facility Capacity vs. Historical Average Occupancy\n(Red = High Demand >= 65% Utilization)", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="lower right", frameon=True, facecolor="white")
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive Plot ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["Capacity"],
        name="Physical Capacity",
        orientation="h",
        marker_color="#CBD5E1",
        hovertemplate="<b>%{y}</b><br>Capacity: %{x:,} bays<extra></extra>"
    ))
    fig_plotly.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgOccupancy"],
        name="Average Occupancy",
        orientation="h",
        marker_color=colors,
        hovertemplate="<b>%{y}</b><br>Avg Occupancy: %{x:,.1f}<br>Utilization: %{customdata:.1f}%<extra></extra>",
        customdata=df["AvgUtilizationPct"]
    ))
    fig_plotly.update_layout(
        title="<b>Parking Facility Capacity vs. Average Observed Occupancy</b><br><sup>Red bars indicate high-demand facilities operating above 65% average utilization</sup>",
        barmode="group",
        xaxis_title="Number of Parking Bays",
        yaxis_title="Parking Facility Identifier",
        height=750
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "capacity_vs_avg_occupancy", output_dir)


def plot_parking_utilization_ranking(
    area_stats_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/occupancy"
) -> Dict[str, str]:
    """
    Visualization 3B: Parking Utilization percentage ranked hierarchy.
    Categorizes facilities into High (>=65%), Moderate (40-65%), and Low (<40%) demand tiers.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        area_stats_df,
        ["SystemCodeNumber", "AvgUtilizationPct"],
        "Parking Utilization Ranking"
    )
    df = area_stats_df.sort_values(by="AvgUtilizationPct", ascending=True).copy()

    # Demand Tier Colors
    colors = []
    for u in df["AvgUtilizationPct"]:
        if u >= 65.0:
            colors.append(COLOR_CRIMSON)   # High Demand / Pressure
        elif u >= 40.0:
            colors.append(COLOR_AMBER)     # Moderate Demand
        else:
            colors.append(COLOR_SECONDARY_BLUE) # Low Demand / Underutilized

    # --- 1. Matplotlib Static ---
    fig_mpl, ax = plt.subplots(figsize=(10.5, 8.5))
    y_pos = np.arange(len(df))
    bars = ax.barh(y_pos, df["AvgUtilizationPct"], color=colors, height=0.65)
    
    # Value annotations on bar tips
    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"{w:.1f}%", xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(3, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=7.5, color="#334155")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["SystemCodeNumber"], fontsize=8)
    ax.axvline(40.0, color=COLOR_AMBER, linestyle="--", linewidth=1.4, label="Moderate Threshold (40%)")
    ax.axvline(65.0, color=COLOR_CRIMSON, linestyle="--", linewidth=1.4, label="High Pressure Threshold (65%)")
    ax.set_xlim(0, 95)
    ax.set_xlabel("Average Utilization Percentage (%)", fontsize=10, fontweight="bold")
    ax.set_title("Figure 3B: Facility-Wise Parking Utilization Ranking & Demand Tiers", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="lower right", frameon=True, facecolor="white")
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgUtilizationPct"],
        orientation="h",
        marker_color=colors,
        text=df["AvgUtilizationPct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Average Utilization: %{x:.2f}%<extra></extra>"
    ))
    fig_plotly.add_vline(x=40.0, line_dash="dash", line_color=COLOR_AMBER, annotation_text="Moderate (40%)")
    fig_plotly.add_vline(x=65.0, line_dash="dash", line_color=COLOR_CRIMSON, annotation_text="High Pressure (65%)")
    fig_plotly.update_layout(
        title="<b>Facility Parking Utilization Ranking by Demand Tier</b>",
        xaxis_title="Average Utilization Percentage (%)",
        yaxis_title="Parking Facility Identifier",
        xaxis=dict(range=[0, 100]),
        height=750
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "parking_utilization_ranking", output_dir)


def plot_peak_occupancy_and_overflow(
    area_stats_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/occupancy"
) -> Dict[str, str]:
    """
    Visualization 3C: Maximum observed occupancy vs. physical capacity.
    Identifies and highlights facilities experiencing overflow (Max Occupancy > Capacity).
    Generates both PNG and HTML.
    """
    validate_required_columns(
        area_stats_df,
        ["SystemCodeNumber", "Capacity", "MaxOccupancy", "OverflowCount"],
        "Peak Occupancy and Overflow"
    )
    df = area_stats_df.sort_values(by="Capacity", ascending=True).copy()
    df["IsOverflow"] = df["MaxOccupancy"] > df["Capacity"]

    # --- 1. Matplotlib Static ---
    fig_mpl, ax = plt.subplots(figsize=(11, 8.5))
    y_pos = np.arange(len(df))
    bar_height = 0.38

    ax.barh(y_pos - bar_height / 2, df["Capacity"], height=bar_height, label="Physical Capacity", color="#CBD5E1")
    
    # Color peak occupancy: Crimson for overflow, deep navy for bounded
    peak_colors = [COLOR_CRIMSON if is_ov else COLOR_PRIMARY_BLUE for is_ov in df["IsOverflow"]]
    ax.barh(y_pos + bar_height / 2, df["MaxOccupancy"], height=bar_height, label="Peak Observed Occupancy", color=peak_colors)

    # Highlight overflow counts with red text on overflow facilities
    for i, (_, row) in enumerate(df.iterrows()):
        if row["IsOverflow"]:
            overflow_diff = row["MaxOccupancy"] - row["Capacity"]
            ax.annotate(f"+{overflow_diff} bay overflow ({int(row['OverflowCount'])} times)",
                        xy=(row["MaxOccupancy"], i + bar_height / 2),
                        xytext=(4, 0), textcoords="offset points",
                        ha="left", va="center", fontsize=7, color=COLOR_CRIMSON, fontweight="bold")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["SystemCodeNumber"], fontsize=8)
    ax.set_xlabel("Number of Parking Bays", fontsize=10, fontweight="bold")
    ax.set_title("Peak Observed Occupancy vs. Physical Capacity\n(Crimson = Facilities Exceeding Physical Capacity)", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="lower right", frameon=True, facecolor="white")
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["Capacity"],
        name="Physical Capacity",
        orientation="h",
        marker_color="#CBD5E1"
    ))
    fig_plotly.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["MaxOccupancy"],
        name="Peak Observed Occupancy",
        orientation="h",
        marker_color=peak_colors,
        hovertemplate="<b>%{y}</b><br>Peak Occupancy: %{x:,}<br>Overflow Events: %{customdata:,}<extra></extra>",
        customdata=df["OverflowCount"]
    ))
    fig_plotly.update_layout(
        title="<b>Peak Observed Occupancy vs. Physical Capacity (Overflow Detection)</b>",
        barmode="group",
        xaxis_title="Number of Parking Bays",
        yaxis_title="Facility Identifier",
        height=750
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "peak_occupancy_and_overflow", output_dir)


def plot_parking_availability(
    area_stats_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/occupancy"
) -> Dict[str, str]:
    """
    Visualization 3D: Average Available Parking Spaces across all 30 facilities.
    Compares facilities with severe bay exhaustion vs. massive surplus capacity.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        area_stats_df,
        ["SystemCodeNumber", "AvgAvailable", "AvgOccupancy", "Capacity"],
        "Parking Availability"
    )
    df = area_stats_df.sort_values(by="AvgAvailable", ascending=True).copy()

    # --- 1. Matplotlib Static ---
    fig_mpl, ax = plt.subplots(figsize=(10.5, 8.5))
    y_pos = np.arange(len(df))
    
    # Palette: Emerald for high availability, Crimson/Amber for low availability
    colors = [COLOR_CRIMSON if a < 150 else (COLOR_AMBER if a < 300 else COLOR_EMERALD) for a in df["AvgAvailable"]]
    bars = ax.barh(y_pos, df["AvgAvailable"], color=colors, height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"{w:,.0f} bays", xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(3, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=7.5, color="#334155")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["SystemCodeNumber"], fontsize=8)
    ax.set_xlabel("Average Available Parking Spaces (Bays)", fontsize=10, fontweight="bold")
    ax.set_title("Average Available Parking Spaces per Facility\n(Crimson = High Scarcity < 150 bays; Emerald = Large Surplus Reservoirs)", fontsize=11, fontweight="bold", pad=12)
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgAvailable"],
        orientation="h",
        marker_color=colors,
        text=df["AvgAvailable"].apply(lambda v: f"{v:,.0f} bays"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Average Available: %{x:,.1f} bays<extra></extra>"
    ))
    fig_plotly.update_layout(
        title="<b>Average Parking Availability per Facility (Surplus vs. Scarcity)</b>",
        xaxis_title="Average Available Bays",
        yaxis_title="Facility Identifier",
        height=750
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "parking_availability", output_dir)


def generate_all_occupancy_charts(
    df_clean: Optional[pd.DataFrame] = None,
    output_dir: str = "outputs/visualizations/occupancy"
) -> Dict[str, Dict[str, str]]:
    """
    Executes the complete Occupancy Analysis visualization suite (3A, 3B, 3C, 3D).
    """
    if df_clean is not None:
        from exploratory_analysis import get_parking_area_statistics
        stats_df = get_parking_area_statistics(df_clean)
    else:
        stats_path = "outputs/parking_area_statistics.csv"
        if not os.path.exists(stats_path):
            raise FileNotFoundError(f"Required statistics file not found: {stats_path}")
        stats_df = pd.read_csv(stats_path)

    results = {
        "capacity_vs_occupancy": plot_capacity_vs_average_occupancy(stats_df, output_dir),
        "utilization_ranking": plot_parking_utilization_ranking(stats_df, output_dir),
        "peak_occupancy_overflow": plot_peak_occupancy_and_overflow(stats_df, output_dir),
        "parking_availability": plot_parking_availability(stats_df, output_dir)
    }
    return results


if __name__ == "__main__":
    from exploratory_analysis import get_parking_area_statistics
    stats = pd.read_csv("outputs/parking_area_statistics.csv")
    res = generate_all_occupancy_charts()
    print("Occupancy Charts Generated:")
    for k, v in res.items():
        print(f"  {k}: PNG -> {v['png']}, HTML -> {v['html']}")

