import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
from database_simple import BoletinesDBSimple
from scraper_simple import ScraperSimple
from buscador_historico import BuscadorHistorico, format_email

def show_buscador_tab(selected_tab):
    st.header("🔍 Buscador Histórico de Boletines")
    st.markdown("**Sistema de búsqueda histórica** - Busca municipios y menciones en datos almacenados")
    
    # Inicializar componentes
    @st.cache_resource
    def init_database():
        return BoletinesDBSimple("tabs/buscador/data/boletines.db")

    @st.cache_resource
    def init_scraper():
        return ScraperSimple("tabs/buscador/data/boletines.db")

    @st.cache_resource
    def init_buscador():
        return BuscadorHistorico("tabs/buscador/data/boletines.db")
    
    # La verificación y carga automática se hace en app.py al inicio
    
    db = init_database()
    scraper = init_scraper()
    buscador = init_buscador()
    
    # Obtener estadísticas
    stats = db.obtener_estadisticas()
    
    # Mostrar estadísticas en el sidebar solo para esta pestaña
    if selected_tab == "🔍 Buscador Histórico":
        with st.sidebar:
            st.divider()
            st.header("📊 Base de Datos Histórica")
            
            if stats and stats.get('total', 0) > 0:
                st.metric("📁 Total boletines HTML", stats.get('total', 0))
                
                if stats.get('por_fuente'):
                    st.subheader("Por fuente:")
                    for fuente, cantidad in stats['por_fuente'].items():
                        st.write(f"• **{fuente}**: {cantidad} días")
                
                if stats.get('fecha_inicio') and stats.get('fecha_fin'):
                    fecha_inicio_display = str(stats['fecha_inicio'])
                    fecha_fin_display = str(stats['fecha_fin'])
                    st.write(f"📅 **Período**: {fecha_inicio_display} → {fecha_fin_display}")
            else:
                st.warning("⚠️ Base de datos vacía")
            
            st.divider()
            
            # Botón para actualizar datos
            if st.button("🔄 Actualizar Base de Datos"):
                with st.spinner("Descargando HTML histórico... (5-10 minutos)"):
                    try:
                        results = scraper.ejecutar_scraping_completo()
                        st.success(f"✅ Proceso completado!")
                        st.json(results)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error descargando: {e}")
                        logging.error(f"Error en scraping: {e}")
    
    # Interfaz principal
    if not stats or stats.get('total', 0) == 0:
        st.warning("⚠️ **Base de datos vacía.** Usa el botón lateral para descargar los boletines históricos primero.")
        st.stop()
    
    # Configuración de búsqueda
    st.subheader("⚙️ Configuración de Búsqueda")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🏛️ Municipios**")
        municipios_text = st.text_area(
            "Lista de municipios (uno por línea):",
            value="Badajoz\nMérida\nCáceres",
            height=120,
            help="Introduce cada municipio en una línea separada"
        )
        municipios = [m.strip() for m in municipios_text.split('\n') if m.strip()]
        st.write(f"✅ **{len(municipios)} municipios** configurados")
    
    with col2:
        st.write("**🔍 Menciones Múltiples**")
        menciones_text = st.text_area(
            "Lista de menciones múltiples (una por línea):",
            value="licitación, obra pública\ncontrato, servicios\nurbanismo, licencia\nordenanza, tráfico\npresupuesto, municipal\nsubvención, asociación",
            height=120,
            help="Cada línea = una búsqueda. Separa palabras con comas para búsqueda AND (todas las palabras deben aparecer)"
        )
        menciones = [m.strip() for m in menciones_text.split('\n') if m.strip()]
        st.write(f"✅ **{len(menciones)} menciones múltiples** configuradas")
        
        # Mostrar preview de las menciones
        with st.expander("👁️ Preview menciones múltiples"):
            for i, mencion in enumerate(menciones, 1):
                palabras = [p.strip() for p in mencion.split(',') if p.strip()]
                if len(palabras) > 1:
                    st.write(f"{i}. **Búsqueda AND**: {' + '.join(palabras)}")
                else:
                    st.write(f"{i}. **Búsqueda simple**: {palabras[0]}")
    
    # Configuración adicional
    col3, col4 = st.columns(2)
    
    with col3:
        fuentes = st.multiselect(
            "📋 Fuentes a consultar:",
            options=["BOE", "DOE", "BOP"],
            default=["BOE", "DOE", "BOP"],
            help="Selecciona qué boletines consultar"
        )
    
    with col4:
        # Obtener rango disponible de la BD
        if stats.get('fecha_inicio') and stats.get('fecha_fin'):
            try:
                fecha_inicio_str = str(stats['fecha_inicio'])
                fecha_fin_str = str(stats['fecha_fin'])
                min_date = datetime.strptime(fecha_inicio_str, "%Y%m%d").date()
                max_date = datetime.strptime(fecha_fin_str, "%Y%m%d").date()
            except (ValueError, TypeError):
                # Si hay error parsing fechas, usar fechas por defecto
                max_date = datetime.now().date()
                min_date = max_date - timedelta(days=90)
        else:
            # BD vacía - usar fechas por defecto
            max_date = datetime.now().date()
            min_date = max_date - timedelta(days=90)
            
            col4_1, col4_2 = st.columns(2)
            with col4_1:
                fecha_inicio = st.date_input(
                    "📅 Fecha inicio:",
                    value=max_date - timedelta(days=30),
                    min_value=min_date,
                    max_value=max_date
                )
            
            with col4_2:
                fecha_fin = st.date_input(
                    "📅 Fecha fin:",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
        else:
            st.error("No se puede determinar el rango de fechas disponible")
            st.stop()
    
    # Validaciones
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin")
        st.stop()
    
    # Botón de búsqueda principal
    st.divider()
    
    if not municipios and not menciones:
        st.error("⚠️ **Configura al menos municipios o menciones** para realizar la búsqueda")
    elif not fuentes:
        st.error("⚠️ **Selecciona al menos una fuente** (BOE, DOE, BOP)")
    else:
        if st.button("🚀 Ejecutar Búsqueda Histórica", type="primary", use_container_width=True):
            with st.spinner("Ejecutando búsqueda histórica..."):
                try:
                    fecha_inicio_str = fecha_inicio.strftime("%Y%m%d")
                    fecha_fin_str = fecha_fin.strftime("%Y%m%d")
                    
                    results = buscador.buscar_municipio_y_menciones(
                        municipios=municipios,
                        menciones=menciones,
                        fuentes=fuentes,
                        fecha_inicio=fecha_inicio_str,
                        fecha_fin=fecha_fin_str
                    )
                    
                    if results:
                        total_anuncios = sum(len(data[0]) for data in results.values())
                        total_menciones = sum(len(data[2]) for data in results.values() if len(data) > 2)
                        total_results = total_anuncios + total_menciones
                        
                        st.success(f"✅ **Búsqueda completada:** {total_results} resultados ({total_anuncios} anuncios + {total_menciones} menciones)")
                        
                        # Mostrar resultados
                        st.subheader("📋 Resultados con Fechas")
                        html_results = format_email(results)
                        st.markdown(html_results, unsafe_allow_html=True)
                        
                        # Descarga
                        st.download_button(
                            label="📥 Descargar Reporte HTML",
                            data=html_results,
                            file_name=f"busqueda_historica_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                            mime="text/html",
                            use_container_width=True
                        )
                        
                        # Resumen
                        with st.expander("📈 Resumen detallado"):
                            for fuente, (anuncios, url, menciones) in results.items():
                                st.write(f"**{fuente}**: {len(anuncios)} anuncios + {len(menciones)} menciones")
                    
                    else:
                        st.info("ℹ️ No se encontraron resultados para la configuración especificada")
                        
                except Exception as e:
                    st.error(f"❌ Error ejecutando búsqueda: {e}")
                    logging.error(f"Error en búsqueda: {e}")