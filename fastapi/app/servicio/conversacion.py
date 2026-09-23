from sqlmodel import Session
from app.persistencia.repositorio import creacion_conversacion, verificacion_existencia_conversacion, historial_conversacion, guardar_mensaje_por_rol
import uuid

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
