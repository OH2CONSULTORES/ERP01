import streamlit as st
import pandas as pd
import json, os
from datetime import date

HISTORIAL_FILE = "historial_cotizaciones.json"
CLIENTES_FILE = "clientes.json"

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_historial(historial):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


# --- Funciones para cargar y guardar clientes ---
def cargar_clientes():
    if os.path.exists(CLIENTES_FILE):
        with open(CLIENTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_clientes(clientes):
    with open(CLIENTES_FILE, "w", encoding="utf-8") as f:
        json.dump(clientes, f, ensure_ascii=False, indent=2)

# --- Cargar clientes ---
clientes = cargar_clientes()
nombres_clientes = [cliente["nombre"] for cliente in clientes]



# =====================
# DATA BASE
# =====================
detalle_costos = ["DISEÑO","PRUEBA DE COLOR","PLACAS","IMPRESIÓN",
    "MATERIAL 1:","COSTO CONVERSION:", "CORTE RESMAS A PLIEGO", "PLASTICO MATE RETIRA","0",
    "0","PELICULA RECUBRIMIENTO","MANTILLA RECUBRIIENTO:","TROQUEL","TROQUELADO 1","TROQUELADO 2",
    "CITOS","HOT STAMPING","CLICHÉ HOT STAMPING","PELICULA HOT STAMPING","REPUJADO","CLICHÉ REPUJADO",
    "PELICULA REPUJADO","MANUALIDAD 1:","MANUALIDAD 2:","ASA DE BOLSA", "EMPAQUETADO",
    "DESGLOCE","CONTRAPLACADO","MOVILIDAD INTERNA","DELIVERY","SUB TOTAL","COSTOS FIJOS",
    "COMISION VENTA","COSTO TOTAL","UTILIDAD","COSTO FINAL VENTA","COSTO FINAL INCLUIDO IGV",
    "COSTO UNIT.","TIRAJE DE IMPRESION","PRECIO MINIMO","HOJAS DE RESMAS A UTILIZAR",
    "CANTIDAD MINIMA DE PLIEGOS"
]

base_data = {
    "DISEÑO": {
        "YA EXISTE": 0,
        "NUEVO SIMPLE": 20,
        "NUEVO MEDIO": 50,
        "NUEVO ESPECIAL": 90
    },

    "PRUEBA DE COLOR": {
        "0": 0,
        "DIGITAL A4": 20,
        "DIGITAL A3": 40,
        "OFFSET 50X35": 90,
        "OFFSET 50X70": 140,
        "OFFSET 70X100": 350
    },


    "IMPRESIÓN": {
        "MAQUINA": [ "GTOZ(50X35CM 1 Y 2 COLORES)",
            "KOMORI(35X50 CM)","KOMORI(50X70 CM)",
            "CD(70X100CM)", "SORSZ(70X100CM 1 Y 2 COLORES)",
            "0"
        ],
        "COLORES DE IMPRESION": [
            "1", "2", "1T/1R", "3", "4", "4S", "2T/2R",
            "5", "4ST/1R", "6", "4ST/2R", "3T/3R", "4ST/4SR"
        ],
        "PLACAS": [
            1, 2, 2, 3, 4, 4, 4,
            5, 5, 6, 6, 6, 8
        ],
        "DATOS_TABLA": {
            "MAQUINA DE IMPRESIÓN": ["1", "2", "1T/1R", "3", "4", "4S", "2T/2R",
            "5", "4ST/1R", "6", "4ST/2R", "3T/3R", "4ST/4SR"],
            "CANTIDAD DE PLACAS": [1, 2, 2, 3, 4, 4, 4, 5, 5, 6, 6, 6, 8],
            "GTOZ(50X35CM 1 Y 2 COLORES)": [25, 50, 50, 75, 100, 50, 100, 125, 75, 150, 100, 150, 100],
            "KOMORI(35X50 CM)": [35, 70, 70, 105, 140, 70, 140, 175, 105, 210, 140, 210, 140],
            "KOMORI(50X70 CM)": [60, 120, 120, 180, 240, 90, 240, 300, 150, 360, 210, 360, 180],
            "CD(70X100CM)": [220, 440, 440, 660, 880, 250, 880, 1100, 470, 1320, 690, 1320, 500],
            "SORSZ(70X100CM 1 Y 2 COLORES)": [120, 240, 240, 360, 480, 300, 480, 600, 420, 720, 540, 720, 600],
            "MEDIDA DE PLACAS": [
                "51X40 PINZA 3 CM", "74.5X60.5 PINZA 6CM", "74.5X60.5 PINZA 6CM",
                "79X103 PINZA 5 CM", "79X103 PINZA 5 CM", "", "", "", "", "", "", "", ""
            ],
            "PRECIO DE PLACAS": [8.75, 15, 15, 25, 30, 0, 0, 0, 0, 0, 0, 0, 0]
        }
    },


    "SERIGRAFIA": {
        "CANTIDAD DE PLACAS": [1, 2, 2, 3, 4, 4, 4, 5, 5, 6, 6, 6, 8],
        "SERIGRAFIA 50X35": [140, 280, 280, 420, 560, 560, 560, 700, 700, 840, 840, 840, 1120],
        "SERIGRAFIA 50X70 CM": [220, 440, 440, 660, 880, 880, 880, 1100, 1100, 1320, 1320, 1320, 1760],
        "SERIGRAFIA 70X100 CM": [300, 600, 600, 900, 1200, 1200, 1200, 1500, 1500, 1800, 1800, 1800, 2400],
        "0": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    },


    "MAQUINA DE TROQUELADO": {
        "HEIDELBERG 40X57 CM": 25,
        "HEIDELBERG 57X82 CM.": 25,
        "MAQUINA DE LIBRO 70X100 CM.TROQUEL GRANDE": 100,
        "MAQUINA DE LIBRO 70X100 CM.TROQUEL MEDIANO-REPUJADO": 70,
        "MAQUINA DE LIBRO 70X100 CM.TROQUEL CHICO": 60,
        "0": 0
    },
    "TIPO DE MANUALIDAD": {
        "PEGA LINEAL CAJA CONGELADOS": 45,
        "TRIPLE PEGA CAJA": 45,
        "ARMADO DE LONCHERA": 45,
        "FORMADORA DE CAJAS": 25,
        "ARMADO DE CAJAS ESPECIALES": 120,
        "PEGADO DE BOLSA 1 PARTE": 350,
        "PEGADO DE CONO": 45,
        "PEGADO DE 1 CUERPO + CONTRAPLACADO DE 2 ASAS INCLUYE COLA": 252.5,
        "PEGADO DE MICA": 25,
        "0": 0
    },
    "CLICHÉ": {
        "0": 0,
        "MINIMO (5X5 CM)": 30,
        "X DIMENSION": "#¡REF!"
    },
    "PELICULA": {
        "0": 0,
        "MINIMO": 14.16,
        "X DIMENSION": "#¡REF!"
    },
    "DESGLOCE": {
        "0": 0,
        "SIMPLE": 5,
        "1 MILLAR X HORA, 1 PERSONA": 9,
        "1 MILLAR X HORA, 2 PERSONA": 18,
        "I MILLAR X HORA, 3 PERSONAS": 27
    },
    "REFUERZOS DE BOLSA": {
        "0": 0,
        "SOLO BASE": 90,
        "BASE Y LATERALES": 120
    },
    "EMPAQUETADO": {
        "PAQUETE DE 400(2 HOJAS X PLIEGO)": 3,
        "MITAD DE PAPEL PAQUETE X 300": 9,
        "MITAD DE PAPEL PAQUETE X 500": 10,
        "LONCHERAS ARMADAS EN CAJAS": 30,
        "LONCHERAS EMPAQUETADAS EN PAPEL": 22,
        "BANDEJAS ARMADAS EMPAQUETADAS EN PAPEL": 5,
        "0": 0
    },

    "TROQUEL": {
        "0": 0,
        "YA EXISTE": 20,
        "MINIMO": 15,
        "NUEVO MEDIANO": 50,
        "NUEVO GRANDE": 120,
        "AGREGA PRECIO MANUALMENTE": 20
    },    
    "MOVILIDAD INTERNA": {
        "0": 0,
        "MOVILIDAD INTERNA CERCA": 25,
        "MOVILIDAD INTERNA LEJOS": 50
    },
    "ASA DE BOLSA": {
        "0": 0,
        "ASA DE PAPEL TWIST": 200,
        "ASA TROQUELADA": 35,
        "ASA DRIZA DELGADA": 94,
        "ASA DRIZA GRUESA": 133,
        "ASA TELA SATINADA 15 MM.": 206,
        "ASA TELA SATINADA 20 MM.": 224,
        "ASA YUTE DELGADA": 76,
        "ASA YUTE GRUESA": 94
    },
    "CLICHÉ COTIZADOR 2": {
        "0": 0,
        "MINIMO (5X5 CM)": 30,
        "X DIMENSION": "#¡REF!"
    },
    "PELICULA COTIZADOR 2": {
        "0": 0,
        "MINIMO": 14.16,
        "X DIMENSION": "#¡REF!"
    },
    "TROQUEL COTIZADOR 2": {
        "0": 0,
        "YA EXISTE": 20,
        "MINIMO": 15,
        "NUEVO MEDIANO": 50,
        "NUEVO GRANDE": 120,
        "AGREGA PRECIO MANUALMENTE": "#¡REF!"
    },
    "DELIVERY": {
        "0": 0,
        "SIMPLE 1 ENTREGA": 25,
        "2 ENTREGAS": 50,
        "3 ENTREGAS": 75,
        "4 ENTREGAS": 100,
        "CAMION PEQUEÑO H100 2 TONELADAS": 250,
        "CAMION MEDIANO H300 5 TONELADAS": 350
    },
    "IMPRESION LASER": {
        "0": 0,
        "A4 (21X29.7 CM.)INCLUYE MATERIAL(COUCHE HASTA 300 GRS -ADHESIVO P3-RB C-14)": 1000,
        "A3 (29.7X42 CM.)INCLUYE MATERIAL(COUCHE HASTA 300 GRS -ADHESIVO P3-RB C-14)": 2000,
        "A4 (21X29.7 CM.)SIN MATERIAL": 800,
        "A3 (29.7X42 CM.)SIN MATERIAL": 1600
    },
    "IMPRESION PLOTER": {
        "0": 0,
        "146X100 CM.VINYL ADHESIVO ARCLAD (IMPRESION + LAMINADO + TROQUELADO)": 50000,
        "146X100 CM.VINYL ADHESIVO ARCLAD (IMPRESION + TROQUELADO)": 4200,
        "146X100 CM. VINYL ADHESIVO ARCLAD(IMPRESION + LAMINADO)": 3400
    },
    "CONTRAPLACADO": {
        "0": 0,
        "50X35 CM": 200,
        "33.3X70 CM.": 240,
        "50X70 CM.": 70,
        "70X100 CM.": 700
    }

}


# --- Función principal para mostrar el cotizador ---
def mostrar_cotizador():
    cotizacion_editando = st.session_state.get("cotizacion_editar", None)
    col_form, col_tabla = st.columns([2,1])

    with col_form:
        st.subheader("N° 0 : Datos principales")

        # --- Layout en tres columnas ---
        # --- Layout principal en tres columnas ---
        col1, col2, col3 = st.columns([1, 2, 1])

        # =========================
        # Columna 1 - Número de cotización
        # =========================
        with col1:
            if cotizacion_editando:
                cotizacion_num = st.text_input("Número de cotización", value=cotizacion_editando["numero"])
            else:
                cotizacion_num = st.text_input(
                    "Número de cotización", 
                    value=f"COT-{len(cargar_historial())+1:04}"
                )

        # =========================
        # Columna 2 - Seleccionar cliente
        # =========================
        with col2:
            clientes = cargar_clientes()
            nombres_clientes = [c["nombre"] for c in clientes]

            cliente_seleccionado = st.selectbox(
                "Selecciona un cliente",
                nombres_clientes,
                index=nombres_clientes.index(cotizacion_editando["cliente"]) if cotizacion_editando else 0
            )

        # =========================
        # Columna 3 - Botón Agregar cliente
        # =========================
        with col3:
            mostrar_agregar_cliente = st.checkbox("➕ Agregar cliente", )

        # =========================
        # Sección para agregar cliente (debajo de todo)
        # =========================
        if mostrar_agregar_cliente:
            st.markdown("###### ➕ Agregar cliente")
            col_a, col_b, col_c = st.columns(3)  # Ahora tenemos 3 columnas

            with col_a:
                nuevo_nombre = st.text_input("Nombre del Cliente")
                nuevo_ruc = st.text_input("RUC", key="ruc_cliente")

            with col_b:
                nuevo_contacto = st.text_input("Contacto", key="Contacto_cliente")
                nueva_direccion = st.text_input("Dirección", key="direccion_cliente")

            with col_c:
                nuevo_telefono = st.text_input("Teléfono", key="Telefono_cliente")

            if st.button("💾 Guardar Cliente"):
                if nuevo_nombre:
                    nuevo_cliente = {
                        "nombre": nuevo_nombre,
                        "direccion": nueva_direccion,
                        "ruc": nuevo_ruc,
                        "telefono": nuevo_telefono,
                        "contacto": nuevo_contacto
                    }
                    clientes.append(nuevo_cliente)
                    guardar_clientes(clientes)
                    st.success(f"✅ Cliente '{nuevo_nombre}' agregado correctamente.")
                    st.rerun()
                else:
                    st.error("❌ El nombre del cliente es obligatorio.")

        # Cliente final seleccionado
        cliente = cliente_seleccionado


        # Tres columnas para: Descripción | Fecha | Cantidad
        col1, col2, col3 = st.columns(3)

        with col1:
            descripcion = st.text_input(
                "Descripción",
                value=cotizacion_editando["descripcion"] if cotizacion_editando else ""
            )

        with col2:
            fecha = st.date_input(
                "Fecha",
                value=date.fromisoformat(cotizacion_editando["fecha"]) if cotizacion_editando else date.today()
            )

        with col3:
            cantidad = st.number_input(
                "Cantidad",
                value=cotizacion_editando["cantidad"] if cotizacion_editando else 0,
                step=1,
                min_value=0
            )






        # Campos nuevos antes de DISEÑO
        col1, col2 = st.columns(2)

        with col1:
            acabados = st.text_input("Acabados", value="")
            material = st.text_input("Material", value="")

        with col2:
            recubrimientos = st.text_input("Recubrimientos", value="")
            maquina_tipo_impresion = st.text_input("Máquina y tipo de impresión", value="")


        st.subheader("N° 1 :  Diseño")

        # Solo las filas que queremos
        detalles_permitidos = ["DISEÑO", "PRUEBA DE COLOR"]

        df = pd.DataFrame({
            "DETALLE DE COSTOS": detalles_permitidos,
            "OPCIÓN": ["" for _ in detalles_permitidos],
            "PRECIO": [0 for _ in detalles_permitidos]
        })

        # Mostrar en dos columnas
        col1, col2 = st.columns(2)

        for i, fila in enumerate(detalles_permitidos):
            opciones = base_data.get(fila)
            if not opciones:
                continue

            opciones_lista = list(opciones.keys())

            default_idx = 0
            if cotizacion_editando:
                try:
                    previa = cotizacion_editando["tabla"][i]["OPCIÓN"]
                    if previa in opciones_lista:
                        default_idx = opciones_lista.index(previa)
                except Exception:
                    default_idx = 0

            # Seleccionar columna donde mostrar cada campo
            with (col1 if i == 0 else col2):
                opcion_sel = st.selectbox(
                    label=fila,
                    options=opciones_lista,
                    index=default_idx,
                    key=f"sel_{fila.replace(' ', '_')}"
                )

            precio_sel = opciones[opcion_sel]
            df.loc[i, "OPCIÓN"] = opcion_sel
            df.loc[i, "PRECIO"] = precio_sel


        st.subheader("N° 2 :  Impresión")

        # ---------------- FUNCIÓN BUSCARV ----------------
        # --- Obtener listas ---
        maquinas = base_data["IMPRESIÓN"]["MAQUINA"]
        colores = base_data["IMPRESIÓN"]["COLORES DE IMPRESION"]
        placas_lista = sorted(set(base_data["IMPRESIÓN"]["DATOS_TABLA"]["CANTIDAD DE PLACAS"]))

        # --- Layout en columnas ---
        col1, col2, col3 = st.columns(3)

        with col1:
            maquina_sel = st.selectbox("MAQUINA DE IMPRESIÓN", maquinas)

        with col2:
            color_sel = st.selectbox("COLORES DE IMPRESION", colores)

        with col3:
            placas_sel = st.selectbox("PLACAS", placas_lista)

        # --- Funciones BUSCARV ---
        def buscar_precio_impresion(maquina, color):
            tabla = base_data["IMPRESIÓN"]["DATOS_TABLA"]
            if color in tabla["MAQUINA DE IMPRESIÓN"]:
                idx = tabla["MAQUINA DE IMPRESIÓN"].index(color)
                return tabla[maquina][idx]
            return 0

        def buscar_precio_placas(color):
            tabla = base_data["IMPRESIÓN"]["DATOS_TABLA"]
            if color in tabla["MAQUINA DE IMPRESIÓN"]:
                idx = tabla["MAQUINA DE IMPRESIÓN"].index(color)
                return tabla["PRECIO DE PLACAS"][idx]
            return 0

        # --- Cálculos ---
        precio_impresion = buscar_precio_impresion(maquina_sel, color_sel)
        precio_placas = buscar_precio_placas(color_sel)

        # --- Mostrar resultados ---
        df = pd.DataFrame([{
            "DETALLE": "IMPRESIÓN",
            "MAQUINA": maquina_sel,
            "COLORES": color_sel,
            "PLACAS": placas_sel,
            "PRECIO_IMPRESION": precio_impresion,
            "PRECIO_PLACAS": precio_placas
        }])

        st.dataframe(df, use_container_width=True)




        st.subheader("N° 3 :  Armado de Producto y Material")# =====================================================================================================================================

        # Datos de ejemplo para MATERIAL (por ahora vacío, luego puedes llenarlo)
        materiales = []

        # --- Layout en 4 columnas ---
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # PRODUCTO X PLIEGO (manual)
            producto_x_pliego = st.number_input("PRODUCTO X PLIEGO", min_value=1, value=1, step=1)

            # Cantidad total (para el cálculo)
            cantidad_total = st.number_input("CANTIDAD TOTAL", min_value=1, value=100, step=1)

            # CANT. DE PLIEGOS REQ (automático)
            cant_pliegos_req = cantidad_total / producto_x_pliego if producto_x_pliego > 0 else 0
            st.number_input("CANT. DE PLIEGOS REQ", value=round(cant_pliegos_req, 2), disabled=True)

        with col2:
            # PLIEGOS DEMASIA (manual)
            pliegos_demasia = st.number_input("PLIEGOS DEMASIA", min_value=0, value=0, step=1)

            # TOTAL PLIEGOS A IMPRIMIR (automático)
            total_pliegos = cant_pliegos_req + pliegos_demasia
            st.number_input("TOTAL PLIEGOS A IMPRIMIR", value=round(total_pliegos, 2), disabled=True)

            # MATERIAL (pendiente)
            material_sel = st.selectbox("MATERIAL", materiales)

        with col3:
            # DETALLE DE CONVERSIÓN (manual)
            detalle_conversion = st.text_input("DETALLE DE CONVERSIÓN")

            pliegos_x_hoja = st.number_input("PLIEGOS X HOJA", min_value=0.0, value=0.0, step=0.01)
            hojas_resma_utilizar = st.number_input("HOJAS DE RESMA A UTILIZAR", min_value=0.0, value=0.0, step=0.01)


        with col4:
            largo_pliego = st.number_input("LARGO PLIEGO", min_value=0.0, value=0.0, step=0.01)
            ancho_pliego = st.number_input("ANCHO PLIEGO", min_value=0.0, value=0.0, step=0.01)
            medida_corte = st.text_input("MEDIDA DE CORTE")
            costo_conversion = st.number_input("COSTO CONVERSIÓN", min_value=0.0, value=0.0, step=0.01)



        st.subheader("---------------------CALCULO DE MEDIDA ESPECIAL EN BOBINA---------------------")# ======================================================================================================================================


        # --- Layout en 4 columnas ---
        col1, col2, col3, col4 = st.columns(4)


        with col1:
            precio_kg = st.number_input("PRECIO KG.", min_value=0.0, value=0.0, step=0.01)
            gramaje = st.number_input("GRAMAJE", min_value=0.0, value=0.0, step=0.01)


        with col2:
            ancho_bobina = st.number_input("ANCHO BOBINA", min_value=0.0, value=0.0, step=0.01)
            largo_bobina = st.number_input("LARGO", min_value=0.0, value=0.0, step=0.01)


        with col3:
            paq = st.number_input("PAQ.", min_value=0.0, value=0.0, step=0.01)

            # METROS PARA ESTE TRABAJO = Hojas de resma a utilizar (de bloque anterior)
            metros_trabajo = hojas_resma_utilizar
            st.number_input("METROS PARA ESTE TRABAJO", value=round(metros_trabajo, 2), disabled=True)


        with col4:
            # PRECIO DE RESMA SIN IGV = precio_kg × gramaje × ancho_bobina × largo_bobina × paq
            precio_resma_sin_igv = precio_kg * gramaje * ancho_bobina * largo_bobina * paq
            st.number_input("PRECIO DE RESMA SIN IGV", value=round(precio_resma_sin_igv, 2), disabled=True)

            # KILOS PARA ESTE TRABAJO = gramaje × ancho_bobina × largo_bobina
            kilos_trabajo = gramaje * ancho_bobina * largo_bobina
            st.number_input("KILOS PARA ESTE TRABAJO", value=round(kilos_trabajo, 2), disabled=True)


        st.subheader("N° 4 :  Recubrimientos")# =====================================================================================================================================
        
        # --- Tres columnas para recubrimientos, bobina y mantilla ---
        col1, col2, col3 = st.columns(3)

        # ------------------- COLUMNA 1 -------------------
        with col1:
            recubrimiento1 = st.text_input("RECUBRIMIENTO 1")
            recubrimiento2 = st.text_input("RECUBRIMIENTO 2")
            recubrimiento3 = st.text_input("RECUBRIMIENTO 3")
            # 💡 Para cambiar a lista desplegable desde base_data:
            # recubrimiento1 = st.selectbox("RECUBRIMIENTO 1", base_data["recubrimiento1"])
            # recubrimiento2 = st.selectbox("RECUBRIMIENTO 2", base_data["recubrimiento2"])
            # recubrimiento3 = st.selectbox("RECUBRIMIENTO 3", base_data["recubrimiento3"])

        # ------------------- COLUMNA 2 -------------------
        with col2:
            bobina_plastico = st.text_input("BOBINA DE PLASTICO A USAR")
            dimension_total = st.text_input("DIMENSION TOTAL A UTILIZAR CM.")
            costo_pelicula = st.number_input("COSTO PELICULA", min_value=0.0, step=0.01)
            # 💡 Para usar lista desplegable desde base_data:
            # bobina_plastico = st.selectbox("BOBINA DE PLASTICO A USAR", base_data["bobinas"])
            # dimension_total = st.selectbox("DIMENSION TOTAL A UTILIZAR CM.", base_data["dimensiones"])
            # costo_pelicula = st.selectbox("COSTO PELICULA", base_data["costos_pelicula"])

        # ------------------- COLUMNA 3 -------------------
        with col3:
            costo_mantilla = st.number_input("COSTO MANTILLA", min_value=0.0, step=0.01)
            dime_recubrimiento = st.text_input("DIME. RECUBRIMIENTO")
            metros_usar = st.number_input("METROS A USAR", min_value=0.0, step=0.01)
            costo_consumo = st.number_input("COSTO X CONSUMO", min_value=0.0, step=0.01)
            # 💡 Para usar lista desplegable desde base_data:
            # costo_mantilla = st.selectbox("COSTO MANTILLA", base_data["mantillas"])
            # dime_recubrimiento = st.selectbox("DIME. RECUBRIMIENTO", base_data["dimensiones_recubrimiento"])
            # metros_usar = st.selectbox("METROS A USAR", base_data["metros"])
            # costo_consumo = st.selectbox("COSTO X CONSUMO", base_data["costos_consumo"])       
            
    
        st.subheader("N° 5 :  Troquel y Troquelado")# =====================================================================================================================================
        

        # --- Cuatro columnas para troquelados y costos ---
        col1, col2, col3, col4 = st.columns(4)

        # ------------------- COLUMNA 1 -------------------
        with col1:
            troquelado1 = st.text_input("TROQUELADO 1")
            # 💡 Si quieres lista desplegable desde base_data:
            # troquelado1 = st.selectbox("TROQUELADO 1", base_data["troquelado1"])

        # ------------------- COLUMNA 2 -------------------
        with col2:
            costo_troquel = st.number_input("COSTO TROQUEL", min_value=0.0, step=0.01)
            # 💡 Si este valor es autocalculado (ej: según troquelado1), 
            #     puedes usar una fórmula:
            # costo_troquel = calcular_costo_troquel(troquelado1)

        # ------------------- COLUMNA 3 -------------------
        with col3:
            troquelado2 = st.text_input("TROQUELADO 2")
            # 💡 Si quieres lista desplegable:
            # troquelado2 = st.selectbox("TROQUELADO 2", base_data["troquelado2"])

        # ------------------- COLUMNA 4 -------------------
        with col4:
            citos = st.number_input("CITOS", min_value=0.0, step=0.01)
            # 💡 Si este valor es autocalculado (ej: multiplicación, suma o fórmula):
            # citos = calcular_citos(troquelado2)

        
        st.subheader("N° 6 :  Repujado y Hot Stamping")# =====================================================================================================================================

        # --- Tres columnas para Hot Stamping y Repujado ---
        col1, col2, col3 = st.columns(3)

        # ------------------- COLUMNA 1 -------------------
        with col1:
            costo_millar_hot = st.number_input("COSTO X MILLAR HOT STAMPING", min_value=0.0, step=0.01)
            # 💡 Si es autocalculado desde base_data:
            # costo_millar_hot = calcular_costo_hot(base_data["hot_stamping"])

            costo_millar_rep = st.number_input("COSTO X MILLAR REPUJADO", min_value=0.0, step=0.01)
            # 💡 Si es autocalculado:
            # costo_millar_rep = calcular_costo_repujado(base_data["repujado"])

        # ------------------- COLUMNA 2 -------------------
        with col2:
            costo_pelicula_hot = st.number_input("COSTO PELICULA HOT STAMPING", min_value=0.0, step=0.01)
            # 💡 Para lista desplegable:
            # costo_pelicula_hot = st.selectbox("COSTO PELICULA HOT STAMPING", base_data["pelicula_hot"])

            costo_pelicula_rep = st.number_input("COSTO PELICULA REPUJADO", min_value=0.0, step=0.01)
            # 💡 Para lista desplegable:
            # costo_pelicula_rep = st.selectbox("COSTO PELICULA REPUJADO", base_data["pelicula_repujado"])

        # ------------------- COLUMNA 3 -------------------
        with col3:
            costo_cliche_hot = st.number_input("COSTO CLICHÉ HOT STAMPING", min_value=0.0, step=0.01)
            # 💡 Si es autocalculado:
            # costo_cliche_hot = calcular_cliche_hot(base_data["hot_stamping"])

            costo_cliche_rep = st.number_input("COSTO CLICHÉ REPUJADO", min_value=0.0, step=0.01)
            # 💡 Si es autocalculado:
            # costo_cliche_rep = calcular_cliche_repujado(base_data["repujado"])



        st.subheader("N° 7 :  Desglose Manualidad y Empaquetado ")# =====================================================================================================================================


        # --- Tres columnas para Manualidades y otros ---
        col1, col2, col3 = st.columns(3)

        # ------------------- COLUMNA 1 -------------------
        with col1:
            manualidad_1 = st.number_input("MANUALIDAD 1", min_value=0.0, step=0.01)
            # 💡 Si es autocalculado:
            # manualidad_1 = calcular_manualidad1(base_data["manualidad"])

            manualidad_2 = st.number_input("MANUALIDAD 2", min_value=0.0, step=0.01)
            # 💡 Si es autocalculado:
            # manualidad_2 = calcular_manualidad2(base_data["manualidad"])

        # ------------------- COLUMNA 2 -------------------
        with col2:
            empaquetado = st.number_input("EMPAQUETADO", min_value=0.0, step=0.01)
            # 💡 Lista desplegable:
            # empaquetado = st.selectbox("EMPAQUETADO", base_data["empaquetado"])

            desgloce = st.number_input("DESGLOCE", min_value=0.0, step=0.01)
            # 💡 Lista desplegable:
            # desgloce = st.selectbox("DESGLOCE", base_data["desgloce"])

        # ------------------- COLUMNA 3 -------------------
        with col3:
            asa_bolsa = st.number_input("ASAS DE BOLSA", min_value=0.0, step=0.01)
            # 💡 Lista desplegable:
            # asa_bolsa = st.selectbox("ASA DE BOLSA", base_data["asa_bolsa"])

            
            contraplacado_opciones = list(base_data["CONTRAPLACADO"].keys())

            # 2️⃣ Selectbox para elegir la opción
            contraplacado_opcion = st.selectbox(
                "CONTRAPLACADO",
                contraplacado_opciones,
                index=0,
                # Esto muestra el nombre + precio en la lista
                format_func=lambda k: f"{k} — S/ {base_data['CONTRAPLACADO'][k]}"
            )

            # 3️⃣ Precio de la opción seleccionada
            contraplacado_precio = base_data["CONTRAPLACADO"][contraplacado_opcion]


# ==========================================================================================================================================






        st.subheader("N° 8 :  Delivery")

        
        # --- Dos columnas para Movilidad Interna y Delivery ---
        col1, col2 = st.columns(2)

        # ------------------- COLUMNA 1 -------------------
        with col1:
            # 💡 Lista desplegable:
            # movilidad_interna = st.selectbox("MOVILIDAD INTERNA", base_data["movilidad_interna"])
            # 💡 Autocalculado:
            # movilidad_interna = calcular_movilidad(base_data["movilidad"])
            movilidad_interna = list(base_data["MOVILIDAD INTERNA"].keys())

            movilidad_opcion = st.selectbox(
                "MOVILIDAD INTERNA",
                movilidad_interna,
                index=0,
                # Esto solo es visual, para mostrar el precio al lado:
                format_func=lambda k: f"{k} — S/ {base_data['MOVILIDAD INTERNA'][k]}"
            )

            movilidad_precio = base_data["MOVILIDAD INTERNA"][movilidad_opcion]






        # ------------------- COLUMNA 2 -------------------
        with col2:
            #delivery = st.selectbox("DELIVERY", base_data["DELIVERY"])
            # 💡 Lista desplegable:
            # delivery = st.selectbox("DELIVERY", base_data["delivery"])
            # 💡 Autocalculado:
            # delivery = calcular_delivery(base_data["delivery"])
            opciones_delivery = list(base_data["DELIVERY"].keys())

            delivery_opcion = st.selectbox(
                "DELIVERY",
                opciones_delivery,
                index=0,
                # Esto solo es visual, para mostrar el precio al lado:
                format_func=lambda k: f"{k} — S/ {base_data['DELIVERY'][k]}"
            )

            delivery_precio = base_data["DELIVERY"][delivery_opcion]







# ==========================================================================================================================================

        if st.button("💾 Guardar Cotización"):
            nueva_cot = {
                "numero": cotizacion_num,
                "cliente": cliente,
                "fecha": str(fecha),
                "descripcion": descripcion,
                "cantidades": cantidad,
                "acabados": acabados,
                "recubrimientos": recubrimientos,
                "material": material,
                "maquina_tipo_impresion": maquina_tipo_impresion,
                "tabla": df.to_dict(orient="records")
            }
            historial = cargar_historial()
            if cotizacion_editando:
                historial = [nueva_cot if c["numero"] == cotizacion_num else c for c in historial]
                st.session_state.pop("cotizacion_editar")
            else:
                historial.append(nueva_cot)

            guardar_historial(historial)
            st.success("Cotización guardada correctamente ✅")
            st.rerun()

# ==================================================================================================================================================

    with col_tabla:
        # Lista de conceptos (filas de la tabla)
        conceptos = [
            "CANTIDAD",
            "DISEÑO",
            "PRUEBA DE COLOR",
            "PLACAS",
            "IMPRESIÓN",
            "MATERIAL 1:",
            "COSTO CONVERSION:",
            "CORTE RESMAS A PLIEGO",
            "BARNIZ UV SECTORIZADO TIRA",
            "0",
            "0",
            "PELICULA RECUBRIMIENTO",
            "MANTILLA RECUBRIIENTO:",
            "TROQUEL",
            "TROQUELADO 1",
            "TROQUELADO 2",
            "CITOS",
            "HOT STAMPING",
            "CLICHÉ HOT STAMPING",
            "PELICULA HOT STAMPING",
            "REPUJADO",
            "CLICHÉ REPUJADO",
            "PELICULA REPUJADO",
            "MANUALIDAD 1:",
            "MANUALIDAD 2:",
            "ASA DE BOLSA",
            "EMPAQUETADO",
            "DESGLOCE",
            "CONTRAPLACADO",
            "MOVILIDAD INTERNA",
            "DELIVERY",
            "SUB TOTAL",
            "COSTOS FIJOS",
            "COMISION VENTA",
            "COSTO TOTAL",
            "UTILIDAD",
            "COSTO FINAL VENTA",
            "COSTO FINAL INCLUIDO IGV",
            "COSTO UNIT.",
            "TIRAJE DE IMPRESION",
            "PRECIO MINIMO",
            "HOJAS DE RESMAS A UTILIZAR",
            "CANTIDAD MINIMA DE PLIEGOS"
        ]

# ==========================================================================================================================================
# ==========================================================================================================================================
# ==========================================================================================================================================

        # Asegurar que existe la tabla (tal como ya lo haces)
        if "tabla_cantidades" not in st.session_state:
            st.session_state.tabla_cantidades = pd.DataFrame(
                {"Concepto": conceptos, "Cantidad 1": [0]*len(conceptos)}
            )



        try:
            # Buscar la fila "CONTRAPLACADO" en la tabla
            idx_contrap = st.session_state.tabla_cantidades.index[
                st.session_state.tabla_cantidades["Concepto"] == "CONTRAPLACADO"
            ][0]
            # Reemplazar su valor con el precio elegido
            st.session_state.tabla_cantidades.at[idx_contrap, "Cantidad 1"] = contraplacado_precio

        except IndexError:
            # Si "CONTRAPLACADO" no existe en la lista de conceptos, no hacer nada
            pass




        try:
            idx_movilidad = st.session_state.tabla_cantidades.index[
                st.session_state.tabla_cantidades["Concepto"] == "MOVILIDAD INTERNA"
            ][0]
            st.session_state.tabla_cantidades.at[idx_movilidad, "Cantidad 1"] = movilidad_precio
        except IndexError:
            pass  # si no existe la fila, no hacemos nada

        # Actualizar la fila DELIVERY con el precio elegido
        try:
            idx_delivery = st.session_state.tabla_cantidades.index[
                st.session_state.tabla_cantidades["Concepto"] == "DELIVERY"
            ][0]
            st.session_state.tabla_cantidades.at[idx_delivery, "Cantidad 1"] = delivery_precio
        except IndexError:
            # Por si la fila "DELIVERY" no estuviera en la lista de conceptos
            pass




        # Estado inicial
        if "tabla_cantidades" not in st.session_state:
            st.session_state.tabla_cantidades = pd.DataFrame({"Concepto": conceptos, "Cantidad 1": [0]*len(conceptos)})
        st.subheader("-------  Costos de produccion  ------")
        # Botón para añadir una nueva columna
        if st.button("➕ Añadir columna de cantidades"):
            col_nueva = f"Cantidad {len(st.session_state.tabla_cantidades.columns)}"
            st.session_state.tabla_cantidades[col_nueva] = st.session_state.tabla_cantidades.iloc[:, 1]  # Copia de Cantidad 1

        # Mostrar tabla editable
        st.subheader("Tabla costos")
        st.session_state.tabla_cantidades = st.data_editor(
            st.session_state.tabla_cantidades,
            num_rows="dynamic",
            use_container_width=True,
         key="tabla_cantidades_ventas"
            
        )
# ==========================================================================================================================================
# ==========================================================================================================================================
# ==========================================================================================================================================

        st.subheader("Historial")
        historial = cargar_historial()
        for cot in historial:
            if st.button(f"✏️ Editar {cot['numero']}"):
                st.session_state["cotizacion_editar"] = cot
                st.rerun()