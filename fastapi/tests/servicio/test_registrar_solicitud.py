from sqlmodel import Session, select
from database import engine
from models import leads
from app.persistencia.repositorio import creacion_conversacion, obtener_items_de_lead
from app.servicio.leads import registrar_solicitud

# Cada prueba corre en una transaccion que se deshace al final: los commit del repositorio solo liberan savepoints
def en_transaccion_deshecha(prueba):
    with engine.connect() as conexion:
        externa = conexion.begin()
        session = Session(bind=conexion, join_transaction_mode="create_savepoint")
        try:
            return prueba(session)
        finally:
            session.close()
            externa.rollback()

def extraccion_con_dos_items():
    return {
        "items": [
            {"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": 10},
            {"id_producto": None, "descripcion": "disco diamantado de 9 pulgadas", "cantidad": 2}
        ],
        "ciudad": "Cali",
        "fecha_requerida": None,
        "fallo_tecnico": False
    }

def extraccion_con_fallo_tecnico(items: list):
    return {"items": items, "ciudad": None, "fecha_requerida": None, "fallo_tecnico": True}

def test_fallo_tecnico_deja_intactos_los_items_del_lead():
    def prueba(session):
        conversacion = creacion_conversacion(canal_user_id="prueba_fallo_con_lead", canal="telegram", nombre="Prueba", session=session)
        lead = registrar_solicitud(id_conversacion=conversacion.id_conversacion, extraccion=extraccion_con_dos_items(), session=session)
        registrar_solicitud(id_conversacion=conversacion.id_conversacion, extraccion=extraccion_con_fallo_tecnico(items=[]), session=session)
        return sorted(item.descripcion for item in obtener_items_de_lead(id_lead=lead.id_lead, session=session))
    assert en_transaccion_deshecha(prueba) == ["disco diamantado de 9 pulgadas", "tornillo drywall"]

def test_fallo_tecnico_sin_lead_abierto_no_crea_ninguno():
    def prueba(session):
        conversacion = creacion_conversacion(canal_user_id="prueba_fallo_sin_lead", canal="telegram", nombre="Prueba", session=session)
        registrar_solicitud(id_conversacion=conversacion.id_conversacion, extraccion=extraccion_con_fallo_tecnico(items=extraccion_con_dos_items()["items"]), session=session)
        return session.exec(select(leads).where(leads.id_conversacion == conversacion.id_conversacion)).all()
    assert en_transaccion_deshecha(prueba) == []
