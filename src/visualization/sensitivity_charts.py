"""
sensitivity_charts.py
Visualizations for Parametric Budget Sensitivity, Saturation, and Diminishing Returns.
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
    COLOR_DARK_SLATE, PLOTLY_TEMPLATE, validate_required_columns, save_static_and_interactive
)


def plot_budget_vs_objective_and_unmet(
    sensitivity_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/sensitivity"
) -> Dict[str, str]:
    """
    Visualization 6.1 & 6.2: Dual-Axis Budget Sensitivity:
    Permit Budget vs. Weighted Objective Value (Primary Axis) & Unmet Demand (Secondary Axis).
    Highlights the Saturation Point (B = 28,823).
    Generates both PNG and HTML.
    """
    validate_required_columns(
        sensitivity_df,
        ["BudgetPermits", "OptimizedObjective", "BaselineObjective", "OptimizedUnmetDemand", "BudgetFraction"],
        "Budget vs. Objective & Unmet Demand"
    )

    sat_row = sensitivity_df[sensitivity_df["BudgetFraction"] >= 1.0].iloc[0]
    sat_b = int(sat_row["BudgetPermits"])

    # --- 1. Matplotlib Static ---
    fig_mpl, ax1 = plt.subplots(figsize=(10.5, 5.5))
    ax2 = ax1.twinx()

    l1 = ax1.plot(sensitivity_df["BudgetPermits"], sensitivity_df["OptimizedObjective"],
                  color=COLOR_PRIMARY_BLUE, marker="s", markersize=5, linewidth=2.4, label="PuLP Optimized (Z*)")
    l2 = ax1.plot(sensitivity_df["BudgetPermits"], sensitivity_df["BaselineObjective"],
                  color=COLOR_SLATE, linestyle="--", linewidth=1.8, label="Proportional Baseline (Z_base)")
    l3 = ax2.plot(sensitivity_df["BudgetPermits"], sensitivity_df["OptimizedUnmetDemand"],
                  color=COLOR_CRIMSON, marker="v", markersize=5, linewidth=2.0, label="Unmet Demand (Deficit)")

    # Saturation Line
    ax1.axvline(sat_b, color=COLOR_TEAL, linestyle=":", linewidth=2.2, label=f"Saturation Threshold (B={sat_b:,})")
    ax1.axvspan(sat_b, sensitivity_df["BudgetPermits"].max(), color="#F1F5F9", alpha=0.5, label="Non-Binding Region")

    ax1.set_xlabel("Managed Parking Permit Allocation Budget (B)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Weighted Objective Value (Z)", color=COLOR_PRIMARY_BLUE, fontsize=10, fontweight="bold")
    ax2.set_ylabel("Total Unmet Vehicle Demand", color=COLOR_CRIMSON, fontsize=10, fontweight="bold")
    ax1.set_title("Figure 6.1: Budget Sensitivity & System Saturation Threshold", fontsize=11, fontweight="bold", pad=12)

    lines = l1 + l2 + l3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="center right", frameon=True, facecolor="white")
    ax1.grid(True, linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive ---
    fig_plotly = make_subplots(specs=[[{"secondary_y": True}]])
    fig_plotly.add_trace(
        go.Scatter(
            x=sensitivity_df["BudgetPermits"],
            y=sensitivity_df["OptimizedObjective"],
            name="Optimized Objective (Z*)",
            mode="lines+markers",
            line=dict(color=COLOR_PRIMARY_BLUE, width=3)
        ),
        secondary_y=False
    )
    fig_plotly.add_trace(
        go.Scatter(
            x=sensitivity_df["BudgetPermits"],
            y=sensitivity_df["BaselineObjective"],
            name="Baseline Objective",
            mode="lines",
            line=dict(color=COLOR_SLATE, dash="dash", width=2)
        ),
        secondary_y=False
    )
    fig_plotly.add_trace(
        go.Scatter(
            x=sensitivity_df["BudgetPermits"],
            y=sensitivity_df["OptimizedUnmetDemand"],
            name="Unmet Demand",
            mode="lines+markers",
            line=dict(color=COLOR_CRIMSON, width=2)
        ),
        secondary_y=True
    )
    fig_plotly.add_vline(
        x=sat_b,
        line_dash="dot",
        line_color=COLOR_TEAL,
        line_width=2.5,
        annotation_text=f"Saturation Point (B={sat_b:,})",
        annotation_position="top left"
    )
    fig_plotly.update_layout(
        title="<b>Parametric Budget Sensitivity: Objective Gain & Unmet Demand vs. Permit Budget</b>",
        xaxis_title="Managed Permit Budget (B)",
        height=520,
        **PLOTLY_TEMPLATE["layout"]
    )
    fig_plotly.update_yaxes(title_text="Weighted Objective Value (Z)", secondary_y=False)
    fig_plotly.update_yaxes(title_text="Total Unmet Demand (Vehicles)", secondary_y=True)

    return save_static_and_interactive(fig_mpl, fig_plotly, "budget_vs_objective_and_unmet", output_dir)


def plot_budget_utilization_and_marginal_returns(
    sensitivity_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/sensitivity"
) -> Dict[str, str]:
    """
    Visualization 6.3: Budget Utilization Percentage & Marginal Value per Permit (dZ/dB).
    Demonstrates resource scarcity binding condition and the Law of Diminishing Marginal Returns.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        sensitivity_df,
        ["BudgetPermits", "BudgetFraction", "BudgetUtilizationPct", "MarginalValuePerPermit"],
        "Budget Utilization and Marginal Returns"
    )
    df_nonzero = sensitivity_df[sensitivity_df["BudgetPermits"] > 0].copy()

    # --- 1. Matplotlib Static Subplots ---
    fig_mpl, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

    # Left: Budget Utilization %
    ax1.plot(sensitivity_df["BudgetFraction"] * 100.0, sensitivity_df["BudgetUtilizationPct"],
             color=COLOR_EMERALD, marker="o", linewidth=2.4)
    ax1.axvline(100.0, color=COLOR_CRIMSON, linestyle="--", label="100% Demand Level")
    ax1.set_xlabel("Budget Level (% of Allocatable Demand)", fontsize=9.5, fontweight="bold")
    ax1.set_ylabel("Budget Utilization Rate (%)", fontsize=9.5, fontweight="bold")
    ax1.set_title("Budget Utilization Efficiency (%)\n(Drops when B > 100% Demand)", fontsize=10.5, fontweight="bold")
    ax1.legend(loc="lower left", frameon=True, facecolor="white")
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Right: Marginal Value (dZ/dB)
    ax2.plot(df_nonzero["BudgetFraction"] * 100.0, df_nonzero["MarginalValuePerPermit"],
             color=COLOR_AMBER, marker="s", linewidth=2.4, drawstyle="steps-post")
    ax2.fill_between(df_nonzero["BudgetFraction"] * 100.0, df_nonzero["MarginalValuePerPermit"],
                     color=COLOR_AMBER, alpha=0.15, step="post")
    ax2.axvline(100.0, color=COLOR_TEAL, linestyle=":", label="Marginal Value = 0 Threshold")
    ax2.set_xlabel("Budget Level (% of Allocatable Demand)", fontsize=9.5, fontweight="bold")
    ax2.set_ylabel("Marginal Objective Return (dZ/dB)", fontsize=9.5, fontweight="bold")
    ax2.set_title("Marginal Value per Permit (dZ/dB)\n(Law of Diminishing Marginal Returns)", fontsize=10.5, fontweight="bold")
    ax2.legend(loc="upper right", frameon=True, facecolor="white")
    ax2.grid(True, linestyle="--", alpha=0.5)

    fig_mpl.suptitle("Figure 6.3: Budget Scarcity Mechanics & Diminishing Marginal Returns", fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()

    # --- 2. Plotly Interactive ---
    fig_plotly = make_subplots(
        rows=1, cols=2,
        subplot_titles=("<b>Budget Utilization Rate (%)</b>", "<b>Marginal Value per Permit (dZ/dB)</b>"),
        horizontal_spacing=0.12
    )
    fig_plotly.add_trace(
        go.Scatter(
            x=sensitivity_df["BudgetFraction"] * 100.0,
            y=sensitivity_df["BudgetUtilizationPct"],
            mode="lines+markers",
            name="Utilization %",
            line=dict(color=COLOR_EMERALD, width=2.8)
        ),
        row=1, col=1
    )
    fig_plotly.add_trace(
        go.Scatter(
            x=df_nonzero["BudgetFraction"] * 100.0,
            y=df_nonzero["MarginalValuePerPermit"],
            mode="lines+markers",
            line=dict(color=COLOR_AMBER, width=2.8, shape="hv"),
            fill="tozeroy",
            fillcolor="rgba(245, 158, 11, 0.15)",
            name="dZ/dB"
        ),
        row=1, col=2
    )
    fig_plotly.update_layout(height=450, **PLOTLY_TEMPLATE["layout"])
    fig_plotly.update_xaxes(title_text="Budget Level (% Demand)", row=1, col=1)
    fig_plotly.update_yaxes(title_text="Utilization (%)", row=1, col=1)
    fig_plotly.update_xaxes(title_text="Budget Level (% Demand)", row=1, col=2)
    fig_plotly.update_yaxes(title_text="Marginal Return (dZ/dB)", row=1, col=2)

    return save_static_and_interactive(fig_mpl, fig_plotly, "budget_utilization_and_marginal_returns", output_dir)


def plot_facility_satisfaction_transitions(
    sensitivity_df: pd.DataFrame,
    output_dir: str = "outputs/visualizations/sensitivity"
) -> Dict[str, str]:
    """
    Visualization 6.4 & 6.5: Facility Satisfaction Transitions Across Budget Levels.
    Tracks count of Fully Satisfied, Partially Satisfied, and Zero Allocation Facilities.
    Generates both PNG and HTML.
    """
    validate_required_columns(
        sensitivity_df,
        ["BudgetFraction", "FullySatisfiedFacilities", "PartiallySatisfiedFacilities", "ZeroAllocationFacilities"],
        "Facility Satisfaction Transitions"
    )

    x_vals = sensitivity_df["BudgetFraction"] * 100.0

    # --- 1. Matplotlib Static Stacked Area ---
    fig_mpl, ax = plt.subplots(figsize=(10, 5))
    ax.stackplot(
        x_vals,
        sensitivity_df["FullySatisfiedFacilities"],
        sensitivity_df["PartiallySatisfiedFacilities"],
        sensitivity_df["ZeroAllocationFacilities"],
        labels=["1. Fully Satisfied Facilities", "2. Partially Satisfied Facilities", "3. Zero Allocation Facilities"],
        colors=[COLOR_EMERALD, COLOR_AMBER, COLOR_CRIMSON],
        alpha=0.85
    )
    ax.axvline(100.0, color=COLOR_DARK_SLATE, linestyle="--", linewidth=1.5, label="Saturation (100% Demand)")
    ax.set_xlabel("Budget Level (% of Allocatable Demand)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Number of Facilities (Total = 30)", fontsize=10, fontweight="bold")
    ax.set_title("Figure 6.4: Transition of Facility Satisfaction Tiers Across Budget Levels", fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="center right", frameon=True, facecolor="white")
    ax.set_ylim(0, 30)
    ax.grid(True, linestyle="--", alpha=0.4)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Scatter(
        x=x_vals, y=sensitivity_df["FullySatisfiedFacilities"],
        name="Fully Satisfied", mode="lines", stackgroup="one", fillcolor="rgba(16, 185, 129, 0.7)", line=dict(color=COLOR_EMERALD)
    ))
    fig_plotly.add_trace(go.Scatter(
        x=x_vals, y=sensitivity_df["PartiallySatisfiedFacilities"],
        name="Partially Satisfied", mode="lines", stackgroup="one", fillcolor="rgba(245, 158, 11, 0.7)", line=dict(color=COLOR_AMBER)
    ))
    fig_plotly.add_trace(go.Scatter(
        x=x_vals, y=sensitivity_df["ZeroAllocationFacilities"],
        name="Zero Allocation", mode="lines", stackgroup="one", fillcolor="rgba(239, 68, 68, 0.7)", line=dict(color=COLOR_CRIMSON)
    ))
    fig_plotly.update_layout(
        title="<b>Facility Satisfaction Tier Transitions (Count of Facilities)</b>",
        xaxis_title="Budget Level (% of Allocatable Demand)",
        yaxis_title="Facility Count (out of 30)",
        height=480
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "facility_satisfaction_transitions", output_dir)


def plot_budget_scenarios_allocation_shifts(
    output_dir: str = "outputs/visualizations/sensitivity"
) -> Dict[str, str]:
    """
    Visualization 6.6: Allocation Changes Under Different Budgets (50% Low, 75% Medium, 90% High).
    Reads from outputs/scenario_comparison.csv.
    Generates both PNG and HTML.
    """
    scen_csv = "outputs/scenario_comparison.csv"
    if not os.path.exists(scen_csv):
        raise FileNotFoundError(f"Missing scenario comparison CSV: {scen_csv}")
    
    df = pd.read_csv(scen_csv)
    # Filter to 95th percentile with Congestion Priority across Low, Med, High
    subset = df[(df["DemandEstimator"] == "p95") & (df["PriorityStrategy"] == "congestion")].copy()
    
    # --- 1. Matplotlib Static ---
    fig_mpl, ax = plt.subplots(figsize=(9, 4.8))
    x_pos = np.arange(len(subset))
    bars = ax.bar(x_pos, subset["OptimizedAllocated"], color=COLOR_PRIMARY_BLUE, width=0.45)
    
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:,}\npermits", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{row['BudgetScenario'].capitalize()} Budget\n({int(row['BudgetFraction']*100)}%)" for _, row in subset.iterrows()], fontsize=9.5)
    ax.set_ylabel("Total Managed Permits Allocated", fontsize=10, fontweight="bold")
    ax.set_title("Figure 6.6: Total Permits Allocated across Low, Medium, and High Budget Tiers", fontsize=11, fontweight="bold", pad=12)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    # --- 2. Plotly Interactive ---
    fig_plotly = go.Figure(layout=PLOTLY_TEMPLATE["layout"])
    fig_plotly.add_trace(go.Bar(
        x=[f"{s.capitalize()} Budget ({int(f*100)}%)" for s, f in zip(subset["BudgetScenario"], subset["BudgetFraction"])],
        y=subset["OptimizedAllocated"],
        marker_color=COLOR_PRIMARY_BLUE,
        text=subset["OptimizedAllocated"].apply(lambda v: f"{v:,} permits"),
        textposition="auto"
    ))
    fig_plotly.update_layout(
        title="<b>Permit Allocation Volume Across Standard Budget Tiers</b>",
        xaxis_title="Budget Scenario",
        yaxis_title="Total Allocated Permits",
        height=450
    )

    return save_static_and_interactive(fig_mpl, fig_plotly, "budget_scenarios_allocation_shifts", output_dir)


def generate_all_sensitivity_charts(
    output_dir: str = "outputs/visualizations/sensitivity"
) -> Dict[str, Dict[str, str]]:
    """
    Executes the complete Sensitivity Analysis visualization suite (6.1 through 6.6).
    """
    sens_path = "outputs/budget_sensitivity.csv"
    if not os.path.exists(sens_path):
        raise FileNotFoundError(f"Missing required sensitivity file: {sens_path}")
    sens_df = pd.read_csv(sens_path)

    results = {
        "budget_vs_objective_and_unmet": plot_budget_vs_objective_and_unmet(sens_df, output_dir),
        "budget_utilization_and_returns": plot_budget_utilization_and_marginal_returns(sens_df, output_dir),
        "satisfaction_transitions": plot_facility_satisfaction_transitions(sens_df, output_dir),
        "budget_scenarios_shifts": plot_budget_scenarios_allocation_shifts(output_dir)
    }
    return results


if __name__ == "__main__":
    res = generate_all_sensitivity_charts()
    print("Sensitivity Charts Generated:")
    for k, v in res.items():
        print(f"  {k}: PNG -> {v['png']}, HTML -> {v['html']}")
