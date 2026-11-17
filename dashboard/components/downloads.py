"""
downloads.py
Reusable export and download buttons for CSV files and Academic PDF reports.
"""

from typing import Optional
import os
import pandas as pd
import streamlit as st


def render_csv_download_button(
    df: pd.DataFrame,
    filename: str,
    label: str = "📥 Download CSV",
    key: Optional[str] = None
) -> None:
    """
    Renders a standard Streamlit download button for a pandas DataFrame.
    """
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=key,
        use_container_width=True
    )


def render_pdf_download_button(
    pdf_bytes: bytes,
    filename: str = "PARKOPT_Academic_Report.pdf",
    label: str = "📄 Download Academic PDF Report",
    key: Optional[str] = "pdf_download_btn"
) -> None:
    """
    Renders a download button for generated ReportLab academic PDF.
    """
    st.download_button(
        label=label,
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        key=key,
        use_container_width=True
    )


def render_file_download_button(
    file_path: str,
    label: str,
    mime_type: str = "text/csv",
    key: Optional[str] = None
) -> None:
    """
    Renders a download button for an existing disk file if present.
    """
    if not os.path.exists(file_path):
        st.warning(f"File {os.path.basename(file_path)} is not available on disk.")
        return
        
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    st.download_button(
        label=label,
        data=file_bytes,
        file_name=os.path.basename(file_path),
        mime=mime_type,
        key=key,
        use_container_width=True
    )

