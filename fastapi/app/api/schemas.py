from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
import uuid
from enum import Enum

class MensajeRespuesta(BaseModel):
    rol : str
    contenido : str
    
class ConversacionResumenSalida(BaseModel):
    id_conversacion: uuid.UUID
    canal_user_id: str
    nombre: Optional[str]
    ultimo_mensaje: str
    actualizado_en: datetime

class ItemSolicitadoSalida(BaseModel):
    id_producto: Optional[int]
    descripcion: str
    cantidad: Optional[int]
    precio_al_momento: Optional[float]
    existencias_al_momento: Optional[int]

# Montos y precios salen como float y no como Decimal para que el JSON los entregue como numero y no como texto
class LeadsPorAsesor(BaseModel):
    id_lead: uuid.UUID
    id_conversacion: uuid.UUID
    nombre_cliente: Optional[str]
    canal_user_id: str
    canal: str
    telefono: Optional[str]
    enlace_whatsapp: Optional[str]
    productos_interes: Optional[str]
    ciudad: Optional[str]
    prioridad: Optional[float]
    nivel_prioridad: Optional[str]
    monto_estimado: Optional[float]
    escalado: bool
    motivo_escalacion: Optional[str]
    fecha_requerida: Optional[date]
    creado_en: datetime
    items: list[ItemSolicitadoSalida]

class EvaluacionLeadSalida(BaseModel):
    monto_estimado: Optional[float]
    relacion_cliente: Optional[float]
    completitud: Optional[float]
    plazo_dias: Optional[int]
    prioridad: Optional[float]
    nivel_prioridad: Optional[str]
    reglas_activadas: list[dict]
    creado_en: datetime

class MensajeEntranteEntrada(BaseModel):
    canal: str
    canal_user_id: str
    nombre: Optional[str] = None
    texto: str

class NotificacionAsesorSalida(BaseModel):
    chat_id: str
    nombre_asesor: str
    texto: str

class MensajeEntranteSalida(BaseModel):
    respuesta_cliente: str
    notificacion_asesor: Optional[NotificacionAsesorSalida]

class ChatEntrada(BaseModel):
    canal_user_id: uuid.UUID
    nombre: Optional[str] = Field(default=None, max_length=80)
    texto: str = Field(min_length=1, max_length=1000)
    telefono: str = Field(pattern=r"^3\d{9}$")

class ChatSalida(BaseModel):
    respuesta_cliente: str

class ChatHistorialEntrada(BaseModel):
    canal_user_id: uuid.UUID

class ResumenDemandaSalida(BaseModel):
    solicitudes: int
    escaladas: int
    ventas: int
    no_ventas: int
    monto_total: float

class NoCubiertaSalida(BaseModel):
    referencia: str
    nombre_producto: str
    veces: int
    unidades_pedidas: int
    unidades_faltantes: int
    monto_faltante: float

class FueraDeCatalogoSalida(BaseModel):
    descripcion: str
    veces: int
    unidades: int

class SobrestockSalida(BaseModel):
    referencia: str
    nombre_producto: str
    existencias: int
    precio_unitario: float
    capital_inmovilizado: float

class DemandaSalida(BaseModel):
    inicio: date
    fin: date
    resumen: ResumenDemandaSalida
    no_cubierta: list[NoCubiertaSalida]
    fuera_de_catalogo: list[FueraDeCatalogoSalida]
    sobrestock: list[SobrestockSalida]

class EstadoCierreEnum(str, Enum):
    venta = "venta"
    no_venta = "no_venta"

class CerrarLeadEntrada(BaseModel):
    id_lead : uuid.UUID
    estado_lead : EstadoCierreEnum

class CerrarLeadSalida(BaseModel):
    id_lead : uuid.UUID
    estado_lead : str
    ok : bool = True

