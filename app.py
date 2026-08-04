import os
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="Panel de Costos de Internación | MULTI",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Estilos personalizados (CSS) - Colores e Identidad MULTI
st.markdown(
    """
    <style>
        /* Fondo del Sidebar en Gris Claro */
        [data-testid="stSidebar"] {
            background-color: #E9ECEF !important;
        }
        
        /* Ajuste de colores en el Sidebar */
        [data-testid="stSidebar"] * {
            color: #212529 !important;
        }

        /* Tarjetas de Indicadores (KPIs) */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #DEE2E6;
            padding: 15px 20px;
            border-radius: 12px;
            box-shadow: 0px 3px 8px rgba(0,0,0,0.05);
        }

        [data-testid="stMetricLabel"] {
            color: #6C757D !important;
            font-weight: 700;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
        }

        [data-testid="stMetricValue"] {
            color: #1A1A1A !important;
            font-weight: 800;
        }

        /* Tags/Pills de filtros seleccionados */
        span[data-baseweb="tag"] {
            background-color: #E30613 !important;
        }
        
        /* Encabezados e Historia de Marca */
        .main-title {
            color: #1A1A1A;
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 0px;
        }
        
        .sub-title {
            color: #E30613;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 20px;
        }

        /* Línea divisora roja */
        hr {
            border-top: 2px solid #E30613 !important;
            margin-top: 15px;
            margin-bottom: 25px;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# 3. Carga de Datos
@st.cache_data
def load_data():
    file_name = "1 julio internacion_2.XLSX"
    if not os.path.exists(file_name):
        file_name = "1 julio internacion.XLSX"

    if not os.path.exists(file_name):
        for f in os.listdir("."):
            if "julio" in f.lower() and f.endswith((".xlsx", ".XLSX")):
                file_name = f
                break
    return pd.read_excel(file_name)


try:
    df = load_data()

    # 4. Sidebar - Encabezado y Filtros
    if os.path.exists("logo1.png"):
        st.sidebar.image("logo1.png", use_container_width=True)
    else:
        st.sidebar.markdown(
            """
            <div style="background-color: #E30613; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
                <h2 style="color: white !important; margin: 0; font-weight: 900; font-size: 24px;">↗ MULTI</h2>
                <span style="color: white !important; font-size: 10px; font-weight: 700; letter-spacing: 2px;">LÍDER EN ACERO</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.sidebar.subheader("🔍 Filtros de Búsqueda")

    st.sidebar.subheader("🔍 Filtros de Búsqueda")

    # Filtro Unidad de Negocio
    unidades_opt = sorted(df["Unidad de negocio"].dropna().unique())
    unidades = st.sidebar.multiselect(
        "Unidad de Negocio", options=unidades_opt, default=unidades_opt
    )

    # Filtro Tipo de Carga
    cargas_opt = sorted(df["Tipo de carga"].dropna().unique())
    cargas = st.sidebar.multiselect(
        "Tipo de Carga", options=cargas_opt, default=cargas_opt
    )

    # Filtro Nombre Grupo art.
    grupos_opt = sorted(df["Nombre Grupo art."].dropna().unique())
    grupos = st.sidebar.multiselect(
        "Nombre Grupo art.", options=grupos_opt, default=grupos_opt
    )

    # Filtro País
    paises_opt = sorted(df["PAIS"].dropna().unique())
    paises = st.sidebar.multiselect(
        "País de Origen", options=paises_opt, default=paises_opt
    )

    # Aplicar filtros
    df_filtered = df[
        (df["Unidad de negocio"].isin(unidades))
        & (df["Tipo de carga"].isin(cargas))
        & (df["Nombre Grupo art."].isin(grupos))
        & (df["PAIS"].isin(paises))
    ]

    # 5. Encabezado de la Aplicación
    st.markdown(
        '<p class="main-title">Panel de Costos de Internación</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-title">Análisis Operativo y Nacionalización de Acero</p>',
        unsafe_allow_html=True,
    )

    # 6. Cálculos de Indicadores (KPIs)
    total_oc = df_filtered["Pedido"].nunique()
    total_tm_recibida = df_filtered["Ctd. TM Recibida"].sum()
    total_monto_real = df_filtered["Valor Real $"].sum()
    total_monto_est = df_filtered["Valor Estimado $"].sum()
    ratio_promedio = (
        total_monto_real / total_tm_recibida if total_tm_recibida > 0 else 0
    )
    grupos_activos = df_filtered["Nombre Grupo art."].nunique()

    # Mostrar KPIs en 4 columnas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "COSTO REAL TOTAL",
        f"${total_monto_real:,.0f}",
        delta=f"Vs Est. ${total_monto_est:,.0f}",
        delta_color="off",
    )
    c2.metric("TONELADAS MÉTRICAS", f"{total_tm_recibida:,.1f} TM")
    c3.metric("RATIO PROMEDIO", f"${ratio_promedio:,.2f} /TM")
    c4.metric("GRUPOS ACTIVOS", f"{grupos_activos} / {len(grupos_opt)}")

    st.markdown("---")

    # 7. Gráfico en escala de Rojos y Grises
    grp_art = (
        df_filtered.groupby("Nombre Grupo art.")
        .agg(
            TM_Recibida=("Ctd. TM Recibida", "sum"),
            Valor_Real_USD=("Valor Real $", "sum"),
        )
        .reset_index()
    )
    grp_art["Ratio_USD_TM"] = grp_art["Valor_Real_USD"] / grp_art["TM_Recibida"]

    # Paleta personalizada: De gris acero a rojo MULTI
    custom_red_grey_scale = [
        "#8D99AE",
        "#ADB5BD",
        "#E63946",
        "#E30613",
        "#990000",
    ]

    fig = px.bar(
        grp_art.sort_values("Ratio_USD_TM", ascending=False),
        x="Nombre Grupo art.",
        y="Ratio_USD_TM",
        title="Costos por Tonelada Métrica (USD / TM) según Grupo de Artículo",
        labels={
            "Ratio_USD_TM": "USD / TM Recibida",
            "Nombre Grupo art.": "Grupo de Artículo",
        },
        text_auto=".2f",
        color="Ratio_USD_TM",
        color_continuous_scale=custom_red_grey_scale,
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color="#212529"),
        title_font=dict(size=18, color="#1A1A1A"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#E9ECEF"),
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig, use_container_width=True)

    # 8. Detalle de Tabla por Pedido (OC) y Denominación
    st.subheader("📋 Detalle de Costos por Pedido (OC) y Denominación")

    detalle_pedido = (
        df_filtered.groupby(
            [
                "Pedido",
                "Denominación",
                "Nombre 1",
                "PAIS",
                "Unidad de negocio",
                "Tipo de carga",
                "Nombre Grupo art.",
            ]
        )
        .agg(
            TM_Pedida=("Cantidad TM", "sum"),
            TM_Recibida=("Ctd. TM Recibida", "sum"),
            Valor_Estimado_USD=("Valor Estimado $", "sum"),
            Valor_Real_USD=("Valor Real $", "sum"),
            Diferencia_USD=("Diferencia $", "sum"),
        )
        .reset_index()
    )

    detalle_pedido["Ratio USD/TM"] = (
        detalle_pedido["Valor_Real_USD"] / detalle_pedido["TM_Recibida"]
    )

    # Renombrar columnas para la tabla final
    detalle_pedido.columns = [
        "Pedido (OC)",
        "Denominación",
        "Proveedor",
        "País",
        "Unidad Negocio",
        "Tipo Carga",
        "Grupo Artículo",
        "TM Pedidas",
        "TM Recibidas",
        "Valor Est. ($)",
        "Valor Real ($)",
        "Diferencia ($)",
        "Ratio ($/TM)",
    ]

    st.dataframe(
        detalle_pedido.style.format(
            {
                "TM Pedidas": "{:,.2f}",
                "TM Recibidas": "{:,.2f}",
                "Valor Est. ($)": "${:,.2f}",
                "Valor Real ($)": "${:,.2f}",
                "Diferencia ($)": "${:,.2f}",
                "Ratio ($/TM)": "${:,.2f}",
            }
        ),
        use_container_width=True,
    )

except Exception as e:
    st.error(f"Error al cargar la aplicación: {e}")
