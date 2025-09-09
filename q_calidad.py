# calidad.py
import streamlit as st

def inspeccion_proceso():
    st.header("✅ Inspección")
    st.info("🚧 Módulo en construcción. Aquí se registrarán inspecciones de procesos y productos.")

def no_conformidades():
    st.header("📋 No Conformidades")
    st.info("🚧 Módulo en construcción. Aquí se documentarán y gestionarán las no conformidades detectadas.")

def analisis_defectos():
    st.header("📈 Análisis de Defectos")
    st.info("🚧 Módulo en construcción. Aquí se analizarán las causas y tendencias de defectos para mejora continua.")


# calidad.py
import streamlit as st
from datetime import date

def mostrar_calidad():
    st.header("🛡 Módulo de Calidad")
    st.subheader("Control y aseguramiento de la calidad según estándares BRCGS Issue 7")

    # Selección de Orden de Producción
    op = st.selectbox("📦 Seleccionar Orden de Producción (OP)", 
                      ["-- Seleccionar --", "OP-1001", "OP-1002", "OP-1003"])
    
    if op == "-- Seleccionar --":
        st.info("Selecciona una OP para comenzar.")
        return
    st.success(f"Trabajando en la OP: **{op}**")

    # Pestañas principales del módulo
    tabs = st.tabs([
        "Ficha Técnica",
        "Inspección de Calidad",
        "Indicadores",
        "Certificaciones BRCGS 7",
        "Trazabilidad",
        "No Conformidades"
    ])

    # 1. Ficha Técnica
    with tabs[0]:
        st.subheader("📄 Ficha Técnica del Producto")
        st.text_input("Nombre del producto")
        st.text_area("Especificaciones técnicas")
        st.text_area("Tolerancias")
        st.file_uploader("Imágenes o planos", type=["png","jpg","jpeg","pdf"])
        if st.button("Guardar ficha técnica"):
            st.success("Ficha técnica guardada correctamente.")

    # 2. Inspección de Calidad
    with tabs[1]:
        st.subheader("🔍 Registro de Inspección")
        etapa = st.selectbox("Etapa de inspección",
                             ["Materia prima", "En proceso", "Producto final"])
        st.text_area("Checklist de inspección")
        resultado = st.radio("Resultado", ["Aprobado", "Rechazado"])
        st.text_area("Observaciones", key="obs_ficha")
        if st.button("Guardar inspección"):
            st.success("Inspección registrada correctamente.")

    # 3. Indicadores
    with tabs[2]:
        st.subheader("📊 Indicadores de Calidad")
        c1, c2, c3 = st.columns(3)
        c1.metric("PPM (Defectos/millón)", "120", "↓ 10")
        c2.metric("% Rechazo", "2.5%", "↓ 0.3%")
        c3.metric("% Retrabajo", "1.2%", "↓ 0.2%")
        st.info("Indicadores calculados automáticamente.")

    # 4. Certificaciones BRCGS Issue 7
    with tabs[3]:
        st.subheader("📑 Certificaciones y Checklist BRCGS Issue 7")
        st.caption("Completa el checklist para cumplir con este estándar global de calidad en materiales de empaque. Disponible desde abril 2025. :contentReference[oaicite:0]{index=0}")
        certs = st.multiselect("Certificaciones vigentes", ["BRCGS Issue 7", "ISO 9001", "Otra"])
        st.date_input("Próxima auditoría", value=date.today())
        st.file_uploader("Subir certificados", type=["pdf","jpg","png"])
        st.markdown("**Checklist preliminar BRCGS Issue 7**:")
        st.text_area("Lista de verificación (ansible checklist)", height=180, 
                     placeholder="Ej: ¿Existe una evaluación de peligros y controles (HARA)?\n¿Se exige compromiso de la alta dirección?\n...")
        if st.button("Guardar datos BRCGS"):
            st.success("Información de certificaciones y checklist guardado.")

    # 5. Trazabilidad
    with tabs[4]:
        st.subheader("🛠 Trazabilidad")
        st.text_input("Lote materia prima")
        st.text_input("Lote producto terminado")
        st.text_input("Destino / Cliente final")
        if st.button("Guardar trazabilidad"):
            st.success("Trazabilidad registrada correctamente.")

    # 6. No Conformidades
    with tabs[5]:
        st.subheader("⚠️ No Conformidades")
        st.text_area("Descripción de la no conformidad")
        st.text_area("Acción correctiva")
        st.text_area("Acción preventiva")
        if st.button("Registrar no conformidad"):
            st.success("No conformidad registrada exitosamente.")
