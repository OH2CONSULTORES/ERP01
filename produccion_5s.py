import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Rutas para guardar datos
DATA_DIR = "data"
EVALUACIONES_FILE = os.path.join(DATA_DIR, "evaluaciones_5s.csv")
IMPLEMENTACION_FILE = os.path.join(DATA_DIR, "implementacion_5s.csv")
AUDITORIAS_FILE = os.path.join(DATA_DIR, "auditorias_5s.csv")

os.makedirs(DATA_DIR, exist_ok=True)

def cargar_datos(file_path, columnas):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columnas)

def guardar_datos(df, file_path):
    df.to_csv(file_path, index=False)

# ================== MÓDULO 1: CAPACITACIÓN ==================
def modulo_capacitacion():
    st.subheader("📚 Capacitación 5S")

    archivo = st.file_uploader("Subir presentación (PPT/PPTX/PDF)", type=["ppt", "pptx", "pdf"])
    if archivo:
        os.makedirs("capacitacion", exist_ok=True)
        ruta = os.path.join("capacitacion", archivo.name)
        with open(ruta, "wb") as f:
            f.write(archivo.read())
        st.success(f"Archivo '{archivo.name}' guardado.")
        st.download_button("📥 Descargar", data=open(ruta, "rb"), file_name=archivo.name)

    enlace_youtube = st.text_input("Enlace de YouTube para capacitación")
    if enlace_youtube:
        st.video(enlace_youtube)

    st.markdown("---")
    st.subheader("📝 Evaluación de Conocimiento")

    preguntas = [
        "¿Qué significa Seiri?",
        "¿Qué significa Seiton?",
        "¿Qué significa Seiso?",
        "¿Qué significa Seiketsu?",
        "¿Qué significa Shitsuke?"
    ]
    nombre = st.text_input("Nombre del trabajador")
    if nombre:
        respuestas = []
        for i, p in enumerate(preguntas):
            respuestas.append(st.text_input(f"{i+1}. {p}"))

        if st.button("Enviar evaluación"):
            correctas = ["Clasificar", "Ordenar", "Limpiar", "Estandarizar", "Disciplina"]
            puntaje = sum([1 for i in range(len(correctas)) if respuestas[i].strip().lower() == correctas[i].lower()])

            df = cargar_datos(EVALUACIONES_FILE, ["Fecha", "Trabajador", "Puntaje"])
            df.loc[len(df)] = [datetime.now().strftime("%Y-%m-%d %H:%M"), nombre, puntaje]
            guardar_datos(df, EVALUACIONES_FILE)

            st.success(f"Puntaje: {puntaje}/{len(correctas)}")
            if puntaje >= 4:
                st.success("✅ ¡Aprobado!")
            else:
                st.error("❌ No aprobado, repetir capacitación.")

    if os.path.exists(EVALUACIONES_FILE):
        st.subheader("📊 Historial de evaluaciones")
        st.dataframe(cargar_datos(EVALUACIONES_FILE, ["Fecha", "Trabajador", "Puntaje"]))

# ================== MÓDULO 2: IMPLEMENTACIÓN ==================
def modulo_implementacion():
    st.subheader("🛠 Implementación 5S")

    area = st.text_input("Área de implementación")
    responsable = st.text_input("Responsable")
    etapa = st.selectbox("Etapa 5S", ["Seiri", "Seiton", "Seiso", "Seiketsu", "Shitsuke"])
    fecha = st.date_input("Fecha")
    checklist = st.text_area("Checklist y observaciones")
    evidencia = st.file_uploader("Evidencia fotográfica", type=["jpg", "png", "jpeg"])

    if st.button("Guardar implementación"):
        df = cargar_datos(IMPLEMENTACION_FILE, ["Fecha", "Área", "Responsable", "Etapa", "Checklist", "Evidencia"])
        ev_file = evidencia.name if evidencia else ""
        df.loc[len(df)] = [fecha.strftime("%Y-%m-%d"), area, responsable, etapa, checklist, ev_file]

        guardar_datos(df, IMPLEMENTACION_FILE)

        if evidencia:
            os.makedirs("evidencias", exist_ok=True)
            with open(os.path.join("evidencias", evidencia.name), "wb") as f:
                f.write(evidencia.read())

        st.success("Implementación registrada.")

    if os.path.exists(IMPLEMENTACION_FILE):
        st.subheader("📋 Historial de implementación")
        st.dataframe(cargar_datos(IMPLEMENTACION_FILE, ["Fecha", "Área", "Responsable", "Etapa", "Checklist", "Evidencia"]))

# ================== MÓDULO 3: AUDITORÍA ==================
def modulo_auditoria():
    st.subheader("🔍 Auditoría 5S")

    area = st.text_input("Área auditada")
    responsable = st.text_input("Auditor")
    fecha = st.date_input("Fecha de auditoría")
    hallazgos = st.text_area("Hallazgos y observaciones")
    puntaje = st.slider("Puntaje (%)", 0, 100, 80)
    evidencia = st.file_uploader("Evidencia fotográfica", type=["jpg", "png", "jpeg"])

    if st.button("Guardar auditoría"):
        df = cargar_datos(AUDITORIAS_FILE, ["Fecha", "Área", "Auditor", "Hallazgos", "Puntaje", "Evidencia"])
        ev_file = evidencia.name if evidencia else ""
        df.loc[len(df)] = [fecha.strftime("%Y-%m-%d"), area, responsable, hallazgos, puntaje, ev_file]

        guardar_datos(df, AUDITORIAS_FILE)

        if evidencia:
            os.makedirs("auditorias", exist_ok=True)
            with open(os.path.join("auditorias", evidencia.name), "wb") as f:
                f.write(evidencia.read())

        st.success("Auditoría registrada.")

    if os.path.exists(AUDITORIAS_FILE):
        st.subheader("📜 Historial de auditorías")
        st.dataframe(cargar_datos(AUDITORIAS_FILE, ["Fecha", "Área", "Auditor", "Hallazgos", "Puntaje", "Evidencia"]))

# ================== FUNCIÓN PRINCIPAL ==================
def mostrar_5s():
    st.header("🛠 Sistema 5S")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📚 Capacitación", key="btn_capacitacion"):
            st.session_state["opcion_5s"] = "capacitacion"

    with col2:
        if st.button("🛠 Implementación", key="btn_implementacion"):
            st.session_state["opcion_5s"] = "implementacion"

    with col3:
        if st.button("📋 Auditoría", key="btn_auditoria"):
            st.session_state["opcion_5s"] = "auditoria"

    # Mostrar el módulo según lo que se eligió
    if "opcion_5s" in st.session_state:
        if st.session_state["opcion_5s"] == "capacitacion":
            modulo_capacitacion()
        elif st.session_state["opcion_5s"] == "implementacion":
            modulo_implementacion()
        elif st.session_state["opcion_5s"] == "auditoria":
            modulo_auditoria()