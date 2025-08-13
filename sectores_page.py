import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pandas.api.types import is_string_dtype
from io import BytesIO
from macrosectores import get_macrosector

# Paleta de colores para macro sectores
MACRO_COLORS = [
    "#001524",
    "#15616D",
    "#8AA79F",
    "#FFECD1",
    "#BC8B70",
    "#78290F",
    "#FF7D00",
]


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
                "Tabla maestro",
            ],
        )
        if subpage == "Panorama de sectores":
            selected_sources = st.multiselect(
                "MDBs", source_list, default=source_list
            )
    # Apply filters
    mask = (df["year"].between(*year_range)) & (df["value_usd"] >= 0)
    df_f = df[mask].copy()
    df_f = df_f[df_f["macro_sector"].ne("No clasificado")]
    if subpage == "Panorama de sectores" and selected_sources:
        df_f = df_f[df_f["source"].isin(selected_sources)]
    top_n = 10

    macros = sorted(df_f["macro_sector"].dropna().unique())
    macro_color_map = {
        macro: MACRO_COLORS[i % len(MACRO_COLORS)] for i, macro in enumerate(macros)
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
        fig_area = px.area(
            df_year_macro,
            x="year",
            y="value_usd",
            color="macro_sector",
            category_orders={"macro_sector": macro_order},
            labels={"year": "Año", "value_usd": "USD (millones)", "macro_sector": "Macro sector"},
            color_discrete_map=macro_color_map,
        )
        st.plotly_chart(fig_area, use_container_width=True)

    elif subpage == "Comparador A vs B":
        sector_list = sorted(df_f["macro_sector"].dropna().unique())
        source_list = sorted(df_f["source"].dropna().unique())
        col1, col2 = st.columns(2)
        with col1:
            sector_a = st.selectbox("Macro sector A", sector_list, key="sector_a")
            source_a = st.selectbox("MDB A", source_list, key="source_a")
        with col2:
            sector_b = st.selectbox("Macro sector B", sector_list, key="sector_b")
            source_b = st.selectbox("MDB B", source_list, key="source_b")
        df_a = df_f[(df_f["macro_sector"] == sector_a) & (df_f["source"] == source_a)]
        df_b = df_f[(df_f["macro_sector"] == sector_b) & (df_f["source"] == source_b)]
        df_a = df_a.groupby("year")["value_usd"].sum().reset_index()
        df_b = df_b.groupby("year")["value_usd"].sum().reset_index()
        df_a["grupo"] = f"{sector_a} - {source_a}"
        df_b["grupo"] = f"{sector_b} - {source_b}"
        comp_df = pd.concat([df_a, df_b])
        comp_df["value_usd"] = comp_df["value_usd"] / 1e6
        fig_line = px.line(
            comp_df,
            x="year",
            y="value_usd",
            color="grupo",
            labels={"value_usd": "USD (millones)", "year": "Año", "grupo": "Grupo"},
        )
        st.plotly_chart(fig_line, use_container_width=True)
        col_a, col_b = st.columns(2)
        for col, (sector, source) in zip((col_a, col_b), ((sector_a, source_a), (sector_b, source_b))):
            s_df = df_f[(df_f["macro_sector"] == sector) & (df_f["source"] == source)]
            total = s_df["value_usd"].sum() / 1e6
            ops = len(s_df)
            ticket = total / ops if ops else 0
            median = s_df["value_usd"].median() / 1e6 if ops else 0
            col.markdown(
                f"**{sector} - {source}**\n\n- Total: {total:,.2f} millones\n- #ops: {ops}\n- Ticket promedio: {ticket:,.2f} millones\n- Mediana: {median:,.2f} millones"
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
            st.dataframe(summary, use_container_width=True)

    elif subpage == "Matrices de concentración":
        st.title("Matrices de concentración")
        focus_countries = ["AR", "BO", "BR", "PY", "UY"]
        df_focus = df_f[df_f["recipientcountry_code"].isin(focus_countries)]
        pivot = (
            df_focus.pivot_table(
                index="macro_sector",
                columns="recipientcountry_codename",
                values="value_usd",
                aggfunc="sum",
                fill_value=0,
            )
        )
        pivot = pivot / 1e6
        fig_heat = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorbar=dict(title="USD (millones)"),
                colorscale="YlOrRd",
            )
        )
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
        pivot2 = pivot2 / 1e6
        fig_heat2 = go.Figure(
            data=go.Heatmap(
                z=pivot2.values,
                x=pivot2.columns,
                y=pivot2.index,
                colorbar=dict(title="USD (millones)"),
                colorscale="YlOrRd",
            )
        )
        st.plotly_chart(fig_heat2, use_container_width=True)

    elif subpage == "Intensidad y estructura":
        source_opts = sorted(df_f["source"].dropna().unique())
        country_opts = sorted(df_f["recipientcountry_codename"].dropna().unique())
        col_filters = st.columns(2)
        with col_filters[0]:
            selected_sources = st.multiselect("MDBs", source_opts, default=source_opts)
        with col_filters[1]:
            selected_countries = st.multiselect("Países", country_opts, default=country_opts)
        df_focus = df_f[
            df_f["source"].isin(selected_sources)
            & df_f["recipientcountry_codename"].isin(selected_countries)
        ]
        bubble_df = (
            df_focus.groupby("macro_sector").agg(
                sum_usd=("value_usd", lambda x: x.sum() / 1e6),
                mean_usd=("value_usd", lambda x: x.mean() / 1e6),
                ops=("iatiidentifier", "count"),
            )
        ).reset_index()
        fig_bubble = px.scatter(
            bubble_df,
            x="mean_usd",
            y="sum_usd",
            size="ops",
            color="macro_sector",
            hover_name="macro_sector",
            labels={"mean_usd": "Ticket promedio (millones)", "sum_usd": "Total USD (millones)", "ops": "# ops"},
            color_discrete_map=macro_color_map,
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

        sankey_df = (
            df_focus.groupby(["source", "macro_sector", "recipientcountry_codename"])["value_usd"].sum().reset_index()
        )
        sankey_df["value_usd"] = sankey_df["value_usd"] / 1e6
        if not sankey_df.empty:
            min_val = float(sankey_df["value_usd"].min())
            max_val = float(sankey_df["value_usd"].max())
            val_range = st.slider(
                "Rango de monto (millones USD)", min_val, max_val, (min_val, max_val)
            )
            sankey_df = sankey_df[sankey_df["value_usd"].between(*val_range)]
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

    elif subpage == "Tabla maestro":
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
