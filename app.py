import os
import sys

# Captura de errores críticos durante la importación
try:
    import pandas as pd
    import plotly.express as px
    import streamlit as st
except Exception as e:
    import streamlit as st

    st.error(f"Error al importar librerías: {e}")
    st.stop()

# Configuración de página
st.set_page_config(
    page_title="Panel de Costos de Internación",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos CSS
st.markdown(
    """
    <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        [data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    </style>
""",
    unsafe_allow_html=True,
)


# Búsqueda automática del archivo de datos
def cargar_datos():
    archivos = [
        f for f in os.listdir(".") if f.lower().endswith((".xlsx", ".xls"))
    ]
    if not archivos:
        st.error("No se encontró ningún archivo Excel (.xlsx) en el repositorio.")
        st.stop()

    # Priorizar el archivo especificado
    archivo_target = None
    for f in archivos:
        if "internacion para dash" in f.lower():
            archivo_target = f
            break
    if not archivo_target:
        archivo_target = archivos[0]

    return pd.read_excel(archivo_target), archivo_target


try:
    df_raw, nombre_archivo = cargar_datos()

    # Encabezado
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        if os.path.exists("logo1.png"):
            st.image("logo1.png", width=180)
        elif os.path.exists("logo.png"):
            st.image("logo.png", width=180)

    with col_titulo:
        st.title("Panel de Costos de Internación")
        st.caption(f"Archivo cargado: {nombre_archivo}")

    st.divider()

    # Limpieza
    df = df_raw.dropna(how="all").dropna(how="all", axis=1).copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Mapeo por coincidencia de texto
    cols = list(df.columns)

    def obtener_columna(keywords, idx_defecto):
        for kw in keywords:
            for c in cols:
                if kw.lower() in c.lower():
                    return c
        return cols[min(idx_defecto, len(cols) - 1)]

    pedido_col = obtener_columna(["pedido", "oc"], 0)
    unid_col = obtener_columna(["unidad de negocio", "unidad"], 1)
    carga_col = obtener_columna(["tipo de carga", "carga"], 2)
    denom_col = obtener_columna(["denominación", "denominacion"], 4)
    prov_col = obtener_columna(["nombre 1", "proveedor"], 5)
    val_est_col = obtener_columna(["usd estimado", "estimado"], 6)
    val_real_col = obtener_columna(["usd real", "valor real"], 7)
    dif_col = obtener_columna(["diferencia"], 8)
    sociedad_col = obtener_columna(["sociedad"], 13)
    material_col = obtener_columna(["tipo de material", "material"], 24)
    tm_col = obtener_columna(["tm mes real", "tm real", "tm"], 28)

    # Filtrar vacíos
    df = df[df[pedido_col].notna()].copy()
    df[pedido_col] = df[pedido_col].astype(str).str.strip()

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

    # Filtros
    st.subheader("🔍 Filtros de Búsqueda")
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        opts_soc = sorted(list(df[sociedad_col].unique()))
        sel_soc = st.multiselect("1. Sociedad", opts_soc, default=opts_soc)

    df_sub1 = df[df[sociedad_col].isin(sel_soc)]

    with f2:
        opts_uni = sorted(list(df_sub1[unid_col].unique()))
        sel_uni = st.multiselect(
            "2. Unidad de Negocio", opts_uni, default=opts_uni
        )

    df_sub2 = df_sub1[df_sub1[unid_col].isin(sel_uni)]

    with f3:
        opts_car = sorted(list(df_sub2[carga_col].unique()))
        sel_car = st.multiselect(
            "3. Tipo de Carga", opts_car, default=opts_car
        )

    df_sub3 = df_sub2[df_sub2[carga_col].isin(sel_car)]

    with f4:
        opts_mat = sorted(list(df_sub3[material_col].unique()))
        sel_mat = st.multiselect(
            "4. Tipo de Material", opts_mat, default=opts_mat
        )

    df_final = df_sub3[df_sub3[material_col].isin(sel_mat)].copy()

    if df_final.empty:
        st.warning("No hay datos para la combinación seleccionada.")
    else:
        # Agrupación por pedido
        resumen = df_final.groupby(pedido_col, as_index=False).agg(
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

        resumen["TM_Real"] = pd.to_numeric(
            resumen["TM_Real"], errors="coerce"
        ).fillna(0)
        resumen["Ratio_USD_TM"] = (
            resumen["USD_Real"] / resumen["TM_Real"]
        ).fillna(0)

        # KPIs
        tm_tot = resumen["TM_Real"].sum()
        real_tot = resumen["USD_Real"].sum()
        est_tot = resumen["USD_Estimado"].sum()
        ratio_gen = real_tot / tm_tot if tm_tot > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("USD REAL TOTAL", f"${real_tot:,.2f}")
        k2.metric("USD ESTIMADO TOTAL", f"${est_tot:,.2f}")
        k3.metric("TONELADAS MÉTRICAS", f"{tm_tot:,.2f} TM")
        k4.metric("RATIO PROMEDIO", f"${ratio_gen:,.2f} /TM")

        st.divider()

        # Gráfico
        grp_mat = resumen.groupby("Tipo_Material", as_index=False).agg(
            TM_Real=("TM_Real", "sum"), USD_Real=("USD_Real", "sum")
        )
        grp_mat["Ratio_USD_TM"] = (
            grp_mat["USD_Real"] / grp_mat["TM_Real"]
        ).fillna(0)

        fig = px.bar(
            grp_mat.sort_values("Ratio_USD_TM", ascending=False),
            x="Tipo_Material",
            y="Ratio_USD_TM",
            title="Ratio USD REAL / TM REAL por Material",
            text_auto=".2f",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabla
        st.subheader("📋 Detalle de Pedidos")
        st.dataframe(resumen, use_container_width=True)

except Exception as err:
    st.error(f"Se produjo un error al ejecutar la aplicación: {err}")
