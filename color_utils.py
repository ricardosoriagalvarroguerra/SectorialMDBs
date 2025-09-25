"""Utility helpers for consistent color mapping across pages."""
from __future__ import annotations

from typing import Iterable

import plotly.express as px

# Canonical order of MDB sources for legend/stacked chart consistency.
BASE_SOURCE_ORDER = ["FONPLATA", "IADB", "WorldBank", "CAF"]

# Brand colors for the known MDB sources. The palette is shared between
# the financiamiento and sectores pages so that a source always appears
# with the same color no matter the chart or subpage.
BASE_SOURCE_COLORS = {
    "FONPLATA": "#c1121f",
    "IADB": "#284b63",
    "WorldBank": "#5fa8d3",
    "CAF": "#29bf12",
}


def order_sources(sources: Iterable[str]) -> list[str]:
    """Return sources sorted by preferred order followed by alphabetical."""

    unique_sources = [s for s in dict.fromkeys(sources) if s]
    ordered = [s for s in BASE_SOURCE_ORDER if s in unique_sources]
    ordered.extend(sorted(s for s in unique_sources if s not in BASE_SOURCE_ORDER))
    return ordered


def get_mdb_color_map(sources: Iterable[str]) -> dict[str, str]:
    """Return a color mapping for the provided MDB sources.

    Known sources use their brand color; additional sources receive colors from
    Plotly qualitative palettes in a deterministic order so that both pages
    share the same mapping.
    """

    ordered_sources = order_sources(sources)
    if not ordered_sources:
        return {}

    palette = (
        px.colors.qualitative.Plotly
        + px.colors.qualitative.D3
        + px.colors.qualitative.Set2
        + px.colors.qualitative.Set3
    )
    color_map: dict[str, str] = {}
    extra_idx = 0
    for source in ordered_sources:
        if source in BASE_SOURCE_COLORS:
            color_map[source] = BASE_SOURCE_COLORS[source]
        else:
            color_map[source] = palette[extra_idx % len(palette)]
            extra_idx += 1
    return color_map
