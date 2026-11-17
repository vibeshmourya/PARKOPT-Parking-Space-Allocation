"""
kpi_cards.py
Responsive, styled KPI metric card components for PARKOPT Streamlit application.
Provides native Streamlit metrics and clean, dedented HTML fallbacks.
"""

import textwrap
from typing import List, Dict, Any, Optional
import streamlit as st
from dashboard.utils.formatting import format_number, format_pct


def render_kpi_card(
    label: str,
    value: Any,
    subtext: Optional[str] = None,
    delta: Optional[str] = None,
    delta_positive: bool = True,
    badge: Optional[str] = None,
    border_left_color: str = "#2563EB"
) -> str:
    """
    Generates clean, dedented HTML string for a single professional KPI card.
    Guaranteed zero leading whitespace to prevent Markdown from interpreting as code blocks.
    """
    delta_html = ""
    if delta:
        delta_color = "#059669" if delta_positive else "#DC2626"
        arrow = "▲" if delta_positive else "▼"
        delta_html = f'<div style="font-size: 0.8rem; font-weight: 700; color: {delta_color}; margin-top: 4px;">{arrow} {delta}</div>'

    badge_html = ""
    if badge:
        badge_html = (
            f'<span style="background-color: #F1F5F9; color: #475569; font-size: 0.7rem; '
            f'font-weight: 700; padding: 2px 7px; border-radius: 9999px; float: right;">{badge}</span>'
        )

    subtext_html = ""
    if subtext:
        subtext_html = f'<div class="kpi-subtext" style="font-size: 0.78rem; color: #64748B; margin-top: 4px;">{subtext}</div>'

    html = textwrap.dedent(f"""\
<div class="kpi-container" style="border-left: 4px solid {border_left_color}; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 16px;">
<div style="display: flex; justify-content: space-between; align-items: flex-start;">
<div class="kpi-label" style="font-size: 0.76rem; font-weight: 600; text-transform: uppercase; color: #64748B;">{label}</div>
{badge_html}
</div>
<div class="kpi-value" style="font-size: 1.55rem; font-weight: 800; color: #0F172A; line-height: 1.2; margin-top: 2px;">{value}</div>
{delta_html}
{subtext_html}
</div>""").strip()

    return html


def render_kpi_row(cards: List[Dict[str, Any]]) -> None:
    """
    Renders a row of KPI cards using Streamlit native components across equal columns.
    Eliminates all raw HTML leakage and markdown parsing errors.
    """
    if not cards:
        return

    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            label = card.get("label", "Metric")
            val = str(card.get("value", "0"))
            delta = card.get("delta")
            delta_pos = card.get("delta_positive", True)
            subtext = card.get("subtext")
            badge = card.get("badge")

            # Clean native card with container border
            with st.container(border=True):
                display_label = f"{label} · {badge}" if badge else label
                delta_color = "normal" if delta_pos else "inverse"
                st.metric(
                    label=display_label,
                    value=val,
                    delta=delta,
                    delta_color=delta_color,
                    help=subtext
                )
                if subtext:
                    st.caption(subtext)
