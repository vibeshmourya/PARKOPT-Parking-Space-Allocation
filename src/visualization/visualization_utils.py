"""
visualization_utils.py
Common styling, color schemes, data validation, and dual-format (PNG & HTML) export utilities.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

import os
import tempfile

# Ensure Matplotlib uses a writable temp cache directory to prevent warnings
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_itor_cache"))

import matplotlib
matplotlib.use("Agg")  # Safe headless rendering on all operating systems
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import plotly.graph_objects as go


# --- Academic / Analytics Color Palette ---
COLOR_PRIMARY_BLUE = "#1E3A8A"     # Deep Navy (Primary brand)
COLOR_SECONDARY_BLUE = "#3B82F6"   # Electric Blue (Secondary metrics)
COLOR_EMERALD = "#10B981"          # Emerald Green (Satisfied / Optimal)
COLOR_CRIMSON = "#EF4444"          # Crimson Red (High Demand / Overcapacity)
COLOR_AMBER = "#F59E0B"            # Amber / Gold (Moderate Demand / Warning)
COLOR_SLATE = "#64748B"            # Slate Gray (Neutral / Baseline)
COLOR_LIGHT_GRAY = "#E2E8F0"       # Soft Gray (Gridlines / Borders)
COLOR_DARK_SLATE = "#0F172A"       # Dark Slate (Typography)
COLOR_SALMON = "#F87171"           # Salmon Pink (Unmet Demand / Deficit)
COLOR_TEAL = "#0D9488"             # Teal Accent
COLOR_PURPLE = "#8B5CF6"           # Purple Accent

# Configure Seaborn Global Aesthetic
sns.set_theme(
    style="whitegrid",
    font="sans-serif",
    rc={
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 0.8,
        "grid.color": "#F1F5F9",
        "grid.linestyle": "--",
        "figure.facecolor": "#FFFFFF",
        "axes.facecolor": "#FFFFFF",
        "text.color": "#1E293B",
        "axes.labelcolor": "#1E293B",
        "xtick.color": "#475569",
        "ytick.color": "#475569"
    }
)

# Plotly Layout Template (Pure dicts for safe unpacking)
PLOTLY_LAYOUT_DEFAULTS = dict(
    font=dict(family="Arial, sans-serif", size=12, color="#1E293B"),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=55, r=45, t=55, b=55),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#CBD5E1",
        borderwidth=1
    ),
    xaxis=dict(gridcolor="#F1F5F9", zerolinecolor="#CBD5E1", linecolor="#CBD5E1"),
    yaxis=dict(gridcolor="#F1F5F9", zerolinecolor="#CBD5E1", linecolor="#CBD5E1")
)

PLOTLY_TEMPLATE = dict(layout=PLOTLY_LAYOUT_DEFAULTS)


def validate_required_columns(df: pd.DataFrame, required_cols: list, context_name: str) -> None:
    """
    Validates that a DataFrame exists, is non-empty, and contains required schema columns.
    Raises ValueError with descriptive context if check fails.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError(f"[{context_name}] Input DataFrame is None or not a valid pandas DataFrame.")
    if len(df) == 0:
        raise ValueError(f"[{context_name}] Input DataFrame is empty (0 records).")
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"[{context_name}] Missing required columns: {missing}. Present: {df.columns.tolist()}")


def save_static_and_interactive(
    fig_mpl: plt.Figure,
    fig_plotly: go.Figure,
    base_name: str,
    output_dir: str
) -> dict:
    """
    Saves a Matplotlib/Seaborn figure as high-resolution PNG (300 DPI)
    and a Plotly figure as self-contained interactive HTML.
    
    Returns:
        dict: {"png": path_to_png, "html": path_to_html}
    """
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    if fig_mpl is not None:
        png_path = os.path.join(output_dir, f"{base_name}.png")
        fig_mpl.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.close(fig_mpl)
        results["png"] = png_path

    if fig_plotly is not None:
        html_path = os.path.join(output_dir, f"{base_name}.html")
        fig_plotly.write_html(html_path, include_plotlyjs="cdn", full_html=True)
        results["html"] = html_path

    return results
