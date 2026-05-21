"""Utilities for cleaning and standardising dataset values."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import pandas as pd
from pandas.api.types import is_integer_dtype, is_object_dtype, is_string_dtype


_IATI_DATASET_PATH = "BDDGLOBALMERGED_ACTUALIZADO.parquet"
_IATI_DATASET_V2_PATH = "BDDGLOBALMERGED_ACTUALIZADO_V2.parquet"
IATI_SNAPSHOTS = {
    "Snapshot noviembre 2025": _IATI_DATASET_PATH,
    "Snapshot mayo 2026": _IATI_DATASET_V2_PATH,
}
_IATI_MANUAL_VALUE_FIXES = {"XM-DAC-46027-PY028": 354_200_000}
_IATI_EXCLUDED_IDENTIFIERS = {
    "ID_CAF-5",
    "ID_CAF-9",
    "ID_CAF-17",
    "ID_CAF-23",
    "ID_CAF-27",
    "ID_CAF-37",
    "ID_CAF-45",
    "ID_CAF-56",
    "ID_CAF-58",
    "ID_CAF-61",
    "ID_CAF-94",
    "ID_CAF-112",
    "ID_CAF-115",
    "ID_CAF-118",
    "ID_CAF-120",
    "ID_CAF-274",
}


_COUNTRY_STANDARDISATION_MAP = {
    "Bolivia": "Bolivia (Plurinational State of)",
    "Brasil": "Brasil",
    "Brazil": "Brasil",
    "Argentina": "Argentina",
    "Bahamas (the)": "Bahamas",
    "Dominican Republic (the)": "Dominican Republic",
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Dominica": "Dominican Republic",
}


def _clean_string_series(series: pd.Series) -> pd.Series:
    """Return a normalised string series with surrounding whitespace removed."""

    if not is_string_dtype(series):
        # Convert to pandas' string dtype so ``str`` accessors are available.
        series = series.astype("string")
    return series.str.strip()


def optimise_dataframe_memory(
    df: pd.DataFrame,
    *,
    max_category_values: int = 128,
    category_ratio: float = 0.5,
) -> pd.DataFrame:
    """Return ``df`` with lower-memory dtypes where the conversion is safe.

    The app keeps dataframes cached between Streamlit reruns. Converting
    low-cardinality text columns to categoricals and downcasting integer fields
    lowers the resident memory without changing the values used in the charts.
    """

    for column in df.columns:
        series = df[column]
        if is_object_dtype(series) or is_string_dtype(series):
            unique_values = series.nunique(dropna=True)
            if unique_values == 0:
                continue
            if unique_values <= max_category_values and unique_values <= len(series) * category_ratio:
                df[column] = series.astype("category")
            continue

        if is_integer_dtype(series):
            df[column] = pd.to_numeric(series, downcast="integer")

    return df


@lru_cache(maxsize=4)
def load_iati_dataset(
    path: str = _IATI_DATASET_PATH, columns: tuple[str, ...] | None = None
) -> pd.DataFrame | None:
    """Return the merged IATI dataset with manual data corrections applied."""

    try:
        df = pd.read_parquet(path, columns=list(columns) if columns else None)
    except Exception:
        return None

    if df is None:
        return None

    df = df.copy()
    if {"iatiidentifier", "value_usd"}.issubset(df.columns):
        for identifier, corrected_value in _IATI_MANUAL_VALUE_FIXES.items():
            mask = df["iatiidentifier"] == identifier
            if mask.any():
                df.loc[mask, "value_usd"] = corrected_value
        if _IATI_EXCLUDED_IDENTIFIERS:
            df = df[~df["iatiidentifier"].isin(_IATI_EXCLUDED_IDENTIFIERS)]
    return optimise_dataframe_memory(df)


def standardise_recipient_countries(
    df: pd.DataFrame, columns: Iterable[str] = ("recipientcountry_codename",)
) -> pd.DataFrame:
    """Return a copy of ``df`` with harmonised country names.

    Parameters
    ----------
    df:
        Source dataframe whose columns contain country names.
    columns:
        Iterable with the column names that should be standardised. Columns that
        are absent in ``df`` are ignored.
    """

    if df is None:
        return df

    df = df.copy()
    for column in columns:
        if column not in df.columns:
            continue
        cleaned = _clean_string_series(df[column])
        df[column] = cleaned.replace(_COUNTRY_STANDARDISATION_MAP)
    return df
