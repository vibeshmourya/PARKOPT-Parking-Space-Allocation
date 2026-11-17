"""Legacy stub forwarding to 1_Dashboard.py."""
import importlib
p = importlib.import_module("dashboard.pages.1_Dashboard")
render_overview_page = p.render_dashboard_page
if __name__ == "__main__":
    render_overview_page()
