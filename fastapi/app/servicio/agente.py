from sqlmodel import Session
from app.persistencia.repositorio import obtener_productos
from app.servicio.conversacion import obtener_historial_conversacion
from models import hoy_bogota
from datetime import date, datetime
from pathlib import Path
from openai import OpenAI, OpenAIError
import uuid
import json
import os
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1", max_retries=4, timeout=20.0)

MODELO_AGENTE = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Se arma con str.format, asi que una llave literal dentro de agente.md tiene que ir doble
PROMPT_AGENTE = (Path(__file__).resolve().parents[2] / "prompts" / "agente.md").read_text(encoding="utf-8")

TEXTO_FALLO_TECNICO = "Tuvimos un inconveniente técnico con nuestro sistema, pero tu solicitud ya quedó registrada y un asesor te va a contactar en breve."

HERRAMIENTA_AGENTE = {
    "type": "function",
    "function": {
        "name": "registrar_solicitud",
        "description": "Herramienta obligatoria para responder al cliente de Tornalba Suministros Técnicos S.A.S. y registrar lo que ha pedido hasta ahora.",
        "parameters": {
            "type": "object",
            "properties": {
                "respuesta_cliente": {
                    "type": "string",
                    "description": "Texto que se le envía al cliente: de usted, breve, claro y sin emojis."
                },
                "items": {
                    "type": "array",
                    "description": "Lista completa y actual de los productos que el cliente ha pedido en toda la conversación, no solo los de su último mensaje. Vacía si todavía no ha pedido ninguno.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id_producto": {
                                "type": ["integer", "null"],
                                "description": "ID exacto del producto en el catálogo. Nulo si el producto no está en el catálogo."
                            },
                            "descripcion": {
                                "type": "string",
                                "description": "Nombre genérico y corto del producto, por ejemplo disco diamantado de 9 pulgadas."
                            },
                            "cantidad": {
                                "type": ["integer", "null"],
                                "description": "Cantidad que pidió el cliente. Nula si no la ha dicho."
                            }
                        },
                        "required": ["id_producto", "descripcion", "cantidad"]
                    }
                },
                "ciudad": {
                    "type": ["string", "null"],
                    "description": "Ciudad del cliente. Nula si no la ha dicho."
                },
                "fecha_requerida": {
                    "type": ["string", "null"],
                    "description": "Fecha para la que el cliente necesita los productos, en formato AAAA-MM-DD, calculada contra la fecha de hoy. Nula si el cliente no mencionó ninguna fecha ni plazo."
                },
                "solicita_asesor": {
                    "type": "boolean",
                    "description": "Verdadero solo si el cliente pidió explícitamente hablar con una persona. Falso en cualquier otro caso."
                }
            },
            "required": ["respuesta_cliente", "items", "ciudad", "fecha_requerida", "solicita_asesor"]
        }
    }
}

def catalogo_a_texto(session: Session):
    producto = obtener_productos(session)
    catalogo_productos = [f" ID: {c.id_producto} | Producto: {c.nombre_producto} | Referencia: {c.referencia} | Precio unitario:  {c.precio_unitario} | Unidad: {c.unidad} | Existencias: {c.existencias} | Categoría: {c.categoria} " for c in producto]
    catalogo_productos_variable = "\n".join(catalogo_productos)
    return catalogo_productos_variable

def armar_prompt_agente(catalogo: str, estado_solicitud: str):
    return PROMPT_AGENTE.format(fecha_actual=hoy_bogota().isoformat(), catalogo=catalogo, estado_solicitud=estado_solicitud)

def convertir_fecha(texto: str):
    # strptime acepta meses y dias de un digito, por eso se exige el largo exacto de AAAA-MM-DD
    if not isinstance(texto, str) or len(texto) != 10:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None

def convertir_id_producto(valor: int):
    # bool es subclase de int: sin este filtro un True pasaria como el producto 1
    if isinstance(valor, bool):
        return None
    if isinstance(valor, str):
        try:
            return int(valor)
        except ValueError:
            return None
    return valor

def validar_extraccion(extraccion: dict, ids_validos: list[int], hoy: date):
    if not isinstance(extraccion, dict):
        extraccion = {}

    respuesta_cliente = extraccion.get("respuesta_cliente")
    fallo_tecnico = False
    if not isinstance(respuesta_cliente, str) or not respuesta_cliente.strip():
        respuesta_cliente = TEXTO_FALLO_TECNICO
        fallo_tecnico = True

    items = []
    for item in extraccion.get("items") or []:
        if not isinstance(item, dict):
            continue
        id_producto = convertir_id_producto(item.get("id_producto"))
        if id_producto not in ids_validos:
            id_producto = None
        items.append({"id_producto": id_producto, "descripcion": item.get("descripcion"), "cantidad": item.get("cantidad")})

    fecha_requerida = convertir_fecha(extraccion.get("fecha_requerida"))
    plazo_dias = None
    if fecha_requerida is not None:
        plazo_dias = (fecha_requerida - hoy).days

    return {
        "respuesta_cliente": respuesta_cliente,
        "items": items,
        "ciudad": extraccion.get("ciudad"),
        "fecha_requerida": fecha_requerida,
        "plazo_dias": plazo_dias,
        "solicita_asesor": extraccion.get("solicita_asesor") is True,
        "fallo_tecnico": fallo_tecnico
    }

def comunicacion_agente(id_conversacion: uuid.UUID, session: Session):
    historial = obtener_historial_conversacion(id_conversacion=id_conversacion, session=session)
    catalogo_productos_variable = catalogo_a_texto(session)
    ids_validos = [producto.id_producto for producto in obtener_productos(session)]
    try:
        response = client.chat.completions.create(
            model = MODELO_AGENTE,
            max_tokens = 1024,
            messages=[{
                        "role": "system", "content": armar_prompt_agente(catalogo=catalogo_productos_variable, estado_solicitud="Sin solicitud abierta")
            }] + [{"role" : m.rol, "content" : m.contenido} for m in historial],
            tools=[HERRAMIENTA_AGENTE],
            tool_choice={"type": "function", "function": {"name": "registrar_solicitud"}}
        )
        texto_respuesta = response.choices[0].message.tool_calls[0].function.arguments
        extraccion = json.loads(texto_respuesta)
        return validar_extraccion(extraccion=extraccion, ids_validos=ids_validos, hoy=hoy_bogota())
    except (OpenAIError, json.JSONDecodeError, IndexError, TypeError):
        logger.exception(f"Error en la comunicación con el Agente de Groq [Conversación ID: {id_conversacion}]")
        return {
            "respuesta_cliente": TEXTO_FALLO_TECNICO,
            "items": [],
            "ciudad": None,
            "fecha_requerida": None,
            "plazo_dias": None,
            "solicita_asesor": False,
            "fallo_tecnico": True
        }
