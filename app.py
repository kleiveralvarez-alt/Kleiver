import os
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuración de la página en modo WIDE
st.set_page_config(
    page_title="Panel de Costos de Internación | MULTI",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Estilos personalizados (CSS)
st.markdown(
    """
    <style>
        /* Ocultar completamente el Sidebar y el botón del menú desplegable */
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Margen superior adecuado para que el logo no se corte */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
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

        /* Tags / Pills de selección */
        span[data-baseweb="tag"] {
            background-color: #E30613 !important;
        }

        /* Encabezados */
        .main-title {
            color: #1A1A1A;
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 0px;
            line-height: 1.1;
        }
        .sub-title {
            color: #E30613;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 0px;
        }

        /* Separador */
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
@st.cache_data(ttl=3600)
def load_data():
    file_name = None

    # Búsqueda flexible de archivos Excel para evitar caídas si cambia el nombre del archivo
    possible_files = [
        "1 julio internacion_2.XLSX",
        "1 julio internacion.XLSX",
        "1 julio internacion_2.xlsx",
        "1 julio internacion.xlsx",
    ]

    for pf in possible_files:
        if os.path.exists(pf):
            file_name = pf
            break

    if not file_name:
        for f in os.listdir("."):
            if "julio" in f.lower() and f.endswith((".xlsx", ".XLSX")):
                file_name = f
                break

    if not file_name or not os.path.exists(file_name):
        return None

    df_raw = pd.read_excel(file_name)
    df_raw = df_raw.dropna(how="all").dropna(how="all", axis=1)

    clean_cols = []
    for c in df_raw.columns:
        if pd.isna(c) or str(c).strip().lower() == "nan":
            clean_cols.append("Columna_Sin_Nombre")
        else:
            clean_cols.append(str(c).strip())
    df_raw.columns = clean_cols

    return df_raw


# Control de ejecución seguro
try:
    df = load_data()

    if df is None or df.empty:
        st.error(
            "⚠️ No se encontró el archivo de datos Excel en el servidor. Por favor verifica que el archivo `.XLSX` esté cargado correctamente."
        )
        st.stop()

    # Columna Pedido
    pedido_col = next(
        (c for c in df.columns if "pedido" in c.lower()), df.columns[0]
    )
    df = df[df[pedido_col].notna()].copy()
    df[pedido_col] = df[pedido_col].astype(str).str.strip()
    df = df[
        ~df[pedido_col].isin(["nan", "None", "", "Columna_Sin_Nombre"])
    ].copy()

    # Identificación segura de columnas principales
    sociedad_col = next(
        (c for c in df.columns if "sociedad" in c.lower()),
        df.columns[min(13, len(df.columns) - 1)],
    )
    material_col = next(
        (
            c
            for c in df.columns
            if "tipo de material" in c.lower() or "material" in c.lower()
        ),
        df.columns[min(24, len(df.columns) - 1)],
    )
    tm_col = next(
        (c for c in df.columns if "tm mes real" in c.lower()),
        next(
            (c for c in df.columns if "tm" in c.lower()),
            df.columns[min(28, len(df.columns) - 1)],
        ),
    )
    val_real_col = next(
        (
            c
            for c in df.columns
            if "usd real" in c.lower() or "valor real" in c.lower()
        ),
        df.columns[min(7, len(df.columns) - 1)],
    )
    val_est_col = next(
        (
            c
            for c in df.columns
            if "usd estimado" in c.lower() or "estimado" in c.lower()
        ),
        df.columns[min(6, len(df.columns) - 1)],
    )
    dif_col = next(
        (c for c in df.columns if "diferencia" in c.lower()),
        df.columns[min(8, len(df.columns) - 1)],
    )
    unid_col = next(
        (c for c in df.columns if "unidad de negocio" in c.lower()),
        df.columns[min(1, len(df.columns) - 1)],
    )
    carga_col = next(
        (c for c in df.columns if "tipo de carga" in c.lower()),
        df.columns[min(2, len(df.columns) - 1)],
    )
    denom_col = next(
        (c for c in df.columns if "denominación" in c.lower()),
        df.columns[min(4, len(df.columns) - 1)],
    )
    prov_col = next(
        (c for c in df.columns if "nombre 1" in c.lower()),
        df.columns[min(5, len(df.columns) - 1)],
    )

    # Normalización de textos
    for c in [
        sociedad_col,
        material_col,
        unid_col,
        carga_col,
        denom_col,
        prov_col,
    ]:
        df[c] = df[c].fillna("Sin Información").astype(str).str.strip()

    # Conversión numérica segura
    for c in [tm_col, val_est_col, val_real_col, dif_col]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # 4. ENCABEZADO
    col_logo, col_titulo = st.columns([1, 4], vertical_alignment="center")

    with col_logo:
        if os.path.exists("logo1.png"):
            st.image("logo1.png", use_container_width=True)
        elif os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown(
                """
                <div style="background-color: #E30613; padding: 12px; border-radius: 8px; text-align: center;">
                    <h2 style="color: white !important; margin: 0; font-weight: 900; font-size: 22px;">↗ MULTI</h2>
                    <span style="color: white !important; font-size: 9px; font-weight: 700; letter-spacing: 2px;">LÍDER EN ACERO</span>
                </div>
            """,
                unsafe_allow_html=True,
            )

    with col_titulo:
        st.markdown(
            '<p class="main-title">Panel de Costos de Internación</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="sub-title">Análisis Operativo y Nacionalización de Acero</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # 5. FILTROS INDEPENDIENTES Y MULTIDIRECCIONALES
    with st.expander("🔍 **FILTROS DE BÚSQUEDA INTERACTIVOS**", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        if "f_soc" not in st.session_state:
            st.session_state.f_soc = []
        if "f_uni" not in st.session_state:
            st.session_state.f_uni = []
        if "f_car" not in st.session_state:
            st.session_state.f_car = []
        if "f_mat" not in st.session_state:
            st.session_state.f_mat = []

        df_soc = df.copy()
        if st.session_state.f_uni:
            df_soc = df_soc[df_soc[unid_col].isin(st.session_state.f_uni)]
        if st.session_state.f_car:
            df_soc = df_soc[df_soc[carga_col].isin(st.session_state.f_car)]
        if st.session_state.f_mat:
            df_soc = df_soc[df_soc[material_col].isin(st.session_state.f_mat)]
        opts_soc = sorted(
            [x for x in df_soc[sociedad_col].unique() if str(x) != "nan"]
        )

        df_uni = df.copy()
        if st.session_state.f_soc:
            df_uni = df_uni[df_uni[sociedad_col].isin(st.session_state.f_soc)]
        if st.session_state.f_car:
            df_uni = df_uni[df_uni[carga_col].isin(st.session_state.f_car)]
        if st.session_state.f_mat:
            df_uni = df_uni[df_uni[material_col].isin(st.session_state.f_mat)]
        opts_uni = sorted(
            [x for x in df_uni[unid_col].unique() if str(x) != "nan"]
        )

        df_car = df.copy()
        if st.session_state.f_soc:
            df_car = df_car[df_car[sociedad_col].isin(st.session_state.f_soc)]
        if st.session_state.f_uni:
            df_car = df_car[df_car[unid_col].isin(st.session_state.f_uni)]
        if st.session_state.f_mat:
            df_car = df_car[df_car[material_col].isin(st.session_state.f_mat)]
        opts_car = sorted(
            [x for x in df_car[carga_col].unique() if str(x) != "nan"]
        )

        df_mat = df.copy()
        if st.session_state.f_soc:
            df_mat = df_mat[df_mat[sociedad_col].isin(st.session_state.f_soc)]
        if st.session_state.f_uni:
            df_mat = df_mat[df_mat[unid_col].isin(st.session_state.f_uni)]
        if st.session_state.f_car:
            df_mat = df_mat[df_mat[carga_col].isin(st.session_state.f_car)]
        opts_mat = sorted(
            [x for x in df_mat[material_col].unique() if str(x) != "nan"]
        )

        with col_f1:
            sociedades = st.multiselect(
                "1. Sociedad",
                options=opts_soc,
                key="f_soc",
                placeholder="Todas las Sociedades",
            )
        with col_f2:
            unidades = st.multiselect(
                "2. Unidad de Negocio",
                options=opts_uni,
                key="f_uni",
                placeholder="Todas las Unidades",
            )
        with col_f3:
            cargas = st.multiselect(
                "3. Tipo de Carga",
                options=opts_car,
                key="f_car",
                placeholder="Todos los Tipos",
            )
        with col_f4:
            materiales = st.multiselect(
                "4. Tipo de Material",
                options=opts_mat,
                key="f_mat",
                placeholder="Todos los Materiales",
            )

    df_filtered = df.copy()
    if sociedades:
        df_filtered = df_filtered[df_filtered[sociedad_col].isin(sociedades)]
    if unidades:
        df_filtered = df_filtered[df_filtered[unid_col].isin(unidades)]
    if cargas:
        df_filtered = df_filtered[df_filtered[carga_col].isin(cargas)]
    if materiales:
        df_filtered = df_filtered[df_filtered[material_col].isin(materiales)]

    if df_filtered.empty:
        st.warning(
            "No hay registros disponibles para la combinación de filtros seleccionada."
        )
    else:
        # 6. Agrupación por Pedido
        detalle_pedido = df_filtered.groupby(
            pedido_col, as_index=False
        ).agg(
            Denominación=(denom_col, "first"),
            Proveedor=(prov_col, "first"),
            Sociedad=(sociedad_col, "first"),
            Unidad_Negocio=(unid_col, "first"),
            Tipo_Carga=(carga_col, "first"),
            Tipo_Material=(material_col, "first"),
            TM_Real=(tm_col, "first"),
            USD_Estimado=(val_est_col, "sum"),
            USD_Real=(val_real_col, "sum"),
            Diferencia_USD=(dif_col, "sum"),
        )

        detalle_pedido["TM_Real"] = pd.to_numeric(
            detalle_pedido["TM_Real"], errors="coerce"
        ).fillna(0)
        detalle_pedido["Ratio_USD_TM"] = (
            detalle_pedido["USD_Real"] / detalle_pedido["TM_Real"]
        ).fillna(0)

        # 7. Indicadores (KPIs)
        total_oc = detalle_pedido[pedido_col].nunique()
        total_tm_real = detalle_pedido["TM_Real"].sum()
        total_usd_real = detalle_pedido["USD_Real"].sum()
        total_usd_est = detalle_pedido["USD_Estimado"].sum()

        ratio_promedio = (
            total_usd_real / total_tm_real if total_tm_real > 0 else 0
        )
        todos_materiales_base = df[material_col].nunique()
        materiales_activos = detalle_pedido["Tipo_Material"].nunique()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "USD REAL TOTAL",
            f"${total_usd_real:,.2f}",
            delta=f"Vs Est. ${total_usd_est:,.2f}",
            delta_color="off",
        )
        c2.metric("TONELADAS MÉTRICAS", f"{total_tm_real:,.2f} TM")
        c3.metric("RATIO PROMEDIO", f"${ratio_promedio:,.2f} /TM")
        c4.metric(
            "TIPOS DE MATERIAL",
            f"{materiales_activos} / {todos_materiales_base}",
        )

        st.markdown("---")

        # 8. Gráfico por Tipo de Material
        grp_mat = detalle_pedido.groupby("Tipo_Material", as_index=False).agg(
            TM_Real=("TM_Real", "sum"), USD_Real=("USD_Real", "sum")
        )
        grp_mat["Ratio_USD_TM"] = (
            grp_mat["USD_Real"] / grp_mat["TM_Real"]
        ).fillna(0)

        custom_red_grey_scale = [
            "#8D99AE",
            "#ADB5BD",
            "#E63946",
            "#E30613",
            "#990000",
        ]

        fig = px.bar(
            grp_mat.sort_values("Ratio_USD_TM", ascending=False),
            x="Tipo_Material",
            y="Ratio_USD_TM",
            title="Costos por Tonelada Métrica (USD REAL / TM REAL) según Tipo de Material",
            labels={
                "Ratio_USD_TM": "USD REAL / TM Real",
                "Tipo_Material": "Tipo de Material",
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

        # 9. Tabla Detallada
        st.subheader("📋 Detalle de Costos por Pedido (OC) y Denominación")

        detalle_tabla = detalle_pedido.copy()
        detalle_tabla.columns = [
            "Pedido (OC)",
            "Denominación",
            "Proveedor",
            "Sociedad",
            "Unidad Negocio",
            "Tipo Carga",
            "Tipo Material",
            "TM Mes Real",
            "USD Estimado",
            "USD Real",
            "Diferencia ($)",
            "Ratio ($/TM)",
        ]

        for col in [
            "USD Estimado",
            "USD Real",
            "Diferencia ($)",
            "Ratio ($/TM)",
        ]:
            detalle_tabla[col] = detalle_tabla[col].map("${:,.2f}".format)

        for col in ["TM Mes Real"]:
            detalle_tabla[col] = detalle_tabla[col].map("{:,.2f}".format)

        st.dataframe(detalle_tabla, use_container_width=True)

except Exception as e:
    st.error(f"Se ha producido un error inesperado en la aplicación: {e}")
