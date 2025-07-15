import functions_framework
from supabase import create_client, Client
import datetime
import pytz
from main import ejecutar_busqueda_para_usuario  # Importa tu función existente
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Supabase (asegúrate de establecer estas variables de entorno en Google Cloud Functions)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Inicializa el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Verificar que las variables de entorno estén definidas
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY: {'***' if SUPABASE_KEY else 'No definida'}")

# Inicializa el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@functions_framework.http
def enviar_alertas_por_hora(request=None):
    """
    Cloud Function que se ejecuta cada hora mediante un cron.
    Consulta las preferencias de los usuarios en Supabase, filtra por hora_envio
    y envía correos a los usuarios correspondientes.
    """
    try:
        # Obtener la hora actual simulada (07:30:00)
        zona_horaria = pytz.timezone('Europe/Madrid')
        hora_actual = datetime.datetime.now(zona_horaria).replace(hour=7, minute=30, second=0, microsecond=0)
        hora_actual_str = hora_actual.strftime('%H:%M:%S')
        print(f"Hora actual simulada: '{hora_actual_str}' (longitud: {len(hora_actual_str)})")

        # Consultar todas las preferencias de los usuarios
        print("Consultando la tabla 'preferencias' en Supabase...")
        response = supabase.table('preferencias').select('user_id, email, municipios, boletines, hora_envio, suscripcion_activa_hasta').execute()
        preferencias = response.data
        print(f"Preferencias encontradas: {len(preferencias)} usuarios")
        print(f"Datos crudos de la respuesta: {preferencias}")

        if not preferencias:
            print("No hay preferencias registradas.")
            return {"status": "success", "message": "No hay preferencias registradas."}, 200

        # Filtrar usuarios cuya hora_envio coincide y tienen suscripción activa
        usuarios_a_notificar = []
        fecha_actual = datetime.date.today()
        print(f"Fecha actual: {fecha_actual}")

        for pref in preferencias:
            print(f"\nProcesando usuario con user_id: {pref.get('user_id')}")
            hora_envio = pref.get('hora_envio', '').strip()  # Eliminar posibles espacios
            print(f"  hora_envio: '{hora_envio}' (longitud: {len(hora_envio)}, tipo: {type(hora_envio)})")
            print(f"  suscripcion_activa_hasta: {pref.get('suscripcion_activa_hasta')}")
            print(f"  Comparando hora_envio '{hora_envio}' con hora_actual_str '{hora_actual_str}'")
            print(f"  Resultado comparación: {hora_envio == hora_actual_str}")

            suscripcion_hasta_str = pref.get('suscripcion_activa_hasta')
            suscripcion_activa = False
            if suscripcion_hasta_str:
                try:
                    suscripcion_hasta = datetime.datetime.strptime(suscripcion_hasta_str, '%Y-%m-%d').date()
                    suscripcion_activa = suscripcion_hasta >= fecha_actual
                    print(f"  Suscripción activa: {suscripcion_activa} (hasta {suscripcion_hasta})")
                except (ValueError, TypeError) as e:
                    print(f"  Error en suscripcion_activa_hasta: {str(e)}")
                    continue

            if suscripcion_activa and hora_envio == hora_actual_str:
                print(f"  Usuario seleccionado para notificar: {pref.get('email')}")
                usuarios_a_notificar.append(pref)
            else:
                print(f"  Usuario no seleccionado (hora_envio no coincide o suscripción inactiva)")

        if not usuarios_a_notificar:
            print(f"No hay usuarios para notificar a las {hora_actual_str}.")
            return {"status": "success", "message": f"No hay usuarios para notificar a las {hora_actual_str}."}, 200

        # Procesar cada usuario
        resultados = []
        print(f"\nProcesando {len(usuarios_a_notificar)} usuarios para enviar correos...")
        for usuario in usuarios_a_notificar:
            email = usuario['email']
            municipios = usuario.get('municipios', [])
            boletines = usuario.get('boletines', [])
            print(f"Enviando correo a {email} con municipios: {municipios}, boletines: {boletines}")
            try:
                mensaje, exito = ejecutar_busqueda_para_usuario(email, municipios, boletines)
                print(f"Resultado para {email}: Éxito={exito}, Mensaje={mensaje}")
                resultados.append({
                    "email": email,
                    "exito": exito,
                    "mensaje": mensaje
                })
            except Exception as e:
                print(f"Error al procesar usuario {email}: {str(e)}")
                resultados.append({
                    "email": email,
                    "exito": False,
                    "mensaje": f"Error al procesar el usuario: {str(e)}"
                })

        print(f"\nProcesados {len(usuarios_a_notificar)} usuarios.")
        return {
            "status": "success",
            "message": f"Procesados {len(usuarios_a_notificar)} usuarios.",
            "resultados": resultados
        }, 200

    except Exception as e:
        print(f"Error general en la Cloud Function: {str(e)}")
        return {
            "status": "error",
            "message": f"Error en la Cloud Function: {str(e)}"
        }, 500

# Para pruebas locales
if __name__ == "__main__":
    print("Ejecutando prueba local...")
    enviar_alertas_por_hora()