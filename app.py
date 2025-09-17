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

# --- VERIFICACIÓN Y CARGA AUTOMÁTICA DE BD ---
@st.cache_data(ttl=3600)  # Cache por 1 hora
def verificar_y_cargar_bd():
    """Verificar si la BD está vacía y cargar datos automáticamente al inicio"""
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'tabs', 'buscador'))
    
    from database_simple import BoletinesDBSimple
    from scraper_simple import ScraperSimple, generar_fechas_ultimo_trimestre
    
    db_path = os.path.join(os.path.dirname(__file__), 'tabs', 'buscador', 'data', 'boletines.db')
    db = BoletinesDBSimple(db_path)
    stats = db.obtener_estadisticas()
    
    if stats.get('total', 0) == 0:
        st.info("🔄 Inicializando base de datos. Descargando datos históricos...")
        progress_bar = st.progress(0, text="Iniciando descarga...")
        
        try:
            scraper = ScraperSimple(db_path)
            fechas = generar_fechas_ultimo_trimestre()
            
            progress_bar.progress(30, text="Descargando DOE...")
            scraper.scraping_doe_historico(fechas)
            
            progress_bar.progress(60, text="Descargando BOP...")
            scraper.scraping_bop_historico(fechas)
            
            progress_bar.progress(90, text="Descargando BOE...")
            scraper.scraping_boe_historico(fechas)
            
            progress_bar.progress(100, text="¡Datos cargados!")
            st.success("✅ Base de datos inicializada correctamente")
            progress_bar.empty()
            
        except Exception as e:
            st.error(f"❌ Error cargando datos: {str(e)}")
            progress_bar.empty()
    
    return True

# --- LÓGICA PRINCIPAL CON AUTENTICACIÓN GLOBAL ---
def main():
    # Verificar y cargar BD al inicio de la app
    verificar_y_cargar_bd()
    # Verificar si el usuario está autenticado
    if 'user' not in st.session_state:
        # Mostrar página de autenticación sin texto adicional
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
        
        # Navegación lateral con pestañas independientes
        with st.sidebar:
            st.header("📋 Navegación")
            selected_tab = st.radio(
                "Selecciona una sección:",
                ["🔔 Alertas por Email", "🔍 Buscador Histórico"],
                label_visibility="collapsed"
            )
        
        # Mostrar contenido según la pestaña seleccionada
        if selected_tab == "🔔 Alertas por Email":
            show_alertas_tab()
        else:  # "🔍 Buscador Histórico"
            show_buscador_tab(selected_tab)

if __name__ == "__main__":
    main()
