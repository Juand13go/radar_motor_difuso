import urllib.request
import urllib.error
import json
import os
import re
import uuid
import logging

logger = logging.getLogger(__name__)

TIMEOUT_TELEGRAM = 5

def leer_token_bot():
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        logger.error("Falta TELEGRAM_BOT_TOKEN")
        return None
    # El token va dentro de la URL, y con caracteres raros urllib la copia en el mensaje de la excepcion
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+", token):
        logger.error("TELEGRAM_BOT_TOKEN no tiene el formato de un token de bot")
        return None
    return token

def enviar_alerta_telegram(chat_id: str, texto: str, id_conversacion: uuid.UUID):
    token = leer_token_bot()
    if not token:
        logger.error(f"La alerta al asesor no se envió porque no hay un token de bot válido [Conversación ID: {id_conversacion}]")
        return False

    # Sin parse_mode, para que ningun caracter que escribio el cliente se lea como formato
    cuerpo = json.dumps({"chat_id": chat_id, "text": texto}).encode("utf-8")
    peticion = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=cuerpo, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=TIMEOUT_TELEGRAM) as respuesta:
            datos = json.loads(respuesta.read())
        if datos.get("ok") is not True:
            logger.error(f"Telegram rechazó la alerta al asesor: {datos.get('description')} [Conversación ID: {id_conversacion}]")
            return False
    except urllib.error.HTTPError as error:
        # Telegram explica el rechazo en el cuerpo (por ejemplo chat not found); si no se puede leer, queda el codigo
        try:
            descripcion = json.loads(error.read()).get("description")
        except Exception:
            descripcion = None
        if descripcion:
            logger.error(f"Telegram rechazó la alerta al asesor con código {error.code}: {descripcion} [Conversación ID: {id_conversacion}]")
        else:
            logger.error(f"Telegram rechazó la alerta al asesor con código {error.code} [Conversación ID: {id_conversacion}]")
        return False
    except Exception:
        logger.exception(f"No se pudo enviar la alerta al asesor por Telegram [Conversación ID: {id_conversacion}]")
        return False

    logger.info(f"Alerta enviada al asesor por Telegram [Conversación ID: {id_conversacion}]")
    return True
