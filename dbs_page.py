"""Streamlit page that exposes repository datasets for download in multiple formats."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype, is_datetime64tz_dtype

from date_utils import parse_transaction_dates

REPO_ROOT = Path(__file__).resolve().parent


@st.cache_data(show_spinner=False)
def _load_parquet(path: str) -> pd.DataFrame:
    """Load a parquet file into a pandas DataFrame."""

    return pd.read_parquet(path)


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the dataframe with timezone aware datetimes normalized."""

    cleaned = df.copy()
    for column in cleaned.columns:
        series = cleaned[column]
        if is_datetime64tz_dtype(series):
            cleaned[column] = series.dt.tz_localize(None)
            continue

        if is_datetime64_any_dtype(series):
            tz = getattr(series.dt, "tz", None)
            if tz is not None:
                cleaned[column] = series.dt.tz_localize(None)
            continue

        if "date" in column.lower():
            parsed = parse_transaction_dates(series)
            if is_datetime64_any_dtype(parsed):
                cleaned[column] = parsed
    return cleaned


def _build_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def render() -> None:
    """Render the DBs page with download buttons for each dataset."""

    st.title("DBs")
    st.markdown(
        "Descarga las bases de datos disponibles en este repositorio en el formato que prefieras."
    )

    file_path = REPO_ROOT / "BDDGLOBALMERGED_ACTUALIZADO.parquet"
    if not file_path.exists():
        st.info("No se encontró la base de datos BDDGLOBALMERGED_ACTUALIZADO.parquet para descargar.")
        return

    df = _load_parquet(str(file_path))
    prepared_df = _prepare_dataframe(df)

    st.subheader(file_path.name)
    st.caption(f"Filas: {len(df):,} · Columnas: {len(df.columns)}")

    columns = st.columns(2)

    with columns[0]:
        with open(file_path, "rb") as file_obj:
            st.download_button(
                "Descargar Parquet",
                data=file_obj.read(),
                file_name=file_path.name,
                mime="application/octet-stream",
                key=f"download_{file_path.stem}_parquet",
            )

    csv_bytes = _build_csv_bytes(prepared_df)
    with columns[1]:
        st.download_button(
            "Descargar CSV",
            data=csv_bytes,
            file_name=f"{file_path.stem}.csv",
            mime="text/csv",
            key=f"download_{file_path.stem}_csv",
        )

    st.divider()
