"""
state_manager.py
Session state management for PARKOPT Streamlit application.
Ensures seamless state persistence across multi-page navigation and user interactions.
"""

from typing import Any, Optional
import streamlit as st
import pandas as pd


# Default optimization parameters
DEFAULT_BUDGET = 21617 # 75% of total P95 demand (28,788)
DEFAULT_DEMAND_METHOD = "p95"
DEFAULT_PRIORITY_SCENARIO = "congestion"


def init_session_state() -> None:
    """
    Initializes default keys in st.session_state if not already present.
    Ensures safe access across all dashboard pages.
    """
    defaults = {
        "is_state_initialized": True,
        "active_page": "Overview",
        "df_clean": None,
        "area_stats": None,
        "demand_estimates": None,
        "hourly_trends": None,
        "day_trends": None,
        "latest_opt_result": None,
        "baseline_comp_df": None,
        "comp_summary": None,
        "scenarios_df": None,
        "sensitivity_df": None,
        "current_budget": DEFAULT_BUDGET,
        "current_demand_method": DEFAULT_DEMAND_METHOD,
        "current_priority_scenario": DEFAULT_PRIORITY_SCENARIO,
        "custom_weights": None,
        "selected_facility": "All Facilities",
        "pdf_bytes": None,
        "last_solved_timestamp": None,
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_state(key: str, default: Any = None) -> Any:
    """Retrieves a value from st.session_state safely."""
    init_session_state()
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Sets a value in st.session_state."""
    init_session_state()
    st.session_state[key] = value


def reset_optimization_state() -> None:
    """Clears solved optimization state to force re-computation if parameters change."""
    init_session_state()
    st.session_state["latest_opt_result"] = None
    st.session_state["baseline_comp_df"] = None
    st.session_state["comp_summary"] = None
    st.session_state["pdf_bytes"] = None
    st.session_state["last_solved_timestamp"] = None

