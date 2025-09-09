# alertas.py
import streamlit as st
import sqlite3
import datetime

DB_ALERTAS = "alertas.db"

def init_db():
    conn = sqlite3.connect(DB_ALERTAS)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            mensaje TEXT,
            fecha TEXT,
            prioridad TEXT
        )
    """)
    conn.commit()
    conn.close()

def registrar_alerta(tipo, mensaje, prioridad="media"):
    conn = sqlite3.connect(DB_ALERTAS)
    c = conn.cursor()
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO alertas (tipo, mensaje, fecha, prioridad) VALUES (?, ?, ?, ?)",
              (tipo, mensaje, fecha, prioridad))
    conn.commit()
    conn.close()

def mostrar_alertas_admin():
    st.header("🔔 Panel de Alertas")
    init_db()
    
    conn = sqlite3.connect(DB_ALERTAS)
    c = conn.cursor()
    c.execute("SELECT tipo, mensaje, fecha, prioridad FROM alertas ORDER BY fecha DESC")
    alertas = c.fetchall()
    conn.close()

    if alertas:
        for tipo, mensaje, fecha, prioridad in alertas:
            color = "🟥" if prioridad == "alta" else "🟨" if prioridad == "media" else "🟩"
            st.markdown(f"{color} **{tipo}** | {mensaje}  \n📅 {fecha}")
    else:
        st.info("✅ No hay alertas pendientes.")

    st.subheader("Registrar nueva alerta")
    tipo = st.selectbox("Tipo de alerta", ["Producción", "Calidad", "Mantenimiento", "Stock"])
    mensaje = st.text_area("Mensaje de alerta")
    prioridad = st.selectbox("Prioridad", ["alta", "media", "baja"])
    
    if st.button("➕ Crear alerta"):
        registrar_alerta(tipo, mensaje, prioridad)
        st.success("✅ Alerta registrada correctamente.")
