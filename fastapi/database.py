import os
from sqlmodel import create_engine, Session
from app.excepciones import ConfiguracionInvalida

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ConfiguracionInvalida

engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session #Pausa la función y entrega la sesión al endpoint. Cuando el endpoint termina, la función continúa y el with cierra la sesión automáticamente.
