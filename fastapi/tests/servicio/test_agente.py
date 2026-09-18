from datetime import date
from app.servicio.agente import validar_extraccion, TEXTO_FALLO_TECNICO

HOY = date(2026, 9, 18)
IDS_VALIDOS = [1, 2, 3, 4, 5]

def extraccion_completa():
    return {
        "respuesta_cliente": "Con gusto. Queda registrada su solicitud.",
        "items": [
            {"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": 10},
            {"id_producto": 2, "descripcion": "tornillo autoperforante", "cantidad": 5}
        ],
        "ciudad": "Medellín",
        "fecha_requerida": "2026-09-25",
        "solicita_asesor": False
    }

def validar(extraccion: dict):
    return validar_extraccion(extraccion=extraccion, ids_validos=IDS_VALIDOS, hoy=HOY)

def test_extraccion_completa_se_devuelve_con_plazo_calculado():
    assert validar(extraccion_completa()) == {
        "respuesta_cliente": "Con gusto. Queda registrada su solicitud.",
        "items": [
            {"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": 10},
            {"id_producto": 2, "descripcion": "tornillo autoperforante", "cantidad": 5}
        ],
        "ciudad": "Medellín",
        "fecha_requerida": date(2026, 9, 25),
        "plazo_dias": 7,
        "solicita_asesor": False,
        "fallo_tecnico": False
    }

def test_id_producto_que_no_existe_queda_nulo_y_conserva_descripcion_y_cantidad():
    extraccion = extraccion_completa()
    extraccion["items"] = [{"id_producto": 99, "descripcion": "disco diamantado de 9 pulgadas", "cantidad": 2}]
    assert validar(extraccion)["items"] == [{"id_producto": None, "descripcion": "disco diamantado de 9 pulgadas", "cantidad": 2}]

def test_fecha_con_formato_invalido_queda_nula_y_sin_plazo():
    extraccion = extraccion_completa()
    extraccion["fecha_requerida"] = "2026-13-45"
    resultado = validar(extraccion)
    assert (resultado["fecha_requerida"], resultado["plazo_dias"]) == (None, None)

def test_sin_fecha_requerida_el_plazo_es_nulo():
    extraccion = extraccion_completa()
    del extraccion["fecha_requerida"]
    assert validar(extraccion)["plazo_dias"] is None

def test_fecha_de_ayer_da_plazo_menos_uno():
    extraccion = extraccion_completa()
    extraccion["fecha_requerida"] = "2026-09-17"
    assert validar(extraccion)["plazo_dias"] == -1

def test_fecha_de_hoy_da_plazo_cero():
    extraccion = extraccion_completa()
    extraccion["fecha_requerida"] = "2026-09-18"
    assert validar(extraccion)["plazo_dias"] == 0

def test_sin_items_devuelve_lista_vacia():
    extraccion = extraccion_completa()
    del extraccion["items"]
    assert validar(extraccion)["items"] == []

def test_sin_ciudad_ni_solicita_asesor_toma_los_valores_por_defecto():
    extraccion = extraccion_completa()
    del extraccion["ciudad"]
    del extraccion["solicita_asesor"]
    resultado = validar(extraccion)
    assert (resultado["ciudad"], resultado["solicita_asesor"]) == (None, False)

def test_item_sin_cantidad_la_conserva_nula_y_no_se_descarta():
    extraccion = extraccion_completa()
    extraccion["items"] = [{"id_producto": 1, "descripcion": "tornillo drywall"}]
    assert validar(extraccion)["items"] == [{"id_producto": 1, "descripcion": "tornillo drywall", "cantidad": None}]

def test_diccionario_vacio_usa_el_texto_de_fallo_y_los_valores_por_defecto():
    assert validar({}) == {
        "respuesta_cliente": TEXTO_FALLO_TECNICO,
        "items": [],
        "ciudad": None,
        "fecha_requerida": None,
        "plazo_dias": None,
        "solicita_asesor": False,
        "fallo_tecnico": True
    }

def test_respuesta_cliente_vacia_usa_el_texto_de_fallo_y_marca_fallo_tecnico():
    extraccion = extraccion_completa()
    extraccion["respuesta_cliente"] = ""
    resultado = validar(extraccion)
    assert (resultado["respuesta_cliente"], resultado["fallo_tecnico"]) == (TEXTO_FALLO_TECNICO, True)

def test_id_producto_como_texto_de_un_entero_se_convierte():
    extraccion = extraccion_completa()
    extraccion["items"] = [{"id_producto": "5", "descripcion": "brocha de 3 pulgadas", "cantidad": 4}]
    assert validar(extraccion)["items"] == [{"id_producto": 5, "descripcion": "brocha de 3 pulgadas", "cantidad": 4}]

def test_id_producto_como_texto_que_no_es_entero_queda_nulo():
    extraccion = extraccion_completa()
    extraccion["items"] = [{"id_producto": "abc", "descripcion": "brocha de 3 pulgadas", "cantidad": 4}]
    assert validar(extraccion)["items"] == [{"id_producto": None, "descripcion": "brocha de 3 pulgadas", "cantidad": 4}]
