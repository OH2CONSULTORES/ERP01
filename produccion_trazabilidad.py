import streamlit as st
import pandas as pd
import plotly.express as px
import json

TRAZABILIDAD_FILE = "data/trazabilidad.json"

def mostrar_trazabilidad():
    st.header("📊 Trazabilidad de Producción")

    # Cargar datos
    try:
        with open(TRAZABILIDAD_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
        df = pd.DataFrame(datos)
    except FileNotFoundError:
        st.warning("No hay registros de trazabilidad.")
        return
    except json.JSONDecodeError:
        st.error("Error al leer el archivo de trazabilidad.")
        return

    if df.empty:
        st.warning("No hay registros de trazabilidad.")
        return

    # Selección de OP
    ops_disponibles = sorted(df["op"].unique())
    ops_seleccionadas = st.multiselect("Selecciona la OP(s)", ops_disponibles)

    if not ops_seleccionadas:
        st.info("Selecciona al menos una OP para continuar.")
        return

    df_filtrado = df[df["op"].isin(ops_seleccionadas)]

    # Selección de indicador
    indicadores = ["mt_utilizada", "merma", "cantidad_final", "setup_time", "cycle_time", "idle_time", "tiempo_total", "personas"]
    indicador = st.selectbox("Selecciona el indicador a mostrar", indicadores)

    # Agrupar datos por etapa
    df_grafico = df_filtrado.groupby("etapa_nueva")[indicador].sum().reset_index()

    # Mostrar tabla
    st.subheader("📋 Datos por etapa")
    st.dataframe(df_grafico)

    # Mostrar gráfica
    st.subheader("📈 Gráfica")
    fig = px.bar(
        df_grafico,
        x="etapa_nueva",
        y=indicador,
        title=f"{indicador} por etapa",
        text_auto=True
    )
    fig.update_layout(xaxis_title="Etapa", yaxis_title=indicador)
    st.plotly_chart(fig, use_container_width=True)
