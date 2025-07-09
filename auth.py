import streamlit as st
from supabase_client import supabase

def show_auth_page():
    st.title("Bienvenido a Alertas de Boletines")

    # Verifica si el usuario ya está logueado
    if 'user' in st.session_state:
        st.write(f"Bienvenido de nuevo, {st.session_state.user['email']}!")
        if st.button("Cerrar Sesión"):
            del st.session_state.user
            st.rerun()
        return

    st.header("Iniciar Sesión o Registrarse")

    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Iniciar Sesión"):
            if email and password:
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = response.user.dict()
                    st.success("Inicio de sesión exitoso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al iniciar sesión: {e}")
            else:
                st.warning("Por favor, introduce tu email y contraseña.")

    with col2:
        if st.button("Registrarse"):
            if email and password:
                try:
                    response = supabase.auth.sign_up({"email": email, "password": password})
                    # La sesión no se crea automáticamente en el registro con email/password
                    # El usuario debe confirmar su email y luego iniciar sesión.
                    st.success("Registro exitoso! Por favor, revisa tu email para confirmar tu cuenta y luego inicia sesión.")
                except Exception as e:
                    st.error(f"Error en el registro: {e}")
            else:
                st.warning("Por favor, introduce un email y contraseña para registrarte.")
