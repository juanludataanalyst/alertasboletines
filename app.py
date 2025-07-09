import streamlit as st
from auth import show_auth_page
from supabase_client import supabase
import json
import datetime

st.set_page_config(page_title="Alertas de Boletines", page_icon=":bell:")

# Lista de municipios (reemplazar con la lista completa)
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

# Función para el panel de control (dashboard)
def show_dashboard():
    st.title("Panel de Control")
    st.write(f"Bienvenido, {st.session_state.user['email']}")
    user_id = st.session_state.user['id']

    # Cargar preferencias existentes
    try:
        response = supabase.table('preferencias').select('*').eq('user_id', user_id).single().execute()
        preferencias = response.data
    except Exception as e:
        preferencias = {} # No hay preferencias o hay un error

    st.header("Configuración de Preferencias")

    # Selector de municipios
    municipios_guardados = preferencias.get('municipios', []) or []
    municipios_seleccionados = st.multiselect(
        "Elige los municipios para recibir alertas:",
        options=MUNICIPIOS_BADAJOZ,
        default=municipios_guardados
    )

    # Selector de boletines con checkboxes
    st.write("Elige los boletines a los que suscribirte:")
    boletines_guardados = preferencias.get('boletines', []) or []
    
    b1 = st.checkbox("DOE", value=("DOE" in boletines_guardados))
    b2 = st.checkbox("BOP", value=("BOP" in boletines_guardados))
    b3 = st.checkbox("BOE", value=("BOE" in boletines_guardados))

    # Selector de hora
    hora_guardada_str = preferencias.get('hora_envio', '08:00:00')
    hora_guardada = datetime.datetime.strptime(hora_guardada_str, '%H:%M:%S').time()
    hora_seleccionada = st.time_input("Elige la hora para recibir el correo:", value=hora_guardada)

    # Campo para el email de envío
    email_guardado = preferencias.get('email', st.session_state.user['email'])
    email_seleccionado = st.text_input("Email para recibir las alertas:", value=email_guardado)

    if st.button("Guardar Preferencias"):
        # Recopilar boletines seleccionados de los checkboxes
        boletines_seleccionados = []
        if b1: boletines_seleccionados.append("DOE")
        if b2: boletines_seleccionados.append("BOP")
        if b3: boletines_seleccionados.append("BOE")

        try:
            # Usamos upsert para insertar o actualizar las preferencias
            datos_para_guardar = {
                "user_id": user_id,
                "municipios": municipios_seleccionados,
                "boletines": boletines_seleccionados,
                "hora_envio": str(hora_seleccionada),
                "email": email_seleccionado
            }
            supabase.table('preferencias').upsert(datos_para_guardar, on_conflict='user_id').execute()
            st.success("¡Preferencias guardadas con éxito!")
        except Exception as e:
            st.error(f"Error al guardar las preferencias: {e}")

    if st.button("Cerrar Sesión", key="logout_dashboard"):
        del st.session_state.user
        st.rerun()

# Lógica principal de la aplicación
def main():
    if 'user' not in st.session_state:
        show_auth_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
