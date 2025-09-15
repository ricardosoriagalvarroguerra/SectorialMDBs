import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_financiamiento() -> pd.DataFrame:
    df = pd.read_parquet("BDDGLOBALMERGED_ACTUALIZADO.parquet")
    df["transactiondate_isodate"] = pd.to_datetime(df["transactiondate_isodate"])
    df["year"] = df["transactiondate_isodate"].dt.year
    return df

def render() -> None:
    st.title("Financiamiento para el desarrollo")
    df = load_financiamiento()
    if df is None or df.empty:
        st.info("No se pudieron cargar los datos.")
        return
    min_year, max_year = int(df["year"].min()), int(df["year"].max())
    year_range = st.sidebar.slider("Rango de años", min_year, max_year, (min_year, max_year))
    df_f = df[df["year"].between(*year_range)]
    if df_f.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return
    total_by_source = (
        df_f.groupby("source")["value_usd"].sum().sort_values(ascending=False) / 1e6
    )
    fig = px.bar(
        x=total_by_source.index,
        y=total_by_source.values,
        labels={"x": "Fuente", "y": "USD (millones)"},
    )
    st.plotly_chart(fig, use_container_width=True)
