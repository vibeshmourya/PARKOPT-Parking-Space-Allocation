"""
optimization_charts.py
Visualizations for Optimization Results, Baseline Comparison, Allocation Shifts, and Strategies.
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
    COLOR_PURPLE, COLOR_DARK_SLATE, PLOTLY_TEMPLATE, validate_required_columns, save_static_and_interactive
)


def plot_baseline_vs_optimized_allocation(
    comp_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/optimization"
) -> Dict[str, str]:
    """
    Visualization 5A: Facility-Wise Allocation Comparison:
    Proportional Demand Baseline vs. PuLP Integer LP Optimized Allocation.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        comp_df,
        ["Facility", "PhysicalCapacity", "BaselineAllocation", "OptimizedAllocation"],
        "Baseline vs. Optimized Allocation"
    )
    df = comp_df.sort_values(by="PhysicalCapacity", ascending=False).copy()

    # --- 1. Matplotlib Static ---
    fig_mpl, ax = plt.subplots(figsize=(12, 5.5))
    x_pos = np.arange(len(df))
    width = 0.38

    ax.bar(x_pos - width / 2, df["BaselineAllocation"], width=width,
           label="Proportional Baseline", color=COLOR_SLATE)
    ax.bar(x_pos + width / 2, df["OptimizedAllocation"], width=width,
           label="PuLP Optimized Allocation", color=COLOR_PRIMARY_BLUE)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(df["Facility"], rotation=90, fontsize=8)
    ax.set_xlabel("Parking Facility", fontsize=10, fontweight="bold")
    ax.set_ylabel("Managed Permit Allocation (Bays)", fontsize=10, fontweight="bold")
    ax.set_title("Figure 5A: Managed Permit Allocation Comparison (Baseline vs. PuLP Optimized)\n(Sorted by Descending Physical Capacity)", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="upper right", frameon=True, facecolor="white")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(
        x=df["Facility"],
        y=df["PhysicalCapacity"],
        name="Physical Capacity",
        marker_color="#E2E8F0"
    ))
    fig_plotly.add_trace(go.Bar(
        x=df["Facility"],
        y=df["BaselineAllocation"],
        name="Proportional Baseline",
        marker_color=COLOR_SLATE
    ))
    fig_plotly.add_trace(go.Bar(
        x=df["Facility"],
        y=df["OptimizedAllocation"],
        name="PuLP Optimized",
        marker_color=COLOR_PRIMARY_BLUE
    ))
    fig_plotly.update_layout(
        title="<b>Managed Permit Allocation Comparison (Baseline vs. PuLP Optimized)</b>",
        barmode="group",
        xaxis_title="Facility",
        yaxis_title="Permits Allocated",
        height=520
    )
    fig_plotly.update_xaxes(tickangle=-45)

    return save_static_and_interactive(fig_mpl, fig_plotly, "baseline_vs_optimized_allocation", output_dir)


def plot_demand_vs_optimized_allocation(
    comp_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/optimization"
) -> Dict[str, str]:
    """
    Visualization 5B: Demand vs. Optimized Allocation.
    Displays Satisfied Demand vs. Unmet Demand (Deficit) under optimization.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        comp_df,
        ["Facility", "EstimatedDemand", "OptimizedAllocation", "OptimizedUnmetDemand"],
        "Demand vs. Optimized Allocation"
    )
    df = comp_df.sort_values(by="EstimatedDemand", ascending=False).copy()

    # --- 1. Matplotlib Static Stacked Bar ---
    fig_mpl, ax = plt.subplots(figsize=(12, 5.5))
    x_pos = np.arange(len(df))
    width = 0.65

    ax.bar(x_pos, df["OptimizedAllocation"], width=width,
           label="Satisfied Demand (Allocated Permits)", color=COLOR_EMERALD)
    ax.bar(x_pos, df["OptimizedUnmetDemand"], bottom=df["OptimizedAllocation"], width=width,
           label="Unmet Demand (Deficit)", color=COLOR_SALMON)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(df["Facility"], rotation=90, fontsize=8)
    ax.set_xlabel("Parking Facility", fontsize=10, fontweight="bold")
    ax.set_ylabel("Demand Units / Vehicles", fontsize=10, fontweight="bold")
    ax.set_title("Figure 5B: Estimated Peak Demand Fulfillment (Satisfied vs. Unmet Demand)", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="upper right", frameon=True, facecolor="white")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive Stacked Bar ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(
        x=df["Facility"],
        y=df["OptimizedAllocation"],
        name="Satisfied Demand",
        marker_color=COLOR_EMERALD,
        hovertemplate="<b>%{x}</b><br>Allocated: %{y:,} permits<extra></extra>"
    ))
    fig_plotly.add_trace(go.Bar(
        x=df["Facility"],
        y=df["OptimizedUnmetDemand"],
        name="Unmet Demand",
        marker_color=COLOR_SALMON,
        hovertemplate="<b>%{x}</b><br>Unmet Demand: %{y:,} vehicles<extra></extra>"
    ))
    fig_plotly.update_layout(
        title="<b>Demand Fulfillment Breakdown: Satisfied vs. Unmet Demand</b>",
        barmode="stack",
        xaxis_title="Facility",
        yaxis_title="Vehicles / Units",
        height=520
    )
    fig_plotly.update_xaxes(tickangle=-45)

    return save_static_and_interactive(fig_mpl, fig_plotly, "demand_vs_optimized_allocation", output_dir)


def plot_allocation_distribution(
    comp_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/optimization"
) -> Dict[str, str]:
    """
    Visualization 5C: Distribution of Total Permit Allocation across Birmingham Facilities.
    Displays proportional share of municipal budget received by each car park.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        comp_df,
        ["Facility", "OptimizedAllocation"],
        "Allocation Distribution"
    )
    df = comp_df[comp_df["OptimizedAllocation"] > 0].sort_values(by="OptimizedAllocation", ascending=False).copy()
    total_permits = df["OptimizedAllocation"].sum()
    df["SharePct"] = (df["OptimizedAllocation"] / total_permits) * 100.0

    # Top 8 facilities + Others aggregate for clean visual presentation
    top_n = 8
    top_df = df.head(top_n).copy()
    others_alloc = df.iloc[top_n:]["OptimizedAllocation"].sum()
    others_pct = df.iloc[top_n:]["SharePct"].sum()

    labels = top_df["Facility"].tolist() + [f"Remaining ({len(df) - top_n} Lots)"]
    values = top_df["OptimizedAllocation"].tolist() + [others_alloc]
    
    palette = [
        COLOR_PRIMARY_BLUE, COLOR_SECONDARY_BLUE, COLOR_TEAL, COLOR_EMERALD,
        COLOR_AMBER, COLOR_PURPLE, "#0284C7", "#6366F1", COLOR_SLATE
    ]

    # --- 1. Matplotlib Static Donut Chart ---
    fig_mpl, ax = plt.subplots(figsize=(8, 7))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        pctdistance=0.78,
        colors=palette[:len(labels)],
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=1.5),
        textprops=dict(fontsize=8)
    )
    for at in autotexts:
        at.set_fontsize(7.5)
        at.set_weight("bold")
    ax.set_title("Figure 5C: Municipal Managed Permit Budget Allocation Shares", fontsize=11, fontweight="bold", pad=12)

    # --- 2. Plotly Interactive Donut Chart ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        marker=dict(colors=palette[:len(labels)]),
        textinfo="label+percent",
        hovertemplate="Facility: <b>%{label}</b><br>Allocated: %{value:,} permits (%{percent})<extra></extra>"
    ))
    fig_plotly.update_layout(
        title="<b>Total Managed Permit Budget Allocation Distribution (%)</b>",
        height=550
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "allocation_distribution", output_dir)


def plot_facility_allocation_changes(
    comp_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/optimization"
) -> Dict[str, str]:
    """
    Visualization 5D: Facility-Wise Allocation Changes (Delta x_i = x_opt - x_base).
    Diverging horizontal bar chart displaying quota inflows (gains) and outflows (donations).
    Generates both PNG and HTML.
    """
    validate_required_columns(
        comp_df,
        ["Facility", "AllocationDifference"],
        "Facility Allocation Changes"
    )
    df = comp_df.sort_values(by="AllocationDifference", ascending=True).copy()
    colors = [COLOR_EMERALD if d >= 0 else COLOR_CRIMSON for d in df["AllocationDifference"]]

    # --- 1. Matplotlib Static Diverging Bar Chart ---
    fig_mpl, ax = plt.subplots(figsize=(11, 8.5))
    y_pos = np.arange(len(df))
    bars = ax.barh(y_pos, df["AllocationDifference"], color=colors, height=0.65)

    for bar in bars:
        w = bar.get_width()
        x_text = w + (18 if w >= 0 else -18)
        align = "left" if w >= 0 else "right"
        ax.annotate(f"{w:+d}", xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(4 if w >= 0 else -4, 0), textcoords="offset points",
                    ha=align, va="center", fontsize=7.5, color="#1E293B", fontweight="bold")

    ax.axvline(0, color=COLOR_DARK_SLATE, linewidth=1.2)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["Facility"], fontsize=8)
    ax.set_xlabel("Allocation Change vs. Baseline (Permits Added or Donated)", fontsize=10, fontweight="bold")
    ax.set_title("Figure 5D: Optimization Impact: Managed Permit Reallocations vs. Baseline\n(Emerald = Quota Inflow to Congested Hubs; Crimson = Donated Underutilized Quota)", fontsize=11, fontweight="bold", pad=12)
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive Diverging Bar Chart ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(
        y=df["Facility"],
        x=df["AllocationDifference"],
        orientation="h",
        marker_color=colors,
        text=df["AllocationDifference"].apply(lambda v: f"{v:+d}"),
        textposition="outside",
        hovertemplate="Facility: <b>%{y}</b><br>Delta: %{x:+d} permits<extra></extra>"
    ))
    fig_plotly.update_layout(
        title="<b>Facility Allocation Shift (PuLP Optimized vs. Baseline)</b>",
        xaxis_title="Net Permit Quota Shift (+ / -)",
        yaxis_title="Facility Identifier",
        height=750
    )
    fig_plotly.add_vline(x=0, line_color="#0F172A", line_width=1.5)

    return save_static_and_interactive(fig_mpl, fig_plotly, "facility_allocation_changes", output_dir)


def plot_priority_strategy_comparison(
    prio_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/optimization"
) -> Dict[str, str]:
    """
    Visualization 5E: Priority Strategy Comparison: Equal vs. Congestion vs. Custom Strategy.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        prio_df,
        ["Facility", "Alloc_Equal", "Alloc_Congestion", "Alloc_Custom", "Weight_Congestion", "Weight_Custom"],
        "Priority Strategy Comparison"
    )
    df = prio_df.sort_values(by="Weight_Congestion", ascending=False).head(15).copy()

    # --- 1. Matplotlib Static ---
    fig_mpl, ax = plt.subplots(figsize=(12, 5.5))
    x_pos = np.arange(len(df))
    width = 0.28

    ax.bar(x_pos - width, df["Alloc_Equal"], width=width, label="Equal Priority (w=1.0)", color=COLOR_SLATE)
    ax.bar(x_pos, df["Alloc_Congestion"], width=width, label="Congestion Priority", color=COLOR_PRIMARY_BLUE)
    ax.bar(x_pos + width, df["Alloc_Custom"], width=width, label="Custom Policy Priority", color=COLOR_TEAL)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(df["Facility"], rotation=90, fontsize=8)
    ax.set_xlabel("Top 15 Congested Parking Facilities", fontsize=10, fontweight="bold")
    ax.set_ylabel("Allocated Permits", fontsize=10, fontweight="bold")
    ax.set_title("Figure 5E: Policy Sensitivity: Quota Allocations Across Priority Strategies", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="upper right", frameon=True, facecolor="white")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(x=df["Facility"], y=df["Alloc_Equal"], name="Equal Priority", marker_color=COLOR_SLATE))
    fig_plotly.add_trace(go.Bar(x=df["Facility"], y=df["Alloc_Congestion"], name="Congestion Priority", marker_color=COLOR_PRIMARY_BLUE))
    fig_plotly.add_trace(go.Bar(x=df["Facility"], y=df["Alloc_Custom"], name="Custom Policy", marker_color=COLOR_TEAL))
    fig_plotly.update_layout(
        title="<b>Priority Strategy Comparison (Equal vs. Congestion vs. Custom)</b>",
        barmode="group",
        xaxis_title="Facility",
        yaxis_title="Allocated Permits",
        height=520
    )
    fig_plotly.update_xaxes(tickangle=-45)

    return save_static_and_interactive(fig_mpl, fig_plotly, "priority_strategy_comparison", output_dir)


def plot_demand_estimator_comparison(
    est_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/optimization"
) -> Dict[str, str]:
    """
    Visualization 5F: Demand Estimator Comparison:
    Mean vs. 85th Percentile vs. 95th Percentile vs. Maximum Observed Occupancy.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        est_df,
        ["SystemCodeNumber", "Capacity", "MeanDemand", "P85Demand", "P95Demand", "MaxDemand"],
        "Demand Estimator Comparison"
    )
    df = est_df.sort_values(by="Capacity", ascending=False).head(15).copy()

    # --- 1. Matplotlib Static ---
    fig_mpl, ax = plt.subplots(figsize=(12, 5.5))
    x_pos = np.arange(len(df))
    width = 0.20

    ax.bar(x_pos - 1.5 * width, df["MeanDemand"], width=width, label="1. Mean Occupancy", color="#93C5FD")
    ax.bar(x_pos - 0.5 * width, df["P85Demand"], width=width, label="2. 85th Percentile", color=COLOR_SECONDARY_BLUE)
    ax.bar(x_pos + 0.5 * width, df["P95Demand"], width=width, label="3. 95th Percentile (Default)", color=COLOR_PRIMARY_BLUE)
    ax.bar(x_pos + 1.5 * width, df["MaxDemand"], width=width, label="4. Maximum Observed", color=COLOR_CRIMSON)

    # Plot capacity markers as step line / points
    ax.plot(x_pos, df["Capacity"], color="#0F172A", marker="_", markersize=14, markeredgewidth=2.5, linestyle="None", label="Physical Capacity")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(df["SystemCodeNumber"], rotation=90, fontsize=8)
    ax.set_xlabel("Parking Facilities (Top 15 by Capacity)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Demand Units / Vehicles", fontsize=10, fontweight="bold")
    ax.set_title("Figure 5F: Demand Estimation Comparison across Four Methodologies", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="upper right", frameon=True, facecolor="white")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(x=df["SystemCodeNumber"], y=df["MeanDemand"], name="Mean Demand", marker_color="#93C5FD"))
    fig_plotly.add_trace(go.Bar(x=df["SystemCodeNumber"], y=df["P85Demand"], name="85th Percentile", marker_color=COLOR_SECONDARY_BLUE))
    fig_plotly.add_trace(go.Bar(x=df["SystemCodeNumber"], y=df["P95Demand"], name="95th Percentile", marker_color=COLOR_PRIMARY_BLUE))
    fig_plotly.add_trace(go.Bar(x=df["SystemCodeNumber"], y=df["MaxDemand"], name="Max Demand", marker_color=COLOR_CRIMSON))
    fig_plotly.add_trace(go.Scatter(x=df["SystemCodeNumber"], y=df["Capacity"], name="Capacity", mode="markers", marker=dict(symbol="line-ew", size=18, line=dict(width=3, color="#0F172A"))))

    fig_plotly.update_layout(
        title="<b>Demand Estimator Hierarchy (Mean vs. P85 vs. P95 vs. Max)</b>",
        barmode="group",
        xaxis_title="Facility",
        yaxis_title="Vehicles Parked",
        height=520
    )
    fig_plotly.update_xaxes(tickangle=-45)

    return save_static_and_interactive(fig_mpl, fig_plotly, "demand_estimator_comparison", output_dir)


def generate_all_optimization_charts(
    output_dir: str = "outputs/visualizations/optimization"
) -> Dict[str, Dict[str, str]]:
    """
    Executes the complete Optimization Result Visualization suite (5A through 5F).
    """
    comp_path = "outputs/baseline_comparison.csv"
    prio_path = "outputs/priority_comparison.csv"
    est_path = "outputs/estimator_comparison.csv"

    if not os.path.exists(comp_path):
        raise FileNotFoundError(f"Missing required comparison file: {comp_path}")
    if not os.path.exists(prio_path):
        raise FileNotFoundError(f"Missing required priority comparison file: {prio_path}")
    if not os.path.exists(est_path):
        raise FileNotFoundError(f"Missing required estimator comparison file: {est_path}")

    comp_df = pd.read_csv(comp_path)
    prio_df = pd.read_csv(prio_path)
    est_df = pd.read_csv(est_path)

    results = {
        "baseline_vs_optimized": plot_baseline_vs_optimized_allocation(comp_df, output_dir),
        "demand_vs_allocation": plot_demand_vs_optimized_allocation(comp_df, output_dir),
        "allocation_distribution": plot_allocation_distribution(comp_df, output_dir),
        "allocation_changes": plot_facility_allocation_changes(comp_df, output_dir),
        "priority_comparison": plot_priority_strategy_comparison(prio_df, output_dir),
        "estimator_comparison": plot_demand_estimator_comparison(est_df, output_dir)
    }
    return results


if __name__ == "__main__":
    res = generate_all_optimization_charts()
    print("Optimization Charts Generated:")
    for k, v in res.items():
        print(f"  {k}: PNG -> {v['png']}, HTML -> {v['html']}")
