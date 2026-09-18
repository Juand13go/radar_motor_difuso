from app.excepciones import ConfiguracionMotorInvalida, EntradaMotorInvalida
from app.motor.pertenencia import triangular, trapezoidal

def operador_y(primero: float, segundo: float):
    return min(primero, segundo)

def grado_de_activacion(grados: list[float]):
    if not grados:
        raise ConfiguracionMotorInvalida("La regla no tiene condiciones")
    activacion = grados[0]
    for grado in grados[1:]:
        activacion = operador_y(activacion, grado)
    return activacion

def prioridad_sugeno(activaciones: list[tuple[float, float]]):
    numerador = 0.0
    denominador = 0.0
    for grado, salida in activaciones:
        numerador += grado * salida
        denominador += grado
    if not denominador:
        return None
    return numerador / denominador

def nivel_de_prioridad(prioridad: float, corte_media: float, corte_alta: float, corte_critica: float):
    if prioridad < corte_media:
        return "baja"
    if prioridad < corte_alta:
        return "media"
    if prioridad < corte_critica:
        return "alta"
    return "critica"

def recortar_al_universo(valor: float, minimo: float, maximo: float):
    if valor is None:
        return None
    return min(max(valor, minimo), maximo)

def grados_de_variable(valor: float, conjuntos: dict):
    grados = {}
    for nombre_conjunto, conjunto in conjuntos.items():
        if valor is None:
            grados[nombre_conjunto] = 0.0
        elif conjunto["tipo"] == "triangular":
            grados[nombre_conjunto] = triangular(valor, *conjunto["puntos"])
        else:
            grados[nombre_conjunto] = trapezoidal(valor, *conjunto["puntos"])
    return grados

def evaluar_prioridad(entradas: dict, configuracion: dict):
    variables = configuracion["variables"]
    for nombre_variable in variables:
        if nombre_variable not in entradas:
            raise EntradaMotorInvalida(f"Falta la variable {nombre_variable} en las entradas del motor")
    for nombre_variable in entradas:
        if nombre_variable not in variables:
            raise EntradaMotorInvalida(f"La variable {nombre_variable} no existe en la configuración del motor")

    recortadas = {}
    grados = {}
    for nombre_variable, variable in variables.items():
        recortadas[nombre_variable] = recortar_al_universo(entradas[nombre_variable], variable["minimo"], variable["maximo"])
        grados[nombre_variable] = grados_de_variable(recortadas[nombre_variable], variable["conjuntos"])

    reglas_activadas = []
    for regla in configuracion["reglas"]:
        grado = grado_de_activacion([grados[nombre_variable][nombre_conjunto] for nombre_variable, nombre_conjunto in regla["si"].items()])
        if grado > 0:
            reglas_activadas.append({"nombre": regla["nombre"], "grado": grado, "entonces": regla["entonces"]})

    prioridad = prioridad_sugeno([(regla["grado"], configuracion["salidas"][regla["entonces"]]) for regla in reglas_activadas])
    nivel = None
    if prioridad is not None:
        cortes = configuracion["cortes"]
        nivel = nivel_de_prioridad(prioridad, cortes["media"], cortes["alta"], cortes["critica"])

    # sorted es estable aun con reverse=True: en un empate queda el orden del YAML
    reglas_activadas = sorted(reglas_activadas, key=lambda regla: regla["grado"], reverse=True)

    return {"prioridad": prioridad, "nivel": nivel, "reglas_activadas": reglas_activadas, "entradas": recortadas}
