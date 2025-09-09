import streamlit as st
import sqlite3
import bcrypt
import json 
# ---------- BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect('login_usuarios.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            rol TEXT,
            etapa TEXT
        )
    ''')
    conn.commit()
    conn.close()

def crear_usuario_por_defecto():
    conn = sqlite3.connect('login_usuarios.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        hashed_password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        c.execute("INSERT INTO usuarios (username, password, rol, etapa) VALUES (?, ?, ?, ?)",
                  ("admin", hashed_password, "administrador", ""))
        conn.commit()
        print("🔐 Usuario por defecto creado: admin / admin123")
    conn.close()




def crear_usuario(username, password, rol, etapa):
    conn = sqlite3.connect('login_usuarios.db')
    c = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO usuarios (username, password, rol, etapa) VALUES (?, ?, ?, ?)", 
                  (username, hashed_password, rol, etapa))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verificar_usuario(username, password):
    conn = sqlite3.connect('login_usuarios.db')
    c = conn.cursor()
    c.execute("SELECT password, rol, etapa FROM usuarios WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        hashed_password, rol, etapa = result
        if bcrypt.checkpw(password.encode(), hashed_password):
            return rol, etapa
    return None, None

def obtener_usuarios():
    conn = sqlite3.connect('login_usuarios.db')
    c = conn.cursor()
    c.execute("SELECT id, username, rol, etapa FROM usuarios")
    users = c.fetchall()
    conn.close()
    return users

def actualizar_usuario(user_id, password=None, rol=None, etapa=None):
    conn = sqlite3.connect('login_usuarios.db')
    c = conn.cursor()
    if password:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        c.execute("UPDATE usuarios SET password=? WHERE id=?", (hashed_password, user_id))
    if rol:
        c.execute("UPDATE usuarios SET rol=? WHERE id=?", (rol, user_id))
    if etapa:
        c.execute("UPDATE usuarios SET etapa=? WHERE id=?", (etapa, user_id))
    conn.commit()
    conn.close()

def eliminar_usuario(user_id):
    conn = sqlite3.connect('login_usuarios.db')
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
# Fuera de login_modulo()

def gestion_usuario():
    st.title("⚙️ Configuración de Usuarios")

    col1, col2, col3 = st.columns(3)

    # ======== Columna 1: Registrar usuario ========
    with col1:
        st.subheader("➕ Crear Usuario")
        username = st.text_input("Nuevo Usuario", key="nuevo_user")
        password = st.text_input("Contraseña", type="password", key="pwd_user")
        rol = st.selectbox("Rol", ["administrador", "planificador", "trabajador"], key="rol_user")
        

            # Leer etapas desde archivo JSON
        try:
            with open("data/etapas.json", "r", encoding="utf-8") as f:
                etapas_config = json.load(f)
        except FileNotFoundError:
            etapas_config = []

        # Extraer solo los nombres de etapa
        nombres_etapas = [etapa["nombre"] for etapa in etapas_config] if etapas_config else []

        # Si no hay etapas configuradas, permitir texto libre
        if nombres_etapas:
            etapa = st.selectbox("Etapa de Producción (si aplica)", nombres_etapas, key="etapa_user")
        else:
            etapa = st.text_input("Etapa de Producción (si aplica)", placeholder="Ej: Corte, Troquelado...", key="etapa_user")


        if st.button("Crear Usuario", key="btn_crear_usuario"):
            if crear_usuario(username, password, rol, etapa):
                st.success("✅ Usuario creado exitosamente")
            else:
                st.error("⚠️ El usuario ya existe")

    # ======== Columna 2: Lista de usuarios ========
    with col2:
        st.subheader("👥 Lista de Usuarios")
        usuarios = obtener_usuarios()
        for user in usuarios:
            user_id, username, rol_actual, etapa_actual = user
            with st.expander(f"👤 {username}"):
                nueva_contra = st.text_input(f"Nueva Contraseña para {username}", key=f"pwd_{user_id}", type="password")
                nuevo_rol = st.selectbox("Nuevo Rol", ["administrador", "planificador", "trabajador"],
                                         key=f"rol_{user_id}", 
                                         index=["administrador", "planificador", "trabajador"].index(rol_actual))
                nueva_etapa = st.text_input("Nueva Etapa", value=etapa_actual or "", key=f"etapa_{user_id}")

                colA, colB = st.columns(2)
                with colA:
                    if st.button("Actualizar", key=f"update_{user_id}"):
                        actualizar_usuario(user_id, nueva_contra if nueva_contra else None, nuevo_rol, nueva_etapa)
                        st.success("Usuario actualizado")
                        st.rerun()
                with colB:
                    if username != "admin":
                        if st.button("❌ Eliminar", key=f"delete_{user_id}"):
                            eliminar_usuario(user_id)
                            st.warning(f"Usuario {username} eliminado.")
                            st.rerun()
                    else:
                        st.info("Este usuario no puede eliminarse.")

    # ======== Columna 3: Usuarios en línea ========
    with col3:
        st.subheader("🟢 Usuarios en Línea")

# ==============================================================================================================================
# ==============================================================================================================================



def login_modulo():
    # --- CSS para personalizar botones ---
    st.markdown("""
        <style>
        /* Botón azul para Iniciar Sesión */
        div[data-testid="stForm"] button[kind="primary"] {
            background-color: #1C2227FF !important;
            color: white !important;
            border-radius: 6px !important;
            border: none !important;
        }
        div[data-testid="stForm"] button[kind="primary"]:hover {
            background-color: #32BD25FF !important;
        }
        /* Botón negro para Ingreso Directo */
        div[data-testid="stForm"] button[kind="secondary"] {
            background-color: #DF0A46FF !important;
            color: white !important;
            border-radius: 6px !important;
            border: none !important;
        }
        div[data-testid="stForm"] button[kind="secondary"]:hover {
            background-color: #DF0A83FF !important;
        }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns([3, 6, 3])

    with cols[1]:
        st.markdown("""
        <h4 style='text-align: center;'>BIENVENIDO</h4>
        <p style='text-align: center;'>Potencia tu productividad y optimiza procesos desde aquí</p>
        """, unsafe_allow_html=True)
        st.image("imagen/logoo.png", use_container_width=True)

    init_db()
    crear_usuario_por_defecto()

    with cols[1]:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")

            btn_cols = st.columns([1, 2,3,4])
            with btn_cols[1]:
                submit = st.form_submit_button("Iniciar Sesión", type="primary")
            with btn_cols[3]:
                ingreso_directo = st.form_submit_button("Ingreso Directo", type="secondary")

            if submit:
                rol, etapa = verificar_usuario(username, password)
                if rol:
                    st.success(f"Bienvenido {username} - Rol: {rol}")
                    st.session_state['usuario'] = username
                    st.session_state['rol'] = rol
                    st.session_state['etapa'] = etapa
                    st.session_state['login'] = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

            if ingreso_directo:
                st.session_state['usuario'] = "invitado"
                st.session_state['rol'] = "invitado"
                st.session_state['etapa'] = None
                st.session_state['login'] = True
                st.rerun()