import pytest
from app.motor.pertenencia import triangular, trapezoidal

def test_triangular_por_debajo_del_soporte_vale_cero():
    assert triangular(5, 10, 20, 40) == pytest.approx(0.0)

def test_triangular_justo_en_a_vale_cero():
    assert triangular(10, 10, 20, 40) == pytest.approx(0.0)

def test_triangular_al_comenzar_la_rampa_izquierda():
    assert triangular(12, 10, 20, 40) == pytest.approx(0.2)

def test_triangular_a_mitad_de_la_rampa_izquierda():
    assert triangular(15, 10, 20, 40) == pytest.approx(0.5)

def test_triangular_en_el_pico_vale_uno():
    assert triangular(20, 10, 20, 40) == pytest.approx(1.0)

def test_triangular_al_comenzar_la_rampa_derecha():
    assert triangular(25, 10, 20, 40) == pytest.approx(0.75)

def test_triangular_a_mitad_de_la_rampa_derecha():
    assert triangular(30, 10, 20, 40) == pytest.approx(0.5)

def test_triangular_justo_en_c_vale_cero():
    assert triangular(40, 10, 20, 40) == pytest.approx(0.0)

def test_triangular_por_encima_del_soporte_vale_cero():
    assert triangular(45, 10, 20, 40) == pytest.approx(0.0)

def test_triangular_con_lado_izquierdo_colapsado_por_debajo_vale_cero():
    assert triangular(-1, 0, 0, 10) == pytest.approx(0.0)

def test_triangular_con_lado_izquierdo_colapsado_en_el_pico_vale_uno():
    assert triangular(0, 0, 0, 10) == pytest.approx(1.0)

def test_triangular_con_lado_izquierdo_colapsado_a_mitad_de_la_rampa():
    assert triangular(5, 0, 0, 10) == pytest.approx(0.5)

def test_triangular_con_lado_izquierdo_colapsado_justo_en_c_vale_cero():
    assert triangular(10, 0, 0, 10) == pytest.approx(0.0)

def test_triangular_con_lado_derecho_colapsado_a_mitad_de_la_rampa():
    assert triangular(5, 0, 10, 10) == pytest.approx(0.5)

def test_triangular_con_lado_derecho_colapsado_en_el_pico_vale_uno():
    assert triangular(10, 0, 10, 10) == pytest.approx(1.0)

def test_triangular_con_lado_derecho_colapsado_por_encima_vale_cero():
    assert triangular(11, 0, 10, 10) == pytest.approx(0.0)

def test_trapezoidal_por_debajo_del_soporte_vale_cero():
    assert trapezoidal(5, 10, 20, 40, 60) == pytest.approx(0.0)

def test_trapezoidal_justo_en_a_vale_cero():
    assert trapezoidal(10, 10, 20, 40, 60) == pytest.approx(0.0)

def test_trapezoidal_al_comenzar_la_rampa_izquierda():
    assert trapezoidal(12, 10, 20, 40, 60) == pytest.approx(0.2)

def test_trapezoidal_a_mitad_de_la_rampa_izquierda():
    assert trapezoidal(15, 10, 20, 40, 60) == pytest.approx(0.5)

def test_trapezoidal_en_el_borde_izquierdo_de_la_meseta_vale_uno():
    assert trapezoidal(20, 10, 20, 40, 60) == pytest.approx(1.0)

def test_trapezoidal_en_el_centro_de_la_meseta_vale_uno():
    assert trapezoidal(30, 10, 20, 40, 60) == pytest.approx(1.0)

def test_trapezoidal_en_el_borde_derecho_de_la_meseta_vale_uno():
    assert trapezoidal(40, 10, 20, 40, 60) == pytest.approx(1.0)

def test_trapezoidal_al_comenzar_la_rampa_derecha():
    assert trapezoidal(45, 10, 20, 40, 60) == pytest.approx(0.75)

def test_trapezoidal_a_mitad_de_la_rampa_derecha():
    assert trapezoidal(50, 10, 20, 40, 60) == pytest.approx(0.5)

def test_trapezoidal_justo_en_d_vale_cero():
    assert trapezoidal(60, 10, 20, 40, 60) == pytest.approx(0.0)

def test_trapezoidal_por_encima_del_soporte_vale_cero():
    assert trapezoidal(65, 10, 20, 40, 60) == pytest.approx(0.0)

def test_trapezoidal_con_hombro_izquierdo_por_debajo_del_universo_vale_cero():
    assert trapezoidal(-5, 0, 0, 20, 40) == pytest.approx(0.0)

def test_trapezoidal_con_hombro_izquierdo_en_el_hombro_vale_uno():
    assert trapezoidal(0, 0, 0, 20, 40) == pytest.approx(1.0)

def test_trapezoidal_con_hombro_izquierdo_en_el_borde_derecho_de_la_meseta_vale_uno():
    assert trapezoidal(20, 0, 0, 20, 40) == pytest.approx(1.0)

def test_trapezoidal_con_hombro_izquierdo_a_mitad_de_la_rampa_derecha():
    assert trapezoidal(30, 0, 0, 20, 40) == pytest.approx(0.5)

def test_trapezoidal_con_hombro_izquierdo_justo_en_d_vale_cero():
    assert trapezoidal(40, 0, 0, 20, 40) == pytest.approx(0.0)

def test_trapezoidal_con_hombro_izquierdo_por_encima_del_soporte_vale_cero():
    assert trapezoidal(45, 0, 0, 20, 40) == pytest.approx(0.0)

def test_trapezoidal_con_hombro_derecho_por_debajo_del_soporte_vale_cero():
    assert trapezoidal(150, 200, 400, 1000, 1000) == pytest.approx(0.0)

def test_trapezoidal_con_hombro_derecho_justo_en_a_vale_cero():
    assert trapezoidal(200, 200, 400, 1000, 1000) == pytest.approx(0.0)

def test_trapezoidal_con_hombro_derecho_a_mitad_de_la_rampa_izquierda():
    assert trapezoidal(300, 200, 400, 1000, 1000) == pytest.approx(0.5)

def test_trapezoidal_con_hombro_derecho_en_el_borde_izquierdo_de_la_meseta_vale_uno():
    assert trapezoidal(400, 200, 400, 1000, 1000) == pytest.approx(1.0)

def test_trapezoidal_con_hombro_derecho_en_el_centro_de_la_meseta_vale_uno():
    assert trapezoidal(700, 200, 400, 1000, 1000) == pytest.approx(1.0)

def test_trapezoidal_con_hombro_derecho_en_el_hombro_vale_uno():
    assert trapezoidal(1000, 200, 400, 1000, 1000) == pytest.approx(1.0)

def test_trapezoidal_con_hombro_derecho_por_encima_del_universo_vale_cero():
    assert trapezoidal(1200, 200, 400, 1000, 1000) == pytest.approx(0.0)
