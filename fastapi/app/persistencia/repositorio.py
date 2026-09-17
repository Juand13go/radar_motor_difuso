from models import conversaciones, mensajes, leads, productos, asesores
from sqlmodel import select, Session, func
import uuid
from app.excepciones import ConversacionNoEncontrada, AsesorNoEncontrado, LeadNoEncontrado

def verificacion_existencia_conversacion(canal:str, canal_user_id:str, session: Session):
    conversacion = session.exec(select(conversaciones).where(conversaciones.canal == canal, conversaciones.canal_user_id == canal_user_id)).first()
    return conversacion

def creacion_conversacion(canal_user_id:str, canal:str, nombre:str, session: Session):
    nueva_conversacion = conversaciones(canal_user_id = canal_user_id, canal = canal, nombre = nombre) 
    session.add(nueva_conversacion) 
    session.commit()
    session.refresh(nueva_conversacion)
    return nueva_conversacion

def historial_conversacion(id_conversacion: uuid.UUID, session: Session):
    ultimos = session.exec(select(mensajes).where(mensajes.id_conversacion == id_conversacion).order_by(mensajes.creado_en.desc()).limit(10)).all()
    # El limite toma los diez mas recientes, pero quien lee el historial lo necesita del mas viejo al mas nuevo
    return list(reversed(ultimos))
    
def guardar_mensaje_por_rol(id_conversacion: uuid.UUID, rol:str, contenido:str, session: Session):
    existe = session.get(conversaciones, id_conversacion)
    if existe is None: 
        raise ConversacionNoEncontrada
    nuevo_mensaje = mensajes(id_conversacion=id_conversacion, rol=rol, contenido=contenido)
    session.add(nuevo_mensaje)
    session.commit()
    session.refresh(nuevo_mensaje)
    return nuevo_mensaje

def actualizar_estado_conversacion(estado: str, id_conversacion: uuid.UUID, session: Session):
    conversacion = session.get(conversaciones, id_conversacion)
    if conversacion is None:
        raise ConversacionNoEncontrada
    conversacion.estado = estado
    session.add(conversacion)
    session.commit()
    session.refresh(conversacion)
    return conversacion

def crear_lead(id_conversacion: uuid.UUID, productos_interes: str, ciudad: str, session: Session): 
    existe = session.get(conversaciones, id_conversacion)
    if existe is None: 
        raise ConversacionNoEncontrada
    lead = leads(id_conversacion=id_conversacion, productos_interes = productos_interes, ciudad = ciudad)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead

def obtener_productos(session: Session):
    return session.exec(select(productos)).all()  

def lista_asesores_para_front(session: Session):
    return session.exec(select(asesores)).all()

def asesor_menos_cargado(session: Session):
    leads_abiertos = func.count(leads.id_lead)
    # El outerjoin deja con cero al asesor que todavia no tiene leads, que es justo el que hay que elegir
    return session.exec(select(asesores.id_asesor).outerjoin(leads, (leads.asesor_encargado == asesores.id_asesor) & (leads.estado_lead == "en_proceso")).group_by(asesores.id_asesor).order_by(leads_abiertos.asc(), asesores.id_asesor.asc())).first()

def obtener_lead_por_id(id_lead: uuid.UUID, session:Session):
    return session.get(leads, id_lead)

def actualizar_asesor(lead: leads, session: Session):
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead

def obtener_asesor_por_id(id_asesor: uuid.UUID, session: Session):
    obtener = session.get(asesores, id_asesor)

    if not obtener: 
        raise AsesorNoEncontrado
    return obtener

def obtener_leads_por_asesor(id_asesor: uuid.UUID, session: Session):
    return session.exec(select(leads).where(leads.asesor_encargado == id_asesor, leads.estado_lead == "en_proceso")).all()

def actualizar_estado_cierre(id_lead: uuid.UUID, estado_lead: str, session: Session): 
    lead = session.get(leads, id_lead)
    if not lead: 
        raise LeadNoEncontrado
    lead.estado_lead = estado_lead
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead
    
    

