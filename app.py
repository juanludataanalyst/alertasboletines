import streamlit as st
import sys
import os

# Agregar paths para importar desde subdirectorios
sys.path.append(os.path.join(os.path.dirname(__file__), 'tabs', 'alertas'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tabs', 'buscador'))

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

# --- LÓGICA PRINCIPAL CON PESTAÑAS ---
def main():
    st.title("📄 Sistema de Boletines Oficiales")
    st.markdown("Sistema completo para alertas y búsquedas históricas")
    
    # Crear pestañas
    tab1, tab2 = st.tabs(["🔔 Alertas por Email", "🔍 Buscador Histórico"])
    
    with tab1:
        show_alertas_tab()
    
    with tab2:
        show_buscador_tab()

if __name__ == "__main__":
    main()
