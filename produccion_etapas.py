import streamlit as st
import json
import os
import pandas as pd

# Guardar en carpeta 'data'
RUTA_ETAPAS = os.path.join("data", "etapas.json")

def cargar_etapas():
    if os.path.exists(RUTA_ETAPAS):
        with open(RUTA_ETAPAS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_etapas(etapas):
    os.makedirs("data", exist_ok=True)  # Asegura que la carpeta exista
    with open(RUTA_ETAPAS, "w", encoding="utf-8") as f:
        json.dump(etapas, f, indent=4, ensure_ascii=False)

def nombre_unico(etapas, nombre, idx_editar=None):
    for idx, etapa in enumerate(etapas):
        if etapa['nombre'].strip().lower() == nombre.strip().lower() and idx != idx_editar:
            return False
    return True

def modulo_etapas():
    st.header("🛠️ Gestión de Etapas de Producción")

    etapas = cargar_etapas()

    # -------- FORMULARIO COMPACTO PARA MÓVIL --------
    with st.expander("➕ Agregar o editar etapa (formulario clásico)"):
        with st.form("form_etapa"):
            opciones_nombres = [e['nombre'] for e in etapas]
            editar_etapa_nombre = st.selectbox("Editar etapa existente (opcional):", [""] + opciones_nombres)

            if editar_etapa_nombre:
                idx_editar = opciones_nombres.index(editar_etapa_nombre)
                etapa_actual = etapas[idx_editar]
            else:
                idx_editar = None
                etapa_actual = {}

            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre", value=etapa_actual.get('nombre',''))
                orden = st.number_input("Orden", min_value=1, value=etapa_actual.get('orden', len(etapas)+1))
                tiempo_estimado = st.number_input("Tiempo estimado (min)", min_value=0, value=etapa_actual.get('tiempo_estimado',0))
                tiempo_preparacion = st.number_input("Preparación (min)", min_value=0, value=etapa_actual.get('tiempo_preparacion',0))
            with col2:
                tiempo_mantenimiento = st.number_input("Mantenimiento (min)", min_value=0, value=etapa_actual.get('tiempo_mantenimiento',0))
                personas_asignadas = st.number_input("Personas", min_value=1, value=etapa_actual.get('personas_asignadas',1))
                horas_trabajo = st.number_input("Horas trabajo", min_value=0.0, step=0.5, value=etapa_actual.get('horas_trabajo',0.0))
                eficiencia_esperada = st.slider("Eficiencia (%)", min_value=0, max_value=100, value=etapa_actual.get('eficiencia_esperada',100))

            descripcion = st.text_area("Descripción", value=etapa_actual.get('descripcion',''), height=70)

            # Este botón DEBE estar dentro del form
            submitted = st.form_submit_button("Guardar")

            if submitted:
                if not nombre.strip():
                    st.warning("El nombre no puede estar vacío.")
                elif not nombre_unico(etapas, nombre, idx_editar):
                    st.warning("Ya existe una etapa con ese nombre.")
                else:
                    etapa_nueva = {
                        "nombre": nombre.strip(),
                        "descripcion": descripcion.strip(),
                        "orden": orden,
                        "tiempo_estimado": tiempo_estimado,
                        "tiempo_preparacion": tiempo_preparacion,
                        "tiempo_mantenimiento": tiempo_mantenimiento,
                        "personas_asignadas": personas_asignadas,
                        "horas_trabajo": horas_trabajo,
                        "eficiencia_esperada": eficiencia_esperada
                    }
                    if idx_editar is not None:
                        etapas[idx_editar] = etapa_nueva
                        st.success(f"Etapa '{nombre}' actualizada.")
                    else:
                        etapas.append(etapa_nueva)
                        st.success(f"Etapa '{nombre}' agregada.")
                    etapas.sort(key=lambda x: x['orden'])
                    guardar_etapas(etapas)
                    st.rerun()

    # -------- TABLA EDITABLE --------
    st.subheader("📝 Etapas registradas")

    df = pd.DataFrame(etapas)

    if not df.empty:
        df_edit = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key="etapas_editor"
        )
        if st.button("Guardar cambios en tabla"):
            guardar_etapas(df_edit.to_dict(orient="records"))
            st.success("Cambios guardados correctamente.")
            st.rerun()
    else:
        st.info("No hay etapas registradas. Puedes agregarlas aquí:")
        df_empty = pd.DataFrame([{
            "nombre": "",
            "descripcion": "",
            "orden": 1,
            "tiempo_estimado": 0,
            "tiempo_preparacion": 0,
            "tiempo_mantenimiento": 0,
            "personas_asignadas": 1,
            "horas_trabajo": 0.0,
            "eficiencia_esperada": 100
        }])

        df_edit = st.data_editor(
            df_empty,
            num_rows="dynamic",
            use_container_width=True,
            key="etapas_editor_nueva"
        )

        if st.button("Agregar etapas"):
            guardar_etapas(df_edit.to_dict(orient="records"))
            st.success("Etapas agregadas correctamente.")
            st.rerun()