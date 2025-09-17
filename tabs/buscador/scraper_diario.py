#!/usr/bin/env python3
"""
Script de actualización diaria para GitHub Actions
Actualiza solo los últimos días para mantener la base de datos al día
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from scraper_simple import ScraperSimple

# Configurar logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'scraper_diario_{datetime.now().strftime("%Y%m")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def obtener_fechas_recientes(dias=3):
    """
    Obtener fechas de los últimos N días
    Se usa 3 días para mantenimiento diario optimizado
    (incluye fines de semana y posibles fallos anteriores)
    """
    fechas = []
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=dias)
    
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        fechas.append(fecha_actual.strftime("%Y%m%d"))
        fecha_actual += timedelta(days=1)
    
    return fechas

def ejecutar_actualizacion_diaria():
    """Ejecutar actualización diaria optimizada"""
    try:
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"=== Iniciando actualización diaria - {fecha_actual} ===")
        
        # Inicializar scraper
        scraper = ScraperSimple()
        
        # Obtener estadísticas iniciales
        stats_inicial = scraper.db.obtener_estadisticas()
        total_inicial = stats_inicial.get('total', 0)
        logging.info(f"📊 Boletines en BD antes de actualizar: {total_inicial}")
        
        # Obtener fechas recientes (últimos 3 días para mantenimiento diario)
        fechas = obtener_fechas_recientes(dias=3)
        logging.info(f"📅 Procesando fechas: {fechas[0]} a {fechas[-1]} ({len(fechas)} días)")
        
        # Ejecutar scraping para cada fuente
        logging.info("🔄 Iniciando descarga de boletines...")
        
        resultados = {}
        
        # DOE
        logging.info("📄 Procesando DOE...")
        resultados['doe'] = scraper.scraping_doe_historico(fechas)
        
        # BOP Badajoz
        logging.info("📄 Procesando BOP Badajoz...")
        resultados['bop'] = scraper.scraping_bop_historico(fechas)
        
        # BOE
        logging.info("📄 Procesando BOE...")
        resultados['boe'] = scraper.scraping_boe_historico(fechas)
        
        # Calcular totales
        total_nuevos = sum(resultados.values())
        
        # Limpiar datos antiguos (mantener solo últimos 3 meses = 90 días)
        logging.info("🧹 Limpiando datos antiguos (>90 días)...")
        eliminados = scraper.db.limpiar_datos_antiguos(dias=90)
        if eliminados > 0:
            logging.info(f"🗑️  Eliminados {eliminados} registros antiguos")
        else:
            logging.info("✅ No hay registros antiguos para eliminar")
        
        # TEST DIRECTO con conexión nueva
        logging.info("🔍 DIAGNÓSTICO: Verificando con conexión SQLite directa...")
        import sqlite3
        db_path = scraper.db.db_path  # Usar el path del scraper
        conn_test = sqlite3.connect(db_path)
        cursor_test = conn_test.cursor()
        cursor_test.execute("SELECT COUNT(*) FROM boletines")
        count_directo = cursor_test.fetchone()[0]
        logging.info(f"📊 CONEXIÓN DIRECTA: {count_directo} registros")
        
        cursor_test.execute("SELECT fuente, COUNT(*) FROM boletines GROUP BY fuente")
        por_fuente_directo = cursor_test.fetchall()
        logging.info(f"📋 CONEXIÓN DIRECTA por fuente: {por_fuente_directo}")
        conn_test.close()
        
        # Estadísticas finales usando la función normal
        logging.info("🔍 DIAGNÓSTICO: Verificando con función obtener_estadisticas()...")
        stats_final = scraper.db.obtener_estadisticas()
        total_final = stats_final.get('total', 0)
        logging.info(f"📊 FUNCIÓN NORMAL: {total_final} registros")
        logging.info(f"📋 FUNCIÓN NORMAL por fuente: {stats_final.get('por_fuente', {})}")
        
        # Logging de resultados
        logging.info("=== Resumen de actualización ===")
        logging.info(f"📥 Nuevos boletines por fuente:")
        logging.info(f"   • DOE: {resultados['doe']}")
        logging.info(f"   • BOP: {resultados['bop']}")
        logging.info(f"   • BOE: {resultados['boe']}")
        logging.info(f"📊 Total nuevos: {total_nuevos}")
        logging.info(f"📚 Total en BD: {total_inicial} → {total_final}")
        
        if total_nuevos > 0:
            logging.info(f"✅ Actualización exitosa: {total_nuevos} boletines nuevos agregados")
        else:
            logging.info("ℹ️  No se encontraron boletines nuevos (BD ya actualizada)")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error en actualización diaria: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    # Ejecutar actualización
    success = ejecutar_actualizacion_diaria()
    
    if success:
        print("✅ Actualización diaria completada exitosamente")
        sys.exit(0)
    else:
        print("❌ Error en actualización diaria")
        sys.exit(1)