from sqlmodel import Session
from app.persistencia.repositorio import obtener_productos

def productos_para_catalogo(productos: list):
    catalogo = [
        {"referencia": p.referencia, "nombre_producto": p.nombre_producto, "categoria": p.categoria, "unidad": p.unidad, "precio_unitario": p.precio_unitario}
        for p in productos
    ]
    return sorted(catalogo, key=lambda p: (p["categoria"], p["referencia"]))

def catalogo_publico(session: Session):
    return productos_para_catalogo(productos=obtener_productos(session=session))
