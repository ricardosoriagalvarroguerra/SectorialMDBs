"""Streamlit page that exposes repository datasets for download in multiple formats."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype, is_datetime64tz_dtype

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
        elif is_datetime64_any_dtype(series):
            tz = getattr(series.dt, "tz", None)
            if tz is not None:
                cleaned[column] = series.dt.tz_localize(None)
    return cleaned


def _build_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _build_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(
        buffer,
        engine="openpyxl",
        datetime_format="yyyy-mm-dd",
        date_format="yyyy-mm-dd",
    ) as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    buffer.seek(0)
    return buffer.read()


def render() -> None:
    """Render the DBs page with download buttons for each dataset."""

    st.title("DBs")
    st.markdown(
        "Descarga las bases de datos disponibles en este repositorio en el formato que prefieras."
    )

    parquet_files = sorted(REPO_ROOT.glob("*.parquet"))
    if not parquet_files:
        st.info("No se encontraron bases de datos en formato Parquet para descargar.")
        return

    for file_path in parquet_files:
        df = _load_parquet(str(file_path))
        prepared_df = _prepare_dataframe(df)

        st.subheader(file_path.name)
        st.caption(f"Filas: {len(df):,} · Columnas: {len(df.columns)}")

        columns = st.columns(3)

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

        excel_bytes = _build_excel_bytes(prepared_df)
        with columns[2]:
            st.download_button(
                "Descargar XLSX",
                data=excel_bytes,
                file_name=f"{file_path.stem}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_{file_path.stem}_xlsx",
            )

        st.divider()
