import os
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración básica
st.set_page_config(
    page_title="Panel de Costos de Internación",
    page_icon="🔴",
    layout="wide",
)


# Ocultar sidebar y ajustar estilos
st.markdown(
    """
    <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    </style>
""",
    unsafe_allow_html=True,
)


# Buscar archivo Excel en la carpeta actual
def get_excel_filename():
    files = [f for f in os.listdir(".") if f.lower().endswith((".xlsx", ".xls"))]
    if not files:
        return None
    # Priorizar archivos que contengan "julio" o "internacion"
    for f in files:
        if "julio" in f.lower() or "internacion" in f.lower():
            return f
    return files[0]


excel_file = get_excel_filename()

if not excel_file:
    st.error(
        "❌ **Error: No se encontró ningún archivo Excel en el repositorio.**"
    )
    st.info(
        "Por favor, sube el archivo Excel (`.xlsx`) a la raíz de tu repositorio en GitHub junto a `app.py`."
    )
    st.stop()

st.success(f"📂 Archivo detectado correctamente: `{excel_file}`")


# Carga de datos
@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)


try:
    df_raw = load_data(excel_file)
except Exception as e:
    st.error(f"❌ Error al abrir el archivo Excel con pandas: {e}")
    st.stop()

# Limpieza inicial
df = df_raw.dropna(how="all").dropna(how="all", axis=1).copy()
clean_cols = [
    "Columna_Sin_Nombre"
    if (pd.isna(c) or str(c).strip().lower() == "nan")
    else str(c).strip()
    for c in df.columns
]
df.columns = clean_cols

# Identificación flexible de columnas por palabras clave
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
df = df[~df[pedido_col].isin(["nan", "None", "", "Columna_Sin_Nombre"])].copy()

# Saneamiento de textos y números
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

# Título y Encabezado
st.title("Panel de Costos de Internación")
st.caption("Análisis Operativo y Nacionalización de Acero")
st.divider()

# Filtros en Cascada
st.subheader("🔍 Filtros de Búsqueda")
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    soc_opts = sorted(list(df[sociedad_col].unique()))
    soc_sel = st.multiselect("1. Sociedad", soc_opts, default=soc_opts)

df_f1 = df[df[sociedad_col].isin(soc_sel)]

with col_f2:
    uni_opts = sorted(list(df_f1[unid_col].unique()))
    uni_sel = st.multiselect("2. Unidad de Negocio", uni_opts, default=uni_opts)

df_f2 = df_f1[df_f1[unid_col].isin(uni_sel)]

with col_f3:
    car_opts = sorted(list(df_f2[carga_col].unique()))
    car_sel = st.multiselect("3. Tipo de Carga", car_opts, default=car_opts)

df_f3 = df_f2[df_f2[carga_col].isin(car_sel)]

with col_f4:
    mat_opts = sorted(list(df_f3[material_col].unique()))
    mat_sel = st.multiselect("4. Tipo de Material", mat_opts, default=mat_opts)

df_filtered = df_f3[df_f3[material_col].isin(mat_sel)].copy()

if df_filtered.empty:
    st.warning("No hay registros para la combinación de filtros seleccionada.")
else:
    # Agrupación por Pedido
    detalle = df_filtered.groupby(pedido_col, as_index=False).agg(
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

    detalle["TM_Real"] = pd.to_numeric(
        detalle["TM_Real"], errors="coerce"
    ).fillna(0)
    detalle["Ratio_USD_TM"] = (
        detalle["USD_Real"] / detalle["TM_Real"]
    ).fillna(0)

    # Indicadores KPIs
    tot_tm = detalle["TM_Real"].sum()
    tot_usd_real = detalle["USD_Real"].sum()
    tot_usd_est = detalle["USD_Estimado"].sum()
    ratio_prom = tot_usd_real / tot_tm if tot_tm > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("USD REAL TOTAL", f"${tot_usd_real:,.2f}")
    k2.metric("USD ESTIMADO TOTAL", f"${tot_usd_est:,.2f}")
    k3.metric("TONELADAS MÉTRICAS", f"{tot_tm:,.2f} TM")
    k4.metric("RATIO PROMEDIO", f"${ratio_prom:,.2f} /TM")

    st.divider()

    # Gráfico
    grp_mat = detalle.groupby("Tipo_Material", as_index=False).agg(
        TM_Real=("TM_Real", "sum"), USD_Real=("USD_Real", "sum")
    )
    grp_mat["Ratio_USD_TM"] = (
        grp_mat["USD_Real"] / grp_mat["TM_Real"]
    ).fillna(0)

    fig = px.bar(
        grp_mat.sort_values("Ratio_USD_TM", ascending=False),
        x="Tipo_Material",
        y="Ratio_USD_TM",
        title="Ratio USD REAL / TM REAL según Tipo de Material",
        text_auto=".2f",
        labels={
            "Ratio_USD_TM": "USD / TM",
            "Tipo_Material": "Tipo de Material",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla
    st.subheader("📋 Detalle por Pedido")
    st.dataframe(detalle, use_container_width=True)
