"""
test_html_rendering.py
Unit tests verifying that all HTML and UI rendering helpers in PARKOPT:
1. Never produce 4 leading spaces (indented code block bug).
2. Never leak raw HTML code as text.
3. Properly close all tags.
4. Correctly clamp and format percentages and status badges.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")

for p in [PROJECT_ROOT, SRC_DIR, DASHBOARD_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dashboard.components.kpi_cards import render_kpi_card
from dashboard.utils.formatting import (
    format_number, format_pct, format_status_badge, format_utilization_bar, CUSTOM_DASHBOARD_CSS
)


class TestHTMLRenderingIntegrity(unittest.TestCase):
    """Verifies that no HTML rendering bugs or code-block indentation exist."""

    def test_kpi_card_has_no_code_block_indentation(self):
        """Markdown treats lines with >= 4 leading spaces as code blocks. Verify zero lines have 4 spaces."""
        card_html = render_kpi_card(
            label="Total Capacity",
            value="39,956 bays",
            subtext="Stationary civil infrastructure",
            delta="+5.31%",
            delta_positive=True,
            badge="VERIFIED",
            border_left_color="#2563EB"
        )
        self.assertIsInstance(card_html, str)
        self.assertTrue(len(card_html) > 0)
        
        # Verify that the opening line starts with <div, not 4 spaces
        self.assertTrue(card_html.startswith("<div"), f"HTML should start with '<div', got: {card_html[:20]!r}")
        
        # Check that no line in the generated HTML begins with 4 or more leading spaces
        for line in card_html.split("\n"):
            if line.strip():
                self.assertFalse(line.startswith("    "), f"Line starts with 4 spaces (code block risk): {line!r}")

    def test_kpi_card_contains_all_content_fields(self):
        """Verifies that all text fields and style rules are injected cleanly."""
        card_html = render_kpi_card(
            label="Peak Vehicles",
            value="20,447 cars",
            subtext="Observed rush hour",
            delta="-12%",
            delta_positive=False,
            badge="PEAK",
            border_left_color="#0F172A"
        )
        self.assertIn("Peak Vehicles", card_html)
        self.assertIn("20,447 cars", card_html)
        self.assertIn("Observed rush hour", card_html)
        self.assertIn("PEAK", card_html)
        self.assertIn("▼ -12%", card_html)
        self.assertIn("#DC2626", card_html) # Red for negative delta
        self.assertIn("#0F172A", card_html) # Border color

    def test_format_status_badge_tag_closure(self):
        """Verifies that status badge produces well-formed closed HTML tags."""
        statuses = ["Optimal", "Infeasible", "Moderate", "Binding", "Low", "Feasible"]
        for s in statuses:
            badge = format_status_badge(s)
            self.assertTrue(badge.startswith("<span"), f"Badge should start with '<span': {badge}")
            self.assertTrue(badge.endswith("</span>"), f"Badge should end with '</span>': {badge}")
            self.assertIn(s, badge)

    def test_format_utilization_bar_clamping(self):
        """Verifies that progress bars clamp cleanly between 0% and 100%."""
        bar_neg = format_utilization_bar(-15.0)
        self.assertIn("0.0%", bar_neg)
        self.assertIn("width: 0.0%", bar_neg)

        bar_over = format_utilization_bar(125.0)
        self.assertIn("100.0%", bar_over)
        self.assertIn("width: 100.0%", bar_over)

        bar_normal = format_utilization_bar(68.5)
        self.assertIn("68.5%", bar_normal)
        self.assertIn("#EF4444", bar_normal) # High threshold color

    def test_css_prevents_horizontal_overflow(self):
        """Verifies that CSS enforces overflow-x hidden to prevent horizontal scrolling."""
        self.assertIn("overflow-x: hidden", CUSTOM_DASHBOARD_CSS)
        self.assertIn("max-width: 100%", CUSTOM_DASHBOARD_CSS)


if __name__ == "__main__":
    unittest.main()

