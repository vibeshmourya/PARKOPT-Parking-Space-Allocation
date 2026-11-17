"""
visualization.py
Academic Visualization Module for Optimal Parking Space Allocation.
Provides both Plotly interactive figures (for Streamlit dashboard)
and Matplotlib publication-grade static figures (for PDF reporting and presentation).
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
import matplotlib
matplotlib.use("Agg")  # Headless rendering safe on all platforms
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# --- Professional Color Palette ---
COLOR_PRIMARY_BLUE = "#1E3A8A"     # Deep Navy
COLOR_SECONDARY_BLUE = "#3B82F6"   # Electric Blue
COLOR_TEAL = "#0D9488"             # Emerald/Teal
COLOR_EMERALD = "#10B981"          # Success / Satisfied
COLOR_CRIMSON = "#EF4444"          # Overcapacity / High Pressure
COLOR_AMBER = "#F59E0B"            # Warning / Moderate
COLOR_GRAY = "#6B7280"             # Neutral / Baseline
COLOR_LIGHT_GRAY = "#E5E7EB"       # Gridlines
COLOR_SALMON = "#F87171"           # Unmet Demand

PLOTLY_LAYOUT_DEFAULTS = dict(
    font=dict(family="Arial, sans-serif", size=12, color="#1F2937"),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=50, r=40, t=50, b=50),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(255,255,255,0.9)"
    )
)


# =====================================================================
# 1. PLOTLY INTERACTIVE FIGURE GENERATORS (For Streamlit Dashboard)
# =====================================================================

def create_capacity_occupancy_chart(area_stats_df: pd.DataFrame) -> go.Figure:
    """
    Creates an interactive grouped bar chart comparing Capacity, Average Occupancy, and Peak Occupancy.
    """
    df = area_stats_df.sort_values(by="Capacity", ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["Capacity"],
        name="Physical Capacity",
        orientation="h",
        marker_color="#94A3B8"
    ))
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgOccupancy"],
        name="Average Occupancy",
        orientation="h",
        marker_color=COLOR_SECONDARY_BLUE
    ))
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["MaxOccupancy"],
        name="Peak Occupancy",
        orientation="h",
        marker_color=COLOR_CRIMSON
    ))

    fig.update_layout(
        title="<b>Parking Facility Capacity vs. Observed Occupancy</b>",
        xaxis_title="Number of Parking Bays",
        yaxis_title="Facility Identifier",
        barmode="group",
        height=750,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    return fig


def create_utilization_ranking_chart(area_stats_df: pd.DataFrame) -> go.Figure:
    """
    Creates a ranked horizontal bar chart of facility utilization categorized by demand tiers.
    """
    df = area_stats_df.sort_values(by="AvgUtilizationPct", ascending=True)
    
    # Assign color by tier
    colors = []
    for u in df["AvgUtilizationPct"]:
        if u >= 65.0:
            colors.append(COLOR_CRIMSON)   # High Demand
        elif u >= 40.0:
            colors.append(COLOR_AMBER)     # Moderate Demand
        else:
            colors.append(COLOR_SECONDARY_BLUE) # Low Demand

    fig = go.Figure(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgUtilizationPct"],
        orientation="h",
        marker_color=colors,
        text=df["AvgUtilizationPct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside"
    ))

    # Add vertical reference lines for tier thresholds
    fig.add_vline(x=40.0, line_dash="dash", line_color=COLOR_AMBER, annotation_text="Moderate Tier (40%)")
    fig.add_vline(x=65.0, line_dash="dash", line_color=COLOR_CRIMSON, annotation_text="High Pressure Tier (65%)")

    fig.update_layout(
        title="<b>Facility Ranking by Average Utilization Percentage (%)</b>",
        xaxis_title="Average Utilization Rate (%)",
        yaxis_title="Facility Identifier",
        height=750,
        xaxis=dict(range=[0, 100]),
        **PLOTLY_LAYOUT_DEFAULTS
    )
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    return fig


def create_temporal_trends_chart(hourly_df: pd.DataFrame, dow_df: pd.DataFrame) -> go.Figure:
    """
    Creates dual-panel subplot: Diurnal Hourly Trend (left) and Day of Week Profile (right).
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("<b>Diurnal Occupancy Profile (07:00 – 16:30)</b>", "<b>Weekly Day-of-Week Occupancy</b>"),
        horizontal_spacing=0.12
    )

    # Panel 1: Hourly Line + Shaded Band
    fig.add_trace(
        go.Scatter(
            x=hourly_df["Hour"],
            y=hourly_df["AvgOccupancy"],
            mode="lines+markers",
            name="Mean Hourly Occupancy",
            line=dict(color=COLOR_PRIMARY_BLUE, width=3),
            marker=dict(size=7),
            fill="tozeroy",
            fillcolor="rgba(30, 58, 138, 0.15)"
        ),
        row=1, col=1
    )

    # Panel 2: Day of Week Bar
    fig.add_trace(
        go.Bar(
            x=dow_df["DayOfWeek"],
            y=dow_df["AvgOccupancy"],
            name="Day of Week Mean",
            marker_color=COLOR_TEAL,
            text=dow_df["AvgOccupancy"].round(1),
            textposition="auto"
        ),
        row=1, col=2
    )

    fig.update_layout(height=420, **PLOTLY_LAYOUT_DEFAULTS)
    fig.update_xaxes(title_text="Hour of Day", row=1, col=1, showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    fig.update_yaxes(title_text="Average Vehicles Parked", row=1, col=1, showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    fig.update_xaxes(title_text="Day of Week", row=1, col=2)
    fig.update_yaxes(title_text="Average Vehicles Parked", row=1, col=2, showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    return fig


def create_allocation_comparison_chart(comp_df: pd.DataFrame) -> go.Figure:
    """
    Compares Baseline Proportional Allocation vs. PuLP Optimized Allocation vs. Physical Capacity.
    """
    df = comp_df.sort_values(by="PhysicalCapacity", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Facility"],
        y=df["PhysicalCapacity"],
        name="Physical Capacity",
        marker_color="#CBD5E1"
    ))
    fig.add_trace(go.Bar(
        x=df["Facility"],
        y=df["BaselineAllocation"],
        name="Proportional Baseline",
        marker_color=COLOR_GRAY
    ))
    fig.add_trace(go.Bar(
        x=df["Facility"],
        y=df["OptimizedAllocation"],
        name="PuLP Optimized Allocation",
        marker_color=COLOR_PRIMARY_BLUE
    ))

    fig.update_layout(
        title="<b>Permit Allocation Comparison: Proportional Baseline vs. PuLP Optimized</b>",
        xaxis_title="Parking Facility",
        yaxis_title="Allocated Permits",
        barmode="group",
        height=520,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    fig.update_xaxes(tickangle=-45, showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    return fig


def create_demand_vs_allocation_chart(comp_df: pd.DataFrame) -> go.Figure:
    """
    Creates a stacked bar chart displaying Satisfied Demand vs. Unmet Demand under Optimization.
    """
    df = comp_df.sort_values(by="EstimatedDemand", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Facility"],
        y=df["OptimizedAllocation"],
        name="Satisfied Demand (Allocated Permits)",
        marker_color=COLOR_EMERALD
    ))
    fig.add_trace(go.Bar(
        x=df["Facility"],
        y=df["OptimizedUnmetDemand"],
        name="Unmet Demand (Deficit)",
        marker_color=COLOR_SALMON
    ))

    fig.update_layout(
        title="<b>Estimated Peak Demand Fulfillment (Satisfied vs. Unmet Demand)</b>",
        xaxis_title="Parking Facility",
        yaxis_title="Vehicle Demand Units",
        barmode="stack",
        height=520,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    fig.update_xaxes(tickangle=-45, showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    return fig


def create_budget_sensitivity_chart(sensitivity_df: pd.DataFrame) -> go.Figure:
    """
    Dual-axis chart of Budget vs. Objective Value (left) and Budget vs. Unmet Demand (right).
    Highlights the Saturation Threshold.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Left Axis: Objective Value (LP and Baseline)
    fig.add_trace(
        go.Scatter(
            x=sensitivity_df["BudgetPermits"],
            y=sensitivity_df["OptimizedObjective"],
            mode="lines+markers",
            name="Optimized Objective (Z*)",
            line=dict(color=COLOR_PRIMARY_BLUE, width=3),
            marker=dict(size=6)
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=sensitivity_df["BudgetPermits"],
            y=sensitivity_df["BaselineObjective"],
            mode="lines",
            name="Baseline Objective (Z_base)",
            line=dict(color=COLOR_GRAY, dash="dash", width=2)
        ),
        secondary_y=False
    )

    # Right Axis: Unmet Demand
    fig.add_trace(
        go.Scatter(
            x=sensitivity_df["BudgetPermits"],
            y=sensitivity_df["OptimizedUnmetDemand"],
            mode="lines+markers",
            name="Total Unmet Demand",
            line=dict(color=COLOR_CRIMSON, width=2),
            marker=dict(symbol="triangle-down", size=6)
        ),
        secondary_y=True
    )

    # Saturation threshold line (where budget = 28823)
    sat_row = sensitivity_df[sensitivity_df["BudgetFraction"] >= 1.0].iloc[0]
    sat_b = sat_row["BudgetPermits"]

    fig.add_vline(
        x=sat_b,
        line_dash="dot",
        line_color=COLOR_TEAL,
        annotation_text=f"Saturation Point (B={sat_b:,})",
        annotation_position="top left"
    )

    fig.update_layout(
        title="<b>Budget Sensitivity Analysis: Objective Value & Unmet Demand vs. Permit Budget</b>",
        xaxis_title="Managed Permit Allocation Budget (B)",
        height=500,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    fig.update_yaxes(title_text="Weighted Objective Value (Z)", secondary_y=False, showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    fig.update_yaxes(title_text="Total Unmet Demand (Vehicles)", secondary_y=True, showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    return fig


def create_marginal_value_chart(sensitivity_df: pd.DataFrame) -> go.Figure:
    """
    Step chart showing the decay of Marginal Value per Permit (dZ/dB) illustrating diminishing returns.
    """
    df = sensitivity_df[sensitivity_df["BudgetPermits"] > 0]

    fig = go.Figure(go.Scatter(
        x=df["BudgetFraction"] * 100.0,
        y=df["MarginalValuePerPermit"],
        mode="lines+markers",
        line=dict(color=COLOR_AMBER, width=3, shape="hv"),
        marker=dict(size=8, color=COLOR_AMBER),
        fill="tozeroy",
        fillcolor="rgba(245, 158, 11, 0.15)",
        name="Marginal Objective (dZ/dB)"
    ))

    fig.update_layout(
        title="<b>Law of Diminishing Marginal Returns: Marginal Value per Permit (dZ/dB)</b>",
        xaxis_title="Budget Level (% of Allocatable Demand)",
        yaxis_title="Marginal Objective Return (dZ/dB)",
        height=420,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    fig.update_yaxes(showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    return fig


def create_scenarios_comparison_chart(scenario_summary_df: pd.DataFrame) -> go.Figure:
    """
    Multi-metric bar chart comparing the 5 canonical optimization scenarios.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("<b>Weighted Objective Value Across Scenarios</b>", "<b>Total Unmet Demand Across Scenarios</b>"),
        horizontal_spacing=0.14
    )

    # Panel 1: Objective Values
    fig.add_trace(
        go.Bar(
            x=scenario_summary_df["ScenarioID"],
            y=scenario_summary_df["WeightedObjective"],
            name="Weighted Objective",
            marker_color=COLOR_PRIMARY_BLUE,
            text=scenario_summary_df["WeightedObjective"].apply(lambda v: f"{v:,.0f}"),
            textposition="auto"
        ),
        row=1, col=1
    )

    # Panel 2: Unmet Demand
    fig.add_trace(
        go.Bar(
            x=scenario_summary_df["ScenarioID"],
            y=scenario_summary_df["TotalUnmetDemand"],
            name="Unmet Demand",
            marker_color=COLOR_CRIMSON,
            text=scenario_summary_df["TotalUnmetDemand"].apply(lambda v: f"{v:,}"),
            textposition="auto"
        ),
        row=1, col=2
    )

    fig.update_layout(height=450, **PLOTLY_LAYOUT_DEFAULTS)
    fig.update_xaxes(title_text="Optimization Scenario", row=1, col=1)
    fig.update_yaxes(title_text="Objective Function Z", row=1, col=1, showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    fig.update_xaxes(title_text="Optimization Scenario", row=1, col=2)
    fig.update_yaxes(title_text="Unmet Demand Units", row=1, col=2, showgrid=True, gridcolor=COLOR_LIGHT_GRAY)
    return fig


# =====================================================================
# 2. MATPLOTLIB STATIC PUBLICATION EXPORTS (For Reports & LaTeX)
# =====================================================================

def export_all_static_figures(
    df_clean: pd.DataFrame,
    output_dir: str = "outputs/figures"
) -> Dict[str, str]:
    """
    Generates high-resolution publication-quality PNG figures using Matplotlib
    for academic documentation and PDF report inclusion.
    """
    os.makedirs(output_dir, exist_ok=True)
    from exploratory_analysis import get_parking_area_statistics, get_hourly_occupancy_trends, get_day_of_week_trends
    from scenario_analysis import run_all_optimization_scenarios
    from sensitivity_analysis import run_budget_sensitivity_analysis
    from optimization_model import run_and_export_phase2_model

    area_stats = get_parking_area_statistics(df_clean)
    hourly = get_hourly_occupancy_trends(df_clean)
    dow = get_day_of_week_trends(df_clean)
    _, comp_df, _ = run_and_export_phase2_model(df_clean, output_dir="outputs")
    sens_df, _ = run_budget_sensitivity_analysis(df_clean, output_dir="outputs")
    scen_summary_df, _, _ = run_all_optimization_scenarios(df_clean, output_dir="outputs")

    exported_files = {}

    # --- Figure 1: Capacity vs Occupancy ---
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    sorted_stats = area_stats.sort_values(by="Capacity", ascending=True)
    y_pos = np.arange(len(sorted_stats))
    ax.barh(y_pos - 0.2, sorted_stats["Capacity"], height=0.4, label="Physical Capacity", color="#94A3B8")
    ax.barh(y_pos + 0.2, sorted_stats["AvgOccupancy"], height=0.4, label="Average Occupancy", color="#1E3A8A")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_stats["SystemCodeNumber"], fontsize=8)
    ax.set_xlabel("Number of Parking Bays", fontsize=10, fontweight="bold")
    ax.set_title("Figure 1: Parking Capacity vs. Average Occupancy across 30 Birmingham Facilities", fontsize=11, fontweight="bold", pad=12)
    ax.legend(frameon=True, facecolor="white")
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    f1_path = os.path.join(output_dir, "fig1_capacity_and_occupancy.png")
    fig.savefig(f1_path)
    plt.close(fig)
    exported_files["fig1"] = f1_path

    # --- Figure 2: Utilization Ranking ---
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    sorted_u = area_stats.sort_values(by="AvgUtilizationPct", ascending=True)
    colors = [COLOR_CRIMSON if u >= 65 else (COLOR_AMBER if u >= 40 else COLOR_SECONDARY_BLUE) for u in sorted_u["AvgUtilizationPct"]]
    y_pos = np.arange(len(sorted_u))
    ax.barh(y_pos, sorted_u["AvgUtilizationPct"], color=colors, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_u["SystemCodeNumber"], fontsize=8)
    ax.axvline(40.0, color=COLOR_AMBER, linestyle="--", linewidth=1.5, label="Moderate Threshold (40%)")
    ax.axvline(65.0, color=COLOR_CRIMSON, linestyle="--", linewidth=1.5, label="High Pressure Threshold (65%)")
    ax.set_xlabel("Average Utilization Percentage (%)", fontsize=10, fontweight="bold")
    ax.set_title("Figure 2: Parking Facility Average Utilization Hierarchy", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="lower right")
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    f2_path = os.path.join(output_dir, "fig2_utilization_ranking.png")
    fig.savefig(f2_path)
    plt.close(fig)
    exported_files["fig2"] = f2_path

    # --- Figure 3: Temporal Trends ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), dpi=300)
    ax1.plot(hourly["Hour"], hourly["AvgOccupancy"], color="#1E3A8A", marker="o", linewidth=2.2)
    ax1.fill_between(hourly["Hour"], hourly["AvgOccupancy"], color="#1E3A8A", alpha=0.15)
    ax1.set_xlabel("Hour of Day", fontsize=9, fontweight="bold")
    ax1.set_ylabel("Average Occupancy", fontsize=9, fontweight="bold")
    ax1.set_title("Diurnal Occupancy Pattern (07:00–16:30)", fontsize=10, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2.bar(dow["DayOfWeek"], dow["AvgOccupancy"], color="#0D9488", width=0.5)
    ax2.set_xlabel("Day of Week", fontsize=9, fontweight="bold")
    ax2.set_ylabel("Average Occupancy", fontsize=9, fontweight="bold")
    ax2.set_title("Weekly Occupancy Distribution", fontsize=10, fontweight="bold")
    ax2.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.xticks(rotation=30)
    fig.suptitle("Figure 3: Temporal Parking Demand Dynamics", fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    f3_path = os.path.join(output_dir, "fig3_temporal_trends.png")
    fig.savefig(f3_path)
    plt.close(fig)
    exported_files["fig3"] = f3_path

    # --- Figure 4: Baseline vs. Optimized Allocation ---
    fig, ax = plt.subplots(figsize=(12, 5), dpi=300)
    sorted_comp = comp_df.sort_values(by="PhysicalCapacity", ascending=False)
    x_idx = np.arange(len(sorted_comp))
    width = 0.35
    ax.bar(x_idx - width/2, sorted_comp["BaselineAllocation"], width=width, label="Proportional Baseline", color="#6B7280")
    ax.bar(x_idx + width/2, sorted_comp["OptimizedAllocation"], width=width, label="PuLP Optimized Allocation", color="#1E3A8A")
    ax.set_xticks(x_idx)
    ax.set_xticklabels(sorted_comp["Facility"], rotation=90, fontsize=7)
    ax.set_ylabel("Allocated Managed Permits", fontsize=9, fontweight="bold")
    ax.set_title("Figure 4: Facility Allocation Comparison: Baseline vs. PuLP Optimized", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    f4_path = os.path.join(output_dir, "fig4_baseline_vs_optimized.png")
    fig.savefig(f4_path)
    plt.close(fig)
    exported_files["fig4"] = f4_path

    # --- Figure 5: Budget Sensitivity Curve ---
    fig, ax_left = plt.subplots(figsize=(10, 5), dpi=300)
    ax_right = ax_left.twinx()

    l1 = ax_left.plot(sens_df["BudgetPermits"], sens_df["OptimizedObjective"], color="#1E3A8A", marker="s", linewidth=2.2, label="Optimized Objective (Z*)")
    l2 = ax_left.plot(sens_df["BudgetPermits"], sens_df["BaselineObjective"], color="#6B7280", linestyle="--", linewidth=1.8, label="Baseline Objective")
    l3 = ax_right.plot(sens_df["BudgetPermits"], sens_df["OptimizedUnmetDemand"], color="#EF4444", marker="v", linewidth=1.8, label="Unmet Demand")

    sat_row = sens_df[sens_df["BudgetFraction"] >= 1.0].iloc[0]
    ax_left.axvline(sat_row["BudgetPermits"], color="#0D9488", linestyle=":", linewidth=2.0, label="Saturation Point (B=28,823)")

    ax_left.set_xlabel("Managed Permit Budget (B)", fontsize=9, fontweight="bold")
    ax_left.set_ylabel("Weighted Objective Value (Z)", color="#1E3A8A", fontsize=9, fontweight="bold")
    ax_right.set_ylabel("Total Unmet Demand (Vehicles)", color="#EF4444", fontsize=9, fontweight="bold")
    ax_left.set_title("Figure 5: Parametric Budget Sensitivity & System Saturation", fontsize=11, fontweight="bold", pad=12)

    lines = l1 + l2 + l3
    labels = [l.get_label() for l in lines]
    ax_left.legend(lines, labels, loc="center right")
    ax_left.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    f5_path = os.path.join(output_dir, "fig5_budget_sensitivity.png")
    fig.savefig(f5_path)
    plt.close(fig)
    exported_files["fig5"] = f5_path

    # --- Figure 6: Scenario Comparison ---
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    x_scen = np.arange(len(scen_summary_df))
    bars = ax.bar(x_scen, scen_summary_df["WeightedObjective"], color="#1E3A8A", width=0.5)
    ax.set_xticks(x_scen)
    ax.set_xticklabels([f"S{i+1}: {name.split('. ')[-1]}" for i, name in enumerate(scen_summary_df["ScenarioName"])], rotation=15, fontsize=8)
    ax.set_ylabel("Weighted Objective Value (Z)", fontsize=9, fontweight="bold")
    ax.set_title("Figure 6: Operations Research Performance across the 5 Canonical Scenarios", fontsize=11, fontweight="bold", pad=12)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    f6_path = os.path.join(output_dir, "fig6_scenario_comparison.png")
    fig.savefig(f6_path)
    plt.close(fig)
    exported_files["fig6"] = f6_path

    return exported_files


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_raw_data
    from data_cleaning import clean_parking_data

    raw = load_raw_data()
    clean, _ = clean_parking_data(raw)
    files = export_all_static_figures(clean)
    print("Static Publication Figures Exported:")
    for k, v in files.items():
        print(f"  {k}: {v}")
