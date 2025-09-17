import sqlite3
import logging
from datetime import datetime
from typing import List, Tuple, Optional

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BoletinesDBSimple:
    def __init__(self, db_path: str = "data/boletines.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar la base de datos con estructura simple"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla simple para boletines
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS boletines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE NOT NULL,
                    fuente TEXT NOT NULL,
                    contenido_html TEXT NOT NULL,
                    fecha_scraping DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(fecha, fuente)
                )
            ''')
            
            # Índices básicos para optimizar búsquedas
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fecha_fuente ON boletines(fecha, fuente)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fecha ON boletines(fecha)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fuente ON boletines(fuente)')
            
            conn.commit()
            logging.info("Base de datos simple inicializada correctamente")
    
    def insertar_boletin_completo(self, fecha: str, fuente: str, contenido_html: str) -> bool:
        """Insertar HTML completo de un boletín para una fecha específica"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO boletines 
                    (fecha, fuente, contenido_html)
                    VALUES (?, ?, ?)
                ''', (fecha, fuente, contenido_html))
                
                if cursor.rowcount > 0:
                    logging.info(f"Insertado/Actualizado: {fuente} - {fecha}")
                    
                    # DIAGNÓSTICO: Verificar inmediatamente después del insert
                    cursor.execute("SELECT COUNT(*) FROM boletines")
                    count_after_insert = cursor.fetchone()[0]
                    logging.info(f"DEBUG: Registros después de insert: {count_after_insert}")
                    
                    return True
                return False
        except sqlite3.Error as e:
            logging.error(f"Error insertando boletín: {e}")
            return False
    
    def obtener_boletines_rango(self, fecha_inicio: str, fecha_fin: str, 
                               fuentes: List[str] = None) -> List[Tuple]:
        """Obtener todos los boletines HTML en un rango de fechas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT fecha, fuente, contenido_html
                    FROM boletines
                    WHERE fecha BETWEEN ? AND ?
                '''
                params = [fecha_inicio, fecha_fin]
                
                if fuentes:
                    query += f" AND fuente IN ({','.join(['?'] * len(fuentes))})"
                    params.extend(fuentes)
                
                query += " ORDER BY fecha ASC, fuente"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                logging.info(f"Obtenidos {len(results)} boletines para el rango {fecha_inicio} - {fecha_fin}")
                return [dict(row) for row in results]
                
        except sqlite3.Error as e:
            logging.error(f"Error obteniendo boletines: {e}")
            return []
    
    def obtener_estadisticas(self) -> dict:
        """Obtener estadísticas básicas de la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de boletines
                cursor.execute("SELECT COUNT(*) FROM boletines")
                total = cursor.fetchone()[0]
                
                # Por fuente
                cursor.execute('''
                    SELECT fuente, COUNT(*) as count 
                    FROM boletines 
                    GROUP BY fuente 
                    ORDER BY count DESC
                ''')
                por_fuente = dict(cursor.fetchall())
                
                # Rango de fechas
                cursor.execute("SELECT MIN(fecha), MAX(fecha) FROM boletines")
                fecha_min, fecha_max = cursor.fetchone()
                
                # Últimos scraping
                cursor.execute("SELECT MAX(fecha_scraping) FROM boletines")
                ultimo_scraping = cursor.fetchone()[0]
                
                return {
                    'total': total,
                    'por_fuente': por_fuente,
                    'fecha_inicio': fecha_min,
                    'fecha_fin': fecha_max,
                    'ultimo_scraping': ultimo_scraping
                }
                
        except sqlite3.Error as e:
            logging.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def limpiar_datos_antiguos(self, dias: int = 180):
        """Limpiar datos más antiguos que X días"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Convertir fecha YYYYMMDD a formato YYYY-MM-DD para comparación correcta
                cursor.execute('''
                    DELETE FROM boletines 
                    WHERE date(substr(fecha, 1, 4) || '-' || substr(fecha, 5, 2) || '-' || substr(fecha, 7, 2)) < date('now', '-' || ? || ' days')
                ''', (dias,))
                
                eliminados = cursor.rowcount
                logging.info(f"Eliminados {eliminados} registros antiguos")
                return eliminados
                
        except sqlite3.Error as e:
            logging.error(f"Error limpiando datos: {e}")
            return 0
    
    def verificar_fechas_existentes(self, fechas: List[str], fuente: str) -> List[str]:
        """Verificar qué fechas ya existen en la BD para evitar re-scraping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Crear placeholder para fechas
                placeholders = ','.join(['?' for _ in fechas])
                query = f'''
                    SELECT fecha FROM boletines 
                    WHERE fuente = ? AND fecha IN ({placeholders})
                '''
                
                cursor.execute(query, [fuente] + fechas)
                fechas_existentes = set(row[0] for row in cursor.fetchall())
                
                # Retornar fechas que NO existen
                fechas_faltantes = [f for f in fechas if f not in fechas_existentes]
                
                logging.info(f"{fuente}: {len(fechas_existentes)} fechas ya existen, {len(fechas_faltantes)} por procesar")
                return fechas_faltantes
                
        except sqlite3.Error as e:
            logging.error(f"Error verificando fechas: {e}")
            return fechas