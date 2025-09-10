import streamlit as st
import sys
import os

# Agregar paths para importar desde subdirectorios
sys.path.append(os.path.join(os.path.dirname(__file__), 'tabs', 'alertas'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tabs', 'buscador'))

from tabs.alertas.auth import show_auth_page
from tabs.alertas.alertas_tab import show_alertas_tab
from tabs.buscador.buscador_tab import show_buscador_tab

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sistema de Boletines Oficiales", page_icon="📄", layout="wide")

# --- CARGAR CSS EXTERNO ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS opcional

load_css("style.css")

# --- LÓGICA PRINCIPAL CON AUTENTICACIÓN GLOBAL ---
def main():
    # Verificar si el usuario está autenticado
    if 'user' not in st.session_state:
        # Mostrar página de autenticación
        st.title("📄 Sistema de Boletines Oficiales")
        st.markdown("Inicia sesión para acceder al sistema completo")
        show_auth_page()
    else:
        # Usuario autenticado - mostrar sistema completo con pestañas
        # Barra superior con info de usuario
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            st.title("📄 Sistema de Boletines Oficiales")
            st.caption(f"Bienvenido, {st.session_state.user['email']}")
        with col2:
            if st.button("Cerrar Sesión"):
                del st.session_state.user
                st.rerun()
        
        st.divider()
        
        # Crear pestañas del sistema
        tab1, tab2 = st.tabs(["🔔 Alertas por Email", "🔍 Buscador Histórico"])
        
        with tab1:
            show_alertas_tab()
        
        with tab2:
            show_buscador_tab()

if __name__ == "__main__":
    main()
