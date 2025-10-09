import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from color_utils import get_mdb_color_map, order_sources
from date_utils import parse_transaction_dates
from download_utils import build_csv_filename, download_csv_button


@st.cache_data
def load_financiamiento() -> pd.DataFrame:
    df = pd.read_parquet("BDDGLOBALMERGED_ACTUALIZADO.parquet")
    df["transactiondate_isodate"] = parse_transaction_dates(
        df["transactiondate_isodate"]
    )
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

    raw_min_year = int(df["transaction_year"].min())
    raw_max_year = int(df["transaction_year"].max())
    desired_min_year, desired_max_year = 2005, 2024
    min_year = max(desired_min_year, raw_min_year)
    max_year = min(desired_max_year, raw_max_year)
    if min_year > max_year:
        st.warning(
            "No hay datos disponibles entre los años 2005 y 2024. "
            "Mostrando el rango disponible en la fuente de datos."
        )
        min_year, max_year = raw_min_year, raw_max_year

    country_list = sorted(df["recipientcountry_codename"].unique())
    macro_sectors = sorted(df["macro_sector"].unique())
    source_list = order_sources(df["source"].dropna().unique())

    focus_countries = [
        "Argentina",
        "Bolivia (Plurinational State of)",
        "Brazil",
        "Paraguay",
        "Uruguay",
    ]
    intensity_country_defaults = [c for c in focus_countries if c in country_list]
    if not intensity_country_defaults and country_list:
        intensity_country_defaults = country_list[:1]

    view_options = ["Resumen general", "Intensidad y estructura"]
    selected_view = view_options[0]
    selected_countries = country_list
    selected_macros = macro_sectors
    intensity_sources = source_list[:1] if source_list else []
    intensity_countries = intensity_country_defaults

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

        selected_view = st.radio("Subpágina", view_options, index=0)
        if selected_view == "Resumen general":
            selected_countries = st.multiselect(
                "País",
                options=country_list,
                default=country_list,
            )
            selected_macros = st.multiselect(
                "Macro sector",
                options=macro_sectors,
                default=macro_sectors,
            )
        else:
            intensity_sources_default = source_list[:1] if source_list else []
            intensity_countries_default = intensity_country_defaults
            intensity_sources = st.multiselect(
                "MDBs",
                options=source_list,
                default=intensity_sources_default,
            )
            intensity_countries = st.multiselect(
                "Países",
                options=country_list,
                default=intensity_countries_default,
            )

    start_year, end_year = date_range
    df_filtered = df[df["transaction_year"].between(start_year, end_year)]
    if df_filtered.empty:
        st.info("No hay datos disponibles para el rango de años seleccionado.")
        return

    if selected_view == "Resumen general":
        if not selected_countries:
            st.info("Seleccione al menos un país para visualizar los datos.")
            return

        if not selected_macros:
            st.info("Seleccione al menos un macro sector para visualizar los datos.")
            return

        df_view = df_filtered[
            df_filtered["recipientcountry_codename"].isin(selected_countries)
            & df_filtered["macro_sector"].isin(selected_macros)
        ]
        if df_view.empty:
            st.info("No hay datos para los filtros seleccionados.")
            return

        year_order = sorted(df_view["transaction_year"].unique())
        year_order_str = [str(year) for year in year_order]

        available_sources = df_view["source"].dropna().unique().tolist()
        if not available_sources:
            st.info("No hay datos de fuentes para los filtros seleccionados.")
            return

        ordered_sources = order_sources(available_sources)
        color_map = get_mdb_color_map(ordered_sources)

        st.subheader("Evolución del financiamiento por fuente")

        aggregated_sources = (
            df_view.groupby(["source", "transaction_year"], as_index=False)["value_usd"].sum()
        )
        aggregated_sources["value_millions"] = aggregated_sources["value_usd"] / 1_000_000
        y_axis_max = (
            aggregated_sources["value_millions"].max() if not aggregated_sources.empty else None
        )
        if pd.isna(y_axis_max) or (y_axis_max is not None and y_axis_max <= 0):
            y_axis_max = None

        columns = st.columns(2)
        for idx, source in enumerate(ordered_sources):
            source_df = df_view[df_view["source"] == source]
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
                height=280,
            )

            columns[idx % 2].plotly_chart(fig, use_container_width=True)
            download_df = grouped[["transaction_year", "value_usd", "value_millions"]].rename(
                columns={
                    "transaction_year": "anio",
                    "value_usd": "valor_usd",
                    "value_millions": "valor_millones_usd",
                }
            )
            download_csv_button(
                download_df,
                build_csv_filename("financiamiento_fuente", source, "evolucion"),
                container=columns[idx % 2],
            )
            if idx % 2 == 1 and idx < len(ordered_sources) - 1:
                columns = st.columns(2)

        st.subheader("Participación porcentual de financiamiento por fuente")

        percentages = (
            df_view.groupby(["transaction_year", "source"], as_index=False)["value_usd"].sum()
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
            height=360,
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
        download_df = percentages[
            ["transaction_year", "source", "value_usd", "value_millions", "percentage"]
        ].rename(
            columns={
                "transaction_year": "anio",
                "value_usd": "valor_usd",
                "value_millions": "valor_millones_usd",
                "percentage": "participacion_porcentaje",
            }
        )
        download_csv_button(
            download_df,
            build_csv_filename("financiamiento_fuente", "participacion"),
        )
        return

    if selected_view == "Intensidad y estructura":
        if not intensity_sources:
            st.info("Seleccione al menos un MDB para visualizar los datos.")
            return

        if not intensity_countries:
            st.info("Seleccione al menos un país para visualizar los datos.")
            return

        df_focus = df_filtered[
            df_filtered["source"].isin(intensity_sources)
            & df_filtered["recipientcountry_codename"].isin(intensity_countries)
        ].dropna(subset=["source", "recipientcountry_codename", "value_usd"])

        if df_focus.empty:
            st.info("No hay datos para los filtros seleccionados.")
            return

        st.subheader("Intensidad del financiamiento por MDB y país")

        bubble_df = (
            df_focus.groupby(["source", "recipientcountry_codename"]).agg(
                total_millions=("value_usd", lambda x: x.sum() / 1_000_000),
                ticket_millions=("value_usd", lambda x: x.mean() / 1_000_000),
                ops=("iatiidentifier", "count"),
            )
        ).reset_index()
        bubble_df = bubble_df[bubble_df["ops"] > 0]
        if bubble_df.empty:
            st.info("No hay datos agregados para los filtros seleccionados.")
            return

        symbol_sequence = [
            "circle",
            "square",
            "diamond",
            "cross",
            "x",
            "triangle-up",
            "triangle-down",
            "triangle-left",
            "triangle-right",
            "triangle-ne",
            "triangle-se",
            "triangle-sw",
            "triangle-nw",
            "pentagon",
            "hexagon",
            "hexagon2",
            "octagon",
            "star",
            "hexagram",
            "bowtie",
            "hourglass",
        ]
        symbol_map = {
            country: symbol_sequence[i % len(symbol_sequence)]
            for i, country in enumerate(bubble_df["recipientcountry_codename"].unique())
        }
        color_map = get_mdb_color_map(bubble_df["source"].unique())

        fig_bubble = px.scatter(
            bubble_df,
            x="ticket_millions",
            y="total_millions",
            color="source",
            symbol="recipientcountry_codename",
            hover_name="recipientcountry_codename",
            labels={
                "ticket_millions": "Ticket promedio (millones)",
                "total_millions": "Total USD (millones)",
                "source": "MDB",
                "recipientcountry_codename": "País",
                "ops": "# actividades",
            },
            color_discrete_map=color_map,
            symbol_map=symbol_map,
            custom_data=[
                "source",
                "recipientcountry_codename",
                "ops",
                "ticket_millions",
                "total_millions",
            ],
        )
        fig_bubble.update_traces(marker=dict(size=12))
        fig_bubble.update_traces(
            hovertemplate=(
                "País: %{customdata[1]}<br>"
                "MDB: %{customdata[0]}<br>"
                "Total: %{customdata[4]:,.2f} millones USD<br>"
                "Ticket promedio: %{customdata[3]:,.2f} millones USD<br>"
                "Actividades: %{customdata[2]}<extra></extra>"
            )
        )
        st.plotly_chart(fig_bubble, use_container_width=True)
        download_csv_button(
            bubble_df.rename(
                columns={
                    "source": "mdb",
                    "recipientcountry_codename": "pais",
                    "total_millions": "total_millones_usd",
                    "ticket_millions": "ticket_promedio_millones_usd",
                    "ops": "numero_actividades",
                }
            ),
            build_csv_filename("financiamiento_intensidad", "burbuja"),
        )

        st.subheader("Estructura del financiamiento por MDB y país")

        sankey_base = df_filtered.dropna(
            subset=["source", "recipientcountry_codename", "value_usd"]
        )
        if sankey_base.empty:
            st.info("No hay datos para construir el diagrama de Sankey.")
            return

        min_val = float(sankey_base["value_usd"].min() / 1_000_000)
        max_val = float(sankey_base["value_usd"].max() / 1_000_000)
        range_cols = st.columns(2)
        with range_cols[0]:
            min_select = st.number_input(
                "Monto mínimo (millones USD)",
                value=min_val,
                min_value=min_val,
                max_value=max_val,
            )
        with range_cols[1]:
            max_select = st.number_input(
                "Monto máximo (millones USD)",
                value=max_val,
                min_value=min_val,
                max_value=max_val,
            )

        if min_select > max_select:
            st.warning("El monto mínimo no puede ser mayor que el máximo")
            return

        sankey_base = sankey_base[
            sankey_base["value_usd"].between(min_select * 1_000_000, max_select * 1_000_000)
        ]
        if sankey_base.empty:
            st.info("No hay datos en el rango de montos seleccionado.")
            return

        sankey_df = (
            sankey_base.groupby(["source", "recipientcountry_codename"])["value_usd"]
            .sum()
            .reset_index()
        )
        sankey_df["value_usd"] = sankey_df["value_usd"] / 1_000_000

        all_sources = order_sources(sankey_df["source"].unique().tolist())
        all_countries = sorted(sankey_df["recipientcountry_codename"].unique().tolist())

        filter_cols = st.columns(2)
        with filter_cols[0]:
            sankey_sources = st.multiselect(
                "MDBs (Sankey)", all_sources, default=all_sources
            )
        with filter_cols[1]:
            sankey_countries = st.multiselect(
                "Países (Sankey)", all_countries, default=all_countries
            )

        sankey_df = sankey_df[
            sankey_df["source"].isin(sankey_sources)
            & sankey_df["recipientcountry_codename"].isin(sankey_countries)
        ]
        if sankey_df.empty:
            st.warning("No hay datos para las selecciones del Sankey")
            return

        sources_nodes = order_sources(sankey_df["source"].unique().tolist())
        country_nodes = sorted(
            sankey_df["recipientcountry_codename"].unique().tolist()
        )
        nodes = sources_nodes + country_nodes
        node_indices = {name: i for i, name in enumerate(nodes)}

        focus_options = ["Todos", "MDBs", "Países"]
        focus = st.selectbox("Resaltar en Sankey", focus_options, index=0)
        focus_value = None
        if focus == "MDBs" and sources_nodes:
            focus_value = st.selectbox("MDB", sources_nodes)
        elif focus == "Países" and country_nodes:
            focus_value = st.selectbox("País", country_nodes)

        ordered_sources = order_sources(sources_nodes)
        source_color_map = get_mdb_color_map(ordered_sources)

        grey_color = "rgba(200,200,200,0.2)"
        node_default_color = "rgba(200,200,200,0.8)"
        node_base_color = [node_default_color] * len(nodes)
        node_highlight = [False] * len(nodes)
        theme_base = st.get_option("theme.base") or "light"
        country_color = "#D3D3D3"
        label_color = "#FFFFFF" if theme_base == "light" else "#000000"

        for name in sources_nodes:
            idx = node_indices[name]
            node_base_color[idx] = source_color_map[name]
        for name in country_nodes:
            idx = node_indices[name]
            node_base_color[idx] = country_color

        link_colors = []
        links = {"source": [], "target": [], "value": [], "color": link_colors}

        def highlight_row(row):
            if focus == "MDBs" and focus_value:
                return row.source == focus_value
            if focus == "Países" and focus_value:
                return row.recipientcountry_codename == focus_value
            return True

        for row in sankey_df.itertuples():
            color = source_color_map.get(row.source, "#888888")
            highlight = highlight_row(row)
            s_idx = node_indices[row.source]
            t_idx = node_indices[row.recipientcountry_codename]
            links["source"].append(s_idx)
            links["target"].append(t_idx)
            links["value"].append(float(row.value_usd))
            link_colors.append(color if highlight else grey_color)
            node_highlight[s_idx] = node_highlight[s_idx] or highlight
            node_highlight[t_idx] = node_highlight[t_idx] or highlight

        node_colors = [
            node_base_color[i] if node_highlight[i] else grey_color
            for i in range(len(nodes))
        ]

        fig_sankey = go.Figure(
            go.Sankey(
                node=dict(label=nodes, color=node_colors),
                link=dict(
                    source=links["source"],
                    target=links["target"],
                    value=links["value"],
                    color=link_colors,
                ),
                textfont=dict(color=label_color),
            )
        )
        fig_sankey.update_layout(height=500, width=1000)
        st.plotly_chart(fig_sankey, use_container_width=True)
        download_csv_button(
            sankey_df.rename(
                columns={
                    "source": "mdb",
                    "recipientcountry_codename": "pais",
                    "value_usd": "valor_millones_usd",
                }
            ),
            build_csv_filename("financiamiento_intensidad", "sankey"),
        )
