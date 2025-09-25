import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas.api.types import is_string_dtype
from io import BytesIO

from date_utils import parse_transaction_dates

# Utilidad para manejar multiselect con opción "Seleccionar todo"
def handle_multiselect_behavior(selected_options, all_options, select_all_text):
    if not selected_options or select_all_text in selected_options:
        return all_options
    return [opt for opt in selected_options if opt != select_all_text]

# Paleta de colores fija para cada macro sector
MACRO_COLOR_MAP = {
    "Social": "#001524",
    "Productivo": "#15616D",
    "Infraestructura": "#8AA79F",
    "Ambiental": "#FFECD1",
    "Gobernanza/Público": "#BC8B70",
    "Multisectorial/Otros": "#78290F",
    "Administrativo / No asignado": "#FF7D00",
}

MDB_COLOR_MAP = {
    "FONPLATA": "#c1121f",
    "IADB": "#284b63",
    "WorldBank": "#5fa8d3",
    "CAF": "#29bf12",
}


def get_mdb_color_map(sources: list[str]) -> dict[str, str]:
    """Return a color map for the given MDB sources respecting predefined colors."""

    unique_sources = list(dict.fromkeys(sources))
    if not unique_sources:
        return {}

    palette = (
        px.colors.qualitative.Plotly
        + px.colors.qualitative.D3
        + px.colors.qualitative.Set2
        + px.colors.qualitative.Set3
    )
    color_map: dict[str, str] = {}
    extra_idx = 0
    for source in unique_sources:
        if source in MDB_COLOR_MAP:
            color_map[source] = MDB_COLOR_MAP[source]
        else:
            color_map[source] = palette[extra_idx % len(palette)]
            extra_idx += 1
    return color_map


@st.cache_data
def load_sectores() -> pd.DataFrame:
    df = pd.read_parquet("BDDGLOBALMERGED_ACTUALIZADO.parquet")
    df["transactiondate_isodate"] = parse_transaction_dates(
        df["transactiondate_isodate"]
    )
    if is_string_dtype(df["sector_code"]):
        df["sector_code"] = pd.to_numeric(df["sector_code"], errors="coerce")
    df["sector_code"] = df["sector_code"].astype("Int64")
    df["year"] = df["transactiondate_isodate"].dt.year.astype("Int64")
    df["month"] = df["transactiondate_isodate"].dt.to_period("M").astype(str)
    return df

def render():
    df = load_sectores()
    fp_mask = df["source"].str.upper().eq("FONPLATA")
    if fp_mask.any():
        fp_min, fp_max = df.loc[fp_mask, "value_usd"].agg(["min", "max"])
    else:
        fp_min = fp_max = 0
    min_year, max_year = int(df["year"].min()), int(df["year"].max())
    source_list = sorted(df["source"].dropna().unique())
    selected_sources = source_list
    country_name_map = {
        "Argentina": ["Argentina"],
        "Bolivia": ["Bolivia (Plurinational State of)"],
        "Brasil": ["Brazil"],
        "Paraguay": ["Paraguay"],
        "Uruguay": ["Uruguay"],
        "Resto Latam": [
            "Barbados",
            "Bahamas (the)",
            "Belize",
            "Chile",
            "Costa Rica",
            "Colombia",
            "Dominican Republic (the)",
            "Guatemala",
            "Guyana",
            "Ecuador",
            "Honduras",
            "Jamaica",
            "Haiti",
            "Mexico",
            "Nicaragua",
            "Panama",
            "Peru",
            "Suriname",
            "El Salvador",
            "Venezuela (Bolivarian Republic of)",
            "Trinidad and Tobago",
            "Antigua and Barbuda",
            "Dominica",
            "Grenada",
            "Saint Lucia",
            "Saint Vincent and the Grenadines",
        ],
    }
    country_options = list(country_name_map.keys())
    all_country_names = [name for names in country_name_map.values() for name in names]
    selected_country_names = all_country_names
    country_list_tabla = sorted(df["recipientcountry_codename"].dropna().unique())
    selected_countries_tabla = country_list_tabla
    with st.sidebar:
        if min_year == max_year:
            st.info(
                f"Solo hay datos disponibles para el año {min_year}. Se utilizará ese rango."
            )
            year_range = (min_year, max_year)
        else:
            year_range = st.slider(
                "Año", min_year, max_year, (min_year, max_year), step=1
            )
        subpage = st.radio(
            "Subpáginas",
            [
                "Panorama de sectores",
                "Comparador A vs B",
                "Ficha de sector",
                "Matrices de concentración",
                "Intensidad y estructura",
                "Tabla maestra",
            ],
        )
        if subpage == "Panorama de sectores":
            selected_sources = st.multiselect(
                "MDBs", source_list, default=source_list
            )
            country_sel = st.multiselect(
                "Países",
                ["Todos los países"] + country_options,
                default=["Todos los países"],
            )
            selected_country_labels = handle_multiselect_behavior(
                country_sel, country_options, "Todos los países"
            )
            selected_country_names = []
            for label in selected_country_labels:
                selected_country_names.extend(country_name_map[label])
        elif subpage == "Matrices de concentración":
            selected_sources = st.multiselect(
                "Source (MDBs)",
                source_list,
                default=source_list,
                key="mdbs_matrices",
            )
            country_sel = st.multiselect(
                "Países",
                ["Argentina", "Bolivia", "Brasil", "Paraguay", "Uruguay"],
                default=["Argentina", "Bolivia", "Brasil", "Paraguay", "Uruguay"],
                key="paises_matrices",
            )
            selected_country_names = []
            for label in country_sel:
                selected_country_names.extend(country_name_map.get(label, []))
        elif subpage == "Tabla maestra":
            selected_sources = st.multiselect(
                "Source (MDBs)", source_list, default=source_list, key="mdbs_maestra"
            )
            selected_countries_tabla = st.multiselect(
                "País", country_list_tabla, default=country_list_tabla, key="paises_maestra"
            )
        rango_fp = st.checkbox("Rango FP")
    # Apply filters
    mask = (df["year"].between(*year_range)) & (df["value_usd"] >= 0)
    df_f = df[mask].copy()
    df_f = df_f[df_f["macro_sector"].ne("No clasificado")]
    if subpage == "Panorama de sectores" and selected_sources:
        df_f = df_f[df_f["source"].isin(selected_sources)]
        df_f = df_f[df_f["recipientcountry_codename"].isin(selected_country_names)]
    elif subpage == "Matrices de concentración" and selected_sources:
        df_f = df_f[df_f["source"].isin(selected_sources)]
        df_f = df_f[df_f["recipientcountry_codename"].isin(selected_country_names)]
    elif subpage == "Tabla maestra":
        df_f = df_f[df_f["source"].isin(selected_sources)]
        df_f = df_f[df_f["recipientcountry_codename"].isin(selected_countries_tabla)]
    if rango_fp:
        df_f = df_f[df_f["value_usd"].between(fp_min, fp_max)]
    top_n = 10

    # Mapear los macro sectores presentes a los colores predefinidos para
    # asegurar consistencia incluso cuando se filtran datos por fechas u otros
    # criterios.
    macro_color_map = {
        m: MACRO_COLOR_MAP[m]
        for m in df_f["macro_sector"].dropna().unique()
        if m in MACRO_COLOR_MAP
    }

    if subpage == "Panorama de sectores":
        st.title("Panorama de Sectores")
        df_macro = (
            df_f.groupby("macro_sector")
            .agg(value_usd=("value_usd", "sum"), ops=("iatiidentifier", "count"))
            .sort_values("value_usd", ascending=True)
        )
        df_macro["value_usd"] = df_macro["value_usd"] / 1e6
        df_macro["ticket"] = df_macro["value_usd"] / df_macro["ops"]
        df_top = df_macro.tail(top_n).reset_index()
        macro_order = df_top["macro_sector"].tolist()
        col_bar, col_donut = st.columns(2)
        with col_bar:
            fig_bar = px.bar(
                df_top,
                x="value_usd",
                y="macro_sector",
                orientation="h",
                labels={"value_usd": "USD (millones)", "macro_sector": "Macro sector"},
                hover_data={"value_usd":":.2f","ops":True,"ticket":":.2f"},
                color_discrete_sequence=["#fca311"],
            )
            fig_bar.update_layout(yaxis={"categoryorder": "array", "categoryarray": macro_order})
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_donut:
            df_donut = df_macro.reset_index()
            fig_donut = px.pie(
                df_donut,
                names="macro_sector",
                values="value_usd",
                hole=0.4,
                color="macro_sector",
                color_discrete_map=macro_color_map,
            )
            fig_donut.update_traces(hovertemplate="%{label}: %{value:,.2f} millones")
            st.plotly_chart(fig_donut, use_container_width=True)

        df_year_macro = (
            df_f[df_f["macro_sector"].isin(macro_order)]
            .groupby(["year", "macro_sector"])["value_usd"].sum()
            .reset_index()
        )
        df_year_macro["value_usd"] = df_year_macro["value_usd"] / 1e6
        df_year_macro["macro_sector"] = pd.Categorical(
            df_year_macro["macro_sector"], categories=macro_order, ordered=True
        )
        # Leyenda manual centrada entre los dos gráficos de barras
        if macro_order:
            legend_items = [
                f"<span style='display:inline-flex;align-items:center;margin-right:8px;'>"
                f"<span style='width:12px;height:12px;background-color:{macro_color_map[m]};"
                f"display:inline-block;border-radius:2px;margin-right:4px;'></span>{m}</span>"
                for m in macro_order
                if m in macro_color_map
            ]
            legend_html = (
                "<div style='text-align:center;margin-bottom:10px;'>"
                + "".join(legend_items)
                + "</div>"
            )
            st.markdown(legend_html, unsafe_allow_html=True)

        col_stack, col_percent = st.columns(2)

        with col_stack:
            fig_stack = px.bar(
                df_year_macro,
                x="year",
                y="value_usd",
                color="macro_sector",
                category_orders={"macro_sector": macro_order},
                labels={
                    "year": "Año",
                    "value_usd": "USD (millones)",
                    "macro_sector": "Macro sector",
                },
                color_discrete_map=macro_color_map,
                barmode="stack",
            )
            fig_stack.update_layout(showlegend=False)
            st.plotly_chart(fig_stack, use_container_width=True)

        with col_percent:
            df_percent = df_year_macro.copy()
            df_percent["percent"] = (
                df_percent.groupby("year")["value_usd"].transform(lambda x: x / x.sum() * 100)
            )
            fig_percent = px.bar(
                df_percent,
                x="year",
                y="percent",
                color="macro_sector",
                category_orders={"macro_sector": macro_order},
                labels={
                    "year": "Año",
                    "percent": "Participación (%)",
                    "macro_sector": "Macro sector",
                },
                color_discrete_map=macro_color_map,
                barmode="stack",
            )
            fig_percent.update_yaxes(range=[0, 100])
            fig_percent.update_layout(showlegend=False)
            st.plotly_chart(fig_percent, use_container_width=True)

    elif subpage == "Comparador A vs B":
        sector_list = sorted(df_f["macro_sector"].dropna().unique())
        source_list = sorted(df_f["source"].dropna().unique())
        country_list = sorted(
            df_f["recipientcountry_codename"].dropna().unique()
        )
        col1, col2 = st.columns(2)
        with col1:
            sector_a = st.selectbox("Macro sector A", sector_list, key="sector_a")
            source_a = st.selectbox("MDB A", source_list, key="source_a")
            country_a = st.selectbox("País A", country_list, key="country_a")
        with col2:
            sector_b = st.selectbox("Macro sector B", sector_list, key="sector_b")
            source_b = st.selectbox("MDB B", source_list, key="source_b")
            country_b = st.selectbox("País B", country_list, key="country_b")
        df_a = df_f[
            (df_f["macro_sector"] == sector_a)
            & (df_f["source"] == source_a)
            & (df_f["recipientcountry_codename"] == country_a)
        ]
        df_b = df_f[
            (df_f["macro_sector"] == sector_b)
            & (df_f["source"] == source_b)
            & (df_f["recipientcountry_codename"] == country_b)
        ]
        df_a = df_a.groupby("year")["value_usd"].sum().reset_index()
        df_b = df_b.groupby("year")["value_usd"].sum().reset_index()
        df_a["grupo"] = f"{sector_a} - {source_a} - {country_a}"
        df_b["grupo"] = f"{sector_b} - {source_b} - {country_b}"
        comp_df = pd.concat([df_a, df_b])
        comp_df["value_usd"] = comp_df["value_usd"] / 1e6
        color_map = {
            f"{sector_a} - {source_a} - {country_a}": "#219ebc",
            f"{sector_b} - {source_b} - {country_b}": "#ffb703",
        }
        fig_bar = px.bar(
            comp_df,
            x="year",
            y="value_usd",
            color="grupo",
            labels={"value_usd": "USD (millones)", "grupo": "Grupo"},
            color_discrete_map=color_map,
            barmode="stack",
        )
        fig_bar.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                title_text="",
            )
        )
        fig_bar.update_xaxes(title="")
        st.plotly_chart(fig_bar, use_container_width=True)
        col_a, col_b = st.columns(2)
        for col, (sector, source, country) in zip(
            (col_a, col_b),
            ((sector_a, source_a, country_a), (sector_b, source_b, country_b)),
        ):
            s_df = df_f[
                (df_f["macro_sector"] == sector)
                & (df_f["source"] == source)
                & (df_f["recipientcountry_codename"] == country)
            ]
            total = s_df["value_usd"].sum() / 1e6
            ops = len(s_df)
            ticket = total / ops if ops else 0
            median = s_df["value_usd"].median() / 1e6 if ops else 0
            col.markdown(
                f"**{sector} - {source} - {country}**\n\n"
                f"- Total: {total:,.2f} millones\n"
                f"- #ops: {ops}\n"
                f"- Ticket promedio: {ticket:,.2f} millones\n"
                f"- Mediana: {median:,.2f} millones"
            )

        st.markdown("---")
        st.subheader("Participación acumulada por MDB")
        dist_sel_cols = st.columns(2)
        with dist_sel_cols[0]:
            sector_a_pct = st.selectbox(
                "Macro sector A (participación)",
                sector_list,
                key="sector_a_pct",
            )
            country_a_pct = st.selectbox(
                "País A (participación)",
                country_list,
                key="country_a_pct",
            )
        with dist_sel_cols[1]:
            sector_b_pct = st.selectbox(
                "Macro sector B (participación)",
                sector_list,
                key="sector_b_pct",
            )
            country_b_pct = st.selectbox(
                "País B (participación)",
                country_list,
                key="country_b_pct",
            )

        comparator_inputs = [
            ("A", sector_a_pct, country_a_pct),
            ("B", sector_b_pct, country_b_pct),
        ]
        dist_results = []
        combined_sources: list[str] = []

        for label, macro_sel, country_sel in comparator_inputs:
            subset = df_f[
                (df_f["macro_sector"] == macro_sel)
                & (df_f["recipientcountry_codename"] == country_sel)
            ].copy()
            if subset.empty:
                dist_results.append((label, macro_sel, country_sel, subset, None))
                continue

            dist_df = (
                subset.groupby(["year", "source"])["value_usd"].sum().reset_index()
            )
            if dist_df.empty:
                dist_results.append((label, macro_sel, country_sel, subset, None))
                continue

            dist_df["value_usd"] = dist_df["value_usd"] / 1e6
            all_years = sorted(dist_df["year"].unique())
            all_sources = list(dict.fromkeys(dist_df["source"]))
            full_index = pd.MultiIndex.from_product(
                [all_years, all_sources], names=["year", "source"]
            )
            dist_df = (
                dist_df.set_index(["year", "source"])
                .reindex(full_index, fill_value=0)
                .reset_index()
                .sort_values(["source", "year"])
            )
            dist_df["cumulative_value"] = (
                dist_df.groupby("source")["value_usd"].cumsum()
            )
            dist_df["total_cumulative"] = dist_df.groupby("year")[
                "cumulative_value"
            ].transform("sum")
            dist_df = dist_df[dist_df["total_cumulative"] > 0]
            if dist_df.empty:
                dist_results.append((label, macro_sel, country_sel, subset, None))
                continue

            dist_df["share"] = dist_df["cumulative_value"] / dist_df[
                "total_cumulative"
            ]
            dist_results.append((label, macro_sel, country_sel, subset, dist_df))
            for source in all_sources:
                if source not in combined_sources:
                    combined_sources.append(source)

        color_map = get_mdb_color_map(combined_sources)
        subplot_titles = [
            f"{macro_sel} - {country_sel}" for _, macro_sel, country_sel, _, _ in dist_results
        ]
        fig_pct = make_subplots(
            rows=1,
            cols=len(dist_results),
            shared_yaxes=True,
            subplot_titles=subplot_titles,
            horizontal_spacing=0.12,
        )

        for idx, (label, macro_sel, country_sel, subset, dist_df) in enumerate(
            dist_results, start=1
        ):
            if dist_df is None or dist_df.empty:
                x_axis = "x" if idx == 1 else f"x{idx}"
                y_axis = "y" if idx == 1 else f"y{idx}"
                fig_pct.add_annotation(
                    text="No hay datos para la selección realizada en este comparador.",
                    x=0.5,
                    y=0.5,
                    xref=f"{x_axis} domain",
                    yref=f"{y_axis} domain",
                    showarrow=False,
                    font=dict(color="#666", size=12),
                )
                continue

            for source in dist_df["source"].unique():
                source_df = dist_df[dist_df["source"] == source]
                fig_pct.add_trace(
                    go.Bar(
                        x=source_df["year"],
                        y=source_df["share"],
                        name=source,
                        marker_color=color_map.get(source),
                        customdata=source_df[["share", "cumulative_value"]],
                        hovertemplate=(
                            "<b>Año:</b> %{x}<br>"
                            "<b>MDB:</b> %{fullData.name}<br>"
                            "<b>Participación acumulada:</b> %{customdata[0]:.1%}<br>"
                            "<b>Monto acumulado:</b> %{customdata[1]:,.2f} millones"
                            "<extra></extra>"
                        ),
                        legendgroup=source,
                        showlegend=(idx == 1),
                    ),
                    row=1,
                    col=idx,
                )

            fig_pct.update_xaxes(title_text="Año acumulado", row=1, col=idx)

        fig_pct.update_yaxes(
            range=[0, 1], tickformat=".0%", title_text="Participación (%)", row=1, col=1
        )
        fig_pct.update_layout(
            barmode="stack",
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
                title_text="",
            ),
            margin=dict(t=70, b=120),
        )
        st.plotly_chart(fig_pct, use_container_width=True)

        metric_cols = st.columns(len(dist_results))
        for col, (label, macro_sel, country_sel, subset, dist_df) in zip(
            metric_cols, dist_results
        ):
            col.markdown(f"**{macro_sel} - {country_sel}**")
            if dist_df is None or subset.empty:
                col.warning(
                    "No hay datos para la selección realizada en este comparador."
                )
                continue

            total = subset["value_usd"].sum() / 1e6
            ops = len(subset)
            ticket = total / ops if ops else 0
            median = subset["value_usd"].median() / 1e6 if ops else 0
            col.markdown(
                f"- Total acumulado: {total:,.2f} millones\n"
                f"- #ops: {ops}\n"
                f"- Ticket promedio: {ticket:,.2f} millones\n"
                f"- Mediana: {median:,.2f} millones"
            )

    elif subpage == "Ficha de sector":
        sector_totals = (
            df_f.groupby("macro_sector")["value_usd"].sum().sort_values(ascending=False)
            / 1e6
        )
        default_sector = sector_totals.index[0] if not sector_totals.empty else None
        sector_sel = st.selectbox(
            "Macro sector", sector_totals.index.tolist(), index=0 if default_sector else None
        )
        sec_df = df_f[df_f["macro_sector"] == sector_sel].copy()
        sec_df["value_usd"] = sec_df["value_usd"] / 1e6
        top_countries = (
            sec_df.groupby("recipientcountry_codename")["value_usd"]
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
        )
        top_sources = (
            sec_df.groupby("source")["value_usd"].sum().sort_values(ascending=False).head(top_n).reset_index()
        )
        col_country, col_source = st.columns(2)
        with col_country:
            fig_country = px.bar(
                top_countries,
                x="value_usd",
                y="recipientcountry_codename",
                orientation="h",
                labels={"value_usd": "USD (millones)", "recipientcountry_codename": "País"},
                color_discrete_sequence=["#fca311"],
            )
            fig_country.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_country, use_container_width=True)
        with col_source:
            fig_source = px.bar(
                top_sources,
                x="source",
                y="value_usd",
                labels={"value_usd": "USD (millones)", "source": "MDB"},
                color_discrete_sequence=["#fca311"],
            )
            st.plotly_chart(fig_source, use_container_width=True)

        st.subheader("Detalle por país")
        focus_labels = ["Argentina", "Brasil", "Bolivia", "Paraguay", "Uruguay"]
        for label in focus_labels:
            country_name = country_name_map[label][0]
            country_df = sec_df[sec_df["recipientcountry_codename"] == country_name]
            if country_df.empty:
                continue
            total_ops = country_df["iatiidentifier"].nunique()
            st.markdown(f"### {country_name} ({total_ops} actividades)")
            summary = (
                country_df.groupby("source")
                .agg(
                    actividades=("iatiidentifier", "count"),
                    ticket_promedio=("value_usd", "mean"),
                    monto=("value_usd", "sum"),
                )
                .sort_values("monto", ascending=False)
                .head(4)
            )
            summary = summary.rename(
                columns={
                    "actividades": "# actividades",
                    "ticket_promedio": "Ticket prom. (millones USD)",
                    "monto": "Monto (millones USD)",
                }
            )
            summary["Ticket prom. (millones USD)"] = (
                summary["Ticket prom. (millones USD)"].round().astype(int)
            )
            summary["Monto (millones USD)"] = (
                summary["Monto (millones USD)"].round().astype(int)
            )
            st.dataframe(summary, use_container_width=True)

    elif subpage == "Matrices de concentración":
        st.title("Matrices de concentración")
        df_focus = df_f[df_f["recipientcountry_codename"].isin(selected_country_names)]
        sector_order = (
            df_focus.groupby("macro_sector")["value_usd"]
            .sum()
            .sort_values(ascending=False)
            .index
        )
        pivot = (
            df_focus.pivot_table(
                index="macro_sector",
                columns="recipientcountry_codename",
                values="value_usd",
                aggfunc="sum",
                fill_value=0,
            )
        )
        pivot = pivot.div(pivot.sum(axis=0), axis=1).fillna(0) * 100
        pivot = pivot.loc[sector_order]
        fig_heat = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorbar=dict(title="Participación (%)"),
                colorscale="YlOrRd",
                zmin=0,
                zmax=100,
                hovertemplate="%{y} - %{x}: %{z:.1f}%<extra></extra>",
            )
        )
        fig_heat.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_heat, use_container_width=True)

        pivot2 = (
            df_focus.pivot_table(
                index="year",
                columns="macro_sector",
                values="value_usd",
                aggfunc="sum",
                fill_value=0,
            )
        )
        pivot2 = pivot2.div(pivot2.sum(axis=1), axis=0).fillna(0) * 100
        pivot2 = pivot2.T
        pivot2 = pivot2.loc[sector_order]
        fig_heat2 = go.Figure(
            data=go.Heatmap(
                z=pivot2.values,
                x=pivot2.columns,
                y=pivot2.index,
                colorbar=dict(title="Participación (%)"),
                colorscale="YlOrRd",
                zmin=0,
                zmax=100,
                hovertemplate="%{y} - %{x}: %{z:.1f}%<extra></extra>",
            )
        )
        fig_heat2.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_heat2, use_container_width=True)

    elif subpage == "Intensidad y estructura":
        allowed_labels = ["Argentina", "Bolivia", "Brasil", "Paraguay", "Uruguay"]
        allowed_names = [country_name_map[l][0] for l in allowed_labels]
        df_base = df_f[df_f["recipientcountry_codename"].isin(allowed_names)]
        source_opts = sorted(df_base["source"].dropna().unique())
        country_opts = allowed_labels
        col_filters = st.columns(2)
        with col_filters[0]:
            source_sel = st.multiselect(
                "MDBs",
                source_opts,
                default=source_opts[:1],
            )
            selected_sources = source_sel
        with col_filters[1]:
            country_sel = st.multiselect(
                "Países",
                country_opts,
                default=country_opts[:1],
            )
            selected_countries = [country_name_map[label][0] for label in country_sel]
        df_focus = df_base[
            df_base["source"].isin(selected_sources)
            & df_base["recipientcountry_codename"].isin(selected_countries)
        ]
        group_cols = ["macro_sector", "source", "recipientcountry_codename"]
        bubble_df = (
            df_focus.groupby(group_cols).agg(
                sum_usd=("value_usd", lambda x: x.sum() / 1e6),
                mean_usd=("value_usd", lambda x: x.mean() / 1e6),
                ops=("iatiidentifier", "count"),
            )
        ).reset_index()
        symbols = [
            "circle",
            "square",
            "diamond",
            "cross",
            "x",
            "triangle-up",
            "triangle-down",
            "triangle-left",
            "triangle-right",
        ]
        symbol_map = {
            sector: symbols[i % len(symbols)]
            for i, sector in enumerate(bubble_df["macro_sector"].unique())
        }
        unique_sources = [
            s for s in bubble_df["source"].unique().tolist() if pd.notna(s)
        ]
        source_color_map = get_mdb_color_map(unique_sources)
        fig_bubble = px.scatter(
            bubble_df,
            x="mean_usd",
            y="sum_usd",
            color="source",
            symbol="macro_sector",
            hover_name="recipientcountry_codename",
            hover_data={"ops": True, "macro_sector": True},
            labels={
                "mean_usd": "Ticket promedio (millones)",
                "sum_usd": "Total USD (millones)",
                "source": "MDB",
                "macro_sector": "Macro sector",
                "recipientcountry_codename": "País",
            },
            color_discrete_map=source_color_map,
            symbol_map=symbol_map,
        )
        fig_bubble.update_traces(marker=dict(size=12))
        st.plotly_chart(fig_bubble, use_container_width=True)

        # El diagrama de Sankey no debe verse afectado por los filtros de
        # "MDBs" y "Países" seleccionados arriba, por lo que se construye a
        # partir de la base completa de datos filtrada solo por el rango de
        # años y países permitidos.
        sankey_base = df_base.copy()
        if not sankey_base.empty:
            min_val = float(sankey_base["value_usd"].min() / 1e6)
            max_val = float(sankey_base["value_usd"].max() / 1e6)
            col_range = st.columns(2)
            with col_range[0]:
                min_select = st.number_input(
                    "Monto mínimo (millones USD)",
                    value=min_val,
                    min_value=min_val,
                    max_value=max_val,
                )
            with col_range[1]:
                max_select = st.number_input(
                    "Monto máximo (millones USD)",
                    value=max_val,
                    min_value=min_val,
                    max_value=max_val,
                )
            if min_select > max_select:
                st.warning("El monto mínimo no puede ser mayor que el máximo")
            else:
                sankey_base = sankey_base[
                    sankey_base["value_usd"].between(
                        min_select * 1e6, max_select * 1e6
                    )
                ]
        sankey_df = (
            sankey_base.groupby(
                ["source", "macro_sector", "recipientcountry_codename"]
            )["value_usd"]
            .sum()
            .reset_index()
        )
        sankey_df["value_usd"] = sankey_df["value_usd"] / 1e6

        # Filtros para el diagrama de Sankey
        all_sources = sorted(sankey_df["source"].unique().tolist())
        all_countries = sorted(
            sankey_df["recipientcountry_codename"].unique().tolist()
        )
        all_macros = sorted(sankey_df["macro_sector"].unique().tolist())
        filter_cols = st.columns(3)
        with filter_cols[0]:
            sankey_sources = st.multiselect(
                "MDBs (Sankey)", all_sources, default=all_sources
            )
        with filter_cols[1]:
            sankey_countries = st.multiselect(
                "Países (Sankey)", all_countries, default=all_countries
            )
        with filter_cols[2]:
            sankey_macros = st.multiselect(
                "Macro sectores (Sankey)", all_macros, default=all_macros
            )
        sankey_df = sankey_df[
            sankey_df["source"].isin(sankey_sources)
            & sankey_df["recipientcountry_codename"].isin(sankey_countries)
            & sankey_df["macro_sector"].isin(sankey_macros)
        ]
        if sankey_df.empty:
            st.warning("No hay datos para las selecciones del Sankey")
        else:
            sources_nodes = sorted(sankey_df["source"].unique().tolist())
            macro_nodes = sorted(sankey_df["macro_sector"].unique().tolist())
            country_nodes = sorted(
                sankey_df["recipientcountry_codename"].unique().tolist()
            )
            nodes = sources_nodes + macro_nodes + country_nodes
            node_indices = {name: i for i, name in enumerate(nodes)}

            # Filtros específicos para resaltar en el diagrama
            focus_options = ["Todos", "MDBs", "Países", "Macro sectores"]
            focus = st.selectbox("Resaltar en Sankey", focus_options, index=0)
            focus_value = None
            if focus == "MDBs" and sources_nodes:
                focus_value = st.selectbox("MDB", sources_nodes)
            elif focus == "Países" and country_nodes:
                focus_value = st.selectbox("País", country_nodes)
            elif focus == "Macro sectores" and macro_nodes:
                focus_value = st.selectbox("Macro sector", macro_nodes)

            link_colors = []
            links = {"source": [], "target": [], "value": [], "color": link_colors}
            source_palette = px.colors.qualitative.Plotly
            custom_colors = {
                "FONPLATA": "#c1121f",
                "IADB": "#006494",
                "WorldBank": "#1b4965",
                "CAF": "#38b000",
            }
            source_color_map = {
                s: custom_colors.get(s, source_palette[i % len(source_palette)])
                for i, s in enumerate(sources_nodes)
            }

            grey_color = "rgba(200,200,200,0.2)"
            node_default_color = "rgba(200,200,200,0.8)"
            node_base_color = [node_default_color] * len(nodes)
            node_highlight = [False] * len(nodes)
            theme_base = st.get_option("theme.base") or "light"
            macro_country_color = "#D3D3D3"
            label_color = "#FFFFFF" if theme_base == "light" else "#000000"

            def highlight_row(row):
                if focus == "MDBs" and focus_value:
                    return row.source == focus_value
                if focus == "Países" and focus_value:
                    return row.recipientcountry_codename == focus_value
                if focus == "Macro sectores" and focus_value:
                    return row.macro_sector == focus_value
                return True

            for row in sankey_df.itertuples():
                color = source_color_map[row.source]
                highlight = highlight_row(row)
                s_idx = node_indices[row.source]
                t_idx = node_indices[row.macro_sector]
                links["source"].append(s_idx)
                links["target"].append(t_idx)
                links["value"].append(row.value_usd)
                link_colors.append(color if highlight else grey_color)
                node_base_color[s_idx] = color
                node_highlight[s_idx] = node_highlight[s_idx] or highlight
            for row in sankey_df.itertuples():
                color = source_color_map[row.source]
                highlight = highlight_row(row)
                s_idx = node_indices[row.macro_sector]
                t_idx = node_indices[row.recipientcountry_codename]
                links["source"].append(s_idx)
                links["target"].append(t_idx)
                links["value"].append(row.value_usd)
                link_colors.append(color if highlight else grey_color)
                node_highlight[s_idx] = node_highlight[s_idx] or highlight
                node_highlight[t_idx] = node_highlight[t_idx] or highlight

            for name in macro_nodes + country_nodes:
                idx = node_indices[name]
                node_base_color[idx] = macro_country_color
                node_highlight[idx] = True

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
                        color=links["color"],
                    ),
                    textfont=dict(color=label_color),
                )
            )
            fig_sankey.update_layout(height=600, width=1000)
            st.plotly_chart(fig_sankey, use_container_width=True)

    elif subpage == "Tabla maestra":
        cols = [
            "iatiidentifier",
            "transactiondate_isodate",
            "recipientcountry_codename",
            "source",
            "macro_sector",
            "sector_code",
            "sector_codename",
            "value_usd",
        ]
        st.dataframe(df_f[cols])
        csv = df_f[cols].to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, file_name="sectores.csv", mime="text/csv")
        excel = BytesIO()
        df_f[cols].to_excel(excel, index=False)
        st.download_button(
            "Descargar Excel", excel.getvalue(), file_name="sectores.xlsx", mime="application/vnd.ms-excel"
        )
