from decimal import Decimal
from models import productos
from app.servicio.catalogo import productos_para_catalogo

def producto(id_producto: int, referencia: str, categoria: str, precio_unitario: Decimal, existencias: int):
    return productos(id_producto=id_producto, referencia=referencia, nombre_producto="Producto de prueba", categoria=categoria, unidad="unidad", precio_unitario=precio_unitario, existencias=existencias)

def test_catalogo_no_incluye_existencias():
    lista = [producto(id_producto=1, referencia="TOR-001", categoria="Fijación y tornillería", precio_unitario=Decimal("14500"), existencias=320)]
    assert "existencias" not in productos_para_catalogo(productos=lista)[0]

def test_catalogo_no_incluye_id_producto():
    lista = [producto(id_producto=1, referencia="TOR-001", categoria="Fijación y tornillería", precio_unitario=Decimal("14500"), existencias=320)]
    assert "id_producto" not in productos_para_catalogo(productos=lista)[0]

def test_catalogo_ordena_por_categoria_y_referencia():
    lista = [
        producto(id_producto=1, referencia="HEL-002", categoria="Herramienta eléctrica", precio_unitario=Decimal("250000"), existencias=5),
        producto(id_producto=2, referencia="TOR-001", categoria="Fijación y tornillería", precio_unitario=Decimal("14500"), existencias=320),
        producto(id_producto=3, referencia="HEL-001", categoria="Herramienta eléctrica", precio_unitario=Decimal("180000"), existencias=8)
    ]
    assert [p["referencia"] for p in productos_para_catalogo(productos=lista)] == ["TOR-001", "HEL-001", "HEL-002"]

def test_catalogo_conserva_el_precio():
    lista = [producto(id_producto=1, referencia="TOR-001", categoria="Fijación y tornillería", precio_unitario=Decimal("14500"), existencias=320)]
    assert productos_para_catalogo(productos=lista)[0]["precio_unitario"] == 14500

def test_catalogo_vacio_devuelve_lista_vacia():
    assert productos_para_catalogo(productos=[]) == []
