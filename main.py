import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import unicodedata
from bs4 import BeautifulSoup
import logging

from dotenv import load_dotenv
import os

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de correo
SENDER_EMAIL = "juanludataanalyst@gmail.com"
APP_PASSWORD = os.environ.get("APP_PASSWORD") 

def normalize_text(text):
    if not text: return ""
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                   if not unicodedata.combining(c)).lower()

# --- FUNCIONES DE EXTRACCIÓN ---
def extract_doe_announcement(html, municipality):
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
    soup = BeautifulSoup(html, 'html.parser')
    normalized_muni = normalize_text(f"Ayuntamiento de {municipality}")
    announcements = []
    found_muni = False
    logging.info(f"Buscando anuncios para {municipality} en BOP Badajoz")
    for element in soup.find_all(['p', 'article']):
        if element.name == 'p' and 'nivel3' in element.get('class', []) and normalized_muni in normalize_text(element.text):
            found_muni = True
            logging.info(f"Encontrado municipio {municipality} en BOP Badajoz")
            continue
        if found_muni and element.name == 'article' and element.find('dl'):
            dt = element.find('dt')
            dd = element.find('dd')
            if dt and dd:
                code = dt.text.strip('[] ').strip()
                link = dd.find('a')
                title = link.text.strip() if link else ""
                pdf_url = f"https://www.dip-badajoz.es/bop/ventana_boletin_completo.php?FechaSolicitada={fecha}#Anuncio_{code}" if link else None
                announcements.append(("", title, pdf_url))
        if found_muni and element.name == 'p' and ('nivel3' in element.get('class', []) or 'nivel2' in element.get('class', [])):
            if normalized_muni not in normalize_text(element.text):
                 found_muni = False
    if not announcements:
        logging.info(f"No se encontraron anuncios para {municipality} en BOP Badajoz")
        announcements = [("", "No se encontró texto de anuncio específico.", None)]
    return announcements

def extract_boe_announcement(html, municipality, fecha):
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
            if normalize_text(mention) in normalized_article_text:
                dt = article.find('dt')
                dd = article.find('dd')
                if dt and dd:
                    code = dt.text.strip('[] ').strip()
                    link = dd.find('a')
                    title = link.text.strip() if link else ""
                    pdf_url = f"https://www.dip-badajoz.es/bop/ventana_boletin_completo.php?FechaSolicitada={fecha}#Anuncio_{code}" if link else None
                    logging.info(f"Encontrada mención '{mention}' en BOP Badajoz (sumario_dinamico)")
                    found_mentions.append((mention, title, pdf_url))
    
    if not found_mentions:
        logging.info("No se encontraron menciones en el sumario_dinamico de BOP Badajoz")
    
    return found_mentions

def extract_doe_mentions(html, mentions):
    soup = BeautifulSoup(html, 'html.parser')
    found_mentions = []
    for mention in mentions:
        normalized_mention = normalize_text(mention)
        for p in soup.find_all('p'):
            paragraph_text = p.get_text()
            if normalized_mention in normalize_text(paragraph_text):
                logging.info(f"Encontrada mención '{mention}' en DOE")
                
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
    soup = BeautifulSoup(html, 'html.parser')
    found_mentions = []
    for li in soup.find_all('li', class_='dispo'):
        p_tag = li.find('p')
        if not p_tag:
            continue
        text = p_tag.get_text(strip=True)
        normalized_text = normalize_text(text)
        for mention in mentions:
            if normalize_text(mention) in normalized_text:
                pdf_link = li.find('li', class_='puntoPDF')
                pdf_url = None
                if pdf_link and pdf_link.find('a'):
                    href = pdf_link.find('a')['href']
                    pdf_url = f"https://www.boe.es{href}" if href.startswith('/boe') else href
                logging.info(f"Encontrada mención '{mention}' en BOE")
                found_mentions.append((mention, text.strip(), pdf_url))
    return found_mentions

# --- FUNCIONES DE COMPROBACIÓN ---
def check_doe(municipalities, mentions):
    fecha = datetime.now().strftime("%Y%m%d")
    url = f"https://doe.juntaex.es/ultimosdoe/mostrardoe.php?fecha={fecha}&t=o"
    logging.info(f"Comprobando DOE: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
        html_normalized = normalize_text(html)
        
        # 1. Encontrar anuncios de municipios
        found_announcements = []
        for muni in municipalities:
            if normalize_text(f"Ayuntamiento de {muni}") in html_normalized:
                announcements = extract_doe_announcement(html, muni)
                for prefix, text, pdf_url in announcements:
                    found_announcements.append((f"Ayuntamiento de {muni}", prefix, text, pdf_url))
        
        # 2. Encontrar todas las menciones
        found_mentions = extract_doe_mentions(html, mentions)

        # 3. Filtrar menciones para evitar duplicados
        announcement_texts = set()
        for muni_name, prefix, text, pdf_url in found_announcements:
            announcement_texts.add(normalize_text(muni_name))
            announcement_texts.add(normalize_text(prefix + " " + text)) # Include prefix and text

        unique_mentions = []
        for mention, paragraph, pdf_url in found_mentions:
            normalized_paragraph = normalize_text(paragraph)
            is_duplicate = False
            for a_text in announcement_texts:
                if normalized_paragraph in a_text or a_text in normalized_paragraph: # Check for substring
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_mentions.append((mention, paragraph, pdf_url))

        return sorted(found_announcements, key=lambda x: x[0]), url, unique_mentions
    except requests.RequestException as e:
        logging.error(f"Error al acceder al DOE: {e}")
        return [], url, []

def check_bop_badajoz(municipalities, mentions):
    fecha = datetime.now().strftime("%Y%m%d") + "000000"
    url = f"https://www.dip-badajoz.es/bop/ventana_boletin_completo.php?FechaSolicitada={fecha}"
    logging.info(f"Comprobando BOP Badajoz: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
        html_normalized = normalize_text(html)
        
        # 1. Encontrar anuncios de municipios
        found_announcements = []
        for muni in municipalities:
            if normalize_text(f"Ayuntamiento de {muni}") in html_normalized:
                announcements = extract_bop_announcement(html, muni, fecha)
                for prefix, text, pdf_url in announcements:
                    found_announcements.append((f"Ayuntamiento de {muni}", prefix, text, pdf_url))
        
        # 2. Encontrar todas las menciones
        found_mentions = extract_bop_mentions(html, mentions, fecha)

        # 3. Filtrar menciones para evitar duplicados
        announcement_texts = set()
        for muni_name, prefix, text, pdf_url in found_announcements:
            announcement_texts.add(normalize_text(muni_name))
            announcement_texts.add(normalize_text(prefix + " " + text)) # Include prefix and text

        unique_mentions = []
        for mention, paragraph, pdf_url in found_mentions:
            normalized_paragraph = normalize_text(paragraph)
            is_duplicate = False
            for a_text in announcement_texts:
                if normalized_paragraph in a_text or a_text in normalized_paragraph: # Check for substring
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_mentions.append((mention, paragraph, pdf_url))

        return sorted(found_announcements, key=lambda x: x[0]), url, unique_mentions
    except requests.RequestException as e:
        logging.error(f"Error al acceder al BOP Badajoz: {e}")
        return [], url, []

def check_boe(municipalities, mentions):
    fecha = datetime.now().strftime("%Y/%m/%d")
    url = f"https://www.boe.es/boe/dias/{fecha}/"
    logging.info(f"Comprobando BOE: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
        html_normalized = normalize_text(html)
        
        # 1. Encontrar anuncios de municipios
        found_announcements = []
        for muni in municipalities:
            if normalize_text(f"Ayuntamiento de {muni}") in html_normalized:
                announcements = extract_boe_announcement(html, muni, fecha)
                for prefix, text, pdf_url in announcements:
                    found_announcements.append((f"Ayuntamiento de {muni}", prefix, text, pdf_url))
        
        # 2. Encontrar todas las menciones
        found_mentions = extract_boe_mentions(html, mentions)

        # 3. Filtrar menciones para evitar duplicados
        announcement_texts = set()
        for muni_name, prefix, text, pdf_url in found_announcements:
            announcement_texts.add(normalize_text(muni_name))
            announcement_texts.add(normalize_text(prefix + " " + text)) # Include prefix and text

        unique_mentions = []
        for mention, paragraph, pdf_url in found_mentions:
            normalized_paragraph = normalize_text(paragraph)
            is_duplicate = False
            for a_text in announcement_texts:
                if normalized_paragraph in a_text or a_text in normalized_paragraph: # Check for substring
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_mentions.append((mention, paragraph, pdf_url))

        return sorted(found_announcements, key=lambda x: x[0]), url, unique_mentions
    except requests.RequestException as e:
        logging.error(f"Error al acceder al BOE: {e}")
        return [], url, []

# Formatea el cuerpo del email en HTML
def format_email(results):
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
        '.footer { font-size: 12px; color: #666; margin-top: 20px; text-align: center; }',
        '</style></head>',
        '<body>',
        f'<h2>Resumen Automático de Publicaciones Oficiales - {today_str}</h2>'
    ]
    
    sources = {
        "DOE": "Municipios nombrados en DOE",
        "BOP Badajoz": "Municipios nombrados en BOP Badajoz",
        "BOE": "Municipios nombrados en BOE"
    }

    mention_sources = {
        "DOE": "DOE",
        "BOP Badajoz": "BOP Badajoz",
        "BOE": "BOE"
    }
    
    for fuente, data in results.items():
        html_content.append(f'<h3>{sources[fuente]}</h3>')
        announcements, url, mentions = data
        # This logic is from your original script.
        # It filters out placeholder announcements before displaying.
        valid_announcements = [a for a in announcements if a[1] != "No se encontró texto de anuncio específico."]

        if valid_announcements:
            html_content.append('<ul>')
            current_muni = None
            for muni, prefix, text, pdf_url in valid_announcements:
                if muni != current_muni:
                    if current_muni is not None:
                        html_content.append('</li>')
                    html_content.append(f'<li><div class="municipality">{muni}</div>')
                    current_muni = muni
                html_content.append('<div class="announcement">')
                html_content.append(f'{text}')
                if pdf_url:
                    html_content.append(f' <a href="{pdf_url}" class="pdf-link">Ver Publicación</a>')
                html_content.append('</div>')
            if current_muni is not None:
                html_content.append('</li>')
            html_content.append('</ul>')
            html_content.append(f'<p><strong>Enlace consultado:</strong> <a href="{url}" class="url-link">{url}</a></p>')
            html_content.append('<br>')
        else:
            html_content.append('<p>Ningún municipio nombrado hoy</p>')
            html_content.append(f'<p><strong>Enlace consultado:</strong> <a href="{url}" class="url-link">{url}</a></p>')
            html_content.append('<br>')
        html_content.append('<hr>')

        if mentions:
            html_content.append(f'<h3>Menciones Encontradas en {mention_sources[fuente]}</h3>')
            html_content.append('<ul>')
            for mention, paragraph, pdf_url in mentions:
                html_content.append(f'<li><div class="municipality">Mención: {mention}</div>')
                html_content.append('<div class="announcement">')
                html_content.append(f'{paragraph}')
                if pdf_url:
                    html_content.append(f' <a href="{pdf_url}" class="pdf-link">Ver Publicación</a>')
                html_content.append('</div></li>')
            html_content.append('</ul>')
            html_content.append('<br>')
    
    html_content.append('<div class="footer">')
    html_content.append('<p>Este correo ha sido generado automáticamente por un servicio de monitoreo de boletines oficiales.</p>')
    html_content.append('</div>')
    html_content.append('</body>')
    html_content.append('</html>')
    
    return "\n".join(html_content)

def send_email(body, recipient_email):
    today_str = datetime.now().strftime("%d/%m/%Y")
    subject = f"Alertas de Boletines Oficiales 3 - {today_str}"
    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        logging.info(f"✅ Email enviado correctamente a {recipient_email}.")
        return True
    except Exception as e:
        logging.error(f"❌ Error enviando email a {recipient_email}: {e}")
        return False

# --- FUNCIÓN PRINCIPAL REUTILIZABLE ---
def ejecutar_busqueda_para_usuario(email, municipios, boletines, menciones):
    logging.info(f"--- Ejecutando búsqueda bajo demanda para: {email} ---")
    if not municipios and not menciones:
        logging.warning("No hay municipios o menciones configurados.")
        return "Configura tus municipios y/o menciones antes de ejecutar la búsqueda.", False

    results = {}
    if "DOE" in boletines:
        results["DOE"] = check_doe(municipios, menciones)
    if "BOP" in boletines:
        results["BOP Badajoz"] = check_bop_badajoz(municipios, menciones)
    if "BOE" in boletines:
        results["BOE"] = check_boe(municipios, menciones)
    
    cuerpo_email = format_email(results)
    logging.info(f"Cuerpo del email para {email}:\n{cuerpo_email}")
    
    email_sent = send_email(cuerpo_email, email)
    
    if email_sent:
        return "Búsqueda completada. Se ha enviado un correo con los resultados.", True
    else:
        return "Búsqueda completada, pero hubo un error al enviar el correo.", False