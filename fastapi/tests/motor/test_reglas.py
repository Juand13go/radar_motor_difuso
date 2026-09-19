import pytest
from pathlib import Path
from app.motor.reglas import validar_configuracion, cargar_configuracion
from app.excepciones import ConfiguracionMotorInvalida

def configuracion_valida():
    return {
        "variables": {
            "monto_estimado": {
                "minimo": 0,
                "maximo": 100,
                "conjuntos": {
                    "bajo": {"tipo": "trapezoidal", "puntos": [0, 0, 20, 50]},
                    "alto": {"tipo": "trapezoidal", "puntos": [20, 50, 100, 100]}
                }
            },
            "plazo_dias": {
                "minimo": 0,
                "maximo": 30,
                "conjuntos": {
                    "corto": {"tipo": "triangular", "puntos": [0, 0, 10]},
                    "largo": {"tipo": "trapezoidal", "puntos": [5, 15, 30, 30]}
                }
            }
        },
        "salidas": {"baja": 0.2, "media": 0.4, "alta": 0.7, "critica": 0.9},
        "cortes": {"media": 0.25, "alta": 0.5, "critica": 0.75},
        "umbral_escalacion": 0.5,
        "reglas": [
            {"nombre": "pedido_grande_urgente", "si": {"monto_estimado": "alto", "plazo_dias": "corto"}, "entonces": "critica"},
            {"nombre": "pedido_pequeno_sin_afan", "si": {"monto_estimado": "bajo", "plazo_dias": "largo"}, "entonces": "baja"},
            {"nombre": "pedido_grande", "si": {"monto_estimado": "alto"}, "entonces": "alta"}
        ]
    }

def test_configuracion_valida_se_devuelve_tal_cual():
    assert validar_configuracion(configuracion_valida()) == configuracion_valida()

def test_falta_la_seccion_reglas():
    configuracion = configuracion_valida()
    del configuracion["reglas"]
    with pytest.raises(ConfiguracionMotorInvalida, match="reglas"):
        validar_configuracion(configuracion)

def test_variable_con_minimo_igual_a_maximo():
    configuracion = configuracion_valida()
    configuracion["variables"]["monto_estimado"]["minimo"] = 100
    with pytest.raises(ConfiguracionMotorInvalida, match="monto_estimado"):
        validar_configuracion(configuracion)

def test_conjunto_con_tipo_desconocido():
    configuracion = configuracion_valida()
    configuracion["variables"]["monto_estimado"]["conjuntos"]["bajo"]["tipo"] = "gaussiana"
    with pytest.raises(ConfiguracionMotorInvalida, match="bajo"):
        validar_configuracion(configuracion)

def test_conjunto_triangular_con_cuatro_puntos():
    configuracion = configuracion_valida()
    configuracion["variables"]["plazo_dias"]["conjuntos"]["corto"]["puntos"] = [0, 0, 10, 10]
    with pytest.raises(ConfiguracionMotorInvalida, match="corto"):
        validar_configuracion(configuracion)

def test_conjunto_trapezoidal_con_tres_puntos():
    configuracion = configuracion_valida()
    configuracion["variables"]["monto_estimado"]["conjuntos"]["bajo"]["puntos"] = [0, 0, 20]
    with pytest.raises(ConfiguracionMotorInvalida, match="bajo"):
        validar_configuracion(configuracion)

def test_conjunto_con_puntos_desordenados():
    configuracion = configuracion_valida()
    configuracion["variables"]["monto_estimado"]["conjuntos"]["bajo"]["puntos"] = [0, 30, 20, 50]
    with pytest.raises(ConfiguracionMotorInvalida, match="bajo"):
        validar_configuracion(configuracion)

def test_conjunto_con_puntos_fuera_del_universo():
    configuracion = configuracion_valida()
    configuracion["variables"]["monto_estimado"]["conjuntos"]["alto"]["puntos"] = [20, 50, 100, 120]
    with pytest.raises(ConfiguracionMotorInvalida, match="alto"):
        validar_configuracion(configuracion)

def test_cortes_que_no_van_en_orden_creciente():
    configuracion = configuracion_valida()
    configuracion["cortes"]["media"] = 0.5
    configuracion["cortes"]["alta"] = 0.25
    with pytest.raises(ConfiguracionMotorInvalida, match="cortes"):
        validar_configuracion(configuracion)

def test_regla_con_si_vacio():
    configuracion = configuracion_valida()
    configuracion["reglas"][0]["si"] = {}
    with pytest.raises(ConfiguracionMotorInvalida, match="pedido_grande_urgente"):
        validar_configuracion(configuracion)

def test_regla_que_nombra_una_variable_que_no_existe():
    configuracion = configuracion_valida()
    configuracion["reglas"][0]["si"]["urgencia"] = "alta"
    with pytest.raises(ConfiguracionMotorInvalida, match="urgencia"):
        validar_configuracion(configuracion)

def test_regla_que_nombra_un_conjunto_que_no_existe():
    configuracion = configuracion_valida()
    configuracion["reglas"][2]["si"]["monto_estimado"] = "medio"
    with pytest.raises(ConfiguracionMotorInvalida, match="medio"):
        validar_configuracion(configuracion)

def test_regla_con_entonces_que_no_esta_en_salidas():
    configuracion = configuracion_valida()
    configuracion["reglas"][0]["entonces"] = "urgentisima"
    with pytest.raises(ConfiguracionMotorInvalida, match="urgentisima"):
        validar_configuracion(configuracion)

def test_dos_reglas_con_el_mismo_nombre():
    configuracion = configuracion_valida()
    configuracion["reglas"][1]["nombre"] = "pedido_grande"
    with pytest.raises(ConfiguracionMotorInvalida, match="pedido_grande"):
        validar_configuracion(configuracion)

def test_cargar_configuracion_lee_el_yaml_de_prueba_con_tres_reglas():
    ruta = Path(__file__).parent / "reglas_prueba.yaml"
    assert len(cargar_configuracion(str(ruta))["reglas"]) == 3

def test_validar_configuracion_con_none_lanza_configuracion_motor_invalida():
    with pytest.raises(ConfiguracionMotorInvalida, match="vacía"):
        validar_configuracion(None)

def test_salida_fuera_de_la_escala():
    configuracion = configuracion_valida()
    configuracion["salidas"]["critica"] = 150
    with pytest.raises(ConfiguracionMotorInvalida, match="salidas"):
        validar_configuracion(configuracion)

def test_corte_fuera_de_la_escala():
    configuracion = configuracion_valida()
    configuracion["cortes"]["critica"] = 150
    with pytest.raises(ConfiguracionMotorInvalida, match="cortes"):
        validar_configuracion(configuracion)

def test_umbral_de_escalacion_fuera_de_la_escala():
    configuracion = configuracion_valida()
    configuracion["umbral_escalacion"] = 150
    with pytest.raises(ConfiguracionMotorInvalida, match="umbral_escalacion"):
        validar_configuracion(configuracion)
