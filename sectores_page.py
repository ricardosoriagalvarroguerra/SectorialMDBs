import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pandas.api.types import is_string_dtype
from io import StringIO, BytesIO


def normalize_name(s: str) -> str:
    """Normalize sector names for mapping."""
    if s is None:
        return ""
    s = s.casefold().strip().replace("-", " ").replace("/", " ")
    return " ".join(s.split())


MACRO_MAP_RAW = {
    # --- Social ---
    "Advanced technical and managerial training": "Social",
    "Basic health care": "Social",
    "Basic health infrastructure": "Social",
    "Basic life skills for youth": "Social",
    "Basic nutrition": "Social",
    "Civil service pensions": "Social",
    "Early childhood education": "Social",
    "Education facilities and training": "Social",
    "Education policy and administrative management": "Social",
    "Educational research": "Social",
    "Employment creation": "Social",
    "Family planning": "Social",
    "General pensions": "Social",
    "Health education": "Social",
    "Health personnel development": "Social",
    "Health policy and administrative management": "Social",
    "Higher education": "Social",
    "Housing policy and administrative management": "Social",
    "Infectious disease control": "Social",
    "Low-cost housing": "Social",
    "Lower secondary education": "Social",
    "Malaria control": "Social",
    "Medical education/training": "Social",
    "Medical services": "Social",
    "Multisector aid for basic social services": "Social",
    "Narcotics control": "Social",
    "Population policy and administrative management": "Social",
    "Primary education": "Social",
    "Recreation and sport": "Social",
    "Reproductive health care": "Social",
    "STD control including HIV/AIDS": "Social",
    "Social Protection": "Social",
    "Social mitigation of HIV/AIDS": "Social",
    "Social protection and welfare services policy, planning and administration": "Social",
    "Social services (incl youth development and women+ children)": "Social",
    "Statistical capacity building": "Social",
    "Teacher training": "Social",
    "Tuberculosis control": "Social",
    "Upper Secondary Education (modified and includes data from 11322)": "Social",
    "Vocational training": "Social",
    # --- Infraestructura ---
    "Air transport": "Infraestructura",
    "Basic drinking water supply": "Infraestructura",
    "Basic drinking water supply and basic sanitation": "Infraestructura",
    "Basic sanitation": "Infraestructura",
    "Biofuel-fired power plants": "Infraestructura",
    "Communications policy and administrative management": "Infraestructura",
    "Communications policy, planning and administration": "Infraestructura",
    "Education and training in water supply and sanitation": "Infraestructura",
    "Electric power transmission and distribution (centralised grids)": "Infraestructura",
    "Electrical transmission/ distribution": "Infraestructura",
    "Energy conservation and demand-side efficiency": "Infraestructura",
    "Energy generation, non-renewable sources, unspecified": "Infraestructura",
    "Energy generation, renewable sources - multiple technologies": "Infraestructura",
    "Energy policy and administrative management": "Infraestructura",
    "Energy sector policy, planning and administration": "Infraestructura",
    "Feeder road construction": "Infraestructura",
    "Geothermal energy": "Infraestructura",
    "Hydro-electric power plants": "Infraestructura",
    "Information and communication technology (ICT)": "Infraestructura",
    "Information services": "Infraestructura",
    "National road construction": "Infraestructura",
    "Power generation/non-renewable sources": "Infraestructura",
    "Power generation/renewable sources": "Infraestructura",
    "Public transport services": "Infraestructura",
    "Rail transport": "Infraestructura",
    "Retail gas distribution": "Infraestructura",
    "River basins development": "Infraestructura",
    "Road transport": "Infraestructura",
    "Sanitation - large systems": "Infraestructura",
    "Solar energy for centralised grids": "Infraestructura",
    "Telecommunications": "Infraestructura",
    "Transport policy and administrative management": "Infraestructura",
    "Transport policy, planning and administration": "Infraestructura",
    "Transport regulation": "Infraestructura",
    "Waste management/disposal": "Infraestructura",
    "Water resources conservation (including data collection)": "Infraestructura",
    "Water sector policy and administrative management": "Infraestructura",
    "Water supply - large systems": "Infraestructura",
    "Water supply and sanitation - large systems": "Infraestructura",
    "Water transport": "Infraestructura",
    # --- Productivo ---
    "Agricultural alternative development": "Productivo",
    "Agricultural co-operatives": "Productivo",
    "Agricultural development": "Productivo",
    "Agricultural education/training": "Productivo",
    "Agricultural extension": "Productivo",
    "Agricultural financial services": "Productivo",
    "Agricultural inputs": "Productivo",
    "Agricultural land resources": "Productivo",
    "Agricultural policy and administrative management": "Productivo",
    "Agricultural research": "Productivo",
    "Agricultural services": "Productivo",
    "Agricultural water resources": "Productivo",
    "Agro-industries": "Productivo",
    "Business policy and administration": "Productivo",
    "Coal": "Productivo",
    "Construction policy and administrative management": "Productivo",
    "Fishery development": "Productivo",
    "Fishery research": "Productivo",
    "Fishery services": "Productivo",
    "Fishing policy and administrative management": "Productivo",
    "Food crop production": "Productivo",
    "Forestry development": "Productivo",
    "Forestry policy and administrative management": "Productivo",
    "Forestry research": "Productivo",
    "Forestry services": "Productivo",
    "Industrial development": "Productivo",
    "Industrial policy and administrative management": "Productivo",
    "Livestock": "Productivo",
    "Livestock/veterinary services": "Productivo",
    "Mineral prospection and exploration": "Productivo",
    "Mineral/mining policy and administrative management": "Productivo",
    "Oil and gas (upstream)": "Productivo",
    "Plant and post-harvest protection and pest control": "Productivo",
    "Privatisation": "Productivo",
    "Responsible business conduct": "Productivo",
    "Small and medium-sized enterprises (SME) development": "Productivo",
    "Technological research and development": "Productivo",
    "Tourism policy and administrative management": "Productivo",
    "Trade education/training": "Productivo",
    "Trade facilitation": "Productivo",
    "Trade policy and administrative management": "Productivo",
    # --- Financiero ---
    "Financial policy and administrative management": "Financiero",
    "Formal sector financial intermediaries": "Financiero",
    "Informal/semi-formal financial intermediaries": "Financiero",
    "Monetary institutions": "Financiero",
    # --- Ambiente y Clima ---
    "Biodiversity": "Ambiente y Clima",
    "Biosphere protection": "Ambiente y Clima",
    "Environmental policy and administrative management": "Ambiente y Clima",
    "Environmental research": "Ambiente y Clima",
    "Flood prevention/control": "Ambiente y Clima",
    "Site preservation": "Ambiente y Clima",
    # --- Multisector ---
    "Disaster Risk Reduction": "Multisector",
    "Multisector aid": "Multisector",
    "Rural development": "Multisector",
    "Rural land policy and management": "Multisector",
    "Urban development": "Multisector",
    "Urban development and management": "Multisector",
    "Urban land policy and management": "Multisector",
    # --- Programático y Deuda ---
    "General budget support-related aid": "Programático y Deuda",
    # --- Institucional y Gobernanza ---
    "Anti-corruption organisations and institutions": "Institucional y Gobernanza",
    "Budget planning": "Institucional y Gobernanza",
    "Civilian peace-building, conflict prevention and resolution": "Institucional y Gobernanza",
    "Debt and aid management": "Institucional y Gobernanza",
    "Decentralisation and support to subnational government": "Institucional y Gobernanza",
    "Democratic participation and civil society": "Institucional y Gobernanza",
    "Domestic revenue mobilisation": "Institucional y Gobernanza",
    "Ending violence against women and girls": "Institucional y Gobernanza",
    "Foreign affairs": "Institucional y Gobernanza",
    "Human rights": "Institucional y Gobernanza",
    "Immigration": "Institucional y Gobernanza",
    "Justice, law and order policy, planning and administration": "Institucional y Gobernanza",
    "Legal and judicial development": "Institucional y Gobernanza",
    "Local government administration": "Institucional y Gobernanza",
    "Local government finance": "Institucional y Gobernanza",
    "Macroeconomic policy": "Institucional y Gobernanza",
    "National monitoring and evaluation": "Institucional y Gobernanza",
    "Other central transfers to institutions": "Institucional y Gobernanza",
    "Other general public services": "Institucional y Gobernanza",
    "Public Procurement": "Institucional y Gobernanza",
    "Public finance management (PFM)": "Institucional y Gobernanza",
    "Public sector policy and administrative management": "Institucional y Gobernanza",
    "Security system management and reform": "Institucional y Gobernanza",
    "Tax collection": "Institucional y Gobernanza",
    "Tax policy and administration support": "Institucional y Gobernanza",
    "Women's rights organisations and movements, and government institutions": "Institucional y Gobernanza",
    # --- Emergencia ---
    "Disaster prevention and preparedness": "Emergencia",
    "Immediate post-emergency reconstruction and rehabilitation": "Emergencia",
    "Material relief assistance and services": "Emergencia",
    "Multi-hazard response preparedness": "Emergencia",
    "Relief co-ordination and support services": "Emergencia",
    # --- Administrativo / No asignado ---
    "Sectors not specified": "Administrativo / No asignado",
    # --- No clasificado ---
    "Agriculture": "No clasificado",
    "Banking & Financial Services": "No clasificado",
    "Communications": "No clasificado",
    "ENERGY GENERATION AND SUPPLY": "No clasificado",
    "Education, Level Unspecified": "No clasificado",
    "Government & Civil Society-general": "No clasificado",
    "Health, General": "No clasificado",
    "Industry": "No clasificado",
    "Other Multisector": "No clasificado",
    "Other Social Infrastructure & Services": "No clasificado",
    "Transport & Storage": "No clasificado",
    "Water Supply & Sanitation": "No clasificado",
}

MACRO_MAP = {normalize_name(k): v for k, v in MACRO_MAP_RAW.items()}


@st.cache_data
def load_sectores() -> pd.DataFrame:
    df = pd.read_parquet("sectores.parquet")
    df["transactiondate_isodate"] = pd.to_datetime(df["transactiondate_isodate"])
    if is_string_dtype(df["sector_code"]):
        df["sector_code"] = pd.to_numeric(df["sector_code"], errors="coerce")
    df["sector_code"] = df["sector_code"].astype("Int64")
    df["year"] = df["transactiondate_isodate"].dt.year
    df["month"] = df["transactiondate_isodate"].dt.to_period("M").astype(str)
    df["macro_sector"] = df["sector_codename"].map(
        lambda s: MACRO_MAP.get(normalize_name(s), "No clasificado")
    )
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
        sector_list = sorted(df_f["sector_codename"].unique())
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
