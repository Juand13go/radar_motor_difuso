from sqlmodel import Session
from app.persistencia.repositorio import obtener_lead_abierto, obtener_items_de_lead
from app.servicio.conversacion import obtener_o_crear_conversacion, guardado_mensajes, obtener_historial_conversacion, CANAL_WEB
from app.servicio.agente import comunicacion_agente, TEXTO_FALLO_TECNICO
from app.servicio.leads import texto_estado_solicitud, registrar_solicitud, evaluar_y_escalar, frase_confirmacion_cliente
from app.servicio.notificaciones import enviar_alerta_telegram
import uuid
import logging

logger = logging.getLogger(__name__)

TEXTO_RESPUESTA_REPETIDA = "Disculpe, creo que me repetí. ¿En qué puedo ayudarle?"
TEXTO_SOLO_TEXTO = "Por ahora solo puedo leer mensajes de texto. ¿Me escribe lo que necesita?"

def es_mensaje_sin_texto(texto: str):
    return texto is None or not texto.strip()

def armar_respuesta_cliente(respuesta: str, escalado: bool, fallo_tecnico: bool, nombre_asesor: str):
    if fallo_tecnico:
        return TEXTO_FALLO_TECNICO
    if escalado:
        # La confirmacion va arriba para que el mensaje termine en la pregunta que hace responder al cliente
        return f"{frase_confirmacion_cliente(nombre_asesor=nombre_asesor)}\n{respuesta}"
    return respuesta

def estado_de_la_solicitud(id_conversacion: uuid.UUID, session: Session):
    lead = obtener_lead_abierto(id_conversacion=id_conversacion, session=session)
    if not lead:
        return texto_estado_solicitud(ciudad=None, fecha_requerida=None, items=[])
    # texto_estado_solicitud trabaja con diccionarios y la base devuelve objetos items_solicitados
    items = [item.model_dump() for item in obtener_items_de_lead(id_lead=lead.id_lead, session=session)]
    return texto_estado_solicitud(ciudad=lead.ciudad, fecha_requerida=lead.fecha_requerida, items=items)

def ultimo_mensaje_asistente(id_conversacion: uuid.UUID, session: Session):
    historial = obtener_historial_conversacion(id_conversacion=id_conversacion, session=session)
    respuestas = [mensaje.contenido for mensaje in historial if mensaje.rol == "assistant"]
    return respuestas[-1] if respuestas else None

def procesar_mensaje_entrante(canal: str, canal_user_id: str, nombre: str, texto: str, session: Session, telefono: str = None):
    if es_mensaje_sin_texto(texto=texto):
        logger.info(f"Mensaje sin texto por el canal {canal}, se respondió el texto fijo")
        return {"respuesta_cliente": TEXTO_SOLO_TEXTO, "notificacion_asesor": None, "id_conversacion": None}

    conversacion = obtener_o_crear_conversacion(canal_user_id=canal_user_id, canal=canal, nombre=nombre, session=session, telefono=telefono)
    mensaje_cliente = guardado_mensajes(id_conversacion=conversacion.id_conversacion, rol="user", contenido=texto, session=session)

    estado_solicitud = estado_de_la_solicitud(id_conversacion=conversacion.id_conversacion, session=session)
    extraccion = comunicacion_agente(id_conversacion=conversacion.id_conversacion, session=session, estado_solicitud=estado_solicitud)

    lead = registrar_solicitud(id_conversacion=conversacion.id_conversacion, extraccion=extraccion, session=session)
    resultado = evaluar_y_escalar(lead=lead, extraccion=extraccion, id_mensaje=mensaje_cliente.id_mensaje, session=session)

    respuesta_cliente = extraccion["respuesta_cliente"]
    # Cuando el cliente insiste, el modelo a veces repite palabra por palabra su respuesta anterior.
    # El texto fijo de fallo tecnico no viene del modelo, asi que no entra en esta comparacion.
    if not extraccion["fallo_tecnico"] and respuesta_cliente == ultimo_mensaje_asistente(id_conversacion=conversacion.id_conversacion, session=session):
        logger.info(f"El modelo repitió su respuesta anterior y se reemplazó por el texto fijo [Conversación ID: {conversacion.id_conversacion}]")
        respuesta_cliente = TEXTO_RESPUESTA_REPETIDA

    nombre_asesor = resultado["notificacion"]["nombre_asesor"] if resultado["notificacion"] else None
    respuesta_cliente = armar_respuesta_cliente(respuesta=respuesta_cliente, escalado=resultado["escalado"], fallo_tecnico=extraccion["fallo_tecnico"], nombre_asesor=nombre_asesor)

    guardado_mensajes(id_conversacion=conversacion.id_conversacion, rol="assistant", contenido=respuesta_cliente, session=session)
    # response_model de /mensaje_entrante descarta id_conversacion, asi que n8n recibe lo mismo de siempre
    return {"respuesta_cliente": respuesta_cliente, "notificacion_asesor": resultado["notificacion"], "id_conversacion": conversacion.id_conversacion}

def procesar_mensaje_web(canal_user_id: uuid.UUID, nombre: str, texto: str, telefono: str, session: Session):
    resultado = procesar_mensaje_entrante(canal=CANAL_WEB, canal_user_id=str(canal_user_id), nombre=nombre, texto=texto, session=session, telefono=telefono)
    notificacion = resultado["notificacion_asesor"]
    # El chat web no pasa por n8n, asi que la alerta al asesor sale desde aqui
    if notificacion:
        enviar_alerta_telegram(chat_id=notificacion["chat_id"], texto=notificacion["texto"], id_conversacion=resultado["id_conversacion"])
    # La notificacion trae prioridad, monto y el chat del asesor, que no le corresponden al cliente
    return {"respuesta_cliente": resultado["respuesta_cliente"]}
