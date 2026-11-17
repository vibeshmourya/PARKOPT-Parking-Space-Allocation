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
    render_facility_hourly_chart
)


def render_dashboard_page() -> None:
    """
    Renders Section 1: Dashboard.
    Displays the 4 primary KPIs, top 5 high-demand facilities, top 5 underutilized facilities,
    hourly demand trend, 3 short analytical insights, and the primary 'Start Optimization' action.
    """
    st.markdown(CUSTOM_DASHBOARD_CSS, unsafe_allow_html=True)
    render_sidebar()

    # 1. Header
    st.markdown(
        """<div class="hero-card">
<h1 class="hero-title">Parking System Overview</h1>
<div class="hero-subtitle">PARKOPT · Smart Parking Allocation System</div>
<p class="hero-desc">Monitor municipal parking capacity and demand across 30 Birmingham facilities. Use Linear Programming to allocate limited permit quotas to the highest-priority facilities.</p>
</div>""",
        unsafe_allow_html=True
    )

    # 2. Load Verified System KPIs and Statistics
    with st.spinner("Loading system metrics..."):
        df_clean = load_cleaned_dataset()
        area_stats = load_facility_statistics(df_clean)
        kpis = load_system_kpis(df_clean)

    # 3. The 4 Primary KPI Cards (Native Streamlit Components)
    total_spaces = kpis.get("total_system_capacity", 39956)
    peak_vehicles = kpis.get("peak_system_occupancy", 20447)
    num_facilities = kpis.get("total_facilities", 30)
    peak_util_pct = kpis.get("peak_system_utilization_pct", 51.17)

    kpi_cards_data = [
        {
            "label": "Total Parking Capacity",
            "value": f"{format_number(total_spaces)} bays",
            "subtext": "Stationary civil infrastructure",
            "badge": "CAPACITY",
            "border_left_color": "#2563EB"
        },
        {
            "label": "Peak Vehicles Observed",
            "value": f"{format_number(peak_vehicles)} cars",
            "subtext": "System-wide peak demand",
            "badge": "DEMAND",
            "border_left_color": "#0F172A"
        },
        {
            "label": "Parking Facilities",
            "value": f"{num_facilities} lots",
            "subtext": "Monitored Birmingham sites",
            "badge": "NETWORK",
            "border_left_color": "#10B981"
        },
        {
            "label": "Peak System Utilization",
            "value": format_pct(peak_util_pct),
            "subtext": "City-wide aggregated peak",
            "badge": "PEAK",
            "border_left_color": "#F59E0B"
        }
    ]
    render_kpi_row(kpi_cards_data)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Top 5 High-Demand & Top 5 Underutilized Facilities
    st.subheader("Parking Demand Distribution")
    col1, col2 = st.columns(2)
    with col1:
        fig_top5 = render_top5_demand_chart(area_stats)
        st.plotly_chart(fig_top5, use_container_width=True)
    with col2:
        fig_under = render_top5_underutilized_chart(area_stats)
        st.plotly_chart(fig_under, use_container_width=True)

    # 5. Hourly Parking Demand Trend
    st.subheader("System Hourly Demand Profile")
    fig_hourly = render_facility_hourly_chart(df_clean, facility_code=None)
    st.plotly_chart(fig_hourly, use_container_width=True)

    # 6. Three Short Analytical Insights
    with st.container(border=True):
        st.markdown("**Key Operational Findings**")
        st.markdown(
            "- **Severe Demand Imbalance:** Commercial center facilities frequently exceed 75% occupancy, while peripheral facilities sit below 35% utilization.\n"
            "- **Midday Peak Bottleneck:** Traffic concentrates sharply between 11:00 and 14:00 (peak 20,447 vehicles), creating severe localized shortages.\n"
            "- **Fixed Civil Capacity:** Physical concrete bays cannot be moved; Linear Programming reallocates managed permit quotas to maximize served demand."
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 7. Primary Action: Start Optimization
    col_act, _ = st.columns([1, 2])
    with col_act:
        if st.button("🚀 Start Optimization", type="primary", use_container_width=True):
            try:
                st.switch_page("dashboard/pages/3_Optimize_Allocation.py")
            except Exception:
                st.info("Navigate to **Section 3: Optimization** using the sidebar to configure and solve the model.")

    # 8. Collapsible Academic Details
    with st.expander("ℹ️ Academic Context & Methodology (MCA ITOR)", expanded=False):
        st.markdown(
            """
            - **Course:** Master of Computer Applications (MCA) — Introduction to Operations Research (ITOR)
            - **Model:** Bounded Integer Knapsack Linear Program solved with PuLP (COIN-OR CBC Solver)
            - **Objective:** $\\max \\sum w_i x_i$ subject to $\\sum x_i \\le B$, $x_i \\le \\min(C_i, d_i)$, $x_i \\in \\mathbb{Z}^+$
            - **Dataset:** Birmingham City Council Parking Dataset (35,501 verified records across 30 municipal lots)
            """
        )


if __name__ == "__main__":
    render_dashboard_page()
