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

    min_date = df["transactiondate_isodate"].min()
    max_date = df["transactiondate_isodate"].max()

    with st.sidebar:
        st.header("Filtros")
        date_range = st.slider(
            "Rango de fechas",
            min_value=min_date.to_pydatetime(),
            max_value=max_date.to_pydatetime(),
            value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
            format="YYYY-MM-DD",
        )

        countries = sorted(df["recipientcountry_codename"].unique())
        selected_countries = st.multiselect("País", options=countries, default=countries)

        macro_sectors = sorted(df["macro_sector"].unique())
        selected_macros = st.multiselect(
            "Macro sector", options=macro_sectors, default=macro_sectors
        )

    start_date, end_date = [pd.to_datetime(dt) for dt in date_range]
    df_filtered = df[df["transactiondate_isodate"].between(start_date, end_date)]

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

    columns = st.columns(2)
    for idx, source in enumerate(ordered_sources):
        source_df = df_filtered[df_filtered["source"] == source]
        if source_df.empty:
            continue

        grouped = (
            source_df.groupby("transactiondate_isodate", as_index=False)["value_usd"]
            .sum()
            .sort_values("transactiondate_isodate")
        )
        grouped["value_millions"] = grouped["value_usd"] / 1_000_000

        fig = px.bar(
            grouped,
            x="transactiondate_isodate",
            y="value_millions",
            labels={
                "transactiondate_isodate": "Fecha de transacción",
                "value_millions": "Monto (millones USD)",
            },
            title=source,
            color_discrete_sequence=[color_map[source]],
        )
        fig.update_traces(
            hovertemplate="Fecha: %{x|%Y-%m-%d}<br>Monto: %{y:.2f} millones USD<extra></extra>"
        )
        fig.update_yaxes(tickformat=",.2f")
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))

        columns[idx % 2].plotly_chart(fig, use_container_width=True)
        if idx % 2 == 1 and idx < len(ordered_sources) - 1:
            columns = st.columns(2)

    st.subheader("Participación porcentual de financiamiento por fuente")

    totals = df_filtered.groupby("source", as_index=False)["value_usd"].sum()
    totals = totals.set_index("source").loc[ordered_sources].reset_index()
    total_value = totals["value_usd"].sum()
    if total_value == 0:
        st.info("No hay montos registrados para los filtros seleccionados.")
        return

    totals["value_millions"] = totals["value_usd"] / 1_000_000
    totals["percentage"] = totals["value_usd"] / total_value * 100
    totals["total_label"] = "Total"

    fig_total = px.bar(
        totals,
        x="total_label",
        y="value_usd",
        color="source",
        barnorm="percent",
        color_discrete_map=color_map,
        category_orders={"source": ordered_sources},
        labels={
            "total_label": "",
            "value_usd": "Participación (%)",
            "source": "Fuente",
        },
    )
    fig_total.update_layout(
        yaxis_title="Participación del total (%)",
        margin=dict(l=0, r=0, t=10, b=0),
    )
    fig_total.update_traces(texttemplate="%{y:.1f}%", textposition="inside")

    for trace in fig_total.data:
        source_name = trace.name
        row = totals[totals["source"] == source_name].iloc[0]
        amount_text = format(row["value_millions"], ",.2f")
        percentage_text = row["percentage"]
        trace.hovertemplate = (
            "Fuente: %{fullData.name}<br>"
            f"Porcentaje: {percentage_text:.1f}%<br>"
            f"Monto: {amount_text} millones USD<extra></extra>"
        )

    st.plotly_chart(fig_total, use_container_width=True)
