from app.excepciones import ConfiguracionMotorInvalida

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
