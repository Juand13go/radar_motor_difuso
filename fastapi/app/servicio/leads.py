from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
from app.excepciones import LeadNoEncontrado, SinAsesoresDisponibles
from app.persistencia.repositorio import crear_lead, asesor_menos_cargado, actualizar_asesor, obtener_asesor_por_id, obtener_lead_por_id
from app.persistencia.repositorio import obtener_leads_por_asesor, actualizar_estado_cierre, lista_asesores_para_front
from app.persistencia.repositorio import obtener_lead_abierto, crear_solicitud, actualizar_datos_solicitud, obtener_productos_por_ids, reemplazar_items_de_lead
from app.persistencia.repositorio import obtener_items_de_lead, guardar_evaluacion, obtener_mensaje_por_id, obtener_leads_cerrados, actualizar_prioridad_lead, marcar_lead_escalado
from app.persistencia.repositorio import obtener_conversacion_por_id, obtener_leads_sin_asignar, evaluaciones_de_lead
from app.motor.reglas import cargar_configuracion
from app.motor.inferencia import evaluar_prioridad
from models import ahora_utc, hoy_bogota
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)

# Se lee una sola vez; si reglas.yaml es invalido, el error sube y detiene el primer uso
@lru_cache(maxsize=1)
def obtener_configuracion():
    return cargar_configuracion(ruta=str(Path(__file__).resolve().parents[1] / "motor" / "reglas.yaml"))

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

def lead_para_bandeja(lead, session: Session):
    items = [item.model_dump() for item in obtener_items_de_lead(id_lead=lead.id_lead, session=session)]
    conversacion = obtener_conversacion_por_id(id_conversacion=lead.id_conversacion, session=session)
    return {**lead.model_dump(), "creado_en": lead.lead_creado_en, "items": items, "nombre_cliente": conversacion.nombre, "canal_user_id": conversacion.canal_user_id}

def listar_leads_por_asesor(id_asesor: uuid.UUID, session: Session):
    return [lead_para_bandeja(lead=lead, session=session) for lead in obtener_leads_por_asesor(id_asesor, session)]

def listar_leads_sin_asignar(session: Session):
    return [lead_para_bandeja(lead=lead, session=session) for lead in obtener_leads_sin_asignar(session=session)]

def listar_evaluaciones_lead(id_lead: uuid.UUID, session: Session):
    if not obtener_lead_por_id(id_lead, session):
        raise LeadNoEncontrado
    return evaluaciones_de_lead(id_lead=id_lead, session=session)

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

def calcular_monto_estimado(items: list):
    monto = Decimal("0")
    for item in items:
        precio = item.get("precio_al_momento")
        if precio is None:
            continue
        cantidad = item.get("cantidad")
        # Un producto pedido sin cantidad no puede dejar el monto en cero: cuenta como una unidad
        if cantidad is None:
            cantidad = 1
        monto += precio * cantidad
    return monto

def calcular_relacion_cliente(leads_cerrados: list):
    return sum(1 for lead in leads_cerrados if lead.estado_lead == "venta")

def calcular_completitud(items: list, ciudad: str):
    completitud = 0.0
    # Un item fuera de catalogo no es un dato faltante sino un producto que no se vende: no cuenta para las senales
    items_del_catalogo = [item for item in items if item.get("id_producto") is not None]
    if items_del_catalogo:
        # "Hay un item del catalogo" y "al menos un item hizo match" son la misma condicion y suman juntas
        completitud += 0.5
        if all(item.get("cantidad") is not None for item in items_del_catalogo):
            completitud += 0.25
    if isinstance(ciudad, str) and ciudad.strip():
        completitud += 0.25
    return completitud

def armar_entradas_del_motor(monto_estimado: Decimal, relacion_cliente: int, completitud: float, plazo_dias: int):
    return {
        "monto_estimado": float(monto_estimado),
        "relacion_cliente": relacion_cliente,
        "completitud": completitud,
        "plazo_dias": plazo_dias
    }

def abrir_solicitud(id_conversacion: uuid.UUID, ciudad: str, fecha_requerida: date, session: Session):
    try:
        lead = crear_solicitud(id_conversacion=id_conversacion, ciudad=ciudad, fecha_requerida=fecha_requerida, session=session)
        logger.info(f"Solicitud creada con id_lead {lead.id_lead} [Conversación ID: {id_conversacion}]")
        return lead
    except IntegrityError as error:
        if "ix_un_lead_abierto_por_conversacion" not in str(error.orig):
            raise
        # Otro mensaje de la misma conversacion abrio la solicitud primero: se sigue con esa
        logger.info(f"La solicitud ya estaba abierta por otro mensaje, se continua con ella [Conversación ID: {id_conversacion}]")
        lead = obtener_lead_abierto(id_conversacion=id_conversacion, session=session)
        return actualizar_datos_solicitud(id_lead=lead.id_lead, ciudad=ciudad, fecha_requerida=fecha_requerida, session=session)

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
        lead = abrir_solicitud(id_conversacion=id_conversacion, ciudad=ciudad, fecha_requerida=fecha_requerida, session=session)
    else:
        lead = actualizar_datos_solicitud(id_lead=lead.id_lead, ciudad=ciudad, fecha_requerida=fecha_requerida, session=session)

    ids = [item.get("id_producto") for item in items_extraidos if item.get("id_producto") is not None]
    productos_por_id = {producto.id_producto: producto for producto in obtener_productos_por_ids(ids=ids, session=session)}
    items = construir_items_para_guardar(items_extraidos=items_extraidos, productos_por_id=productos_por_id)
    reemplazar_items_de_lead(id_lead=lead.id_lead, items=items, session=session)
    return lead

def decidir_escalacion(prioridad: float, umbral: float, solicita_asesor: bool, fallo_tecnico: bool, ya_escalado: bool):
    if ya_escalado:
        return None
    if fallo_tecnico:
        return "fallo_tecnico"
    if solicita_asesor:
        return "solicitud_cliente"
    if prioridad is not None and prioridad >= umbral:
        return "motor"
    return None

def texto_notificacion_asesor(nombre_cliente: str, canal_user_id: str, nivel_prioridad: str, monto_estimado: Decimal, items: list, fallo_tecnico: bool):
    if isinstance(nombre_cliente, str) and nombre_cliente.strip():
        lineas = [f"Nueva solicitud de {nombre_cliente} (ID en el canal: {canal_user_id})."]
    else:
        lineas = [f"Nueva solicitud del cliente con ID en el canal {canal_user_id}."]
    if fallo_tecnico:
        lineas.append("Hubo un fallo técnico con el asistente y la solicitud no se pudo leer completa: hay que revisar la conversación con el cliente.")
    lineas.append(f"Prioridad: {nivel_prioridad or 'sin calcular'}")
    if monto_estimado is None:
        lineas.append("Monto estimado: sin estimar")
    else:
        lineas.append("Monto estimado: $" + f"{monto_estimado:,.0f}".replace(",", "."))
    if not items:
        lineas.append("La solicitud todavía no tiene productos registrados.")
    else:
        lineas.append("Productos pedidos:")
        for item in items:
            cantidad = item.get("cantidad")
            if cantidad is None:
                lineas.append(f"- {item.get('descripcion')}, cantidad sin definir")
            else:
                lineas.append(f"- {item.get('descripcion')}, cantidad {cantidad}")
    return "\n".join(lineas)

def frase_confirmacion_cliente(nombre_asesor: str):
    return f"Su solicitud ya quedó en manos de {nombre_asesor}, que lo va a contactar en breve."

def evaluar_y_escalar(lead, extraccion: dict, id_mensaje: uuid.UUID, session: Session):
    fallo_tecnico = extraccion.get("fallo_tecnico") is True

    if not lead and not fallo_tecnico:
        return {"escalado": False, "motivo": None, "notificacion": None, "evaluacion": None}

    if not lead:
        # El lead llega nulo, asi que la conversacion se toma del mensaje que se esta procesando
        mensaje = obtener_mensaje_por_id(id_mensaje=id_mensaje, session=session)
        lead = abrir_solicitud(id_conversacion=mensaje.id_conversacion, ciudad=None, fecha_requerida=None, session=session)

    configuracion = obtener_configuracion()
    items = [item.model_dump() for item in obtener_items_de_lead(id_lead=lead.id_lead, session=session)]
    evaluacion = None

    if not fallo_tecnico:
        monto_estimado = calcular_monto_estimado(items=items)
        relacion_cliente = calcular_relacion_cliente(leads_cerrados=obtener_leads_cerrados(id_conversacion=lead.id_conversacion, session=session))
        completitud = calcular_completitud(items=items, ciudad=lead.ciudad)
        # El plazo sale de la fecha guardada en el lead, que se conserva aunque el cliente no la repita en este mensaje
        plazo_dias = None
        if lead.fecha_requerida is not None:
            plazo_dias = (lead.fecha_requerida - hoy_bogota()).days
        entradas = armar_entradas_del_motor(monto_estimado=monto_estimado, relacion_cliente=relacion_cliente, completitud=completitud, plazo_dias=plazo_dias)
        evaluacion = evaluar_prioridad(entradas=entradas, configuracion=configuracion)
        guardar_evaluacion(id_lead=lead.id_lead, id_mensaje=id_mensaje, monto_estimado=monto_estimado, relacion_cliente=relacion_cliente, completitud=completitud, plazo_dias=plazo_dias, prioridad=evaluacion["prioridad"], nivel_prioridad=evaluacion["nivel"], reglas_activadas=evaluacion["reglas_activadas"], session=session)
        lead = actualizar_prioridad_lead(id_lead=lead.id_lead, monto_estimado=monto_estimado, prioridad=evaluacion["prioridad"], nivel_prioridad=evaluacion["nivel"], session=session)
        if evaluacion["prioridad"] is None:
            logger.error(f"El motor no activo ninguna regla y el lead {lead.id_lead} queda sin prioridad [Conversación ID: {lead.id_conversacion}]")
        else:
            logger.info(f"Motor evaluado con prioridad {evaluacion['prioridad']:.2f} y nivel {evaluacion['nivel']} [Conversación ID: {lead.id_conversacion}]")

    prioridad = evaluacion["prioridad"] if evaluacion else None
    motivo = decidir_escalacion(prioridad=prioridad, umbral=configuracion["umbral_escalacion"], solicita_asesor=extraccion.get("solicita_asesor") is True, fallo_tecnico=fallo_tecnico, ya_escalado=lead.escalado)
    if not motivo:
        return {"escalado": False, "motivo": None, "notificacion": None, "evaluacion": evaluacion}

    lead = actualizacion_asesor(id_lead=lead.id_lead, session=session)
    lead = marcar_lead_escalado(id_lead=lead.id_lead, motivo_escalacion=motivo, escalado_en=ahora_utc(), session=session)
    asesor = obtener_nombre_asesor(id_asesor=lead.asesor_encargado, session=session)
    conversacion = obtener_conversacion_por_id(id_conversacion=lead.id_conversacion, session=session)
    texto = texto_notificacion_asesor(nombre_cliente=conversacion.nombre, canal_user_id=conversacion.canal_user_id, nivel_prioridad=lead.nivel_prioridad, monto_estimado=lead.monto_estimado, items=items, fallo_tecnico=fallo_tecnico)
    logger.info(f"Lead {lead.id_lead} escalado con motivo {motivo} y prioridad {prioridad} [Conversación ID: {lead.id_conversacion}]")
    return {
        "escalado": True,
        "motivo": motivo,
        "notificacion": {"chat_id": asesor.chat_id, "nombre_asesor": asesor.nombre_asesor, "texto": texto},
        "evaluacion": evaluacion
    }
