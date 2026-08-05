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

# 2. Estilos personalizados (CSS) - Ocultar Sidebar y Ajustar Logo
st.markdown(
    """
    <style>
        /* Ocultar completamente el Sidebar y el botón desplegable */
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Ajuste de márgenes superiores para que el logo no se corte */
        .block-container {
            padding-top: 2.5rem !important;
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

        /* Tags de selección */
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
@st.cache_data
def load_data():
    # Lectura del nuevo archivo indicado
    file_name = "Internacion para Dash julio.xlsx"

    if not os.path.exists(file_name):
        for f in os.listdir("."):
            if "internacion" in f.lower() and f.endswith((".xlsx", ".XLSX")):
                file_name = f
                break

    df_raw = pd.read_excel(file_name)

    # Limpieza básica
    df_raw = df_raw.dropna(how="all").dropna(how="all", axis=1)

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

    # Mapeo de columnas
    cols = list(df.columns)

    def find_col(keywords, default_idx):
        for kw in keywords:
            for c in cols:
                if kw.lower() in c.lower():
                    return c
        return cols[min(default_idx, len(cols) - 1)]

    pedido_col = find_col(["pedido", "oc"], 0)
    unid_col = find_col(["unidad de negocio", "unidad"], 1)
    carga_col = find_col(["tipo de carga", "carga"], 2)
    denom_col = find_col(["denominación", "denominacion"], 4)
    prov_col = find_col(["nombre 1", "proveedor"], 5)
    val_est_col = find_col(["usd estimado", "estimado"], 6)
    val_real_col = find_col(["usd real", "valor real"], 7)
    dif_col = find_col(["diferencia"], 8)
    sociedad_col = find_col(["sociedad"], 13)
    material_col = find_col(["tipo de material", "material"], 24)
    tm_col = find_col(["tm mes real", "tm real", "tm"], 28)

    # Filtrar pedidos válidos
    df = df[df[pedido_col].notna()].copy()
    df[pedido_col] = df[pedido_col].astype(str).str.strip()
    df = df[
        ~df[pedido_col].isin(["nan", "None", "", "Columna_Sin_Nombre"])
    ].copy()

    # Saneamiento
    for c in [
        sociedad_col,
        material_col,
        unid_col,
        carga_col,
        denom_col,
        prov_col,
    ]:
        df[c] = df[c].fillna("Sin Información").astype(str).str.strip()

    for c in [tm_col, val_est_col, val_real_col, dif_col]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # 4. ENCABEZADO CON LOGO COMPLETO Y FIJO
    col_logo, col_titulo = st.columns([1, 4])

    with col_logo:
        if os.path.exists("logo1.png"):
            st.image("logo1.png", width=200)
        elif os.path.exists("logo.png"):
            st.image("logo.png", width=200)
        else:
            st.markdown(
                """
                <div style="background-color: #E30613; padding: 10px; border-radius: 8px; text-align: center;">
                    <h2 style="color: white !important; margin: 0; font-weight: 900; font-size: 20px;">↗ MULTI</h2>
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

    # 5. FILTROS EN CASCADA
    with st.expander("🔍 **FILTROS DE BÚSQUEDA (CASCADA)**", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        with col_f1:
            sociedades_opt = sorted(
                [x for x in df[sociedad_col].unique() if str(x) != "nan"]
            )
            sociedades = st.multiselect(
                "1. Sociedad", options=sociedades_opt, default=sociedades_opt
            )

        df_lvl1 = df[df[sociedad_col].isin(sociedades)]

        with col_f2:
            unidades_opt = sorted(
                [x for x in df_lvl1[unid_col].unique() if str(x) != "nan"]
            )
            unidades = st.multiselect(
                "2. Unidad de Negocio",
                options=unidades_opt,
                default=unidades_opt,
            )

        df_lvl2 = df_lvl1[df_lvl1[unid_col].isin(unidades)]

        with col_f3:
            cargas_opt = sorted(
                [x for x in df_lvl2[carga_col].unique() if str(x) != "nan"]
            )
            cargas = st.multiselect(
                "3. Tipo de Carga", options=cargas_opt, default=cargas_opt
            )

        df_lvl3 = df_lvl2[df_lvl2[carga_col].isin(cargas)]

        with col_f4:
            materiales_opt = sorted(
                [x for x in df_lvl3[material_col].unique() if str(x) != "nan"]
            )
            materiales = st.multiselect(
                "4. Tipo de Material",
                options=materiales_opt,
                default=materiales_opt,
            )

    df_filtered = df_lvl3[df_lvl3[material_col].isin(materiales)].copy()

    if df_filtered.empty:
        st.warning(
            "No hay registros disponibles para los filtros seleccionados."
        )
    else:
        # 6. Agrupación y KPIs
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

        total_tm_real = detalle_pedido["TM_Real"].sum()
        total_usd_real = detalle_pedido["USD_Real"].sum()
        total_usd_est = detalle_pedido["USD_Estimado"].sum()
        ratio_promedio = (
            total_usd_real / total_tm_real if total_tm_real > 0 else 0
        )
        materiales_activos = detalle_pedido["Tipo_Material"].nunique()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("USD REAL TOTAL", f"${total_usd_real:,.2f}")
        c2.metric("TONELADAS MÉTRICAS", f"{total_tm_real:,.2f} TM")
        c3.metric("RATIO PROMEDIO", f"${ratio_promedio:,.2f} /TM")
        c4.metric(
            "TIPOS DE MATERIAL", f"{materiales_activos} / {len(materiales_opt)}"
        )

        st.markdown("---")

        # 7. Gráfico
        grp_mat = detalle_pedido.groupby("Tipo_Material", as_index=False).agg(
            TM_Real=("TM_Real", "sum"), USD_Real=("USD_Real", "sum")
        )
        grp_mat["Ratio_USD_TM"] = (
            grp_mat["USD_Real"] / grp_mat["TM_Real"]
        ).fillna(0)

        fig = px.bar(
            grp_mat.sort_values("Ratio_USD_TM", ascending=False),
            x="Tipo_Material",
            y="Ratio_USD_TM",
            title="Costos por Tonelada Métrica (USD REAL / TM REAL) según Tipo de Material",
            text_auto=".2f",
            color="Ratio_USD_TM",
            color_continuous_scale=[
                "#8D99AE",
                "#ADB5BD",
                "#E63946",
                "#E30613",
                "#990000",
            ],
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#E9ECEF"),
            coloraxis_showscale=False,
        )

        st.plotly_chart(fig, use_container_width=True)

        # 8. Tabla Detallada
        st.subheader("📋 Detalle de Costos por Pedido (OC)")
        st.dataframe(detalle_pedido, use_container_width=True)

except Exception as e:
    st.error(f"Error al procesar la aplicación: {e}")
