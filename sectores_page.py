import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pandas.api.types import is_string_dtype
from io import BytesIO
from macrosectores import get_macrosector

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


@st.cache_data
def load_sectores() -> pd.DataFrame:
    df = pd.read_parquet("sectores.parquet")
    df["transactiondate_isodate"] = pd.to_datetime(df["transactiondate_isodate"])
    if is_string_dtype(df["sector_code"]):
        df["sector_code"] = pd.to_numeric(df["sector_code"], errors="coerce")
    df["sector_code"] = df["sector_code"].astype("Int64")
    df["year"] = df["transactiondate_isodate"].dt.year
    df["month"] = df["transactiondate_isodate"].dt.to_period("M").astype(str)
    df["macro_sector"] = df["sector_codename"].map(get_macrosector)
    df.loc[df["sector_codename"].eq("Sectors not specified"), "macro_sector"] = (
        "Administrativo / No asignado"
    )
    return df

def render():
    df = load_sectores()
    min_year, max_year = int(df["year"].min()), int(df["year"].max())
    source_list = sorted(df["source"].dropna().unique())
    selected_sources = source_list
    country_code_map = {
        "Argentina": ["AR"],
        "Bolivia": ["BO"],
        "Brasil": ["BR"],
        "Paraguay": ["PY"],
        "Uruguay": ["UY"],
        "Resto Latam": [
            "CL",
            "CR",
            "CO",
            "GT",
            "EC",
            "HN",
            "MX",
            "NI",
            "PA",
            "PE",
            "SV",
        ],
    }
    country_options = list(country_code_map.keys())
    all_country_codes = [code for codes in country_code_map.values() for code in codes]
    selected_country_codes = all_country_codes
    country_list_tabla = sorted(df["recipientcountry_codename"].dropna().unique())
    selected_countries_tabla = country_list_tabla
    with st.sidebar:
        year_range = st.slider("Año", min_year, max_year, (min_year, max_year), step=1)
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
            selected_country_codes = []
            for label in selected_country_labels:
                selected_country_codes.extend(country_code_map[label])
        elif subpage == "Matrices de concentración":
            selected_sources = st.multiselect(
                "Source (MDBs)",
                source_list,
                default=source_list,
                key="mdbs_matrices",
            )
        elif subpage == "Tabla maestra":
            selected_sources = st.multiselect(
                "Source (MDBs)", source_list, default=source_list, key="mdbs_maestra"
            )
            selected_countries_tabla = st.multiselect(
                "País", country_list_tabla, default=country_list_tabla, key="paises_maestra"
            )
    # Apply filters
    mask = (df["year"].between(*year_range)) & (df["value_usd"] >= 0)
    df_f = df[mask].copy()
    df_f = df_f[df_f["macro_sector"].ne("No clasificado")]
    if subpage == "Panorama de sectores" and selected_sources:
        df_f = df_f[df_f["source"].isin(selected_sources)]
        df_f = df_f[df_f["recipientcountry_code"].isin(selected_country_codes)]
    elif subpage == "Matrices de concentración" and selected_sources:
        df_f = df_f[df_f["source"].isin(selected_sources)]
    elif subpage == "Tabla maestra":
        df_f = df_f[df_f["source"].isin(selected_sources)]
        df_f = df_f[df_f["recipientcountry_codename"].isin(selected_countries_tabla)]
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
        focus_codes = ["AR", "BR", "BO", "PY", "UY"]
        for code in focus_codes:
            country_df = sec_df[sec_df["recipientcountry_code"] == code]
            if country_df.empty:
                continue
            country_name = country_df["recipientcountry_codename"].iloc[0]
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
        focus_countries = ["AR", "BO", "BR", "PY", "UY"]
        df_focus = df_f[df_f["recipientcountry_code"].isin(focus_countries)]
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
        allowed_codes = ["AR", "BO", "BR", "PY", "UY"]
        df_base = df_f[df_f["recipientcountry_code"].isin(allowed_codes)]
        source_opts = sorted(df_base["source"].dropna().unique())
        country_map = (
            df_base[["recipientcountry_code", "recipientcountry_codename"]]
            .drop_duplicates()
            .set_index("recipientcountry_code")["recipientcountry_codename"]
        )
        country_opts = [country_map[c] for c in allowed_codes if c in country_map]
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
            selected_countries = country_sel
        df_focus = df_base[
            df_base["source"].isin(selected_sources)
            & df_base["recipientcountry_codename"].isin(selected_countries)
        ]
        group_cols = ["macro_sector"]
        symbol_col = None
        if len(selected_sources) > 1 and len(selected_countries) > 1:
            group_cols += ["source", "recipientcountry_codename"]
            symbol_col = "grupo"
        elif len(selected_sources) > 1:
            group_cols.append("source")
            symbol_col = "source"
        elif len(selected_countries) > 1:
            group_cols.append("recipientcountry_codename")
            symbol_col = "recipientcountry_codename"
        bubble_df = (
            df_focus.groupby(group_cols).agg(
                sum_usd=("value_usd", lambda x: x.sum() / 1e6),
                mean_usd=("value_usd", lambda x: x.mean() / 1e6),
                ops=("iatiidentifier", "count"),
            )
        ).reset_index()
        if symbol_col == "grupo":
            bubble_df["grupo"] = (
                bubble_df["source"] + " - " + bubble_df["recipientcountry_codename"]
            )
        symbol_map = None
        if symbol_col:
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
                name: symbols[i % len(symbols)]
                for i, name in enumerate(bubble_df[symbol_col].unique())
            }
        fig_bubble = px.scatter(
            bubble_df,
            x="mean_usd",
            y="sum_usd",
            size="ops",
            color="macro_sector",
            hover_name="macro_sector",
            labels={
                "mean_usd": "Ticket promedio (millones)",
                "sum_usd": "Total USD (millones)",
                "ops": "# ops",
            },
            color_discrete_map=macro_color_map,
            symbol=symbol_col,
            symbol_map=symbol_map,
        )
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
        sources_nodes = sankey_df["source"].unique().tolist()
        macro_nodes = sankey_df["macro_sector"].unique().tolist()
        country_nodes = sankey_df["recipientcountry_codename"].unique().tolist()
        nodes = sources_nodes + macro_nodes + country_nodes
        node_indices = {name: i for i, name in enumerate(nodes)}
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
        for row in sankey_df.itertuples():
            color = source_color_map[row.source]
            links["source"].append(node_indices[row.source])
            links["target"].append(node_indices[row.macro_sector])
            links["value"].append(row.value_usd)
            link_colors.append(color)
        for row in sankey_df.itertuples():
            color = source_color_map[row.source]
            links["source"].append(node_indices[row.macro_sector])
            links["target"].append(node_indices[row.recipientcountry_codename])
            links["value"].append(row.value_usd)
            link_colors.append(color)
        fig_sankey = go.Figure(
            go.Sankey(
                node=dict(label=nodes),
                link=dict(
                    source=links["source"],
                    target=links["target"],
                    value=links["value"],
                    color=links["color"],
                ),
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
