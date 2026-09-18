import pytest
from pathlib import Path
from app.motor.inferencia import evaluar_prioridad
from app.motor.reglas import cargar_configuracion
from app.excepciones import EntradaMotorInvalida

def configuracion_de_prueba():
    return cargar_configuracion(str(Path(__file__).parent / "reglas_prueba.yaml"))

def evaluar(monto_estimado: float, plazo_dias: float):
    return evaluar_prioridad({"monto_estimado": monto_estimado, "plazo_dias": plazo_dias}, configuracion_de_prueba())

def nombres(resultado: dict):
    return [regla["nombre"] for regla in resultado["reglas_activadas"]]

def test_pedido_grande_urgente_prioridad():
    assert evaluar(80, 2)["prioridad"] == pytest.approx(1.42 / 1.8)

def test_pedido_grande_urgente_nivel():
    assert evaluar(80, 2)["nivel"] == "critica"

def test_pedido_grande_urgente_reglas_ordenadas_por_grado():
    assert nombres(evaluar(80, 2)) == ["pedido_grande", "pedido_grande_urgente"]

def test_pedido_grande_urgente_grados_de_las_reglas():
    assert [regla["grado"] for regla in evaluar(80, 2)["reglas_activadas"]] == pytest.approx([1.0, 0.8])

def test_pedido_pequeno_sin_afan_prioridad():
    assert evaluar(10, 20)["prioridad"] == pytest.approx(0.2)

def test_pedido_pequeno_sin_afan_nivel():
    assert evaluar(10, 20)["nivel"] == "baja"

def test_pedido_pequeno_sin_afan_reglas():
    assert nombres(evaluar(10, 20)) == ["pedido_pequeno_sin_afan"]

def test_empate_prioridad():
    assert evaluar(35, 10)["prioridad"] == pytest.approx(0.45)

def test_empate_nivel():
    assert evaluar(35, 10)["nivel"] == "media"

def test_empate_conserva_el_orden_del_yaml():
    assert nombres(evaluar(35, 10)) == ["pedido_pequeno_sin_afan", "pedido_grande"]

def test_fuera_del_universo_prioridad():
    assert evaluar(500, -3)["prioridad"] == pytest.approx(0.8)

def test_fuera_del_universo_nivel():
    assert evaluar(500, -3)["nivel"] == "critica"

def test_fuera_del_universo_recorta_las_entradas():
    assert evaluar(500, -3)["entradas"] == {"monto_estimado": 100, "plazo_dias": 0}

def test_sin_reglas_activas_prioridad_es_none():
    resultado = evaluar(10, 2)
    assert resultado["prioridad"] is None

def test_sin_reglas_activas_nivel_es_none():
    resultado = evaluar(10, 2)
    assert resultado["nivel"] is None

def test_sin_reglas_activas_no_hay_reglas_activadas():
    assert evaluar(10, 2)["reglas_activadas"] == []

def test_plazo_desconocido_prioridad():
    assert evaluar(80, None)["prioridad"] == pytest.approx(0.7)

def test_plazo_desconocido_solo_activa_pedido_grande():
    assert nombres(evaluar(80, None)) == ["pedido_grande"]

def test_entradas_sin_una_variable_lanza_entrada_motor_invalida():
    with pytest.raises(EntradaMotorInvalida):
        evaluar_prioridad({"monto_estimado": 80}, configuracion_de_prueba())

def test_entradas_con_una_variable_de_mas_lanza_entrada_motor_invalida():
    with pytest.raises(EntradaMotorInvalida):
        evaluar_prioridad({"monto_estimado": 80, "plazo_dias": 2, "urgencia": 1}, configuracion_de_prueba())
