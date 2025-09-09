# compras.py
import streamlit as st
import sqlite3
import os
from datetime import datetime
from PIL import Image
import pandas as pd
import sqlite3
from streamlit_echarts import st_echarts
import orden_compra


DB_COMPRAS = "compras.db"

def init_db():
    conn = sqlite3.connect(DB_COMPRAS)
    c = conn.cursor()

    # Tabla proveedores
    c.execute("""
    CREATE TABLE IF NOT EXISTS proveedores (
        proveedor TEXT,
        ruc TEXT,
        direccion TEXT,
        telefono TEXT,
        contacto TEXT,
        moneda TEXT,
        cond_pago TEXT,
        moneda2 TEXT,
        cliente_nombre TEXT,
        cliente_contacto TEXT,
        cliente_correo TEXT,
        cliente_cuenta TEXT,
        cliente_detalles TEXT,
        trazabilidad TEXT,
        normativa_calidad TEXT,
        certificacion TEXT,
        firma_ing TEXT,
        firma_gerente TEXT
    )
    """)










    # Tabla ordenes de compra
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordenes_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            fecha TEXT,
            clausulas_pago TEXT,
            firma TEXT,
            nombre_firma TEXT,
            pdf_path TEXT,
            estado TEXT
        )
    """)

    # Tabla ordenes de servicio
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordenes_servicio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            fecha TEXT,
            clausulas_pago TEXT,
            firma TEXT,
            nombre_firma TEXT,
            pdf_path TEXT,
            estado TEXT
        )
    """)

    # Tabla recepcion
    c.execute("""
        CREATE TABLE IF NOT EXISTS recepcion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT, -- 'compra' o 'servicio'
            orden_id INTEGER,
            fecha TEXT,
            checklist TEXT,
            foto TEXT,
            firma TEXT,
            nombre_firma TEXT
        )
    """)

    conn.commit()
    conn.close()





def mostrar_modulo_compras():
    st.header("📄 Orden de Compra")
    init_db()

    tab1, tab2, tab3 = st.tabs([
        "📝 Aprobación de Proveedores",
        "🛒 Crear Orden de Compra",
        "📂 Estado de Órdenes de Compra"
    ])

    # --- TAB 1 ---
    with tab1:
        

        col1, col2 = st.columns([2, 2])  # Igual ancho

        # ======== COLUMNA IZQUIERDA: FORMULARIO ========
        with col1:
            with st.form("form_proveedor"):
                st.subheader("📋 Datos del Proveedor")
                proveedor = st.text_input("Proveedor")
                ruc = st.text_input("RUC")
                direccion = st.text_area("Dirección")
                telefono = st.text_input("Teléfono")
                contacto = st.text_input("Persona de contacto")
                moneda = st.selectbox("Moneda principal", ["PEN - Soles", "USD - Dólares", "EUR - Euros"])
                cond_pago = st.selectbox("Condición de pago (ej. 30 días, pago a X letras)", ["", "30 - días", "60 - días", "90 - días"])
                moneda2 = st.selectbox("Moneda secundaria (opcional)", ["", "PEN - Soles", "USD - Dólares", "EUR - Euros"])
                
                st.markdown("### 🧾 Datos de Cliente Asociado")
                cliente_nombre = st.text_input("Nombre del cliente")
                cliente_contacto = st.text_input("Contacto del cliente")
                cliente_correo = st.text_input("Correo del cliente")
                cliente_cuenta = st.text_input("Cuenta bancaria")
                cliente_detalles = st.text_area("Detalles adicionales del cliente")

                st.markdown("---")
                st.subheader("✅ Evaluación BRCGS - Aprobación del Proveedor")

                trazabilidad = st.radio(
                    "¿El producto fabricado o manufacturado cuenta con registros de trazabilidad?",
                    ["Sí", "No"]
                )
                if trazabilidad == "Sí":
                    trazabilidad_docs = st.file_uploader(
                        "Adjuntar documentos de trazabilidad", 
                        type=["pdf", "jpg", "png"], 
                        accept_multiple_files=True
                    )

                normativa_calidad = st.radio(
                    "¿Cuenta con una normativa de calidad implementada?",
                    ["Sí - ISO 9001", "Sí - BRCGS", "Sí - HACCP", "Otra", "No"]
                )
                if normativa_calidad != "No":
                    normativa_docs = st.file_uploader(
                        "Adjuntar documentos de normativa de calidad", 
                        type=["pdf", "jpg", "png"], 
                        accept_multiple_files=True
                    )

                certificacion = st.radio(
                    "¿Cuenta con certificaciones vigentes?",
                    ["Sí", "No"]
                )
                if certificacion == "Sí":
                    cert_docs = st.file_uploader(
                        "Adjuntar certificados", 
                        type=["pdf", "jpg", "png"], 
                        accept_multiple_files=True
                    )

                st.markdown("---")
                st.subheader("🔏 Autorizaciones")
                codigo_autorizacion = st.text_input("Código de autorización (solo para uso interno)", type="password")
                firma_ing = st.text_input("Firma - Ingeniero de Seguridad y Calidad", type="password")
                firma_gerente = st.text_input("Firma - Gerente General", type="password")

                submitted = st.form_submit_button("💾 Guardar proveedor")

                if submitted:
                    if codigo_autorizacion != "159":
                        st.error("❌ Código de autorización incorrecto.")
                    else:
                        conn = sqlite3.connect(DB_COMPRAS)
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO proveedores (
                                proveedor, ruc, direccion, telefono, contacto, moneda, cond_pago, moneda2,
                                cliente_nombre, cliente_contacto, cliente_correo, cliente_cuenta, cliente_detalles,
                                trazabilidad, normativa_calidad, certificacion,
                                firma_ing, firma_gerente
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            proveedor, ruc, direccion, telefono, contacto, moneda, cond_pago, moneda2,
                            cliente_nombre, cliente_contacto, cliente_correo, cliente_cuenta, cliente_detalles,
                            trazabilidad, normativa_calidad, certificacion,
                            firma_ing, firma_gerente
                        ))
                        conn.commit()
                        conn.close()
                        st.success("Proveedor guardado correctamente ✅")

        # ======== COLUMNA DERECHA: HISTORIAL Y KPIs ========
        with col2:
            st.subheader("📜 Historial de Proveedores")
            
            conn = sqlite3.connect(DB_COMPRAS)
            df = pd.read_sql_query("SELECT * FROM proveedores", conn)
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


    # --- TAB 2 ---
    with tab2:
        orden_compra.mostrar_orden_compra()



    # --- TAB 3 ---
    with tab3:
        conn = sqlite3.connect(DB_COMPRAS)
        c = conn.cursor()
        c.execute("SELECT id, proveedor_id, fecha, estado FROM ordenes_compra")
        ordenes = c.fetchall()
        conn.close()

        if ordenes:
            st.table(ordenes)
        else:
            st.info("No hay órdenes registradas.")



def mostrar_recepcion_materiales():
    st.header("📦 Recepción de Materiales")
    init_db()

    tipo = st.selectbox("Seleccionar tipo de orden", ["Orden de Compra", "Orden de Servicio"])

    conn = sqlite3.connect(DB_COMPRAS)
    c = conn.cursor()
    if tipo == "Orden de Compra":
        c.execute("SELECT id FROM ordenes_compra")
    else:
        c.execute("SELECT id FROM ordenes_servicio")
    ordenes = c.fetchall()
    conn.close()

    orden_id = st.selectbox("Seleccionar orden", [o[0] for o in ordenes] if ordenes else [])

    if orden_id:
        checklist_items = ["Cumple con etiquetado", "Cantidad correcta", "Sin daños", "Dentro de fecha acordada"]
        resultados = {}
        for item in checklist_items:
            resultados[item] = st.selectbox(f"{item}:", ["Sí", "No"])

        foto = st.file_uploader("Subir foto del producto", type=["jpg", "png"])
        firma = st.file_uploader("Firma del receptor", type=["jpg", "png"])
        nombre_firma = st.text_input("Nombre del receptor")

        if st.button("Registrar recepción"):
            conn = sqlite3.connect(DB_COMPRAS)
            c = conn.cursor()
            c.execute("""
                INSERT INTO recepcion (tipo, orden_id, fecha, checklist, foto, firma, nombre_firma)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (tipo.lower(), orden_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  str(resultados), foto.name if foto else None, firma.name if firma else None, nombre_firma))
            conn.commit()
            conn.close()
            st.success("Recepción registrada ✅")
