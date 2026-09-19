from sqlmodel import Session
from app.persistencia.repositorio import obtener_lead_abierto, obtener_items_de_lead
from app.servicio.conversacion import obtener_o_crear_conversacion, guardado_mensajes
from app.servicio.agente import comunicacion_agente
from app.servicio.leads import texto_estado_solicitud, registrar_solicitud, evaluar_y_escalar, frase_confirmacion_cliente
import uuid

def estado_de_la_solicitud(id_conversacion: uuid.UUID, session: Session):
    lead = obtener_lead_abierto(id_conversacion=id_conversacion, session=session)
    if not lead:
        return texto_estado_solicitud(ciudad=None, fecha_requerida=None, items=[])
    # texto_estado_solicitud trabaja con diccionarios y la base devuelve objetos items_solicitados
    items = [item.model_dump() for item in obtener_items_de_lead(id_lead=lead.id_lead, session=session)]
    return texto_estado_solicitud(ciudad=lead.ciudad, fecha_requerida=lead.fecha_requerida, items=items)

def procesar_mensaje_entrante(canal: str, canal_user_id: str, nombre: str, texto: str, session: Session):
    conversacion = obtener_o_crear_conversacion(canal_user_id=canal_user_id, canal=canal, nombre=nombre, session=session)
    mensaje_cliente = guardado_mensajes(id_conversacion=conversacion.id_conversacion, rol="user", contenido=texto, session=session)

    estado_solicitud = estado_de_la_solicitud(id_conversacion=conversacion.id_conversacion, session=session)
    extraccion = comunicacion_agente(id_conversacion=conversacion.id_conversacion, session=session, estado_solicitud=estado_solicitud)

    lead = registrar_solicitud(id_conversacion=conversacion.id_conversacion, extraccion=extraccion, session=session)
    resultado = evaluar_y_escalar(lead=lead, extraccion=extraccion, id_mensaje=mensaje_cliente.id_mensaje, session=session)

    respuesta_cliente = extraccion["respuesta_cliente"]
    if resultado["escalado"]:
        # La confirmacion va arriba para que el mensaje termine en la pregunta que hace responder al cliente
        respuesta_cliente = f"{frase_confirmacion_cliente(nombre_asesor=resultado['notificacion']['nombre_asesor'])}\n{respuesta_cliente}"

    guardado_mensajes(id_conversacion=conversacion.id_conversacion, rol="assistant", contenido=respuesta_cliente, session=session)
    return {"respuesta_cliente": respuesta_cliente, "notificacion_asesor": resultado["notificacion"]}
