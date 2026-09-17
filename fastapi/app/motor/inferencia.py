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
