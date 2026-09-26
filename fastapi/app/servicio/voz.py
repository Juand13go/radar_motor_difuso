from app.servicio.agente import obtener_cliente_modelo
from app.servicio.notificaciones import leer_token_bot
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import logging

logger = logging.getLogger(__name__)

# Con `or` y no con el valor por defecto de getenv, porque docker compose pasa la variable vacia cuando falta en el .env
MODELO_VOZ = os.getenv("GROQ_MODELO_VOZ") or "whisper-large-v3-turbo"

TIMEOUT_DESCARGA_VOZ = 10
TAMANO_MAXIMO_VOZ = 5 * 1024 * 1024

def nombre_para_transcripcion(file_path: str):
    nombre = file_path.rsplit("/", 1)[-1]
    # Telegram guarda las notas de voz como .oga y Groq solo reconoce la extension .ogg
    if nombre.endswith(".oga"):
        return nombre[:-4] + ".ogg"
    return nombre

def descargar_audio_telegram(file_id: str, canal: str):
    token = leer_token_bot()
    if not token:
        logger.error(f"La nota de voz no se descargó porque no hay un token de bot válido, por el canal {canal}")
        return None

    cuerpo = json.dumps({"file_id": file_id}).encode("utf-8")
    peticion = urllib.request.Request(f"https://api.telegram.org/bot{token}/getFile", data=cuerpo, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=TIMEOUT_DESCARGA_VOZ) as respuesta:
            datos = json.loads(respuesta.read())
        if datos.get("ok") is not True:
            logger.error(f"Telegram rechazó la consulta de la nota de voz: {datos.get('description')}, por el canal {canal}")
            return None
        archivo = datos.get("result") or {}
        file_path = archivo.get("file_path")
        if not file_path:
            logger.error(f"Telegram no devolvió la ruta de la nota de voz, por el canal {canal}")
            return None
        if (archivo.get("file_size") or 0) > TAMANO_MAXIMO_VOZ:
            logger.info(f"La nota de voz supera el tamaño máximo y no se descargó, por el canal {canal}")
            return None

        # quote evita que un caracter raro en la ruta haga que urllib copie la URL, con el token, en la excepcion
        url_archivo = f"https://api.telegram.org/file/bot{token}/{urllib.parse.quote(file_path)}"
        with urllib.request.urlopen(url_archivo, timeout=TIMEOUT_DESCARGA_VOZ) as respuesta:
            # Se lee un byte de mas para detectar el exceso cuando getFile no informa el tamaño
            contenido = respuesta.read(TAMANO_MAXIMO_VOZ + 1)
    except urllib.error.HTTPError as error:
        try:
            descripcion = json.loads(error.read()).get("description")
        except Exception:
            descripcion = None
        if descripcion:
            logger.error(f"Telegram rechazó la descarga de la nota de voz con código {error.code}: {descripcion}, por el canal {canal}")
        else:
            logger.error(f"Telegram rechazó la descarga de la nota de voz con código {error.code}, por el canal {canal}")
        return None
    except Exception:
        logger.exception(f"No se pudo descargar la nota de voz de Telegram, por el canal {canal}")
        return None

    if len(contenido) > TAMANO_MAXIMO_VOZ:
        logger.info(f"La nota de voz supera el tamaño máximo y no se transcribió, por el canal {canal}")
        return None
    return contenido, nombre_para_transcripcion(file_path=file_path)

def transcribir_voz(file_id: str, canal: str):
    audio = descargar_audio_telegram(file_id=file_id, canal=canal)
    if not audio:
        return None
    contenido, nombre_archivo = audio
    try:
        transcripcion = obtener_cliente_modelo().audio.transcriptions.create(model=MODELO_VOZ, file=(nombre_archivo, contenido), language="es")
    except Exception:
        logger.exception(f"No se pudo transcribir la nota de voz con Groq, por el canal {canal}")
        return None
    logger.info(f"Nota de voz transcrita, por el canal {canal}")
    return transcripcion.text
