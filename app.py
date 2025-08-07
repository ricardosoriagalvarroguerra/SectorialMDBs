import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Diccionario de macrosectores
macrosectores_dict = {
    "Social": [
        "Health", "Health education", "Health personnel development", "Health policy and administrative management",
        "Basic health care", "Basic health infrastructure", "Medical services", "Medical education/training",
        "Reproductive health care", "STD control including HIV/AIDS", "Malaria control", "Tuberculosis control",
        "Basic nutrition", "Family planning",
        "Education", "Education facilities and training", "Education policy and administrative management", "Early childhood education",
        "Higher education", "Lower secondary education", "Upper Secondary Education (modified and includes data from 11322)",
        "Teacher training", "Trade education/training", "Vocational training", "Educational research",
        "Basic life skills for youth", "Recreation and sport",
        "Social protection", "Social protection and welfare services policy, planning and administration",
        "Social services (incl youth development and women+ children)", "Civil service pensions", "General pensions"
    ],
    "Productivo": [
        "Agriculture, forestry and fishing", "Agricultural development", "Agricultural co-operatives", "Agricultural extension",
        "Agricultural education/training", "Agricultural inputs", "Agricultural land resources", "Agricultural alternative development",
        "Agricultural policy and administrative management", "Agricultural financial services", "Agricultural research", "Agricultural services",
        "Agricultural water resources", "Agro-industries", "Livestock", "Fishery development", "Fishery services", "Fishing policy and administrative management",
        "Forestry development", "Forestry policy and administrative management",
        "Industry, mining, construction", "Industrial development", "Industrial policy and administrative management", "Technological research and development",
        "Business policy and administration", "Small and medium-sized enterprises (SME) development",
        "Tourism policy and administrative management", "Responsible business conduct",
        "Banking and financial services", "Formal sector financial intermediaries", "Informal/semi-formal financial intermediaries", "Monetary institutions",
        "Financial policy and administrative management", "Retail gas distribution"
    ],
    "Infraestructura": [
        "Transport and storage", "Transport policy, planning and administration", "Transport regulation", "Feeder road construction", "National road construction",
        "Rail transport", "Water transport", "Air transport", "Public transport services",
        "Water supply and sanitation", "Water supply and sanitation - large systems", "Basic drinking water supply", "Basic drinking water supply and basic sanitation",
        "Basic sanitation", "Sanitation - large systems", "Waste management/disposal", "Water supply - large systems",
        "Electric power transmission and distribution (centralised grids)", "Energy generation and supply", "Energy generation, renewable sources - multiple technologies",
        "Energy sector policy, planning and administration", "Energy conservation and demand-side efficiency", "Hydro-electric power plants", "Geothermal energy",
        "Oil and gas (upstream)", "Solar energy for centralised grids", "Construction policy and administrative management",
        "Information and communication technology (ICT)", "Telecommunications", "Communications policy, planning and administration",
        "Urban development", "Urban land policy and management", "Rural development", "Rural land policy and management",
        "Low-cost housing", "Housing policy and administrative management"
    ],
    "Ambiental": [
        "Environmental policy and administrative management", "Environmental research", "Biodiversity", "Biosphere protection", "Flood prevention/control",
        "Disaster Risk Reduction", "Disaster prevention and preparedness", "Multi-hazard response preparedness",
        "Water resources conservation (including data collection)", "River basins development", "Site preservation"
    ],
    "Gobernanza/Público": [
        "Public sector policy and administrative management", "Budget planning", "General budget support-related aid",
        "Macroeconomic policy", "Debt and aid management", "Other general public services", "Other central transfers to institutions",
        "National monitoring and evaluation", "Justice, law and order policy, planning and administration", "Civilian peace-building, conflict prevention and resolution",
        "Security system management and reform", "Immigration", "Human rights", "Democratic participation and civil society",
        "Anti-corruption organisations and institutions", "Ending violence against women and girls", "Women's rights organisations and movements, and government institutions",
        "Foreign affairs", "Tax collection", "Tax policy and administration support", "Local government administration", "Local government finance",
        "Privatisation"
    ],
    "Multisectorial/Otros": [
        "Other multisector", "Sectors not specified", "Multisector aid for basic social services", "Immediate post-emergency reconstruction and rehabilitation",
        "Material relief assistance and services", "Relief co-ordination and support services"
    ]
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

# Función para obtener el macrosector de un sector
def get_macrosector(sector_name):
    """Retorna el macrosector al que pertenece un sector específico"""
    for macrosector, sectors in macrosectores_dict.items():
        if sector_name in sectors:
            return macrosector
    return "No clasificado"

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

# Cargar datos
@st.cache_data
def load_data():
    return pd.read_parquet('IDS.parquet')

df = load_data()

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

st.sidebar.radio('Ir a:', ['Transacciones'], key='pagina_iati', index=None, on_change=set_pagina_from_iati)

pagina = st.session_state.get('pagina', st.session_state.get('pagina_ids', 'Deuda externa'))

# Cargar datos IATI
@st.cache_data
def load_iati_data():
    try:
        return pd.read_parquet('BDDGLOBALMERGED_ACTUALIZADO.parquet')
    except:
        return None

df_iati = load_iati_data()

if pagina == 'Deuda externa':
    st.title('Deuda externa')
    # Filtros en la sidebar
    paises = [col for col in df.columns if '[' in col and ']' in col and not col.startswith('PIB') and not col.startswith('%')]
    pais = st.sidebar.selectbox('Selecciona país', paises)
    # Filtro adicional para SC4
    sc4_options = df['SC4'].dropna().unique() if 'SC4' in df.columns else []
    sc4 = st.sidebar.selectbox('Selecciona SC4', sc4_options) if len(sc4_options) > 0 else None
    # Filtro adicional para SC2
    sc2_options = df['SC2'].dropna().unique() if 'SC2' in df.columns else []
    sc2 = st.sidebar.selectbox('Selecciona SC2', sc2_options) if len(sc2_options) > 0 else None
    df_filtrado = df.copy()
    if sc4 is not None:
        df_filtrado = df_filtrado[df_filtrado['SC4'] == sc4]
    if sc2 is not None:
        df_filtrado = df_filtrado[df_filtrado['SC2'] == sc2]
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
        # Tomar el valor máximo por año y SC3 para evitar duplicados (mantiene el valor más significativo)
        df_pais_agg = df_pais.groupby(['Time', 'SC3'])[pais].max().reset_index()
        st.markdown('**Serie temporal de deuda por SC3 (Stacked Bar)**')
        fig1 = px.bar(
            df_pais_agg,
            x='Time',
            y=pais,
            color='SC3',
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
    paises = [col for col in df.columns if '[' in col and ']' in col and not col.startswith('PIB') and not col.startswith('%')]
    pais = st.sidebar.selectbox('Selecciona país', paises)
    sc2_options = df['SC2'].dropna().unique() if 'SC2' in df.columns else []
    sc2 = st.sidebar.selectbox('Selecciona SC2', sc2_options) if len(sc2_options) > 0 else None
    # Filtrado
    df_filtrado = df.copy()
    if sc2 is not None:
        df_filtrado = df_filtrado[df_filtrado['SC2'] == sc2]
    # Filtro por rango de años
    if 'Time' in df_filtrado.columns and not df_filtrado['Time'].empty:
        min_year = int(df_filtrado['Time'].min())
        max_year = int(df_filtrado['Time'].max())
        year_range = st.sidebar.slider('Rango de años', min_year, max_year, (min_year, max_year), key='multilaterales_anos')
        df_filtrado = df_filtrado[(df_filtrado['Time'] >= year_range[0]) & (df_filtrado['Time'] <= year_range[1])]
    # El dataframe filtrado por país se usará en los gráficos
    if pais in df_filtrado.columns:
        df_pais = df_filtrado[["Multilateral", "SC3", "Time", pais]].dropna()
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
        
        # Definir colores consistentes para multilaterales
        multilateral_colors = {
            'BIS': '#1f77b4',      # Azul
            'CAF': '#ff7f0e',      # Naranja
            'EIB': '#2ca02c',      # Verde
            'IDB': '#d62728',      # Rojo
            'IFAD': '#9467bd',     # Púrpura
            'IIB': '#8c564b',      # Marrón
            'IMF': '#e377c2',      # Rosa
            'OPEC': '#7f7f7f',     # Gris
            'FONPLATA': '#bcbd22', # Amarillo verdoso
            'World': '#17becf',    # Cian
            'WB-IBRD': '#ff9896',  # Rosa claro
            'WB-IDA': '#98df8a',   # Verde claro
            'WB-MIGA': '#ffbb78'   # Naranja claro
        }
        
        fig1 = px.bar(
            df_pais_agg,
            x='Time',
            y=pais,
            color='Multilateral',
            color_discrete_map=multilateral_colors,
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
            color_discrete_map=multilateral_colors,
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
    multilaterales = df['Multilateral'].dropna().unique()
    multilateral = st.sidebar.selectbox('Selecciona Multilateral', multilaterales)
    sc2_options = df['SC2'].dropna().unique() if 'SC2' in df.columns else []
    sc2 = st.sidebar.selectbox('Selecciona SC2', sc2_options) if len(sc2_options) > 0 else None
    df_filtrado = df[df['Multilateral'] == multilateral]
    if sc2 is not None:
        df_filtrado = df_filtrado[df_filtrado['SC2'] == sc2]
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
    from streamlit import columns
    
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
    # Filtro por rango de años
    if 'Time' in df_comprometido.columns and not df_comprometido['Time'].empty:
        min_year = int(df_comprometido['Time'].min())
        max_year = int(df_comprometido['Time'].max())
        year_range = st.sidebar.slider('Rango de años', min_year, max_year, (min_year, max_year), key='comprometido_anos')
        df_comprometido = df_comprometido[(df_comprometido['Time'] >= year_range[0]) & (df_comprometido['Time'] <= year_range[1])]
    
    # Definir colores consistentes para multilaterales (mismo que en la página de multilaterales)
    multilateral_colors = {
        'BIS': '#1f77b4',      # Azul
        'CAF': '#ff7f0e',      # Naranja
        'EIB': '#2ca02c',      # Verde
        'IDB': '#d62728',      # Rojo
        'IFAD': '#9467bd',     # Púrpura
        'IIB': '#8c564b',      # Marrón
        'IMF': '#e377c2',      # Rosa
        'OPEC': '#7f7f7f',     # Gris
        'FONPLATA': '#bcbd22', # Amarillo verdoso
        'World': '#17becf',    # Cian
        'WB-IBRD': '#ff9896',  # Rosa claro
        'WB-IDA': '#98df8a',   # Verde claro
        'WB-MIGA': '#ffbb78'   # Naranja claro
    }
    
    # Definir países
    paises = ['Argentina [ARG]', 'Bolivia [BOL]', 'Brazil [BRA]', 'Paraguay [PRY]']
    
    # Verificar que existan las columnas de países
    paises_disponibles = [pais for pais in paises if pais in df_comprometido.columns]
    
    if paises_disponibles:
        import plotly.express as px
        from streamlit import columns
        
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
                        color_discrete_map=multilateral_colors,
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
                        color_discrete_map=multilateral_colors,
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
                        color_discrete_map=multilateral_colors,
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
                        color_discrete_map=multilateral_colors,
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

elif pagina == 'Transacciones':
    st.title('Transacciones IATI')
    st.markdown("---")
    
    # Filtros desplegables en el sidebar para la página de Transacciones
    if df_iati is not None:
        # Crear un selectbox para elegir la subpágina activa
        subpage_active = st.sidebar.selectbox(
            "Subpágina activa:",
            ["Financiadores", "Países"],
            index=0,
            key="transacciones_subpage_select"
        )
        st.session_state['subpage_active'] = subpage_active

        # Mostrar filtros según la subpágina seleccionada
        if subpage_active == "Financiadores":
            st.sidebar.markdown("---")
            st.sidebar.subheader("Filtros (Financiadores)")
            
            # Slider de años
            selected_years = st.sidebar.slider(
                "Rango de Años:",
                min_value=2010,
                max_value=2024,
                value=(2010, 2024),
                step=1,
                key="transacciones_years_slider"
            )
            st.session_state['selected_years'] = selected_years
            
            # Obtener datos filtrados para los filtros
            outgoing_commitments = df_iati[df_iati['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
            if len(outgoing_commitments) > 0:
                # Convertir la columna de fecha
                outgoing_commitments['transactiondate_isodate'] = pd.to_datetime(outgoing_commitments['transactiondate_isodate'])
                
                # Filtrar por años seleccionados
                outgoing_commitments = outgoing_commitments[
                    (outgoing_commitments['transactiondate_isodate'].dt.year >= selected_years[0]) & 
                    (outgoing_commitments['transactiondate_isodate'].dt.year <= selected_years[1])
                ]
                
                # Filtro de regiones
                selected_region = st.sidebar.selectbox(
                    "Seleccionar Región:",
                    ["Todas las regiones"] + list(regiones_dict.keys()),
                    index=0,
                    key="transacciones_region_select"
                )
                st.session_state['selected_region'] = selected_region
                
                # Filtro de países basado en la región seleccionada
                if selected_region != "Todas las regiones" and 'recipientcountry_codename' in outgoing_commitments.columns:
                    # Filtrar países por la región seleccionada
                    paises_region = regiones_dict[selected_region]
                    countries_in_region = [country for country in outgoing_commitments['recipientcountry_codename'].dropna().astype(str).unique() 
                                         if country in paises_region]
                    countries = sorted(countries_in_region)
                    
                    # Agregar opción "Todos" al inicio
                    countries_with_all = ["Todos"] + countries
                    
                    selected_countries = st.sidebar.multiselect(
                        "Seleccionar Países:",
                        options=countries_with_all,
                        default=["Todos"],
                        key="transacciones_countries_multiselect"
                    )
                    
                    # Aplicar comportamiento de multiselect
                    final_countries = handle_multiselect_behavior(selected_countries, countries, "Todos")
                    st.session_state['selected_countries'] = final_countries
                
                # Filtro de modalidades
                if 'modality' in outgoing_commitments.columns:
                    modalities = sorted(outgoing_commitments['modality'].dropna().astype(str).unique())
                    
                    selected_modality = st.sidebar.selectbox(
                        "Seleccionar Modalidad:",
                        ["Todas las modalidades"] + list(modalities),
                        index=0,
                        key="transacciones_modality_select"
                    )
                    st.session_state['selected_modality'] = selected_modality
                
                # Filtro de macrosectores
                if 'sector_codename' in outgoing_commitments.columns:
                    sectors = sorted(outgoing_commitments['sector_codename'].dropna().astype(str).unique())
                    
                    # Crear lista de macrosectores disponibles
                    available_macrosectors = set()
                    for sector in sectors:
                        macrosector = get_macrosector(sector)
                        if macrosector != "No clasificado":
                            available_macrosectors.add(macrosector)
                    
                    available_macrosectors = sorted(list(available_macrosectors))
                    
                    # Filtro de macrosectores
                    selected_macrosector = st.sidebar.selectbox(
                        "Seleccionar Macrosector:",
                        ["Todos los macrosectores"] + available_macrosectors,
                        index=0,
                        key="transacciones_macrosector_select"
                    )
                    st.session_state['selected_macrosector'] = selected_macrosector

        elif subpage_active == "Países":
            st.sidebar.markdown("---")
            st.sidebar.subheader("Filtros (Países)")

            # Slider de años
            selected_years = st.sidebar.slider(
                "Rango de Años:",
                min_value=2010,
                max_value=2024,
                value=(2010, 2024),
                step=1,
                key="transacciones_paises_years_slider",
            )
            st.session_state['selected_years'] = selected_years
    
    # Obtener la subpágina activa del sidebar
    subpage_active = st.session_state.get('subpage_active', 'Financiadores')
    
    # Obtener la subpágina activa del sidebar
    subpage_active = st.session_state.get('subpage_active', 'Financiadores')
    
    if subpage_active == "Financiadores":
        st.subheader("Financiadores")
        st.markdown("---")
        
        # Verificar si los datos IATI están cargados
        if df_iati is not None:
            # Filtrar solo transacciones de tipo "Outgoing Commitment"
            outgoing_commitments = df_iati[df_iati['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
            if len(outgoing_commitments) > 0:
                # Convertir la columna de fecha
                outgoing_commitments['transactiondate_isodate'] = pd.to_datetime(outgoing_commitments['transactiondate_isodate'])
                
                # Obtener rango de años del sidebar
                selected_years = st.session_state.get('selected_years', (2010, 2024))
                
                # Filtrar por años seleccionados
                outgoing_commitments = outgoing_commitments[
                    (outgoing_commitments['transactiondate_isodate'].dt.year >= selected_years[0]) & 
                    (outgoing_commitments['transactiondate_isodate'].dt.year <= selected_years[1])
                ]
                
                # Obtener filtros del sidebar (solo para Financiadores)
                selected_modality = st.session_state.get('selected_modality', "Todas las modalidades")
                selected_macrosector = st.session_state.get('selected_macrosector', "Todos los macrosectores")
                
                # Aplicar filtros
                df_filtered_by_filters = outgoing_commitments.copy()
                
                # Filtrar valores negativos
                df_filtered_by_filters = df_filtered_by_filters[df_filtered_by_filters['value_usd'] > 0]
                
                # Filtrar "Other" en modality
                if 'modality' in df_filtered_by_filters.columns:
                    df_filtered_by_filters = df_filtered_by_filters[~df_filtered_by_filters['modality'].str.contains('other', case=False, na=False)]
                
                # Aplicar filtro de región
                selected_region = st.session_state.get('selected_region', "Todas las regiones")
                if selected_region != "Todas las regiones" and 'recipientcountry_codename' in df_filtered_by_filters.columns:
                    paises_region = regiones_dict[selected_region]
                    df_filtered_by_filters = df_filtered_by_filters[
                        df_filtered_by_filters['recipientcountry_codename'].isin(paises_region)
                    ]
                
                # Aplicar filtro de países múltiples
                selected_countries = st.session_state.get('selected_countries', [])
                if selected_countries and 'recipientcountry_codename' in df_filtered_by_filters.columns:
                    # Filtrar por los países seleccionados (ya procesados por handle_multiselect_behavior)
                    df_filtered_by_filters = df_filtered_by_filters[
                        df_filtered_by_filters['recipientcountry_codename'].astype(str).isin(selected_countries)
                    ]
                
                if selected_modality != "Todas las modalidades" and 'modality' in df_filtered_by_filters.columns:
                    df_filtered_by_filters = df_filtered_by_filters[
                        df_filtered_by_filters['modality'].astype(str) == selected_modality
                    ]
                
                # Aplicar filtro de macrosector
                if selected_macrosector != "Todos los macrosectores" and 'sector_codename' in df_filtered_by_filters.columns:
                    # Obtener sectores del macrosector seleccionado
                    macrosector_sectors = macrosectores_dict.get(selected_macrosector, [])
                    df_filtered_by_filters = df_filtered_by_filters[
                        df_filtered_by_filters['sector_codename'].astype(str).isin(macrosector_sectors)
                    ]
                
                # Definir colores para cada institución
                colors = {
                    'fonplata': '#c1121f',
                    'iadb': '#0496ff', 
                    'caf': '#38b000',
                    'worldbank': '#004e89'
                }
                
                # Filtrar por las instituciones específicas
                instituciones = ['fonplata', 'iadb', 'caf', 'worldbank']
                df_filtered = df_filtered_by_filters[df_filtered_by_filters['prefix'].isin(instituciones)].copy()
                
                if len(df_filtered) > 0:
                    # Agrupar por año y institución para los gráficos de línea
                    df_filtered['year'] = df_filtered['transactiondate_isodate'].dt.year
                    yearly_data = df_filtered.groupby(['year', 'prefix'])['value_usd'].sum().reset_index()
                    
                    # Convertir valores a millones para mejor visualización
                    yearly_data['value_usd_millions'] = yearly_data['value_usd'] / 1000000
                    
                    # Calcular el valor máximo para normalizar todos los ejes Y
                    max_value_millions = yearly_data['value_usd_millions'].max()
                    
                    # Crear gráficos de barras individuales para cada institución
                    st.subheader("Evolución Anual por Institución")
                    
                    # Crear subplots para los gráficos de barras
                    fig_bars = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=('IADB', 'World Bank', 'FONPLATA', 'CAF'),
                        specs=[[{"secondary_y": False}, {"secondary_y": False}],
                               [{"secondary_y": False}, {"secondary_y": False}]]
                    )
                    
                    positions = [(1,1), (1,2), (2,1), (2,2)]
                    
                    # Reordenar las instituciones según el nuevo orden
                    instituciones_ordenadas = ['iadb', 'worldbank', 'fonplata', 'caf']
                    
                    for i, inst in enumerate(instituciones_ordenadas):
                        inst_data = yearly_data[yearly_data['prefix'] == inst]
                        if len(inst_data) > 0:
                            fig_bars.add_trace(
                                go.Bar(
                                    x=inst_data['year'],
                                    y=inst_data['value_usd_millions'],
                                    name=inst.upper(),
                                    marker_color=colors[inst],
                                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                                'Año: %{x}<br>' +
                                                'Valor: $%{y:.1f}M USD<br>' +
                                                '<extra></extra>'
                                ),
                                row=positions[i][0], col=positions[i][1]
                            )
                    
                    fig_bars.update_layout(
                        height=600,
                        showlegend=False
                    )
                    
                    # Actualizar ejes con rango dinámico basado en el máximo
                    for idx, (row, col) in enumerate(positions):
                        inst = instituciones_ordenadas[idx]

                        # Determinar títulos de ejes según la institución
                        x_title = "Año" if inst in ["fonplata", "caf"] else None
                        y_title = "Valor USD (Millones)" if inst in ["iadb", "fonplata"] else None

                        fig_bars.update_xaxes(title_text=x_title, row=row, col=col, showgrid=False)
                        fig_bars.update_yaxes(
                            title_text=y_title,
                            row=row, col=col,
                            showgrid=False,
                            range=[0, max_value_millions * 1.1]  # 10% de margen arriba
                        )
                    
                    st.plotly_chart(fig_bars, use_container_width=True)
                    
                    # Mostrar leyenda
                    legend_html = "<div style='display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 16px;'>"
                    for nombre, color in colors.items():
                        legend_html += f"<div style='display: flex; align-items: center; gap: 6px;'><div style='width: 18px; height: 18px; background: {color}; border-radius: 3px; border: 1px solid #888;'></div><span style='font-size: 15px;'>{nombre.upper()}</span></div>"
                    legend_html += "</div>"
                    st.markdown(legend_html, unsafe_allow_html=True)
                    
                    # Gráfico de barras apiladas al 100%
                    st.subheader("Distribución Porcentual por Institución")
                    
                    # Calcular porcentajes para el gráfico apilado
                    total_by_year = yearly_data.groupby('year')['value_usd'].sum().reset_index()
                    yearly_data_with_pct = yearly_data.merge(total_by_year, on='year', suffixes=('', '_total'))
                    yearly_data_with_pct['percentage'] = (yearly_data_with_pct['value_usd'] / yearly_data_with_pct['value_usd_total']) * 100
                    
                    # Asegurar que los porcentajes no excedan el 100% y redondear a 2 decimales
                    yearly_data_with_pct['percentage'] = yearly_data_with_pct['percentage'].clip(upper=100).round(2)
                    
                    # Crear gráfico de barras apiladas
                    fig_stacked = go.Figure()
                    
                    for inst in instituciones:
                        inst_data = yearly_data_with_pct[yearly_data_with_pct['prefix'] == inst]
                        if len(inst_data) > 0:
                            fig_stacked.add_trace(go.Bar(
                                name=inst.upper(),
                                x=inst_data['year'],
                                y=inst_data['percentage'],
                                marker_color=colors[inst],
                                hovertemplate='<b>%{fullData.name}</b><br>' +
                                            'Año: %{x}<br>' +
                                            'Porcentaje: %{y:.1f}%<br>' +
                                            '<extra></extra>'
                            ))
                    
                    fig_stacked.update_layout(
                        barmode='stack',
                        xaxis_title="Año",
                        yaxis_title="Porcentaje (%)",
                        height=500,
                        showlegend=False
                    )
                    
                    # Eliminar gridlines del gráfico apilado
                    fig_stacked.update_xaxes(showgrid=False)
                    fig_stacked.update_yaxes(showgrid=False)
                    
                    st.plotly_chart(fig_stacked, use_container_width=True)
                    
                    # Mostrar leyenda
                    st.markdown(legend_html, unsafe_allow_html=True)
                    
                else:
                    st.info("No hay datos disponibles para las instituciones seleccionadas.")
            else:
                st.info("No se encontraron transacciones de tipo 'Outgoing Commitment'.")
        else:
            st.error("No se pudieron cargar los datos IATI. Verifique que el archivo 'BDDGLOBALMERGED_ACTUALIZADO.parquet' esté disponible.")
    
    elif subpage_active == "Países":
        st.subheader("Países")
        st.markdown("---")
        
        # Selector de tipo de visualización
        visualization_type = st.selectbox(
            "Tipo de Visualización:",
            ["MDBs", "Sectores", "Modalidad"],
            index=0
        )
        
        # Verificar si los datos IATI están cargados
        if df_iati is not None:
            # Filtrar solo transacciones de tipo "Outgoing Commitment"
            outgoing_commitments = df_iati[df_iati['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
            if len(outgoing_commitments) > 0:
                # Convertir la columna de fecha
                outgoing_commitments['transactiondate_isodate'] = pd.to_datetime(outgoing_commitments['transactiondate_isodate'])
                
                # Obtener rango de años del sidebar
                selected_years = st.session_state.get('selected_years', (2010, 2024))
                
                # Filtrar por años seleccionados
                outgoing_commitments = outgoing_commitments[
                    (outgoing_commitments['transactiondate_isodate'].dt.year >= selected_years[0]) & 
                    (outgoing_commitments['transactiondate_isodate'].dt.year <= selected_years[1])
                ]
                
                # Filtrar solo los países específicos: AR, BO, BR, PY, UY
                paises_especificos = ['AR', 'BO', 'BR', 'PY', 'UY']
                outgoing_commitments = outgoing_commitments[
                    outgoing_commitments['recipientcountry_code'].isin(paises_especificos)
                ]
                
                # Filtrar valores negativos de value_usd
                outgoing_commitments = outgoing_commitments[outgoing_commitments['value_usd'] > 0]
                
                if len(outgoing_commitments) > 0:
                    # Definir colores para cada categoría según el tipo de visualización
                    if visualization_type == "MDBs":
                        colors = {
                            'fonplata': '#c1121f',
                            'iadb': '#0496ff', 
                            'caf': '#38b000',
                            'worldbank': '#004e89'
                        }
                        # Filtrar por las instituciones específicas
                        categorias = ['fonplata', 'iadb', 'caf', 'worldbank']
                        df_filtered = outgoing_commitments[outgoing_commitments['prefix'].isin(categorias)].copy()
                        categoria_column = 'prefix'
                        
                    elif visualization_type == "Sectores":
                        # Agregar columna de macrosector
                        outgoing_commitments['macrosector'] = outgoing_commitments['sector_codename'].apply(get_macrosector)
                        df_filtered = outgoing_commitments[outgoing_commitments['macrosector'] != "No clasificado"].copy()
                        categoria_column = 'macrosector'
                        
                        # Colores para macrosectores - nueva paleta
                        colors = {
                            'Social': '#15616D',
                            'Productivo': '#FFECD1',
                            'Infraestructura': '#FF7D00',
                            'Ambiental': '#FFB569',
                            'Gobernanza/Público': '#8AA79F',
                            'Multisectorial/Otros': '#BC5308'
                        }
                        categorias = list(colors.keys())
                        
                    elif visualization_type == "Modalidad":
                        df_filtered = outgoing_commitments.copy()
                        categoria_column = 'modality'
                        
                        # Filtrar "Other" de las modalidades
                        df_filtered = df_filtered[~df_filtered['modality'].str.contains('other', case=False, na=False)]
                        
                        # Obtener modalidades únicas después del filtrado
                        modalidades_unicas = df_filtered['modality'].dropna().unique()
                        colors = {}
                        paleta_modalidades = ['#C1121F', '#FDF0D5', '#003049', '#669BBC', '#DF817A']
                        for i, modalidad in enumerate(modalidades_unicas):
                            colors[modalidad] = paleta_modalidades[i % len(paleta_modalidades)]
                        categorias = list(colors.keys())
                    
                    # Filtrar observaciones que contengan "Other" en cualquier categoría
                    if visualization_type == "MDBs":
                        df_filtered = df_filtered[~df_filtered['prefix'].str.contains('other', case=False, na=False)]
                    elif visualization_type == "Sectores":
                        df_filtered = df_filtered[~df_filtered['macrosector'].str.contains('other', case=False, na=False)]
                    # Para Modalidad ya se filtró arriba, no necesitamos filtrar de nuevo
                    
                    if len(df_filtered) > 0:
                        # Agregar columna de año
                        df_filtered['year'] = df_filtered['transactiondate_isodate'].dt.year
                        
                        # Crear gráficos individuales para cada país
                        st.subheader(f"Evolución Anual por País - {visualization_type}")
                        
                        # Definir el orden de los países
                        paises_orden = ['AR', 'BO', 'BR', 'PY', 'UY']
                        
                        # Crear subplots: 2 filas, 3 columnas (primera fila: AR, BO, BR; segunda fila: PY, UY)
                        fig = make_subplots(
                            rows=2, cols=3,
                            subplot_titles=('Argentina', 'Bolivia', 'Brasil', 'Paraguay', 'Uruguay', ''),
                            specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
                                   [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]]
                        )
                        
                        # Posiciones para cada país
                        positions = {
                            'AR': (1, 1),  # Primera fila, primera columna
                            'BO': (1, 2),  # Primera fila, segunda columna
                            'BR': (1, 3),  # Primera fila, tercera columna
                            'PY': (2, 1),  # Segunda fila, primera columna
                            'UY': (2, 2)   # Segunda fila, segunda columna
                        }
                        
                        for pais in paises_orden:
                            pais_data = df_filtered[df_filtered['recipientcountry_code'] == pais]
                            
                            if len(pais_data) > 0:
                                # Agrupar por año y categoría
                                pais_yearly_data = pais_data.groupby(['year', categoria_column])['value_usd'].sum().reset_index()
                                pais_yearly_data['value_usd_millions'] = pais_yearly_data['value_usd'] / 1000000
                                
                                # Agregar barras apiladas para cada categoría en este país
                                for categoria in categorias:
                                    if categoria in pais_yearly_data[categoria_column].values:
                                        cat_data = pais_yearly_data[pais_yearly_data[categoria_column] == categoria]
                                        if len(cat_data) > 0:
                                            fig.add_trace(
                                                go.Bar(
                                                    x=cat_data['year'],
                                                    y=cat_data['value_usd_millions'],
                                                    name=categoria.upper() if visualization_type == "MDBs" else categoria,
                                                    marker_color=colors.get(categoria, '#999999'),
                                                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                                                'Año: %{x}<br>' +
                                                                'Valor: $%{y:.1f}M USD<br>' +
                                                                '<extra></extra>'
                                                ),
                                                row=positions[pais][0], col=positions[pais][1]
                                            )

                        fig.update_layout(
                            height=800,
                            barmode='stack',  # Hacer que las barras sean apiladas
                            showlegend=False
                        )
                        
                        # Actualizar ejes para todos los subplots
                        for i in range(1, 3):
                            for j in range(1, 4):
                                if j == 1:  # Argentina y Paraguay sin título del eje X
                                    fig.update_xaxes(title_text="", row=i, col=j, showgrid=False)
                                else:  # Bolivia, Brasil y Uruguay mantienen el título del eje X
                                    fig.update_xaxes(title_text="Año", row=i, col=j, showgrid=False)
                                
                                if j == 1:  # Solo Argentina mantiene el título del eje Y
                                    fig.update_yaxes(title_text="Valor USD (Millones)", row=i, col=j, showgrid=False)
                                else:  # Bolivia, Brasil, Paraguay y Uruguay sin título del eje Y
                                    fig.update_yaxes(title_text="", row=i, col=j, showgrid=False)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        # Leyenda superpuesta sobre el gráfico de Uruguay (segunda fila, segunda columna)
                        st.markdown(
                            f"""
                            <div style='position:relative; width:100%; height:0;'>
                                <div style='position:absolute; right:-2vw; top:-22vw; z-index:10; background:#23272e; padding:16px 20px 16px 16px; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.08); min-width:220px;'>
                                    <b style='color:#fff'>{'Instituciones' if visualization_type=='MDBs' else ('Macrosector' if visualization_type=='Sectores' else 'Modalidad')}:</b><br>
                                    {''.join([f"<div style='display:flex;align-items:center;gap:6px;margin-top:8px;'><div style='width:18px;height:18px;background:{color};border-radius:3px;border:1px solid #888;'></div><span style='font-size:15px;color:#fff'>{nombre}</span></div>" for nombre, color in colors.items()])}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("No hay datos disponibles para los filtros seleccionados.")
                else:
                    st.info("No se encontraron transacciones de tipo 'Outgoing Commitment'.")
            else:
                st.error("No se pudieron cargar los datos IATI. Verifique que el archivo 'BDDGLOBALMERGED_ACTUALIZADO.parquet' esté disponible.")
