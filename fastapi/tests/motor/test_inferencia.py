import pytest
from app.motor.inferencia import operador_y, grado_de_activacion, prioridad_sugeno, nivel_de_prioridad
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

def test_prioridad_sugeno_con_una_sola_regla_devuelve_su_salida():
    assert prioridad_sugeno([(0.8, 0.9)]) == pytest.approx(0.9)

def test_prioridad_sugeno_con_grados_iguales_promedia():
    assert prioridad_sugeno([(0.5, 0.2), (0.5, 0.8)]) == pytest.approx(0.5)

def test_prioridad_sugeno_se_acerca_a_la_regla_mas_fuerte():
    assert prioridad_sugeno([(0.6, 0.9), (0.2, 0.3)]) == pytest.approx(0.75)

def test_prioridad_sugeno_con_los_grados_intercambiados_cambia_de_lado():
    assert prioridad_sugeno([(0.2, 0.9), (0.6, 0.3)]) == pytest.approx(0.45)

def test_prioridad_sugeno_con_una_regla_apagada_no_la_cuenta():
    assert prioridad_sugeno([(0.4, 1.0), (0.0, 0.0)]) == pytest.approx(1.0)

def test_prioridad_sugeno_con_tres_reglas():
    assert prioridad_sugeno([(0.3, 0.2), (0.5, 0.6), (0.2, 1.0)]) == pytest.approx(0.56)

def test_prioridad_sugeno_con_dos_reglas_iguales():
    assert prioridad_sugeno([(0.1, 0.2), (0.1, 0.2)]) == pytest.approx(0.2)

def test_prioridad_sugeno_con_grados_que_no_suman_uno():
    assert prioridad_sugeno([(0.9, 0.8), (0.9, 0.4)]) == pytest.approx(0.6)

def test_prioridad_sugeno_sin_reglas_activas_devuelve_none():
    resultado = prioridad_sugeno([(0.0, 0.9), (0.0, 0.1)])
    assert resultado is None

def test_prioridad_sugeno_con_la_lista_vacia_devuelve_none():
    resultado = prioridad_sugeno([])
    assert resultado is None

def test_nivel_de_prioridad_en_el_piso_es_baja():
    assert nivel_de_prioridad(0.0, 0.25, 0.5, 0.75) == "baja"

def test_nivel_de_prioridad_justo_debajo_del_primer_corte_es_baja():
    assert nivel_de_prioridad(0.24, 0.25, 0.5, 0.75) == "baja"

def test_nivel_de_prioridad_en_el_primer_corte_sube_a_media():
    assert nivel_de_prioridad(0.25, 0.25, 0.5, 0.75) == "media"

def test_nivel_de_prioridad_justo_debajo_del_segundo_corte_es_media():
    assert nivel_de_prioridad(0.49, 0.25, 0.5, 0.75) == "media"

def test_nivel_de_prioridad_en_el_segundo_corte_sube_a_alta():
    assert nivel_de_prioridad(0.5, 0.25, 0.5, 0.75) == "alta"

def test_nivel_de_prioridad_justo_debajo_del_tercer_corte_es_alta():
    assert nivel_de_prioridad(0.74, 0.25, 0.5, 0.75) == "alta"

def test_nivel_de_prioridad_en_el_tercer_corte_sube_a_critica():
    assert nivel_de_prioridad(0.75, 0.25, 0.5, 0.75) == "critica"

def test_nivel_de_prioridad_en_el_techo_es_critica():
    assert nivel_de_prioridad(1.0, 0.25, 0.5, 0.75) == "critica"
