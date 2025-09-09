import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Flujo de Producción - Sankey", layout="wide")

st.title("🌀 Visualización de Flujo de Producción con Sankey")

# =========================
# Definición de etapas y subetapas
# =========================
etapas_definidas = {
    "Compra": ["Proveedor 1", "Proveedor 2"],
    "Logística": ["Recolección"],
    "Transporte": [],
    "Corte": ["Convertidora", "Guillotina"]
}

# =========================
# Función para crear OP
# =========================
def crear_op(nombre_op):
    st.subheader(f"📦 {nombre_op}")
    etapas = st.multiselect(
        f"Selecciona las etapas para {nombre_op}",
        list(etapas_definidas.keys()),
        default=list(etapas_definidas.keys())
    )

    flujo = []
    for etapa in etapas:
        subetapas = etapas_definidas[etapa]
        if subetapas:
            seleccionadas = st.multiselect(
                f"Selecciona subetapas de {etapa} ({nombre_op})",
                subetapas,
                default=subetapas
            )
            for s in seleccionadas:
                flujo.append(f"{etapa} - {s}")
        else:
            flujo.append(etapa)
    return flujo

# =========================
# Crear 2 OP
# =========================
col1, col2 = st.columns(2)
with col1:
    flujo_op1 = crear_op("OP 1")
with col2:
    flujo_op2 = crear_op("OP 2")

# =========================
# Botón para graficar Sankey
# =========================
if st.button("📊 Generar Diagrama Sankey"):
    # Unimos todos los nodos
    nodos = list(set(flujo_op1 + flujo_op2))
    etiquetas = nodos
    indice = {nodo: i for i, nodo in enumerate(nodos)}

    # Creamos enlaces secuenciales por OP
    links_source = []
    links_target = []
    links_value = []
    links_color = []

    def agregar_flujo(flujo, color):
        for i in range(len(flujo)-1):
            links_source.append(indice[flujo[i]])
            links_target.append(indice[flujo[i+1]])
            links_value.append(10)  # peso fijo, podrías usar cantidades reales
            links_color.append(color)

    agregar_flujo(flujo_op1, "rgba(0,128,255,0.5)")  # azul OP1
    agregar_flujo(flujo_op2, "rgba(255,128,0,0.5)")  # naranja OP2

    # Graficamos
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=30,
            thickness=25,
            line=dict(color="black", width=0.8),
            label=etiquetas,
            color="lightgray"
        ),
        link=dict(
            source=links_source,
            target=links_target,
            value=links_value,
            color=links_color
        )
    )])

    fig.update_layout(title_text="🌀 Flujo de Producción (2 OP en paralelo)", font_size=12)
    st.plotly_chart(fig, use_container_width=True)
