"""
3_Optimize_Allocation.py
Section 3: Optimization Configuration & Solver Execution for PARKOPT.
Allows users to configure permit budget, demand estimator, and priority strategies,
then executes the PuLP Integer Linear Programming solver and stores verified results.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import streamlit as st
import pandas as pd
from dashboard.utils.formatting import CUSTOM_DASHBOARD_CSS, format_number, format_pct
from dashboard.utils.state_manager import get_state, set_state
from dashboard.utils.data_service import (
    load_cleaned_dataset,
    load_demand_estimates
)
from dashboard.utils.optimization_service import (
    run_solver_workflow,
    compute_facility_weights_preview
)
from dashboard.components.sidebar import render_sidebar
from dashboard.components.kpi_cards import render_kpi_row


def render_optimize_allocation_page() -> None:
    """
    Renders Section 3: Optimization.
    Provides controls for Budget, Demand Estimator, and Priority Strategy,
    validates inputs, solves the PuLP LP model, displays result KPIs, and directs to Section 4.
    """
    st.markdown(CUSTOM_DASHBOARD_CSS, unsafe_allow_html=True)
    render_sidebar()

    # 1. Header
    st.markdown(
        """<div class="hero-card">
<h1 class="hero-title">Optimize Parking Allocation</h1>
<div class="hero-subtitle">Linear Programming Permit Quota Allocation</div>
<p class="hero-desc">Configure your available permit quota, demand estimation method, and priority strategy. The PuLP solver determines the unique global optimum that maximizes served priority demand across all 4 parking zones (193 physical bays).</p>
</div>""",
        unsafe_allow_html=True
    )

    df_clean = load_cleaned_dataset()

    # 2. Controls Section
    st.subheader("1. Allocation Parameters")

    # Budget preset state handling
    if "opt_budget_val" not in st.session_state:
        st.session_state["opt_budget_val"] = get_state("current_budget") or 87

    col_presets, _ = st.columns([2, 1])
    with col_presets:
        st.markdown("<span style='font-size: 0.82rem; font-weight: 600; color: #475569;'>Quick Budget Presets:</span>", unsafe_allow_html=True)
        btn1, btn2, btn3 = st.columns(3)
        with btn1:
            if st.button("Low (60 permits)", use_container_width=True):
                st.session_state["opt_budget_val"] = 60
        with btn2:
            if st.button("Medium (87 permits)", use_container_width=True):
                st.session_state["opt_budget_val"] = 87
        with btn3:
            if st.button("High (116 permits)", use_container_width=True):
                st.session_state["opt_budget_val"] = 116

    col_in1, col_in2, col_in3 = st.columns(3)

    with col_in1:
        st.markdown("<b>Available Parking Permits</b>", unsafe_allow_html=True)
        budget = st.slider(
            "Permit Budget Limit:",
            min_value=10,
            max_value=193,
            value=int(st.session_state["opt_budget_val"]),
            step=1,
            help="Total managed parking permits or reserved admission slots available to allocate across all 4 zones.",
            label_visibility="collapsed"
        )
        st.caption(f"Selected Budget: **{format_number(budget)} permits** (Capacity: 193 bays)")

    with col_in2:
        st.markdown("<b>Demand Estimation Method</b>", unsafe_allow_html=True)
        demand_choice = st.selectbox(
            "Select Demand Method:",
            options=[
                "95th Percentile (P95) [Recommended]",
                "85th Percentile (P85)",
                "Historical Mean (Average Occupancy)",
                "Maximum Observed Occupancy (Peak)"
            ],
            index=0,
            label_visibility="collapsed",
            help="Statistical model representing estimated vehicle demand per parking area."
        )
        method_map = {
            "95th Percentile (P95) [Recommended]": "p95",
            "85th Percentile (P85)": "p85",
            "Historical Mean (Average Occupancy)": "mean",
            "Maximum Observed Occupancy (Peak)": "max"
        }
        demand_method = method_map[demand_choice]

    with col_in3:
        st.markdown("<b>Allocation Priority Strategy</b>", unsafe_allow_html=True)
        priority_choice = st.selectbox(
            "Select Priority Strategy:",
            options=[
                "Congestion Priority [Recommended]",
                "Equal Priority (Equal weights)",
                "Custom Weights (Policy-driven)"
            ],
            index=0,
            label_visibility="collapsed",
            help="Mathematical weighting scheme w_i in the objective function."
        )
        priority_map = {
            "Congestion Priority [Recommended]": "congestion",
            "Equal Priority (Equal weights)": "equal",
            "Custom Weights (Policy-driven)": "custom"
        }
        priority_scenario = priority_map[priority_choice]

    # Priority Strategy Explanation Pill
    explanation_map = {
        "congestion": "<b>Congestion Priority:</b> Weights scale dynamically between 1.0 and 3.0 based on historical occupancy pressure (w_i = 1.0 + 2.0 · util_i / max_util). Higher pressure zones are protected.",
        "equal": "<b>Equal Priority:</b> All facilities receive an identical weight of 1.0. Maximizes the raw volume of served parking permits.",
        "custom": "<b>Custom Strategy:</b> Pre-configured policy weights reflecting municipal smart parking priorities: Zone A (2.5), Zone B (2.2), Zone C (1.8), Zone D (1.4)."
    }
    with st.container(border=True):
        st.markdown(explanation_map[priority_scenario], unsafe_allow_html=True)

    # 3. Solver Execution Action Button
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    col_btn, _ = st.columns([1, 2])
    with col_btn:
        solve_clicked = st.button("⚡ Run PuLP LP Solver", type="primary", use_container_width=True)

    if solve_clicked:
        with st.spinner("Formulating and solving Linear Program with PuLP..."):
            opt_result, comp_df, comp_summary = run_solver_workflow(
                df_clean=df_clean,
                budget=budget,
                demand_method=demand_method,
                priority_scenario=priority_scenario
            )

        # Update Session State
        set_state("latest_opt_result", opt_result)
        set_state("comparison_df", comp_df)
        set_state("comparison_summary", comp_summary)
        set_state("current_budget", budget)
        set_state("current_demand_method", demand_method)
        set_state("current_priority_scenario", priority_scenario)

    # 4. Display Results if an optimization run is cached
    opt_result = get_state("latest_opt_result")
    comp_summary = get_state("comparison_summary")

    if opt_result and comp_summary:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.subheader("2. Solver Execution Results")

        status_str = opt_result.get("solver_status", "Optimal")
        total_alloc = comp_summary.get("optimized_total_allocated", budget)
        unmet_demand = comp_summary.get("optimized_unmet_demand", 0)
        obj_value = comp_summary.get("optimized_objective", 0.0)
        remaining_budget = max(0, budget - total_alloc)

        # Clean native KPI metric row
        result_kpis = [
            {"label": "Solver Status", "value": status_str, "subtext": "PuLP CBC Global Optimum", "badge": "STATUS", "border_left_color": "#10B981"},
            {"label": "Total Allocated Permits", "value": f"{format_number(total_alloc)}", "subtext": f"Budget: {format_number(budget)}", "badge": "ALLOCATED", "border_left_color": "#2563EB"},
            {"label": "Remaining Budget", "value": f"{format_number(remaining_budget)}", "subtext": "Unused permit capacity", "badge": "SURPLUS", "border_left_color": "#64748B"},
            {"label": "Estimated Unmet Demand", "value": f"{format_number(unmet_demand)}", "subtext": "Unserved demand", "badge": "UNMET", "border_left_color": "#EF4444" if unmet_demand > 0 else "#10B981"},
            {"label": "Optimization Score (Z*)", "value": f"{format_number(obj_value, decimals=1)}", "subtext": "Weighted objective", "badge": "OBJECTIVE", "border_left_color": "#7E22CE"}
        ]
        render_kpi_row(result_kpis)

        # Concise Result Summary Card
        with st.container(border=True):
            st.markdown(
                f"**Optimization Execution Summary:** The solver allocated **{format_number(total_alloc)} permits** across the 4 parking zones (193 bays), "
                f"achieving an optimization priority score of **{format_number(obj_value, decimals=1)}**. "
                f"Remaining unserved demand is **{format_number(unmet_demand)} permits**, concentrated at physical bottlenecks."
            )

        col_next, _ = st.columns([1, 2])
        with col_next:
            if st.button("📊 View Detailed Results & Reports →", type="primary", use_container_width=True):
                try:
                    st.switch_page("dashboard/pages/4_Results_and_Reports.py")
                except Exception:
                    st.info("Navigate to **Section 4: Results & Reports** from the sidebar to inspect facility allocations.")

    # 5. Expandable Mathematical Explanation Section
    with st.expander("📐 Mathematical Model & Linear Programming Formulation", expanded=False):
        st.markdown(
            r"""
            ### Integer Linear Programming (ILP) Formulation

            **Decision Variables:**
            $$x_i \in \mathbb{Z}^+ \quad \forall i \in \{1, 2, 3, 4\} \quad (\text{Zone A, Zone B, Zone C, Zone D})$$
            *Integer number of managed parking permits or admission quotas allocated to zone $i$.*

            **Objective Function:**
            $$\text{Maximize } Z = \sum_{i=1}^{4} w_i x_i$$
            *Maximizes total priority-weighted permit allocation across all smart parking zones.*

            **Subject to Constraints:**
            1. **Total Available Permit Budget:**
               $$\sum_{i=1}^{4} x_i \le B$$
            2. **Physical Civil Capacity Bound:**
               $$x_i \le C_i \quad \forall i \in \{1, \dots, 4\} \quad (C_A=50, C_B=50, C_C=49, C_D=44)$$
            3. **Estimated Demand Ceiling:**
               $$x_i \le d_i \quad \forall i \in \{1, \dots, 4\}$$
            4. **Non-negativity and Integrality:**
               $$x_i \ge 0, \quad x_i \in \mathbb{Z} \quad \forall i \in \{1, \dots, 4\}$$
            """
        )


if __name__ == "__main__":
    render_optimize_allocation_page()
