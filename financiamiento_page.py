import streamlit as st
import pandas as pd
import plotly.express as px
from itertools import cycle

COLOR_MAP = {
    "FONPLATA": "#c1121f",
    "IADB": "#003566",
    "worldbank": "#6096ba",
    "CAF": "#38b000",
}


@st.cache_data
def load_financiamiento() -> pd.DataFrame:
    df = pd.read_parquet("BDDGLOBALMERGED_ACTUALIZADO.parquet")
    df["transactiondate_isodate"] = pd.to_datetime(df["transactiondate_isodate"])
    return df


def render() -> None:
    st.title("Financiamiento para el desarrollo")

    df = load_financiamiento()
    if df is None or df.empty:
        st.info("No se pudieron cargar los datos.")
        return

    df = df.copy()
    df = df.dropna(subset=["transactiondate_isodate"])
    if df.empty:
        st.info("No hay fechas de transacción disponibles.")
        return

    df["macro_sector"] = df["macro_sector"].fillna("Sin dato")
    df["recipientcountry_codename"] = df["recipientcountry_codename"].fillna("Sin dato")
    df["transaction_year"] = df["transactiondate_isodate"].dt.year

    df = df[df["transaction_year"] >= 2013]
    if df.empty:
        st.info("No hay datos disponibles desde 2013 en adelante.")
        return

    min_year = int(df["transaction_year"].min())
    max_year = int(df["transaction_year"].max())

    with st.sidebar:
        st.header("Filtros")
        if min_year == max_year:
            selected_year = st.slider(
                "Año disponible",
                min_value=min_year,
                max_value=max_year,
                value=min_year,
                step=1,
            )
            date_range = (selected_year, selected_year)
        else:
            date_range = st.slider(
                "Rango de años",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
                step=1,
            )

        countries = sorted(df["recipientcountry_codename"].unique())
        selected_countries = st.multiselect("País", options=countries, default=countries)

        macro_sectors = sorted(df["macro_sector"].unique())
        selected_macros = st.multiselect(
            "Macro sector", options=macro_sectors, default=macro_sectors
        )

    start_year, end_year = date_range
    df_filtered = df[df["transaction_year"].between(start_year, end_year)]

    if selected_countries:
        df_filtered = df_filtered[
            df_filtered["recipientcountry_codename"].isin(selected_countries)
        ]
    else:
        st.info("Seleccione al menos un país para visualizar los datos.")
        return

    if selected_macros:
        df_filtered = df_filtered[df_filtered["macro_sector"].isin(selected_macros)]
    else:
        st.info("Seleccione al menos un macro sector para visualizar los datos.")
        return

    if df_filtered.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return

    year_order = sorted(df_filtered["transaction_year"].unique())
    year_order_str = [str(year) for year in year_order]

    available_sources = df_filtered["source"].dropna().unique().tolist()
    if not available_sources:
        st.info("No hay datos de fuentes para los filtros seleccionados.")
        return

    ordered_sources = [
        *[source for source in COLOR_MAP if source in available_sources],
        *sorted(source for source in available_sources if source not in COLOR_MAP),
    ]

    color_cycle = cycle(px.colors.qualitative.Plotly)
    color_map = COLOR_MAP.copy()
    for source in ordered_sources:
        if source not in color_map:
            color_map[source] = next(color_cycle)

    st.subheader("Evolución del financiamiento por fuente")

    aggregated_sources = (
        df_filtered.groupby(["source", "transaction_year"], as_index=False)["value_usd"].sum()
    )
    aggregated_sources["value_millions"] = aggregated_sources["value_usd"] / 1_000_000
    y_axis_max = aggregated_sources["value_millions"].max() if not aggregated_sources.empty else None
    if pd.isna(y_axis_max) or (y_axis_max is not None and y_axis_max <= 0):
        y_axis_max = None

    columns = st.columns(2)
    for idx, source in enumerate(ordered_sources):
        source_df = df_filtered[df_filtered["source"] == source]
        if source_df.empty:
            continue

        source_key = source.lower().replace(" ", "")
        remove_x_title = source_key in {"iadb", "fonplata"}
        remove_y_title = source_key in {"iadb", "worldbank"}

        grouped = (
            source_df.groupby("transaction_year", as_index=False)["value_usd"]
            .sum()
            .sort_values("transaction_year")
        )
        grouped["value_millions"] = grouped["value_usd"] / 1_000_000
        grouped["transaction_year_str"] = grouped["transaction_year"].astype(str)

        fig = px.bar(
            grouped,
            x="transaction_year_str",
            y="value_millions",
            labels={
                "transaction_year_str": "Año",
                "value_millions": "Monto anual (millones USD)",
            },
            title=source,
            color_discrete_sequence=[color_map[source]],
        )
        fig.update_traces(
            hovertemplate="Año: %{x}<br>Monto: %{y:.2f} millones USD<extra></extra>"
        )
        fig.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=year_order_str,
        )
        if y_axis_max is not None:
            fig.update_yaxes(range=[0, y_axis_max], tickformat=",.2f")
        else:
            fig.update_yaxes(tickformat=",.2f")
        if remove_x_title:
            fig.update_xaxes(title_text=None)
        if remove_y_title:
            fig.update_yaxes(title_text=None)
        fig.update_layout(
            title={"text": source, "x": 0.5, "xanchor": "center"},
            margin=dict(l=0, r=0, t=40, b=0),
        )

        columns[idx % 2].plotly_chart(fig, use_container_width=True)
        if idx % 2 == 1 and idx < len(ordered_sources) - 1:
            columns = st.columns(2)

    st.subheader("Participación porcentual de financiamiento por fuente")

    percentages = (
        df_filtered.groupby(["transaction_year", "source"], as_index=False)["value_usd"].sum()
    )
    percentages = (
        percentages.sort_values(["transaction_year", "source"]).reset_index(drop=True)
    )
    if percentages.empty:
        st.info("No hay montos registrados para los filtros seleccionados.")
        return

    percentages["year_total"] = percentages.groupby("transaction_year")["value_usd"].transform(
        "sum"
    )
    percentages = percentages[percentages["year_total"] > 0]
    if percentages.empty:
        st.info("No hay montos registrados para los filtros seleccionados.")
        return

    percentages["value_millions"] = percentages["value_usd"] / 1_000_000
    percentages["percentage"] = percentages["value_usd"] / percentages["year_total"] * 100
    percentages["transaction_year_str"] = percentages["transaction_year"].astype(str)

    fig_total = px.bar(
        percentages,
        x="transaction_year_str",
        y="percentage",
        color="source",
        color_discrete_map=color_map,
        category_orders={
            "source": ordered_sources,
            "transaction_year_str": year_order_str,
        },
        labels={
            "transaction_year_str": "Año",
            "percentage": "Participación (%)",
            "source": "Fuente",
        },
    )
    fig_total.update_layout(
        yaxis_title="Participación del total (%)",
        margin=dict(l=0, r=0, t=10, b=0),
        barmode="stack",
        yaxis=dict(range=[0, 100]),
    )
    fig_total.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=year_order_str,
    )
    fig_total.update_traces(texttemplate="%{y:.1f}%", textposition="inside")

    for trace in fig_total.data:
        source_name = trace.name
        source_rows = percentages[percentages["source"] == source_name]
        values_by_year = dict(
            zip(
                source_rows["transaction_year_str"],
                source_rows["value_millions"],
            )
        )
        trace.customdata = [
            [values_by_year.get(x, 0)] for x in trace.x
        ]
        trace.hovertemplate = (
            "Fuente: %{fullData.name}<br>"
            "Año: %{x}<br>"
            "Porcentaje: %{y:.1f}%<br>"
            "Monto: %{customdata[0]:,.2f} millones USD<extra></extra>"
        )

    st.plotly_chart(fig_total, use_container_width=True)
