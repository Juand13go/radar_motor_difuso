from datetime import datetime, timezone
import uuid
from uuid import UUID
from typing import Optional
from decimal import Decimal
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field

def ahora_utc():
    return datetime.now(timezone.utc)

# Las columnas de fecha se declaran con zona para que Postgres devuelva datetimes comparables con ahora_utc()
def columna_fecha():
    return Column(DateTime(timezone=True), nullable=False)

class conversaciones(SQLModel, table=True):
    id_conversacion: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    canal: str
    canal_user_id: str
    nombre: Optional[str] = None
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
    id_lead: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id_conversacion: UUID = Field(foreign_key="conversaciones.id_conversacion")
    productos_interes: str
    estado_lead : str = Field(default="en_proceso")
    ciudad: str
    lead_creado_en: datetime = Field(default_factory=ahora_utc, sa_column=columna_fecha())
    asesor_encargado: Optional[UUID] = Field(default=None, foreign_key="asesores.id_asesor")

class productos(SQLModel, table=True):
    id_producto: int = Field(primary_key=True)
    referencia: str
    nombre_producto: str
    categoria: str
    unidad: str
    precio_unitario: Decimal
    existencias: int
    actualizado_en: datetime = Field(default_factory=ahora_utc, sa_column=columna_fecha())
