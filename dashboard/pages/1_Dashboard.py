"""
1_Dashboard.py
Section 1: Main Dashboard for PARKOPT.
Provides high-level system metrics, demand distribution, hourly trends, and key insights.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import streamlit as st
from dashboard.utils.formatting import CUSTOM_DASHBOARD_CSS, format_number, format_pct
from dashboard.utils.data_service import (
    load_cleaned_dataset,
    load_facility_statistics,
    load_system_kpis
)
from dashboard.components.sidebar import render_sidebar
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.charts import (
    render_top5_demand_chart,
    render_top5_underutilized_chart,
    render_facility_hourly_chart,
    render_vehicle_type_chart,
    render_user_type_chart
)


def render_dashboard_page() -> None:
    """
    Renders Section 1: Dashboard.
    Displays the 4 primary KPIs, zone demand distribution, fleet & user mix,
    hourly demand profile, 3 short analytical insights, and the primary 'Start Optimization' action.
    """
    st.markdown(CUSTOM_DASHBOARD_CSS, unsafe_allow_html=True)
    render_sidebar()

    # 1. Header
    st.markdown(
        """<div class="hero-card">
<h1 class="hero-title">Smart Parking System Overview</h1>
<div class="hero-subtitle">PARKOPT · Smart Parking Allocation System</div>
<p class="hero-desc">Monitor smart parking capacity and demand across 4 parking zones (193 IoT sensor bays). Use Linear Programming to allocate limited permit quotas to the highest-priority facilities.</p>
</div>""",
        unsafe_allow_html=True
    )

    # 2. Load Verified System KPIs and Statistics
    with st.spinner("Loading system metrics..."):
        df_clean = load_cleaned_dataset()
        area_stats = load_facility_statistics(df_clean)
        kpis = load_system_kpis(df_clean)

    # 3. The 4 Primary KPI Cards (Native Streamlit Components)
    total_spaces = kpis.get("total_system_capacity", 193)
    peak_vehicles = kpis.get("peak_system_occupancy", 40)
    num_facilities = kpis.get("total_facilities", 4)
    peak_util_pct = kpis.get("peak_system_utilization_pct", 80.0)

    kpi_cards_data = [
        {
            "label": "Total Parking Capacity",
            "value": f"{format_number(total_spaces)} bays",
            "subtext": "193 IoT sensor bays",
            "badge": "CAPACITY",
            "border_left_color": "#2563EB"
        },
        {
            "label": "Peak Vehicles Observed",
            "value": f"{format_number(peak_vehicles)} cars",
            "subtext": "Single zone peak load",
            "badge": "DEMAND",
            "border_left_color": "#0F172A"
        },
        {
            "label": "Parking Zones",
            "value": f"{num_facilities} zones",
            "subtext": "Zones A, B, C & D",
            "badge": "NETWORK",
            "border_left_color": "#10B981"
        },
        {
            "label": "Peak System Utilization",
            "value": format_pct(peak_util_pct),
            "subtext": "Highest observed rate",
            "badge": "PEAK",
            "border_left_color": "#F59E0B"
        }
    ]
    render_kpi_row(kpi_cards_data)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Zone Demand Distribution
    st.subheader("Parking Demand & Utilization by Zone")
    col1, col2 = st.columns(2)
    with col1:
        fig_top = render_top5_demand_chart(area_stats)
        st.plotly_chart(fig_top, use_container_width=True)
    with col2:
        fig_under = render_top5_underutilized_chart(area_stats)
        st.plotly_chart(fig_under, use_container_width=True)

    # 5. Smart Parking Fleet & User Profiles
    st.subheader("Smart Parking Vehicle & User Breakdown")
    col_v, col_u = st.columns(2)
    with col_v:
        fig_v = render_vehicle_type_chart(df_clean)
        st.plotly_chart(fig_v, use_container_width=True)
    with col_u:
        fig_u = render_user_type_chart(df_clean)
        st.plotly_chart(fig_u, use_container_width=True)

    # 6. Hourly Parking Demand Trend
    st.subheader("System Hourly Demand Profile")
    fig_hourly = render_facility_hourly_chart(df_clean, facility_code=None)
    st.plotly_chart(fig_hourly, use_container_width=True)

    # 7. Three Short Analytical Insights
    with st.container(border=True):
        st.markdown("**Key Operational Findings**")
        st.markdown(
            "- **Zone Bottleneck:** Zone D records the highest average utilization at 31.3% and peak load at 80.0%, requiring priority quota protection.\n"
            "- **Fleet & User Demographics:** Registered commuters account for 73.2% of sessions, while passenger cars make up 70.4% and electric vehicles 10.5%.\n"
            "- **Stationary Civil Assets:** Concrete parking bays cannot be physically relocated; Linear Programming reallocates managed permit quotas to maximize satisfied demand."
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 8. Primary Action: Start Optimization
    col_act, _ = st.columns([1, 2])
    with col_act:
        if st.button("🚀 Start Optimization", type="primary", use_container_width=True):
            try:
                st.switch_page("dashboard/pages/3_Optimize_Allocation.py")
            except Exception:
                st.info("Navigate to **Section 3: Optimization** using the sidebar to configure and solve the model.")

    # 9. Collapsible Academic Details
    with st.expander("ℹ️ Academic Context & Methodology (MCA ITOR)", expanded=False):
        st.markdown(
            """
            - **Course:** Master of Computer Applications (MCA) — Introduction to Operations Research (ITOR)
            - **Model:** Bounded Integer Knapsack Linear Program solved with PuLP (COIN-OR CBC Solver)
            - **Objective:** $\\max \\sum w_i x_i$ subject to $\\sum x_i \\le B$, $x_i \\le \\min(C_i, d_i)$, $x_i \\in \\mathbb{Z}^+$
            - **Dataset:** Smart Parking Management Dataset (1,000 verified IoT sensor records across 4 zones and 193 bays)
            """
        )


if __name__ == "__main__":
    render_dashboard_page()
