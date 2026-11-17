"""
app.py
Main application entry point for PARKOPT – Smart Parking Allocation System.
Part of MCA ITOR Academic Project: Optimal Parking Space Allocation Using Linear Programming.

Run with:
    streamlit run dashboard/app.py
"""

import os
import sys
import tempfile
import streamlit as st

# Prevent matplotlib cache directory warnings
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")
for p in [PROJECT_ROOT, SRC_DIR, DASHBOARD_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dashboard.utils.state_manager import init_session_state
from dashboard.pages import (
    render_dashboard_page,
    render_explore_parking_page,
    render_optimize_allocation_page,
    render_results_and_reports_page
)

# 1. Global Page Configuration
st.set_page_config(
    page_title="PARKOPT — Smart Parking Allocation System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Initialize Session State
init_session_state()

# 3. Configure Clean 4-Section Multi-Page Navigation
page_dashboard = st.Page(
    render_dashboard_page,
    title="1. Dashboard",
    icon="📊",
    default=True
)
page_facilities = st.Page(
    render_explore_parking_page,
    title="2. Parking Facilities",
    icon="🚗"
)
page_optimize = st.Page(
    render_optimize_allocation_page,
    title="3. Optimization",
    icon="⚡"
)
page_results = st.Page(
    render_results_and_reports_page,
    title="4. Results",
    icon="📈"
)

nav = st.navigation(
    [page_dashboard, page_facilities, page_optimize, page_results]
)

# 4. Run Active Page
nav.run()
