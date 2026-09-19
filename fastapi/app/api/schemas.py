from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
import uuid
from enum import Enum

class ConversacionCrear(BaseModel):
    canal_user_id : str
    canal: str
    nombre: str

class ConversacionRespuesta(BaseModel):
    id_conversacion: uuid.UUID

class MensajeRespuesta(BaseModel):
    rol : str
    contenido : str
    
class GuardarMensajeEntrada(BaseModel):
    id_conversacion : uuid.UUID
    rol : str
    contenido : str

class EstadoEntrada(BaseModel):
    estado : str
    id_conversacion : uuid.UUID

class EstadoSalida(BaseModel):
    estado : str

class LeadEntrada(BaseModel):
    id_conversacion: uuid.UUID
    productos_interes: str = Field(min_length=1)
    ciudad: str = Field(min_length=1)

class ProcesarEntrada(BaseModel):
    id_conversacion : uuid.UUID

class ProcesarSalida(BaseModel):
    respuesta : str
    escalar : bool
    productos_interes : Optional[str]
    ciudad : Optional[str]

class LeadSalida(BaseModel):
    id_lead : uuid.UUID

class ConfirmacionRespuesta(BaseModel):
    ok: bool

class AsesorSalida(BaseModel):
    asesor_encargado : uuid.UUID 

class AsesorEntrada(BaseModel):
    id_lead : uuid.UUID

class ObtenerAsesorSalida(BaseModel):
    id_asesor : uuid.UUID
    nombre_asesor : str 
    chat_id : str

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

