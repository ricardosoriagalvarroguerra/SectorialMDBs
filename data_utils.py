"""Utilities for cleaning and standardising dataset values."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
from pandas.api.types import is_string_dtype


_IATI_DATASET_PATH = "BDDGLOBALMERGED_ACTUALIZADO.parquet"
_IATI_MANUAL_VALUE_FIXES = {"XM-DAC-46027-PY028": 354_200_000}


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


def load_iati_dataset(path: str = _IATI_DATASET_PATH) -> pd.DataFrame | None:
    """Return the merged IATI dataset with manual data corrections applied."""

    try:
        df = pd.read_parquet(path)
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
    return df


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

