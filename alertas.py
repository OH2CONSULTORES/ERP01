import streamlit as st
import json
import os
from datetime import datetime

ALERTAS_FILE = "data/alertas_pendientes.json"
HISTORIAL_ALERTAS = "data/alertas_atendidas.json"

def cargar_alertas_pendientes():
    if os.path.exists(ALERTAS_FILE):
        with open(ALERTAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_alertas_pendientes(alertas):
    with open(ALERTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(alertas, f, indent=2, ensure_ascii=False)

def registrar_alerta_atendida(alerta, usuario):
    alerta_atendida = alerta.copy()
    alerta_atendida["atendida_por"] = usuario
    alerta_atendida["fecha_atendida"] = datetime.now().isoformat()

    historial = []
    if os.path.exists(HISTORIAL_ALERTAS):
        with open(HISTORIAL_ALERTAS, "r", encoding="utf-8") as f:
            historial = json.load(f)

    historial.append(alerta_atendida)

    with open(HISTORIAL_ALERTAS, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)

def mostrar_notificaciones(usuario):
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔔 Notificaciones")

        alertas = cargar_alertas_pendientes()
        nuevas_alertas = []

        for i, alerta in enumerate(alertas):
            col1, col2 = st.columns([5, 1])
            with col1:
                msg = f"🚨 OP {alerta['numero_op']} - {alerta['tipo_alerta'].upper()} - Etapa: {alerta['etapa']} ({alerta['fecha'][:16].replace('T',' ')})"
                st.error(msg)
            with col2:
                if st.button("✔️", key=f"atender_{i}"):
                    registrar_alerta_atendida(alerta, usuario)
                    continue  # No se agrega de nuevo
                nuevas_alertas.append(alerta)

        guardar_alertas_pendientes(nuevas_alertas)

        if not nuevas_alertas:
            st.info("No hay notificaciones nuevas.")
def obtener_notificaciones():
    """Devuelve la cantidad de alertas pendientes."""
    alertas = cargar_alertas_pendientes()
    return len(alertas)