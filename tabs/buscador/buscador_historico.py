import logging
from datetime import datetime
from database_simple import BoletinesDBSimple
from extractor_sender import (
    extract_doe_announcement, extract_bop_announcement, extract_boe_announcement,
    extract_doe_mentions, extract_bop_mentions, extract_boe_mentions,
    normalize_text
)
from typing import List

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BuscadorHistorico:
    def __init__(self, db_path: str = "data/boletines.db"):
        self.db = BoletinesDBSimple(db_path)
    
    def buscar_municipio_historico(self, municipio: str, fuentes: List[str], 
                                  fecha_inicio: str, fecha_fin: str) -> dict:
        """
        Buscar un municipio específico usando las funciones exactas de sender.py
        pero aplicadas sobre múltiples fechas históricas
        """
        # Obtener todos los boletines HTML del rango
        boletines = self.db.obtener_boletines_rango(fecha_inicio, fecha_fin, fuentes)
        
        results = {}
        
        for fuente in fuentes:
            found_announcements = []
            
            # Filtrar boletines por fuente
            boletines_fuente = [b for b in boletines if b['fuente'] == fuente]
            
            for boletin in boletines_fuente:
                fecha = boletin['fecha']
                html = boletin['contenido_html']
                
                try:
                    # Aplicar función de extracción exacta según fuente
                    if fuente == "DOE":
                        announcements = extract_doe_announcement(html, municipio)
                    elif fuente == "BOP":
                        announcements = extract_bop_announcement(html, municipio, fecha + "000000")
                    elif fuente == "BOE":
                        announcements = extract_boe_announcement(html, municipio, fecha)
                    else:
                        continue
                    
                    # Agregar fecha a cada resultado y filtrar válidos
                    for prefix, text, pdf_url in announcements:
                        if text != "No se encontró texto de anuncio específico.":
                            found_announcements.append((
                                f"Ayuntamiento de {municipio}",
                                prefix,
                                text,
                                pdf_url,
                                fecha  # Agregamos fecha para referencia
                            ))
                            
                except Exception as e:
                    logging.error(f"Error procesando {fuente} {fecha}: {e}")
                    continue
            
            # URL simulada para formato compatible
            if fuente == "DOE":
                url = "https://doe.juntaex.es/ultimosdoe/ (Búsqueda histórica)"
            elif fuente == "BOP":
                url = "https://www.dip-badajoz.es/bop/ (Búsqueda histórica)"
            else:  # BOE
                url = "https://www.boe.es/boe/dias/ (Búsqueda histórica)"
            
            # Formato compatible con sender.py (sin fecha en tupla final)
            announcements_compatible = [(a[0], a[1], a[2], a[3]) for a in found_announcements]
            
            # Mapear nombre de fuente para compatibilidad
            fuente_key = "BOP Badajoz" if fuente == "BOP" else fuente
            results[fuente_key] = (sorted(announcements_compatible, key=lambda x: x[0]), url, [])
        
        return results
    
    def buscar_menciones_historico(self, menciones: List[str], fuentes: List[str],
                                  fecha_inicio: str, fecha_fin: str) -> dict:
        """
        Buscar menciones específicas usando las funciones exactas de sender.py
        pero aplicadas sobre múltiples fechas históricas
        """
        # Obtener todos los boletines HTML del rango
        boletines = self.db.obtener_boletines_rango(fecha_inicio, fecha_fin, fuentes)
        
        results = {}
        
        for fuente in fuentes:
            found_mentions = []
            
            # Filtrar boletines por fuente
            boletines_fuente = [b for b in boletines if b['fuente'] == fuente]
            
            for boletin in boletines_fuente:
                fecha = boletin['fecha']
                html = boletin['contenido_html']
                
                try:
                    # Aplicar función de extracción de menciones según fuente
                    if fuente == "DOE":
                        mentions = extract_doe_mentions(html, menciones)
                    elif fuente == "BOP":
                        mentions = extract_bop_mentions(html, menciones, fecha + "000000")
                    elif fuente == "BOE":
                        mentions = extract_boe_mentions(html, menciones)
                    else:
                        continue
                    
                    # Agregar menciones encontradas
                    found_mentions.extend(mentions)
                            
                except Exception as e:
                    logging.error(f"Error procesando menciones {fuente} {fecha}: {e}")
                    continue
            
            # URL simulada
            if fuente == "DOE":
                url = "https://doe.juntaex.es/ultimosdoe/ (Búsqueda histórica)"
            elif fuente == "BOP":
                url = "https://www.dip-badajoz.es/bop/ (Búsqueda histórica)"
            else:  # BOE
                url = "https://www.boe.es/boe/dias/ (Búsqueda histórica)"
            
            # Mapear nombre de fuente para compatibilidad
            fuente_key = "BOP Badajoz" if fuente == "BOP" else fuente
            results[fuente_key] = ([], url, found_mentions)
        
        return results
    
    def buscar_municipio_y_menciones(self, municipios: List[str], menciones: List[str],
                                   fuentes: List[str], fecha_inicio: str, fecha_fin: str) -> dict:
        """
        Buscar municipios Y/O menciones - Funcionalidad completa como sender.py
        """
        logging.info(f"Búsqueda histórica: {len(municipios)} municipios, {len(menciones)} menciones")
        logging.info(f"Rango: {fecha_inicio} - {fecha_fin}")
        logging.info(f"Fuentes: {fuentes}")
        
        if not municipios and not menciones:
            logging.warning("No hay municipios ni menciones para buscar")
            return {}
        
        # Obtener todos los boletines HTML del rango
        boletines = self.db.obtener_boletines_rango(fecha_inicio, fecha_fin, fuentes)
        
        if not boletines:
            logging.warning("No se encontraron boletines en el rango especificado")
            return {}
        
        logging.info(f"Procesando {len(boletines)} boletines históricos...")
        
        results = {}
        
        for fuente in fuentes:
            found_announcements = []
            found_mentions = []
            
            # Filtrar boletines por fuente
            boletines_fuente = [b for b in boletines if b['fuente'] == fuente]
            logging.info(f"{fuente}: Procesando {len(boletines_fuente)} boletines")
            
            for boletin in boletines_fuente:
                fecha = boletin['fecha']
                html = boletin['contenido_html']
                
                # 1. Buscar municipios
                if municipios:
                    for municipio in municipios:
                        try:
                            if fuente == "DOE":
                                announcements = extract_doe_announcement(html, municipio)
                            elif fuente == "BOP":
                                announcements = extract_bop_announcement(html, municipio, str(fecha) + "000000")
                            elif fuente == "BOE":
                                announcements = extract_boe_announcement(html, municipio, str(fecha))
                            else:
                                continue
                            
                            # Agregar anuncios válidos con fecha
                            for prefix, text, pdf_url in announcements:
                                if text != "No se encontró texto de anuncio específico.":
                                    found_announcements.append((
                                        f"Ayuntamiento de {municipio}",
                                        prefix,
                                        text,
                                        pdf_url,
                                        fecha
                                    ))
                                    
                        except Exception as e:
                            logging.error(f"Error procesando municipio {municipio} en {fuente} {fecha}: {e}")
                            continue
                
                # 2. Buscar menciones
                if menciones:
                    try:
                        if fuente == "DOE":
                            mentions = extract_doe_mentions(html, menciones)
                        elif fuente == "BOP":
                            mentions = extract_bop_mentions(html, menciones, str(fecha) + "000000")
                        elif fuente == "BOE":
                            mentions = extract_boe_mentions(html, menciones)
                        else:
                            continue
                        
                        # Agregar fecha a cada mención encontrada
                        for mention, paragraph, pdf_url in mentions:
                            found_mentions.append((mention, paragraph, pdf_url, fecha))
                                
                    except Exception as e:
                        logging.error(f"Error procesando menciones en {fuente} {fecha}: {e}")
                        continue
            
            # 3. Filtrar duplicados (lógica exacta de sender.py)
            announcement_texts = set()
            for muni_name, prefix, text, pdf_url, fecha in found_announcements:
                announcement_texts.add(normalize_text(muni_name))
                announcement_texts.add(normalize_text(prefix + " " + text))

            unique_mentions = []
            for item in found_mentions:
                if len(item) == 4:  # Con fecha
                    mention, paragraph, pdf_url, fecha = item
                else:  # Sin fecha (compatibilidad)
                    mention, paragraph, pdf_url = item
                    fecha = None
                    
                normalized_paragraph = normalize_text(paragraph)
                is_duplicate = False
                for a_text in announcement_texts:
                    if normalized_paragraph in a_text or a_text in normalized_paragraph:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    if fecha is not None:
                        unique_mentions.append((mention, paragraph, pdf_url, fecha))
                    else:
                        unique_mentions.append((mention, paragraph, pdf_url))
            
            # URL simulada
            if fuente == "DOE":
                url = "https://doe.juntaex.es/ultimosdoe/ (Búsqueda histórica)"
            elif fuente == "BOP":
                url = "https://www.dip-badajoz.es/bop/ (Búsqueda histórica)"
            else:  # BOE
                url = "https://www.boe.es/boe/dias/ (Búsqueda histórica)"
            
            # Mapear nombre para compatibilidad con format_email()
            fuente_key = "BOP Badajoz" if fuente == "BOP" else fuente
            results[fuente_key] = (
                sorted(found_announcements, key=lambda x: x[0]), 
                url, 
                unique_mentions
            )
            
            logging.info(f"{fuente}: {len(found_announcements)} anuncios, {len(unique_mentions)} menciones únicas")
        
        return results

# Función format_email copiada exacta de sender.py
def format_email(results):
    """Formatea el cuerpo del email en HTML (copiado exacto de sender.py)"""
    today_str = datetime.now().strftime("%d/%m/%Y")
    html_content = [
        '<html>',
        '<head><style>',
        'body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 20px; }',
        'h2 { color: #2c3e50; font-size: 24px; text-align: center; border-bottom: 2px solid #ddd; padding-bottom: 10px; }',
        'h3 { color: #34495e; font-size: 20px; margin-top: 20px; margin-bottom: 10px; }',
        'ul { list-style: none; padding-left: 0; }',
        'li { margin-bottom: 20px; }',
        'a.pdf-link { background-color: #e6f0ff; color: #007bff; padding: 5px 10px; border-radius: 3px; text-decoration: none; display: inline-block; }',
        'a.pdf-link:hover { background-color: #cce4ff; }',
        'a.url-link { color: #007bff; text-decoration: none; }',
        'a.url-link:hover { text-decoration: underline; }',
        'hr { border: 0; border-top: 1px solid #ddd; margin: 10px 0; }',
        '.municipality { font-size: 18px; font-weight: bold; padding-left: 10px; border-left: 3px solid #34495e; margin-bottom: 10px; }',
        '.announcement { font-size: 16px; margin-left: 30px; margin-bottom: 10px; padding-left: 10px; }',
        '.fecha-mencion { font-size: 12px; color: #666; font-style: italic; margin-top: 5px; }',
        '.footer { font-size: 12px; color: #666; margin-top: 20px; text-align: center; }',
        '</style></head>',
        '<body>',
        f'<h2>Resumen Búsqueda Histórica - {today_str}</h2>'
    ]
    
    sources = {
        "DOE": "Resultados DOE",
        "BOP Badajoz": "Resultados BOP",
        "BOE": "Resultados BOE"
    }
    
    # Orden específico de aparición: BOE, DOE, BOP
    orden_fuentes = ["BOE", "DOE", "BOP Badajoz"]
    
    for fuente in orden_fuentes:
        if fuente not in results:
            continue
        data = results[fuente]
        html_content.append(f'<h3>{sources[fuente]}</h3>')
        announcements, url, mentions = data
        
        # Filtrar anuncios válidos
        valid_announcements = [a for a in announcements if a[2] != "No se encontró texto de anuncio específico."]
        
        # Si hay anuncios válidos o menciones, mostrar contenido
        if valid_announcements or mentions:
            html_content.append('<ul>')
            
            # Mostrar anuncios de municipios
            if valid_announcements:
                current_muni = None
                for item in valid_announcements:
                    if len(item) == 5:  # Con fecha
                        muni, prefix, text, pdf_url, fecha = item
                        try:
                            fecha_formateada = datetime.strptime(str(fecha), "%Y%m%d").strftime("%d/%m/%Y")
                        except:
                            fecha_formateada = str(fecha)
                    else:  # Sin fecha (compatibilidad)
                        muni, prefix, text, pdf_url = item
                        fecha_formateada = ""
                    
                    if muni != current_muni:
                        if current_muni is not None:
                            html_content.append('</li>')
                        html_content.append(f'<li><div class="municipality">{muni}</div>')
                        current_muni = muni
                    html_content.append('<div class="announcement">')
                    html_content.append(f'{text}')
                    if fecha_formateada:
                        html_content.append(f'<div class="fecha-mencion">📅 Fecha: {fecha_formateada}</div>')
                    if pdf_url:
                        html_content.append(f' <a href="{pdf_url}" class="pdf-link">Ver Publicación</a>')
                    html_content.append('</div>')
                if current_muni is not None:
                    html_content.append('</li>')
            
            # Mostrar menciones
            if mentions:
                for item in mentions:
                    if len(item) == 4:  # Nueva formato con fecha
                        mention, paragraph, pdf_url, fecha = item
                        # Formatear fecha para mostrar
                        try:
                            fecha_formateada = datetime.strptime(str(fecha), "%Y%m%d").strftime("%d/%m/%Y")
                        except:
                            fecha_formateada = str(fecha)
                    else:  # Formato anterior sin fecha
                        mention, paragraph, pdf_url = item
                        fecha_formateada = ""
                    
                    html_content.append(f'<li><div class="municipality">Mención: {mention}</div>')
                    html_content.append('<div class="announcement">')
                    html_content.append(f'{paragraph}')
                    if fecha_formateada:
                        html_content.append(f'<div class="fecha-mencion">📅 Fecha: {fecha_formateada}</div>')
                    if pdf_url:
                        html_content.append(f' <a href="{pdf_url}" class="pdf-link">Ver Publicación</a>')
                    html_content.append('</div></li>')
            
            html_content.append('</ul>')
        else:
            html_content.append('<p>Sin resultados para el período consultado</p>')
        
        html_content.append(f'<p><strong>Enlace consultado:</strong> <a href="{url}" class="url-link">{url}</a></p>')
        html_content.append('<hr>')
    
    html_content.append('<div class="footer">')
    html_content.append('<p>Este reporte ha sido generado por búsqueda histórica en boletines oficiales.</p>')
    html_content.append('</div>')
    html_content.append('</body>')
    html_content.append('</html>')
    
    return "\n".join(html_content)