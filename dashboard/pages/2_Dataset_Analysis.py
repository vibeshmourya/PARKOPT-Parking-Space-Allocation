"""Legacy stub forwarding to 2_Explore_Parking.py."""
import importlib
p = importlib.import_module("dashboard.pages.2_Explore_Parking")
render_dataset_analysis_page = p.render_explore_parking_page
if __name__ == "__main__":
    render_dataset_analysis_page()
