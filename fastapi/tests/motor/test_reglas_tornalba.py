import pytest
from pathlib import Path
from app.motor.inferencia import evaluar_prioridad
from app.motor.reglas import cargar_configuracion

def configuracion_tornalba():
    return cargar_configuracion(str(Path(__file__).parents[2] / "app" / "motor" / "reglas.yaml"))

def evaluar(monto_estimado: float, relacion_cliente: float, completitud: float, plazo_dias: float):
    return evaluar_prioridad({"monto_estimado": monto_estimado, "relacion_cliente": relacion_cliente, "completitud": completitud, "plazo_dias": plazo_dias}, configuracion_tornalba())

def test_grande_urgente_cliente_nuevo_prioridad():
    assert evaluar(15000000, 0, 1.0, 1)["prioridad"] == pytest.approx(76.6667)

def test_grande_urgente_cliente_nuevo_nivel():
    assert evaluar(15000000, 0, 1.0, 1)["nivel"] == "critica"

def test_grande_sin_fecha_cliente_nuevo_prioridad():
    assert evaluar(15000000, 0, 1.0, None)["prioridad"] == pytest.approx(70.0)

def test_grande_sin_fecha_cliente_nuevo_nivel():
    assert evaluar(15000000, 0, 1.0, None)["nivel"] == "alta"

def test_grande_urgente_cliente_recurrente_prioridad():
    assert evaluar(15000000, 3, 1.0, 1)["prioridad"] == pytest.approx(80.0)

def test_grande_urgente_cliente_recurrente_nivel():
    assert evaluar(15000000, 3, 1.0, 1)["nivel"] == "critica"

def test_mediano_urgente_cliente_nuevo_prioridad():
    assert evaluar(3000000, 0, 1.0, 1)["prioridad"] == pytest.approx(61.6667)

def test_mediano_urgente_cliente_nuevo_nivel():
    assert evaluar(3000000, 0, 1.0, 1)["nivel"] == "alta"

def test_pequeno_urgente_cliente_nuevo_prioridad():
    assert evaluar(100000, 0, 1.0, 0)["prioridad"] == pytest.approx(32.5)

def test_pequeno_urgente_cliente_nuevo_nivel():
    assert evaluar(100000, 0, 1.0, 0)["nivel"] == "media"

def test_pequeno_sin_afan_cliente_nuevo_prioridad():
    assert evaluar(100000, 0, 1.0, 30)["prioridad"] == pytest.approx(20.0)

def test_pequeno_sin_afan_cliente_nuevo_nivel():
    assert evaluar(100000, 0, 1.0, 30)["nivel"] == "baja"

def test_grande_urgente_supera_a_grande_sin_fecha_en_cliente_nuevo():
    assert evaluar(15000000, 0, 1.0, 1)["prioridad"] > evaluar(15000000, 0, 1.0, None)["prioridad"]

def test_configuracion_real_tiene_quince_reglas():
    assert len(configuracion_tornalba()["reglas"]) == 15
