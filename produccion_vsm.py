# vsm.py
# Requisitos: streamlit, streamlit-echarts, pandas
import streamlit as st
from streamlit_echarts import st_echarts
import pandas as pd
import json
import os
from datetime import datetime
import random

import speech_recognition as sr
import pyttsx3
# --- Rutas a archivos (ajusta si es necesario) ---
TRAZABILIDAD_FILE = os.path.join("data", "trazabilidad.json")
ORDENES_FILE = os.path.join("data", "ordenes_produccion.json")

# -----------------------
# Utilidades de carga
# -----------------------
def cargar_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def cargar_trazabilidad():
    data = cargar_json(TRAZABILIDAD_FILE)
    if data is None:
        return []
    # Aseguramos que sea lista
    return data if isinstance(data, list) else [data]

def cargar_ordenes():
    data = cargar_json(ORDENES_FILE)
    if data is None:
        return []
    return data if isinstance(data, list) else [data]

# -----------------------
# Normalización de entradas de trazabilidad
# -----------------------
def extraer_campos_traza(traza):
    """
    Extrae campos relevantes desde una entrada de trazabilidad.
    Soporta entradas con 'datos_etapa' (objeto) o con campos planos.
    Devuelve dic con valores numéricos o None cuando no exista.
    """
    fuente = {}
    if isinstance(traza, dict) and "datos_etapa" in traza and isinstance(traza["datos_etapa"], dict):
        fuente = traza["datos_etapa"]
    else:
        fuente = traza

    def get_num(k):
        v = fuente.get(k)
        if v is None:
            return None
        try:
            return float(v)
        except Exception:
            return None

    return {
        "cycle_time": get_num("cycle_time") or get_num("tiempo_ciclo") or get_num("tiempo_ciclo_seg") or get_num("tiempo_ciclo_min"),
        "idle_time": get_num("idle_time") or get_num("tiempo_inactivo") or get_num("idle_time_min"),
        "setup_time": get_num("setup_time") or get_num("tiempo_setup") or get_num("setup_time_min"),
        "tiempo_total": get_num("tiempo_total"),
        "merma": get_num("merma") or get_num("mermas"),
        "cantidad_final": get_num("cantidad_final") or get_num("cantidad_entregada"),
        "personas": get_num("personas"),
        "errores": get_num("errores"),
        "rechazos": get_num("rechazos"),
        "mt_utilizada": get_num("mt_utilizada") or get_num("materia_utilizada")
    }

def parse_fecha(traza):
    f = traza.get("fecha") or traza.get("timestamp") or traza.get("fecha_inicio")
    if not f:
        return None
    try:
        return datetime.fromisoformat(f)
    except Exception:
        try:
            return datetime.strptime(f, "%Y-%m-%dT%H:%M:%S.%f")
        except Exception:
            return None

# -----------------------
# Normalizar OP -> dataframe para VSM
# -----------------------
def normalizar_op_para_vsm(op, trazabilidad_list):
    """
    op: dict de ordenes_produccion.json
    trazabilidad_list: lista de dicts de trazabilidad.json
    Devuelve dataframe con columnas:
    ['etapa', 'cycle_time', 'idle_time', 'setup_time', 'merma', 'cantidad_final', 'tiempo_total', 'eficiencia', 'lead_time_acumulado', 'personas', 'errores', 'rechazos']
    """
    etapas = op.get("etapas", []) or []
    numero_op = str(op.get("numero_op", "")).strip()
    # Filtrar trazas correspondientes a esta OP
    trazas_op = [t for t in trazabilidad_list if str(t.get("op","")).strip() == numero_op]
    # normalizar fechas
    for t in trazas_op:
        t["_fecha_parsed"] = parse_fecha(t) or datetime.min

    datos = []
    lead_time = 0

    for etapa in etapas:
        # buscar la traza más reciente para esta etapa (match case-insensitive en etapa_nueva o 'etapa')
        matches = [t for t in trazas_op if (
            (t.get("etapa_nueva") and str(t.get("etapa_nueva")).strip().lower() == str(etapa).strip().lower())
            or (t.get("etapa") and str(t.get("etapa")).strip().lower() == str(etapa).strip().lower())
            or (t.get("etapa_anterior") and str(t.get("etapa_anterior")).strip().lower() == str(etapa).strip().lower())
        )]
        chosen = None
        if matches:
            # elegimos la con mayor fecha parseada
            matches_sorted = sorted(matches, key=lambda x: x.get("_fecha_parsed", datetime.min), reverse=True)
            chosen = matches_sorted[0]

        if chosen:
            campos = extraer_campos_traza(chosen)
        else:
            campos = {
                "cycle_time": None,
                "idle_time": None,
                "setup_time": None,
                "tiempo_total": None,
                "merma": None,
                "cantidad_final": None,
                "personas": None,
                "errores": None,
                "rechazos": None
            }

        # convertir None a 0 para cálculos (pero manteniendo posibilidad de null si quieres)
        ct = float(campos.get("cycle_time") or 0)
        idle = float(campos.get("idle_time") or 0)
        setup = float(campos.get("setup_time") or 0)
        tiempo_total = campos.get("tiempo_total")
        if tiempo_total is None:
            tiempo_total = ct + idle + setup
        else:
            tiempo_total = float(tiempo_total)

        eficiencia = round((ct / tiempo_total) * 100, 2) if tiempo_total > 0 else 0

        lead_time += tiempo_total

        datos.append({
            "etapa": etapa,
            "cycle_time": ct,
            "idle_time": idle,
            "setup_time": setup,
            "merma": float(campos.get("merma") or 0),
            "cantidad_final": float(campos.get("cantidad_final") or 0),
            "tiempo_total": tiempo_total,
            "eficiencia": eficiencia,
            "lead_time_acumulado": lead_time,
            "personas": float(campos.get("personas") or 0),
            "errores": int(campos.get("errores") or 0),
            "rechazos": int(campos.get("rechazos") or 0)
        })

    return pd.DataFrame(datos)

# -----------------------
# Simulación (mantener para fallback)
# -----------------------
def generar_simulado(etapas, seed=None):
    if seed is not None:
        random.seed(seed)
    datos = []
    lead_time = 0
    for etapa in etapas:
        ct = random.randint(20, 80)
        idle = random.randint(5, 30)
        setup = random.randint(5, 25)
        errores = random.randint(0, 3)
        rechazos = random.randint(0, 8)
        total = ct + idle + setup
        eficiencia = round((ct / total) * 100, 2) if total > 0 else 0
        lead_time += total
        datos.append({
            "etapa": etapa,
            "cycle_time": ct,
            "idle_time": idle,
            "setup_time": setup,
            "merma": 0,
            "cantidad_final": 0,
            "tiempo_total": total,
            "eficiencia": eficiencia,
            "lead_time_acumulado": lead_time,
            "personas": 1,
            "errores": errores,
            "rechazos": rechazos
        })
    return pd.DataFrame(datos)

# -----------------------
# Gráficas helper
# -----------------------

def graficar_echarts(titulo, categorias, datos, tipo="bar", referencia=None):
    options = {
        "backgroundColor": "#ffffff",  # 👈 Fondo blanco puro
        "title": {"text": titulo},
        "xAxis": {"type": "category", "data": categorias},
        "yAxis": {"type": "value"},
        "series": [{"data": datos, "type": tipo, "label": {"show": True, "position": "top"}}],

        # 👇 Caja de estilo con sombra y bordes redondeados
        "graphic": [{
            "type": "rect",
            "left": "center",
            "top": "middle",
            "shape": {"width": "95%", "height": "95%"},
            "style": {
                "fill": "#ffffff",              # Fondo blanco puro
                "shadowColor": "rgba(0,0,0,0.25)", # Sombra gris suave
                "shadowBlur": 20,
                "shadowOffsetX": 5,
                "shadowOffsetY": 5,
                "borderRadius": 50             # Bordes redondeados
            },
            "z": -10  # lo pone detrás de la gráfica
        }]
    }
    if referencia is not None:
        options["series"].append({
            "data": [referencia] * len(categorias),
            "type": "line",
            "label": {"show": True, "position": "top"},
            "lineStyle": {"type": "dashed"},
            "name": "Referencia"
        })
    st_echarts(options=options, height="380px")



# 🔊 Función única para leer texto
def leer_texto(texto):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)   # velocidad de voz
        engine.setProperty('volume', 1.0) # volumen máximo

        # Opcional: cambiar voz (masculina/femenina según sistema)
        voces = engine.getProperty('voices')
        if voces:
            engine.setProperty('voice', voces[0].id)

        engine.say(texto)
        engine.runAndWait()
    except Exception as e:
        print(f"Error al leer texto: {e}")

# 🤖 Asistente Oso
def asistente_oso(df, eficiencia_global, cuello, takt_time):
    recognizer = sr.Recognizer()

    # 🔊 Oso saluda
    saludo = "Hola, soy Oso. Tu asistente de producción. ¿Quieres que te dé el reporte de VSM?"
    st.write(f"🗣️ Oso dice: {saludo}")
    leer_texto(saludo)

    # 🎤 Escuchar la respuesta del usuario
    with sr.Microphone() as source:
        st.info("🎙️ Escuchando... responde con 'sí' o 'no'")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

    try:
        texto = recognizer.recognize_google(audio, language="es-ES").lower()
        st.write(f"👉 Dijiste: {texto}")
    except:
        texto = ""
        st.warning("No se entendió lo que dijiste.")

    if "sí" in texto or "reporte" in texto:
        # 📊 Preparar reporte de VSM
        reporte = f"""
        Reporte de la OP:
        Eficiencia global: {eficiencia_global} por ciento.
        Cuello de botella en la etapa {cuello['etapa']} con {int(cuello['tiempo_total'])} minutos.
        Takt time: {takt_time} minutos por unidad.
        """
        st.success(reporte)
        leer_texto(reporte)  # 🔊 Aquí lo lee en voz alta
    else:
        despedida = "De acuerdo, no mostraré el reporte por ahora."
        st.write(f"🗣️ Oso dice: {despedida}")
        leer_texto(despedida)






# -----------------------
# Módulo principal
# -----------------------
def mostrar_vsm():
    st.header("📦 Dashboard de OP y VSM")
   
    # Cargar datos
    trazabilidad = cargar_trazabilidad()
    ordenes = cargar_ordenes()

    # Fuente de datos: simular o reales
    fuente = st.radio("Fuente de datos:", ("Simular (aleatorio)", "Usar datos reales (archivos JSON)"))

    # Default etapas (por si simular)
    etapas_default = ["Recepción", "Almacén", "Preparación", "Impresión", "Barnizado", "Corte", "Empaque"]

    df = pd.DataFrame()
    selected_order = None

    if fuente == "Usar datos reales (archivos JSON)":
        if not ordenes:
            st.warning("No se encontraron órdenes en data/ordenes_produccion.json — caeré a simulación.")
            fuente = "Simular (aleatorio)"
        else:
            # selector OP
            solo_en_curso = st.checkbox("Mostrar solo OP en curso (no TERMINADOS)", value=True)
            ops_filtradas = ordenes
            if solo_en_curso:
                ops_filtradas = [o for o in ordenes if str(o.get("estado_actual","")).strip().upper() != "TERMINADOS"]

            if not ops_filtradas:
                st.warning("No hay órdenes disponibles según el filtro.")
                st.stop()

            opciones = ops_filtradas
            sel = st.selectbox("📋 Selecciona la OP:", options=opciones,
                               format_func=lambda x: f"OP {x.get('numero_op')} — {x.get('cliente','')} — {x.get('producto','')} — {x.get('estado_actual','')}")
            selected_order = sel
            # Normalizar trazabilidad para la OP seleccionada
            df = normalizar_op_para_vsm(selected_order, trazabilidad)

    # Si decidimos simular (por elección o falta de datos reales)
    if fuente == "Simular (aleatorio)":
        etapas = etapas_default
        # permitimos al usuario elegir número de estaciones / etapas
        n = st.slider("Número de etapas a simular", min_value=3, max_value=20, value=len(etapas))
        # si aumentan las etapas, generamos nombres automáticos
        if n <= len(etapas):
            etapas = etapas[:n]
        else:
            etapas = etapas + [f"Etapa {i}" for i in range(len(etapas)+1, n+1)]
        df = generar_simulado(etapas)

    # Si df vacío — salir
    if df.empty:
        st.info("No hay datos para mostrar.")
        return

    # -----------------------
    # Cálculos KPIs
    # -----------------------
    total_unidades = int(selected_order.get("cantidad", 120) if selected_order else 120)
    turno_min = 480  # configurable si quieres exponer como input
    takt_time = round(turno_min / total_unidades, 2) if total_unidades > 0 else None

    eficiencia_global = round(df["eficiencia"].mean(), 2) if "eficiencia" in df.columns else 0
    tiempo_ciclo_prom = round(df["cycle_time"].mean(), 2) if "cycle_time" in df.columns else 0
    tiempo_inactivo_total = int(df["idle_time"].sum()) if "idle_time" in df.columns else 0
    setup_total = int(df["setup_time"].sum()) if "setup_time" in df.columns else 0
    tiempo_total_sum = int(df["tiempo_total"].sum()) if "tiempo_total" in df.columns else 0
    lead_time_final = int(df["lead_time_acumulado"].iloc[-1]) if "lead_time_acumulado" in df.columns else tiempo_total_sum

    # Cuello de botella (la etapa con mayor tiempo_total)
    cuello = {"etapa": "", "tiempo_total": 0}
    if "tiempo_total" in df.columns:
        max_idx = df["tiempo_total"].idxmax()
        cuello = {"etapa": df.at[max_idx, "etapa"], "tiempo_total": float(df.at[max_idx, "tiempo_total"])}

    # -----------------------
    # Mostrar KPIs y tabla
    # -----------------------
    # ==================== 🎨 ESTILO PERSONALIZADO PARA METRICS ====================
    st.markdown("""
        <style>
        /* Caja general de cada métrica */
        div[data-testid="stMetric"] {
            background-color: #ffffff;      /* 👈 Fondo blanco (puedes cambiarlo a cualquier color) */
            border-radius: 15px;            /* Bordes redondeados */
            padding: 15px;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.2);  /* Sombra efecto 3D */
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    # ==================== 📊 KPIs ====================
    st.subheader("🎯 KPIs de la Orden")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⏱ Tiempo Total", f"{tiempo_total_sum} min")
    col2.metric("⏳ Lead Time", f"{lead_time_final} min")
    col3.metric("💤 Tiempo Inactivo", f"{tiempo_inactivo_total} min")
    col4.metric("🧰 Setup Total", f"{setup_total} min")

    col5, col6, col7 = st.columns(3)
    col5.metric("🔁 Takt Time", f"{takt_time} min/u" if takt_time is not None else "N/A")
    col6.metric("🍾 Cuello de Botella", f"{cuello['etapa']}")
    col7.metric("📈 Eficiencia Global", f"{eficiencia_global} %")

    st.subheader("📋 Datos por etapa")
    st.dataframe(df, use_container_width=True)

    # -----------------------
    # Recomendaciones automáticas
    # -----------------------
    st.subheader("🛠️ Herramientas Lean sugeridas con justificación")
    recomendaciones = []

    def clasificar_gravedad(condicion):
        if condicion == "alta":
            return "#ff0000"
        elif condicion == "media":
            return "#ffe603"
        elif condicion == "baja":
            return "#ff6a00"
        return "#00ff91"

    if eficiencia_global < 70:
        recomendaciones.append({
            "herramienta": "TPM (Mantenimiento Productivo Total)",
            "justificacion": f"La eficiencia global es baja ({eficiencia_global}%). TPM ayuda a mejorar la disponibilidad.",
            "nivel": "alta"
        })

    if tiempo_inactivo_total > 100:
        recomendaciones.append({
            "herramienta": "Jidoka o Andon",
            "justificacion": f"Se detectó un alto tiempo inactivo total ({tiempo_inactivo_total} min).",
            "nivel": "media"
        })

    if cuello["etapa"]:
        recomendaciones.append({
            "herramienta": "Balanceo de línea",
            "justificacion": f"Se identificó un cuello de botella en la etapa '{cuello['etapa']}' con {int(cuello['tiempo_total'])} min.",
            "nivel": "media"
        })

    if takt_time is not None and takt_time < tiempo_ciclo_prom:
        recomendaciones.append({
            "herramienta": "SMED (Setup rápido)",
            "justificacion": f"El tiempo de ciclo promedio ({tiempo_ciclo_prom} min) es mayor al Takt Time ({takt_time} min/u).",
            "nivel": "alta"
        })

    if setup_total > 60:
        recomendaciones.append({
            "herramienta": "SMED (Altos tiempos de setup)",
            "justificacion": f"El tiempo total de setup es elevado ({setup_total} min).",
            "nivel": "media"
        })

    total_rechazos = int(df["rechazos"].sum()) if "rechazos" in df.columns else 0
    total_errores = int(df["errores"].sum()) if "errores" in df.columns else 0

    if total_rechazos > 10:
        recomendaciones.append({
            "herramienta": "Poka-Yoke",
            "justificacion": f"Se registraron {total_rechazos} rechazos, lo que indica errores de calidad.",
            "nivel": "media"
        })

    if total_errores > 5:
        recomendaciones.append({
            "herramienta": "5S + Estandarización de trabajo",
            "justificacion": f"Se detectaron {total_errores} errores.",
            "nivel": "baja"
        })

    if recomendaciones:
        for i in range(0, len(recomendaciones), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(recomendaciones):
                    r = recomendaciones[i + j]
                    with cols[j]:
                        st.markdown(f"""
                        <div style="background-color:{clasificar_gravedad(r['nivel'])}; padding:12px; border-radius:8px;">
                            <h5 style="margin:0">✔ {r['herramienta']}</h5>
                            <p style="margin:0.25rem 0 0 0; font-size:13px;">{r['justificacion']}</p>
                            <p style="margin-top:6px; font-size:12px; color:#333;"><strong>Prioridad:</strong> {r['nivel'].capitalize()}</p>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("✅ No se detectan mejoras urgentes.")

    # -----------------------
    # Visualizaciones
    # -----------------------
    st.markdown("## 📊 Visualizaciones Lean")
    colA, colB = st.columns(2)
    
    with colA:
        
        st.markdown("### 1. Diagrama de flujo (etapas)")

        etapas = df["etapa"].tolist()

        # 🔹 Ejemplo de estados asignados a cada etapa
        estados_por_etapa = {
            "Corte": "terminado",
            "Impresión": "en proceso",
            "Barnizado": "pendiente",
            "Empaque": "pendiente"
        }

        # 🔹 Colores según estado
        colores_estados = {
            "pendiente": "#B0BEC5",    # gris
            "en proceso": "#FFC107",   # amarillo
            "terminado": "#4CAF50"     # verde
        }

        data_nodes = [
            {
                "name": etapa,
                "symbolSize": 70,
                "draggable": True,
                "itemStyle": {
                    "color": colores_estados.get(estados_por_etapa.get(etapa, "pendiente"), "#B0BEC5"),
                    "shadowColor": "rgba(0,0,0,0.3)",
                    "shadowBlur": 15,
                    "shadowOffsetX": 5,
                    "shadowOffsetY": 5
                },
                "label": {
                    "show": True,
                    "formatter": f"{etapa}\n({estados_por_etapa.get(etapa, 'pendiente')})"
                }
            }
            for etapa in etapas
        ]

        links = [{"source": etapas[i], "target": etapas[i + 1]} for i in range(len(etapas) - 1)]

        flow_options = {
            "backgroundColor": "#ffffff",
            "tooltip": {"formatter": "{b}"},  
            "series": [{
                "type": "graph",
                "layout": "force",
                "force": {
                    "repulsion": 200,
                    "edgeLength": 100
                },
                "symbolSize": 70,
                "roam": True,
                "label": {"show": True},
                "edgeSymbol": ['none', 'arrow'],
                "edgeSymbolSize": [4, 10],
                "data": data_nodes,
                "links": links,
                "lineStyle": {"opacity": 0.9, "width": 2, "curveness": 0.1}
            }]
        }

        st_echarts(options=flow_options, height="360px")

    with colB:
        st.markdown("### 2. Cycle Time por etapa")
        graficar_echarts("Cycle Time", df["etapa"].tolist(), df["cycle_time"].tolist(), "bar", referencia=takt_time)

    colC, colD = st.columns(2)
    with colC:
        st.markdown("### 3. Idle Time por etapa")
        graficar_echarts("Idle Time", df["etapa"].tolist(), df["idle_time"].tolist())

    with colD:
        st.markdown("### 4. Setup Time por etapa")
        graficar_echarts("Setup Time", df["etapa"].tolist(), df["setup_time"].tolist())

    colE, colF = st.columns(2)
    with colE:
        st.markdown("### 5. VA vs NVA")
        total_int = int(df["tiempo_total"].sum())
        va = int(df["cycle_time"].sum())
        nva = max(total_int - va, 0)
        donut_opts = {
            "tooltip": {"trigger": "item"},
            "legend": {"top": "5%", "left": "center"},
            "series": [{
                "name": "Tiempo",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "label": {"show": True, "position": "inside"},
                "data": [
                    {"value": va, "name": "Valor Agregado"},
                    {"value": nva, "name": "No Valor Agregado"}
                ]
            }]
        }
        st_echarts(options=donut_opts, height="360px")

    with colF:
        st.markdown("### 6. Lead Time acumulado")
        graficar_echarts("Lead Time acumulado", df["etapa"].tolist(), df["lead_time_acumulado"].tolist(), "line")

    colG, colH = st.columns(2)
    with colG:
        st.markdown("### 7. Mermas (rechazos)")
        if "merma" in df.columns:
            graficar_echarts("Mermas", df["etapa"].tolist(), df["merma"].tolist())
        else:
            st.info("No hay datos de merma en el dataset.")

    with colH:
        st.markdown("### 8. Paros / Errores")
        if "errores" in df.columns:
            graficar_echarts("Errores", df["etapa"].tolist(), df["errores"].tolist())
        else:
            st.info("No hay datos de errores en el dataset.")

    st.markdown("### 9. Cuello de Botella - Tiempo por Etapa")
    tipo_linea = st.radio("Selecciona línea de referencia:", ("Takt Time (Total)", "Takt Time (Ciclo)"))
    if tipo_linea == "Takt Time (Total)":
        linea_takt = df["tiempo_total"].mean()
    else:
        linea_takt = tiempo_ciclo_prom

    max_tiempo = df["tiempo_total"].max() if "tiempo_total" in df.columns else 0
    etapas_cb = df["etapa"].tolist()
    tiempos_cb = df["tiempo_total"].tolist() if "tiempo_total" in df.columns else [0]*len(etapas_cb)
    colores = ["#e11912" if t == max_tiempo else "#00ff48" for t in tiempos_cb]
    cb_chart_opts = {
        "xAxis": {"type": "category", "data": etapas_cb},
        "yAxis": {"type": "value"},
        "series": [
            {
                "type": "bar",
                "data": [{"value": t, "itemStyle": {"color": c}} for t, c in zip(tiempos_cb, colores)],
                "label": {"show": True, "position": "top"}
            },
            {
                "type": "line",
                "name": "Línea Takt Time",
                "data": [linea_takt] * len(etapas_cb),
                "lineStyle": {"type": "dashed", "color": "#b2b3b4"},
                "symbol": "none"
            }
        ],
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Tiempo Total", "Línea Takt Time"]}
    }
    st_echarts(options=cb_chart_opts, height="450px")

    


