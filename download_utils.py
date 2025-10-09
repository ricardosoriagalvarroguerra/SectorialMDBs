"""Utilities to add CSV download buttons for Plotly charts."""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def _ensure_dataframe(data: pd.DataFrame | pd.Series | list | tuple | dict) -> pd.DataFrame:
    """Convert the provided data into a pandas DataFrame when possible."""
    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, pd.Series):
        return data.to_frame().reset_index(drop=True)
    if isinstance(data, dict):
        try:
            return pd.DataFrame(data)
        except ValueError:
            return pd.DataFrame()
    if isinstance(data, (list, tuple)):
        try:
            return pd.DataFrame(data)
        except ValueError:
            return pd.DataFrame()
    return pd.DataFrame()


def build_csv_filename(*parts: str, suffix: str = "csv") -> str:
    """Construct a filesystem-friendly filename using the provided parts."""

    sanitized_parts = [
        re.sub(r"[^A-Za-z0-9_-]+", "_", part.strip())
        for part in parts
        if part and part.strip()
    ]
    sanitized_parts = [part.strip("_") for part in sanitized_parts if part.strip("_")]
    if not sanitized_parts:
        sanitized_parts = ["data"]
    name = "_".join(sanitized_parts)
    return f"{name}.{suffix}"


def download_csv_button(
    data: pd.DataFrame | pd.Series | list | tuple | dict | None,
    filename: str,
    *,
    label: str = "Descargar CSV",
    key: Optional[str] = None,
    container: Optional[DeltaGenerator] = None,
) -> None:
    """Render a CSV download button for the provided data.

    Parameters
    ----------
    data:
        Data to export. It will be converted to a pandas DataFrame. If the
        resulting dataframe is empty, the button is not rendered.
    filename:
        Name of the file offered to the user when downloading.
    label:
        Text displayed on the download button.
    key:
        Optional Streamlit widget key. If omitted a key derived from the
        filename is used.
    container:
        Optional container (e.g. a column) where the button should be
        rendered. When ``None`` the button is added to the main container.
    """

    df = _ensure_dataframe(data)
    if df.empty:
        return

    sanitized_name = re.sub(r"[^A-Za-z0-9_-]+", "_", filename)
    widget_key = key or f"download_{sanitized_name}"

    csv_data = df.to_csv(index=False).encode("utf-8")
    target = container if container is not None else st
    target.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=widget_key,
    )
