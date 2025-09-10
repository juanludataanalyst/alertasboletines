import unicodedata
from bs4 import BeautifulSoup
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def normalize_text(text):
    """Normalizar texto para comparaciones (copiado exacto de sender.py)"""
    if not text: return ""
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                   if not unicodedata.combining(c)).lower()

# --- FUNCIONES DE EXTRACCIÓN COPIADAS EXACTAS DE SENDER.PY ---

def extract_doe_announcement(html, municipality):
    """Copiado exacto de sender.py"""
    soup = BeautifulSoup(html, 'html.parser')
    normalized_muni = normalize_text(f"Ayuntamiento de {municipality}")
    announcements = []
    found_muni = False
    for p in soup.find_all('p'):
        doe2_span = p.find('span', class_='DOE2')
        if doe2_span and normalized_muni in normalize_text(doe2_span.text):
            found_muni = True
            logging.info(f"Encontrado municipio {municipality} en DOE")
            continue
        if found_muni:
            div = p.find_parent('div', class_='justificado')
            if div:
                doe4_span = p.find('span', class_='DOE4')
                if doe4_span:
                    doe2_span = p.find('span', class_='DOE2')
                    prefix = doe2_span.text.strip() + ".-" if doe2_span else ""
                    text = doe4_span.text.strip()
                    pdf_link = p.find('a', class_='enlace_dis')
                    pdf_url = f"https://doe.juntaex.es{pdf_link['href']}" if pdf_link else None
                    announcements.append((prefix, text, pdf_url))
                if doe2_span and normalize_text(doe2_span.text) != normalized_muni:
                    break
    if not announcements:
        logging.info(f"No se encontraron anuncios para {municipality} en DOE")
        announcements = [("", "No se encontró texto de anuncio específico.", None)]
    return announcements

def extract_bop_announcement(html, municipality, fecha):
    """Copiado exacto de sender.py"""
    soup = BeautifulSoup(html, 'html.parser')
    normalized_muni = normalize_text(f"Ayuntamiento de {municipality}")
    announcements = []
    found_muni = False
    first_admin_local_passed = False
    logging.info(f"Buscando anuncios para {municipality} en BOP Badajoz")
    
    for element in soup.find_all(['p', 'article']):
        # Parar después de la primera sección "Administración Local"
        if element.name == 'p' and 'nivel1' in element.get('class', []):
            element_text = normalize_text(element.text)
            if 'administracion local' in element_text:
                if first_admin_local_passed:
                    # Ya pasamos la primera sección, paramos
                    break
                else:
                    first_admin_local_passed = True
                    continue
            elif first_admin_local_passed and 'administracion' not in element_text:
                # Si ya pasamos Administración Local y encontramos otra sección, paramos
                break
        
        # Lógica original: buscar municipios
        if element.name == 'p' and 'nivel3' in element.get('class', []) and normalized_muni in normalize_text(element.text):
            found_muni = True
            logging.info(f"Encontrado municipio {municipality} en BOP Badajoz")
            continue
            
        # Lógica original: capturar artículos
        if found_muni and element.name == 'article' and element.find('dl'):
            dt = element.find('dt')
            dd = element.find('dd')
            if dt and dd:
                code = dt.text.strip('[] ').strip()
                link = dd.find('a')
                title = link.text.strip() if link else ""
                pdf_url = f"https://www.dip-badajoz.es/bop/ventana_boletin_completo.php?FechaSolicitada={fecha}#Anuncio_{code}" if link else None
                announcements.append(("", title, pdf_url))
        
        # Lógica original: resetear found_muni
        if found_muni and element.name == 'p' and ('nivel3' in element.get('class', []) or 'nivel2' in element.get('class', [])):
            if normalized_muni not in normalize_text(element.text):
                found_muni = False
                
    if not announcements:
        logging.info(f"No se encontraron anuncios para {municipality} en BOP Badajoz")
        announcements = [("", "No se encontró texto de anuncio específico.", None)]
    return announcements

def extract_boe_announcement(html, municipality, fecha):
    """Copiado exacto de sender.py"""
    soup = BeautifulSoup(html, 'html.parser')
    normalized_muni = normalize_text(f"Ayuntamiento de {municipality}")
    announcements = []
    logging.info(f"Buscando anuncios para {municipality} en BOE")
    for li in soup.find_all('li', class_='dispo'):
        p_tag = li.find('p')
        if not p_tag:
            continue
        text = p_tag.get_text(strip=True)
        if normalized_muni in normalize_text(text):
            main_text = text.strip()
            pdf_link = li.find('li', class_='puntoPDF')
            pdf_url = None
            if pdf_link and pdf_link.find('a'):
                href = pdf_link.find('a')['href']
                pdf_url = f"https://www.boe.es{href}" if href.startswith('/boe') else href
            announcements.append(("", main_text, pdf_url))
    if not announcements:
        logging.info(f"No se encontraron anuncios para {municipality} en BOE")
        announcements = [("", "No se encontró texto de anuncio específico.", None)]
    return announcements

def extract_bop_mentions(html, mentions, fecha):
    """Modificado para búsqueda múltiple AND"""
    soup = BeautifulSoup(html, 'html.parser')
    found_mentions = []
    
    # Buscar solo dentro del contenedor sumario_dinamico
    container = soup.find('div', id='sumario_dinamico')
    if not container:
        logging.warning("No se encontró el contenedor 'sumario_dinamico' en BOP Badajoz")
        return found_mentions

    for article in container.find_all('article'):
        article_text = article.get_text()
        normalized_article_text = normalize_text(article_text)
        
        for mention in mentions:
            # Separar por comas para búsqueda múltiple
            palabras = [p.strip() for p in mention.split(',') if p.strip()]
            
            # Verificar que TODAS las palabras estén presentes (AND)
            if all(normalize_text(palabra) in normalized_article_text for palabra in palabras):
                dt = article.find('dt')
                dd = article.find('dd')
                if dt and dd:
                    code = dt.text.strip('[] ').strip()
                    link = dd.find('a')
                    title = link.text.strip() if link else ""
                    pdf_url = f"https://www.dip-badajoz.es/bop/ventana_boletin_completo.php?FechaSolicitada={fecha}#Anuncio_{code}" if link else None
                    logging.info(f"Encontrada mención múltiple '{mention}' en BOP Badajoz")
                    found_mentions.append((mention, title, pdf_url))
    
    if not found_mentions:
        logging.info("No se encontraron menciones múltiples en BOP Badajoz")
    
    return found_mentions

def extract_doe_mentions(html, mentions):
    """Modificado para búsqueda múltiple AND"""
    soup = BeautifulSoup(html, 'html.parser')
    found_mentions = []
    
    for mention in mentions:
        # Separar por comas para búsqueda múltiple
        palabras = [p.strip() for p in mention.split(',') if p.strip()]
        
        for p in soup.find_all('p'):
            paragraph_text = p.get_text()
            normalized_paragraph = normalize_text(paragraph_text)
            
            # Verificar que TODAS las palabras estén presentes (AND)
            palabras_normalizadas = [normalize_text(palabra) for palabra in palabras]
            palabras_encontradas = [palabra_norm for palabra_norm in palabras_normalizadas if palabra_norm in normalized_paragraph]
            
            if len(palabras_encontradas) == len(palabras_normalizadas):
                logging.info(f"Encontrada mención múltiple '{mention}' en DOE")
                
                # Buscar el enlace al PDF asociado al anuncio
                pdf_url = None
                div = p.find_parent('div', class_='justificado')
                if div:
                    pdf_link = div.find('a', class_='enlace_dis')
                    if pdf_link and pdf_link.has_attr('href'):
                        pdf_url = f"https://doe.juntaex.es{pdf_link['href']}"

                found_mentions.append((mention, paragraph_text.strip(), pdf_url))
    
    return found_mentions

def extract_boe_mentions(html, mentions):
    """Modificado para búsqueda múltiple AND"""
    soup = BeautifulSoup(html, 'html.parser')
    found_mentions = []
    
    for li in soup.find_all('li', class_='dispo'):
        p_tag = li.find('p')
        if not p_tag:
            continue
        text = p_tag.get_text(strip=True)
        normalized_text = normalize_text(text)
        
        for mention in mentions:
            # Separar por comas para búsqueda múltiple
            palabras = [p.strip() for p in mention.split(',') if p.strip()]
            
            # Debug: mostrar qué se está buscando
            palabras_normalizadas = [normalize_text(palabra) for palabra in palabras]
            
            # Verificar que TODAS las palabras estén presentes (AND)
            palabras_encontradas = [palabra_norm for palabra_norm in palabras_normalizadas if palabra_norm in normalized_text]
            
            if len(palabras_encontradas) == len(palabras_normalizadas):
                pdf_link = li.find('li', class_='puntoPDF')
                pdf_url = None
                if pdf_link and pdf_link.find('a'):
                    href = pdf_link.find('a')['href']
                    pdf_url = f"https://www.boe.es{href}" if href.startswith('/boe') else href
                logging.info(f"Encontrada mención múltiple '{mention}' en BOE")
                found_mentions.append((mention, text.strip(), pdf_url))
    
    return found_mentions