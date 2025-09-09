import os
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ============================
# Configuración general
# ============================
st.set_page_config(page_title="📘 Módulo de Estandarización de Trabajo", layout="wide")

DATA_DIR = Path("data_estandarizacion")
MEDIA_DIR = DATA_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "estandarizacion.db"

# ============================
# Funciones de base de datos
# ============================

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS procedimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            area TEXT,
            proceso TEXT,
            normativa TEXT,
            documento_path TEXT,
            video_path TEXT,
            layout_path TEXT,
            creado_en TEXT NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dop_etapas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            procedimiento_id INTEGER NOT NULL,
            etapa TEXT NOT NULL,
            secuencia INTEGER NOT NULL,
            FOREIGN KEY (procedimiento_id) REFERENCES procedimientos(id) ON DELETE CASCADE
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pasos_fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            procedimiento_id INTEGER NOT NULL,
            paso_num INTEGER NOT NULL,
            descripcion TEXT,
            image_path TEXT,
            FOREIGN KEY (procedimiento_id) REFERENCES procedimientos(id) ON DELETE CASCADE
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS capacitaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            procedimiento_id INTEGER NOT NULL,
            trabajador TEXT,
            comprension INTEGER,
            registrado_en TEXT NOT NULL,
            FOREIGN KEY (procedimiento_id) REFERENCES procedimientos(id) ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    conn.close()


init_db()

# ============================
# Utilidades
# ============================

def save_uploaded_file(uploaded_file, target_dir: Path) -> str | None:
    if not uploaded_file:
        return None
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name.replace(' ', '_')}"
    dest = target_dir / safe_name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)


def insert_procedimiento(titulo, area, proceso, normativa, documento_path, video_path, layout_path) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO procedimientos (titulo, area, proceso, normativa, documento_path, video_path, layout_path, creado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            titulo,
            area,
            proceso,
            normativa,
            documento_path,
            video_path,
            layout_path,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    proc_id = cur.lastrowid
    conn.commit()
    conn.close()
    return proc_id


def bulk_insert_dop(proc_id: int, etapas: list[str]):
    conn = get_conn()
    cur = conn.cursor()
    for i, etapa in enumerate(etapas, start=1):
        cur.execute(
            "INSERT INTO dop_etapas (procedimiento_id, etapa, secuencia) VALUES (?, ?, ?)",
            (proc_id, etapa, i),
        )
    conn.commit()
    conn.close()


def bulk_insert_pasos(proc_id: int, pasos: list[dict]):
    conn = get_conn()
    cur = conn.cursor()
    for p in pasos:
        cur.execute(
            "INSERT INTO pasos_fotos (procedimiento_id, paso_num, descripcion, image_path) VALUES (?, ?, ?, ?)",
            (proc_id, p["paso_num"], p.get("descripcion"), p.get("image_path")),
        )
    conn.commit()
    conn.close()


def insert_capacitacion(proc_id: int, trabajador: str, comprension: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO capacitaciones (procedimiento_id, trabajador, comprension, registrado_en) VALUES (?, ?, ?, ?)",
        (proc_id, trabajador, comprension, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def listar_procedimientos() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT id, titulo, area, proceso, creado_en FROM procedimientos ORDER BY id DESC",
        conn,
    )
    conn.close()
    return df


def cargar_procedimiento(proc_id: int) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM procedimientos WHERE id=?", (proc_id,))
    row = cur.fetchone()
    cols = [c[0] for c in cur.description]
    proc = dict(zip(cols, row)) if row else None

    dop = pd.read_sql_query(
        "SELECT etapa, secuencia FROM dop_etapas WHERE procedimiento_id = ? ORDER BY secuencia",
        conn,
        params=(proc_id,),
    )
    pasos = pd.read_sql_query(
        "SELECT paso_num, descripcion, image_path FROM pasos_fotos WHERE procedimiento_id = ? ORDER BY paso_num",
        conn,
        params=(proc_id,),
    )
    caps = pd.read_sql_query(
        "SELECT trabajador, comprension, registrado_en FROM capacitaciones WHERE procedimiento_id = ? ORDER BY id DESC",
        conn,
        params=(proc_id,),
    )
    conn.close()
    return {"proc": proc, "dop": dop, "pasos": pasos, "caps": caps}


# ============================
# Sidebar navegación
# ============================
st.sidebar.title("📘 Estandarización de Trabajo")
modo = st.sidebar.radio("Elige un modo", ["➕ Crear/Editar procedimiento", "📚 Historial y consulta"])  # future: editar

# ============================
# Crear/Editar procedimiento
# ============================
if modo.startswith("➕"):
    st.title("➕ Crear procedimiento estandarizado")
    st.caption("Carga documentos, video, DOP, fotos por paso y normativas. Disposición en dos columnas.")

    # Form principal para datos generales
    with st.form("form_proc", clear_on_submit=False):
        col1, col2 = st.columns([2, 1], gap="large")

        with col1:
            st.subheader("📋 Procedimiento de Trabajo")
            titulo = st.text_input("Título del procedimiento *", placeholder="Cambio de rodillos en convertidora")
            area = st.text_input("Área", placeholder="Producción")
            proceso = st.text_input("Proceso/Etapa", placeholder="Convertidora → Barnizado")

            doc = st.file_uploader("📑 Documento del procedimiento (PDF/DOCX)", type=["pdf", "docx"], key="doc")
            video = st.file_uploader("🎥 Video paso a paso (MP4)", type=["mp4"], key="vid")

            st.markdown("---")
            st.markdown("### 📝 DOP – Diagrama de Operaciones")
            etapas_txt = st.text_area(
                "Ingresa las etapas en orden (una por línea)",
                "Recepción de material\nCorte\nInspección\nEmpaque",
                height=140,
            )
            etapas_list = [e.strip() for e in etapas_txt.split("\n") if e.strip()]
            if etapas_list:
                dop_df_preview = pd.DataFrame({"Secuencia": range(1, len(etapas_list) + 1), "Etapa": etapas_list})
                st.dataframe(dop_df_preview, use_container_width=True)
                # Gráfica simple del DOP
                fig, ax = plt.subplots()
                ax.bar(dop_df_preview["Etapa"], dop_df_preview["Secuencia"])
                ax.set_ylabel("Secuencia")
                ax.set_title("Diagrama de Operaciones")
                plt.xticks(rotation=45, ha="right")
                st.pyplot(fig)

            st.markdown("---")
            st.markdown("### 📸 Fotos por paso")
            num_pasos = st.number_input("Número de pasos", min_value=1, max_value=30, value=3)
            pasos_inputs = []
            for i in range(1, num_pasos + 1):
                with st.expander(f"Paso {i}", expanded=False):
                    desc = st.text_input(f"Descripción del paso {i}", key=f"desc_{i}")
                    img = st.file_uploader(f"Imagen del paso {i} (JPG/PNG)", type=["jpg", "jpeg", "png"], key=f"img_{i}")
                    pasos_inputs.append({"paso_num": i, "desc": desc, "img": img})

        with col2:
            st.subheader("📚 Normativas y Layout")
            normativa = st.text_area("Normativa aplicable (texto libre)", height=240)
            layout_img = st.file_uploader("🏭 Layout del área (JPG/PNG)", type=["jpg", "jpeg", "png"], key="layout")

            st.markdown("---")
            st.subheader("📊 Toma de datos de capacitación")
            trabajador = st.text_input("Nombre del trabajador")
            comprension = st.slider("Nivel de comprensión del procedimiento", 0, 100, 60)
            registrar_cap = st.checkbox("Registrar evaluación al guardar", value=False)

            submitted = st.form_submit_button("💾 Guardar procedimiento")

    if submitted:
        if not titulo:
            st.error("El título es obligatorio.")
            st.stop()

        # Carpeta para el procedimiento (se crea tras insertar para conocer el ID)
        # Guardado preliminar: primero insert sin rutas, luego actualizamos con rutas correctas
        # Para simplificar, guardamos archivos en carpeta temporal y luego movemos.

        # Insert vacio para obtener ID
        proc_id = insert_procedimiento(
            titulo=titulo,
            area=area,
            proceso=proceso,
            normativa=normativa,
            documento_path=None,
            video_path=None,
            layout_path=None,
        )

        proc_dir = MEDIA_DIR / f"proc_{proc_id}"
        proc_dir.mkdir(parents=True, exist_ok=True)

        # Guardar archivos subidos
        doc_path = save_uploaded_file(doc, proc_dir)
        vid_path = save_uploaded_file(video, proc_dir)
        layout_path = save_uploaded_file(layout_img, proc_dir)

        # Actualizar rutas en la fila del procedimiento
        conn = get_conn()
        conn.execute(
            "UPDATE procedimientos SET documento_path=?, video_path=?, layout_path=? WHERE id=?",
            (doc_path, vid_path, layout_path, proc_id),
        )
        conn.commit()
        conn.close()

        # Guardar DOP
        if etapas_list:
            bulk_insert_dop(proc_id, etapas_list)

        # Guardar pasos + imágenes
        pasos_data = []
        for p in pasos_inputs:
            saved_img = save_uploaded_file(p["img"], proc_dir) if p["img"] is not None else None
            pasos_data.append(
                {
                    "paso_num": p["paso_num"],
                    "descripcion": p["desc"],
                    "image_path": saved_img,
                }
            )
        bulk_insert_pasos(proc_id, pasos_data)

        # Registrar capacitación si aplica
        if registrar_cap and trabajador and comprension is not None:
            insert_capacitacion(proc_id, trabajador, comprension)

        st.success(f"Procedimiento guardado con ID #{proc_id} ✅")
        st.toast("Guardado correctamente", icon="✅")

# ============================
# Historial y consulta
# ============================
else:
    st.title("📚 Historial y consulta de procedimientos")

    df = listar_procedimientos()
    if df.empty:
        st.info("Aún no hay procedimientos registrados.")
        st.stop()

    # Filtros
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        filtro_area = st.text_input("Filtrar por área")
    with c2:
        filtro_proceso = st.text_input("Filtrar por proceso")
    with c3:
        filtro_texto = st.text_input("Buscar en título")

    df_f = df.copy()
    if filtro_area:
        df_f = df_f[df_f["area"].str.contains(filtro_area, case=False, na=False)]
    if filtro_proceso:
        df_f = df_f[df_f["proceso"].str.contains(filtro_proceso, case=False, na=False)]
    if filtro_texto:
        df_f = df_f[df_f["titulo"].str.contains(filtro_texto, case=False, na=False)]

    st.dataframe(df_f, use_container_width=True)

    proc_ids = df_f["id"].tolist()
    if not proc_ids:
        st.warning("No hay resultados con esos filtros.")
        st.stop()

    proc_id_sel = st.selectbox("Selecciona un procedimiento", proc_ids)
    data = cargar_procedimiento(proc_id_sel)

    if not data["proc"]:
        st.error("No se encontró el procedimiento.")
        st.stop()

    proc = data["proc"]
    dop = data["dop"]
    pasos = data["pasos"]
    caps = data["caps"]

    st.markdown(f"## {proc['titulo']}")
    st.caption(f"Área: **{proc.get('area') or '-'}** · Proceso: **{proc.get('proceso') or '-'}** · Creado: {proc['creado_en']}")

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        with st.expander("📑 Documento del procedimiento", expanded=False):
            if proc.get("documento_path") and os.path.exists(proc["documento_path"]):
                st.download_button("Descargar documento", data=open(proc["documento_path"], "rb").read(), file_name=os.path.basename(proc["documento_path"]))
            else:
                st.info("No se adjuntó documento.")

        with st.expander("🎥 Video paso a paso", expanded=False):
            if proc.get("video_path") and os.path.exists(proc["video_path"]):
                st.video(proc["video_path"])
            else:
                st.info("No se adjuntó video.")

        with st.expander("📝 DOP – Diagrama de Operaciones", expanded=True):
            if not dop.empty:
                st.dataframe(dop.rename(columns={"etapa": "Etapa", "secuencia": "Secuencia"}), use_container_width=True)
                fig, ax = plt.subplots()
                ax.bar(dop["etapa"], dop["secuencia"])
                ax.set_ylabel("Secuencia")
                ax.set_title("Diagrama de Operaciones")
                plt.xticks(rotation=45, ha="right")
                st.pyplot(fig)
            else:
                st.info("Sin etapas registradas.")

        with st.expander("📸 Fotos por paso", expanded=True):
            if not pasos.empty:
                for _, r in pasos.iterrows():
                    st.markdown(f"**Paso {int(r['paso_num'])}** – {r['descripcion'] or ''}")
                    if r["image_path"] and os.path.exists(r["image_path"]):
                        st.image(r["image_path"], use_container_width=True)
                    st.markdown("---")
            else:
                st.info("Sin fotos registradas.")

    with col2:
        with st.expander("📚 Normativa", expanded=True):
            st.text(proc.get("normativa") or "Sin normativa registrada.")

        with st.expander("🏭 Layout del área", expanded=True):
            if proc.get("layout_path") and os.path.exists(proc["layout_path"]):
                st.image(proc["layout_path"], caption="Layout", use_container_width=True)
            else:
                st.info("No se adjuntó layout.")

        with st.expander("📊 Registros de capacitación", expanded=True):
            if not caps.empty:
                st.dataframe(caps, use_container_width=True)
                # Registrar nueva evaluación rápida
                with st.form("form_cap_rapido"):
                    t = st.text_input("Trabajador")
                    c = st.slider("Comprensión", 0, 100, 70)
                    add = st.form_submit_button("Agregar evaluación")
                if add and t:
                    insert_capacitacion(proc_id_sel, t, c)
                    st.success("Evaluación agregada.")
                    st.experimental_rerun()
            else:
                st.info("No hay evaluaciones registradas.")
                with st.form("form_cap_ini"):
                    t = st.text_input("Trabajador")
                    c = st.slider("Comprensión", 0, 100, 70)
                    add = st.form_submit_button("Agregar evaluación")
                if add and t:
                    insert_capacitacion(proc_id_sel, t, c)
                    st.success("Evaluación agregada.")
                    st.experimental_rerun()

    # Descargas útiles
    st.markdown("### ⬇️ Exportar")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Exportar DOP a CSV"):
            csv = dop.to_csv(index=False).encode("utf-8") if not dop.empty else b"etapa,secuencia\n"
            st.download_button("Descargar DOP.csv", data=csv, file_name=f"dop_proc_{proc_id_sel}.csv")
    with c2:
        if st.button("Exportar capacitaciones a CSV"):
            csv2 = caps.to_csv(index=False).encode("utf-8") if not caps.empty else b"trabajador,comprension,registrado_en\n"
            st.download_button("Descargar capacitaciones.csv", data=csv2, file_name=f"caps_proc_{proc_id_sel}.csv")


# ============================
# Notas de uso (pie de página)
# ============================
st.markdown(
    """
    ---
    **Notas:**
    - Los archivos y la base de datos se guardan en la carpeta `data_estandarizacion/` junto a esta app.
    - Para instalar dependencias: `pip install streamlit pandas matplotlib`.
    - Ejecuta con: `streamlit run streamlit_modulo_estandarizacion.py`.
    """
)
