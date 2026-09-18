from sqlmodel import Session
from app.excepciones import LeadNoEncontrado, SinAsesoresDisponibles
from app.persistencia.repositorio import creacion_conversacion, verificacion_existencia_conversacion, historial_conversacion, guardar_mensaje_por_rol, obtener_lead_por_id
from app.persistencia.repositorio import crear_lead, actualizar_estado_conversacion, asesor_menos_cargado, actualizar_asesor, obtener_asesor_por_id
from app.persistencia.repositorio import obtener_leads_por_asesor, actualizar_estado_cierre, lista_asesores_para_front
import uuid
import logging

logger = logging.getLogger(__name__)

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

def actualizacion_estado(estado: str, id_conversacion: uuid.UUID, session: Session):
    return actualizar_estado_conversacion(estado, id_conversacion, session)

def creacion_lead(id_conversacion: uuid.UUID, productos_interes: str, ciudad: str, session: Session):
    return crear_lead(id_conversacion, productos_interes, ciudad, session)

def menos_cargado(session: Session):
    return asesor_menos_cargado(session=session)

def actualizacion_asesor(id_lead: uuid.UUID, session: Session):
    lead = obtener_lead_por_id(id_lead, session)

    if not lead: 
        raise LeadNoEncontrado

    if not lead.asesor_encargado:
        asesor_encargado = menos_cargado(session)

        if not asesor_encargado:
            logger.error(f"La variable id_menos_cargado llego con valor {asesor_encargado}, verificar existencia de asesores.")
            raise SinAsesoresDisponibles

        lead.asesor_encargado = asesor_encargado
        actualizar_asesor(lead, session)
    return lead

def obtener_nombre_asesor(id_asesor: uuid.UUID, session: Session):
    return obtener_asesor_por_id(id_asesor, session)

def listar_leads_por_asesor(id_asesor: uuid.UUID, session: Session):
    return obtener_leads_por_asesor(id_asesor, session)

def cambiar_estado_lead_para_cierre(id_lead: uuid.UUID, estado_lead: str, session: Session):
    return actualizar_estado_cierre(id_lead=id_lead, estado_lead=estado_lead, session=session)

def funcion_listado_asesores(session: Session):
    return lista_asesores_para_front(session=session)