from sqlmodel import Session
from app.persistencia.repositorio import creacion_conversacion, verificacion_existencia_conversacion, historial_conversacion, guardar_mensaje_por_rol
from app.persistencia.repositorio import obtener_conversacion_por_id, conversaciones_por_canal, mensajes_de_conversacion
from app.excepciones import ConversacionNoEncontrada
import uuid

CANAL_SIMULADOR = "simulador"

def obtener_o_crear_conversacion(canal_user_id: str, canal: str, nombre: str, session):
    conversacion = verificacion_existencia_conversacion(canal=canal, canal_user_id=canal_user_id, session=session)
    if conversacion:
        return conversacion
    else:
        return creacion_conversacion(canal_user_id, canal, nombre, session)

def obtener_historial_conversacion(id_conversacion: uuid.UUID, session: Session):
    return historial_conversacion(id_conversacion, session)

def guardado_mensajes(id_conversacion: uuid.UUID, rol:str, contenido:str, session: Session):
    return guardar_mensaje_por_rol(id_conversacion, rol, contenido, session)

def listar_conversaciones_simulador(session: Session):
    return [dict(fila._mapping) for fila in conversaciones_por_canal(canal=CANAL_SIMULADOR, session=session)]

def obtener_mensajes_simulador(id_conversacion: uuid.UUID, session: Session):
    conversacion = obtener_conversacion_por_id(id_conversacion=id_conversacion, session=session)
    # Las conversaciones de otros canales son de personas reales; se responde igual que si no existieran
    if conversacion.canal != CANAL_SIMULADOR:
        raise ConversacionNoEncontrada
    return mensajes_de_conversacion(id_conversacion=id_conversacion, session=session)
