import streamlit as st
import sqlite3
import base64
import os
from datetime import datetime

DB_NAME = "logistica_planos.db"
PLANOS_DIR = "planos_guardados"

# Crear carpeta de planos
os.makedirs(PLANOS_DIR, exist_ok=True)

# --- Inicializar base de datos ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS planos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            fecha TEXT,
            ruta TEXT
        )
    """)
    conn.commit()
    conn.close()

def guardar_plano(nombre, archivo):
    ruta = os.path.join(PLANOS_DIR, nombre)
    os.makedirs(PLANOS_DIR, exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(archivo)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO planos (nombre, fecha, ruta) VALUES (?, ?, ?)",
                  (nombre, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ruta))
        conn.commit()
    except sqlite3.IntegrityError:
        st.warning(f"⚠ El archivo '{nombre}' ya existe en la base de datos.")
    conn.close()

def obtener_planos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, nombre, fecha, ruta FROM planos ORDER BY fecha DESC")
    data = c.fetchall()
    conn.close()
    return data

def obtener_plano_por_id(plano_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT ruta FROM planos WHERE id=?", (plano_id,))
    data = c.fetchone()
    conn.close()
    return data[0] if data else None

def eliminar_plano(plano_id):
    ruta = obtener_plano_por_id(plano_id)
    if ruta and os.path.exists(ruta):
        os.remove(ruta)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM planos WHERE id=?", (plano_id,))
    conn.commit()
    conn.close()

def mostrar_visor_glb():
    init_db()

    st.header("🛠 Módulo de Gestión y Visualización de Plano")

    archivo_glb = st.file_uploader("Sube tu archivo GLB", type=["glb", "gltf"])

    if archivo_glb:
        guardar_plano(archivo_glb.name, archivo_glb.read())
        st.success(f"✅ Archivo {archivo_glb.name} guardado correctamente.")
        st.session_state['refresh'] = True  # Para recargar la lista de planos

    planos = obtener_planos()

    if planos:
        st.subheader("📂 Planos guardados")
        cols = st.columns(min(len(planos), 3))

        for i, (pid, nombre, fecha, ruta) in enumerate(planos):
            col = cols[i % 3]
            with col:
                if st.button(f"👁 {nombre}\n📅 {fecha}", key=f"view_{pid}_{i}"):
                    st.session_state['selected_id'] = pid
                if st.button("🗑 Eliminar", key=f"delete_{pid}_{i}"):
                    eliminar_plano(pid)
                    st.warning(f"🗑 Plano '{nombre}' eliminado.")
                    st.session_state.pop("selected_id", None)
                    st.rerun()

    # Mostrar visor solo si hay un archivo seleccionado
    if "selected_id" in st.session_state:
        ruta = obtener_plano_por_id(st.session_state['selected_id'])
        if ruta and os.path.exists(ruta):
            with open(ruta, "rb") as f:
                archivo = f.read()

            glb_base64 = base64.b64encode(archivo).decode("utf-8")
            st.components.v1.html(
                f"""
                <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
                <model-viewer 
                    src="data:model/gltf-binary;base64,{glb_base64}" 
                    alt="Modelo 3D" 
                    auto-rotate 
                    camera-controls 
                    style="width: 100%; height: 600px; background: linear-gradient(135deg, #4da6ff, #cce6ff);">
                </model-viewer>
                """,
                height=650,
            )
        else:
            st.warning("El archivo seleccionado no existe físicamente.")
