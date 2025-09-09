import streamlit as st
import graphviz

# ----------------------------
# Config básica de la página
# ----------------------------
st.set_page_config(page_title="VSM Interactivo", layout="wide")

# Paleta (Azul + Blanco + Verde Agua)
COLOR_BG = "#1E3A8A"
COLOR_ACCENT = "#7FFFD4"
COLOR_TEXT = "#FFFFFF"
COLOR_PROC = "#C7F9E8"   # caja proceso
COLOR_INV = "#E3F2FD"    # inventario
COLOR_INFO = "#FFB300"   # flujos de información
COLOR_MATERIAL = "#000000"

# ----------------------------
# Estado inicial (editable)
# ----------------------------
if "procesos" not in st.session_state:
    # Ejemplo parecido a tu imagen
    st.session_state.procesos = [
        {"nombre": "Almacén",   "tc": 30, "tct": 0, "disp": 98, "cap": 27000, "inventario": 2500},
        {"nombre": "Maquinado", "tc": 60, "tct": 0, "disp": 98, "cap": 27000, "inventario": 50},
        {"nombre": "Ensamble",  "tc": 50, "tct": 0, "disp": 98, "cap": 27000, "inventario": 100},
        {"nombre": "Empaque",   "tc": 64, "tct": 0, "disp": 98, "cap": 27000, "inventario": 0},
        {"nombre": "Almacén",   "tc": 100,"tct": 0, "disp": 98, "cap": 27000, "inventario": 0},
    ]

if "info_global" not in st.session_state:
    st.session_state.info_global = {
        "lead_times": ["5 días", "30 s", "0.6 días", "45 s", "0.2 días", "54 s", "0 días", "120 s"],
        "proveedor_text": "Semanales",
        "cliente_text": "Diarias"
    }

# ----------------------------
# Sidebar: edición de datos
# ----------------------------
st.sidebar.title("⚙️ Configuración VSM")

# Proveedor / Cliente
st.sidebar.subheader("Proveedor/Cliente")
st.session_state.info_global["proveedor_text"] = st.sidebar.text_input(
    "Frecuencia proveedor", value=st.session_state.info_global["proveedor_text"]
)
st.session_state.info_global["cliente_text"] = st.sidebar.text_input(
    "Frecuencia cliente", value=st.session_state.info_global["cliente_text"]
)

st.sidebar.markdown("---")

# Editor de procesos
st.sidebar.subheader("Procesos")
for i, p in enumerate(st.session_state.procesos):
    with st.sidebar.expander(f"🧱 {p['nombre']}"):
        p["nombre"] = st.text_input(f"Nombre #{i+1}", p["nombre"], key=f"n_{i}")
        col1, col2 = st.columns(2)
        with col1:
            p["tc"]  = st.number_input("TC (s)", 0, 100000, int(p["tc"]), key=f"tc_{i}")
            p["tct"] = st.number_input("TCT (s)", 0, 100000, int(p["tct"]), key=f"tct_{i}")
        with col2:
            p["disp"] = st.number_input("Disponibilidad (%)", 0, 100, int(p["disp"]), key=f"disp_{i}")
            p["cap"]  = st.number_input("Capacidad (u/día)", 0, 10**9, int(p["cap"]), key=f"cap_{i}")
        p["inventario"] = st.number_input("Inventario frente al proceso (u)", 0, 10**9, int(p["inventario"]), key=f"inv_{i}")

# Botones para agregar / quitar
col_add, col_del = st.sidebar.columns(2)
with col_add:
    if st.button("➕ Agregar proceso al final"):
        st.session_state.procesos.append({"nombre": "Nuevo Proceso", "tc": 0, "tct": 0, "disp": 100, "cap": 0, "inventario": 0})
with col_del:
    if st.button("➖ Eliminar último"):
        if st.session_state.procesos:
            st.session_state.procesos.pop()

st.sidebar.markdown("---")
descargar = st.sidebar.checkbox("Habilitar descarga DOT/PNG")

# ----------------------------
# Construcción del DOT (Graphviz)
# ----------------------------
def construir_dot(procesos, info):
    g = graphviz.Digraph(name="VSM", format="png")

    # Estilo global
    g.attr(rankdir="LR", bgcolor="white", fontname="Arial")
    g.attr("node", shape="box", style="filled", color="black", fontname="Arial", fontsize="10")
    g.attr("edge", color=COLOR_MATERIAL)

    # Nodos de información (arriba)
    g.node("Proveedor", "🏭 Proveedor", fillcolor="#F5F5F5")
    g.node("Cliente",   "🏭 Cliente",   fillcolor="#F5F5F5")
    g.node("MRP",       "MRP",          fillcolor="#FFF59D", shape="ellipse")
    g.node("Supervisor","Supervisor de producción", fillcolor="#FFD54F")

    # Etiquetas de camiones (texto simple)
    g.node("TruckIn",  f"🚚 {info['proveedor_text']}",  fillcolor="#FFFFFF", shape="plaintext")
    g.node("TruckOut", f"🚚 {info['cliente_text']}",    fillcolor="#FFFFFF", shape="plaintext")

    # Conectar info
    g.edge("Proveedor", "MRP", label="Forecast / Email", color=COLOR_INFO, style="dashed")
    g.edge("Cliente",   "MRP", label="Orden de compra",  color=COLOR_INFO, style="dashed")
    g.edge("MRP", "Supervisor", color=COLOR_INFO, style="dashed")
    # Supervisor a cada proceso (línea punteada)
    for i in range(len(procesos)):
        g.edge("Supervisor", f"P{i}", color=COLOR_INFO, style="dashed")

    # Cinta transportadora (material): Proveedor -> Procesos -> Cliente
    # Nodo inicial de material: Almacén/entrada
    g.node("Entrada", "📦 Recepción / Almacén inicial", fillcolor=COLOR_INV)

    # Crear procesos + inventarios como triángulos
    prev = "Entrada"
    for i, p in enumerate(procesos):
        # Inventario antes del proceso (triángulo)
        inv_id = f"I{i}"
        g.node(inv_id, f"▲\n{p['inventario']} unid.", shape="triangle", fillcolor=COLOR_INV)

        g.edge(prev, inv_id)  # material hacia inventario

        # Caja de proceso (con ficha)
        ficha = f"TC: {p['tc']} s\\nTCT: {p['tct']} s\\nDispon: {p['disp']}%\\nTD: {p['cap']}/día"
        g.node(f"P{i}", f"{p['nombre']}\\n{ficha}", fillcolor=COLOR_PROC)

        # Conexión inventario -> proceso
        g.edge(inv_id, f"P{i}")

        # Pasar al siguiente
        prev = f"P{i}"

    # Salida hacia almacén final y cliente
    g.node("Salida", "📦 Almacén final", fillcolor=COLOR_INV)
    g.edge(prev, "Salida")
    g.edge("Salida", "Cliente")

    # Camiones como texto cerca de extremos
    g.edge("Proveedor", "Entrada", label="", color=COLOR_MATERIAL)
    g.edge("Salida", "TruckOut", style="invis")  # solo para posicionar el texto

    # Línea inferior con lead times (texto decorativo)
    # En Graphviz es más fácil como nodo plaintext
    lt = "   ".join(info["lead_times"])
    g.node("LT", f"LT: {lt}", shape="plaintext")

    return g

dot = construir_dot(st.session_state.procesos, st.session_state.info_global)

# ----------------------------
# Render en pantalla
# ----------------------------
st.title("📊 VSM Interactivo (Value Stream Mapping)")
st.caption("Edita procesos, inventarios y flujos desde la barra lateral. El diagrama se actualiza al vuelo.")

st.graphviz_chart(dot)

# ----------------------------
# Descargas (opcional)
# ----------------------------
if descargar:
    # Cadena DOT
    dot_src = dot.source
    st.download_button("⬇️ Descargar DOT", data=dot_src, file_name="vsm.dot", mime="text/plain")

    # Render PNG temporal (requiere Graphviz instalado en el sistema)
    try:
        png_bytes = dot.pipe(format="png")
        st.download_button("⬇️ Descargar PNG", data=png_bytes, file_name="vsm.png", mime="image/png")
    except Exception as e:
        st.info("Para exportar PNG necesitas tener Graphviz instalado en el servidor/sistema.")
        st.code(str(e))
