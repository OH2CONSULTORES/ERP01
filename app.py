import streamlit as st
import time
# ⚙ Configuración de la página
st.set_page_config(
    page_title="ERP. V3 INDUSTRIA DEL TROQUEL",
    page_icon="imagen/ico.png",  # Ruta al archivo de imagen
    layout="wide"
)

# 🚫 Eliminar header, menú, footer y también el header de la barra lateral
st.markdown(
    """
    <style>
    /* Ocultar header principal */
    header[data-testid="stHeader"] {
        display: none;
    }

    /* Ocultar menú */
    #MainMenu {
        visibility: hidden;
    }

    /* Ocultar footer */
    footer {
        visibility: hidden;
    }

    /* Quitar espacio superior */
    .block-container {
        padding-top: 0.1rem !important;
    }

    /* Ocultar header del sidebar (logo y botón de colapsar) */
    [data-testid="stSidebarHeader"] {
        display: none;
    }

    /* Opcional: ajustar el tamaño del contenido del sidebar */
    [data-testid="stSidebar"] {
        padding-top: 0.1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)



# Ocultar header original
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)






# 🎨 Estilos personalizados
# 🎨 Estilos personalizados con paleta Azul + Blanco + Verde Agua
# 🎨 Estilos personalizados con efecto 3D
# 🎨 Estilos personalizados con efecto 3D en botones y tabs
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #1E3A8A, #1E3A8A); /* Azul oscuro a azul fuerte */
        color: white;
    }

    /* Títulos principales */
    h1, h2, h3, h4, h5, h6 {
        color: #7FFFD4 !important; /* Verde agua claro */
    }

    /* Texto en Markdown */
    .stMarkdown, .stMarkdown p, .stMarkdown strong {
        color: #FFFFFFFF !important; /* Blanco */
    }

    /* Etiquetas de widgets (inputs, sliders, etc.) */
    label[data-testid="stWidgetLabel"] {
        color: white !important;
        font-weight: bold;
    }

    /* Tabs con efecto 3D */
    .stTabs [role="tab"] {
        background: linear-gradient(145deg, #7FFFD4, #00CED1);
        color: #003366;
        font-weight: bold;
        border-radius: 12px;
        margin-right: 6px;
        padding: 8px 16px;
        border: none;
        box-shadow: 4px 4px 8px #00334d, -4px -4px 8px #ffffff;
        transition: all 0.2s ease-in-out;
    }
    .stTabs [role="tab"]:hover {
        background: linear-gradient(145deg, #00CED1, #20B2AA);
        color: white;
        transform: translateY(-3px);
        box-shadow: 6px 6px 10px #002233, -6px -6px 10px #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(145deg, #20B2AA, #008B8B) !important;
        color: white !important;
        font-weight: bold;
        transform: translateY(-2px);
        box-shadow: inset 4px 4px 8px #00334d, inset -4px -4px 8px #ffffff;
    }

    /* Expanders */
    .stExpander {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(127, 255, 212, 0.4); /* Borde verde agua */
        border-radius: 9px;
        padding: 3px;
        margin-bottom: 3px;
    }
    .stExpander:hover {
        background: rgba(127, 255, 212, 0.2);
    }

    /* DataFrames y Markdown contenedores */
    .stMarkdown div, .stDataFrame {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 9px;
        padding: 0px;
    }

    /* 🔘 Botones 3D */
    .stButton button {
        width: 100%;
        margin: 8px 8px;
        padding: 12px;  
        border-radius: 8px;
        border: none;
        font-weight: bold;
        font-size: 13px;
        color: #003968; /* Azul oscuro */
        background: linear-gradient(145deg, #7FFFD4, #00CED1);
        box-shadow: 4px 4px 8px #00334d, -4px -4px 8px #ffffff;
        transition: all 0.2s ease-in-out;
    }

    /* Hover efecto */
    .stButton button:hover {
        background: linear-gradient(145deg, #00CED1, #20B2AA);
        color: white;
        transform: translateY(-2px);
        box-shadow: 6px 6px 10px #002233, -6px -6px 10px #ffffff;
    }

    /* Botón presionado */
    .stButton button:active {
        transform: translateY(2px);
        box-shadow: inset 4px 4px 8px #00334d, inset -4px -4px 8px #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)


import login
import produccion_etapas
import produccion_crear_op
import produccion
import json
import os
import alertas
import produccion_trazabilidad
import produccion_tpm  # Módulo TPM
import logistica_planos  # ⬅ Aquí importamos tu nuevo módulo
import produccion_vsm
import produccion_5s
import configuracion
import alertas_admin
import orden_general
import d_ventas
import logistica
import q_calidad
import orden_servicios
import produccion_smed
from inventario import mostrar_gestion_inventario  # ⬅ Aquí importamos Inventario

# Archivos de datos
ALERTAS_FILE = "data/alertas_pendientes.json"
OPS_FILE = "data/ordenes_produccion.json"

# Mostrar información del usuario y botón de logout
def mostrar_usuario_rol_logout():
    col1, col2 = st.sidebar.columns([3, 1])
        
    def colored_write(label, value, label_color="#1E90FF", value_color="#000000"):
        st.markdown(
            f"<span style='color:{label_color}; font-weight:bold;'>{label}:</span> "
            f"<span style='color:{value_color};'>{value}</span>",
            unsafe_allow_html=True
        )

    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)

        usuario = st.session_state.get("usuario", "Invitado")
        rol = st.session_state.get("rol", "Invitado")
        etapa = st.session_state.get("etapa", "None")

        # Aquí definimos los colores
        colored_write("Usuario", usuario, "#1E90FF", "#FF0000" if usuario in ["None", "Invitado"] else "#000000")
        colored_write("Rol", rol, "#1E90FF", "#FF0000" if rol in ["None", "Invitado"] else "#000000")
        colored_write("Etapa", etapa, "#1E90FF", "#FF0000" if etapa in ["None", "Invitado"] else "#000000")




    with col2:
        if st.button("🔚"):
            st.session_state.clear()
            st.rerun()



# Cargar OPs desde archivo JSON
def cargar_ops():
    if os.path.exists(OPS_FILE):
        with open(OPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


if 'login' not in st.session_state or not st.session_state['login']:

    login.login_modulo()

    
else:
    progress_text = "⏳ Preparando tu panel..."
    # Creamos un contenedor vacío
    progress_container = st.empty()

    # Dentro del contenedor ponemos la barra
    my_bar = progress_container.progress(0, text=progress_text)

    for percent_complete in range(100):
        time.sleep(0.02)  # velocidad (0.02 → tarda ~2 seg)
        my_bar.progress(percent_complete + 1, text=progress_text)

    # Mensaje de listo dentro del mismo contenedor
    progress_container.success("✅ Listo!")
    time.sleep(0.8)

    # 🔥 Aquí borramos todo (barra + mensaje)
    progress_container.empty()

    # 👉 Después de esto ya renderizas tu dashboard
    # main_tabs = st.tabs([...])
    # Inicializar estado
    if "mostrar_sidebar" not in st.session_state:
        st.session_state.mostrar_sidebar = False
    
    # --- Tabs principales ---
    main_tabs = st.tabs([
        "📋 Menú  ",
        "📋 Administración  ",
        "🛒 Compras  ",
        "💰 Ventas  ",
        "🏭 Producción  ",
        "🚚 Logística  ",
        "✅ Calidad  "
    ])

    # --- MENU---

# --- Pestaña Menú ---
    with main_tabs[0]:
        # Botón menú
        if st.button("📋 Menú", key="menu_btn"):
            st.session_state.mostrar_menu = not st.session_state.get("mostrar_menu", False)

        # Si está abierto, mostrar opciones
        if st.session_state.get("mostrar_menu", False):
            mostrar_usuario_rol_logout()
            alertas.mostrar_notificaciones(st.session_state['usuario'])


    # --- ADMINISTRACIÓN ---
    with main_tabs[1]:
        sub_tabs_admin = st.tabs(["👤 Usuarios", "⚙️ Configuración", "🔔 Alertas"])

        with sub_tabs_admin[0]:
            if st.session_state['rol'] == "administrador":
                login.gestion_usuario()
                
            else:
                st.warning("No tienes permiso para ver esta sección.")

        with sub_tabs_admin[1]:
            if st.session_state['rol'] == "administrador":
                configuracion.mostrar_configuracion()
            else:
                st.warning("No tienes permiso para ver esta sección.")

        with sub_tabs_admin[2]:
            alertas_admin.mostrar_alertas_admin()

    # --- COMPRAS ---
    with main_tabs[2]:
        sub_tabs_compras = st.tabs(["📄 Orden de Compra ", "📄 Orden de Servicio ", "📦 Recepción "])

        with sub_tabs_compras[0]:
            orden_general.mostrar_modulo_compras()

        with sub_tabs_compras[1]:
            orden_servicios.mostrar_modulo_servicios()

        with sub_tabs_compras[2]:
            orden_general.mostrar_recepcion_materiales()



    # --- VENTAS ---
    with main_tabs[3]:
        sub_tabs_ventas = st.tabs(["📄 Cotizaciones ", "📄 Órdenes de Venta ", "🚚 Despachos "])

        with sub_tabs_ventas[0]:
            d_ventas.mostrar_cotizaciones()

        with sub_tabs_ventas[1]:
            d_ventas.mostrar_ordenes_venta()

        with sub_tabs_ventas[2]:
            d_ventas.mostrar_despachos()

    # --- PRODUCCIÓN ---
    with main_tabs[4]:
        sub_tabs_produccion = st.tabs([
            "➕ Crear OP ", "⚙️ Etapas ", "📊 Control de Producción ",
            "🗺️ VSM ", "🧹 5S ", "SMED ", "🔧 TPM  ", "🔍 Trazabilidad "
        ])

        with sub_tabs_produccion[0]:
            if st.session_state['rol'] in ["administrador", "planificador"]:
                produccion_crear_op.crear_op()

        with sub_tabs_produccion[1]:
            produccion_etapas.modulo_etapas()

        with sub_tabs_produccion[2]:
            produccion.tablero_kanban()
            produccion.visualizar_trazabilidad_sankey()

        with sub_tabs_produccion[3]:
            produccion_vsm.mostrar_vsm()
          

        with sub_tabs_produccion[4]:
            produccion_5s.mostrar_5s()

        with sub_tabs_produccion[5]:
            produccion_smed.smed_app()
        
        with sub_tabs_produccion[6]:
            produccion_tpm.mostrar_tpm()

        with sub_tabs_produccion[7]:
            produccion_trazabilidad.mostrar_trazabilidad()

    # --- LOGÍSTICA ---
    with main_tabs[5]:
        sub_tabs_logistica = st.tabs(["📐 Layout ", "🚛 Distribución ", "📦 Inventario "])

        with sub_tabs_logistica[0]:
            logistica_planos.mostrar_visor_glb()

        with sub_tabs_logistica[1]:
            logistica.mostrar_distribucion()

        with sub_tabs_logistica[2]:
            mostrar_gestion_inventario()

    # --- CALIDAD ---
    with main_tabs[6]:
        sub_tabs_calidad = st.tabs(["✅ Inspección ", "📋 No Conformidades ", "📈 Análisis de Defectos "])

        with sub_tabs_calidad[0]:
            q_calidad.mostrar_calidad()

        with sub_tabs_calidad[1]:
            q_calidad.no_conformidades()

        with sub_tabs_calidad[2]:
            q_calidad.analisis_defectos()