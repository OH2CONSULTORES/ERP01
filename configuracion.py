# configuracion.py
import streamlit as st
import sqlite3
import os

DB_PATH = "configuracion.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT,
            ruc TEXT,
            direccion TEXT,
            logo TEXT,
            tipo_cambio REAL,
            objetivo_eficiencia REAL,
            objetivo_calidad REAL,
            tiempo_alerta INTEGER
        )
    """)
    conn.commit()
    conn.close()

def mostrar_configuracion():
    st.header("⚙️ Configuración del Sistema")
    init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM configuracion ORDER BY id DESC LIMIT 1")
    config = c.fetchone()

    empresa = st.text_input("Nombre de la empresa", value=config[1] if config else "")
    ruc = st.text_input("RUC", value=config[2] if config else "")
    direccion = st.text_area("Dirección", value=config[3] if config else "")
    logo = st.file_uploader("Logo de la empresa", type=["png", "jpg"])
    tipo_cambio = st.number_input("Tipo de cambio (USD → PEN)", value=config[5] if config else 3.5)
    objetivo_eficiencia = st.slider("Objetivo de eficiencia (%)", 50, 100, value=int(config[6] if config else 90))
    objetivo_calidad = st.slider("Objetivo de calidad (%)", 50, 100, value=int(config[7] if config else 95))
    tiempo_alerta = st.number_input("Tiempo máximo antes de alerta (horas)", value=config[8] if config else 24)

    if st.button("💾 Guardar configuración"):
        c.execute("INSERT INTO configuracion (empresa, ruc, direccion, logo, tipo_cambio, objetivo_eficiencia, objetivo_calidad, tiempo_alerta) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (empresa, ruc, direccion, logo.name if logo else None, tipo_cambio, objetivo_eficiencia, objetivo_calidad, tiempo_alerta))
        conn.commit()
        st.success("✅ Configuración guardada correctamente.")
    conn.close()
