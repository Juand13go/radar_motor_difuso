import yaml
from app.excepciones import ConfiguracionMotorInvalida

SECCIONES = ("variables", "salidas", "cortes", "umbral_escalacion", "reglas")
PUNTOS_POR_TIPO = {"triangular": 3, "trapezoidal": 4}

def validar_secciones(configuracion: dict):
    for seccion in SECCIONES:
        if seccion not in configuracion:
            raise ConfiguracionMotorInvalida(f"Falta la sección {seccion} en la configuración del motor")

def validar_conjunto(nombre_conjunto: str, conjunto: dict, nombre_variable: str, minimo: float, maximo: float):
    tipo = conjunto.get("tipo")
    if tipo not in PUNTOS_POR_TIPO:
        raise ConfiguracionMotorInvalida(f"El conjunto {nombre_conjunto} de la variable {nombre_variable} tiene un tipo desconocido: {tipo}")
    puntos = conjunto.get("puntos") or []
    if len(puntos) != PUNTOS_POR_TIPO[tipo]:
        raise ConfiguracionMotorInvalida(f"El conjunto {nombre_conjunto} de la variable {nombre_variable} es {tipo} y necesita {PUNTOS_POR_TIPO[tipo]} puntos, pero trae {len(puntos)}")
    if puntos != sorted(puntos):
        raise ConfiguracionMotorInvalida(f"Los puntos del conjunto {nombre_conjunto} de la variable {nombre_variable} no están en orden no decreciente")
    # Ya estan ordenados, asi que basta con mirar los extremos
    if puntos[0] < minimo or puntos[-1] > maximo:
        raise ConfiguracionMotorInvalida(f"Los puntos del conjunto {nombre_conjunto} se salen del universo de la variable {nombre_variable}")

def validar_variables(variables: dict):
    for nombre_variable, variable in variables.items():
        minimo = variable.get("minimo")
        maximo = variable.get("maximo")
        if minimo is None or maximo is None or minimo >= maximo:
            raise ConfiguracionMotorInvalida(f"La variable {nombre_variable} necesita un minimo menor que su maximo")
        for nombre_conjunto, conjunto in variable.get("conjuntos", {}).items():
            validar_conjunto(nombre_conjunto, conjunto, nombre_variable, minimo, maximo)

def esta_en_la_escala(valor: float):
    # bool es subclase de int: sin este filtro un true del YAML pasaria como 1
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and 0 <= valor <= 100

def validar_cortes(cortes: dict):
    media = cortes.get("media")
    alta = cortes.get("alta")
    critica = cortes.get("critica")
    if media is None or alta is None or critica is None or not media < alta < critica:
        raise ConfiguracionMotorInvalida("Los cortes deben cumplir media menor que alta y alta menor que critica")
    for nombre_corte, corte in cortes.items():
        if not esta_en_la_escala(corte):
            raise ConfiguracionMotorInvalida(f"El corte {nombre_corte} de la sección cortes debe ser un número entre 0 y 100")

def validar_salidas(salidas: dict):
    for nombre_salida, salida in salidas.items():
        if not esta_en_la_escala(salida):
            raise ConfiguracionMotorInvalida(f"La salida {nombre_salida} de la sección salidas debe ser un número entre 0 y 100")

def validar_umbral_escalacion(umbral_escalacion: float):
    if not esta_en_la_escala(umbral_escalacion):
        raise ConfiguracionMotorInvalida("La sección umbral_escalacion debe ser un número entre 0 y 100")

def validar_reglas(reglas: list, variables: dict, salidas: dict):
    for regla in reglas:
        nombre = regla.get("nombre")
        condiciones = regla.get("si") or {}
        if not condiciones:
            raise ConfiguracionMotorInvalida(f"La regla {nombre} no tiene condiciones en si")
        for nombre_variable, nombre_conjunto in condiciones.items():
            if nombre_variable not in variables:
                raise ConfiguracionMotorInvalida(f"La regla {nombre} nombra la variable {nombre_variable}, que no está en variables")
            if nombre_conjunto not in variables[nombre_variable]["conjuntos"]:
                raise ConfiguracionMotorInvalida(f"La regla {nombre} pide la variable {nombre_variable} en el conjunto {nombre_conjunto}, que no existe")
        if regla.get("entonces") not in salidas:
            raise ConfiguracionMotorInvalida(f"La regla {nombre} tiene un entonces que no está en salidas: {regla.get('entonces')}")
    nombres = [regla.get("nombre") for regla in reglas]
    for nombre in nombres:
        if nombres.count(nombre) > 1:
            raise ConfiguracionMotorInvalida(f"Hay dos reglas con el mismo nombre: {nombre}")

def validar_configuracion(configuracion: dict):
    if not isinstance(configuracion, dict):
        raise ConfiguracionMotorInvalida("La configuración del motor está vacía o no es un diccionario")
    validar_secciones(configuracion)
    validar_variables(configuracion["variables"])
    validar_cortes(configuracion["cortes"])
    validar_salidas(configuracion["salidas"])
    validar_umbral_escalacion(configuracion["umbral_escalacion"])
    validar_reglas(configuracion["reglas"], configuracion["variables"], configuracion["salidas"])
    return configuracion

def cargar_configuracion(ruta: str):
    with open(ruta, encoding="utf-8") as archivo:
        configuracion = yaml.safe_load(archivo)
    return validar_configuracion(configuracion)
