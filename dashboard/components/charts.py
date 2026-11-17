"""
charts.py
Interactive Plotly visualizations for the PARKOPT Streamlit application.
Renders responsive, publication-quality Operations Research charts.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Professional Academic Color Palette
COLOR_PRIMARY_BLUE = "#1E3A8A"
COLOR_SECONDARY_BLUE = "#2563EB"
COLOR_TEAL = "#0D9488"
COLOR_EMERALD = "#10B981"
COLOR_CRIMSON = "#EF4444"
COLOR_AMBER = "#F59E0B"
COLOR_SLATE = "#64748B"
COLOR_LIGHT_GRAY = "#E2E8F0"

PLOTLY_LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=11, color="#1E293B"),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    autosize=True,
    margin=dict(l=35, r=25, t=40, b=35),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#CBD5E1",
        borderwidth=1
    )
)


def render_capacity_vs_occupancy_chart(area_stats_df: pd.DataFrame) -> go.Figure:
    """
    Renders Capacity vs Average Occupancy across facilities.
    Dynamically scales height according to the number of facilities.
    """
    df = area_stats_df.sort_values(by="Capacity", ascending=True).copy()
    
    colors = [COLOR_CRIMSON if u >= 65.0 else COLOR_SECONDARY_BLUE for u in df["AvgUtilizationPct"]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["Capacity"],
        name="Physical Capacity",
        orientation="h",
        marker=dict(color="#CBD5E1"),
        hovertemplate="<b>%{y}</b><br>Capacity: %{x:,} bays<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgOccupancy"],
        name="Average Occupancy",
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="<b>%{y}</b><br>Avg Occupancy: %{x:.1f} vehicles<extra></extra>"
    ))

    chart_height = max(260, min(750, len(df) * 24)) if len(df) > 1 else 240

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Facility Capacity vs. Historical Average Occupancy</b>", font=dict(size=13, color="#0F172A")),
        barmode="group",
        height=chart_height,
        xaxis_title="Number of Parking Bays / Vehicles",
        yaxis=dict(autorange="reversed")
    )
    return fig


def render_utilization_ranking_chart(area_stats_df: pd.DataFrame) -> go.Figure:
    """
    Renders ranked facility utilization percentages with demand threshold reference lines.
    """
    df = area_stats_df.sort_values(by="AvgUtilizationPct", ascending=True).copy()
    
    colors = []
    tiers = []
    for u in df["AvgUtilizationPct"]:
        if u >= 65.0:
            colors.append(COLOR_CRIMSON)
            tiers.append("High Demand (>=65%)")
        elif u >= 40.0:
            colors.append(COLOR_AMBER)
            tiers.append("Moderate Demand (40-65%)")
        else:
            colors.append(COLOR_SECONDARY_BLUE)
            tiers.append("Low Demand (<40%)")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgUtilizationPct"],
        orientation="h",
        marker=dict(color=colors),
        text=[f"{u:.1f}%" for u in df["AvgUtilizationPct"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Utilization: %{x:.1f}%<extra></extra>"
    ))

    fig.add_vline(x=40.0, line_dash="dash", line_color=COLOR_AMBER, annotation_text="Moderate (40%)", annotation_position="top right")
    fig.add_vline(x=65.0, line_dash="dash", line_color=COLOR_CRIMSON, annotation_text="High Pressure (65%)", annotation_position="top right")

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Facility-Wise Parking Utilization Ranking & Demand Tiers</b>", font=dict(size=14, color="#0F172A")),
        height=720,
        xaxis=dict(title="Average Utilization Rate (%)", range=[0, 95]),
        yaxis=dict(autorange="reversed"),
        showlegend=False
    )
    return fig


def render_peak_vs_capacity_chart(area_stats_df: pd.DataFrame) -> go.Figure:
    """
    Renders Peak Occupancy vs Physical Capacity identifying overflow facilities.
    """
    df = area_stats_df.copy()
    peak_col = "PeakOccupancy" if "PeakOccupancy" in df.columns else "MaxOccupancy"
    df = df.sort_values(by=peak_col, ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["Capacity"],
        name="Physical Capacity",
        orientation="h",
        marker=dict(color="#CBD5E1"),
        hovertemplate="<b>%{y}</b><br>Capacity: %{x:,}<extra></extra>"
    ))
    
    overflow_colors = [COLOR_CRIMSON if p > c else COLOR_TEAL for p, c in zip(df[peak_col], df["Capacity"])]
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df[peak_col],
        name="Peak Observed Occupancy",
        orientation="h",
        marker=dict(color=overflow_colors),
        hovertemplate="<b>%{y}</b><br>Peak Occupancy: %{x:,}<extra></extra>"
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Peak Occupancy vs. Physical Capacity (Overflow Detection)</b>", font=dict(size=14, color="#0F172A")),
        barmode="overlay",
        height=720,
        xaxis_title="Vehicles / Parking Bays",
        yaxis=dict(autorange="reversed")
    )
    return fig


def render_temporal_diurnal_chart(hourly_df: pd.DataFrame, day_df: pd.DataFrame) -> go.Figure:
    """
    Renders combined diurnal hourly occupancy profile and day-of-week trends.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Diurnal Hourly Occupancy Curve (24h Profile)", "Day-of-Week Occupancy Volume"),
        column_widths=[0.6, 0.4]
    )

    # 1. Hourly Trend
    fig.add_trace(
        go.Scatter(
            x=hourly_df["Hour"],
            y=hourly_df["AvgOccupancy"],
            mode="lines+markers",
            name="Hourly Mean",
            line=dict(color=COLOR_PRIMARY_BLUE, width=2.8),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.1)",
            hovertemplate="Hour %{x}:00<br>Avg Occupancy: %{y:,.0f} cars<extra></extra>"
        ),
        row=1, col=1
    )

    # 2. Day-of-week Trend
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if "Day_of_Week" in day_df.columns:
        day_df_sorted = day_df.copy()
        day_df_sorted["sort_idx"] = day_df_sorted["Day_of_Week"].map(lambda d: days_order.index(d) if d in days_order else 99)
        day_df_sorted = day_df_sorted.sort_values(by="sort_idx")
        day_names = day_df_sorted["Day_of_Week"]
        day_vals = day_df_sorted["AvgOccupancy"]
    else:
        day_names = day_df.iloc[:, 0]
        day_vals = day_df.iloc[:, 1]

    bar_colors = [COLOR_AMBER if d in ["Saturday", "Sunday"] else COLOR_TEAL for d in day_names]
    fig.add_trace(
        go.Bar(
            x=day_names,
            y=day_vals,
            name="Day Mean",
            marker=dict(color=bar_colors),
            hovertemplate="Day: %{x}<br>Avg Occupancy: %{y:,.0f} cars<extra></extra>"
        ),
        row=1, col=2
    )

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Temporal Parking Dynamics (Diurnal and Weekly Cycle)</b>", font=dict(size=14, color="#0F172A")),
        height=380,
        showlegend=False
    )
    fig.update_xaxes(title_text="Hour of Day (0-23)", row=1, col=1)
    fig.update_yaxes(title_text="Average Occupancy (Vehicles)", row=1, col=1)
    fig.update_xaxes(title_text="Day of Week", row=1, col=2)
    fig.update_yaxes(title_text="Average Occupancy", row=1, col=2)
    return fig


def render_hourly_heatmap_chart(df_clean: pd.DataFrame) -> go.Figure:
    """
    Renders 2D Matrix Heatmap: 30 Facilities vs 24 Hours Average Occupancy.
    """
    df = df_clean.copy()
    if "Hour" not in df.columns:
        df["Hour"] = pd.to_datetime(df["LastUpdated"]).dt.hour

    pivot = df.pivot_table(index="SystemCodeNumber", columns="Hour", values="Occupancy", aggfunc="mean").fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in pivot.columns],
        y=pivot.index,
        colorscale="Viridis",
        colorbar=dict(title="Avg Cars"),
        hovertemplate="Facility: %{y}<br>Time: %{x}<br>Avg Occupancy: %{z:.1f}<extra></extra>"
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Facility Occupancy Heatmap Across 24-Hour Cycle</b>", font=dict(size=14, color="#0F172A")),
        height=720,
        xaxis_title="Time of Day",
        yaxis=dict(autorange="reversed")
    )
    return fig


def render_baseline_vs_opt_chart(comp_df: pd.DataFrame) -> go.Figure:
    """
    Renders grouped bar comparison of Proportional Baseline vs PuLP LP Optimized allocation.
    """
    df = comp_df.sort_values(by="EstimatedDemand", ascending=True).copy()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Facility"],
        x=df["BaselineAllocation"],
        name="Proportional Baseline",
        orientation="h",
        marker=dict(color="#94A3B8"),
        hovertemplate="<b>%{y}</b><br>Baseline: %{x:,} permits<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        y=df["Facility"],
        x=df["OptimizedAllocation"],
        name="PuLP LP Optimized",
        orientation="h",
        marker=dict(color=COLOR_SECONDARY_BLUE),
        hovertemplate="<b>%{y}</b><br>Optimized: %{x:,} permits<extra></extra>"
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Baseline vs. PuLP LP Optimized Permit Allocation</b>", font=dict(size=14, color="#0F172A")),
        barmode="group",
        height=750,
        xaxis_title="Allocated Managed Permits / Admission Slots",
        yaxis=dict(autorange="reversed")
    )
    return fig


def render_demand_fulfillment_chart(comp_df: pd.DataFrame) -> go.Figure:
    """
    Renders stacked bar chart of Allocated Permits vs Unmet Demand per facility.
    """
    df = comp_df.sort_values(by="EstimatedDemand", ascending=True).copy()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Facility"],
        x=df["OptimizedAllocation"],
        name="Satisfied Demand (Allocated)",
        orientation="h",
        marker=dict(color=COLOR_EMERALD),
        hovertemplate="<b>%{y}</b><br>Satisfied: %{x:,} permits<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        y=df["Facility"],
        x=df["OptimizedUnmetDemand"],
        name="Unmet Demand",
        orientation="h",
        marker=dict(color=COLOR_CRIMSON),
        hovertemplate="<b>%{y}</b><br>Unmet Demand: %{x:,} permits<extra></extra>"
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Demand Fulfillment Breakdown: Allocated vs. Unmet Demand</b>", font=dict(size=14, color="#0F172A")),
        barmode="stack",
        height=750,
        xaxis_title="Total Estimated Demand (Permits)",
        yaxis=dict(autorange="reversed")
    )
    return fig


def render_allocation_diff_chart(comp_df: pd.DataFrame) -> go.Figure:
    """
    Renders diverging horizontal bar chart of reallocations (Delta = Optimized - Baseline).
    """
    df = comp_df.sort_values(by="AllocationDifference", ascending=True).copy()
    colors = [COLOR_EMERALD if d >= 0 else COLOR_CRIMSON for d in df["AllocationDifference"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Facility"],
        x=df["AllocationDifference"],
        orientation="h",
        marker=dict(color=colors),
        text=[f"{d:+d}" for d in df["AllocationDifference"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Reallocation Shift: %{x:+d} permits<extra></extra>"
    ))

    fig.add_vline(x=0, line_color="#0F172A", line_width=1.2)

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Reallocation Shifts: Optimized vs. Baseline (&Delta; = LP - Base)</b>", font=dict(size=14, color="#0F172A")),
        height=750,
        xaxis_title="Net Reallocation Shift (Managed Permits)",
        yaxis=dict(autorange="reversed"),
        showlegend=False
    )
    return fig


def render_budget_sweep_chart(sens_df: pd.DataFrame) -> go.Figure:
    """
    Renders Budget Sweep Curve showing Total Allocated Permits and Unmet Demand.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=sens_df["Budget"],
        y=sens_df["TotalAllocated"],
        name="Total Allocated Permits",
        mode="lines+markers",
        line=dict(color=COLOR_PRIMARY_BLUE, width=3),
        hovertemplate="Budget: %{x:,}<br>Allocated: %{y:,}<extra></extra>"
    ))
    
    fig.add_trace(go.Scatter(
        x=sens_df["Budget"],
        y=sens_df["UnmetDemand"],
        name="System Unmet Demand",
        mode="lines+markers",
        line=dict(color=COLOR_CRIMSON, width=3, dash="dot"),
        hovertemplate="Budget: %{x:,}<br>Unmet: %{y:,}<extra></extra>"
    ))

    # Mark Saturation Threshold B* = 28,823
    fig.add_vline(x=28823, line_dash="dash", line_color=COLOR_EMERALD, annotation_text="Saturation Threshold B* = 28,823", annotation_position="top left")

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Budget Sensitivity Analysis: Total Allocation & Unmet Demand</b>", font=dict(size=14, color="#0F172A")),
        height=420,
        xaxis_title="Managed Permit Budget (B)",
        yaxis_title="Permits / Units"
    )
    return fig


def render_marginal_return_chart(sens_df: pd.DataFrame) -> go.Figure:
    """
    Renders Marginal Return of Objective Value (dZ/dB) vs Budget.
    """
    df = sens_df.sort_values(by="Budget").copy()
    if "MarginalGain" not in df.columns:
        df["MarginalGain"] = df["ObjectiveValue"].diff() / df["Budget"].diff()
        df["MarginalGain"] = df["MarginalGain"].fillna(1.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Budget"],
        y=df["MarginalGain"],
        mode="lines+markers",
        name="Marginal Return (dZ/dB)",
        line=dict(color=COLOR_TEAL, width=2.8, shape="hv"),
        fill="tozeroy",
        fillcolor="rgba(13, 148, 136, 0.1)",
        hovertemplate="Budget: %{x:,}<br>Marginal Gain: %{y:.3f}<extra></extra>"
    ))

    fig.add_vline(x=28823, line_dash="dash", line_color=COLOR_CRIMSON, annotation_text="dZ/dB = 0.000 at B* = 28,823", annotation_position="top right")

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Marginal Objective Return: dZ/dB vs. Budget Limit</b>", font=dict(size=14, color="#0F172A")),
        height=380,
        xaxis_title="Managed Permit Budget (B)",
        yaxis_title="Marginal Objective Gain (dZ/dB)"
    )
    return fig


def render_satisfaction_transitions_chart(sens_df: pd.DataFrame) -> go.Figure:
    """
    Renders breakdown of Fully Satisfied, Partially Satisfied, and Zero Allocation facilities across budget.
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sens_df["Budget"],
        y=sens_df["FullySatisfiedCount"],
        name="Fully Satisfied Facilities",
        marker=dict(color=COLOR_EMERALD)
    ))
    fig.add_trace(go.Bar(
        x=sens_df["Budget"],
        y=sens_df["PartiallySatisfiedCount"],
        name="Partially Satisfied Facilities",
        marker=dict(color=COLOR_AMBER)
    ))
    fig.add_trace(go.Bar(
        x=sens_df["Budget"],
        y=sens_df["ZeroAllocationCount"],
        name="Zero Allocation Facilities",
        marker=dict(color=COLOR_CRIMSON)
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Facility Satisfaction Transitions Under Varying Budgets</b>", font=dict(size=14, color="#0F172A")),
        barmode="stack",
        height=400,
        xaxis_title="Managed Permit Budget (B)",
        yaxis_title="Number of Facilities (Total: 30)"
    )
    return fig


def render_scenarios_comparison_chart(summary_df: pd.DataFrame) -> go.Figure:
    """
    Renders comparison across canonical scenarios.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Weighted Objective Value (Z*)", "System Unmet Demand (Permits)"),
        column_widths=[0.5, 0.5]
    )

    scen_names = summary_df["ScenarioName"].tolist()

    fig.add_trace(
        go.Bar(
            x=scen_names,
            y=summary_df["ObjectiveValue"],
            name="Objective Value",
            marker=dict(color=COLOR_PRIMARY_BLUE),
            hovertemplate="Scenario: %{x}<br>Obj: %{y:,.1f}<extra></extra>"
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(
            x=scen_names,
            y=summary_df["UnmetDemand"],
            name="Unmet Demand",
            marker=dict(color=COLOR_CRIMSON),
            hovertemplate="Scenario: %{x}<br>Unmet: %{y:,.0f}<extra></extra>"
        ),
        row=1, col=2
    )

    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Canonical Scenarios Evaluation: Objective Value & Unmet Demand</b>", font=dict(size=14, color="#0F172A")),
        height=400,
        showlegend=False
    )
    return fig


# ---------------------------------------------------------------------
# Simplified Clean Charts for Modern UI/UX Redesign
# ---------------------------------------------------------------------

def render_top5_demand_chart(area_stats_df: pd.DataFrame) -> go.Figure:
    """
    Renders Top 5 high-demand facilities horizontal bar chart comparing Capacity and Average Occupancy.
    """
    df = area_stats_df.sort_values(by="AvgOccupancy", ascending=False).head(5).sort_values(by="AvgOccupancy", ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["Capacity"],
        name="Capacity",
        orientation="h",
        marker=dict(color="#CBD5E1"),
        hovertemplate="<b>%{y}</b><br>Capacity: %{x:,} bays<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgOccupancy"],
        name="Avg Occupied",
        orientation="h",
        marker=dict(color=COLOR_SECONDARY_BLUE),
        hovertemplate="<b>%{y}</b><br>Avg Occupancy: %{x:.0f} cars<extra></extra>"
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Top 5 High-Demand Facilities (Occupancy vs Capacity)</b>", font=dict(size=13, color="#0F172A")),
        barmode="group",
        height=280,
        xaxis_title="Number of Parking Spaces",
        yaxis=dict(autorange="reversed")
    )
    return fig


def render_top5_underutilized_chart(area_stats_df: pd.DataFrame) -> go.Figure:
    """
    Renders Top 5 underutilized facilities horizontal bar chart comparing Capacity and Average Occupancy.
    """
    df = area_stats_df.sort_values(by="AvgUtilizationPct", ascending=True).head(5).sort_values(by="AvgUtilizationPct", ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["Capacity"],
        name="Capacity",
        orientation="h",
        marker=dict(color="#CBD5E1"),
        hovertemplate="<b>%{y}</b><br>Capacity: %{x:,} bays<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        y=df["SystemCodeNumber"],
        x=df["AvgOccupancy"],
        name="Avg Occupied",
        orientation="h",
        marker=dict(color="#64748B"),
        hovertemplate="<b>%{y}</b><br>Avg Occupancy: %{x:.0f} cars<extra></extra>"
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Top 5 Underutilized Facilities (Excess Buffer)</b>", font=dict(size=13, color="#0F172A")),
        barmode="group",
        height=280,
        xaxis_title="Number of Parking Spaces",
        yaxis=dict(autorange="reversed")
    )
    return fig



def render_utilization_distribution_chart(area_stats_df: pd.DataFrame) -> go.Figure:
    """
    Renders breakdown of parking facilities by utilization tier (High, Moderate, Low).
    """
    high_count = int((area_stats_df["AvgUtilizationPct"] >= 65.0).sum())
    mod_count = int(((area_stats_df["AvgUtilizationPct"] >= 40.0) & (area_stats_df["AvgUtilizationPct"] < 65.0)).sum())
    low_count = int((area_stats_df["AvgUtilizationPct"] < 40.0).sum())
    
    categories = ["High Demand (≥ 65%)", "Moderate (40–65%)", "Low Demand (< 40%)"]
    counts = [high_count, mod_count, low_count]
    colors = [COLOR_AMBER, COLOR_SECONDARY_BLUE, "#94A3B8"]
    
    fig = go.Figure(data=[go.Bar(
        x=categories,
        y=counts,
        text=[f"{c} lots" for c in counts],
        textposition="outside",
        marker=dict(color=colors)
    )])
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text="<b>Facility Count by Demand Tier</b>", font=dict(size=13, color="#0F172A")),
        height=320,
        yaxis=dict(title="Number of Facilities", range=[0, max(counts) + 4]),
        showlegend=False
    )
    return fig


def render_facility_hourly_chart(df_clean: pd.DataFrame, facility_code: Optional[str] = None) -> go.Figure:
    """
    Renders hourly occupancy trend curve for a specific facility or the entire system.
    """
    df = df_clean.copy()
    if "Hour" not in df.columns:
        df["Hour"] = pd.to_datetime(df["LastUpdated"]).dt.hour
        
    if facility_code and facility_code != "All Facilities":
        df = df[df["SystemCodeNumber"] == facility_code]
        title_text = f"<b>Hourly Occupancy Pattern — {facility_code}</b>"
    else:
        title_text = "<b>Hourly Parking Demand Pattern (Overall System)</b>"
        
    hourly_avg = df.groupby("Hour")["Occupancy"].mean().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hourly_avg["Hour"],
        y=hourly_avg["Occupancy"],
        mode="lines+markers",
        name="Average Occupancy",
        line=dict(color=COLOR_SECONDARY_BLUE, width=3),
        fill="tozeroy",
        fillcolor="rgba(37, 99, 235, 0.08)",
        hovertemplate="Hour %{x}:00<br>Avg Occupancy: %{y:,.1f} vehicles<extra></extra>"
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title=dict(text=title_text, font=dict(size=13, color="#0F172A")),
        height=340,
        xaxis=dict(title="Hour of Day (0–23)", dtick=2),
        yaxis=dict(title="Occupied Spaces (Vehicles)"),
        showlegend=False
    )
    return fig


def render_demand_vs_recommended_chart(comp_df: pd.DataFrame) -> go.Figure:
    """Renders simplified Demand vs Recommended Allocation chart."""
    return render_demand_fulfillment_chart(comp_df)


def render_reallocation_shifts_chart(comp_df: pd.DataFrame) -> go.Figure:
    """Renders simplified Reallocation Shifts chart."""
    return render_allocation_diff_chart(comp_df)

