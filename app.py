import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from typing import Optional
from sectores_page import render as render_sectores
from financiamiento_page import render as render_financiamiento

# Paleta unificada para los multilaterales según lineamientos IDS.
MULTILATERAL_COLOR_MAP = {
    "BIS": "#fff15c",
    "BCIE": "#7cc6fe",
    "CAF": "#f4a259",
    "EIB": "#f1d8a7",
    "IDB": "#0b2545",
    "IFAD": "#2d6a4f",
    "IIB": "#5ca06a",
    "IMF": "#2660a4",
    "OPEC": "#386641",
    "FONPLATA": "#af1d1d",
    "World": "#6b6b6b",
    "WB-IBRD": "#c0c5ce",
    "WB-IDA": "#7ba6de",
    "WB-MIGA": "#1f78d1",
    "NDB": "#5e2b97",
    "IFC": "#7f3f98",
}

SC3_COLOR_OVERRIDES = {
    "Bilateral": "#5E7FD7",
    "Multilateral": "#4CAF50",
    "PPG debt: bonds": "#2F3847",
    "Other private creditors": "#7655A6",
    "PPG debt commercial banks": "#D6B23F",
    "International Monetary Fund (IMF)": "#8B2F2F",
}

# Diccionario de regiones
regiones_dict = {
    "Caribe": [
        "Antigua and Barbuda", "Bahamas (the)", "Barbados", "Dominica", "Dominican Republic (the)",
        "Grenada", "Haiti", "Jamaica", "Saint Lucia", "Trinidad and Tobago"
    ],
    "Centroamérica": [
        "Belize", "Costa Rica", "El Salvador", "Guatemala", "Honduras", "Nicaragua", "Panama", "Mexico"
    ],
    "Sudamérica": [
        "Argentina", "Bolivia (Plurinational State of)", "Brazil", "Chile", "Colombia", "Ecuador",
        "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela (Bolivarian Republic of)"
    ]
}

# Función para manejar el comportamiento de multiselect con "Seleccionar todo"
def handle_multiselect_behavior(selected_options, all_options, select_all_text="Seleccionar todo"):
    """
    Maneja el comportamiento de multiselect donde "Seleccionar todo" es exclusivo
    con las opciones individuales.
    
    Args:
        selected_options: Lista de opciones seleccionadas
        all_options: Lista de todas las opciones disponibles (sin "Seleccionar todo")
        select_all_text: Texto de la opción "Seleccionar todo"
    
    Returns:
        Lista de opciones finales a usar para filtrar
    """
    if not selected_options:
        return all_options
    
    # Si solo "Seleccionar todo" está seleccionado, retornar todas las opciones
    if selected_options == [select_all_text]:
        return all_options
    
    # Si hay opciones individuales seleccionadas (con o sin "Seleccionar todo"), 
    # excluir "Seleccionar todo" y retornar solo las opciones individuales
    individual_options = [opt for opt in selected_options if opt != select_all_text]
    if individual_options:
        return individual_options
    
    # Si no hay opciones individuales, retornar todas las opciones
    return all_options


def get_contrasting_text_color(hex_color: str) -> str:
    """Return black or white depending on the perceived brightness of the color."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#FFFFFF"
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "#000000" if brightness > 186 else "#FFFFFF"

# Cargar datos
COUNTRY_COLUMN_EXCLUSIONS = ('PIB', '%')
SPECIAL_COUNTRY_KEYWORDS = ("Costa Rica", "Dominican Republic")


def get_country_columns(dataframe: Optional[pd.DataFrame]) -> list[str]:
    if dataframe is None:
        return []
    return [
        col
        for col in dataframe.columns
        if '[' in col
        and ']' in col
        and not any(col.startswith(prefix) for prefix in COUNTRY_COLUMN_EXCLUSIONS)
    ]


@st.cache_data
def load_data():
    df_ids = pd.read_parquet('IDS.parquet')
    if 'SC3' in df_ids.columns:
        sc3_clean = df_ids['SC3'].astype(str).str.strip().str.lower()
        df_ids = df_ids[~sc3_clean.eq('private')]
    return df_ids


@st.cache_data
def load_special_country_data():
    try:
        df_special = pd.read_parquet('IDS_CRI_DR.parquet')
    except FileNotFoundError:
        return None
    if 'SC3' in df_special.columns:
        sc3_clean = df_special['SC3'].astype(str).str.strip().str.lower()
        df_special = df_special[~sc3_clean.eq('private')]
    return df_special


df = load_data()
df_special = load_special_country_data()
base_country_columns = get_country_columns(df)
special_country_columns = []
if df_special is not None:
    special_country_columns = [
        col
        for col in get_country_columns(df_special)
        if any(keyword in col for keyword in SPECIAL_COUNTRY_KEYWORDS)
    ]
all_country_columns = base_country_columns.copy()
for col in special_country_columns:
    if col not in all_country_columns:
        all_country_columns.append(col)
special_country_set = set(special_country_columns)

# Sidebar para navegación
st.sidebar.title('Navegación')
st.sidebar.markdown('**IDS**')

# Funciones para manejar la navegación y limpiar selección
def set_pagina_from_ids():
    st.session_state['pagina'] = st.session_state['pagina_ids']
    st.session_state['pagina_iati'] = None

def set_pagina_from_iati():
    st.session_state['pagina'] = st.session_state['pagina_iati']

paginas_ids = [
    'Deuda externa',
    'Multilaterales',
    'Plazos y Tasas',
    'Comprometido',
    'Visor BDD',
]

st.sidebar.radio('Ir a:', paginas_ids, key='pagina_ids', on_change=set_pagina_from_ids)

st.sidebar.divider()
st.sidebar.markdown('**IATI**')

paginas_iati = ['Financiamiento para el desarrollo', 'Sectores']
st.sidebar.radio('Ir a:', paginas_iati, key='pagina_iati', index=None, on_change=set_pagina_from_iati)

pagina = st.session_state.get('pagina', st.session_state.get('pagina_ids', 'Deuda externa'))

# Cargar datos IATI
@st.cache_data
def load_iati_data():
    try:
        df = pd.read_parquet('BDDGLOBALMERGED_ACTUALIZADO.parquet')
        df.rename(columns={"macro_sector": "macrosector"}, inplace=True)
        # Ajuste manual para proyecto específico con valor incorrecto
        mask = df['iatiidentifier'] == 'XM-DAC-46027-PY028'
        df.loc[mask, 'value_usd'] = 354200000
        return df
    except Exception:
        return None

df_iati = load_iati_data()


if pagina == 'Deuda externa':
    st.title('Deuda externa')
    # Filtros en la sidebar
    paises = all_country_columns
    pais = st.sidebar.selectbox('Selecciona país', paises)
    use_special_data = df_special is not None and pais in special_country_set
    df_source = df_special if use_special_data else df
    # Filtro adicional para SC4
    sc4_allowed = [
        "General Government",
        "Private Guaranteed by Public Sector",
        "Public and Publicly Guaranteed",
        "Public Sector",
    ]
    sc4_options = [
        opt for opt in sc4_allowed if 'SC4' in df_source.columns and opt in df_source['SC4'].dropna().unique()
    ]
    sc4 = st.sidebar.selectbox('Selecciona SC4', sc4_options) if sc4_options else None
    # Filtro adicional para SC2
    sc2_allowed = [
        "Debt outstanding and disbursed",
        "Disbursements",
        "interest payments",
        "Net flows (DIS - AMT)",
        "Net transfers (NFL - INT)",
        "principal repayments",
        "Total debt service (AMT + INT)",
    ]
    sc2_options = [
        opt for opt in sc2_allowed if 'SC2' in df_source.columns and opt in df_source['SC2'].dropna().unique()
    ]
    sc2 = st.sidebar.selectbox('Selecciona SC2', sc2_options) if sc2_options else None
    df_filtrado = df_source.copy()
    if sc4 is not None:
        df_filtrado = df_filtrado[df_filtrado['SC4'] == sc4]
    if sc2 is not None:
        df_filtrado = df_filtrado[df_filtrado['SC2'] == sc2]
    df_filtrado = df_filtrado[df_filtrado['Time'] <= 2023]
    # Filtro por rango de años
    if 'Time' in df_filtrado.columns and not df_filtrado['Time'].empty:
        min_year = int(df_filtrado['Time'].min())
        max_year = int(df_filtrado['Time'].max())
        year_range = st.sidebar.slider('Rango de años', min_year, max_year, (min_year, max_year), key='deuda_anos')
        df_filtrado = df_filtrado[(df_filtrado['Time'] >= year_range[0]) & (df_filtrado['Time'] <= year_range[1])]
    # Tabla eliminada

    # Graficos para el país seleccionado con Plotly
    st.subheader(f'Gráficos para {pais}')
    import plotly.express as px
    if pais in df_filtrado.columns:
        df_pais = df_filtrado[["SC3", "Time", pais]].dropna()
        df_pais = df_pais[~df_pais["SC3"].str.contains("All creditors", case=False, na=False)]
        excluded_sc3 = {"official", "bilateral concessional", "multilateral concessional"}
        df_pais = df_pais[
            ~df_pais["SC3"].str.strip().str.lower().isin(excluded_sc3)
        ]
        # Tomar el valor máximo por año y SC3 para evitar duplicados (mantiene el valor más significativo)
        df_pais_agg = df_pais.groupby(['Time', 'SC3'])[pais].max().reset_index()
        # Paleta de colores específica para categorías de deuda externa
        sc3_categories = df_pais_agg['SC3'].unique()
        base_palette = [
            '#6A80C4', '#A7B6E2', '#002B8F', '#DC493A', '#FFFFFF',
            '#4392F1', '#E2C3CE', '#715676', '#243156', '#82AFED'
        ]
        fallback_palette = [color for color in base_palette if color not in SC3_COLOR_OVERRIDES.values()]
        extra_palettes = (
            px.colors.qualitative.Plotly
            + px.colors.qualitative.Safe
            + px.colors.qualitative.Set3
            + px.colors.qualitative.Pastel
            + px.colors.qualitative.D3
        )
        for color in extra_palettes:
            if color not in fallback_palette and color not in SC3_COLOR_OVERRIDES.values():
                fallback_palette.append(color)
        sc3_color_map = {}
        fallback_index = 0
        for cat in sc3_categories:
            if cat in SC3_COLOR_OVERRIDES:
                sc3_color_map[cat] = SC3_COLOR_OVERRIDES[cat]
            else:
                if fallback_index >= len(fallback_palette):
                    fallback_palette.append(px.colors.qualitative.Light24[fallback_index % len(px.colors.qualitative.Light24)])
                sc3_color_map[cat] = fallback_palette[fallback_index]
                fallback_index += 1

        st.markdown('**Serie temporal de deuda por SC3 (Stacked Bar)**')
        fig1 = px.bar(
            df_pais_agg,
            x='Time',
            y=pais,
            color='SC3',
            color_discrete_map=sc3_color_map,
            labels={pais: pais, 'Time': 'Año', 'SC3': 'SC3'},
            title='USD',
            height=400
        )
        fig1.update_xaxes(showgrid=False)
        fig1.update_yaxes(showgrid=False, tickformat=',.0f', title_text=f'{pais} (millones USD)')
        fig1.update_yaxes(tickformat='.2s')
        fig1.update_traces(
            hovertemplate="<b>Año:</b> %{x}<br><b>SC3:</b> %{fullData.name}<br><b>Valor:</b> %{y:.2s} USD<extra></extra>"
        )
        fig1.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.8,  # Más separado del gráfico
                xanchor="center",
                x=0.5,
                title_text=''  # Quitar el título de la leyenda
            ),
            title={'text': 'USD', 'x': 0.5, 'xanchor': 'center'}
        )
        st.plotly_chart(fig1, use_container_width=True)
        # Gráfico 100% stacked bar
        total_por_anio = df_pais_agg.groupby('Time')[pais].transform('sum')
        df_pais_agg['proporcion'] = df_pais_agg[pais] / total_por_anio
        fig2 = px.bar(
            df_pais_agg,
            x='Time',
            y='proporcion',
            color='SC3',
            color_discrete_map=sc3_color_map,
            labels={'proporcion': 'Proporción', 'Time': 'Año', 'SC3': 'SC3'},
            title='%',
            height=400
        )
        fig2.update_layout(barmode='stack', yaxis_tickformat='.0%', yaxis_title='Proporción', showlegend=False, title={'text': '%', 'x': 0.5, 'xanchor': 'center'})
        fig2.update_xaxes(showgrid=False)
        fig2.update_yaxes(showgrid=False)
        fig2.update_traces(
            hovertemplate="<b>Año:</b> %{x}<br><b>SC3:</b> %{fullData.name}<br><b>Porcentaje:</b> %{y:.1%}<extra></extra>"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info(f'No se encontró la columna "{pais}" en la base de datos.')

elif pagina == 'Multilaterales':
    st.title('Multilaterales')
    # Filtros país y SC2
    paises = all_country_columns
    pais = st.sidebar.selectbox('Selecciona país', paises)
    use_special_data = df_special is not None and pais in special_country_set
    df_source = df_special if use_special_data else df
    allowed_sc2 = [
        'Debt outstanding and disbursed',
        'Disbursements',
        'interest payments',
        'Net flows (DIS - AMT)',
        'Net transfers (NFL - INT)',
        'principal repayments',
        'Total debt service (AMT + INT)'
    ]
    if 'SC2' in df_source.columns:
        sc2_options = [opt for opt in allowed_sc2 if opt in df_source['SC2'].dropna().unique()]
    else:
        sc2_options = []
    sc2 = st.sidebar.selectbox('Selecciona SC2', sc2_options) if sc2_options else None
    # Filtrado
    df_filtrado = df_source.copy()
    if sc2 is not None:
        df_filtrado = df_filtrado[df_filtrado['SC2'] == sc2]
    df_filtrado = df_filtrado[df_filtrado['Time'] <= 2023]
    # Filtro por rango de años
    if 'Time' in df_filtrado.columns and not df_filtrado['Time'].empty:
        min_year = int(df_filtrado['Time'].min())
        max_year = int(df_filtrado['Time'].max())
        year_range = st.sidebar.slider('Rango de años', min_year, max_year, (min_year, max_year), key='multilaterales_anos')
        df_filtrado = df_filtrado[(df_filtrado['Time'] >= year_range[0]) & (df_filtrado['Time'] <= year_range[1])]
    # El dataframe filtrado por país se usará en los gráficos
    if pais in df_filtrado.columns:
        df_pais = df_filtrado[["Multilateral", "SC3", "Time", pais]].dropna()
        df_pais = df_pais[~df_pais["Multilateral"].str.strip().str.lower().eq("world")]
    else:
        df_pais = None
    # st.dataframe(df_filtrado)  # Opcional: mostrar la tabla filtrada

    # Gráficos solo si hay datos para el país seleccionado
    if df_pais is not None and not df_pais.empty:
        # Tomar el valor máximo por año y multilateral para evitar duplicados (mantiene el valor más significativo)
        df_pais_agg = df_pais.groupby(['Time', 'Multilateral'])[pais].max().reset_index()
        
        import plotly.express as px
        st.subheader(f'Gráficos para {pais}')
        st.markdown('**Serie temporal de deuda por Multilateral (Stacked Bar)**')
        
        fig1 = px.bar(
            df_pais_agg,
            x='Time',
            y=pais,
            color='Multilateral',
            color_discrete_map=MULTILATERAL_COLOR_MAP,
            labels={pais: pais, 'Time': 'Año', 'Multilateral': 'Multilateral'},
            title='USD',
            height=400
        )
        fig1.update_xaxes(showgrid=False)
        fig1.update_yaxes(showgrid=False, tickformat=',.0f', title_text=f'{pais} (millones USD)')
        fig1.update_yaxes(tickformat='.2s')
        fig1.update_traces(
            hovertemplate="<b>Año:</b> %{x}<br><b>Multilateral:</b> %{fullData.name}<br><b>Valor:</b> %{y:.2s} USD<extra></extra>"
        )
        fig1.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.8,
                xanchor="center",
                x=0.5,
                title_text=''
            ),
            title={'text': 'USD', 'x': 0.5, 'xanchor': 'center'}
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Gráfico 100% stacked bar
        total_por_anio = df_pais_agg.groupby('Time')[pais].transform('sum')
        df_pais_agg['proporcion'] = df_pais_agg[pais] / total_por_anio
        fig2 = px.bar(
            df_pais_agg,
            x='Time',
            y='proporcion',
            color='Multilateral',
            color_discrete_map=MULTILATERAL_COLOR_MAP,
            labels={'proporcion': 'Proporción', 'Time': 'Año', 'Multilateral': 'Multilateral'},
            title='%',
            height=400
        )
        fig2.update_layout(barmode='stack', yaxis_tickformat='.0%', yaxis_title='Proporción', showlegend=False, title={'text': '%', 'x': 0.5, 'xanchor': 'center'})
        fig2.update_xaxes(showgrid=False)
        fig2.update_yaxes(showgrid=False)
        fig2.update_traces(
            hovertemplate="<b>Año:</b> %{x}<br><b>Multilateral:</b> %{fullData.name}<br><b>Porcentaje:</b> %{y:.1%}<extra></extra>"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info(f'No se encontró la columna "{pais}" en la base de datos para el SC2 seleccionado.')

elif pagina == 'Plazos y Tasas':
    st.title('Plazos y Tasas')
    # Filtro Multilateral y SC2
    multilaterales = [m for m in df['Multilateral'].dropna().unique() if m.strip().lower() != 'world']
    multilateral = st.sidebar.selectbox('Selecciona Multilateral', multilaterales)
    sc2_allowed = [
        'Average grace period on new external commitments',
        'Average grant element on new external debt commitments',
        'Average interest on new external debt commitments',
        'Average maturity on new external debt commitments',
    ]
    sc2_options = [opt for opt in sc2_allowed if 'SC2' in df.columns and opt in df['SC2'].dropna().unique()]
    sc2 = st.sidebar.selectbox('Selecciona SC2', sc2_options) if sc2_options else None
    df_filtrado = df[df['Multilateral'] == multilateral]
    if sc2 is not None:
        df_filtrado = df_filtrado[df_filtrado['SC2'] == sc2]
    df_filtrado = df_filtrado[df_filtrado['Time'] <= 2023]
    # Filtro por rango de años
    if 'Time' in df_filtrado.columns and not df_filtrado['Time'].empty:
        min_year = int(df_filtrado['Time'].min())
        max_year = int(df_filtrado['Time'].max())
        year_range = st.sidebar.slider('Rango de años', min_year, max_year, (min_year, max_year), key='plazos_anos')
        df_filtrado = df_filtrado[(df_filtrado['Time'] >= year_range[0]) & (df_filtrado['Time'] <= year_range[1])]
    # Definir países
    pais_arg = 'Argentina [ARG]'
    paises_grupo = ['Brazil [BRA]', 'Bolivia [BOL]', 'Paraguay [PRY]']
    # Verificar que existan las columnas
    cols_arg = [col for col in [pais_arg] if col in df_filtrado.columns]
    cols_grupo = [col for col in paises_grupo if col in df_filtrado.columns]
    # Dataframes para gráficos
    df_arg = df_filtrado[['Time'] + cols_arg].dropna()
    df_grupo = df_filtrado[['Time'] + cols_grupo].dropna()

    # Gráficos organizados en filas
    import plotly.express as px

    # Primera fila: Argentina y Bolivia
    col1, col2 = st.columns(2)
    
    if not df_arg.empty:
        # Tomar el valor máximo por año para evitar duplicados (mantiene el valor más significativo)
        df_arg_agg = df_arg.groupby('Time')[pais_arg].max().reset_index()
        with col1:
            st.markdown("<h3 style='text-align: center;'>Argentina</h3>", unsafe_allow_html=True)
            fig_arg = px.bar(df_arg_agg, x='Time', y=pais_arg, title='', color_discrete_sequence=['#fca311'], height=300)
            fig_arg.update_xaxes(showgrid=False, tickangle=45)
            fig_arg.update_yaxes(showgrid=False)
            fig_arg.update_layout(title={'text': '', 'x': 0.5, 'xanchor': 'center'})
            st.plotly_chart(fig_arg, use_container_width=True)
    else:
        with col1:
            st.info('No hay datos para Argentina con el Multilateral seleccionado.')
    
    # Buscar Bolivia en el dataframe
    bolivia_col = 'Bolivia [BOL]'
    if bolivia_col in df_filtrado.columns:
        df_bolivia = df_filtrado[['Time', bolivia_col]].dropna()
        if not df_bolivia.empty:
            # Tomar el valor máximo por año para evitar duplicados (mantiene el valor más significativo)
            df_bolivia_agg = df_bolivia.groupby('Time')[bolivia_col].max().reset_index()
            with col2:
                st.markdown("<h3 style='text-align: center;'>Bolivia</h3>", unsafe_allow_html=True)
                fig_bolivia = px.bar(df_bolivia_agg, x='Time', y=bolivia_col, title='', color_discrete_sequence=['#fca311'], height=300)
                fig_bolivia.update_xaxes(showgrid=False, tickangle=45)
                fig_bolivia.update_yaxes(showgrid=False)
                fig_bolivia.update_layout(title={'text': '', 'x': 0.5, 'xanchor': 'center'})
                st.plotly_chart(fig_bolivia, use_container_width=True)
        else:
            with col2:
                st.info('No hay datos para Bolivia con el Multilateral seleccionado.')
    else:
        with col2:
            st.info('No se encontró la columna de Bolivia.')
    
    # Segunda fila: Brasil y Paraguay
    col3, col4 = st.columns(2)
    
    # Brasil
    brasil_col = 'Brazil [BRA]'
    if brasil_col in df_filtrado.columns:
        df_brasil = df_filtrado[['Time', brasil_col]].dropna()
        if not df_brasil.empty:
            # Tomar el valor máximo por año para evitar duplicados (mantiene el valor más significativo)
            df_brasil_agg = df_brasil.groupby('Time')[brasil_col].max().reset_index()
            with col3:
                st.markdown("<h3 style='text-align: center;'>Brasil</h3>", unsafe_allow_html=True)
                fig_brasil = px.bar(df_brasil_agg, x='Time', y=brasil_col, title='', color_discrete_sequence=['#fca311'], height=300)
                fig_brasil.update_xaxes(showgrid=False, tickangle=45)
                fig_brasil.update_yaxes(showgrid=False)
                fig_brasil.update_layout(title={'text': '', 'x': 0.5, 'xanchor': 'center'})
                st.plotly_chart(fig_brasil, use_container_width=True)
        else:
            with col3:
                st.info('No hay datos para Brasil con el Multilateral seleccionado.')
    else:
        with col3:
            st.info('No se encontró la columna de Brasil.')
    
    # Paraguay
    paraguay_col = 'Paraguay [PRY]'
    if paraguay_col in df_filtrado.columns:
        df_paraguay = df_filtrado[['Time', paraguay_col]].dropna()
        if not df_paraguay.empty:
            # Tomar el valor máximo por año para evitar duplicados (mantiene el valor más significativo)
            df_paraguay_agg = df_paraguay.groupby('Time')[paraguay_col].max().reset_index()
            with col4:
                st.markdown("<h3 style='text-align: center;'>Paraguay</h3>", unsafe_allow_html=True)
                fig_paraguay = px.bar(df_paraguay_agg, x='Time', y=paraguay_col, title='', color_discrete_sequence=['#fca311'], height=300)
                fig_paraguay.update_xaxes(showgrid=False, tickangle=45)
                fig_paraguay.update_yaxes(showgrid=False)
                fig_paraguay.update_layout(title={'text': '', 'x': 0.5, 'xanchor': 'center'})
                st.plotly_chart(fig_paraguay, use_container_width=True)
        else:
            with col4:
                st.info('No hay datos para Paraguay con el Multilateral seleccionado.')
    else:
        with col4:
            st.info('No se encontró la columna de Paraguay.')

elif pagina == 'Comprometido':
    st.title('Comprometido')

    # Filtrar por SC2 = "Commitments"
    df_comprometido = df[df['SC2'] == 'Commitments'].copy()
    df_comprometido = df_comprometido[~df_comprometido['Multilateral'].str.strip().str.lower().eq('world')]
    df_comprometido = df_comprometido[df_comprometido['Time'] <= 2023]
    # Filtro por rango de años
    if 'Time' in df_comprometido.columns and not df_comprometido['Time'].empty:
        min_year = int(df_comprometido['Time'].min())
        max_year = int(df_comprometido['Time'].max())
        year_range = st.sidebar.slider('Rango de años', min_year, max_year, (min_year, max_year), key='comprometido_anos')
        df_comprometido = df_comprometido[(df_comprometido['Time'] >= year_range[0]) & (df_comprometido['Time'] <= year_range[1])]
    
    # Definir países
    paises = ['Argentina [ARG]', 'Bolivia [BOL]', 'Brazil [BRA]', 'Paraguay [PRY]']
    
    # Verificar que existan las columnas de países
    paises_disponibles = [pais for pais in paises if pais in df_comprometido.columns]
    
    if paises_disponibles:
        import plotly.express as px

        # Primera fila: Argentina y Bolivia
        col1, col2 = st.columns(2)
        
        # Argentina
        if 'Argentina [ARG]' in paises_disponibles:
            df_arg = df_comprometido[["Multilateral", "Time", "Argentina [ARG]"]].dropna()
            if not df_arg.empty:
                # Tomar el valor máximo por año y multilateral para evitar duplicados (mantiene el valor más significativo)
                df_arg_agg = df_arg.groupby(['Time', 'Multilateral'])['Argentina [ARG]'].max().reset_index()
                with col1:
                    st.markdown("<h3 style='text-align: center;'>Argentina</h3>", unsafe_allow_html=True)
                    fig_arg = px.bar(
                        df_arg_agg,
                        x='Time',
                        y='Argentina [ARG]',
                        color='Multilateral',
                        color_discrete_map=MULTILATERAL_COLOR_MAP,
                        title='USD',
                        height=300
                    )
                    fig_arg.update_xaxes(showgrid=False, tickangle=45)
                    fig_arg.update_yaxes(showgrid=False, tickformat='.2s', title_text='Argentina [ARG] (millones USD)')
                    fig_arg.update_traces(
                        hovertemplate="<b>Año:</b> %{x}<br><b>Multilateral:</b> %{fullData.name}<br><b>Valor:</b> %{y:.2s} USD<extra></extra>"
                    )
                    fig_arg.update_layout(
                        title={'text': 'USD', 'x': 0.5, 'xanchor': 'center'},
                        showlegend=False
                    )
                    st.plotly_chart(fig_arg, use_container_width=True)
            else:
                with col1:
                    st.info('No hay datos para Argentina con SC2 = Commitments.')
        else:
            with col1:
                st.info('No se encontró la columna de Argentina.')
        
        # Bolivia
        if 'Bolivia [BOL]' in paises_disponibles:
            df_bol = df_comprometido[["Multilateral", "Time", "Bolivia [BOL]"]].dropna()
            if not df_bol.empty:
                # Tomar el valor máximo por año y multilateral para evitar duplicados (mantiene el valor más significativo)
                df_bol_agg = df_bol.groupby(['Time', 'Multilateral'])['Bolivia [BOL]'].max().reset_index()
                with col2:
                    st.markdown("<h3 style='text-align: center;'>Bolivia</h3>", unsafe_allow_html=True)
                    fig_bol = px.bar(
                        df_bol_agg,
                        x='Time',
                        y='Bolivia [BOL]',
                        color='Multilateral',
                        color_discrete_map=MULTILATERAL_COLOR_MAP,
                        title='USD',
                        height=300
                    )
                    fig_bol.update_xaxes(showgrid=False, tickangle=45)
                    fig_bol.update_yaxes(showgrid=False, tickformat='.2s', title_text='Bolivia [BOL] (millones USD)')
                    fig_bol.update_traces(
                        hovertemplate="<b>Año:</b> %{x}<br><b>Multilateral:</b> %{fullData.name}<br><b>Valor:</b> %{y:.2s} USD<extra></extra>"
                    )
                    fig_bol.update_layout(
                        title={'text': 'USD', 'x': 0.5, 'xanchor': 'center'},
                        showlegend=False
                    )
                    st.plotly_chart(fig_bol, use_container_width=True)
            else:
                with col2:
                    st.info('No hay datos para Bolivia con SC2 = Commitments.')
        else:
            with col2:
                st.info('No se encontró la columna de Bolivia.')
        
        # Segunda fila: Brasil y Paraguay
        col3, col4 = st.columns(2)
        
        # Brasil
        if 'Brazil [BRA]' in paises_disponibles:
            df_bra = df_comprometido[["Multilateral", "Time", "Brazil [BRA]"]].dropna()
            if not df_bra.empty:
                # Tomar el valor máximo por año y multilateral para evitar duplicados (mantiene el valor más significativo)
                df_bra_agg = df_bra.groupby(['Time', 'Multilateral'])['Brazil [BRA]'].max().reset_index()
                with col3:
                    st.markdown("<h3 style='text-align: center;'>Brasil</h3>", unsafe_allow_html=True)
                    fig_bra = px.bar(
                        df_bra_agg,
                        x='Time',
                        y='Brazil [BRA]',
                        color='Multilateral',
                        color_discrete_map=MULTILATERAL_COLOR_MAP,
                        title='USD',
                        height=300
                    )
                    fig_bra.update_xaxes(showgrid=False, tickangle=45)
                    fig_bra.update_yaxes(showgrid=False, tickformat='.2s', title_text='Brazil [BRA] (millones USD)')
                    fig_bra.update_traces(
                        hovertemplate="<b>Año:</b> %{x}<br><b>Multilateral:</b> %{fullData.name}<br><b>Valor:</b> %{y:.2s} USD<extra></extra>"
                    )
                    fig_bra.update_layout(
                        title={'text': 'USD', 'x': 0.5, 'xanchor': 'center'},
                        showlegend=False
                    )
                    st.plotly_chart(fig_bra, use_container_width=True)
            else:
                with col3:
                    st.info('No hay datos para Brasil con SC2 = Commitments.')
        else:
            with col3:
                st.info('No se encontró la columna de Brasil.')
        
        # Paraguay
        if 'Paraguay [PRY]' in paises_disponibles:
            df_pry = df_comprometido[["Multilateral", "Time", "Paraguay [PRY]"]].dropna()
            if not df_pry.empty:
                # Tomar el valor máximo por año y multilateral para evitar duplicados (mantiene el valor más significativo)
                df_pry_agg = df_pry.groupby(['Time', 'Multilateral'])['Paraguay [PRY]'].max().reset_index()
                with col4:
                    st.markdown("<h3 style='text-align: center;'>Paraguay</h3>", unsafe_allow_html=True)
                    fig_pry = px.bar(
                        df_pry_agg,
                        x='Time',
                        y='Paraguay [PRY]',
                        color='Multilateral',
                        color_discrete_map=MULTILATERAL_COLOR_MAP,
                        title='USD',
                        height=300
                    )
                    fig_pry.update_xaxes(showgrid=False, tickangle=45)
                    fig_pry.update_yaxes(showgrid=False, tickformat='.2s', title_text='Paraguay [PRY] (millones USD)')
                    fig_pry.update_traces(
                        hovertemplate="<b>Año:</b> %{x}<br><b>Multilateral:</b> %{fullData.name}<br><b>Valor:</b> %{y:.2s} USD<extra></extra>"
                    )
                    fig_pry.update_layout(
                        title={'text': 'USD', 'x': 0.5, 'xanchor': 'center'},
                        showlegend=False
                    )
                    st.plotly_chart(fig_pry, use_container_width=True)
            else:
                with col4:
                    st.info('No hay datos para Paraguay con SC2 = Commitments.')
        else:
            with col4:
                st.info('No se encontró la columna de Paraguay.')
    
    else:
        st.info('No se encontraron datos con SC2 = "Commitments" para los países especificados.')

elif pagina == 'Visor BDD':
    st.title('Visor BDD')
    # Parámetros de paginación
    page_size = 10  # Observaciones por página
    total_rows = len(df)
    total_pages = (total_rows - 1) // page_size + 1

    page = st.number_input(
        'Página',
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
        help=f"Total de páginas: {total_pages}"
    )

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    st.dataframe(df.iloc[start_idx:end_idx])
    st.caption(f"Mostrando filas {start_idx+1} a {min(end_idx, total_rows)} de {total_rows}")

elif pagina == 'Financiamiento para el desarrollo':
    render_financiamiento()
elif pagina == 'Sectores':
    render_sectores()
