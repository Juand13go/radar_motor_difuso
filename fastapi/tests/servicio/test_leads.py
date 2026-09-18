from datetime import date
from decimal import Decimal
from models import productos
from app.servicio.leads import construir_items_para_guardar, texto_estado_solicitud

def productos_por_id():
    return {
        1: productos(id_producto=1, referencia="TOR-001", nombre_producto="Tornillo drywall punta fina 6x1 caja x100", categoria="Fijación y tornillería", unidad="caja", precio_unitario=Decimal("14500"), existencias=320),
        2: productos(id_producto=2, referencia="TOR-002", nombre_producto="Tornillo autoperforante 12x1 caja x100", categoria="Fijación y tornillería", unidad="caja", precio_unitario=Decimal("32000"), existencias=0)
    }

def test_item_del_catalogo_copia_precio_y_existencias():
    items = [{"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": 10}]
    assert construir_items_para_guardar(items_extraidos=items, productos_por_id=productos_por_id()) == [
        {"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": 10, "precio_al_momento": Decimal("14500"), "existencias_al_momento": 320}
    ]

def test_item_sin_id_deja_precio_y_existencias_nulos_y_conserva_descripcion_y_cantidad():
    items = [{"id_producto": None, "descripcion": "disco diamantado de 9 pulgadas", "cantidad": 2}]
    assert construir_items_para_guardar(items_extraidos=items, productos_por_id=productos_por_id()) == [
        {"id_producto": None, "descripcion": "disco diamantado de 9 pulgadas", "cantidad": 2, "precio_al_momento": None, "existencias_al_momento": None}
    ]

def test_item_con_id_que_no_esta_en_el_diccionario_queda_fuera_de_catalogo():
    items = [{"id_producto": 99, "descripcion": "brocha de 3 pulgadas", "cantidad": 4}]
    assert construir_items_para_guardar(items_extraidos=items, productos_por_id=productos_por_id()) == [
        {"id_producto": None, "descripcion": "brocha de 3 pulgadas", "cantidad": 4, "precio_al_momento": None, "existencias_al_momento": None}
    ]

def test_lista_vacia_devuelve_lista_vacia():
    assert construir_items_para_guardar(items_extraidos=[], productos_por_id=productos_por_id()) == []

def test_dos_items_conservan_el_orden():
    items = [
        {"id_producto": 2, "descripcion": "tornillo autoperforante", "cantidad": 5},
        {"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": 10}
    ]
    assert [item["descripcion"] for item in construir_items_para_guardar(items_extraidos=items, productos_por_id=productos_por_id())] == ["tornillo autoperforante", "tornillo drywall"]

def test_item_sin_cantidad_la_conserva_nula_y_copia_precio_y_existencias():
    items = [{"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": None}]
    assert construir_items_para_guardar(items_extraidos=items, productos_por_id=productos_por_id()) == [
        {"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": None, "precio_al_momento": Decimal("14500"), "existencias_al_momento": 320}
    ]

def test_estado_sin_datos_es_sin_solicitud_abierta():
    assert texto_estado_solicitud(ciudad=None, fecha_requerida=None, items=[]) == "Sin solicitud abierta"

def test_estado_con_dos_items_contiene_las_dos_descripciones():
    items = [{"descripcion": "tornillo drywall", "cantidad": 10}, {"descripcion": "disco diamantado de 9 pulgadas", "cantidad": None}]
    texto = texto_estado_solicitud(ciudad=None, fecha_requerida=None, items=items)
    assert all(descripcion in texto for descripcion in ["tornillo drywall", "disco diamantado de 9 pulgadas"])

def test_estado_con_ciudad_la_contiene():
    assert "Medellín" in texto_estado_solicitud(ciudad="Medellín", fecha_requerida=None, items=[])

def test_estado_con_fecha_la_contiene_en_formato_iso():
    assert "2026-09-25" in texto_estado_solicitud(ciudad=None, fecha_requerida=date(2026, 9, 25), items=[])
