import streamlit as st
from auth import show_auth_page
from supabase_client import supabase
import datetime
import time
from main import ejecutar_busqueda_para_usuario

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

def show_alertas_tab():
    # --- PANEL DE CONTROL (DASHBOARD) ---
    user_email = st.session_state.user['email']
    user_id = st.session_state.user['id']

    st.header("🔔 Configuración de Alertas")
    st.markdown("Configura tus suscripciones para recibir alertas automáticas por email")

    # --- Contenido Principal ---
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
    st.subheader("⚙️ Mis Preferencias")
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        if suscripcion_activa:
            st.success(f"Suscripción activa hasta el {suscripcion_hasta.strftime('%d/%m/%Y')}.")
        else:
            st.warning("Suscripción caducada o no activa.")

    with st.expander("Suscripciones a Boletines", expanded=True):
        st.write("**📍 Municipios**")
        municipios_guardados = preferencias.get('municipios', []) or []
        municipios_seleccionados = st.multiselect(
            "Selecciona los municipios para monitorizar:",
            options=MUNICIPIOS_BADAJOZ,
            default=municipios_guardados
        )
        st.write("**📰 Boletines**")
        boletines_guardados = preferencias.get('boletines', []) or []
        b1 = st.checkbox("Diario Oficial de Extremadura (DOE)", value=("DOE" in boletines_guardados))
        b2 = st.checkbox("Boletín Oficial de la Provincia (BOP)", value=("BOP" in boletines_guardados))
        b3 = st.checkbox("Boletín Oficial del Estado (BOE)", value=("BOE" in boletines_guardados))

    with st.expander("📝 Mis Menciones", expanded=True):
        st.markdown("""
        **¿Cómo configurar tus menciones?**
        - **Una línea = Una búsqueda**
        - **Ejemplo simple**: `licitación` → Encuentra cualquier texto que mencione "licitación"
        - **Ejemplo múltiple**: `subvención, empresas` → Encuentra solo textos que mencionen ambas palabras juntas
        """)
        
        st.write("**Menciones Guardadas**")
        menciones_guardadas = preferencias.get('menciones_multiples', []) or []
        menciones_seleccionadas_existentes = st.multiselect(
            "Tus menciones actuales. Desmárcalas para eliminarlas.",
            options=menciones_guardadas,
            default=menciones_guardadas
        )
        
        # Mostrar preview de las menciones existentes
        if menciones_seleccionadas_existentes:
            with st.expander("👁️ Vista previa de tus menciones"):
                for i, mencion in enumerate(menciones_seleccionadas_existentes, 1):
                    if isinstance(mencion, list):
                        st.write(f"{i}. Buscar: **{' + '.join(mencion)}** (todas estas palabras juntas)")
                    else:
                        st.write(f"{i}. Buscar: **{mencion}**")

        st.write("**Añadir Nuevas Menciones**")
        nuevas_menciones_texto = st.text_area(
            "Escribe nuevas menciones (una por línea):",
            placeholder="licitación, obra pública\ncontrato, servicios\nurbanismo, licencia\nsubvención, pymes",
            help="Una línea por búsqueda. Si quieres buscar varias palabras juntas, sepáralas con comas"
        )

    with st.expander("Configuración de Notificaciones", expanded=True):
        st.write("**📧 Opciones de Envío**")
        hora_guardada_str = preferencias.get('hora_envio') or '08:00:00'
        hora_guardada = datetime.datetime.strptime(hora_guardada_str, '%H:%M:%S').time()
        hora_seleccionada = st.time_input("Hora de envío del correo:", value=hora_guardada, step=3600)

        email_guardado = preferencias.get('email', user_email)
        email_seleccionado = st.text_input("Email para recibir las alertas:", value=email_guardado)

    if st.button("Guardar Cambios", use_container_width=True):
        boletines_seleccionados = []
        if b1: boletines_seleccionados.append("DOE")
        if b2: boletines_seleccionados.append("BOP")
        if b3: boletines_seleccionados.append("BOE")

        # Procesa las menciones (una por línea)
        nuevas_menciones_procesadas = []
        nuevas_menciones_raw = [m.strip() for m in nuevas_menciones_texto.split('\n') if m.strip()]
        for m in nuevas_menciones_raw:
            parts = [p.strip() for p in m.split(',') if p.strip()]
            if len(parts) > 1:
                nuevas_menciones_procesadas.append(parts)
            elif parts:
                nuevas_menciones_procesadas.append(parts[0])

        # Combinar y eliminar duplicados
        # (la conversión a tupla es para poder usar 'set' con listas anidadas)
        menciones_existentes_tuples = [tuple(m) if isinstance(m, list) else m for m in menciones_seleccionadas_existentes]
        nuevas_menciones_tuples = [tuple(m) if isinstance(m, list) else m for m in nuevas_menciones_procesadas]
        
        menciones_finales_tuples = sorted(list(set(menciones_existentes_tuples + nuevas_menciones_tuples)), key=lambda x: str(x))
        
        # Convertir de nuevo a listas
        menciones_finales = [list(m) if isinstance(m, tuple) else m for m in menciones_finales_tuples]

        fecha_suscripcion_final = str(suscripcion_hasta) if suscripcion_activa else str(datetime.date.today() + datetime.timedelta(days=30))

        try:
            datos_para_guardar = {
                "user_id": user_id,
                "municipios": municipios_seleccionados,
                "boletines": boletines_seleccionados,
                "menciones_multiples": menciones_finales,
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