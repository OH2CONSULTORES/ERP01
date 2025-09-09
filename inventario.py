# inventario.py
import streamlit as st
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.colors import black
import io
import pandas as pd
from datetime import datetime
import altair as alt
import textwrap

# ---------- BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT,
            cantidad INTEGER,
            bloque TEXT,
            ubicacion TEXT,
            costo REAL,
            codigo TEXT UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            descripcion TEXT,
            tipo TEXT,
            cantidad INTEGER,
            fecha TEXT
        )
    """)
    conn.commit()
    conn.close()

def registrar_movimiento(codigo, descripcion, tipo, cantidad):
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO movimientos (codigo, descripcion, tipo, cantidad, fecha)
        VALUES (?, ?, ?, ?, ?)
    """, (codigo, descripcion, tipo, cantidad, fecha))
    conn.commit()
    conn.close()

def generar_codigo_automatico():
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM inventario")
    total = c.fetchone()[0] + 1
    conn.close()
    return f"PROD{str(total).zfill(4)}"

def agregar_item(descripcion, cantidad, bloque, ubicacion, costo, codigo):
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO inventario (descripcion, cantidad, bloque, ubicacion, costo, codigo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (descripcion, cantidad, bloque, ubicacion, costo, codigo))
        conn.commit()
        registrar_movimiento(codigo, descripcion, "Ingreso", cantidad)
    except sqlite3.IntegrityError:
        st.warning("⚠️ Ya existe un producto con ese código.")
    conn.close()

def registrar_egreso(codigo, cantidad):
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute("SELECT descripcion, cantidad, bloque, ubicacion, costo FROM inventario WHERE lower(codigo) = ?", (codigo.lower(),))
    res = c.fetchone()
    if res:
        descripcion, cantidad_actual, bloque, ubicacion, costo = res
        if cantidad <= cantidad_actual:
            nueva = cantidad_actual - cantidad
            c.execute("UPDATE inventario SET cantidad = ? WHERE lower(codigo) = ?", (nueva, codigo.lower()))
            conn.commit()
            conn.close()
            registrar_movimiento(codigo, descripcion, "Egreso", cantidad)
            pdf = generar_comprobante_egreso_pdf(codigo, descripcion, cantidad, bloque, ubicacion, costo)
            st.download_button("📄 Descargar comprobante de egreso", data=pdf, file_name=f"egreso_{codigo}.pdf", mime="application/pdf")
            st.success(f"✅ Egreso de {cantidad} unidades registrado")
        else:
            conn.close()
            st.error("❌ No hay suficiente stock")
    else:
        conn.close()
        st.warning("Producto no encontrado")

def buscar_por_codigo(codigo):
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute("SELECT * FROM inventario WHERE lower(codigo) = ?", (codigo.lower(),))
    item = c.fetchone()
    conn.close()
    return item

def obtener_todos():
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute("SELECT * FROM inventario")
    items = c.fetchall()
    conn.close()
    return items

def obtener_movimientos():
    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()
    c.execute("SELECT * FROM movimientos ORDER BY fecha DESC")
    data = c.fetchall()
    conn.close()
    return data

def importar_desde_excel(file):
    df = pd.read_excel(file)
    for _, row in df.iterrows():
        agregar_item(
            row['Descripción'], int(row['Cantidad']), row['Bloque'], row['Ubicación'], float(row['Costo']), row['Código']
        )

def generar_excel_en_blanco():
    df = pd.DataFrame(columns=['Descripción', 'Cantidad', 'Bloque', 'Ubicación', 'Costo', 'Código'])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer

# ---------- PDF ----------
def generar_etiqueta_pdf_lote(productos, ancho_mm=70, alto_mm=50):
    ancho = ancho_mm * mm
    alto = alto_mm * mm
    margen = 10
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto * len(productos)))
    for i, item in enumerate(productos):
        y_offset = alto * (len(productos) - i - 1)
        c.setStrokeColor(black)
        c.rect(margen, y_offset + margen, ancho - 2 * margen, alto - 2 * margen)
        c.setFont("Helvetica-Bold", 9)
        x_text = margen + 8
        y_text = y_offset + alto - margen - 15
        descripcion_envuelta = textwrap.wrap(f"Descripción: {item[1]}", width=50)
        for linea in descripcion_envuelta:
            c.drawString(x_text, y_text, linea)
            y_text -= 12
        c.drawString(x_text, y_text, f"Cantidad: {item[2]} | Costo: S/ {item[5]:.2f}")
        y_text -= 12
        c.drawString(x_text, y_text, f"Bloque: {item[3]} | Ubicación: {item[4]}")
        y_text -= 12
        c.drawString(x_text, y_text, f"Código: {item[6]}")
        barcode = code128.Code128(item[6].upper(), barHeight=15 * mm, barWidth=1.2)
        barcode.drawOn(c, (ancho - barcode.width) / 2, y_offset + margen + 10)
    c.save()
    buffer.seek(0)
    return buffer

def generar_comprobante_egreso_pdf(codigo, descripcion, cantidad, bloque, ubicacion, costo):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A6)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(10, 260, "🧾 Comprobante de Egreso")
    c.setFont("Helvetica", 10)
    c.drawString(10, 240, f"Código: {codigo}")
    c.drawString(10, 225, f"Descripción: {descripcion}")
    c.drawString(10, 210, f"Cantidad: {cantidad}")
    c.drawString(10, 195, f"Bloque: {bloque}")
    c.drawString(10, 180, f"Ubicación: {ubicacion}")
    c.drawString(10, 165, f"Costo unitario: S/ {costo:.2f}")
    c.drawString(10, 150, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    barcode = code128.Code128(codigo.upper(), barHeight=15 * mm, barWidth=0.4)
    barcode.drawOn(c, 10, 100)
    c.save()
    buffer.seek(0)
    return buffer

# ---------- UI PRINCIPAL ----------
def mostrar_gestion_inventario():
    init_db()
    st.subheader("📦 Gestión de Inventario")

    # Siempre mostrar las opciones
    st.session_state.mostrar_inventario_opciones = True
    
    if st.session_state.mostrar_inventario_opciones:
        tabs = st.tabs(["➕ Agregar Producto", "📋 Inventario", "🔍 Buscar / Egreso", "🕓 Historial", "📊 Dashboard"])

        # === ➕ Agregar Producto ===
        with tabs[0]:
            st.header("➕ Agregar nuevo producto")
            with st.form("form_agregar"):
                descripcion = st.text_input("Descripción del producto")
                cantidad = st.number_input("Cantidad", min_value=0, step=1)
                bloque = st.text_input("Bloque o estante")
                ubicacion = st.text_input("Ubicación interna")
                costo = st.number_input("Costo del producto (S/)", min_value=0.0, step=0.1)
                codigo = generar_codigo_automatico()
                st.code(f"Código generado automáticamente: {codigo}")
                generar = st.form_submit_button("Guardar y generar etiqueta")
            if generar and descripcion and cantidad and bloque and ubicacion and codigo:
                agregar_item(descripcion, cantidad, bloque, ubicacion, costo, codigo)
                pdf = generar_etiqueta_pdf_lote([(0, descripcion, cantidad, bloque, ubicacion, costo, codigo)])
                st.success("✅ Producto guardado correctamente")
                st.download_button("📄 Descargar etiqueta PDF", data=pdf, file_name=f"etiqueta_{codigo}.pdf", mime="application/pdf")

        # === 📋 Inventario ===
        with tabs[1]:
            st.header("📋 Inventario actual")
            data = obtener_todos()
            if data:
                df = pd.DataFrame(data, columns=["ID", "Descripción", "Cantidad", "Bloque", "Ubicación", "Costo", "Código"])
                st.dataframe(df, use_container_width=True)
                total_costo = df["Cantidad"] * df["Costo"]
                st.metric("💰 Costo total del inventario", f"S/ {total_costo.sum():,.2f}")

                seleccion = st.multiselect("Selecciona productos para imprimir etiquetas:", df["Código"].tolist())
                ancho_mm = st.number_input("Ancho de etiqueta (mm)", value=105)
                alto_mm = st.number_input("Alto de etiqueta (mm)", value=70)

                if st.button("📄 Generar PDF con etiquetas"):
                    seleccionados = [item for item in data if item[6] in seleccion]
                    if seleccionados:
                        pdf = generar_etiqueta_pdf_lote(seleccionados, ancho_mm, alto_mm)
                        st.download_button("📥 Descargar PDF", data=pdf, file_name="etiquetas_seleccionadas.pdf", mime="application/pdf")
                    else:
                        st.warning("No se seleccionaron productos válidos.")

                st.markdown("### 📥 Importar desde Excel")
                archivo = st.file_uploader("Seleccionar archivo Excel (.xlsx)", type=["xlsx"])
                if archivo and st.button("📤 Importar productos"):
                    importar_desde_excel(archivo)
                    st.success("✅ Productos importados correctamente")

                st.download_button("📄 Descargar plantilla en blanco", data=generar_excel_en_blanco(), file_name="plantilla_inventario.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("No hay productos registrados aún.")

        # === 🔍 Buscar / Egreso ===
        with tabs[2]:
            st.header("🔍 Buscar productos por código para salida múltiple")
            if "productos_egreso" not in st.session_state:
                st.session_state.productos_egreso = []

            cod = st.text_input("🔎 Escanea o ingresa el código del producto")
            if st.button("➕ Agregar a la lista"):
                item = buscar_por_codigo(cod)
                if item:
                    if not any(p[6] == item[6] for p in st.session_state.productos_egreso):
                        st.session_state.productos_egreso.append(item)
                        st.success(f"Producto agregado: {item[1]}")
                    else:
                        st.warning("⚠️ Ese producto ya está en la lista.")
                else:
                    st.warning("❌ Producto no encontrado")

            if st.session_state.productos_egreso:
                st.subheader("🧾 Lista de productos por egresar")
                cantidades = {}
                for i, item in enumerate(st.session_state.productos_egreso):
                    st.markdown(f"**{item[1]}** (Código: `{item[6]}`) - Stock actual: {item[2]}")
                    cantidades[item[6]] = st.number_input(f"Cantidad a egresar para {item[6]}", min_value=1, max_value=item[2], key=f"cant_{i}")

                if st.button("✅ Registrar egreso de todos"):
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=A6)
                    for item in st.session_state.productos_egreso:
                        cantidad = cantidades[item[6]]
                        registrar_egreso(item[6], cantidad)
                        c.setFont("Helvetica-Bold", 10)
                        c.drawString(10, 260, "🧾 Comprobante de Egreso")
                        c.setFont("Helvetica", 9)
                        c.drawString(10, 245, f"Código: {item[6]}")
                        c.drawString(10, 232, f"Descripción: {item[1]}")
                        c.drawString(10, 219, f"Cantidad: {cantidad}")
                        c.drawString(10, 206, f"Bloque: {item[3]}")
                        c.drawString(10, 193, f"Ubicación: {item[4]}")
                        c.drawString(10, 180, f"Costo: S/ {item[5]:.2f}")
                        c.drawString(10, 167, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        barcode = code128.Code128(item[6].upper(), barHeight=15 * mm, barWidth=0.4)
                        barcode.drawOn(c, 10, 110)
                        c.showPage()
                    c.save()
                    buffer.seek(0)
                    st.download_button("📄 Descargar comprobante PDF", data=buffer, file_name="egreso_multiple.pdf", mime="application/pdf")
                    st.success("✅ Egreso registrado correctamente")
                    st.session_state.productos_egreso.clear()

        # === 🕓 Historial ===
        with tabs[3]:
            st.subheader("🕓 Historial de movimientos")
            movs = obtener_movimientos()
            if movs:
                dfm = pd.DataFrame(movs, columns=["ID", "Código", "Descripción", "Tipo", "Cantidad", "Fecha"])
                st.dataframe(dfm, use_container_width=True)
            else:
                st.info("No hay movimientos registrados todavía.")

        # === 📊 Dashboard ===
        with tabs[4]:
            st.subheader("📊 Dashboard de Indicadores de Inventario")
            data = obtener_todos()
            movimientos = obtener_movimientos()
            if data and movimientos:
                df_inv = pd.DataFrame(data, columns=["ID", "Descripción", "Cantidad", "Bloque", "Ubicación", "Costo", "Código"])
                df_mov = pd.DataFrame(movimientos, columns=["ID", "Código", "Descripción", "Tipo", "Cantidad", "Fecha"])
                df_mov["Fecha"] = pd.to_datetime(df_mov["Fecha"])

                st.markdown("### 📆 Filtrar por período")
                col_f1, col_f2 = st.columns(2)
                fecha_inicio = col_f1.date_input("Desde", value=datetime.now().replace(day=1))
                fecha_fin = col_f2.date_input("Hasta", value=datetime.now())
                df_filtrado = df_mov[(df_mov["Fecha"] >= pd.to_datetime(fecha_inicio)) & (df_mov["Fecha"] <= pd.to_datetime(fecha_fin))]

                total_stock = df_inv["Cantidad"].sum()
                total_valor = (df_inv["Cantidad"] * df_inv["Costo"]).sum()
                col1, col2 = st.columns(2)
                col1.metric("📦 Total unidades en stock", f"{total_stock:,}")
                col2.metric("💰 Valor total del inventario", f"S/ {total_valor:,.2f}")

                ingresos = df_filtrado[df_filtrado["Tipo"] == "Ingreso"]["Cantidad"].sum()
                egresos = df_filtrado[df_filtrado["Tipo"] == "Egreso"]["Cantidad"].sum()
                col3, col4 = st.columns(2)
                col3.metric("📥 Ingresos en periodo", ingresos)
                col4.metric("📤 Egresos en periodo", egresos)

                st.markdown("### 📈 Tendencia de movimientos en el tiempo")
                tendencia = df_filtrado.groupby([df_filtrado["Fecha"].dt.date, "Tipo"])["Cantidad"].sum().reset_index()
                chart = alt.Chart(tendencia).mark_line(point=True).encode(
                    x='Fecha:T',
                    y='Cantidad:Q',
                    color='Tipo:N',
                    tooltip=['Fecha:T', 'Tipo:N', 'Cantidad:Q']
                ).properties(width='container', height=300)
                st.altair_chart(chart, use_container_width=True)

                st.markdown("### 🔝 Top 5 productos más egresados")
                top_egresos = df_filtrado[df_filtrado["Tipo"] == "Egreso"].groupby("Descripción")["Cantidad"].sum().sort_values(ascending=False).head(5)
                st.bar_chart(top_egresos)

                st.markdown("### ⚠️ Alerta de bajo stock")
                bajo_stock = df_inv[df_inv["Cantidad"] <= 5]
                if not bajo_stock.empty:
                    st.warning("Productos por debajo del nivel mínimo:")
                    st.dataframe(bajo_stock[["Descripción", "Cantidad", "Código"]])
                else:
                    st.success("✅ Todos los productos tienen stock suficiente.")

                st.markdown("### 🧱 Valor por bloque")
                valor_bloque = df_inv.groupby("Bloque").apply(lambda x: (x["Cantidad"] * x["Costo"]).sum())
                st.bar_chart(valor_bloque)

                st.markdown("### 📤 Exportar dashboard")
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                    df_inv.to_excel(writer, sheet_name="Inventario", index=False)
                    df_mov.to_excel(writer, sheet_name="Movimientos", index=False)
                excel_buffer.seek(0)
                st.download_button("📥 Descargar Dashboard en Excel", data=excel_buffer, file_name="dashboard_inventario.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("No hay datos suficientes para mostrar el dashboard.")
