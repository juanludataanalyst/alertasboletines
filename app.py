import streamlit as st
from auth import show_auth_page
from supabase_client import supabase
import datetime
import time
from main import ejecutar_busqueda_para_usuario # Importar la función

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Alertas de Boletines", page_icon="🔔", layout="wide")

# --- CARGAR CSS EXTERNO ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("style.css")

# --- LISTAS DE DATOS ---
MUNICIPIOS_BADAJOZ = [
    "Acedera", "Aceuchal", "Ahillones", "Alange", "La Albuera", "Alburquerque",
    "Alconchel", "Alconera", "Aljucén", "Almendral", "Almendralejo", "Arroyo de San Serván",
    "Atalaya", "Azuaga", "Badajoz", "Barcarrota", "Baterno", "Benquerencia de la Serena",
    "Berlanga", "Bienvenida", "Bodonal de la Sierra", "Burguillos del Cerro", "Cabeza del Buey",
    "Cabeza la Vaca", "Calamonte", "Calera de León", "Calzadilla de los Barros", "Campanario",
    "Campillo de Llerena", "Capilla", "Carmonita", "El Carrascalejo", "Casas de Don Pedro",
    "Casas de Reina", "Castilblanco", "Castuera", "Cheles", "La Codosera", "Cordobilla de Lácara",
    "La Coronada", "Corte de Peleas", "Cristina", "Don Álvaro", "Don Benito", "Entrín Bajo",
    "Esparragalejo", "Esparragosa de la Serena", "Esparragosa de Lares", "Feria", "Fregenal de la Sierra",
    "Fuenlabrada de los Montes", "Fuente de Cantos", "Fuente del Arco", "Fuente del Maestre",
    "Fuentes de León", "Galizuela", "Garbayuela", "Garlitos", "La Garrovilla", "Granja de Torrehermosa",
    "Guareña", "La Haba", "Helechosa de los Montes", "Herrera del Duque", "Higuera de la Serena",
    "Higuera de Llerena", "Higuera de Vargas", "Higuera la Real", "Hinojosa del Valle", "Hornachos",
    "Jerez de los Caballeros", "La Lapa", "Llera", "Llerena", "Lobón", "Magacela", "Maguilla",
    "Malcocinado", "Malpartida de la Serena", "Manchita", "Medellín", "Medina de las Torres",
    "Mengabril", "Mérida", "Mirandilla", "Monesterio", "Montemolín", "Monterrubio de la Serena",
    "Montijo", "La Morera", "La Nava de Santiago", "Navalvillar de Pela", "Nogales",
    "Oliva de la Frontera", "Oliva de Mérida", "Olivenza", "Orellana de la Sierra", "Orellana la Vieja",
    "Palomas", "La Parra", "Peñalsordo", "Peraleda del Zaucejo", "Puebla de Alcocer",
    "Puebla de la Calzada", "Puebla de la Reina", "Puebla de Obando", "Puebla de Sancho Pérez",
    "Puebla del Maestre", "Puebla del Prior", "Pueblonuevo del Guadiana", "Quintana de la Serena",
    "Reina", "Rena", "Retamal de Llerena", "Ribera del Fresno", "Risco", "La Roca de la Sierra",
    "Salvaleón", "Salvatierra de los Barros", "San Pedro de Mérida", "San Vicente de Alcántara",
    "Sancti-Spíritus", "Santa Amalia", "Santa Marta", "Los Santos de Maimona", "Segura de León",
    "Siruela", "Solana de los Barros", "Talarrubias", "Talavera la Real", "Táliga", "Tamurejo",
    "Torre de Miguel Sesmero", "Torremayor", "Torremejía", "Trasierra", "Trujillanos", "Usagre",
    "Valdecaballeros", "Valdelacalzada", "Valdetorres", "Valencia de las Torres", "Valencia del Mombuey",
    "Valencia del Ventoso", "Valle de la Serena", "Valle de Matamoros", "Valle de Santa Ana",
    "Valverde de Burguillos", "Valverde de Leganés", "Valverde de Llerena", "Valverde de Mérida",
    "Villafranca de los Barros", "Villagarcía de la Torre", "Villagonzalo", "Villalba de los Barros",
    "Villanueva de la Serena", "Villanueva del Fresno", "Villar de Rena", "Villar del Rey",
    "Villarta de los Montes", "Zafra", "Zahínos", "Zalamea de la Serena", "La Zarza",
    "Zarza-Capilla"
]
BOLETINES = ["DOE", "BOP", "BOE"]

# --- PANEL DE CONTROL (DASHBOARD) ---
def show_dashboard():
    user_email = st.session_state.user['email']
    user_id = st.session_state.user['id']

    # --- Barra de Navegación Superior ---
    with st.container():
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            st.title("Alertas de Boletines Oficiales")
            st.caption(f"Bienvenido, {user_email}")
        with col2:
            if st.button("Cerrar Sesión"):
                del st.session_state.user
                st.rerun()
    st.markdown("<hr style='margin-top: 0;'/>", unsafe_allow_html=True)

    # --- Contenido Principal Centrado ---
    _, main_col, _ = st.columns([1, 3, 1])
    with main_col:
        # --- Cargar preferencias ---
        try:
            response = supabase.table('preferencias').select('*').eq('user_id', user_id).single().execute()
            preferencias = response.data
        except Exception:
            preferencias = {}

        # --- Lógica y estado de la suscripción ---
        suscripcion_hasta_str = preferencias.get('suscripcion_activa_hasta')
        suscripcion_activa = False
        if suscripcion_hasta_str:
            try:
                suscripcion_hasta = datetime.datetime.strptime(suscripcion_hasta_str, '%Y-%m-%d').date()
                if suscripcion_hasta >= datetime.date.today():
                    suscripcion_activa = True
            except (ValueError, TypeError):
                st.error("Error en la fecha de suscripción.")

        # --- Formulario de configuración ---
        with st.container():
            st.header("⚙️ Mis Preferencias")
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                if suscripcion_activa:
                    st.success(f"Suscripción activa hasta el {suscripcion_hasta.strftime('%d/%m/%Y')}.")
                else:
                    st.warning("Suscripción caducada o no activa.")
            with col2:
                pass  ## Aqui ira el boton de renovar suscripcion

            st.markdown("Ajusta tus suscripciones y notificaciones.")

            with st.expander("Suscripciones a Boletines", expanded=True):
                st.subheader("📍 Municipios")
                municipios_guardados = preferencias.get('municipios', []) or []
                municipios_seleccionados = st.multiselect(
                    "Selecciona los municipios para monitorizar:",
                    options=MUNICIPIOS_BADAJOZ,
                    default=municipios_guardados
                )
                st.subheader("📰 Boletines")
                boletines_guardados = preferencias.get('boletines', []) or []
                b1 = st.checkbox("Diario Oficial de Extremadura (DOE)", value=("DOE" in boletines_guardados))
                b2 = st.checkbox("Boletín Oficial de la Provincia (BOP)", value=("BOP" in boletines_guardados))
                b3 = st.checkbox("Boletín Oficial del Estado (BOE)", value=("BOE" in boletines_guardados))

            with st.expander("📝 Mis Menciones", expanded=True):
                st.subheader("Palabras Clave Guardadas")
                menciones_guardadas = preferencias.get('menciones', []) or []
                menciones_seleccionadas_existentes = st.multiselect(
                    "Tus palabras clave actuales. Desmárcalas para eliminarlas.",
                    options=menciones_guardadas,
                    default=menciones_guardadas
                )

                st.subheader("Añadir Nuevas Palabras Clave")
                nuevas_menciones_texto = st.text_area(
                    "Escribe nuevas palabras clave separadas por comas:",
                    placeholder="Ej: fondos europeos, digitalización, pymes"
                )

            with st.expander("Configuración de Notificaciones", expanded=True):
                st.subheader("📧 Opciones de Envío")
                hora_guardada_str = preferencias.get('hora_envio') or '08:00:00'
                hora_guardada = datetime.datetime.strptime(hora_guardada_str, '%H:%M:%S').time()
                hora_seleccionada = st.time_input("Hora de envío del correo:", value=hora_guardada, step=3600)

                email_guardado = preferencias.get('email', user_email)
                email_seleccionado = st.text_input("Email para recibir las alertas:", value=email_guardado)

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Guardar Cambios", use_container_width=True):
                boletines_seleccionados = []
                if b1: boletines_seleccionados.append("DOE")
                if b2: boletines_seleccionados.append("BOP")
                if b3: boletines_seleccionados.append("BOE")

                # Procesa las menciones para guardarlas como una lista de strings
                nuevas_menciones = [m.strip() for m in nuevas_menciones_texto.split(',') if m.strip()]
                menciones_finales = sorted(list(set(menciones_seleccionadas_existentes + nuevas_menciones)))

                fecha_suscripcion_final = str(suscripcion_hasta) if suscripcion_activa else str(datetime.date.today() + datetime.timedelta(days=30))

                try:
                    datos_para_guardar = {
                        "user_id": user_id,
                        "municipios": municipios_seleccionados,
                        "boletines": boletines_seleccionados,
                        "menciones": menciones_finales,
                        "hora_envio": str(hora_seleccionada),
                        "email": email_seleccionado,
                        "suscripcion_activa_hasta": fecha_suscripcion_final
                    }
                    supabase.table('preferencias').upsert(datos_para_guardar, on_conflict='user_id').execute()
                    st.success("¡Tus preferencias se han guardado con éxito!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudieron guardar los cambios: {e}")

        st.markdown("<hr style='margin: 2rem 0;'/>", unsafe_allow_html=True)

        st.header("🚀 Probar Alerta")
        if st.button("Enviar Email Ahora", use_container_width=True, disabled=not suscripcion_activa):
            with st.spinner("Buscando en los boletines... Esto puede tardar un minuto."):
                municipios = preferencias.get('municipios', [])
                boletines = preferencias.get('boletines', [])
                menciones = preferencias.get('menciones', [])
                mensaje, exito = ejecutar_busqueda_para_usuario(user_email, municipios, boletines, menciones)
                if exito:
                    st.success(mensaje)
                else:
                    st.error(mensaje)
        if not suscripcion_activa:
            st.warning("Necesitas una suscripción activa para realizar búsquedas.")

# --- LÓGICA PRINCIPAL ---
def main():
    if 'user' not in st.session_state:
        show_auth_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
