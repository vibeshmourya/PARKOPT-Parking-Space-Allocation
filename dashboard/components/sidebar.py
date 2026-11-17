"""
sidebar.py
Standard sidebar navigation and system status header for PARKOPT.
Part of MCA ITOR Academic Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import textwrap
import streamlit as st
from dashboard.utils.state_manager import get_state


def render_sidebar() -> None:
    """
    Renders the unified sidebar with brand headers, academic metadata,
    4-step onboarding guide, and system status widgets.
    Uses dedented HTML to prevent Markdown parser code block conversion.
    """
    with st.sidebar:
        # 1. Branding Header
        st.markdown(
            textwrap.dedent("""\
            <div style="padding-bottom: 12px; border-bottom: 1px solid #E2E8F0; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.7rem;">🚗</span>
            <span style="font-size: 1.4rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">PARKOPT</span>
            </div>
            <div style="font-size: 0.82rem; font-weight: 600; color: #2563EB; margin-top: 2px;">
            Smart Parking Allocation System
            </div>
            <div style="font-size: 0.74rem; color: #64748B; margin-top: 2px;">
            Linear Programming Optimization
            </div>
            </div>"""),
            unsafe_allow_html=True
        )

        # 2. Academic Project Badges
        st.markdown(
            textwrap.dedent("""\
            <div style="margin-bottom: 14px; display: flex; gap: 6px; flex-wrap: wrap;">
            <span style="background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600;">MCA ITOR</span>
            <span style="background-color: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600;">PuLP LP</span>
            <span style="background-color: #FAF5FF; color: #7E22CE; border: 1px solid #E9D5FF; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600;">4 Zones · 193 Bays</span>
            </div>"""),
            unsafe_allow_html=True
        )

        # 3. How to use PARKOPT (4-Step Guide)
        with st.container(border=True):
            st.markdown(
                textwrap.dedent("""\
                <div style="font-size: 0.74rem; font-weight: 700; color: #0F172A; text-transform: uppercase; margin-bottom: 6px;">
                How to use PARKOPT
                </div>
                <div style="font-size: 0.78rem; color: #334155; line-height: 1.45;">
                <div style="margin-bottom: 5px;"><b>1. Dashboard:</b> Review parking capacity & demand</div>
                <div style="margin-bottom: 5px;"><b>2. Facilities:</b> Inspect individual lot occupancy</div>
                <div style="margin-bottom: 5px;"><b>3. Optimize:</b> Set permit budget & run solver</div>
                <div><b>4. Results:</b> Compare allocations & export report</div>
                </div>"""),
                unsafe_allow_html=True
            )

        # 4. System Status Widget
        opt_result = get_state("latest_opt_result")
        solver_status = opt_result.get("status", "Ready to Solve") if opt_result else "Ready to Solve"
        status_color = "#10B981" if solver_status == "Optimal" else "#2563EB"

        with st.container(border=True):
            st.markdown(
                textwrap.dedent(f"""\
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 6px;">System Status</div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                <span style="color: #475569;">Facilities:</span>
                <span style="font-weight: 600; color: #0F172A;">4 Zones</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                <span style="color: #475569;">Total Capacity:</span>
                <span style="font-weight: 600; color: #0F172A;">193 bays</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                <span style="color: #475569;">Solver State:</span>
                <span style="font-weight: 700; color: {status_color};">{solver_status}</span>
                </div>"""),
                unsafe_allow_html=True
            )

        # 5. Operations Research Modeling Rule
        st.info(
            "**Operational Principle:** Physical bays are stationary civil infrastructure. "
            "Linear Programming optimizes managed permits and admission quotas."
        )

        st.divider()

        # 6. Project Information Footer
        st.caption("MCA ITOR Academic Project · Smart Parking Management Dataset · PuLP Solver")
