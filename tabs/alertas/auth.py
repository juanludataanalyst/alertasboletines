import streamlit as st
from supabase_client import supabase

def show_auth_page():
    st.markdown("""
        <style>
            /* Ocultar la barra de navegación por defecto de Streamlit en la página de login */
            div[data-testid="stToolbar"] {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    _, col2, _ = st.columns([1, 1, 1])

    with col2:
        st.title("Alertas de Boletines Oficiales")
        
        with st.container():
          #  st.header("Bienvenido de nuevo")
          #  st.markdown("Por favor, inicia sesión para continuar.")

            email = st.text_input("Email", placeholder="tu@email.com")
            password = st.text_input("Contraseña", type="password", placeholder="********")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Iniciar Sesión", use_container_width=True):
                if email and password:
                    try:
                        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = response.user.dict()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: Las credenciales no son correctas o el usuario no existe.")
                else:
                    st.warning("Por favor, introduce tu email y contraseña.")
