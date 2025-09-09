import streamlit as st
import sqlite3
import datetime
import os
from PIL import Image
import pandas as pd
import re

DB_NAME = "produccion_tpm_inspecciones.db"
PHOTO_DIR = "fotos_evidencia"
os.makedirs(PHOTO_DIR, exist_ok=True)

# --- CONEXIÓN A BASE DE DATOS ---
def init_db():   
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inspecciones (
                    id INTEGER PRIMARY KEY,
                    fecha TEXT,
                    maquina TEXT,
                    seccion TEXT,
                    pregunta TEXT,
                    respuesta TEXT,
                    observacion TEXT,
                    foto TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS maquinas (
                    id INTEGER PRIMARY KEY,
                    nombre TEXT,
                    modelo TEXT,
                    fecha_ultimo_mant TEXT,
                    observaciones TEXT,
                    foto TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mantenimientos (
                    id INTEGER PRIMARY KEY,
                    maquina TEXT,
                    tipo TEXT,
                    fecha_programada TEXT,
                    realizado INTEGER,
                    evidencia TEXT,
                    observacion TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE BASE DE DATOS ---
def guardar_respuesta(fecha, maquina, seccion, pregunta, respuesta, observacion, foto_path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO inspecciones (fecha, maquina, seccion, pregunta, respuesta, observacion, foto)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (fecha, maquina, seccion, pregunta, respuesta, observacion, foto_path))
    conn.commit()
    conn.close()

def guardar_maquina(nombre, modelo, fecha_ultimo_mant, observaciones, foto_path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO maquinas (nombre, modelo, fecha_ultimo_mant, observaciones, foto)
                 VALUES (?, ?, ?, ?, ?)""",
              (nombre, modelo, fecha_ultimo_mant, observaciones, foto_path))
    conn.commit()
    conn.close()

def programar_mantenimiento(maquina, tipo, fecha_programada):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO mantenimientos (maquina, tipo, fecha_programada, realizado, evidencia, observacion)
                 VALUES (?, ?, ?, 0, '', '')""",
              (maquina, tipo, fecha_programada))
    conn.commit()
    conn.close()

def limpiar_nombre_archivo(texto):
    texto = re.sub(r'[^\w\s-]', '', texto)
    texto = texto.strip().replace(' ', '_')
    return texto[:50]

# --- DASHBOARD ---
def generar_dashboard_urgente():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM inspecciones WHERE respuesta = 'No'", conn)
    conn.close()
    st.subheader("🚨 Mantenimientos Urgentes")
    if df.empty:
        st.success("No hay acciones urgentes registradas.")
    else:
        urgencias = df.groupby(["maquina", "seccion"]).size().reset_index(name="Cantidad de fallas")
        urgencias = urgencias.sort_values("Cantidad de fallas", ascending=False)
        st.dataframe(urgencias)

def generar_recomendaciones():
    st.subheader("💡 Recomendaciones de mantenimiento")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM inspecciones", conn)
    conn.close()

    for maquina in df["maquina"].unique():
        st.markdown(f"### 🏭 {maquina}")
        df_m = df[df["maquina"] == maquina]
        fallas = df_m[df_m["respuesta"] == "No"]
        preventivos = df_m[df_m["respuesta"] == "N.A."]
        
        if not fallas.empty:
            st.error("🔧 **Correctivos necesarios:**")
            st.write(fallas[["seccion", "pregunta", "observacion"]])
        
        if not preventivos.empty:
            st.warning("📋 **Posibles actividades preventivas omitidas o por revisar:**")
            st.write(preventivos[["seccion", "pregunta", "observacion"]])

def mostrar_calendario_mantenimientos():
    st.subheader("📅 Calendario de mantenimientos")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM mantenimientos", conn)
    conn.close()

    df["fecha_programada"] = pd.to_datetime(df["fecha_programada"])
    df = df.sort_values("fecha_programada")
    st.dataframe(df[["maquina", "tipo", "fecha_programada", "realizado", "observacion"]])

    for _, row in df.iterrows():
        if not row["realizado"]:
            st.markdown(f"🔜 **{row['maquina']}** → {row['tipo']} el `{row['fecha_programada'].date()}`")

# --- FUNCIÓN PRINCIPAL ---
def mostrar_tpm():
    st.header("🛠️ Sistema TPM - Mantenimiento e Inspecciones")

    # --- REGISTRO DE MAQUINAS ---
    st.subheader("📋 Registro de Equipos/Máquinas")
    with st.expander("➕ Agregar nueva máquina"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del equipo")
            modelo = st.text_input("Modelo")
            fecha_mant = st.date_input("Fecha último mantenimiento")
            observ_maquina = st.text_area("Observaciones")
        with col2:
            foto_maquina = st.file_uploader("Foto del equipo", type=["jpg", "png", "jpeg"], key="foto_maquina")

        if st.button("Guardar máquina"):
            foto_path = None
            if foto_maquina:
                foto_path = os.path.join(PHOTO_DIR, f"{nombre}_{modelo}.jpg")
                with open(foto_path, "wb") as f:
                    f.write(foto_maquina.getbuffer())
            guardar_maquina(nombre, modelo, str(fecha_mant), observ_maquina, foto_path)
            st.success("✅ Máquina registrada correctamente")

    # --- FORMULARIO DE INSPECCIÓN TPM ---
    st.subheader("📑 Formulario de Inspección TPM")
    fecha = st.date_input("📅 Fecha de inspección", value=datetime.date.today())

    conn = sqlite3.connect(DB_NAME)
    maquinas = [row[0] for row in conn.execute("SELECT nombre FROM maquinas").fetchall()]
    conn.close()

    maquina = st.selectbox("🔧 Selecciona la máquina", maquinas)
    
    cuestionario = {
        "Cuerpo Principal del Equipo": [
            "Suciedad, polvo, exceso de aceite, lodos o rebabas en partes de contacto, superficies de montaje o posicionadores",
            "Suciedad en estructuras, camas, depósitos de aceite, líneas de transferencia, bandas, etc.",
            "Pernos de referencia o superficies barridas",
            "Suciedad en fixtures, gages, dados, cilindros, tanques, cables, mangueras, etc.",
            "Tornillos, tuercas o rondanas flojas o faltantes",
            "Objetos innecesarios sobre el cuerpo de la máquina",
            "¿Está la máquina firmemente asentada o anclada al piso?"
        ],
        "Dispositivos Auxiliares": [
            "Suciedad, grasa o rebabas en cilindros de aire, válvulas solenoides, transformadores",
            "Micro switches, switches de proximidad, sensores sucios o dañados",
            "Condiciones de motores, bandas, bombas, impulsores, flechas y ventiladores",
            "Condición de superficies de instrumentos, gabinetes e indicadores analógicos o digitales",
            "Alambrado y conductería en mal estado",
            "Fugas de aceite, agua, anticongelante, aire, gas o vapor"
        ],
        "Sistema de Lubricación": [
            "¿Están llenos los depósitos de aceite o a su nivel especificado?",
            "¿Es fácilmente visible el nivel de aceite?",
            "¿Llega el aceite a las partes esenciales?",
            "¿Hay boquillas de lubricación o entradas de aceite dañadas?",
            "¿Hay fugas de aceite en mangueras, tuberías o uniones?",
            "¿Se limpian las aceiteras por dentro y por fuera?"
        ],
        "Sistema Hidráulico": [
            "¿Están llenos los depósitos de aceite o a su nivel especificado?",
            "¿Hace la bomba algún ruido anormal?",
            "¿Están aseguradas las tuercas de las válvulas de alivio, reducción y aceleración?",
            "¿Están operando bien los controles y las válvulas de alivio?",
            "¿Hay alguna distensión o desgaste en las conexiones de las mangueras de alta presión?"
        ],
        "Sistema Eléctrico": [
            "¿Funcionan bien los interruptores de límite?",
            "¿Falta o está fundida alguna luz indicadora o piloto?",
            "¿Están los diagramas de cableado en los paneles de control o tableros eléctricos?",
            "¿Existen cables o tuberías flexibles innecesarias, dañadas o expuestas?"
        ],
        "Elementos de Transferencia de Energía": [
            "¿Golpean las bandas V la parte inferior de las ranuras de las poleas?",
            "¿Hay daños, grietas o desgaste en las bandas?",
            "¿Hay suficiente lubricación entre las espigas y los bujes de las cadenas?",
            "¿Hay sobrecalentamiento o vibración en los rodamientos de la flecha?",
            "¿Están desbalanceadas o flojas o sueltas las uniones?",
            "¿Hay ruido excesivo, calentamiento o vibración en los mecanismos de engranaje?"
        ],
        "Tuercas y Pernos": [
            "¿Son las tuercas y pernos del tipo y tamaño adecuado?",
            "¿Las rondanas son del tamaño correcto y se usan de manera consistente?",
            "¿Sobresalen los tornillos de las tuercas entre 2 y 3 vueltas?",
            "¿Hay tuercas, tornillos, rondanas, seguros, etc. flojos o faltantes?"
        ],
        "Sistema Neumático": [
            "¿Hay alguna fuga en la válvula de paso o de bola?",
            "¿Se observan fugas en válvulas (fugas de aire)?",
            "¿Hay elementos, mangueras o tuberías innecesarias?",
            "¿Están las tuberías y mangueras en orden y fácilmente identificables?",
            "¿Están claramente los calibradores de presión en el ajuste correcto?"
        ]
    }

    for seccion, preguntas in cuestionario.items():
        with st.expander(f"📋 {seccion}"):
            for pregunta in preguntas:
                cols = st.columns([4, 2, 3, 3])
                with cols[0]:
                    st.markdown(f"**{pregunta}**")
                with cols[1]:
                    st.radio("", ["Sí", "No", "N.A."], key=f"r_{seccion}_{pregunta}")
                with cols[2]:
                    st.text_input("Observación", key=f"o_{seccion}_{pregunta}")
                with cols[3]:
                    st.file_uploader("📸 Fotos (múltiples)", type=["png", "jpg", "jpeg"],
                                     accept_multiple_files=True, key=f"f_{seccion}_{pregunta}")
    def limpiar_nombre_archivo(texto):
        texto = re.sub(r'[^\w\s-]', '', texto)  # quita caracteres especiales
        texto = texto.strip().replace(' ', '_')  # espacios a guiones bajos
        return texto[:50]  # limitar largo

    if st.button("💾 Guardar todo el cuestionario", key="guardar_cuestionario"):
        for seccion, preguntas in cuestionario.items():
            for pregunta in preguntas:
                respuesta = st.session_state.get(f"r_{seccion}_{pregunta}", "")
                observacion = st.session_state.get(f"o_{seccion}_{pregunta}", "")
                fotos = st.session_state.get(f"f_{seccion}_{pregunta}", [])

                if fotos:
                    for idx, foto in enumerate(fotos):
                        try:
                            img = Image.open(foto)
                            ext = foto.type.split("/")[-1]
                            maquina_safe = limpiar_nombre_archivo(maquina)
                            fecha_safe = str(fecha).replace(":", "-").replace("/", "-")
                            seccion_safe = limpiar_nombre_archivo(seccion)
                            pregunta_safe = limpiar_nombre_archivo(pregunta)

                            nombre_archivo = f"{maquina_safe}_{fecha_safe}_{seccion_safe}_{pregunta_safe}_{idx}.{ext}"
                            ruta_archivo = os.path.join(PHOTO_DIR, nombre_archivo)

                            img.save(ruta_archivo)
                            guardar_respuesta(str(fecha), maquina, seccion, pregunta, respuesta, observacion, ruta_archivo)
                        except Exception as e:
                            st.error(f"❌ Error al guardar foto de '{pregunta}': {e}")
                else:
                    guardar_respuesta(str(fecha), maquina, seccion, pregunta, respuesta, observacion, None)

        st.success("✅ Todas las respuestas fueron guardadas exitosamente.")

    # --- VER INSPECCIONES REGISTRADAS ---
    st.subheader("📊 Inspecciones Registradas")
    with st.expander("🔍 Filtrar y visualizar inspecciones"):
        conn = sqlite3.connect(DB_NAME)
        data = conn.execute("SELECT fecha, maquina, seccion, pregunta, respuesta, observacion, foto FROM inspecciones").fetchall()
        columns = ["Fecha", "Máquina", "Sección", "Pregunta", "Respuesta", "Observación", "Foto"]
        df = pd.DataFrame(data, columns=columns)
        conn.close()

        fecha_filtro = st.date_input("Filtrar por fecha", value=None)
        if fecha_filtro:
            df = df[df["Fecha"] == str(fecha_filtro)]

        st.dataframe(df)
        for i, row in df.iterrows():
            if row["Foto"] and os.path.exists(row["Foto"]):
                st.image(row["Foto"], caption=f"{row['Máquina']} - {row['Pregunta']}", width=400)

    # Puedes continuar este proyecto si deseas que lo divida en módulos (app.py, mod_inspeccion.py, mod_dashboard.py, etc.)
    def generar_dashboard_urgente():
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM inspecciones WHERE respuesta = 'No'", conn)
        conn.close()
        st.subheader("🚨 Mantenimientos Urgentes")
        if df.empty:
            st.success("No hay acciones urgentes registradas.")
        else:
            urgencias = df.groupby(["maquina", "seccion"]).size().reset_index(name="Cantidad de fallas")
            urgencias = urgencias.sort_values("Cantidad de fallas", ascending=False)
            st.dataframe(urgencias)

    with st.expander("📆 Programar mantenimiento"):
        maquina_mant = st.selectbox("Selecciona máquina", maquinas)
        tipo_mant = st.selectbox("Tipo", ["Preventivo", "Correctivo"])
        fecha_prog = st.date_input("Fecha programada")
        if st.button("📌 Programar"):
            programar_mantenimiento(maquina_mant, tipo_mant, str(fecha_prog))
            st.success("Mantenimiento programado correctamente.")

    def generar_recomendaciones():
        st.subheader("💡 Recomendaciones de mantenimiento")
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM inspecciones", conn)
        conn.close()

        for maquina in df["maquina"].unique():
            st.markdown(f"### 🏭 {maquina}")
            df_m = df[df["maquina"] == maquina]
            fallas = df_m[df_m["respuesta"] == "No"]
            preventivos = df_m[df_m["respuesta"] == "N.A."]
            
            if not fallas.empty:
                st.error("🔧 **Correctivos necesarios:**")
                st.write(fallas[["seccion", "pregunta", "observacion"]])
            
            if not preventivos.empty:
                st.warning("📋 **Posibles actividades preventivas omitidas o por revisar:**")
                st.write(preventivos[["seccion", "pregunta", "observacion"]])

    def mostrar_calendario_mantenimientos():
        st.subheader("📅 Calendario de mantenimientos")
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM mantenimientos", conn)
        conn.close()

        df["fecha_programada"] = pd.to_datetime(df["fecha_programada"])
        df = df.sort_values("fecha_programada")

        st.dataframe(df[["maquina", "tipo", "fecha_programada", "realizado", "observacion"]])

        for _, row in df.iterrows():
            if not row["realizado"]:
                st.markdown(f"🔜 **{row['maquina']}** → {row['tipo']} el `{row['fecha_programada'].date()}`")
    with st.expander("📤 Exportar inspecciones"):
        if st.button("📄 Exportar a Excel"):
            df.to_excel("inspecciones_export.xlsx", index=False)
            with open("inspecciones_export.xlsx", "rb") as f:
                st.download_button("📥 Descargar Excel", f, file_name="inspecciones_export.xlsx")
    

