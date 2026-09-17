def trapezoidal(valor: float, a: float, b: float, c: float, d: float):
    if valor < a or valor > d:
        return 0.0
    if b <= valor <= c:
        return 1.0
    # La meseta se resuelve antes que las rampas, asi que un hombro (a == b o c == d) nunca llega a dividir por cero
    if valor < b:
        return (valor - a) / (b - a)
    return (d - valor) / (d - c)

def triangular(valor: float, a: float, b: float, c: float):
    # Un triangulo es un trapecio con la meseta de ancho cero
    return trapezoidal(valor, a, b, b, c)
