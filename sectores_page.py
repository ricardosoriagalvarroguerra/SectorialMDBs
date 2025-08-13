import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pandas.api.types import is_string_dtype
from io import StringIO, BytesIO
from macrosectores import get_macrosector


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


# --------- Helper functions ---------

def kpi_block(df: pd.DataFrame):
    total = df["value_usd"].sum()
    ops = len(df)
    avg_ticket = total / ops if ops else 0
    median_ticket = df["value_usd"].median() if ops else 0
    countries = df["recipientcountry_codename"].nunique()
    sectors = df["sector_codename"].nunique()
    leader = (
        df.groupby("sector_codename")["value_usd"].sum().sort_values(ascending=False).head(1)
    )
    if not leader.empty and total:
        leader_name = leader.index[0]
        leader_pct = leader.iloc[0] / total * 100
        leader_text = f"{leader_name} ({leader_pct:.1f}%)"
    else:
        leader_text = "N/A"
    st.markdown(
        f"**Total USD:** {total:,.2f}  |  **# Operaciones:** {ops}  |  **Ticket promedio:** {avg_ticket:,.2f}  |  **Mediana:** {median_ticket:,.2f}  |  **# Países:** {countries}  |  **# Sectores:** {sectors}  |  **Sector líder:** {leader_text}"
    )


def render():
    df = load_sectores()
    min_year, max_year = int(df["year"].min()), int(df["year"].max())
    with st.sidebar:
        year_range = st.slider("Año", min_year, max_year, (min_year, max_year), step=1)
        countries = st.multiselect(
            "País", sorted(df["recipientcountry_codename"].dropna().unique())
        )
        sources = st.multiselect("Fuente / MDB", sorted(df["source"].dropna().unique()))
        orgs = st.multiselect(
            "Organización reportante", sorted(df["reportingorg_ref"].dropna().unique())
        )
        sector_options = (
            df[["sector_code", "sector_codename"]]
            .drop_duplicates()
            .dropna()
            .sort_values("sector_code")
        )
        sector_labels = {
            f"{row.sector_code:05d} - {row.sector_codename}": row.sector_codename
            for row in sector_options.itertuples()
        }
        sector_selection = st.multiselect("Sector (5 dígitos)", list(sector_labels.keys()))
        macro_selection = st.multiselect("Macro sector", sorted(df["macro_sector"].unique()))
        min_val, max_val = float(df["value_usd"].min()), float(df["value_usd"].max())
        value_range = st.slider("Monto (USD)", min_val, max_val, (min_val, max_val))
        exclude_neg = st.checkbox("Excluir negativos", True)
        show_pct = st.checkbox("Mostrar % del total")
        log_scale = st.checkbox("Escala log en distribuciones")
        top_n = st.slider("Top N", 1, 50, 10)
    # Apply filters
    mask = (df["year"].between(*year_range)) & (df["value_usd"].between(*value_range))
    if exclude_neg:
        mask &= df["value_usd"] >= 0
    if countries:
        mask &= df["recipientcountry_codename"].isin(countries)
    if sources:
        mask &= df["source"].isin(sources)
    if orgs:
        mask &= df["reportingorg_ref"].isin(orgs)
    if sector_selection:
        sectors = [sector_labels[s] for s in sector_selection]
        mask &= df["sector_codename"].isin(sectors)
    if macro_selection:
        mask &= df["macro_sector"].isin(macro_selection)
    df_f = df[mask].copy()
    kpi_block(df_f)

    tabs = st.tabs([
        "Panorama de sectores",
        "Comparador A vs B",
        "Ficha de sector",
        "Matrices de concentración",
        "Intensidad y estructura",
        "Tabla maestro",
    ])

    # -------- Tab 0: Panorama --------
    with tabs[0]:
        df_sector = (
            df_f.groupby("sector_codename")
            .agg(value_usd=("value_usd", "sum"), ops=("iatiidentifier", "count"))
            .sort_values("value_usd", ascending=False)
        )
        df_sector["ticket"] = df_sector["value_usd"] / df_sector["ops"]
        df_top = df_sector.head(top_n).reset_index()
        fig_bar = px.bar(
            df_top,
            x="value_usd",
            y="sector_codename",
            orientation="h",
            labels={"value_usd": "USD", "sector_codename": "Sector"},
            hover_data={"value_usd":":.2f","ops":True,"ticket":":.2f"},
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_bar, use_container_width=True)

        df_macro = df_f.groupby("macro_sector")["value_usd"].sum().reset_index()
        if show_pct and df_macro["value_usd"].sum() != 0:
            df_macro["value"] = df_macro["value_usd"] / df_macro["value_usd"].sum() * 100
            value_col = "value"
            hover_template = "%{label}: %{value:.1f}%"
        else:
            value_col = "value_usd"
            hover_template = "%{label}: %{value:,.2f}"
        fig_donut = px.pie(
            df_macro,
            names="macro_sector",
            values=value_col,
            hole=0.4,
        )
        fig_donut.update_traces(hovertemplate=hover_template)
        st.plotly_chart(fig_donut, use_container_width=True)

        top_sectors = df_sector.head(top_n).index
        df_year_sector = (
            df_f[df_f["sector_codename"].isin(top_sectors)]
            .groupby(["year", "sector_codename"])["value_usd"].sum()
            .reset_index()
        )
        if show_pct:
            total_year = df_f.groupby("year")["value_usd"].sum().reset_index()
            df_year_sector = df_year_sector.merge(total_year, on="year", suffixes=("", "_total"))
            df_year_sector["value_usd"] = df_year_sector["value_usd"] / df_year_sector["value_usd_total"] * 100
            y_label = "% del total"
        else:
            y_label = "USD"
        fig_area = px.area(
            df_year_sector,
            x="year",
            y="value_usd",
            color="sector_codename",
            labels={"year": "Año", "value_usd": y_label, "sector_codename": "Sector"},
        )
        st.plotly_chart(fig_area, use_container_width=True)

    # -------- Tab 1: Comparador A vs B --------
    with tabs[1]:
        sector_list = sorted(df_f["sector_codename"].dropna().unique())
        col1, col2 = st.columns(2)
        with col1:
            sector_a = st.selectbox("Sector A", sector_list, key="sector_a")
        with col2:
            sector_b = st.selectbox("Sector B", sector_list, key="sector_b")
        comp_df = (
            df_f[df_f["sector_codename"].isin([sector_a, sector_b])]
            .groupby(["year", "sector_codename"])["value_usd"].sum()
            .reset_index()
        )
        fig_line = px.line(comp_df, x="year", y="value_usd", color="sector_codename")
        st.plotly_chart(fig_line, use_container_width=True)
        col_a, col_b = st.columns(2)
        for col, sector in zip((col_a, col_b), (sector_a, sector_b)):
            s_df = df_f[df_f["sector_codename"] == sector]
            total = s_df["value_usd"].sum()
            ops = len(s_df)
            ticket = total / ops if ops else 0
            median = s_df["value_usd"].median() if ops else 0
            countries = s_df["recipientcountry_codename"].nunique()
            col.markdown(
                f"**{sector}**\n\n- Total: {total:,.2f}\n- #ops: {ops}\n- Ticket promedio: {ticket:,.2f}\n- Mediana: {median:,.2f}\n- # Países: {countries}"
            )

    # -------- Tab 2: Ficha de sector --------
    with tabs[2]:
        sector_totals = (
            df_f.groupby("sector_codename")["value_usd"].sum().sort_values(ascending=False)
        )
        default_sector = sector_totals.index[0] if not sector_totals.empty else None
        sector_sel = st.selectbox(
            "Sector", sector_totals.index.tolist(), index=0 if default_sector else None
        )
        sec_df = df_f[df_f["sector_codename"] == sector_sel]
        top_countries = (
            sec_df.groupby("recipientcountry_codename")["value_usd"].sum().sort_values(ascending=False).head(top_n).reset_index()
        )
        fig_country = px.bar(
            top_countries,
            x="value_usd",
            y="recipientcountry_codename",
            orientation="h",
            labels={"value_usd": "USD", "recipientcountry_codename": "País"},
        )
        fig_country.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_country, use_container_width=True)

        top_sources = (
            sec_df.groupby("source")["value_usd"].sum().sort_values(ascending=False).head(top_n).reset_index()
        )
        fig_source = px.bar(top_sources, x="source", y="value_usd", labels={"value_usd": "USD", "source": "Fuente"})
        st.plotly_chart(fig_source, use_container_width=True)

        fig_dist = px.box(sec_df, y="value_usd")
        if log_scale:
            fig_dist.update_yaxes(type="log")
        st.plotly_chart(fig_dist, use_container_width=True)

        display_cols = [
            "iatiidentifier",
            "year",
            "recipientcountry_codename",
            "source",
            "value_usd",
        ]
        st.dataframe(sec_df[display_cols])
        csv = sec_df[display_cols].to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, file_name="operaciones_sector.csv", mime="text/csv")
        excel = BytesIO()
        sec_df[display_cols].to_excel(excel, index=False)
        st.download_button(
            "Descargar Excel", excel.getvalue(), file_name="operaciones_sector.xlsx", mime="application/vnd.ms-excel"
        )

    # -------- Tab 3: Matrices --------
    with tabs[3]:
        top_countries = (
            df_f.groupby("recipientcountry_codename")["value_usd"].sum().sort_values(ascending=False).head(top_n).index
        )
        pivot = (
            df_f[df_f["recipientcountry_codename"].isin(top_countries)]
            .pivot_table(
                index="recipientcountry_codename",
                columns="sector_codename",
                values="value_usd",
                aggfunc="sum",
                fill_value=0,
            )
        )
        fig_heat = go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index))
        st.plotly_chart(fig_heat, use_container_width=True)

        pivot2 = (
            df_f.pivot_table(
                index="year",
                columns="macro_sector",
                values="value_usd",
                aggfunc="sum",
                fill_value=0,
            )
        )
        fig_heat2 = go.Figure(data=go.Heatmap(z=pivot2.values, x=pivot2.columns, y=pivot2.index))
        st.plotly_chart(fig_heat2, use_container_width=True)

    # -------- Tab 4: Intensidad y estructura --------
    with tabs[4]:
        bubble_df = (
            df_f.groupby("sector_codename").agg(
                sum_usd=("value_usd", "sum"),
                mean_usd=("value_usd", "mean"),
                ops=("iatiidentifier", "count"),
            )
        ).reset_index()
        fig_bubble = px.scatter(
            bubble_df,
            x="mean_usd",
            y="sum_usd",
            size="ops",
            hover_name="sector_codename",
            labels={"mean_usd": "Ticket promedio", "sum_usd": "Total USD", "ops": "# ops"},
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

        sankey_df = (
            df_f.groupby(["source", "macro_sector", "recipientcountry_codename"])["value_usd"].sum().reset_index()
        )
        sources_nodes = sankey_df["source"].unique().tolist()
        macro_nodes = sankey_df["macro_sector"].unique().tolist()
        country_nodes = sankey_df["recipientcountry_codename"].unique().tolist()
        nodes = sources_nodes + macro_nodes + country_nodes
        node_indices = {name: i for i, name in enumerate(nodes)}
        links = {
            "source": [],
            "target": [],
            "value": [],
        }
        for row in sankey_df.itertuples():
            links["source"].append(node_indices[row.source])
            links["target"].append(node_indices[row.macro_sector])
            links["value"].append(row.value_usd)
        for row in sankey_df.itertuples():
            links["source"].append(node_indices[row.macro_sector])
            links["target"].append(node_indices[row.recipientcountry_codename])
            links["value"].append(row.value_usd)
        fig_sankey = go.Figure(
            go.Sankey(
                node=dict(label=nodes),
                link=dict(
                    source=links["source"], target=links["target"], value=links["value"]
                ),
            )
        )
        st.plotly_chart(fig_sankey, use_container_width=True)

    # -------- Tab 5: Tabla maestro --------
    with tabs[5]:
        cols = [
            "iatiidentifier",
            "transactiondate_isodate",
            "recipientcountry_codename",
            "source",
            "sector_code",
            "sector_codename",
            "value_usd",
        ]
        st.dataframe(df_f[cols])
        total_usd = df_f["value_usd"].sum()
        total_ops = len(df_f)
        st.markdown(f"**Total USD:** {total_usd:,.2f} | **# Operaciones:** {total_ops}")
        csv = df_f[cols].to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, file_name="sectores.csv", mime="text/csv")
        excel = BytesIO()
        df_f[cols].to_excel(excel, index=False)
        st.download_button(
            "Descargar Excel", excel.getvalue(), file_name="sectores.xlsx", mime="application/vnd.ms-excel"
        )
