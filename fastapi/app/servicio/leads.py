from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
from app.excepciones import LeadNoEncontrado, SinAsesoresDisponibles
from app.persistencia.repositorio import crear_lead, asesor_menos_cargado, actualizar_asesor, obtener_asesor_por_id, obtener_lead_por_id
from app.persistencia.repositorio import obtener_leads_por_asesor, actualizar_estado_cierre, lista_asesores_para_front
from app.persistencia.repositorio import obtener_lead_abierto, crear_solicitud, actualizar_datos_solicitud, obtener_productos_por_ids, reemplazar_items_de_lead
from datetime import date
import uuid
import logging

logger = logging.getLogger(__name__)

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

def construir_items_para_guardar(items_extraidos: list, productos_por_id: dict):
    items = []
    for item in items_extraidos:
        producto = productos_por_id.get(item.get("id_producto"))
        items.append({
            "id_producto": producto.id_producto if producto else None,
            "descripcion": item.get("descripcion"),
            "cantidad": item.get("cantidad"),
            "precio_al_momento": producto.precio_unitario if producto else None,
            "existencias_al_momento": producto.existencias if producto else None
        })
    return items

def texto_estado_solicitud(ciudad: str, fecha_requerida: date, items: list):
    lineas = []
    if ciudad:
        lineas.append(f"Ciudad: {ciudad}")
    if fecha_requerida:
        lineas.append(f"Fecha requerida: {fecha_requerida.isoformat()}")
    if items:
        lineas.append("Productos pedidos:")
        for item in items:
            cantidad = item.get("cantidad")
            if cantidad is None:
                lineas.append(f"- {item.get('descripcion')}, cantidad sin definir")
            else:
                lineas.append(f"- {item.get('descripcion')}, cantidad {cantidad}")
    if not lineas:
        return "Sin solicitud abierta"
    return "\n".join(lineas)

def registrar_solicitud(id_conversacion: uuid.UUID, extraccion: dict, session: Session):
    lead = obtener_lead_abierto(id_conversacion=id_conversacion, session=session)
    items_extraidos = extraccion.get("items") or []
    ciudad = extraccion.get("ciudad")
    fecha_requerida = extraccion.get("fecha_requerida")

    # Con fallo tecnico la extraccion no es confiable: reemplazar los items borraria lo que el cliente ya pidio
    if extraccion.get("fallo_tecnico") is True:
        if not lead:
            return None
        return actualizar_datos_solicitud(id_lead=lead.id_lead, ciudad=ciudad, fecha_requerida=fecha_requerida, session=session)

    if not lead and not items_extraidos:
        return None

    if not lead:
        try:
            lead = crear_solicitud(id_conversacion=id_conversacion, ciudad=ciudad, fecha_requerida=fecha_requerida, session=session)
            logger.info(f"Solicitud creada con id_lead {lead.id_lead} [Conversación ID: {id_conversacion}]")
        except IntegrityError as error:
            if "ix_un_lead_abierto_por_conversacion" not in str(error.orig):
                raise
            # Otro mensaje de la misma conversacion abrio la solicitud primero: se sigue con esa
            logger.info(f"La solicitud ya estaba abierta por otro mensaje, se continua con ella [Conversación ID: {id_conversacion}]")
            lead = obtener_lead_abierto(id_conversacion=id_conversacion, session=session)
            lead = actualizar_datos_solicitud(id_lead=lead.id_lead, ciudad=ciudad, fecha_requerida=fecha_requerida, session=session)
    else:
        lead = actualizar_datos_solicitud(id_lead=lead.id_lead, ciudad=ciudad, fecha_requerida=fecha_requerida, session=session)

    ids = [item.get("id_producto") for item in items_extraidos if item.get("id_producto") is not None]
    productos_por_id = {producto.id_producto: producto for producto in obtener_productos_por_ids(ids=ids, session=session)}
    items = construir_items_para_guardar(items_extraidos=items_extraidos, productos_por_id=productos_por_id)
    reemplazar_items_de_lead(id_lead=lead.id_lead, items=items, session=session)
    return lead
