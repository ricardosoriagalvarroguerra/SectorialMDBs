"""Utilities for cleaning and standardising dataset values."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
from pandas.api.types import is_string_dtype


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

