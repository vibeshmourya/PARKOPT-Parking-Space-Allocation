"""
4_Results_and_Reports.py
Section 4: Results & Academic Reports for PARKOPT.
Compares recommended allocations against proportional baseline, presents facility tables,
demand fulfillment charts, 5-scenario evaluation, and exports CSV and academic PDF reports.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import streamlit as st
import pandas as pd
from dashboard.utils.formatting import (
    CUSTOM_DASHBOARD_CSS, format_number, format_pct
)
from dashboard.utils.state_manager import get_state, set_state
from dashboard.utils.data_service import (
    load_cleaned_dataset,
    load_facility_statistics,
    load_scenario_summaries,
    load_budget_sensitivity_data
)
from dashboard.utils.optimization_service import run_solver_workflow
from dashboard.utils.report_service import generate_academic_pdf_report
from dashboard.components.sidebar import render_sidebar
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.charts import (
    render_demand_fulfillment_chart,
    render_allocation_diff_chart,
    render_scenarios_comparison_chart
)
from dashboard.components.tables import render_simple_results_table, render_allocation_comparison_table


def render_results_and_reports_page() -> None:
    """
    Renders Section 4: Results.
    Displays recommended allocation metrics, baseline comparison, facility-wise allocation table,
    demand fulfillment chart, reallocation difference chart, 5-scenario analysis, and PDF/CSV downloads.
    """
    st.markdown(CUSTOM_DASHBOARD_CSS, unsafe_allow_html=True)
    render_sidebar()

    # 1. Header
    st.markdown(
        """<div class="hero-card">
<h1 class="hero-title">Optimization Results & Evaluation</h1>
<div class="hero-subtitle">Comparative Allocation Analysis, Scenarios & Reports</div>
<p class="hero-desc">Evaluate the LP recommended permit allocations against the proportional baseline. Examine demand fulfillment, reallocation shifts, and multi-scenario stress tests.</p>
</div>""",
        unsafe_allow_html=True
    )

    df_clean = load_cleaned_dataset()
    area_stats = load_facility_statistics(df_clean)

    # 2. Retrieve or Compute Optimization Results
    opt_result = get_state("latest_opt_result")
    comp_df = get_state("comparison_df")
    comp_summary = get_state("comparison_summary")

    if opt_result is None or comp_df is None or comp_summary is None:
        # Run default canonical optimization
        with st.spinner("Computing baseline vs. optimal allocation..."):
            opt_result, comp_df, comp_summary = run_solver_workflow(
                df_clean=df_clean,
                budget=87,
                demand_method="p95",
                priority_scenario="congestion"
            )
            set_state("latest_opt_result", opt_result)
            set_state("comparison_df", comp_df)
            set_state("comparison_summary", comp_summary)
            set_state("current_budget", 87)
            set_state("current_demand_method", "p95")
            set_state("current_priority_scenario", "congestion")

    # 3. High-Level Allocation KPIs (Native Streamlit Components)
    budget = get_state("current_budget") or 87
    total_alloc = comp_summary.get("optimized_total_allocated", budget)
    unmet = comp_summary.get("optimized_unmet_demand", 0)
    obj_val = comp_summary.get("optimized_objective", 0.0)
    obj_gain = comp_summary.get("objective_improvement", 0.0)
    obj_gain_pct = comp_summary.get("objective_improvement_pct", 0.0)

    render_kpi_row([
        {"label": "Recommended Allocation", "value": f"{format_number(total_alloc)} permits", "subtext": f"Budget: {format_number(budget)}", "badge": "ALLOCATED", "border_left_color": "#2563EB"},
        {"label": "Optimization Score (Z*)", "value": f"{format_number(obj_val, decimals=1)}", "subtext": f"+{obj_gain:,.1f} vs baseline", "delta": f"+{obj_gain_pct:.1f}%", "delta_positive": True, "badge": "SCORE", "border_left_color": "#10B981"},
        {"label": "Estimated Unmet Demand", "value": f"{format_number(unmet)} permits", "subtext": "Demand exceeding quota", "badge": "UNMET", "border_left_color": "#EF4444" if unmet > 0 else "#10B981"},
        {"label": "Fully Satisfied Facilities", "value": f"{int((comp_df['OptimizedUnmetDemand'] == 0).sum())} of {len(comp_df)}", "subtext": "100% demand covered", "badge": "SATISFIED", "border_left_color": "#0F172A"}
    ])

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Facility-Wise Allocation Table
    st.subheader("1. Facility-Wise Allocation & Baseline Comparison")
    tab_summary, tab_detailed = st.tabs(["Summary View (4 Columns)", "Complete Comparison Matrix (All Metrics)"])

    with tab_summary:
        render_simple_results_table(comp_df)

    with tab_detailed:
        render_allocation_comparison_table(comp_df)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 5. Core Charts: Demand Fulfillment & Reallocation Difference
    st.subheader("2. Allocation Analysis Charts")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Chart 1: Demand Fulfillment (Allocated vs Unmet Demand)
        fig_fulfill = render_demand_fulfillment_chart(comp_df)
        fig_fulfill.update_layout(height=460)
        st.plotly_chart(fig_fulfill, use_container_width=True)

    with chart_col2:
        # Chart 2: Allocation Difference (Optimized - Baseline Shifts)
        fig_shifts = render_allocation_diff_chart(comp_df)
        fig_shifts.update_layout(height=460)
        st.plotly_chart(fig_shifts, use_container_width=True)

    # 6. Clear Operational Explanation: Historical Occupancy vs Permit Allocation
    with st.container(border=True):
        st.markdown(
            "**Operational Infrastructure Distinction:**\n"
            "- **Observed Historical Occupancy** reflects raw empirical vehicle arrivals recorded by municipal street sensors.\n"
            "- **Managed Parking Permits ($x_i$)** represent administrative quotas allocated across facilities.\n"
            "- Physical concrete parking bays are geographically static civil assets that cannot be physically moved across zones. "
            "Linear Programming reallocates administrative permit quotas away from underutilized buffers to high-demand bottleneck lots."
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 7. Five Scenario Comparison Section
    st.subheader("3. Operations Research Scenario Analysis")
    st.caption("Comparison across the 5 canonical academic policy scenarios under different demand and budget assumptions:")

    summary_df, _ = load_scenario_summaries()
    fig_scen = render_scenarios_comparison_chart(summary_df)
    st.plotly_chart(fig_scen, use_container_width=True)

    # Clean Scenario Summary Table
    scenario_display_cols = ["ScenarioName", "BudgetPermits", "TotalAllocated", "TotalUnmetDemand", "WeightedObjective", "FullySatisfiedLots", "ZeroAllocationLots"]
    scenario_view = summary_df[[c for c in scenario_display_cols if c in summary_df.columns]].copy()
    scenario_view.rename(columns={
        "ScenarioName": "Scenario",
        "BudgetPermits": "Budget (Permits)",
        "TotalAllocated": "Total Allocated",
        "TotalUnmetDemand": "Unmet Demand",
        "WeightedObjective": "Optimization Score (Z*)",
        "FullySatisfiedLots": "Fully Satisfied Lots",
        "ZeroAllocationLots": "Zero Allocation Lots"
    }, inplace=True)
    st.dataframe(scenario_view, use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 8. Primary Actions: Download CSV and Download Academic PDF Report
    st.subheader("4. Data Export & Reports")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        csv_data = comp_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Recommended Allocation (CSV)",
            data=csv_data,
            file_name="parkopt_optimized_allocation.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_dl2:
        try:
            demand_method = get_state("current_demand_method") or "p95"
            priority_scenario = get_state("current_priority_scenario") or "congestion"

            pdf_bytes = generate_academic_pdf_report(
                opt_result=opt_result,
                comp_df=comp_df,
                comp_summary=comp_summary,
                area_stats_df=area_stats,
                scenarios_summary_df=summary_df,
                current_demand_method=demand_method,
                current_priority_scenario=priority_scenario,
                current_budget=budget
            )
            st.download_button(
                label="📑 Download Academic Project Report (PDF)",
                data=pdf_bytes,
                file_name="PARKOPT_Academic_Report.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF Generation Notice: {str(e)}")

    # 9. Expandable Viva Preparation Questions
    with st.expander("📚 Academic Viva & Oral Defense Preparation Guide", expanded=False):
        st.markdown(
            """
            1. **Why Linear Programming instead of proportional allocation?**
               - *Answer:* Proportional heuristics blindly assign quotas based on lot size, stranding permits in empty lots while starving crowded hubs. LP mathematically maximizes the priority-weighted volume of satisfied demand.
            2. **What are the decision variables and constraints?**
               - *Answer:* Decision variables $x_i$ represent integer managed permit quotas. Constraints enforce the total permit budget $\sum x_i \le B$, physical capacity $x_i \le C_i$, and estimated demand $x_i \le d_i$.
            3. **What is the saturation budget ($B^*$)?**
               - *Answer:* At $B^* = 28,823$ permits (for P95 demand), every facility's demand or capacity is 100% satisfied. Increasing budget beyond $B^*$ yields a marginal return $dZ/dB = 0$.
            """
        )


if __name__ == "__main__":
    render_results_and_reports_page()
