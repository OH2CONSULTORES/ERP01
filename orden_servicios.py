# servicios.py
import streamlit as st
import sqlite3
import pandas as pd
from streamlit_echarts import st_echarts
from datetime import datetime
import orden_servicios2
DB_SERVICIOS = "orden_servicios.db"

# ---------------------- BASE DE DATOS ----------------------
def init_db():
    conn = sqlite3.connect(DB_SERVICIOS)
    c = conn.cursor()

    # Tabla proveedores de servicios
    c.execute("""
    CREATE TABLE IF NOT EXISTS proveedores_servicio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor TEXT,
        ruc TEXT,
        direccion TEXT,
        telefono TEXT,
        contacto TEXT,
        tipo_servicio TEXT,
        experiencia TEXT,
        trazabilidad TEXT,
        normativa_calidad TEXT,
        certificacion TEXT,
        firma_ing TEXT,
        firma_gerente TEXT
    )
    """)

    # Tabla ordenes de servicio
    c.execute("""
    CREATE TABLE IF NOT EXISTS ordenes_servicio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER,
        nro_orden TEXT,
        fecha TEXT,
        servicio_detalle TEXT,
        clausulas_pago TEXT,
        firma TEXT,
        nombre_firma TEXT,
        estado TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------------------- MÓDULO STREAMLIT ----------------------
def mostrar_modulo_servicios():
    st.header("⚙️ Gestión de Proveedores y Órdenes de Servicio")
    init_db()

    tab0, tab1, tab2 = st.tabs([
        "📝 Aprobación de Proveedores de Servicio",
        "🛠 Crear Orden de Servicio",
        "📂 Estado de Órdenes de Servicio"
    ])

    # ---------------- TAB 0: Proveedores ----------------
    with tab0:
        col1, col2 = st.columns([2, 2])

        with col1:
            with st.form("form_proveedor_servicio"):
                st.subheader("📋 Datos del Proveedor de Servicio")
                proveedor = st.text_input("Nombre de la Empresa")
                ruc = st.text_input("RUC")
                direccion = st.text_area("Dirección")
                telefono = st.text_input("Teléfono")
                contacto = st.text_input("Persona de contacto")
                tipo_servicio = st.selectbox("Tipo de servicio", ["Producción", "Troquelado", "Transporte", "Mantenimiento", "Otro"])
                experiencia = st.text_area("Experiencia relevante / Clientes previos")

                st.markdown("### ✅ Evaluación del Proveedor")
                trazabilidad = st.radio("¿Cuenta con trazabilidad en el servicio prestado?", ["Sí", "No"])
                normativa_calidad = st.radio("¿Cuenta con normativa de calidad?", ["Sí - ISO 9001", "Sí - BRCGS", "Sí - HACCP", "Otra", "No"])
                certificacion = st.radio("¿Tiene certificaciones vigentes?", ["Sí", "No"])

                st.markdown("### 🔏 Autorizaciones")
                codigo_autorizacion = st.text_input("Código de autorización interno", type="password")
                firma_ing = st.text_input("Firma - Ing. Seguridad/Calidad", type="password")
                firma_gerente = st.text_input("Firma - Gerente General", type="password")

                submitted = st.form_submit_button("💾 Guardar proveedor")

                if submitted:
                    if codigo_autorizacion != "159":
                        st.error("❌ Código de autorización incorrecto.")
                    else:
                        conn = sqlite3.connect(DB_SERVICIOS)
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO proveedores_servicio (
                                proveedor, ruc, direccion, telefono, contacto, tipo_servicio, experiencia,
                                trazabilidad, normativa_calidad, certificacion, firma_ing, firma_gerente
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            proveedor, ruc, direccion, telefono, contacto, tipo_servicio, experiencia,
                            trazabilidad, normativa_calidad, certificacion, firma_ing, firma_gerente
                        ))
                        conn.commit()
                        conn.close()
                        st.success("Proveedor de servicio guardado correctamente ✅")
        #======== COLUMNA DERECHA: HISTORIAL Y KPIs ========
        with col2:
            st.subheader("📜 Historial de Proveedores")
            
            conn = sqlite3.connect(DB_SERVICIOS)
            df = pd.read_sql_query("SELECT * FROM proveedores_servicio", conn)
            conn.close()

            if not df.empty:
                st.dataframe(df, use_container_width=True)

                total_proveedores = len(df)
                con_calidad = df[df["normativa_calidad"] != "No"].shape[0]
                sin_calidad = total_proveedores - con_calidad
                pct_con_calidad = round((con_calidad / total_proveedores) * 100, 2)
                pct_sin_calidad = round((sin_calidad / total_proveedores) * 100, 2)

                st.markdown("### 📊 KPIs de Calidad")
                st.write(f"✅ Proveedores con normativa de calidad: **{pct_con_calidad}%**")
                st.write(f"⚠ Proveedores sin normativa de calidad: **{pct_sin_calidad}%**")

                # --- Pie chart ---
                pie_options = {
                    "title": {"text": "Normativa de Calidad", "left": "center"},
                    "tooltip": {"trigger": "item"},
                    "legend": {"orient": "vertical", "left": "left"},
                    "series": [
                        {
                            "name": "Evaluación BRCGS",
                            "type": "pie",
                            "radius": "50%",
                            "data": [
                                {"value": con_calidad, "name": "Con normativa"},
                                {"value": sin_calidad, "name": "Sin normativa"}
                            ]
                        }
                    ]
                }
                st_echarts(options=pie_options, height="400px")

                # --- Bar chart ---
                barras_options = {
                    "title": {"text": "Trazabilidad y Certificación", "left": "center"},
                    "xAxis": {"type": "category", "data": ["Con Trazabilidad", "Sin Trazabilidad", "Con Certificación", "Sin Certificación"]},
                    "yAxis": {"type": "value"},
                    "series": [
                        {
                            "data": [
                                df[df["trazabilidad"] == "Sí"].shape[0],
                                df[df["trazabilidad"] == "No"].shape[0],
                                df[df["certificacion"] == "Sí"].shape[0],
                                df[df["certificacion"] == "No"].shape[0]
                            ],
                            "type": "bar"
                        }
                    ]
                }
                st_echarts(options=barras_options, height="400px")
            else:
                st.info("📭 No hay proveedores registrados todavía.")
            

    # ---------------- TAB 1: Orden de Servicio ----------------
    with tab1:
        orden_servicios2.mostrar_orden_servicio()
        





    # ---------------- TAB 2: Estado de Órdenes ----------------
    with tab2:
        st.subheader("📂 Estado de Órdenes de Servicio")
        conn = sqlite3.connect(DB_SERVICIOS)
        df = pd.read_sql_query("""
            SELECT os.id, ps.proveedor, os.nro_orden, os.fecha, os.servicio_detalle, os.estado
            FROM ordenes_servicio os
            JOIN proveedores_servicio ps ON os.proveedor_id = ps.id
        """, conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📭 No hay órdenes de servicio registradas todavía.")