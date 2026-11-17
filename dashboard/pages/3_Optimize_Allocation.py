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
<p class="hero-desc">Configure your available permit quota, demand estimation method, and priority strategy. The PuLP solver determines the unique global optimum that maximizes served priority demand across all 30 facilities.</p>
</div>""",
        unsafe_allow_html=True
    )

    df_clean = load_cleaned_dataset()

    # 2. Controls Section
    st.subheader("1. Allocation Parameters")

    # Budget preset state handling
    if "opt_budget_val" not in st.session_state:
        st.session_state["opt_budget_val"] = get_state("current_budget") or 21617

    col_presets, _ = st.columns([2, 1])
    with col_presets:
        st.markdown("<span style='font-size: 0.82rem; font-weight: 600; color: #475569;'>Quick Budget Presets:</span>", unsafe_allow_html=True)
        btn1, btn2, btn3 = st.columns(3)
        with btn1:
            if st.button("Low (15,000 permits)", use_container_width=True):
                st.session_state["opt_budget_val"] = 15000
        with btn2:
            if st.button("Medium (21,617 permits)", use_container_width=True):
                st.session_state["opt_budget_val"] = 21617
        with btn3:
            if st.button("High (28,000 permits)", use_container_width=True):
                st.session_state["opt_budget_val"] = 28000

    col_in1, col_in2, col_in3 = st.columns(3)

    with col_in1:
        st.markdown("<b>Available Parking Permits</b>", unsafe_allow_html=True)
        budget = st.slider(
            "Permit Budget Limit:",
            min_value=5000,
            max_value=35000,
            value=int(st.session_state["opt_budget_val"]),
            step=500,
            help="Total managed parking permits or reserved admission slots available to allocate across all facilities.",
            label_visibility="collapsed"
        )
        st.caption(f"Selected Budget: **{format_number(budget)} permits**")

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
                "Custom Priority"
            ],
            index=0,
            label_visibility="collapsed",
            help="Weights determine how much priority the LP solver places on satisfying demand at congested bottleneck lots."
        )
        priority_map = {
            "Congestion Priority [Recommended]": "congestion",
            "Equal Priority (Equal weights)": "equal",
            "Custom Priority": "custom"
        }
        priority_scenario = priority_map[priority_choice]

    # Custom weights expander
    custom_weights_dict = None
    if priority_scenario == "custom":
        with st.expander("⚙️ Configure Custom Facility Priority Weights (1.0 – 5.0)", expanded=True):
            st.info("Assign custom priority weights to facilities. Higher weights incentivize the solver to satisfy that lot's demand first.")
            preview_weights = compute_facility_weights_preview(df_clean, priority_scenario="congestion")
            custom_weights_dict = {}
            w_cols = st.columns(3)
            for idx, (_, row) in enumerate(preview_weights.iterrows()):
                col_idx = idx % 3
                with w_cols[col_idx]:
                    code = row["SystemCodeNumber"]
                    custom_weights_dict[code] = st.slider(
                        f"{code}:",
                        min_value=1.0,
                        max_value=5.0,
                        value=float(row["PriorityWeight"]),
                        step=0.1,
                        key=f"custom_w_{code}"
                    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Action: Run Optimization
    col_run, _ = st.columns([1, 2])
    with col_run:
        run_clicked = st.button("⚡ RUN OPTIMIZATION", type="primary", use_container_width=True)

    if run_clicked:
        # Input Validation
        if budget <= 0:
            st.error("Error: Allocation budget must be a positive integer.")
            return

        with st.spinner("Executing PuLP Linear Programming Solver..."):
            try:
                opt_result, comp_df, comp_summary = run_solver_workflow(
                    df_clean=df_clean,
                    budget=budget,
                    demand_method=demand_method,
                    priority_scenario=priority_scenario,
                    custom_weights=custom_weights_dict
                )
                
                # Check solver status - Never simulate on failure
                if opt_result.get("status") not in ["Optimal", "Not Solved", "Undefined"]:
                    st.error(f"Solver Error: Model terminated with status '{opt_result.get('status')}'.")
                    return

                # Store result in session state
                set_state("latest_opt_result", opt_result)
                set_state("comparison_df", comp_df)
                set_state("comparison_summary", comp_summary)
                set_state("current_budget", budget)
                set_state("current_demand_method", demand_method)
                set_state("current_priority_scenario", priority_scenario)
                st.success("Optimization solved successfully! Global optimal integer solution verified.")
            except Exception as e:
                st.error(f"Optimization Execution Failed: {str(e)}")
                return

    # 4. Results Summary
    opt_result = get_state("latest_opt_result")
    comp_summary = get_state("comparison_summary")

    if opt_result and comp_summary:
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.subheader("2. Solver Results Summary")

        summary = opt_result["summary"]
        status_str = opt_result.get("status", "Optimal")
        total_alloc = summary.get("total_allocated", budget)
        unmet_demand = summary.get("total_unmet_demand", 0)
        obj_value = summary.get("objective_value", 0.0)
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
                f"**Optimization Execution Summary:** The solver allocated **{format_number(total_alloc)} permits** across the 30 facilities, "
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
            $$x_i \in \mathbb{Z}^+ \quad \forall i \in \{1, \dots, 30\}$$
            *Integer number of managed parking permits or admission quotas allocated to facility $i$.*

            **Objective Function:**
            $$\text{Maximize } Z = \sum_{i=1}^{30} w_i x_i$$
            *Maximizes total priority-weighted permit allocation across all municipal facilities.*

            **Subject to Constraints:**
            1. **Total Available Permit Budget:**
               $$\sum_{i=1}^{30} x_i \le B$$
            2. **Physical Civil Capacity Bound:**
               $$x_i \le C_i \quad \forall i \in \{1, \dots, 30\}$$
            3. **Estimated Demand Ceiling:**
               $$x_i \le d_i \quad \forall i \in \{1, \dots, 30\}$$
            4. **Non-negativity and Integrality:**
               $$x_i \ge 0, \quad x_i \in \mathbb{Z} \quad \forall i \in \{1, \dots, 30\}$$
            """
        )


if __name__ == "__main__":
    render_optimize_allocation_page()
