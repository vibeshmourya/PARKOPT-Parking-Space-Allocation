"""Legacy stub forwarding to 3_Optimize_Allocation.py."""
import importlib
p = importlib.import_module("dashboard.pages.3_Optimize_Allocation")
render_optimization_model_page = p.render_optimize_allocation_page
if __name__ == "__main__":
    render_optimization_model_page()
