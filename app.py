import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración inicial de la página
st.set_page_config(page_title="Dashboard Multi", layout="wide")

# CSS personalizado para bajar el logo, ajustar la interfaz y darle nitidez
st.markdown("""
    <style>
        .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 1rem !important;
        }
        .logo-img {
            margin-top: 15px;
            margin-bottom: 15px;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }
    </style>
""", unsafe_allow_html=True)

# Paletas de colores oficiales (Rojos para Real, Grises para Estimado)
COLOR_RED_SHADES = ['#8B0000', '#C00000', '#FF0000', '#FF4D4D', '#FF8080']
COLOR_GREY_SHADES = ['#333333', '#555555', '#777777', '#999999', '#BBBBBB']

# 1. Cargar archivo de datos en la barra lateral
st.sidebar.header("Configuración de Datos")
uploaded_file = st.sidebar.file_drop_here if hasattr(st.sidebar, "file_drop_here") else st.sidebar.file_uploader("Cargar archivo Excel o CSV", type=["xlsx", "csv"])

# Función para cargar datos generados o reales
@st.cache_data
def cargar_datos(file):
    if file is not None:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    else:
        # Datos de demostración estructurados si no hay archivo cargado
        data = {
            'Sociedad': ['MP-PT.CR', 'MP-PT.GT', 'MP-PT.NIC', 'MP-PT.CR', 'MP-PT.GT', 'MP-PT.NIC'],
            'Unidad_Negocio': ['DECO', 'MEGA', 'TECHO', 'TUBO', 'DECO', 'MEGA'],
            'Tipo_Carga': ['Carga suelta', 'Contenedor', 'Carga suelta', 'Contenedor', 'Carga suelta', 'Contenedor'],
            'Tipo_Material': ['Atad Hierro Angular', 'Bobina LE', 'Bobina LRA', 'Bobina LRC', 'Bobina LRF', 'Lámina Negra'],
            'USD_Real': [250000, 210000, 100000, 80000, 50000, 49175.79],
            'USD_Estimado': [200000, 190000, 110000, 60000, 40000, 11978.04],
            'Toneladas': [12000, 10000, 5000, 3000, 2000, 1424.98]
        }
        return pd.DataFrame(data)

df = cargar_datos(uploaded_file)

# Encabezado principal del Dashboard
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    # Muestra el logo desde una URL fija o imagen local si la tienes
    st.markdown('<h2 style="color: #C00000; margin: 0;"><b>MULTI</b></h2><p style="margin: 0; font-size: 12px; color: #555;"><b>LÍDER EN ACERO</b></p>', unsafe_allow_html=True)
with col_titulo:
    st.title("Panel de Control de Gestión")

st.markdown("---")

# 2. Seccion de Filtros
st.subheader("🔍 Filtros de Búsqueda")
f_col1, f_col2, f_col3, f_col4 = st.columns(4)

with f_col1:
    sociedades = st.multiselect("1. Sociedad", options=df['Sociedad'].unique(), default=df['Sociedad'].unique())
with f_col2:
    unidades = st.multiselect("2. Unidad de Negocio", options=df['Unidad_Negocio'].unique(), default=df['Unidad_Negocio'].unique())
with f_col3:
    cargas = st.multiselect("3. Tipo de Carga", options=df['Tipo_Carga'].unique(), default=df['Tipo_Carga'].unique())
with f_col4:
    materiales = st.multiselect("4. Tipo de Material", options=df['Tipo_Material'].unique(), default=df['Tipo_Material'].unique())

# Filtrar DataFrame según las selecciones
df_filtered = df[
    (df['Sociedad'].isin(sociedades)) &
    (df['Unidad_Negocio'].isin(unidades)) &
    (df['Tipo_Carga'].isin(cargas)) &
    (df['Tipo_Material'].isin(materiales))
]

# 3. Métricas Principales (KPIs)
st.markdown("---")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_real = df_filtered['USD_Real'].sum()
total_est = df_filtered['USD_Estimado'].sum()
total_tm = df_filtered['Toneladas'].sum()
ratio_prom = (total_real / total_tm) if total_tm > 0 else 0

kpi1.metric("USD REAL TOTAL", f"${total_real:,.2f}")
kpi2.metric("USD ESTIMADO TOTAL", f"${total_est:,.2f}")
kpi3.metric("TONELADAS MÉTRICAS", f"{total_tm:,.2f} TM")
kpi4.metric("RATIO PROMEDIO", f"${ratio_prom:,.2f} /TM")

# 4. Gráficos con Tonos Rojos y Grises
st.markdown("---")
st.subheader("Análisis Comparativo por Categoría")

col_g1, col_g2 = st.columns(2)

with col_g1:
    # Gráfico de USD Real por Sociedad en Tonos Rojos
    df_soc = df_filtered.groupby('Sociedad')['USD_Real'].sum().reset_index()
    fig_real = px.bar(
        df_soc, 
        x='Sociedad', 
        y='USD_Real', 
        title="USD Real por Sociedad",
        color_discrete_sequence=COLOR_RED_SHADES
    )
    fig_real.update_layout(plot_bgcolor="white", paper_bgcolor="white", font=dict(color="#333"))
    st.plotly_chart(fig_real, use_container_width=True)

with col_g2:
    # Gráfico de USD Estimado por Sociedad en Tonos Grises
    df_est = df_filtered.groupby('Sociedad')['USD_Estimado'].sum().reset_index()
    fig_est = px.bar(
        df_est, 
        x='Sociedad', 
        y='USD_Estimado', 
        title="USD Estimado por Sociedad",
        color_discrete_sequence=COLOR_GREY_SHADES
    )
    fig_est.update_layout(plot_bgcolor="white", paper_bgcolor="white", font=dict(color="#333"))
    st.plotly_chart(fig_est, use_container_width=True)
