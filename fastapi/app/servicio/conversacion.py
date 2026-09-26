from sqlmodel import Session
from app.persistencia.repositorio import creacion_conversacion, verificacion_existencia_conversacion, historial_conversacion, guardar_mensaje_por_rol
from app.persistencia.repositorio import obtener_conversacion_por_id, conversaciones_por_canal, mensajes_de_conversacion, completar_telefono_conversacion
from app.excepciones import ConversacionNoEncontrada
import uuid

CANAL_SIMULADOR = "simulador"
CANAL_WEB = "web"

def obtener_o_crear_conversacion(canal_user_id: str, canal: str, nombre: str, session: Session, telefono: str = None):
    conversacion = verificacion_existencia_conversacion(canal=canal, canal_user_id=canal_user_id, session=session)
    if conversacion:
        if telefono and not conversacion.telefono:
            return completar_telefono_conversacion(id_conversacion=conversacion.id_conversacion, telefono=telefono, session=session)
        return conversacion
    else:
        return creacion_conversacion(canal_user_id=canal_user_id, canal=canal, nombre=nombre, session=session, telefono=telefono)

def obtener_historial_conversacion(id_conversacion: uuid.UUID, session: Session):
    return historial_conversacion(id_conversacion=id_conversacion, session=session)

def guardado_mensajes(id_conversacion: uuid.UUID, rol:str, contenido:str, session: Session):
    return guardar_mensaje_por_rol(id_conversacion=id_conversacion, rol=rol, contenido=contenido, session=session)

def listar_conversaciones_simulador(session: Session):
    return [dict(fila._mapping) for fila in conversaciones_por_canal(canal=CANAL_SIMULADOR, session=session)]

def obtener_mensajes_simulador(id_conversacion: uuid.UUID, session: Session):
    conversacion = obtener_conversacion_por_id(id_conversacion=id_conversacion, session=session)
    # Las conversaciones de otros canales son de personas reales; se responde igual que si no existieran
    if conversacion.canal != CANAL_SIMULADOR:
        raise ConversacionNoEncontrada
    return mensajes_de_conversacion(id_conversacion=id_conversacion, session=session)

def obtener_mensajes_web(canal_user_id: uuid.UUID, session: Session):
    conversacion = verificacion_existencia_conversacion(canal=CANAL_WEB, canal_user_id=str(canal_user_id), session=session)
    # Un cliente que abre el chat por primera vez todavia no tiene conversacion, y eso no es un error
    if not conversacion:
        return []
    return mensajes_de_conversacion(id_conversacion=conversacion.id_conversacion, session=session)
