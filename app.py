import streamlit as st
from auth import show_auth_page
from supabase_client import supabase

st.set_page_config(page_title="Alertas de Boletines", page_icon=":bell:")

# Función para el panel de control (dashboard)
def show_dashboard():
    st.title("Panel de Control")
    st.write(f"Bienvenido, {st.session_state.user['email']}")

    st.header("Configuración de Preferencias")
    # Aquí irán los componentes para que el usuario configure sus preferencias
    st.write("Próximamente podrás configurar tus municipios y la hora de envío aquí.")

    if st.button("Cerrar Sesión"):
        del st.session_state.user
        st.rerun()

# Lógica principal de la aplicación
def main():
    # Comprobar si el usuario está en el estado de la sesión
    if 'user' not in st.session_state:
        # Intentar recuperar la sesión de Supabase
        try:
            # Esta es una llamada síncrona, puede que necesites gestionarla de forma asíncrona
            # en un entorno de producción real, pero para Streamlit esto puede funcionar.
            # La librería de Python de Supabase aún no tiene un método directo como `getSession` de JS.
            # La sesión se gestiona principalmente a través de st.session_state en este ejemplo.
            # Por ahora, simplemente mostramos la página de login/registro.
            show_auth_page()
        except Exception as e:
            show_auth_page() # Si hay error, mostrar login
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
