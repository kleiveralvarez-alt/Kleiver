import os
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="Panel de Costos de Internación | MULTI",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Estilos personalizados (CSS) - Ocultar Sidebar y Maximizar Pantalla
st.markdown(
    """
    <style>
        /* Ocultar Sidebar lateral */
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Ajuste de márgenes superiores para evitar cortes */
        .block-container {
            padding-top: 2rem !important;
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

    # Eliminar filas y columnas totalmente vacías
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

    # Columna Pedido
    pedido_col = next(
        (c for c in df.columns if "pedido" in c.lower()), df.columns[0]
    )
    df = df[df[pedido_col].notna()].copy()
    df[pedido_col] = df[pedido_col].astype(str).str.strip()
    df = df[
        ~df[pedido_col].isin(["nan", "None", "", "Columna_Sin_Nombre"])
    ].copy()

    # Columna N (índice 13) - Sociedad
    sociedad_col = next(
        (c for c in df.columns if "sociedad" in c.lower()),
        df.columns[min(13, len(df.columns) - 1)],
    )

    # Columna Y (índice 24) - Tipo de Material
    material_col = next(
        (
            c
            for c in df.columns
            if "tipo de material" in c.lower() or "material" in c.lower()
        ),
        df.columns[min(24, len(df.columns) - 1)],
    )

    # Columna AC (índice 28) - TM MES REAL
    tm_col = next(
        (c for c in df.columns if "tm mes real" in c.lower()),
        next(
            (c for c in df.columns if "tm" in c.lower()),
            df.columns[min(28, len(df.columns) - 1)],
        ),
    )

    # USD REAL y USD ESTIMADO
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

    # Otras columnas secundarias
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

    # Conversión numérica
    for c in [tm_col, val_est_col, val_real_col, dif_col]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # 4. ENCABEZADO FIJO CON LOGO Y TÍTULO
    col_logo, col_titulo = st.columns([1, 4])

    with col_logo:
        if os.path.exists("logo1.png"):
            st.image("logo1.png", width=220)
        elif os.path.exists("logo.png"):
            st.image("logo.png", width=220)
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

    # 5. FILTROS EN CASCADA (DEPENDIENTES)
    with st.expander("🔍 **FILTROS DE BÚSQUEDA (CASCADA)**", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        # Nivel 1: Sociedad
        with col_f1:
            sociedades_opt = sorted(
                [x for x in df[sociedad_col].unique() if str(x) != "nan"]
            )
            sociedades = st.multiselect(
                "1. Sociedad", options=sociedades_opt, default=sociedades_opt
            )

        # Filtrado para Nivel 2
        df_lvl1 = df[df[sociedad_col].isin(sociedades)]

        # Nivel 2: Unidad de Negocio
        with col_f2:
            unidades_opt = sorted(
                [x for x in df_lvl1[unid_col].unique() if str(x) != "nan"]
            )
            unidades = st.multiselect(
                "2. Unidad de Negocio",
                options=unidades_opt,
                default=unidades_opt,
            )

        # Filtrado para Nivel 3
        df_lvl2 = df_lvl1[df_lvl1[unid_col].isin(unidades)]

        # Nivel 3: Tipo de Carga
        with col_f3:
            cargas_opt = sorted(
                [x for x in df_lvl2[carga_col].unique() if str(x) != "nan"]
            )
            cargas = st.multiselect(
                "3. Tipo de Carga", options=cargas_opt, default=cargas_opt
            )

        # Filtrado para Nivel 4
        df_lvl3 = df_lvl2[df_lvl2[carga_col].isin(cargas)]

        # Nivel 4: Tipo de Material
        with col_f4:
            materiales_opt = sorted(
                [x for x in df_lvl3[material_col].unique() if str(x) != "nan"]
            )
            materiales = st.multiselect(
                "4. Tipo de Material",
                options=materiales_opt,
                default=materiales_opt,
            )

    # Filtro final aplicado
    df_filtered = df_lvl3[df_lvl3[material_col].isin(materiales)].copy()

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

        # Ratio USD / TM exacto usando USD REAL
        detalle_pedido["Ratio_USD_TM"] = (
            detalle_pedido["USD_Real"] / detalle_pedido["TM_Real"]
        ).fillna(0)

        # 7. Indicadores (KPIs)
        total_oc = detalle_pedido[pedido_col].nunique()
        total_tm_real = detalle_pedido["TM_Real"].sum()
        total_usd_real = detalle_pedido["USD_Real"].sum()
        total_usd_est = detalle_pedido["USD_Estimado"].sum()

        # Ratio Promedio General = Suma USD REAL / Suma TM REAL
        ratio_promedio = (
            total_usd_real / total_tm_real if total_tm_real > 0 else 0
        )
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
            "TIPOS DE MATERIAL", f"{materiales_activos} / {len(materiales_opt)}"
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

        # Formato numérico en la tabla
        for col in ["USD Estimado", "USD Real", "Diferencia ($)", "Ratio ($/TM)"]:
            detalle_tabla[col] = detalle_tabla[col].map("${:,.2f}".format)

        for col in ["TM Mes Real"]:
            detalle_tabla[col] = detalle_tabla[col].map("{:,.2f}".format)

        st.dataframe(detalle_tabla, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la aplicación: {e}")
