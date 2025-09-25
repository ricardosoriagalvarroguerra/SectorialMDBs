"""Utility helpers to parse transaction date values consistently."""

from __future__ import annotations

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

# Accepted lower/upper bounds for realistic civil years.
_MIN_VALID_YEAR = 1900
_MAX_VALID_YEAR = 2100


def parse_transaction_dates(series: pd.Series) -> pd.Series:
    """Return a datetime series from heterogeneous raw date representations.

    The source data combines timestamps stored as integers (days since the Unix
    epoch), plain years and ISO formatted strings. Pandas will interpret integer
    values as nanoseconds when ``unit`` is not provided, producing the spurious
    1970 dates that were showing up in the visualisations. This helper performs
    a couple of checks to infer the appropriate unit so that the conversion is
    robust across the different encodings we receive.
    """

    if is_datetime64_any_dtype(series):
        return series

    # ``to_numeric`` converts non-numeric entries to ``NaN`` which are then
    # ignored by the heuristic below. Values <= 0 are treated as missing to
    # avoid the Epoch (1970) artefact when dealing with filled zeros.
    numeric = pd.to_numeric(series, errors="coerce") if not is_numeric_dtype(series) else series
    numeric = pd.to_numeric(numeric, errors="coerce")
    numeric = numeric.where(numeric > 0)
    numeric_non_na = numeric.dropna()

    if numeric_non_na.empty:
        return pd.to_datetime(series, errors="coerce", infer_datetime_format=True)

    # Years stored as integers (e.g. 2014) should map to the first day of that
    # year instead of the Unix epoch.
    if numeric_non_na.between(_MIN_VALID_YEAR, _MAX_VALID_YEAR).all():
        return pd.to_datetime(
            numeric.astype("Int64").astype(str) + "-01-01", errors="coerce"
        )

    max_value = float(numeric_non_na.max())

    # Integers around ~10^4 represent days since 1970 in the original files.
    if max_value < 1_000_000:
        return pd.to_datetime(
            numeric, unit="D", origin="1970-01-01", errors="coerce"
        )

    # Fall back to the usual timestamp units, selecting the first match that
    # keeps the resulting years in a reasonable range.
    for unit, threshold in (("s", 1e11), ("ms", 1e14), ("us", 1e17), ("ns", float("inf"))):
        if max_value < threshold:
            converted = pd.to_datetime(
                numeric, unit=unit, origin="1970-01-01", errors="coerce"
            )
            years = converted.dt.year.dropna()
            if not years.empty and years.between(_MIN_VALID_YEAR, _MAX_VALID_YEAR).all():
                return converted

    # As a last resort defer to pandas' parser.
    return pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
