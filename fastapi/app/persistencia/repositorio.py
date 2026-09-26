from models import conversaciones, mensajes, leads, productos, asesores, items_solicitados, evaluaciones_motor, ahora_utc
from sqlmodel import select, Session, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy import true
from datetime import date, datetime
from decimal import Decimal
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
    return session.exec(select(leads).where(leads.asesor_encargado == id_asesor, leads.estado_lead == "en_proceso").order_by(leads.prioridad.desc().nulls_last(), leads.lead_creado_en.asc())).all()

def obtener_leads_sin_asignar(session: Session):
    return session.exec(select(leads).where(leads.asesor_encargado.is_(None), leads.estado_lead == "en_proceso").order_by(leads.prioridad.desc().nulls_last(), leads.lead_creado_en.asc())).all()

def actualizar_estado_cierre(id_lead: uuid.UUID, estado_lead: str, session: Session): 
    lead = session.get(leads, id_lead)
    if not lead: 
        raise LeadNoEncontrado
    lead.estado_lead = estado_lead
    lead.cerrado_en = ahora_utc()
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead

def reemplazar_items_de_lead(id_lead: uuid.UUID, items: list[dict], session: Session):
    lead = session.get(leads, id_lead)
    if not lead:
        raise LeadNoEncontrado
    anteriores = session.exec(select(items_solicitados).where(items_solicitados.id_lead == id_lead)).all()
    for anterior in anteriores:
        session.delete(anterior)
    nuevos = [items_solicitados(id_lead=id_lead, **item) for item in items]
    for nuevo in nuevos:
        session.add(nuevo)
    # Borrado e insercion van en el mismo commit para que el lead nunca quede a medias
    session.commit()
    for nuevo in nuevos:
        session.refresh(nuevo)
    return nuevos

def obtener_items_de_lead(id_lead: uuid.UUID, session: Session):
    return session.exec(select(items_solicitados).where(items_solicitados.id_lead == id_lead)).all()

def guardar_evaluacion(id_lead: uuid.UUID, id_mensaje: uuid.UUID, monto_estimado: float, relacion_cliente: float, completitud: float, plazo_dias: int, prioridad: float, nivel_prioridad: str, reglas_activadas: list, session: Session):
    evaluacion = evaluaciones_motor(id_lead=id_lead, id_mensaje=id_mensaje, monto_estimado=monto_estimado, relacion_cliente=relacion_cliente, completitud=completitud, plazo_dias=plazo_dias, prioridad=prioridad, nivel_prioridad=nivel_prioridad, reglas_activadas=reglas_activadas)
    session.add(evaluacion)
    session.commit()
    session.refresh(evaluacion)
    return evaluacion

def evaluaciones_de_lead(id_lead: uuid.UUID, session: Session):
    return session.exec(select(evaluaciones_motor).where(evaluaciones_motor.id_lead == id_lead).order_by(evaluaciones_motor.creado_en.asc())).all()

def obtener_lead_abierto(id_conversacion: uuid.UUID, session: Session):
    return session.exec(select(leads).where(leads.id_conversacion == id_conversacion, leads.estado_lead == "en_proceso")).first()

def crear_solicitud(id_conversacion: uuid.UUID, ciudad: str, fecha_requerida: date, session: Session):
    existe = session.get(conversaciones, id_conversacion)
    if existe is None:
        raise ConversacionNoEncontrada
    if not isinstance(ciudad, str) or not ciudad.strip():
        ciudad = None
    lead = leads(id_conversacion=id_conversacion, ciudad=ciudad, fecha_requerida=fecha_requerida, estado_lead="en_proceso")
    session.add(lead)
    try:
        session.commit()
    except IntegrityError:
        # Se deshace aqui para que la sesion quede usable; quien llama decide que hacer con el error
        session.rollback()
        raise
    session.refresh(lead)
    return lead

def actualizar_datos_solicitud(id_lead: uuid.UUID, ciudad: str, fecha_requerida: date, session: Session):
    lead = session.get(leads, id_lead)
    if not lead:
        raise LeadNoEncontrado
    if isinstance(ciudad, str) and ciudad.strip():
        lead.ciudad = ciudad
    if fecha_requerida is not None:
        lead.fecha_requerida = fecha_requerida
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead

def obtener_productos_por_ids(ids: list[int], session: Session):
    return session.exec(select(productos).where(productos.id_producto.in_(ids))).all()

def obtener_mensaje_por_id(id_mensaje: uuid.UUID, session: Session):
    return session.get(mensajes, id_mensaje)

def obtener_conversacion_por_id(id_conversacion: uuid.UUID, session: Session):
    conversacion = session.get(conversaciones, id_conversacion)
    if not conversacion:
        raise ConversacionNoEncontrada
    return conversacion

def obtener_leads_cerrados(id_conversacion: uuid.UUID, session: Session):
    return session.exec(select(leads).where(leads.id_conversacion == id_conversacion, leads.estado_lead.in_(["venta", "no_venta"]))).all()

def actualizar_prioridad_lead(id_lead: uuid.UUID, monto_estimado: Decimal, prioridad: float, nivel_prioridad: str, session: Session):
    lead = session.get(leads, id_lead)
    if not lead:
        raise LeadNoEncontrado
    lead.monto_estimado = monto_estimado
    lead.prioridad = prioridad
    lead.nivel_prioridad = nivel_prioridad
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead

def marcar_lead_escalado(id_lead: uuid.UUID, motivo_escalacion: str, escalado_en: datetime, session: Session):
    lead = session.get(leads, id_lead)
    if not lead:
        raise LeadNoEncontrado
    lead.escalado = True
    lead.motivo_escalacion = motivo_escalacion
    lead.escalado_en = escalado_en
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead
    
    

def consultar_demanda_no_cubierta(desde: datetime, hasta: datetime, session: Session):
    faltante = items_solicitados.cantidad - items_solicitados.existencias_al_momento
    monto_faltante = func.sum(faltante * items_solicitados.precio_al_momento)
    consulta = (
        select(productos.referencia, productos.nombre_producto, func.count(items_solicitados.id_item).label("veces"), func.sum(items_solicitados.cantidad).label("unidades_pedidas"), func.sum(faltante).label("unidades_faltantes"), monto_faltante.label("monto_faltante"))
        .join(leads, leads.id_lead == items_solicitados.id_lead)
        .join(productos, productos.id_producto == items_solicitados.id_producto)
        .where(leads.lead_creado_en >= desde, leads.lead_creado_en < hasta, items_solicitados.cantidad > items_solicitados.existencias_al_momento)
        .group_by(productos.referencia, productos.nombre_producto)
        .order_by(monto_faltante.desc())
    )
    return session.exec(consulta).all()

def consultar_demanda_fuera_de_catalogo(desde: datetime, hasta: datetime, session: Session):
    descripcion_normalizada = func.lower(func.trim(func.regexp_replace(items_solicitados.descripcion, r"\s+", " ", "g")))
    veces = func.count(items_solicitados.id_item)
    consulta = (
        select(descripcion_normalizada.label("descripcion"), veces.label("veces"), func.coalesce(func.sum(items_solicitados.cantidad), 0).label("unidades"))
        .join(leads, leads.id_lead == items_solicitados.id_lead)
        .where(leads.lead_creado_en >= desde, leads.lead_creado_en < hasta, items_solicitados.id_producto.is_(None))
        .group_by(descripcion_normalizada)
        .order_by(veces.desc(), descripcion_normalizada.asc())
    )
    return session.exec(consulta).all()

def consultar_sobrestock(desde: datetime, hasta: datetime, session: Session):
    pedidos_en_rango = (
        select(items_solicitados.id_producto)
        .join(leads, leads.id_lead == items_solicitados.id_lead)
        .where(leads.lead_creado_en >= desde, leads.lead_creado_en < hasta, items_solicitados.id_producto.is_not(None))
    )
    capital = productos.existencias * productos.precio_unitario
    consulta = (
        select(productos.referencia, productos.nombre_producto, productos.existencias, productos.precio_unitario, capital.label("capital_inmovilizado"))
        .where(productos.existencias > 0, productos.id_producto.not_in(pedidos_en_rango))
        .order_by(capital.desc())
    )
    return session.exec(consulta).all()

def consultar_resumen_periodo(desde: datetime, hasta: datetime, session: Session):
    consulta = (
        select(func.count(leads.id_lead).label("solicitudes"), func.count(leads.id_lead).filter(leads.escalado.is_(True)).label("escaladas"), func.count(leads.id_lead).filter(leads.estado_lead == "venta").label("ventas"), func.count(leads.id_lead).filter(leads.estado_lead == "no_venta").label("no_ventas"), func.coalesce(func.sum(leads.monto_estimado), 0).label("monto_total"))
        .where(leads.lead_creado_en >= desde, leads.lead_creado_en < hasta)
    )
    return session.exec(consulta).one()

def conversaciones_por_canal(canal: str, session: Session):
    ultimo = (
        select(mensajes.contenido, mensajes.creado_en)
        .where(mensajes.id_conversacion == conversaciones.id_conversacion)
        .order_by(mensajes.creado_en.desc())
        .limit(1)
        .lateral()
    )
    # El join interno con la lateral deja por fuera las conversaciones que todavia no tienen mensajes
    consulta = (
        select(conversaciones.id_conversacion, conversaciones.canal_user_id, conversaciones.nombre, ultimo.c.contenido.label("ultimo_mensaje"), ultimo.c.creado_en.label("actualizado_en"))
        .join(ultimo, true())
        .where(conversaciones.canal == canal)
        .order_by(ultimo.c.creado_en.desc())
    )
    return session.exec(consulta).all()

def mensajes_de_conversacion(id_conversacion: uuid.UUID, session: Session):
    return session.exec(select(mensajes).where(mensajes.id_conversacion == id_conversacion).order_by(mensajes.creado_en.asc())).all()
