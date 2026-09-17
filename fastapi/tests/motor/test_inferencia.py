import pytest
from app.motor.inferencia import operador_y, grado_de_activacion
from app.excepciones import ConfiguracionMotorInvalida

def test_operador_y_devuelve_el_menor_cuando_viene_primero():
    assert operador_y(0.3, 0.8) == pytest.approx(0.3)

def test_operador_y_devuelve_el_menor_cuando_viene_segundo():
    assert operador_y(0.8, 0.3) == pytest.approx(0.3)

def test_operador_y_con_los_dos_grados_iguales():
    assert operador_y(0.5, 0.5) == pytest.approx(0.5)

def test_operador_y_con_un_cero_devuelve_cero():
    assert operador_y(0.0, 0.9) == pytest.approx(0.0)

def test_operador_y_con_los_dos_plenos_devuelve_uno():
    assert operador_y(1.0, 1.0) == pytest.approx(1.0)

def test_grado_de_activacion_con_una_sola_condicion():
    assert grado_de_activacion([0.7]) == pytest.approx(0.7)

def test_grado_de_activacion_con_dos_condiciones():
    assert grado_de_activacion([0.4, 0.9]) == pytest.approx(0.4)

def test_grado_de_activacion_no_depende_del_orden():
    assert grado_de_activacion([0.9, 0.4]) == pytest.approx(0.4)

def test_grado_de_activacion_con_el_menor_en_el_medio():
    assert grado_de_activacion([0.6, 0.2, 0.8]) == pytest.approx(0.2)

def test_grado_de_activacion_con_tres_grados_iguales():
    assert grado_de_activacion([0.5, 0.5, 0.5]) == pytest.approx(0.5)

def test_grado_de_activacion_con_una_condicion_en_cero_apaga_la_regla():
    assert grado_de_activacion([0.0, 0.9, 0.7]) == pytest.approx(0.0)

def test_grado_de_activacion_con_todas_las_condiciones_plenas():
    assert grado_de_activacion([1.0, 1.0]) == pytest.approx(1.0)

def test_grado_de_activacion_con_flotantes_no_redondos():
    assert grado_de_activacion([0.33, 0.66]) == pytest.approx(0.33)

def test_grado_de_activacion_sin_condiciones_lanza_configuracion_motor_invalida():
    with pytest.raises(ConfiguracionMotorInvalida):
        grado_de_activacion([])
