import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

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

# Configuración de la página
st.set_page_config(
    page_title="Análisis Sectorial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para cargar los datos
def load_data():
    """Carga los archivos Parquet principales"""
    try:
        # Verificar si el archivo existe
        if not os.path.exists('BDDGLOBALMERGED_ACTUALIZADO.parquet'):
            return False
        
        # Cargar BDDGLOBALMERGED_ACTUALIZADO.parquet
        try:
            bdd_global = pd.read_parquet('BDDGLOBALMERGED_ACTUALIZADO.parquet')
        except Exception as e:
            st.error(f"Error al cargar BDDGLOBALMERGED_ACTUALIZADO.parquet: {str(e)}")
            return False
        
        # Verificar que el DataFrame se cargó correctamente
        if bdd_global is None or len(bdd_global) == 0:
            return False
        
        # Verificar si el archivo BDDGLOBALACT.parquet existe
        if not os.path.exists('BDDGLOBALACT.parquet'):
            return {'bdd_global': bdd_global, 'bdd_global_act': None}
        
        # Cargar BDDGLOBALACT.parquet
        try:
            bdd_global_act = pd.read_parquet('BDDGLOBALACT.parquet')
        except Exception as e:
            st.error(f"Error al cargar BDDGLOBALACT.parquet: {str(e)}")
            return {'bdd_global': bdd_global, 'bdd_global_act': None}
        
        return {'bdd_global': bdd_global, 'bdd_global_act': bdd_global_act}
        
    except Exception as e:
        st.error(f"Error general al cargar datos: {str(e)}")
        return False

# Función para la página Home
def home_page():
    st.title("Página de Inicio")
    st.markdown("---")
    
    st.header("Bienvenido al Sistema de Análisis Sectorial")
    st.write("Esta aplicación permite analizar datos sectoriales de diferentes fuentes.")
    
    # Información sobre los datos cargados
    if 'bdd_global' in st.session_state and 'bdd_global_act' in st.session_state:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("BDDGLOBALMERGED_ACTUALIZADO.parquet")
            st.write(f"**Registros:** {len(st.session_state['bdd_global'])}")
            st.write(f"**Columnas:** {len(st.session_state['bdd_global'].columns)}")
            
        with col2:
            st.subheader("BDDGLOBALACT.parquet")
            st.write(f"**Registros:** {len(st.session_state['bdd_global_act'])}")
            st.write(f"**Columnas:** {len(st.session_state['bdd_global_act'].columns)}")
    
    st.markdown("---")
    st.subheader("Páginas Disponibles")
    st.write("""
    - **Home:** Página principal con información general
    - **Ejecución:** Análisis de ejecución de proyectos
    - **Transacciones:** Análisis de transacciones financieras
    - **Sectores:** Análisis por sectores económicos
    - **Mercado:** Análisis de mercado
    - **Ticket:** Gestión de tickets y reportes
    """)

# Función para la página Ejecución
def ejecucion_page():
    st.title("Ejecución")
    st.markdown("---")
    
    st.header("Análisis de Ejecución")
    st.write("Esta página mostrará análisis relacionados con la ejecución de proyectos y actividades.")
    
    if 'bdd_global' in st.session_state:
        st.subheader("Datos de Ejecución Disponibles")
        st.write(f"Total de registros: {len(st.session_state['bdd_global'])}")
        
        # Mostrar las primeras columnas para referencia
        if len(st.session_state['bdd_global'].columns) > 0:
            pass

# Función para la página Transacciones
def transacciones_page():
    st.title("Transacciones")
    st.markdown("---")
    
    # Obtener la subpágina activa del sidebar
    subpage_active = st.session_state.get('subpage_active', 'Financiadores')
    
    if subpage_active == "Financiadores":
        st.subheader("Financiadores")
        st.markdown("---")
        
        if 'bdd_global' in st.session_state:
            # Verificar que estamos usando la BDD correcta
            df = st.session_state['bdd_global']
            
            # Filtrar solo transacciones de tipo "Outgoing Commitment"
            outgoing_commitments = df[df['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
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
                
                # Aplicar filtro de países múltiples
                selected_countries = st.session_state.get('selected_countries', [])
                if selected_countries and 'recipientcountry_codename' in df_filtered_by_filters.columns:
                    # Si "Todos" está seleccionado, no filtrar por países específicos
                    if "Todos" in selected_countries:
                        pass  # No aplicar filtro, incluir todos los países de la región
                    else:
                        # Filtrar por los países específicos seleccionados
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
                    st.subheader("📊 Evolución Anual por Institución")
                    
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
                        showlegend=False,
                        title_text="Evolución de Outgoing Commitments por Institución (2010-2024)",
                        title_x=0.5
                    )
                    
                    # Actualizar ejes con rango dinámico basado en el máximo
                    for i in range(1, 3):
                        for j in range(1, 3):
                            fig_bars.update_xaxes(title_text="Año", row=i, col=j, showgrid=False)
                            fig_bars.update_yaxes(
                                title_text="Valor USD (Millones)", 
                                row=i, col=j, 
                                showgrid=False,
                                range=[0, max_value_millions * 1.1]  # 10% de margen arriba
                            )
                    
                    st.plotly_chart(fig_bars, use_container_width=True)
                    
                    # Gráfico de barras apiladas al 100%
                    st.subheader("📊 Distribución Porcentual por Institución")
                    
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
                        title_text="Distribución Porcentual de Outgoing Commitments por Año (2010-2024)",
                        title_x=0.5,
                        xaxis_title="Año",
                        yaxis_title="Porcentaje (%)",
                        height=500
                    )
                    
                    # Eliminar gridlines del gráfico apilado
                    fig_stacked.update_xaxes(showgrid=False)
                    fig_stacked.update_yaxes(showgrid=False)
                    
                    st.plotly_chart(fig_stacked, use_container_width=True)
                    
                else:
                    pass
            else:
                pass
        else:
            pass
    
    elif subpage_active == "Países":
        st.subheader("Países")
        st.markdown("---")
        
        # Selector de tipo de visualización
        visualization_type = st.selectbox(
            "📊 Tipo de Visualización:",
            ["MDBs", "Sectores", "Modalidad"],
            index=0
        )
        
        if 'bdd_global' in st.session_state:
            # Verificar que estamos usando la BDD correcta
            df = st.session_state['bdd_global']
            
            # Filtrar solo transacciones de tipo "Outgoing Commitment"
            outgoing_commitments = df[df['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
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
                        
                        # Obtener modalidades únicas y asignar colores con nueva paleta
                        modalidades_unicas = df_filtered['modality'].dropna().unique()
                        # Filtrar "Other" de las modalidades
                        modalidades_unicas = [mod for mod in modalidades_unicas if 'other' not in mod.lower()]
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
                    elif visualization_type == "Modalidad":
                        df_filtered = df_filtered[~df_filtered['modality'].str.contains('other', case=False, na=False)]
                        # También filtrar después de obtener las modalidades únicas
                        modalidades_unicas = df_filtered['modality'].dropna().unique()
                        modalidades_unicas = [mod for mod in modalidades_unicas if 'other' not in mod.lower()]
                        categorias = modalidades_unicas
                        colors = {}
                        paleta_modalidades = ['#C1121F', '#FDF0D5', '#003049', '#669BBC', '#DF817A']
                        for i, modalidad in enumerate(modalidades_unicas):
                            colors[modalidad] = paleta_modalidades[i % len(paleta_modalidades)]
                    
                    if len(df_filtered) > 0:
                        # Agregar columna de año
                        df_filtered['year'] = df_filtered['transactiondate_isodate'].dt.year
                        
                        # Crear gráficos individuales para cada país
                        st.subheader(f"📊 Evolución Anual por País - {visualization_type}")
                        
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
                                                                '<extra></extra>',
                                                    showlegend=False
                                                ),
                                                row=positions[pais][0], col=positions[pais][1]
                                            )
                        
                        fig.update_layout(
                            height=800,
                            title_text=f"Evolución de Outgoing Commitments por País - {visualization_type} (2010-2024)",
                            title_x=0.5,
                            showlegend=False,
                            barmode='stack'  # Hacer que las barras sean apiladas
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
                        
                        # Crear leyenda debajo del gráfico de Brasil y al lado de Uruguay
                        col1, col2, col3 = st.columns([1, 1, 1])
                        
                        with col3:
                            st.markdown("**<span style='font-size: 12px;'>Leyenda:</span>**", unsafe_allow_html=True)
                            for categoria in categorias:
                                color_hex = colors.get(categoria, '#999999')
                                nombre_mostrar = categoria.upper() if visualization_type == "MDBs" else categoria
                                st.markdown(f"<div style='display: flex; align-items: center; margin-bottom: 3px;'><span style='font-size: 10px; font-weight: bold;'>{nombre_mostrar}</span><div style='width: 12px; height: 8px; background-color: {color_hex}; border: 1px solid #ccc; margin-left: 8px;'></div></div>", unsafe_allow_html=True)
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass

# Función para la página Sectores
def sectores_page():
    st.title("Sectores")
    st.markdown("---")
    
    st.header("Análisis por Sectores")
    st.write("Esta página mostrará análisis desglosados por sectores económicos y macrosectores.")
    
    # Mostrar información sobre macrosectores
    st.subheader("🏗️ Macrosectores Disponibles")
    
    # Crear tabs para cada macrosector
    macrosector_tabs = st.tabs(list(macrosectores_dict.keys()))
    
    for i, (macrosector, sectors) in enumerate(macrosectores_dict.items()):
        with macrosector_tabs[i]:
            st.write(f"**{macrosector}**")
            st.write(f"Total de sectores: {len(sectors)}")
            
            # Mostrar sectores en columnas para mejor visualización
            cols = st.columns(2)
            for j, sector in enumerate(sectors):
                col_idx = j % 2
                with cols[col_idx]:
                    st.write(f"• {sector}")
    
    # Análisis de datos si están disponibles
    if 'bdd_global' in st.session_state:
        st.markdown("---")
        st.subheader("📊 Análisis de Datos por Macrosector")
        
        df = st.session_state['bdd_global']
        if 'sector_codename' in df.columns:
            # Agregar columna de macrosector al dataframe
            df_with_macrosector = df.copy()
            df_with_macrosector['macrosector'] = df_with_macrosector['sector_codename'].apply(get_macrosector)
            
            # Filtrar solo transacciones de tipo "Outgoing Commitment"
            outgoing_commitments = df_with_macrosector[df_with_macrosector['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
            if len(outgoing_commitments) > 0:
                # Convertir la columna de fecha
                outgoing_commitments['transactiondate_isodate'] = pd.to_datetime(outgoing_commitments['transactiondate_isodate'])
                
                # Filtrar por años 2010-2024
                outgoing_commitments = outgoing_commitments[
                    (outgoing_commitments['transactiondate_isodate'].dt.year >= 2010) & 
                    (outgoing_commitments['transactiondate_isodate'].dt.year <= 2024)
                ]
                
                # Agrupar por macrosector
                macrosector_data = outgoing_commitments.groupby('macrosector')['value_usd'].sum().reset_index()
                macrosector_data = macrosector_data[macrosector_data['macrosector'] != "No clasificado"]
                
                if len(macrosector_data) > 0:
                    # Convertir a millones para mejor visualización
                    macrosector_data['value_usd_millions'] = macrosector_data['value_usd'] / 1000000
                    
                    # Gráfico de barras por macrosector
                    fig = px.bar(
                        macrosector_data,
                        x='macrosector',
                        y='value_usd_millions',
                        title="Distribución de Outgoing Commitments por Macrosector (2010-2024)",
                        labels={'value_usd_millions': 'Valor USD (Millones)', 'macrosector': 'Macrosector'},
                        color='macrosector',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    
                    fig.update_layout(
                        xaxis_title="Macrosector",
                        yaxis_title="Valor USD (Millones)",
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabla con estadísticas
                    st.subheader("📋 Estadísticas por Macrosector")
                    st.dataframe(macrosector_data.sort_values('value_usd_millions', ascending=False))
                else:
                    pass
            else:
                pass
        else:
            pass
    else:
        pass

# Función para la página Mercado
def mercado_page():
    st.title("Mercado")
    st.markdown("---")
    
    st.header("Análisis de Mercado")
    st.write("Esta página mostrará análisis relacionados con el mercado y tendencias.")
    
    st.subheader("Indicadores de Mercado")
    st.write("Aquí se mostrarán indicadores y análisis de mercado.")

# Función para la página Ticket
def ticket_page():
    st.title("Ticket")
    st.markdown("---")
    
    # Obtener la subpágina activa del sidebar
    subpage_active = st.session_state.get('ticket_subpage_active', 'Financiadores')
    
    if subpage_active == "Financiadores":
        st.subheader("Financiadores")
        st.markdown("---")
        
        if 'bdd_global' in st.session_state:
            # Verificar que estamos usando la BDD correcta
            df = st.session_state['bdd_global']
            
            # Filtrar solo transacciones de tipo "Outgoing Commitment"
            outgoing_commitments = df[df['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
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
                
                # Obtener filtros del sidebar
                selected_modality = st.session_state.get('selected_modality', "Todas las modalidades")
                selected_macrosector = st.session_state.get('selected_macrosector', "Todos los macrosectores")
                
                # Aplicar filtros
                df_filtered_by_filters = outgoing_commitments.copy()
                
                # Filtrar valores negativos
                df_filtered_by_filters = df_filtered_by_filters[df_filtered_by_filters['value_usd'] > 0]
                
                # Filtrar "Other" en modality
                if 'modality' in df_filtered_by_filters.columns:
                    df_filtered_by_filters = df_filtered_by_filters[~df_filtered_by_filters['modality'].str.contains('other', case=False, na=False)]
                
                # Aplicar filtro de países múltiples
                selected_countries = st.session_state.get('selected_countries', [])
                if selected_countries and 'recipientcountry_codename' in df_filtered_by_filters.columns:
                    # Si "Todos" está seleccionado, no filtrar por países específicos
                    if "Todos" in selected_countries:
                        pass  # No aplicar filtro, incluir todos los países de la región
                    else:
                        # Filtrar por los países específicos seleccionados
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
                    # Convertir valores a millones para mejor visualización
                    df_filtered['value_usd_millions'] = df_filtered['value_usd'] / 1000000
                    
                    # Crear box plots para cada institución
                    st.subheader("📊 Box Plots por Institución Financiera")
                    
                    # Crear un solo gráfico con todos los box plots
                    fig_boxes = go.Figure()
                    
                    # Reordenar las instituciones según el nuevo orden
                    instituciones_ordenadas = ['iadb', 'worldbank', 'fonplata', 'caf']
                    
                    for inst in instituciones_ordenadas:
                        inst_data = df_filtered[df_filtered['prefix'] == inst]
                        if len(inst_data) > 0:
                            fig_boxes.add_trace(
                                go.Box(
                                    y=inst_data['value_usd_millions'],
                                    name=inst.upper(),
                                    marker_color=colors[inst],
                                    boxpoints='outliers',
                                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                                'Valor: $%{y:.2f}M USD<br>' +
                                                '<extra></extra>'
                                )
                            )
                    
                    fig_boxes.update_layout(
                        height=500,
                        title_text="Distribución de Valores por Institución Financiera (Box Plots)",
                        title_x=0.5,
                        xaxis_title="Institución Financiera",
                        yaxis_title="Valor USD (Millones)",
                        showlegend=False
                    )
                    
                    # Actualizar ejes
                    fig_boxes.update_xaxes(showgrid=False)
                    fig_boxes.update_yaxes(showgrid=False)
                    
                    st.plotly_chart(fig_boxes, use_container_width=True)
                    
                    # Mostrar estadísticas descriptivas para cada institución
                    st.subheader("📋 Estadísticas Descriptivas por Institución")
                    
                    # Crear tabla de estadísticas
                    stats_data = []
                    for inst in instituciones_ordenadas:
                        inst_data = df_filtered[df_filtered['prefix'] == inst]
                        if len(inst_data) > 0:
                            stats = {
                                'Institución': inst.upper(),
                                'Observaciones': len(inst_data),
                                'Media (M USD)': inst_data['value_usd_millions'].mean(),
                                'Mediana (M USD)': inst_data['value_usd_millions'].median(),
                                'Desv. Est. (M USD)': inst_data['value_usd_millions'].std(),
                                'Mínimo (M USD)': inst_data['value_usd_millions'].min(),
                                'Máximo (M USD)': inst_data['value_usd_millions'].max(),
                                'Q1 (M USD)': inst_data['value_usd_millions'].quantile(0.25),
                                'Q3 (M USD)': inst_data['value_usd_millions'].quantile(0.75)
                            }
                            stats_data.append(stats)
                    
                    if stats_data:
                        stats_df = pd.DataFrame(stats_data)
                        # Redondear valores numéricos
                        numeric_columns = ['Media (M USD)', 'Mediana (M USD)', 'Desv. Est. (M USD)', 
                                         'Mínimo (M USD)', 'Máximo (M USD)', 'Q1 (M USD)', 'Q3 (M USD)']
                        for col in numeric_columns:
                            if col in stats_df.columns:
                                stats_df[col] = stats_df[col].round(2)
                        
                        st.dataframe(stats_df, use_container_width=True)
                        
                        # Mostrar información adicional
                        st.markdown("---")
                        st.subheader("ℹ️ Información sobre los Box Plots")
                        st.write("""
                        - **Caja (Box):** Representa el rango intercuartílico (Q1 a Q3)
                        - **Línea central:** Mediana de los datos
                        - **Bigotes (Whiskers):** Extensión hasta 1.5 veces el rango intercuartílico
                        - **Puntos:** Valores atípicos (outliers)
                        - **Observaciones:** Número total de transacciones por institución
                        """)
                    else:
                        st.warning("No hay datos suficientes para generar estadísticas.")
                else:
                    st.warning("No hay datos disponibles para las instituciones seleccionadas.")
            else:
                st.warning("No hay transacciones de tipo 'Outgoing Commitment' disponibles.")
        else:
            st.warning("No hay datos cargados en la sesión.")
    
    elif subpage_active == "Gestión":
        st.subheader("Gestión de Tickets")
        st.write("Esta página permitirá gestionar tickets y reportes.")
        
        st.subheader("Funcionalidades de Ticket")
        st.write("""
        - Crear nuevos tickets
        - Ver tickets existentes
        - Generar reportes
        - Seguimiento de estado
        """)

# Función para inicializar la sesión
def initialize_session():
    """Inicializa las variables de sesión si no existen"""
    if 'bdd_global' not in st.session_state:
        st.session_state['bdd_global'] = None
    if 'bdd_global_act' not in st.session_state:
        st.session_state['bdd_global_act'] = None

# Función para limpiar la sesión
def clear_session():
    """Limpia los datos de la sesión"""
    if 'bdd_global' in st.session_state:
        del st.session_state['bdd_global']
    if 'bdd_global_act' in st.session_state:
        del st.session_state['bdd_global_act']

# Función principal
def main():
    # Inicializar sesión
    initialize_session()
    
    # Verificar si los datos ya están cargados en la sesión
    if st.session_state['bdd_global'] is not None:
        pass
        
        # Mostrar información adicional sobre los datos
        df = st.session_state['bdd_global']
        if len(df.columns) > 0:
            pass
    else:
        # Cargar datos
        pass
        data_result = load_data()
        
        if data_result is False:
            st.stop()
        
        # Guardar los datos en la sesión
        if isinstance(data_result, dict):
            st.session_state['bdd_global'] = data_result['bdd_global']
            st.session_state['bdd_global_act'] = data_result['bdd_global_act']
            
            # Verificar que los datos se guardaron correctamente
            if 'bdd_global' in st.session_state and st.session_state['bdd_global'] is not None:
                pass
                
                # Mostrar información adicional sobre los datos
                df = st.session_state['bdd_global']
                if len(df.columns) > 0:
                    pass
            else:
                st.stop()
        else:
            st.stop()
    
    # Sidebar para navegación
    st.sidebar.title("Análisis Sectorial")
    st.sidebar.markdown("---")
    
    # Menú de navegación
    page = st.sidebar.selectbox(
        "Seleccione una página:",
        ["Home", "Ejecución", "Transacciones", "Sectores", "Mercado", "Ticket"]
    )
    
    # Filtros desplegables en el sidebar (solo para la página de Transacciones - subpágina Financiadores)
    if page == "Transacciones" and 'bdd_global' in st.session_state:
        # Crear un selectbox para elegir la subpágina activa
        subpage_active = st.sidebar.selectbox(
            "📊 Subpágina activa:",
            ["Financiadores", "Países"],
            index=0,
            key="transacciones_subpage_select"
        )
        st.session_state['subpage_active'] = subpage_active
        
        # Solo mostrar filtros si estamos en la subpágina de Financiadores
        if subpage_active == "Financiadores":
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 Filtros (Financiadores)")
            
            # Slider de años
            selected_years = st.sidebar.slider(
                "📅 Rango de Años:",
                min_value=2010,
                max_value=2024,
                value=(2010, 2024),
                step=1,
                key="transacciones_years_slider"
            )
            st.session_state['selected_years'] = selected_years
            
            # Obtener datos filtrados para los filtros
            df = st.session_state['bdd_global']
            outgoing_commitments = df[df['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
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
                    "🌎 Seleccionar Región:",
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
                        "🌍 Seleccionar Países:",
                        options=countries_with_all,
                        default=["Todos"],  # Por defecto selecciona "Todos"
                        key="transacciones_countries_multiselect"
                    )
                    st.session_state['selected_countries'] = selected_countries
                
                # Filtro de modalidades
                if 'modality' in outgoing_commitments.columns:
                    modalities = sorted(outgoing_commitments['modality'].dropna().astype(str).unique())
                    
                    selected_modality = st.sidebar.selectbox(
                        "📋 Seleccionar Modalidad:",
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
                        "🏗️ Seleccionar Macrosector:",
                        ["Todos los macrosectores"] + available_macrosectors,
                        index=0,
                        key="transacciones_macrosector_select"
                    )
                    st.session_state['selected_macrosector'] = selected_macrosector
    
    # Filtros desplegables en el sidebar para la página de Ticket
    if page == "Ticket" and 'bdd_global' in st.session_state:
        # Crear un selectbox para elegir la subpágina activa
        ticket_subpage_active = st.sidebar.selectbox(
            "📊 Subpágina activa:",
            ["Financiadores", "Gestión"],
            index=0,
            key="ticket_subpage_select"
        )
        st.session_state['ticket_subpage_active'] = ticket_subpage_active
        
        # Solo mostrar filtros si estamos en la subpágina de Financiadores
        if ticket_subpage_active == "Financiadores":
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 Filtros (Financiadores)")
            
            # Slider de años
            selected_years = st.sidebar.slider(
                "📅 Rango de Años:",
                min_value=2010,
                max_value=2024,
                value=(2010, 2024),
                step=1,
                key="ticket_years_slider"
            )
            st.session_state['selected_years'] = selected_years
            
            # Obtener datos filtrados para los filtros
            df = st.session_state['bdd_global']
            outgoing_commitments = df[df['transactiontype_codename'] == 'Outgoing Commitment'].copy()
            
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
                    "🌎 Seleccionar Región:",
                    ["Todas las regiones"] + list(regiones_dict.keys()),
                    index=0,
                    key="ticket_region_select"
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
                        "🌍 Seleccionar Países:",
                        options=countries_with_all,
                        default=["Todos"],  # Por defecto selecciona "Todos"
                        key="ticket_countries_multiselect"
                    )
                    st.session_state['selected_countries'] = selected_countries
                
                # Filtro de modalidades
                if 'modality' in outgoing_commitments.columns:
                    modalities = sorted(outgoing_commitments['modality'].dropna().astype(str).unique())
                    
                    selected_modality = st.sidebar.selectbox(
                        "📋 Seleccionar Modalidad:",
                        ["Todas las modalidades"] + list(modalities),
                        index=0,
                        key="ticket_modality_select"
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
                        "🏗️ Seleccionar Macrosector:",
                        ["Todos los macrosectores"] + available_macrosectors,
                        index=0,
                        key="ticket_macrosector_select"
                    )
                    st.session_state['selected_macrosector'] = selected_macrosector
    
    # Navegación basada en la selección
    if page == "Home":
        home_page()
    elif page == "Ejecución":
        ejecucion_page()
    elif page == "Transacciones":
        transacciones_page()
    elif page == "Sectores":
        sectores_page()
    elif page == "Mercado":
        mercado_page()
    elif page == "Ticket":
        ticket_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Desarrollado con Streamlit**")

if __name__ == "__main__":
    main() 