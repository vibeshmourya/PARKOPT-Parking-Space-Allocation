"""
formatting.py
Data and UI formatting utilities for the PARKOPT Streamlit application.
Provides consistent number, percentage, badge, and responsive light theme styling.
"""

from typing import Union, Optional


def format_number(val: Union[int, float, None], decimals: int = 0) -> str:
    """Formats numeric values with thousands separators."""
    if val is None or (isinstance(val, float) and (val != val)): # NaN check
        return "N/A"
    if decimals == 0:
        return f"{int(round(val)):,}"
    return f"{float(val):,.{decimals}f}"


def format_pct(val: Union[int, float, None], decimals: int = 1) -> str:
    """Formats percentages with a trailing '%' symbol."""
    if val is None or (isinstance(val, float) and (val != val)):
        return "N/A"
    return f"{float(val):.{decimals}f}%"


def format_status_badge(status: str) -> str:
    """
    Returns an HTML styled pill badge for statuses like Optimal, Feasible,
    Binding, Slack, High, Moderate, Low.
    """
    status_lower = str(status).strip().lower()
    
    if any(k in status_lower for k in ["optimal", "fully satisfied", "low"]):
        bg_color = "#ECFDF5" # Emerald light
        text_color = "#047857"
        border_color = "#A7F3D0"
    elif any(k in status_lower for k in ["moderate", "partially satisfied", "warning"]):
        bg_color = "#FFFBEB" # Amber light
        text_color = "#B45309"
        border_color = "#FDE68A"
    elif any(k in status_lower for k in ["infeasible", "overflow", "high", "zero allocation", "danger"]):
        bg_color = "#FEF2F2" # Crimson light
        text_color = "#B91C1C"
        border_color = "#FECACA"
    elif any(k in status_lower for k in ["binding", "active"]):
        bg_color = "#EFF6FF" # Blue light
        text_color = "#1D4ED8"
        border_color = "#BFDBFE"
    else:
        bg_color = "#F1F5F9" # Slate light
        text_color = "#475569"
        border_color = "#CBD5E1"

    return (
        f'<span style="'
        f'background-color: {bg_color}; '
        f'color: {text_color}; '
        f'border: 1px solid {border_color}; '
        f'padding: 3px 8px; '
        f'border-radius: 9999px; '
        f'font-size: 0.75rem; '
        f'font-weight: 600; '
        f'display: inline-block;'
        f'">{status}</span>'
    )


def format_utilization_bar(pct: float, width_px: int = 90) -> str:
    """
    Renders a compact HTML horizontal progress bar representing utilization percentage.
    """
    pct_clamped = max(0.0, min(100.0, float(pct)))
    
    if pct_clamped >= 65.0:
        bar_color = "#EF4444" # High / Bottleneck
    elif pct_clamped >= 40.0:
        bar_color = "#F59E0B" # Moderate
    else:
        bar_color = "#2563EB" # Low / Underutilized

    return (
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<div style="background-color: #E2E8F0; border-radius: 4px; width: {width_px}px; height: 8px; overflow: hidden;">'
        f'<div style="background-color: {bar_color}; width: {pct_clamped}%; height: 100%;"></div>'
        f'</div>'
        f'<span style="font-size: 0.8rem; font-weight: 600; color: #1E293B;">{pct_clamped:.1f}%</span>'
        f'</div>'
    )


# CSS Injection for Clean Modern Light Responsive Streamlit Theme
CUSTOM_DASHBOARD_CSS = """
<style>
/* Prevent horizontal window scrolling across resolutions */
html, body, [data-testid="stAppViewContainer"] {
    overflow-x: hidden !important;
}

/* Responsive Main Page Container */
.main .block-container {
    padding-top: 1.4rem;
    padding-bottom: 2.5rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    max-width: 100%;
}

/* Header & Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #0F172A;
    font-weight: 700;
    letter-spacing: -0.015em;
}

/* Modern Clean Hero Banner */
.hero-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #2563EB;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 18px;
}

.hero-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #0F172A;
    margin: 0;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    font-size: 0.92rem;
    color: #2563EB;
    font-weight: 600;
    margin-top: 2px;
    margin-bottom: 6px;
}

.hero-desc {
    font-size: 0.88rem;
    color: #475569;
    line-height: 1.45;
    margin-bottom: 0;
}

/* Metric / KPI Cards */
.kpi-container {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    height: 100%;
}

.kpi-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

.kpi-label {
    font-size: 0.76rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #64748B;
    margin-bottom: 4px;
}

.kpi-value {
    font-size: 1.55rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.2;
}

.kpi-subtext {
    font-size: 0.78rem;
    font-weight: 500;
    color: #64748B;
    margin-top: 4px;
}

/* Academic Badges */
.academic-badge {
    display: inline-flex;
    align-items: center;
    background-color: #F8FAFC;
    color: #334155;
    border: 1px solid #CBD5E1;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
    margin-top: 6px;
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #F8FAFC;
    border-right: 1px solid #E2E8F0;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.2rem;
    padding-left: 1.0rem;
    padding-right: 1.0rem;
}

/* Callouts */
.callout-info {
    background-color: #F0F7FF;
    border-left: 4px solid #2563EB;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 14px;
    font-size: 0.85rem;
    color: #1E3A8A;
}

.callout-success {
    background-color: #F0FDF4;
    border-left: 4px solid #10B981;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 14px;
    font-size: 0.88rem;
    color: #065F46;
}

/* Clean Accent Section Box */
.section-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 18px;
}
</style>
"""
