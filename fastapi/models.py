from datetime import date, datetime, timezone
import uuid
from uuid import UUID
from typing import Optional
from decimal import Decimal
from zoneinfo import ZoneInfo
from sqlalchemy import Column, DateTime, Index, JSON, text
from sqlmodel import SQLModel, Field

def ahora_utc():
    return datetime.now(timezone.utc)

# Las marcas de tiempo se guardan en UTC, pero el hoy del negocio es el de Colombia
def hoy_bogota():
    return datetime.now(ZoneInfo("America/Bogota")).date()

# Las columnas de fecha se declaran con zona para que Postgres devuelva datetimes comparables con ahora_utc()
def columna_fecha(nullable: bool = False):
    return Column(DateTime(timezone=True), nullable=nullable)

class conversaciones(SQLModel, table=True):
    id_conversacion: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    canal: str
    canal_user_id: str
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    estado: str = Field(default="activo")
    conv_actualizado_en: datetime = Field(default_factory=ahora_utc, sa_column=columna_fecha())

class mensajes(SQLModel, table=True):
    id_mensaje: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id_conversacion: UUID = Field(foreign_key="conversaciones.id_conversacion")
    rol: str
    contenido: str
    creado_en : datetime = Field(default_factory=ahora_utc, sa_column=columna_fecha())

class asesores(SQLModel, table=True):
    id_asesor : UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre_asesor : str
    chat_id : str = Field(default="6560871955")

class leads(SQLModel, table=True):
    # La base impide dos leads abiertos en la misma conversacion aunque lleguen dos mensajes a la vez
    __table_args__ = (Index("ix_un_lead_abierto_por_conversacion", "id_conversacion", unique=True, postgresql_where=text("estado_lead = 'en_proceso'")),)

    id_lead: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id_conversacion: UUID = Field(foreign_key="conversaciones.id_conversacion")
    productos_interes: Optional[str] = None
    estado_lead : str = Field(default="en_proceso")
    ciudad: Optional[str] = None
    lead_creado_en: datetime = Field(default_factory=ahora_utc, sa_column=columna_fecha())
    asesor_encargado: Optional[UUID] = Field(default=None, foreign_key="asesores.id_asesor")
    monto_estimado: Optional[Decimal] = None
    fecha_requerida: Optional[date] = None
    prioridad: Optional[float] = None
    nivel_prioridad: Optional[str] = None
    escalado: bool = Field(default=False, sa_column_kwargs={"server_default": text("false")})
    motivo_escalacion: Optional[str] = None
    escalado_en: Optional[datetime] = Field(default=None, sa_column=columna_fecha(nullable=True))
    cerrado_en: Optional[datetime] = Field(default=None, sa_column=columna_fecha(nullable=True))

class productos(SQLModel, table=True):
    id_producto: int = Field(primary_key=True)
    referencia: str
    nombre_producto: str
    categoria: str
    unidad: str
    precio_unitario: Decimal
    existencias: int
    actualizado_en: datetime = Field(default_factory=ahora_utc, sa_column=columna_fecha())

class items_solicitados(SQLModel, table=True):
    id_item: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id_lead: UUID = Field(foreign_key="leads.id_lead")
    id_producto: Optional[int] = Field(default=None, foreign_key="productos.id_producto")
    descripcion: str
    cantidad: Optional[int] = None
    precio_al_momento: Optional[Decimal] = None
    existencias_al_momento: Optional[int] = None

class evaluaciones_motor(SQLModel, table=True):
    id_evaluacion: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id_lead: UUID = Field(foreign_key="leads.id_lead")
    id_mensaje: UUID = Field(foreign_key="mensajes.id_mensaje")
    monto_estimado: Optional[Decimal] = None
    relacion_cliente: Optional[float] = None
    completitud: Optional[float] = None
    plazo_dias: Optional[int] = None
    prioridad: Optional[float] = None
    nivel_prioridad: Optional[str] = None
    reglas_activadas: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    creado_en: datetime = Field(default_factory=ahora_utc, sa_column=columna_fecha())
