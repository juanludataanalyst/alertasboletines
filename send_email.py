import functions_framework
from supabase import create_client, Client
import datetime
import pytz
import os
from main import ejecutar_busqueda_para_usuario

# Configuración de Supabase (usando variables de entorno en Google Cloud)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Inicializa el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@functions_framework.http
def enviar_alertas_por_hora(request):
    """
    Cloud Function que se ejecuta cada hora mediante un cron.
    Consulta las preferencias de los usuarios en Supabase, filtra por hora_envio
    y envía correos a los usuarios correspondientes.
    """
    try:
        # Obtener la hora actual en la zona horaria Europe/Madrid
        zona_horaria = pytz.timezone('Europe/Madrid')
        hora_actual = datetime.datetime.now(zona_horaria).replace(minute=0, second=0, microsecond=0)
        hora_actual_str = hora_actual.strftime('%H:%M:%S')

        # Consultar todas las preferencias de los usuarios
        response = supabase.table('preferencias').select('user_id, email, municipios, boletines, hora_envio, suscripcion_activa_hasta').execute()
        preferencias = response.data

        if not preferencias:
            return {"status": "success", "message": "No hay preferencias registradas."}, 200

        # Filtrar usuarios cuya hora_envio coincide y tienen suscripción activa
        usuarios_a_notificar = []
        fecha_actual = datetime.date.today()

        for pref in preferencias:
            suscripcion_hasta_str = pref.get('suscripcion_activa_hasta')
            suscripcion_activa = False
            if suscripcion_hasta_str:
                try:
                    suscripcion_hasta = datetime.datetime.strptime(suscripcion_hasta_str, '%Y-%m-%d').date()
                    suscripcion_activa = suscripcion_hasta >= fecha_actual
                except (ValueError, TypeError):
                    continue

            hora_envio = pref.get('hora_envio', '').strip()
            if suscripcion_activa and hora_envio == hora_actual_str:
                usuarios_a_notificar.append(pref)

        if not usuarios_a_notificar:
            return {"status": "success", "message": f"No hay usuarios para notificar a las {hora_actual_str}."}, 200

        # Procesar cada usuario
        resultados = []
        for usuario in usuarios_a_notificar:
            email = usuario['email']
            municipios = usuario.get('municipios', [])
            boletines = usuario.get('boletines', [])
            try:
                mensaje, exito = ejecutar_busqueda_para_usuario(email, municipios, boletines)
                resultados.append({
                    "email": email,
                    "exito": exito,
                    "mensaje": mensaje
                })
            except Exception as e:
                resultados.append({
                    "email": email,
                    "exito": False,
                    "mensaje": f"Error al procesar el usuario: {str(e)}"
                })

        return {
            "status": "success",
            "message": f"Procesados {len(usuarios_a_notificar)} usuarios.",
            "resultados": resultados
        }, 200

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en la Cloud Function: {str(e)}"
        }, 500