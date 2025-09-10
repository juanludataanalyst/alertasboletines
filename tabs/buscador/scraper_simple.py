import requests
from datetime import datetime, timedelta
import time
import logging
from database_simple import BoletinesDBSimple
from typing import List

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generar_fechas_ultimo_trimestre():
    """Generar lista de fechas de los últimos 3 meses"""
    fechas = []
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=90)  # Aproximadamente 3 meses
    
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        fechas.append(fecha_actual.strftime("%Y%m%d"))
        fecha_actual += timedelta(days=1)
    
    logging.info(f"Generadas {len(fechas)} fechas desde {fecha_inicio.strftime('%Y-%m-%d')} hasta {fecha_fin.strftime('%Y-%m-%d')}")
    return fechas

class ScraperSimple:
    def __init__(self, db_path: str = "data/boletines.db"):
        self.db = BoletinesDBSimple(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scraping_doe_historico(self, fechas: List[str]) -> int:
        """Descargar y guardar HTML completo del DOE para cada fecha"""
        # Filtrar fechas que ya existen
        fechas_pendientes = self.db.verificar_fechas_existentes(fechas, "DOE")
        
        if not fechas_pendientes:
            logging.info("DOE: Todas las fechas ya están en la BD")
            return 0
        
        total_insertados = 0
        
        for i, fecha in enumerate(fechas_pendientes):
            url = f"https://doe.juntaex.es/ultimosdoe/mostrardoe.php?fecha={fecha}&t=o"
            
            try:
                logging.info(f"DOE: Descargando {fecha} ({i+1}/{len(fechas_pendientes)})")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # Guardar HTML completo
                if self.db.insertar_boletin_completo(fecha, "DOE", response.text):
                    total_insertados += 1
                
                time.sleep(2)  # Pausa entre requests para ser respetuoso
                
            except requests.RequestException as e:
                logging.error(f"Error descargando DOE {fecha}: {e}")
                continue
        
        logging.info(f"DOE: Insertados {total_insertados} boletines HTML")
        return total_insertados
    
    def scraping_bop_historico(self, fechas: List[str]) -> int:
        """Descargar y guardar HTML completo del BOP Badajoz para cada fecha"""
        # Filtrar fechas que ya existen
        fechas_pendientes = self.db.verificar_fechas_existentes(fechas, "BOP")
        
        if not fechas_pendientes:
            logging.info("BOP: Todas las fechas ya están en la BD")
            return 0
        
        total_insertados = 0
        
        for i, fecha in enumerate(fechas_pendientes):
            url = f"https://www.dip-badajoz.es/bop/ventana_boletin_completo.php?FechaSolicitada={fecha}000000"
            
            try:
                logging.info(f"BOP: Descargando {fecha} ({i+1}/{len(fechas_pendientes)})")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # Guardar HTML completo
                if self.db.insertar_boletin_completo(fecha, "BOP", response.text):
                    total_insertados += 1
                
                time.sleep(2)  # Pausa entre requests
                
            except requests.RequestException as e:
                logging.error(f"Error descargando BOP {fecha}: {e}")
                continue
        
        logging.info(f"BOP: Insertados {total_insertados} boletines HTML")
        return total_insertados
    
    def scraping_boe_historico(self, fechas: List[str]) -> int:
        """Descargar y guardar HTML completo del BOE para cada fecha"""
        # Filtrar fechas que ya existen
        fechas_pendientes = self.db.verificar_fechas_existentes(fechas, "BOE")
        
        if not fechas_pendientes:
            logging.info("BOE: Todas las fechas ya están en la BD")
            return 0
        
        total_insertados = 0
        
        for i, fecha in enumerate(fechas_pendientes):
            fecha_boe = datetime.strptime(fecha, "%Y%m%d").strftime("%Y/%m/%d")
            url = f"https://www.boe.es/boe/dias/{fecha_boe}/"
            
            try:
                logging.info(f"BOE: Descargando {fecha} ({i+1}/{len(fechas_pendientes)})")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # Guardar HTML completo
                if self.db.insertar_boletin_completo(fecha, "BOE", response.text):
                    total_insertados += 1
                
                time.sleep(2)  # Pausa entre requests
                
            except requests.RequestException as e:
                logging.error(f"Error descargando BOE {fecha}: {e}")
                continue
        
        logging.info(f"BOE: Insertados {total_insertados} boletines HTML")
        return total_insertados
    
    def ejecutar_scraping_completo(self) -> dict:
        """Ejecutar scraping completo de los últimos 3 meses - Solo HTML"""
        fechas = generar_fechas_ultimo_trimestre()
        
        resultados = {
            'fechas_total': len(fechas),
            'doe': 0,
            'bop': 0,
            'boe': 0,
            'total': 0
        }
        
        logging.info("=== Iniciando scraping HTML histórico (últimos 3 meses) ===")
        
        # DOE
        logging.info("--- Descargando DOE ---")
        resultados['doe'] = self.scraping_doe_historico(fechas)
        
        # BOP
        logging.info("--- Descargando BOP Badajoz ---")
        resultados['bop'] = self.scraping_bop_historico(fechas)
        
        # BOE
        logging.info("--- Descargando BOE ---")
        resultados['boe'] = self.scraping_boe_historico(fechas)
        
        resultados['total'] = resultados['doe'] + resultados['bop'] + resultados['boe']
        
        logging.info(f"=== Scraping completado: {resultados['total']} boletines HTML descargados ===")
        return resultados

if __name__ == "__main__":
    scraper = ScraperSimple()
    resultados = scraper.ejecutar_scraping_completo()
    print(f"Proceso completado: {resultados}")
    
    # Mostrar estadísticas finales
    stats = scraper.db.obtener_estadisticas()
    print(f"Estadísticas BD: {stats}")