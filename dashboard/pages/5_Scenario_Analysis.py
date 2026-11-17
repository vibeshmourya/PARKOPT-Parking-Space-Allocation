"""Legacy stub forwarding to 4_Results_and_Reports.py."""
import importlib
p = importlib.import_module("dashboard.pages.4_Results_and_Reports")
render_scenario_analysis_page = p.render_results_and_reports_page
if __name__ == "__main__":
    render_scenario_analysis_page()
