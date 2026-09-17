from sqlmodel import Session
from app.excepciones import LeadNoEncontrado, SinAsesoresDisponibles
from app.persistencia.repositorio import creacion_conversacion, verificacion_existencia_conversacion, historial_conversacion, guardar_mensaje_por_rol, obtener_lead_por_id
from app.persistencia.repositorio import crear_lead, actualizar_estado_conversacion, obtener_productos, asesor_menos_cargado, actualizar_asesor, obtener_asesor_por_id
from app.persistencia.repositorio import obtener_leads_por_asesor, actualizar_estado_cierre, lista_asesores_para_front
import uuid
from openai import OpenAI, OpenAIError
import json
import os
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

def catalogo_a_texto(session: Session):
    producto = obtener_productos(session)
    catalogo_productos = [f" Producto: {c.nombre_producto} | Referencia: {c.referencia} | Precio unitario:  {c.precio_unitario} | Unidad: {c.unidad} | Existencias: {c.existencias} | Categoría: {c.categoria} " for c in producto]
    catalogo_productos_variable = "\n".join(catalogo_productos)
    return catalogo_productos_variable

client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1", max_retries=4, timeout=20.0) 

MODELO_AGENTE = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

def comunicacion_agente(id_conversacion: uuid.UUID, session: Session):
    historial = obtener_historial_conversacion(id_conversacion=id_conversacion, session=session)
    catalogo_productos_variable = catalogo_a_texto(session) 
    try:
        response = client.chat.completions.create(
            model = MODELO_AGENTE,
            max_tokens = 1024,
            messages=[{
                        "role": "system", "content": f"""Eres el agente encargado del manejo de cotizaciones de Tornalba Suministros Técnicos S.A.S., una distribuidora de suministros industriales y ferretería técnica, vas a recibir el historial de un chat con los mensajes del cliente + el catalogo con los productos: {catalogo_productos_variable}. Ten en cuenta que el publico al que te diriges es de Colombia;
                        empieza el chat saludando al cliente y preguntandole por su ubicación;
                        Primero consigue ciudad y productos_interes, solo cuando tengas ambos si el cliente tiene clara intención de compra (ej. quiere dejar sus datos, pide cotización formal, pregunta dónde pagar), si está muy enojado o si pide explícitamente hablar con un asesor humano actualiza el estado de escalación a True. De lo contrario, marca False (Como booleano).
                        Si el cliente no proporciona información en ciudad o productos_interes, llena esas variables con un string vacío ("").
                        El cliente no debe saber el estado de escalación del Lead, ni si sera conectado con un asesor."""
            }] + [{"role" : m.rol, "content" : m.contenido} for m in historial],
            tools=[
                {
                    "type" : "function",
                    "function": {

                        "name" : "evaluar_y_responder",
                        "description" : "Herramienta obligatoria para generar la respuesta al cliente de Tornalba Suministros Técnicos S.A.S. y decidir si se requiere atención humana.",

                        "parameters":{
                            "type" : "object",
                            
                            "properties" : {
                                "respuesta_cliente" : {
                                    "type" : "string",
                                    "description" : "El mensaje de texto amigable, comercial y profesional que el bot le enviará al usuario por Telegram respondiendo sus dudas usando el catalogo"
                                },
                                "productos_interes" : {
                                    "type" : "string",
                                    "description" : "Retornar los productos de interes del cliente, separados por comas si son varios."
                                },
                                "ciudad" : {
                                    "type" : "string",
                                    "description" : "Ciudad desde donde el cliente realiza el contacto."
                                },
                                "debe_escalar" : {
                                    "type" : "boolean",
                                    "description" : "Actualizar el estado de escalación (True o False)"
                                }
                            },
                            "required" : ["respuesta_cliente", "debe_escalar"]
                        }
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "evaluar_y_responder"}}
        )
        texto_respuesta = response.choices[0].message.tool_calls[0].function.arguments
        datos_parseados = json.loads(texto_respuesta)

        respuesta = datos_parseados.get("respuesta_cliente", "")
        escalar = True if (datos_parseados.get("debe_escalar", False) in [True, "True", "true"]) else False
        productos_interes = datos_parseados.get("productos_interes") or ""
        # El modelo a veces devuelve los productos como lista aunque la herramienta pida un texto
        if isinstance(productos_interes, list):
            productos_interes = ", ".join(str(p) for p in productos_interes)
        productos_interes = str(productos_interes).strip()
        ciudad = str(datos_parseados.get("ciudad") or "").strip()

        if not ciudad or not productos_interes:
            escalar = False

        return {
            "respuesta" : respuesta, 
            "escalar" : escalar,
            "productos_interes": productos_interes,
            "ciudad": ciudad 
        }
    except (OpenAIError, json.JSONDecodeError, IndexError, TypeError):
        logger.exception(f"Error en la comunicación con el Agente de Groq [Conversación ID: {id_conversacion}]")
        return {
            "respuesta" : "Tuvimos un inconveniente técnico con nuestro sistema, pero tu solicitud ya quedó registrada y un asesor te va a contactar en breve.",
            "escalar" : True,
            "productos_interes": "Por confirmar",
            "ciudad": "Por confirmar"
        }

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