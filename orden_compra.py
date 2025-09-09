import os
import json
import sqlite3
import streamlit as st
import pandas as pd
from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def mostrar_orden_compra():
    # ----------------------
    # Constantes de BD / Archivos
    # ----------------------
    DB_ORDENES = "ordenes_compra.db"
    DB_CONFIG = "configuracion.db"
    DB_COMPRAS = "compras.db"
    CODIGOS_FILE = "codigos_autorizacion.json"

    # ----------------------
    # Archivo de códigos (crea si no existe)
    # ----------------------
    if not os.path.exists(CODIGOS_FILE):
        codigos_default = {
            "codigo_autorizacion": "159",
            "firma_ing": "clave_ing",
            "firma_gerente": "clave_gerente"
        }
        with open(CODIGOS_FILE, "w", encoding="utf-8") as f:
            json.dump(codigos_default, f, ensure_ascii=False, indent=4)

    with open(CODIGOS_FILE, "r", encoding="utf-8") as f:
        CODIGOS = json.load(f)

    # ----------------------
    # Utilidades de BD
    # ----------------------
    def ensure_db():
        conn = sqlite3.connect(DB_ORDENES)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS ordenes_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_oc TEXT,
                fecha TEXT,
                empresa TEXT,
                ruc_empresa TEXT,
                direccion_empresa TEXT,
                proveedor TEXT,
                ruc_proveedor TEXT,
                direccion_proveedor TEXT,
                telefono_proveedor TEXT,
                contacto_proveedor TEXT,
                moneda TEXT,
                cond_pago TEXT,
                items TEXT, -- JSON
                subtotal REAL,
                igv REAL,
                total REAL,
                fecha_entrega TEXT,
                lugar_entrega TEXT,
                estado TEXT, -- 'pendiente' | 'aprobada'
                firma_gerente TEXT
            )
        """)
        conn.commit()
        conn.close()

    def get_config_empresa():
        conn = sqlite3.connect(DB_CONFIG)
        c = conn.cursor()
        c.execute("SELECT empresa, ruc, direccion FROM configuracion ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return {"empresa": row[0], "ruc": row[1], "direccion": row[2]}
        return {"empresa": "", "ruc": "", "direccion": ""}

    def get_proveedores():
        conn = sqlite3.connect(DB_COMPRAS)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM proveedores ORDER BY proveedor ASC")
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_proveedor_by_name(name):
        conn = sqlite3.connect(DB_COMPRAS)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM proveedores WHERE proveedor = ?", (name,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def next_order_number():
        conn = sqlite3.connect(DB_ORDENES)
        c = conn.cursor()
        c.execute("SELECT numero_oc FROM ordenes_compra ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if not row or not row[0]:
            return "0001"
        try:
            n = int(row[0])
            return f"{n+1:04d}"
        except:
            return "0001"

    def save_order(data, edit_id=None):
        conn = sqlite3.connect(DB_ORDENES)
        c = conn.cursor()
        if edit_id:
            c.execute("""
                UPDATE ordenes_compra
                SET numero_oc=?, fecha=?, empresa=?, ruc_empresa=?, direccion_empresa=?,
                    proveedor=?, ruc_proveedor=?, direccion_proveedor=?, telefono_proveedor=?,
                    contacto_proveedor=?, moneda=?, cond_pago=?, items=?, subtotal=?, igv=?, total=?,
                    fecha_entrega=?, lugar_entrega=?, estado=?, firma_gerente=?
                WHERE id = ?
            """, (
                data["numero_oc"], data["fecha"], data["empresa"], data["ruc_empresa"], data["direccion_empresa"],
                data["proveedor"], data["ruc_proveedor"], data["direccion_proveedor"], data["telefono_proveedor"],
                data["contacto_proveedor"], data["moneda"], data["cond_pago"], json.dumps(data["items"]),
                data["subtotal"], data["igv"], data["total"], data["fecha_entrega"], data["lugar_entrega"],
                data["estado"], data.get("firma_gerente",""), edit_id
            ))
        else:
            c.execute("""
                INSERT INTO ordenes_compra (
                    numero_oc, fecha, empresa, ruc_empresa, direccion_empresa, proveedor, ruc_proveedor,
                    direccion_proveedor, telefono_proveedor, contacto_proveedor, moneda, cond_pago, items,
                    subtotal, igv, total, fecha_entrega, lugar_entrega, estado, firma_gerente
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["numero_oc"], data["fecha"], data["empresa"], data["ruc_empresa"], data["direccion_empresa"],
                data["proveedor"], data["ruc_proveedor"], data["direccion_proveedor"], data["telefono_proveedor"],
                data["contacto_proveedor"], data["moneda"], data["cond_pago"], json.dumps(data["items"]),
                data["subtotal"], data["igv"], data["total"], data["fecha_entrega"], data["lugar_entrega"],
                data["estado"], data.get("firma_gerente","")
            ))
        conn.commit()
        conn.close()

    def load_order(order_id):
        conn = sqlite3.connect(DB_ORDENES)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM ordenes_compra WHERE id=?", (order_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_orders(estado=None):
        conn = sqlite3.connect(DB_ORDENES)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if estado:
            c.execute("SELECT * FROM ordenes_compra WHERE estado=? ORDER BY id DESC", (estado,))
        else:
            c.execute("SELECT * FROM ordenes_compra ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ----------------------
    # PDF
    # ----------------------
    def export_pdf(order, path_pdf):
        doc = SimpleDocTemplate(path_pdf, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28)
        styles = getSampleStyleSheet()
        story = []

        # Encabezado
        header = [
            ["SISTEMA DE GESTION INTEGRADO", "CODIGO: 0000ESGIREG"],
            ["VERSION: 01", ""],
            ["ORDEN DE COMPRA", f"FECHA: {order['fecha']}"],
            ["PAGINA: 01 DE 01", ""]
        ]
        t = Table(header, colWidths=[300, 220])
        t.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("LINEBELOW", (0,2), (-1,2), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))

        # Número de OC
        story.append(Paragraph(f"<b>ORDEN DE COMPRA N°</b> {order['numero_oc']}", styles['Heading3']))
        story.append(Spacer(1, 6))

        # Empresa y entrega
        empresa_data = [
            [f"RUC: {order['ruc_empresa']}"],
            [f"SEDE PRINCIPAL: {order['direccion_empresa']}"],
            [f"LUGAR DE ENTREGA PLAN: {order['lugar_entrega']}"],
        ]
        t2 = Table(empresa_data, colWidths=[520])
        t2.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 9)]))
        story.append(t2)
        story.append(Spacer(1, 8))

        # Proveedor
        prov_table = [
            ["PROVEEDOR:", order["proveedor"], "FECHA:", order["fecha"]],
            ["RUC:", order["ruc_proveedor"], "MONEDA:", order["moneda"]],
            ["DIRECCIÓN:", order["direccion_proveedor"], "COND. DE PAGO:", order["cond_pago"]],
            ["TELÉFONO:", order["telefono_proveedor"], "", ""],
            ["CONTACTO:", order["contacto_proveedor"], "", ""],
        ]
        t3 = Table(prov_table, colWidths=[80, 240, 80, 120])
        t3.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("TEXTCOLOR", (0,0), (-1,-1), colors.black),
            ("BACKGROUND", (0,0), (0,-1), colors.whitesmoke),
            ("BACKGROUND", (2,0), (2,0), colors.whitesmoke),
        ]))
        story.append(t3)
        story.append(Spacer(1, 8))

        # Items
        items = json.loads(order["items"]) if isinstance(order["items"], str) else order["items"]
        items_data = [["ITEM", "DESCRIPCIÓN", "CANTIDAD", "PRECIO UNITARIO", "SUB TOTAL"]]
        for i, it in enumerate(items, 1):
            items_data.append([
                str(i),
                it.get("descripcion",""),
                f"{it.get('cantidad',0)}",
                f"{float(it.get('precio_unitario',0.0)):.2f}",
                f"{float(it.get('cantidad',0))*float(it.get('precio_unitario',0.0)):.2f}"
            ])

        t4 = Table(items_data, colWidths=[40, 260, 70, 90, 90])
        t4.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN", (2,1), (-1,-1), "RIGHT"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("FONTSIZE", (0,0), (-1,-1), 9),
        ]))
        story.append(t4)
        story.append(Spacer(1, 6))

        # Totales
        tot_table = [
            ["", "", "SUB TOTAL", f"{order['subtotal']:.2f}"],
            ["", "", "IGV (18%)", f"{order['igv']:.2f}"],
            ["", "", "TOTAL", f"{order['total']:.2f}"],
        ]
        t5 = Table(tot_table, colWidths=[40, 260, 160, 90])
        t5.setStyle(TableStyle([
            ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
            ("ALIGN", (2,0), (-1,-1), "RIGHT"),
            ("GRID", (2,0), (-1,-1), 0.5, colors.black),
            ("FONTSIZE", (0,0), (-1,-1), 9),
        ]))
        story.append(t5)
        story.append(Spacer(1, 10))

        # Entrega
        entrega_table = [
            ["FECHA DE ENTREGA", order["fecha_entrega"]],
            ["LUGAR DE ENTREGA", order["lugar_entrega"]],
            ["HORARIOS DE ENTREGA", "DE LUNES A VIERNES 8.30 AM A 5.00 PM / SÁBADOS 8.30 AM A 1.00 PM"],
        ]
        t6 = Table(entrega_table, colWidths=[160, 360])
        t6.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,-1), colors.whitesmoke),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ]))
        story.append(t6)
        story.append(Spacer(1, 18))

        # Firma
        firma = order.get("firma_gerente","")
        story.append(Paragraph(f"{firma if firma else '_________________________'}", styles["Normal"]))
        story.append(Paragraph("GERENTE GENERAL", styles["Normal"]))
        story.append(Spacer(1, 16))

        # Nota
        nota = """<b>NOTA:</b> RECORDAR QUE LAS FACTURAS EMITIDAS YA SEA A 15, 30, 45, 60 O 90 DÍAS, NO DEBEN DE TENER COMO FECHAS DE VENCIMIENTO SÁBADO, DOMINGO NI FERIADO. CASO CONTRARIO SE PROCESARÁ A LA DEVOLUCIÓN DEL MISMO."""
        story.append(Paragraph(nota, styles["Normal"]))

        doc.build(story)

    # ----------------------
    # UI - Streamlit
    # ----------------------

    ensure_db()

    # Estado inicial seguro (usar SIEMPRE la clave, no el atributo)
    if "items" not in st.session_state:
        st.session_state["items"] = []
    if "editing_id" not in st.session_state:
        st.session_state["editing_id"] = None

    empresa_cfg = get_config_empresa()
    proveedores = get_proveedores()
    proveedor_names = ["-- Selecciona --"] + [p["proveedor"] for p in proveedores]

    col_form, col_right = st.columns([2,1], gap="large")

    # ----------------------
    # Columna derecha: Historial y Por aprobar
    # ----------------------
    with col_right:
        st.subheader("📜 Historial")
        orders = list_orders()
        if orders:
            df_hist = pd.DataFrame([{
                "ID": o["id"],
                "N° OC": o["numero_oc"],
                "Fecha": o["fecha"],
                "Proveedor": o["proveedor"],
                "Total": o["total"],
                "Estado": o["estado"]
            } for o in orders])
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
            # Botones por fila
            for o in orders:
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button(f"📝 Editar {o['numero_oc']}", key=f"edit_{o['id']}"):
                        st.session_state["editing_id"] = o["id"]
                        st.session_state["items"] = json.loads(o["items"]) if isinstance(o["items"], str) else o["items"]
                        st.rerun()
                with c2:
                    if st.button(f"📄 PDF {o['numero_oc']}", key=f"pdf_{o['id']}"):
                        file_name = f"OC_{o['numero_oc']}_{o['proveedor'].replace(' ','_')}.pdf"
                        export_pdf(o, file_name)
                        st.success(f"PDF generado: {file_name}")
                        with open(file_name, "rb") as f:
                            st.download_button("⬇️ Descargar PDF", data=f, file_name=file_name, mime="application/pdf", key=f"dl_{o['id']}")
                with c3:
                    st.write(f"Estado: **{o['estado']}**")
        else:
            st.info("Sin órdenes registradas aún.")

        st.markdown("---")
        st.subheader("📝 Órdenes por aprobar")
        pendientes = list_orders(estado="pendiente")
        if pendientes:
            df_p = pd.DataFrame([{
                "ID": o["id"],
                "N° OC": o["numero_oc"],
                "Proveedor": o["proveedor"],
                "Total": o["total"]
            } for o in pendientes])
            st.dataframe(df_p, use_container_width=True, hide_index=True)
            for o in pendientes:
                if st.button(f"✅ Aprobar / Editar {o['numero_oc']}", key=f"ap_{o['id']}"):
                    st.session_state["editing_id"] = o["id"]
                    st.session_state["items"] = json.loads(o["items"]) if isinstance(o["items"], str) else o["items"]
                    st.rerun()
        else:
            st.success("No hay órdenes pendientes.")

    # ----------------------
    # Columna izquierda: Formulario
    # ----------------------
    with col_form:
        st.subheader("🧾 Orden de Compra")

        # Si estamos editando, cargar datos
        editing_order = load_order(st.session_state["editing_id"]) if st.session_state["editing_id"] else None

        numero_oc = st.text_input("N° Orden de Compra (auto)", value=(editing_order["numero_oc"] if editing_order else next_order_number()), disabled=True)
        fecha = st.date_input("Fecha", value=(datetime.strptime(editing_order["fecha"], "%Y-%m-%d").date() if (editing_order and editing_order.get("fecha")) else date.today()), key="fecha_orden de compra")

        st.markdown("**Empresa** (autocompletado)")
        empresa = st.text_input("Razón Social", value=editing_order["empresa"] if editing_order else empresa_cfg["empresa"], disabled=True)
        ruc_empresa = st.text_input("RUC Empresa", value=editing_order["ruc_empresa"] if editing_order else empresa_cfg["ruc"], disabled=True)
        direccion_empresa = st.text_area("Dirección Empresa", value=editing_order["direccion_empresa"] if editing_order else empresa_cfg["direccion"], disabled=True, height=70)

        st.markdown("---")
        st.markdown("**Proveedor**")
        default_idx = 0
        if editing_order:
            prov_sel_name = editing_order["proveedor"]
            default_idx = proveedor_names.index(prov_sel_name) if prov_sel_name in proveedor_names else 0
        prov_name = st.selectbox("Proveedor", proveedor_names, index=default_idx)

        prov_data = None
        if prov_name and prov_name != "-- Selecciona --":
            prov_data = get_proveedor_by_name(prov_name)

        ruc_proveedor = st.text_input("RUC Proveedor", value=(editing_order["ruc_proveedor"] if editing_order else (prov_data["ruc"] if prov_data else "")), disabled=True)
        direccion_proveedor = st.text_area("Dirección Proveedor", value=(editing_order["direccion_proveedor"] if editing_order else (prov_data["direccion"] if prov_data else "")), height=70, disabled=True)
        telefono_proveedor = st.text_input("Teléfono Proveedor", value=(editing_order["telefono_proveedor"] if editing_order else (prov_data["telefono"] if prov_data else "")), disabled=True)
        contacto_proveedor = st.text_input("Contacto", value=(editing_order["contacto_proveedor"] if editing_order else (prov_data["contacto"] if prov_data else "")), disabled=True)
        moneda = st.text_input("Moneda", value=(editing_order["moneda"] if editing_order else (prov_data["moneda"] if prov_data else "")), disabled=True)
        cond_pago = st.text_input("Condición de Pago", value=(editing_order["cond_pago"] if editing_order else (prov_data["cond_pago"] if prov_data else "")), disabled=False)

        st.markdown("---")
        st.markdown("**Ítems**")

        # Inicializar items si el editor lo necesita
        if editing_order and not st.session_state["items"]:
            st.session_state["items"] = json.loads(editing_order["items"]) if isinstance(editing_order["items"], str) else editing_order["items"]

        # Botón para agregar ítem
        if st.button("➕ Agregar ítem"):
            st.session_state["items"].append({"descripcion": "", "cantidad": 1.0, "precio_unitario": 0.0})

        # Render de items
        to_delete = []
        subtotal = 0.0
        for idx, item in enumerate(st.session_state["items"]):
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([4,1,1,1])
                desc = c1.text_input("Descripción", value=item.get("descripcion",""), key=f"desc_{idx}")
                cant = c2.number_input("Cantidad", min_value=0.0, value=float(item.get("cantidad", 0.0)), step=1.0, key=f"cant_{idx}")
                punit = c3.number_input("Precio Unitario", min_value=0.0, value=float(item.get("precio_unitario",0.0)), step=0.1, format="%.2f", key=f"punit_{idx}")
                if c4.button("🗑️ Eliminar", key=f"del_{idx}"):
                    to_delete.append(idx)
                # actualizar en session
                st.session_state["items"][idx] = {"descripcion": desc, "cantidad": cant, "precio_unitario": punit}
                subtotal += cant * punit

        # Eliminar marcados
        for i in sorted(to_delete, reverse=True):
            st.session_state["items"].pop(i)

        igv = subtotal * 0.18
        total = subtotal + igv
        st.write(f"**Sub Total:** {subtotal:,.2f}")
        st.write(f"**IGV (18%):** {igv:,.2f}")
        st.write(f"**TOTAL:** {total:,.2f}")

        st.markdown("---")
        fecha_entrega = st.date_input(
            "Fecha de Entrega",
            value=(datetime.strptime(editing_order["fecha_entrega"], "%Y-%m-%d").date()
                if (editing_order and editing_order.get("fecha_entrega")) else date.today())
        )
        lugares = [
            "JR. GENERAL VIDAL 835 - BREÑA - LIMA",
            empresa_cfg["direccion"]
        ]
        lugar_entrega = st.selectbox(
            "Lugar de Entrega",
            lugares,
            index=(0 if not editing_order else (lugares.index(editing_order["lugar_entrega"]) if editing_order["lugar_entrega"] in lugares else 0))
        )

        st.markdown("---")
        st.subheader("🔏 Firma Gerencia")
        firma_nombre = st.text_input(
            "Nombre del Gerente General (opcional)",
            value=(editing_order["firma_gerente"] if editing_order and editing_order["firma_gerente"] and editing_order["estado"]=="aprobada" else "")
        )
        firma_codigo = st.text_input("Código de aprobación (solo gerente)", type="password")

        st.caption("NOTA: RECORDAR QUE LAS FACTURAS EMITIDAS YA SEA A 15, 30, 45, 60 O 90 DÍAS, NO DEBEN DE TENER COMO FECHAS DE VENCIMIENTO SÁBADO, DOMINGO NI FERIADO. CASO CONTRARIO SE PROCESARÁ A LA DEVOLUCIÓN DEL MISMO.")

        csave, capprove, cclear = st.columns([1,1,1])
        with csave:
            if st.button("💾 Guardar (Pendiente)"):
                # Guardar como pendiente
                data = {
                    "numero_oc": numero_oc,
                    "fecha": fecha.strftime("%Y-%m-%d"),
                    "empresa": empresa,
                    "ruc_empresa": ruc_empresa,
                    "direccion_empresa": direccion_empresa,
                    "proveedor": prov_name if prov_name!="-- Selecciona --" else "",
                    "ruc_proveedor": ruc_proveedor,
                    "direccion_proveedor": direccion_proveedor,
                    "telefono_proveedor": telefono_proveedor,
                    "contacto_proveedor": contacto_proveedor,
                    "moneda": moneda,
                    "cond_pago": cond_pago,
                    "items": st.session_state["items"],
                    "subtotal": subtotal,
                    "igv": igv,
                    "total": total,
                    "fecha_entrega": fecha_entrega.strftime("%Y-%m-%d"),
                    "lugar_entrega": lugar_entrega,
                    "estado": "pendiente",
                    "firma_gerente": ""
                }
                save_order(data, edit_id=st.session_state["editing_id"])
                st.success("Orden guardada como pendiente.")
                st.session_state["items"] = []
                st.session_state["editing_id"] = None
                st.rerun()

        with capprove:
            if st.button("✅ Aprobar y Guardar"):
                if firma_codigo != CODIGOS["firma_gerente"]:
                    st.error("Código de aprobación incorrecto.")
                else:
                    firma_out = firma_nombre.strip() if firma_nombre.strip() else "GERENTE GENERAL"
                    data = {
                        "numero_oc": numero_oc,
                        "fecha": fecha.strftime("%Y-%m-%d"),
                        "empresa": empresa,
                        "ruc_empresa": ruc_empresa,
                        "direccion_empresa": direccion_empresa,
                        "proveedor": prov_name if prov_name!="-- Selecciona --" else "",
                        "ruc_proveedor": ruc_proveedor,
                        "direccion_proveedor": direccion_proveedor,
                        "telefono_proveedor": telefono_proveedor,
                        "contacto_proveedor": contacto_proveedor,
                        "moneda": moneda,
                        "cond_pago": cond_pago,
                        "items": st.session_state["items"],
                        "subtotal": subtotal,
                        "igv": igv,
                        "total": total,
                        "fecha_entrega": fecha_entrega.strftime("%Y-%m-%d"),
                        "lugar_entrega": lugar_entrega,
                        "estado": "aprobada",
                        "firma_gerente": firma_out
                    }
                    save_order(data, edit_id=st.session_state["editing_id"])
                    st.success("Orden aprobada y guardada.")
                    st.session_state["items"] = []
                    st.session_state["editing_id"] = None
                    st.rerun()

        with cclear:
            if st.button("🧹 Limpiar formulario"):
                st.session_state["items"] = []
                st.session_state["editing_id"] = None
                st.rerun()
