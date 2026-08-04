import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Panel de Costos de Internación",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Panel de Costos de Internación")
st.markdown(
    "Desglose de costos reales de nacionalización por tipo de carga, unidad de negocio, país y grupo de artículo, expresados en costo por tonelada métrica (TM)."
)


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

    # Sidebar - Filtros
    st.sidebar.header("🔍 Filtros de Búsqueda")

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

    # Filtrado dinámico
    df_filtered = df[
        (df["Unidad de negocio"].isin(unidades))
        & (df["Tipo de carga"].isin(cargas))
        & (df["Nombre Grupo art."].isin(grupos))
        & (df["PAIS"].isin(paises))
    ]

    # Cálculos globales
    total_oc = df_filtered["Pedido"].nunique()
    total_tm_recibida = df_filtered["Ctd. TM Recibida"].sum()
    total_monto_real = df_filtered["Valor Real $"].sum()
    total_monto_est = df_filtered["Valor Estimado $"].sum()
    ratio_promedio = (
        total_monto_real / total_tm_recibida if total_tm_recibida > 0 else 0
    )
    grupos_activos = df_filtered["Nombre Grupo art."].nunique()

    # Indicadores (KPIs)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "COSTO REAL TOTAL",
        f"${total_monto_real:,.0f}",
        delta=f"Vs Est. ${total_monto_est:,.0f}",
    )
    c2.metric("TONELADAS MÉTRICAS", f"{total_tm_recibida:,.1f} TM")
    c3.metric("RATIO PROMEDIO", f"${ratio_promedio:,.2f} /TM")
    c4.metric("GRUPOS ACTIVOS", f"{grupos_activos} / {len(grupos_opt)}")

    st.markdown("---")

    # Gráfico de barras por Grupo de Artículo
    grp_art = (
        df_filtered.groupby("Nombre Grupo art.")
        .agg(
            TM_Recibida=("Ctd. TM Recibida", "sum"),
            Valor_Real_USD=("Valor Real $", "sum"),
        )
        .reset_index()
    )
    grp_art["Ratio_USD_TM"] = grp_art["Valor_Real_USD"] / grp_art["TM_Recibida"]

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
        color_continuous_scale="Reds",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detalle por Pedido y Denominación
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
