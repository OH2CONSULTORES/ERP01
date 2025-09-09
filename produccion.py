import streamlit as st
import json
import os
from datetime import datetime
import uuid
import shutil  # para guardar archivos
from pathlib import Path
import time
import plotly.graph_objects as go
import random
ETAPAS_FILE = "data/etapas.json"
OPS_FILE = "data/ordenes_produccion.json"
TRAZABILIDAD_FILE = "data/trazabilidad.json"
USUARIOS_FILE = "data/usuarios.json"
ALERTAS_FILE = "data/alertas_pendientes.json"
EVIDENCIA_DIR = "evidencias"
IMAGENES_DIR = Path("files/imagenes_op")  # Usamos pathlib para mayor compatibilidad

def cargar_etapas():
    if os.path.exists(ETAPAS_FILE):
        with open(ETAPAS_FILE, "r", encoding="utf-8") as f: 
            return json.load(f)
    return []

def cargar_ops():
    if os.path.exists(OPS_FILE):
        with open(OPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_ops(ops):
    os.makedirs(os.path.dirname(OPS_FILE), exist_ok=True)
    with open(OPS_FILE, "w", encoding="utf-8") as f:
        json.dump(ops, f, indent=4, ensure_ascii=False)

def guardar_trazabilidad(data):
    os.makedirs(os.path.dirname(TRAZABILIDAD_FILE), exist_ok=True)
    if os.path.exists(TRAZABILIDAD_FILE):
        with open(TRAZABILIDAD_FILE, "r", encoding="utf-8") as f:
            historial = json.load(f)
    else:
        historial = []
    historial.append(data)
    with open(TRAZABILIDAD_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

def get_usuario_actual():
    return st.session_state.get("usuario", None)

def cargar_usuario_info():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_permisos_usuario(usuario):
    usuarios = cargar_usuario_info()
    info = usuarios.get(usuario, {})
    return info.get("rol", ""), info.get("etapa_asignada", "")

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def guardar_evidencia(archivo, numero_op, etapa):
    if archivo:
        os.makedirs(EVIDENCIA_DIR, exist_ok=True)
        extension = os.path.splitext(archivo.name)[1]
        nombre_archivo = f"{numero_op}_{etapa}_{uuid.uuid4().hex}{extension}"
        ruta_archivo = os.path.join(EVIDENCIA_DIR, nombre_archivo)
        with open(ruta_archivo, "wb") as f:
            f.write(archivo.read())
        return nombre_archivo
    return None

def tablero_kanban():
    st.subheader("📊 Control de  Producción")

    etapas = cargar_etapas()
    ops = cargar_ops()

    if not etapas:
        st.warning("No hay etapas creadas.")
        return
    if not ops:
        st.info("No hay OPs creadas.")
        return

    usuario = get_usuario_actual()
    if not usuario:
        st.warning("No has iniciado sesión.")
        return
    rol, etapa_asignada = get_permisos_usuario(usuario)

    max_cols = 4
    filas_etapas = list(chunk_list(etapas, max_cols))

    for fila_etapas in filas_etapas:
        columnas = st.columns(len(fila_etapas))
        for i, etapa in enumerate(fila_etapas):
            with columnas[i]:
                st.markdown(f"<h6 style='text-align: center;'>{etapa['nombre']}➡️</h6>", unsafe_allow_html=True)
                ops_en_etapa = [op for op in ops if op["estado_actual"] == etapa["nombre"]]

                for op in ops_en_etapa:
                    # Determinar ícono y color del estado
                    color_fondo = "🟢"
                    if "color_alerta" in op:
                        if op["color_alerta"] == "red":
                            color_fondo = "🔴"
                        elif op["color_alerta"] == "orange":
                            color_fondo = "🟡"

                    # Construir expander con ícono de estado
                    with st.expander(f"{color_fondo} OP: {op['numero_op']} - {op['producto']}"):
                        
                        st.markdown(f"**Cliente:** {op['cliente']}")
                        st.markdown(f"**Cantidad:** {op['cantidad']}")


                        
                        # Obtener el nombre del archivo de imagen registrado en la OP
                        imagen_op = op.get("imagen_op")

                        if imagen_op:
                            ruta_imagen = IMAGENES_DIR / Path(imagen_op).name  # Componemos ruta usando pathlib

                            if ruta_imagen.exists():
                                if st.button(f"🔍 Visualizar OP", key=f"ver_imagen_{op['numero_op']}"):
                                    tab1, tab2 = st.tabs(["Detalles OP", "Imagen OP"])

                                    with tab1:
                                        # Aquí pones todos los detalles de la OP que quieras mostrar
                                        st.markdown(f"- **Cliente:** {op.get('cliente', '-')}")
                                        st.markdown(f"- **Producto:** {op.get('producto', '-')}")
                                        st.markdown(f"- **Cantidad:** {op.get('cantidad', '-')}")
                                        st.markdown(f"- **Fecha de entrega:** {op.get('fecha_entrega', '-')}")
                                        st.markdown(f"- **Etapas:** {', '.join(op.get('etapas', []))}")

                                    with tab2:
                                        st.image(str(ruta_imagen), caption=f"OP: {op['numero_op']} - Imagen asociada", use_container_width=True)
                            else:
                                st.warning(f"⚠️ La imagen asociada no se encontró en: {ruta_imagen}")
                        else:
                            st.info("🖼️ Esta OP no tiene imagen registrada.")

                        mostrar_alerta = st.checkbox("📢 Reportar alerta", key=f"ver_alerta_{op['numero_op']}")

                        if mostrar_alerta:
                            st.markdown("**Tipo de alerta**")
                            notif_maquina = st.checkbox("Report. máquina malograda (TPM)", key=f"notif_maquina_{op['numero_op']}")
                            notif_descanso = st.checkbox("Paro Almuerzo (1h) (Gestión Visual / TPM)", key=f"notif_descanso_{op['numero_op']}")
                            notif_material = st.checkbox("Reabastecimiento-material (Just-In-Time)", key=f"notif_material_{op['numero_op']}")
                            notif_op_fisica = st.checkbox("No tiene OP física (Gestión Visual)", key=f"notif_op_fisica_{op['numero_op']}")

                            st.markdown("**Subir Evidencia**")
                            evidencia = st.file_uploader("Foto (opcional)", type=["png", "jpg", "jpeg"], key=f"foto_{op['numero_op']}")
                            comentario = st.text_area("Comentario breve", key=f"comentario_{op['numero_op']}")

                            # Evaluación de alertas (no modificado)
                            tipo_alerta = None
                            color_alerta = None
                            if notif_maquina:
                                tipo_alerta = "Máquina malograda"
                                color_alerta = "red"
                            elif notif_material or notif_op_fisica:
                                tipo_alerta = "Falta de material o sin OP física"
                                color_alerta = "orange"

                            if tipo_alerta:
                                if st.button(f"🚨 Enviar alerta de: {tipo_alerta}", key=f"alerta_{op['numero_op']}"):
                                    now = datetime.now().isoformat()
                                    etapa_actual = op["estado_actual"]
                                    nombre_foto = guardar_evidencia(evidencia, op["numero_op"], etapa_actual)

                                    alerta = {
                                        "numero_op": op["numero_op"],
                                        "cliente": op["cliente"],
                                        "producto": op["producto"],
                                        "fecha": now,
                                        "usuario": usuario,
                                        "etapa": etapa_actual,
                                        "tipo_alerta": tipo_alerta,
                                        "color": color_alerta,
                                        "comentario": comentario,
                                        "foto_nombre": nombre_foto
                                    }

                                    os.makedirs(os.path.dirname(ALERTAS_FILE), exist_ok=True)
                                    if os.path.exists(ALERTAS_FILE):
                                        with open(ALERTAS_FILE, "r", encoding="utf-8") as f:
                                            alertas = json.load(f)
                                    else:
                                        alertas = []
                                    alertas.append(alerta)
                                    with open(ALERTAS_FILE, "w", encoding="utf-8") as f:
                                        json.dump(alertas, f, indent=4, ensure_ascii=False)

                                    op["color_alerta"] = color_alerta
                                    guardar_ops(ops)

                                    guardar_trazabilidad({
                                        "op": op["numero_op"],
                                        "fecha": now,
                                        "usuario": usuario,
                                        "etapa_anterior": etapa_actual,
                                        "etapa_nueva": etapa_actual,
                                        "tipo_alerta": tipo_alerta,
                                        "comentario": comentario,
                                        "foto_nombre": nombre_foto
                                    })

                                    st.success(f"🚨 Alerta registrada en etapa: {etapa_actual}")
                                    st.rerun()


                        # Checkbox para eliminar OP
                        eliminar_op = st.checkbox("🗑️ Eliminar esta OP", key=f"eliminar_{op['numero_op']}")

                        if eliminar_op:
                            if etapa_actual == "En Cola":
                                # Eliminar completamente
                                ops = [o for o in ops if o["numero_op"] != op["numero_op"]]
                                guardar_ops(ops)
                                st.success(f"✅ OP {op['numero_op']} eliminada completamente.")
                                st.rerun()
                            elif etapa_actual == etapas[-1]["nombre"]:  # Última etapa
                                st.info(f"🗓️ La OP {op['numero_op']} está en la última etapa y se limpiará automáticamente el fin de semana.")
                            else:
                                st.warning(f"⚠️ Solo se pueden eliminar OPs que estén en 'En Cola' o la última etapa.")

                        
                        if st.checkbox("➕ Dividir OP", key=f"dividir_{op['numero_op']}"):
                            num_subops = st.number_input("¿En cuántas partes quieres dividir esta OP?", min_value=2, max_value=10, step=1, key=f"n_partes_{op['numero_op']}")

                            cantidades = []
                            total_distribuido = 0
                            for i in range(num_subops):
                                cantidad_subop = st.number_input(
                                    f"Cantidad para sub-OP {i+1}",
                                    min_value=0,
                                    key=f"cantidad_subop_{op['numero_op']}_{i}"
                                )
                                cantidades.append(cantidad_subop)
                                total_distribuido += cantidad_subop

                            cantidad_original = op.get("cantidad", 0)
                            diferencia = cantidad_original - total_distribuido

                            if diferencia < 0:
                                st.error(f"La suma de las cantidades excede la cantidad original de {cantidad_original}")
                            elif diferencia > 0:
                                st.warning(f"Aún faltan distribuir {diferencia} unidades")
                            else:
                                if st.button("✅ Confirmar y crear sub-OPs", key=f"btn_confirmar_{op['numero_op']}"):
                                    nuevas_ops = []
                                    sufijos = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                                    for i in range(num_subops):
                                        nueva_op = op.copy()
                                        nueva_op["numero_op"] = f"{op['numero_op']}-{sufijos[i]}"
                                        nueva_op["cantidad"] = cantidades[i]
                                        nueva_op["estado_actual"] = op["estado_actual"]
                                        nuevas_ops.append(nueva_op)

                                    # Eliminar la OP original y agregar las nuevas
                                    ops = [o for o in ops if o["numero_op"] != op["numero_op"]]
                                    ops.extend(nuevas_ops)

                                    guardar_ops(ops)

                                    # Registrar en trazabilidad
                                    for subop in nuevas_ops:
                                        guardar_trazabilidad({
                                            "op": subop["numero_op"],
                                            "fecha": datetime.now().isoformat(),
                                            "usuario": usuario,
                                            "etapa_anterior": op["estado_actual"],
                                            "etapa_nueva": op["estado_actual"],
                                            "tipo_alerta": "Subdivisión de OP",
                                            "comentario": f"Creada como parte de subdivisión de {op['numero_op']}"
                                        })

                                    st.success(f"✔️ OP dividida exitosamente en {num_subops} sub-OPs.")
                                    st.rerun()
                        etapa_actual = op["estado_actual"]
                        if etapa_actual in op["etapas"]:
                            indice_etapa = op["etapas"].index(etapa_actual)
                        else:
                            st.error(f"Error: La etapa '{etapa_actual}' no está en las etapas de OP {op['numero_op']}.")
                            continue

                        puede_avanzar = indice_etapa < len(op["etapas"]) - 1
                        siguiente_etapa = op["etapas"][indice_etapa + 1] if puede_avanzar else None

                        if puede_avanzar:
                            datos = {
                                "cantidad_inicial": op.get("cantidad", 0),
                                "tiempo_inicio": None,
                                "tiempo_fin": None,
                                "tiempo_total": None,
                                "personas": None
                            }

                            numero_op = op["numero_op"]
                            mostrar_formulario = st.checkbox("📝 Registrar datos de etapa", key=f"check_formulario_{numero_op}")

                            if mostrar_formulario:
                                st.write("📊 Registro de Cantidades")
                                st.info(f"Cantidad inicial: **{datos['cantidad_inicial']}** unidades")

                                mt_utilizada = st.number_input("Cantidad de materia prima utilizada (MT)", min_value=0, key=f"mt_{numero_op}")
                                merma = st.number_input("Cantidad de merma", min_value=0, key=f"merma_{numero_op}")

                                cantidad_final = mt_utilizada - merma
                                st.success(f"Cantidad final: **{cantidad_final}** unidades")

                                mostrar_tiempos = st.checkbox("⏱️ Registrar tiempos VSM", key=f"check_tiempos_{numero_op}")
                                if mostrar_tiempos:
                                    st.subheader("📈 Tiempos VSM")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        setup_time = st.number_input("Setup Time (min)", min_value=0, key=f"setup_{numero_op}",help="Tiempo de preparación antes de comenzar la producción"  )
                                    with col2:
                                        cycle_time = st.number_input("Cycle Time por unidad (seg)", min_value=0, key=f"cycle_{numero_op}",help="Tiempo de ciclo necesario para producir una unidad" )
                                    with col3:
                                        idle_time = st.number_input("Idle Time (min)", min_value=0, key=f"idle_{numero_op}", help="Tiempo en el que la máquina o recurso está inactivo" )
                                mostrar_crono = st.checkbox("🕒 Iniciar proceso con cronómetro", key=f"check_crono_{numero_op}")
                                if mostrar_crono:
                                    if st.button("▶️ Iniciar proceso", key=f"iniciar_{numero_op}"):
                                        datos["tiempo_inicio"] = time.time()
                                        st.success("Proceso iniciado...")

                                    if st.button("⏹ Finalizar proceso", key=f"fin_{numero_op}"):
                                        datos["tiempo_fin"] = time.time()
                                        if datos["tiempo_inicio"]:
                                            tiempo_total = round((datos["tiempo_fin"] - datos["tiempo_inicio"]) / 60, 2)
                                            datos["tiempo_total"] = tiempo_total
                                            st.success(f"⏱️ Tiempo total: {tiempo_total} minutos")
                                        else:
                                            st.warning("Debes iniciar primero el proceso.")

                                mostrar_personas = st.checkbox("👥 Registrar número de personas", key=f"check_personas_{numero_op}")
                                if mostrar_personas:
                                    personas = st.number_input("Número de personas involucradas", min_value=1, key=f"personas_{numero_op}")
                                    datos["personas"] = personas

                                st.write("📄 Resumen de etapa")
                                st.write(f"- Cantidad inicial: {datos['cantidad_inicial']}")
                                st.write(f"- MT utilizada: {mt_utilizada}")
                                st.write(f"- Merma: {merma}")
                                st.write(f"- Cantidad final: {cantidad_final}")
                                if mostrar_tiempos:
                                    st.write(f"- Setup Time: {setup_time} min")
                                    st.write(f"- Cycle Time: {cycle_time} seg")
                                    st.write(f"- Idle Time: {idle_time} min")
                                if datos["tiempo_total"]:
                                    st.write(f"- Tiempo total proceso: {datos['tiempo_total']} min")
                                if mostrar_personas:
                                    st.write(f"- Personas involucradas: {datos['personas']}")

                                if st.button("📤 Enviar a siguiente etapa", key=f"btn_avanzar_{numero_op}"):
                                    op["estado_actual"] = siguiente_etapa
                                    op["cantidad"] = cantidad_final
                                    guardar_ops(ops)
                                    guardar_trazabilidad({
                                        "op": numero_op,
                                        "fecha": datetime.now().isoformat(),
                                        "usuario": usuario,
                                        "etapa_anterior": etapa_actual,
                                        "etapa_nueva": siguiente_etapa,
                                        "mt_utilizada": mt_utilizada,
                                        "merma": merma,
                                        "cantidad_final": cantidad_final,
                                        "setup_time": setup_time if mostrar_tiempos else None,
                                        "cycle_time": cycle_time if mostrar_tiempos else None,
                                        "idle_time": idle_time if mostrar_tiempos else None,
                                        "tiempo_total": datos["tiempo_total"],
                                        "personas": datos["personas"]
                                    })
                                    st.success(f"✅ OP {numero_op} enviada a etapa: {siguiente_etapa}")
                                    st.rerun()
                        else:
                            st.success("✅ Esta OP ha completado todas sus etapas.")

                        st.markdown("</div>", unsafe_allow_html=True)

                        



OPS_FILE = "data/ordenes_produccion.json"
TRAZABILIDAD_FILE = "data/trazabilidad.json"

def visualizar_trazabilidad_sankey():
    st.subheader("🔎 Visualización de Flujo de Producción (Sankey)")

    # Validación de archivos
    if not os.path.exists(OPS_FILE) or not os.path.exists(TRAZABILIDAD_FILE):
        st.info("📂 No hay datos suficientes para graficar.")
        return

    with open(OPS_FILE, "r", encoding="utf-8") as f:
        ordenes = json.load(f)

    with open(TRAZABILIDAD_FILE, "r", encoding="utf-8") as f:
        historial = json.load(f)

    if not ordenes or not historial:
        st.info("📂 No hay registros de OPs o trazabilidad.")
        return

    nodos = []
    for op in ordenes:
        for etapa in op.get("etapas", []):
            if etapa not in nodos:
                nodos.append(etapa)

    for evento in historial:
        if evento["etapa_anterior"] not in nodos:
            nodos.append(evento["etapa_anterior"])
        if evento["etapa_nueva"] not in nodos:
            nodos.append(evento["etapa_nueva"])

    indice_nodos = {etapa: i for i, etapa in enumerate(nodos)}

    colores_op = {}
    for op in ordenes:
        colores_op[op["numero_op"]] = "hsl(%d,70%%,50%%)" % random.randint(0, 360)

    source, target, value, hover_labels, colors = [], [], [], [], []
    for evento in historial:
        op = evento.get("op")
        origen = evento.get("etapa_anterior")
        destino = evento.get("etapa_nueva")

        if origen and destino and op:
            source.append(indice_nodos[origen])
            target.append(indice_nodos[destino])
            value.append(0.04)
            colors.append(colores_op.get(op, "gray"))
            hover_labels.append(
                f"OP {op}<br>{origen} → {destino}"
                f"<br>Usada: {evento.get('mt_utilizada', 0)}"
                f"<br>Merma: {evento.get('merma', 0)}"
                f"<br>Final: {evento.get('cantidad_final', 0)}"
                f"<br>Setup: {evento.get('setup_time', 0)}"
                f"<br>Ciclo: {evento.get('cycle_time', 0)}"
                f"<br>Idle: {evento.get('idle_time', 0)}"
            )

    if not source:
        st.warning("⚠️ No hay suficientes datos de flujo para graficar.")
        return

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=5,
            thickness=9,
            line=dict(color="blue", width=2),
            label=nodos,
            color="blue"
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=colors,
            line=dict(width=1),   # 👈 aquí controlas el grosor de TODAS las líneas
            customdata=hover_labels,
            hovertemplate='%{customdata}<extra></extra>'
        )
    )])

    fig.update_layout(title_text="📊 Flujo Real de Producción (Sankey)", font_size=12)
    st.plotly_chart(fig, use_container_width=True)

    fig.update_layout(
    title_text="📊 Flujo Real de Producción (Sankey)",
    font=dict(size=16, color="white", family="Arial")  # ✅ aquí va el estilo de la letra
)
