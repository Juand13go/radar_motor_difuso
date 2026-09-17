from sqlmodel import select, Session
from models import productos, asesores
import json
from database import engine

with open("productos.json", "r", encoding="utf-8") as f: 
    datos_productos = json.load(f)

def poblar_productos():
    with Session(engine) as session:
        for prod in datos_productos:
            existe = session.exec(select(productos).where(productos.id_producto == prod["id_producto"])).first()
            if not existe:
                producto = productos(**prod)
                session.add(producto)
                print(f"El producto {prod['nombre_producto']} fue agregado con éxito.")
            else: 
                print(f"El producto {prod['nombre_producto']} ya existe en la base de datos.")
        session.commit()


with open("asesores.json", "r", encoding="utf-8") as a:
    datos_asesores = json.load(a)
    
def poblar_asesores():
    with Session(engine) as session:
        for ases in datos_asesores:
            id_asesor = ases.get("id_asesor")
            existe = None

            if id_asesor:
                existe = session.exec(select(asesores).where(asesores.id_asesor == id_asesor)).first()

            if not existe:
                asesor = asesores(**ases)
                session.add(asesor)
                print(f"El asesor {asesor.nombre_asesor} fue agregado con éxito.")
            else:
                print(f"El asesor {ases['nombre_asesor']} ya existe en la base de datos.")

        session.commit()

if __name__ == "__main__":
    poblar_productos()
    poblar_asesores()
