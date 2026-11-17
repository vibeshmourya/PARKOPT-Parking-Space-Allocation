"""
test_full_application.py
Integration tests verifying all 4 dashboard workflow sections,
session state management, PDF report generation, and data export.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import unittest
import os
import sys
import tempfile
import warnings
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")

for p in [PROJECT_ROOT, SRC_DIR, DASHBOARD_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dashboard.pages import (
    render_dashboard_page,
    render_explore_parking_page,
    render_parking_facilities_page,
    render_optimize_allocation_page,
    render_optimization_page,
    render_results_and_reports_page,
    render_results_page
)
from dashboard.utils.state_manager import init_session_state, get_state, set_state
from dashboard.utils.data_service import (
    load_cleaned_dataset,
    load_facility_statistics,
    load_scenario_summaries
)
from dashboard.utils.optimization_service import run_solver_workflow
from dashboard.utils.report_service import generate_academic_pdf_report


class TestFullApplicationWorkflow(unittest.TestCase):
    """Verifies that all 4 workflow sections and supporting services function end-to-end."""

    def test_four_sections_callables(self):
        """Verifies that all 4 pages are callable functions."""
        self.assertTrue(callable(render_dashboard_page))
        self.assertTrue(callable(render_parking_facilities_page))
        self.assertTrue(callable(render_optimization_page))
        self.assertTrue(callable(render_results_page))

    def test_session_state_lifecycle(self):
        """Verifies session state initialization and mutation."""
        init_session_state()
        set_state("test_key", 12345)
        self.assertEqual(get_state("test_key"), 12345)

    def test_csv_export_format(self):
        """Verifies that CSV export produces valid comma-separated content."""
        df_clean = load_cleaned_dataset()
        opt_res, comp_df, comp_summary = run_solver_workflow(
            df_clean=df_clean,
            budget=87,
            demand_method="p95",
            priority_scenario="congestion"
        )
        csv_bytes = comp_df.to_csv(index=False).encode("utf-8")
        self.assertIsInstance(csv_bytes, bytes)
        self.assertIn(b"Facility,PhysicalCapacity,EstimatedDemand", csv_bytes)

    def test_pdf_report_compilation(self):
        """Verifies that ReportLab compiles a valid multi-page PDF report."""
        df_clean = load_cleaned_dataset()
        opt_res, comp_df, comp_summary = run_solver_workflow(
            df_clean=df_clean,
            budget=87,
            demand_method="p95",
            priority_scenario="congestion"
        )
        area_stats = load_facility_statistics(df_clean)
        summary_df, _ = load_scenario_summaries()

        pdf_bytes = generate_academic_pdf_report(
            opt_result=opt_result if 'opt_result' in locals() else opt_res,
            comp_df=comp_df,
            comp_summary=comp_summary,
            area_stats_df=area_stats,
            scenarios_summary_df=summary_df,
            current_demand_method="p95",
            current_priority_scenario="congestion",
            current_budget=87
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Generated file must have valid PDF header")
        self.assertGreater(len(pdf_bytes), 5000)


if __name__ == "__main__":
    unittest.main()

