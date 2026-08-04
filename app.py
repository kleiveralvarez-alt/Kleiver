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
        [data-testid="stSidebar"] {
            background-color: #E9ECEF !important;
        }
        [data-testid="stSidebar"] * {
            color: #212529 !important;
        }
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
        span[data-baseweb="tag"] {
            background-color: #E30613 !important;
        }
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
        hr {
            border-top: 2px solid #E30613 !important;
            margin-top: 15px;
            margin-bottom: 25px;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# 3. Carga y Limpieza de Datos
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

    df_raw = pd.read_excel(file_name)

    # Eliminar filas y columnas completamente vacías
    df_raw = df_raw.dropna(how="all").dropna(how="all", axis=1)

    # Sanitizar nombres de columnas
    clean_cols = []
    for c in df_raw.columns:
        if pd.isna(c) or str(c).strip().lower() == "nan":
            clean_cols.append("Columna_Sin_Nombre")
        else:
            clean_cols.append(str(c).strip())
    df_raw.columns = clean_cols

    return df_raw


try:
    df = load_data()

    # Identificar columna para 'Pedido'
    pedido_col = next(
        (c for c in df.columns if "pedido" in c.lower()), df.columns[0]
    )

    # Eliminar registros donde Pedido sea nulo o inválido
    df = df[df[pedido_col].notna()].copy()
    df[pedido_col] = df[pedido_col].astype(str).str.strip()
    df = df[
        ~df[pedido_col].isin(["nan", "None", "", "Columna_Sin_Nombre"])
    ].copy()

    # Identificar columna de 'Sociedad' (Columna N)
    sociedad_col = next(
        (c for c in df.columns if "sociedad" in c.lower()),
        df.columns[min(13, len(df.columns) - 1)],
    )

    # Identificar columna de 'TM MES REAL' (Columna AC)
    tm_col = next(
        (c for c in df.columns if "tm mes real" in c.lower()),
        next(
            (c for c in df.columns if "tm" in c.lower()),
            df.columns[min(28, len(df.columns) - 1)],
        ),
    )

    # Identificar otras columnas requeridas con respaldo de posición
    unid_col = next(
        (c for c in df.columns if "unidad de negocio" in c.lower()),
        df.columns[min(1, len(df.columns) - 1)],
    )
    carga_col = next(
        (c for c in df.columns if "tipo de carga" in c.lower()),
        df.columns[min(2, len(df.columns) - 1)],
    )
    grupo_col = next(
        (c for c in df.columns if "grupo art" in c.lower()),
        df.columns[min(3, len(df.columns) - 1)],
    )
    denom_col = next(
        (c for c in df.columns if "denominación" in c.lower()),
        df.columns[min(4, len(df.columns) - 1)],
    )
    prov_col = next(
        (c for c in df.columns if "nombre 1" in c.lower()),
        df.columns[min(5, len(df.columns) - 1)],
    )

    val_est_col = next(
        (c for c in df.columns if "estimado" in c.lower()),
        df.columns[min(6, len(df.columns) - 1)],
    )
    val_real_col = next(
        (c for c in df.columns if "valor real" in c.lower()),
        df.columns[min(7, len(df.columns) - 1)],
    )
    dif_col = next(
        (c for c in df.columns if "diferencia" in c.lower()),
        df.columns[min(8, len(df.columns) - 1)],
    )

    # Reemplazar valores nulos en textos
    for c in [sociedad_col, unid_col, carga_col, grupo_col, denom_col, prov_col]:
        df[c] = df[c].fillna("Sin Información").astype(str).str.strip()

    # Convertir valores numéricos
    for c in [tm_col, val_est_col, val_real_col, dif_col]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # 4. Sidebar - Encabezado con Logo y Filtros
    if os.path.exists("logo1.png"):
        st.sidebar.image("logo1.png", use_container_width=True)
    elif os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)
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

    # Opciones de Filtros
    unidades_opt = sorted([x for x in df[unid_col].unique() if str(x) != "nan"])
    unidades = st.sidebar.multiselect(
        "Unidad de Negocio", options=unidades_opt, default=unidades_opt
    )

    cargas_opt = sorted([x for x in df[carga_col].unique() if str(x) != "nan"])
    cargas = st.sidebar.multiselect(
        "Tipo de Carga", options=cargas_opt, default=cargas_opt
    )

    grupos_opt = sorted([x for x in df[grupo_col].unique() if str(x) != "nan"])
    grupos = st.sidebar.multiselect(
        "Nombre Grupo art.", options=grupos_opt, default=grupos_opt
    )

    sociedades_opt = sorted(
        [x for x in df[sociedad_col].unique() if str(x) != "nan"]
    )
    sociedades = st.sidebar.multiselect(
        "Sociedad", options=sociedades_opt, default=sociedades_opt
    )

    # Filtrar datos
    df_filtered = df[
        (df[unid_col].isin(unidades))
        & (df[carga_col].isin(cargas))
        & (df[grupo_col].isin(grupos))
        & (df[sociedad_col].isin(sociedades))
    ].copy()

    # 5. Encabezado de la Aplicación
    st.markdown(
        '<p class="main-title">Panel de Costos de Internación</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-title">Análisis Operativo y Nacionalización de Acero</p>',
        unsafe_allow_html=True,
    )

    if df_filtered.empty:
        st.warning(
            "No hay registros disponibles para los filtros seleccionados."
        )
    else:
        # 6. Agrupación por Pedido tomando la primera línea para TM MES REAL
        detalle_pedido = (
            df_filtered.groupby(pedido_col, as_index=False)
            .agg(
                Denominación=(denom_col, "first"),
                Proveedor=(prov_col, "first"),
                Sociedad=(sociedad_col, "first"),
                Unidad_Negocio=(unid_col, "first"),
                Tipo_Carga=(carga_col, "first"),
                Grupo_Articulo=(grupo_col, "first"),
                TM_Real=(tm_col, "first"),
                Valor_Estimado_USD=(val_est_col, "sum"),
                Valor_Real_USD=(val_real_col, "sum"),
                Diferencia_USD=(dif_col, "sum"),
            )
        )

        detalle_pedido["TM_Real"] = pd.to_numeric(
            detalle_pedido["TM_Real"], errors="coerce"
        ).fillna(0)
        detalle_pedido["Ratio USD/TM"] = (
            detalle_pedido["Valor_Real_USD"] / detalle_pedido["TM_Real"]
        ).fillna(0)

        # 7. Indicadores (KPIs)
        total_oc = detalle_pedido[pedido_col].nunique()
        total_tm_real = detalle_pedido["TM_Real"].sum()
        total_monto_real = detalle_pedido["Valor_Real_USD"].sum()
        total_monto_est = detalle_pedido["Valor_Estimado_USD"].sum()
        ratio_promedio = (
            total_monto_real / total_tm_real if total_tm_real > 0 else 0
        )
        grupos_activos = detalle_pedido["Grupo_Articulo"].nunique()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "COSTO REAL TOTAL",
            f"${total_monto_real:,.0f}",
            delta=f"Vs Est. ${total_monto_est:,.0f}",
            delta_color="off",
        )
        c2.metric("TONELADAS MÉTRICAS", f"{total_tm_real:,.1f} TM")
        c3.metric("RATIO PROMEDIO", f"${ratio_promedio:,.2f} /TM")
        c4.metric("GRUPOS ACTIVOS", f"{grupos_activos} / {len(grupos_opt)}")

        st.markdown("---")

        # 8. Gráfico por Grupo de Artículo
        grp_art = (
            detalle_pedido.groupby("Grupo_Articulo", as_index=False)
            .agg(
                TM_Real=("TM_Real", "sum"),
                Valor_Real_USD=("Valor_Real_USD", "sum"),
            )
        )
        grp_art["Ratio_USD_TM"] = (
            grp_art["Valor_Real_USD"] / grp_art["TM_Real"]
        ).fillna(0)

        custom_red_grey_scale = [
            "#8D99AE",
            "#ADB5BD",
            "#E63946",
            "#E30613",
            "#990000",
        ]

        fig = px.bar(
            grp_art.sort_values("Ratio_USD_TM", ascending=False),
            x="Grupo_Articulo",
            y="Ratio_USD_TM",
            title="Costos por Tonelada Métrica (USD / TM) según Grupo de Artículo",
            labels={
                "Ratio_USD_TM": "USD / TM Real",
                "Grupo_Articulo": "Grupo de Artículo",
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

        # 9. Tabla Detallada Limpia
        st.subheader("📋 Detalle de Costos por Pedido (OC) y Denominación")

        detalle_tabla = detalle_pedido.copy()
        detalle_tabla.columns = [
            "Pedido (OC)",
            "Denominación",
            "Proveedor",
            "Sociedad",
            "Unidad Negocio",
            "Tipo Carga",
            "Grupo Artículo",
            "TM Mes Real",
            "Valor Est. ($)",
            "Valor Real ($)",
            "Diferencia ($)",
            "Ratio ($/TM)",
        ]

        # Formato limpio sin depender del formatter estricto
        for col in [
            "Valor Est. ($)",
            "Valor Real ($)",
            "Diferencia ($)",
            "Ratio ($/TM)",
        ]:
            detalle_tabla[col] = detalle_tabla[col].map("${:,.2f}".format)

        for col in ["TM Mes Real"]:
            detalle_tabla[col] = detalle_tabla[col].map("{:,.2f}".format)

        st.dataframe(detalle_tabla, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la aplicación: {e}")
