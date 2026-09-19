import pytest
import uuid
from datetime import date
from decimal import Decimal
from models import productos, leads
from app.servicio.leads import construir_items_para_guardar, texto_estado_solicitud, calcular_monto_estimado, calcular_relacion_cliente
from app.servicio.leads import calcular_completitud, armar_entradas_del_motor
from app.servicio.leads import decidir_escalacion, texto_notificacion_asesor, frase_confirmacion_cliente

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

def item(id_producto: int, cantidad: int, precio: Decimal):
    return {"id_producto": id_producto, "descripcion": "producto de prueba", "cantidad": cantidad, "precio_al_momento": precio, "existencias_al_momento": None}

def lead_cerrado(estado_lead: str):
    return leads(id_conversacion=uuid.uuid4(), estado_lead=estado_lead)

def test_monto_de_dos_items_suma_precio_por_cantidad():
    assert calcular_monto_estimado(items=[item(1, 10, Decimal("14500")), item(2, 5, Decimal("32000"))]) == Decimal("305000")

def test_monto_de_item_sin_cantidad_cuenta_una_unidad():
    assert calcular_monto_estimado(items=[item(1, None, Decimal("14500"))]) == Decimal("14500")

def test_monto_de_item_sin_precio_no_suma():
    assert calcular_monto_estimado(items=[item(1, 2, Decimal("14500")), item(None, 3, None)]) == Decimal("29000")

def test_monto_de_lista_vacia_es_cero():
    assert calcular_monto_estimado(items=[]) == Decimal("0")

def test_relacion_cuenta_las_ventas_entre_los_leads_cerrados():
    assert calcular_relacion_cliente(leads_cerrados=[lead_cerrado("venta"), lead_cerrado("no_venta"), lead_cerrado("venta")]) == 2

def test_relacion_de_cliente_nuevo_es_cero():
    assert calcular_relacion_cliente(leads_cerrados=[]) == 0

def test_relacion_sin_ninguna_venta_es_cero():
    assert calcular_relacion_cliente(leads_cerrados=[lead_cerrado("no_venta"), lead_cerrado("no_venta"), lead_cerrado("no_venta")]) == 0

def test_completitud_con_todo_conocido_es_uno():
    assert calcular_completitud(items=[item(1, 10, Decimal("14500"))], ciudad="Cali") == pytest.approx(1.0)

def test_completitud_sin_items_y_con_ciudad_es_un_cuarto():
    assert calcular_completitud(items=[], ciudad="Cali") == pytest.approx(0.25)

def test_completitud_sin_ciudad_es_tres_cuartos():
    assert calcular_completitud(items=[item(1, 10, Decimal("14500"))], ciudad=None) == pytest.approx(0.75)

def test_completitud_con_un_item_fuera_de_catalogo_con_cantidad_no_baja():
    assert calcular_completitud(items=[item(1, 10, Decimal("14500")), item(None, 3, None)], ciudad="Cali") == pytest.approx(1.0)

def test_completitud_con_un_item_sin_cantidad_es_tres_cuartos():
    assert calcular_completitud(items=[item(1, None, Decimal("14500"))], ciudad="Cali") == pytest.approx(0.75)

def test_completitud_sin_items_y_con_ciudad_vacia_es_cero():
    assert calcular_completitud(items=[], ciudad="") == pytest.approx(0.0)

def test_completitud_de_pedido_mixto_con_el_fuera_de_catalogo_sin_cantidad_es_uno():
    assert calcular_completitud(items=[item(26, 3, Decimal("615000")), item(None, None, None)], ciudad="Cali") == pytest.approx(1.0)

def test_completitud_de_un_solo_item_fuera_de_catalogo_con_ciudad_es_un_cuarto():
    assert calcular_completitud(items=[item(None, 1, None)], ciudad="Cali") == pytest.approx(0.25)

def test_entradas_del_motor_traen_las_cuatro_claves():
    entradas = armar_entradas_del_motor(monto_estimado=Decimal("305000"), relacion_cliente=2, completitud=0.75, plazo_dias=7)
    assert sorted(entradas) == ["completitud", "monto_estimado", "plazo_dias", "relacion_cliente"]

def test_entradas_del_motor_convierten_el_monto_a_float():
    assert isinstance(armar_entradas_del_motor(monto_estimado=Decimal("305000"), relacion_cliente=2, completitud=0.75, plazo_dias=7)["monto_estimado"], float)

def test_entradas_del_motor_conservan_plazo_nulo():
    assert armar_entradas_del_motor(monto_estimado=Decimal("0"), relacion_cliente=0, completitud=0.0, plazo_dias=None)["plazo_dias"] is None

def test_entradas_del_motor_conservan_plazo_negativo_sin_recortar():
    assert armar_entradas_del_motor(monto_estimado=Decimal("0"), relacion_cliente=0, completitud=0.0, plazo_dias=-3)["plazo_dias"] == -3

def decidir(prioridad: float, solicita_asesor: bool = False, fallo_tecnico: bool = False, ya_escalado: bool = False):
    return decidir_escalacion(prioridad=prioridad, umbral=50, solicita_asesor=solicita_asesor, fallo_tecnico=fallo_tecnico, ya_escalado=ya_escalado)

def notificacion_de_pedido_grande():
    items = [item(14, 8, Decimal("1850000")), {"id_producto": None, "descripcion": "disco diamantado de 9 pulgadas", "cantidad": 2, "precio_al_momento": None, "existencias_al_momento": None}]
    return texto_notificacion_asesor(nombre_cliente="Juan Diego Ramírez", canal_user_id="6560871955", nivel_prioridad="critica", monto_estimado=Decimal("18700000"), items=items, fallo_tecnico=False)

def test_escalacion_de_lead_ya_escalado_no_se_repite():
    assert decidir(90, ya_escalado=True) is None

def test_escalacion_por_fallo_tecnico_sin_prioridad():
    assert decidir(None, fallo_tecnico=True) == "fallo_tecnico"

def test_escalacion_por_fallo_tecnico_gana_a_la_solicitud_del_cliente():
    assert decidir(None, solicita_asesor=True, fallo_tecnico=True) == "fallo_tecnico"

def test_escalacion_por_solicitud_del_cliente_con_prioridad_baja():
    assert decidir(20, solicita_asesor=True) == "solicitud_cliente"

def test_escalacion_por_solicitud_del_cliente_sin_prioridad():
    assert decidir(None, solicita_asesor=True) == "solicitud_cliente"

def test_escalacion_por_motor_sobre_el_umbral():
    assert decidir(70) == "motor"

def test_escalacion_por_motor_justo_en_el_umbral():
    assert decidir(50) == "motor"

def test_sin_escalacion_justo_debajo_del_umbral():
    assert decidir(49.9) is None

def test_sin_escalacion_sin_prioridad_ni_motivo():
    assert decidir(None) is None

def test_notificacion_nombra_el_nivel():
    assert "critica" in notificacion_de_pedido_grande()

def test_notificacion_formatea_el_monto_con_miles():
    assert "18.700.000" in notificacion_de_pedido_grande()

def test_notificacion_incluye_el_segundo_item():
    assert "disco diamantado de 9 pulgadas" in notificacion_de_pedido_grande()

def test_notificacion_por_fallo_tecnico_lo_menciona():
    assert "fallo técnico" in texto_notificacion_asesor(nombre_cliente="Juan Diego Ramírez", canal_user_id="6560871955", nivel_prioridad=None, monto_estimado=None, items=[], fallo_tecnico=True)

def test_notificacion_con_nombre_identifica_al_cliente_por_su_canal():
    assert "6560871955" in notificacion_de_pedido_grande()

def test_notificacion_sin_nombre_identifica_al_cliente_por_su_canal():
    assert "6560871955" in texto_notificacion_asesor(nombre_cliente=None, canal_user_id="6560871955", nivel_prioridad="alta", monto_estimado=Decimal("14800000"), items=[], fallo_tecnico=False)

def test_frase_para_el_cliente_nombra_al_asesor_y_lo_trata_de_usted():
    assert frase_confirmacion_cliente(nombre_asesor="Natalia Ramírez Rendón") == "Su solicitud ya quedó en manos de Natalia Ramírez Rendón, que lo va a contactar en breve."
