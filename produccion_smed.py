# smed_module.py
import streamlit as st
import sqlite3
import time
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import os

# =======================
# BASE DE DATOS
# =======================
def init_db():
    conn = sqlite3.connect("produccion_smed.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS smed_implementaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT,
                    maquina TEXT,
                    fecha TEXT
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS smed_actividades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT,
                    descripcion TEXT,
                    operadores INTEGER,
                    tiempo REAL,
                    tipo TEXT,
                    mejora TEXT,
                    foto_path TEXT
                )''')
    conn.commit()
    conn.close()

# =======================
# FUNCIONES AUXILIARES
# =======================
def guardar_implementacion(version, maquina):
    conn = sqlite3.connect("produccion_smed.db")
    c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO smed_implementaciones (version, maquina, fecha) VALUES (?, ?, ?)", 
              (version, maquina, fecha))
    conn.commit()
    conn.close()

def guardar_actividad(version, descripcion, operadores, tiempo, tipo, mejora, foto_path=None):
    conn = sqlite3.connect("produccion_smed.db")
    c = conn.cursor()
    c.execute("INSERT INTO smed_actividades (version, descripcion, operadores, tiempo, tipo, mejora, foto_path) VALUES (?, ?, ?, ?, ?, ?, ?)", 
              (version, descripcion, operadores, tiempo, tipo, mejora, foto_path))
    conn.commit()
    conn.close()

def exportar_pdf(version):
    conn = sqlite3.connect("produccion_smed.db")
    c = conn.cursor()
    c.execute("SELECT * FROM smed_actividades WHERE version=?", (version,))
    actividades = c.fetchall()
    conn.close()

    filename = f"smed_{version}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Reporte SMED - Versión {version}", styles["Title"]), Spacer(1, 20)]

    data = [["Descripción", "Operadores", "Tiempo (s)", "Tipo", "Mejora"]]
    for act in actividades:
        data.append([act[2], act[3], act[4], act[5], act[6]])

    table = Table(data)
    table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 1, "black")]))
    story.append(table)
    doc.build(story)

    return filename

# =======================
# MODULO PRINCIPAL
# =======================
def smed_app():
    init_db()
    st.title("📊 Módulo SMED")

    tabs = st.tabs(["Documentación de Actividades", "Secuencia de Actividades y Puesta a Prueba", "Plan de Acción"])

    # TAB 1
    with tabs[0]:
        st.subheader("📌 Documentación de Actividades")

        version = st.text_input("Versión de implementación (código de rastreo)")
        maquina = st.text_input("Etapa o máquina a aplicar SMED")

        if st.button("Guardar implementación"):
            if version and maquina:
                guardar_implementacion(version, maquina)
                st.success(f"Implementación {version} guardada en {maquina}")
            else:
                st.warning("Debes ingresar versión y máquina")

        st.write("---")
        st.subheader("➕ Añadir Actividad")

        descripcion = st.text_area("Descripción de actividad")
        operadores = st.number_input("Cantidad de operadores", min_value=1, step=1)
        
        # Cronómetro
        if "start_time" not in st.session_state:
            st.session_state.start_time = None
        if st.button("▶ Iniciar Cronómetro"):
            st.session_state.start_time = time.time()
        if st.button("⏹ Detener Cronómetro"):
            if st.session_state.start_time:
                elapsed = time.time() - st.session_state.start_time
                st.session_state.tiempo = elapsed
                st.success(f"Tiempo registrado: {elapsed:.2f} segundos")
                st.session_state.start_time = None

        tiempo = st.session_state.get("tiempo", 0)

        tipo = st.radio("Tipo de actividad", ["Interna", "Externa"])
        mejora = st.text_area("Descripción de la mejora a realizar")
        foto = st.file_uploader("Subir foto (opcional)", type=["jpg", "png"])

        foto_path = None
        if foto:
            os.makedirs("fotos", exist_ok=True)
            foto_path = os.path.join("fotos", foto.name)
            with open(foto_path, "wb") as f:
                f.write(foto.getbuffer())

        if st.button("Guardar Actividad"):
            if version and descripcion:
                guardar_actividad(version, descripcion, operadores, tiempo, tipo, mejora, foto_path)
                st.success("Actividad guardada ✅")
            else:
                st.warning("Debes ingresar versión y descripción")

        st.write("---")
        st.subheader("📜 Historial de actividades")
        conn = sqlite3.connect("produccion_smed.db")
        c = conn.cursor()
        c.execute("SELECT * FROM smed_actividades WHERE version=?", (version,))
        actividades = c.fetchall()
        conn.close()
        st.table(actividades)

        if st.button("📄 Exportar PDF"):
            if version:
                filename = exportar_pdf(version)
                st.success(f"Reporte exportado: {filename}")

    # TAB 2
    with tabs[1]:
        st.subheader("📊 Secuencia de Actividades y Puesta a Prueba")

        version_sel = st.text_input("Ingrese número de versión para cargar actividades")
        if st.button("Cargar actividades"):
            conn = sqlite3.connect("produccion_smed.db")
            c = conn.cursor()
            c.execute("SELECT descripcion, tiempo, tipo FROM smed_actividades WHERE version=?", (version_sel,))
            acts = c.fetchall()
            conn.close()
            st.write("Actividades registradas:")
            st.dataframe(acts)

            # Aquí se puede extender con gráficos tipo Gantt
            # TODO: Implementar Gantt con Plotly

    # TAB 3
    with tabs[2]:
        st.subheader("📝 Plan de Acción")
        st.write("Aquí se podrían ingresar responsables, fechas y seguimiento de acciones correctivas.")
