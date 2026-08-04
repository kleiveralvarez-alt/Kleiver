import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dashboard OC - Ratio por TM",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Dashboard Interactivo de Ratios por TM")


# Carga de datos flexible
@st.cache_data
def load_data():
    file_name = "1 julio internacion.XLSX"
    if not os.path.exists(file_name):
        for f in os.listdir("."):
            if "julio" in f.lower() and f.endswith((".xlsx", ".XLSX")):
                file_name = f
                break
    return pd.read_excel(file_name)


try:
    df = load_data()

    # Sidebar Filtros
    st.sidebar.header("Filtros de Búsqueda")
    unidades = st.sidebar.multiselect(
        "Unidad de Negocio",
        options=sorted(df["Unidad de negocio"].dropna().unique()),
        default=list(df["Unidad de negocio"].dropna().unique()),
    )

    cargas = st.sidebar.multiselect(
        "Tipo de Carga",
        options=sorted(df["Tipo de carga"].dropna().unique()),
        default=list(df["Tipo de carga"].dropna().unique()),
    )

    # Filtrado
    df_filtered = df[
        (df["Unidad de negocio"].isin(unidades))
        & (df["Tipo de carga"].isin(cargas))
    ]

    # Agrupación
    grp = (
        df_filtered.groupby(
            ["Unidad de negocio", "Tipo de carga", "Nombre Grupo art."]
        )
        .agg(
            OC_Unicas=("Pedido", "nunique"),
            TM_Pedida=("Cantidad TM", "sum"),
            TM_Recibida=("Ctd. TM Recibida", "sum"),
            Valor_Real_USD=("Valor Real $", "sum"),
        )
        .reset_index()
    )

    grp["Ratio_USD_TM_Recibida"] = grp["Valor_Real_USD"] / grp["TM_Recibida"]

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Órdenes de Compra", f"{df_filtered['Pedido'].nunique()}")
    c2.metric("TM Recibidas", f"{grp['TM_Recibida'].sum():,.2f}")
    c3.metric("Monto Real ($)", f"${grp['Valor_Real_USD'].sum():,.2f}")
    ratio_gen = (
        grp["Valor_Real_USD"].sum() / grp["TM_Recibida"].sum()
        if grp["TM_Recibida"].sum() > 0
        else 0
    )
    c4.metric("Ratio Promedio ($/TM)", f"${ratio_gen:,.2f}")

    st.markdown("---")

    # Gráfico
    fig = px.bar(
        grp,
        x="Nombre Grupo art.",
        y="Ratio_USD_TM_Recibida",
        color="Unidad de negocio",
        facet_col="Tipo de carga",
        title="Ratio USD por TM Recibida según Grupo de Artículos",
        labels={"Ratio_USD_TM_Recibida": "USD / TM Recibida ($)"},
        barmode="group",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de Datos
    st.subheader("Detalle por Grupo de Artículos")
    st.dataframe(grp, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la aplicación: {e}")
