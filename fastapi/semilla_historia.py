from sqlmodel import select, Session
from models import conversaciones, mensajes, leads, productos, asesores, items_solicitados, evaluaciones_motor, hoy_bogota, ahora_utc
from app.servicio.leads import calcular_monto_estimado, calcular_completitud, armar_entradas_del_motor, obtener_configuracion
from app.motor.inferencia import evaluar_prioridad
from database import engine
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import random
import sys

CANAL_SEMILLA = "semilla"

CLIENTES = [
    "Ferretería Los Guayacanes de Itagüí S.A.S.",
    "Construcciones Altamira del Valle S.A.S.",
    "Ferremateriales La Aguacatala",
    "Estructuras Metálicas Quebrada Seca S.A.S.",
    "Montajes Industriales Ayurá Ltda.",
    "Ferretería San Cayetano de Bello",
    "Obras Civiles Piedra Verde S.A.S.",
    "Suministros El Ancón de Sabaneta",
    "Ferrecentro La Tablaza",
    "Constructora Loma del Chocho S.A.S.",
    "Metalmecánica Guayabal Norte",
    "Soldaduras y Montajes Primavera de Caldas",
]

# El primer cliente es el de confianza: todas sus solicitudes cierran en venta
SOLICITUDES_POR_CLIENTE = [8, 7, 6, 6, 5, 5, 5, 5, 4, 4, 3, 2]

CIUDADES = ["Medellín", "Itagüí", "Envigado", "Bello", "Sabaneta", "La Estrella", "Copacabana", "Caldas"]

# Demanda no cubierta concentrada: referencia, cantidades posibles y existencias que habia al pedir
FALTANTES = {
    "ABR-005": {"solicitudes": 9, "cantidades": (5, 30), "existencias": 0},
    "EPP-006": {"solicitudes": 7, "cantidades": (2, 12), "existencias": 0},
    "SOL-002": {"solicitudes": 8, "cantidades": (20, 80), "existencias": 12},
}

FUERA_DE_CATALOGO = [
    ("Pintura epóxica", 4, 20),
    ("pintura epóxica", 2, 10),
    ("Pintura epóxica ", 5, 15),
    ("Andamio multidireccional", 1, 4),
    ("andamio multidireccional", 2, 6),
    ("Cemento gris", 20, 80),
    ("cemento gris", 10, 50),
    ("Cemento  gris", 30, 60),
    ("Malla electrosoldada", 5, 25),
    ("malla electrosoldada", 10, 30),
]

# Mercancia parada: no aparece en ninguna solicitud
REFERENCIAS_EXCLUIDAS = {"HEL-005", "ELE-001", "EPP-003", "HEL-001", "TOR-003", "HMA-004", "HMA-005"}

# Una distribuidora recibe muchas consultas chicas y pocos pedidos grandes
SOLICITUDES_CHICAS = 32
PRECIO_MAXIMO_CHICA = 60000

# Pedidos grandes y con afan del cliente de confianza: monto alto con confianza o urgencia es lo que llega a critico
SOLICITUDES_CRITICAS = 3
PEDIDO_CRITICO = [("SOL-003", 6), ("HEL-002", 3), ("HEL-004", 1)]

SEGUNDOS_MENSAJES = [
    "¿Me confirma disponibilidad y precio, por favor?",
    "Si se puede, lo necesitamos lo antes posible.",
    "Quedo atento a la cotización.",
    "¿Hacen despacho a obra?",
]

def fecha_bogota(dia, hora: int, minuto: int):
    return datetime.combine(dia, time(hora, minuto), tzinfo=ZoneInfo("America/Bogota")).astimezone(timezone.utc)

def cantidad_cubierta(producto: productos, chica: bool, generador: random.Random):
    if chica:
        maxima = 5
    elif producto.precio_unitario >= 500000:
        maxima = 3
    elif producto.precio_unitario >= 100000:
        maxima = 6
    else:
        maxima = 60
    # Fuera de las tres referencias faltantes, lo pedido siempre alcanza con las existencias
    return generador.randint(1, min(maxima, producto.existencias))

# Primero los productos que nadie ha pedido, para que el sobrestock muestre solo los excluidos a proposito
def elegir_productos(candidatos: list, cantidad: int, sin_pedir: set, generador: random.Random):
    nuevos = [producto for producto in candidatos if producto.referencia in sin_pedir]
    elegidos = generador.sample(nuevos, min(cantidad, len(nuevos)))
    restantes = [producto for producto in candidatos if producto not in elegidos]
    elegidos += generador.sample(restantes, cantidad - len(elegidos))
    for producto in elegidos:
        sin_pedir.discard(producto.referencia)
    return elegidos

def texto_primer_mensaje(items: list, ciudad: str):
    partes = []
    for item in items:
        if item["cantidad"] is None:
            partes.append(item["descripcion"])
        else:
            partes.append(f"{item['cantidad']} de {item['descripcion']}")
    texto = "Buenos días, necesito " + ", ".join(partes)
    if ciudad:
        texto += f" para {ciudad}"
    return texto + "."

def plan_de_solicitudes(generador: random.Random):
    clientes = []
    for indice, cantidad in enumerate(SOLICITUDES_POR_CLIENTE):
        clientes.extend([indice] * cantidad)
    estados = ["venta"] * 32 + ["no_venta"] * 20
    generador.shuffle(estados)
    plan = []
    for indice_cliente in clientes:
        estado = "venta" if indice_cliente == 0 else estados.pop()
        plan.append({"cliente": indice_cliente, "estado": estado, "dias_atras": generador.randint(1, 27), "chica": False, "critica": False, "faltantes": [], "fuera_de_catalogo": None})
    # Las ultimas del cliente de confianza, cuando ya acumula cinco ventas; el orden es el mismo con que se cargan
    del_cliente_de_confianza = sorted([solicitud for solicitud in plan if solicitud["cliente"] == 0], key=lambda solicitud: solicitud["dias_atras"], reverse=True)
    for solicitud in del_cliente_de_confianza[-SOLICITUDES_CRITICAS:]:
        solicitud["critica"] = True
    normales = [solicitud for solicitud in plan if not solicitud["critica"]]
    for solicitud in generador.sample(normales, SOLICITUDES_CHICAS):
        solicitud["chica"] = True
    # Los faltantes tienen precios altos y solo caben en los pedidos grandes
    grandes = [solicitud for solicitud in normales if not solicitud["chica"]]
    for referencia, datos in FALTANTES.items():
        for solicitud in generador.sample(grandes, datos["solicitudes"]):
            solicitud["faltantes"].append(referencia)
    for solicitud, fuera in zip(generador.sample(normales, len(FUERA_DE_CATALOGO)), FUERA_DE_CATALOGO):
        solicitud["fuera_de_catalogo"] = fuera
    return plan

def poblar_historia():
    generador = random.Random(2026)
    configuracion = obtener_configuracion()
    with Session(engine) as session:
        existente = session.exec(select(conversaciones).where(conversaciones.canal == CANAL_SEMILLA)).first()
        if existente:
            print("La semilla de historia ya está cargada, no se agrega nada.")
            return

        catalogo = session.exec(select(productos).order_by(productos.id_producto)).all()
        por_referencia = {producto.referencia: producto for producto in catalogo}
        disponibles = [producto for producto in catalogo if producto.existencias > 0 and producto.referencia not in REFERENCIAS_EXCLUIDAS and producto.referencia not in FALTANTES]
        sin_pedir = {producto.referencia for producto in disponibles}
        disponibles_chicas = [producto for producto in disponibles if producto.precio_unitario <= PRECIO_MAXIMO_CHICA]
        lista_asesores = session.exec(select(asesores).order_by(asesores.nombre_asesor)).all()
        hoy = hoy_bogota()

        conversaciones_semilla = []
        for indice, nombre in enumerate(CLIENTES):
            conversacion = conversaciones(canal=CANAL_SEMILLA, canal_user_id=f"semilla-{indice + 1:02d}", nombre=nombre)
            session.add(conversacion)
            conversaciones_semilla.append(conversacion)
        session.flush()

        plan = sorted(plan_de_solicitudes(generador), key=lambda solicitud: solicitud["dias_atras"], reverse=True)
        ventas_por_cliente = [0] * len(CLIENTES)
        ultimo_mensaje_por_cliente = {}
        escaladas = 0

        for numero, solicitud in enumerate(plan):
            conversacion = conversaciones_semilla[solicitud["cliente"]]
            dia = hoy - timedelta(days=solicitud["dias_atras"])
            creado_en = fecha_bogota(dia, generador.randint(7, 17), generador.randint(0, 59))

            items = []
            for referencia in solicitud["faltantes"]:
                producto = por_referencia[referencia]
                datos = FALTANTES[referencia]
                items.append({"id_producto": producto.id_producto, "descripcion": producto.nombre_producto, "cantidad": generador.randint(*datos["cantidades"]), "precio_al_momento": producto.precio_unitario, "existencias_al_momento": datos["existencias"]})
            if solicitud["critica"]:
                for referencia, cantidad in PEDIDO_CRITICO:
                    producto = por_referencia[referencia]
                    items.append({"id_producto": producto.id_producto, "descripcion": producto.nombre_producto, "cantidad": cantidad, "precio_al_momento": producto.precio_unitario, "existencias_al_momento": producto.existencias})
            objetivo = 0 if solicitud["critica"] else generador.randint(1, 2) if solicitud["chica"] else generador.randint(1, 4)
            if solicitud["fuera_de_catalogo"]:
                objetivo = max(objetivo - 1, 0)
            candidatos = disponibles_chicas if solicitud["chica"] else disponibles
            for producto in elegir_productos(candidatos=candidatos, cantidad=max(objetivo - len(items), 0), sin_pedir=sin_pedir, generador=generador):
                items.append({"id_producto": producto.id_producto, "descripcion": producto.nombre_producto, "cantidad": cantidad_cubierta(producto=producto, chica=solicitud["chica"], generador=generador), "precio_al_momento": producto.precio_unitario, "existencias_al_momento": producto.existencias})
            if solicitud["fuera_de_catalogo"]:
                descripcion, minima, maxima = solicitud["fuera_de_catalogo"]
                items.append({"id_producto": None, "descripcion": descripcion, "cantidad": generador.randint(minima, maxima), "precio_al_momento": None, "existencias_al_momento": None})

            # La mayoria trae ciudad y fecha; las demas quedan incompletas como en una conversacion real
            ciudad = generador.choice(CIUDADES) if generador.random() < 0.85 else None
            fecha_requerida = dia + timedelta(days=generador.randint(1, 20)) if generador.random() < 0.85 else None
            if solicitud["critica"]:
                ciudad = generador.choice(CIUDADES)
                fecha_requerida = dia + timedelta(days=generador.randint(1, 3))

            mensaje = mensajes(id_conversacion=conversacion.id_conversacion, rol="user", contenido=texto_primer_mensaje(items=items, ciudad=ciudad), creado_en=creado_en)
            session.add(mensaje)
            if generador.random() < 0.5:
                mensaje = mensajes(id_conversacion=conversacion.id_conversacion, rol="user", contenido=generador.choice(SEGUNDOS_MENSAJES), creado_en=creado_en + timedelta(minutes=2))
                session.add(mensaje)
            ultimo_mensaje_por_cliente[solicitud["cliente"]] = mensaje.creado_en

            monto_estimado = calcular_monto_estimado(items=items)
            relacion_cliente = ventas_por_cliente[solicitud["cliente"]]
            completitud = calcular_completitud(items=items, ciudad=ciudad)
            plazo_dias = (fecha_requerida - dia).days if fecha_requerida else None
            entradas = armar_entradas_del_motor(monto_estimado=monto_estimado, relacion_cliente=relacion_cliente, completitud=completitud, plazo_dias=plazo_dias)
            evaluacion = evaluar_prioridad(entradas=entradas, configuracion=configuracion)

            motivo = None
            if evaluacion["prioridad"] is not None and evaluacion["prioridad"] >= configuracion["umbral_escalacion"]:
                motivo = "motor"
            elif generador.random() < 0.15:
                motivo = "solicitud_cliente"

            # El cierre cae entre uno y cuatro dias despues, sin pasarse del momento actual
            cerrado_en = min(creado_en + timedelta(days=generador.randint(1, 4), hours=generador.randint(0, 6)), ahora_utc() - timedelta(hours=1))
            lead = leads(id_conversacion=conversacion.id_conversacion, estado_lead=solicitud["estado"], ciudad=ciudad, lead_creado_en=creado_en, monto_estimado=monto_estimado, fecha_requerida=fecha_requerida, prioridad=evaluacion["prioridad"], nivel_prioridad=evaluacion["nivel"], cerrado_en=cerrado_en)
            if motivo:
                lead.escalado = True
                lead.motivo_escalacion = motivo
                lead.escalado_en = creado_en + timedelta(minutes=3)
                lead.asesor_encargado = lista_asesores[escaladas % len(lista_asesores)].id_asesor
                escaladas += 1
            session.add(lead)
            session.flush()

            for item in items:
                session.add(items_solicitados(id_lead=lead.id_lead, **item))
            session.add(evaluaciones_motor(id_lead=lead.id_lead, id_mensaje=mensaje.id_mensaje, monto_estimado=monto_estimado, relacion_cliente=relacion_cliente, completitud=completitud, plazo_dias=plazo_dias, prioridad=evaluacion["prioridad"], nivel_prioridad=evaluacion["nivel"], reglas_activadas=evaluacion["reglas_activadas"], creado_en=creado_en + timedelta(minutes=1)))
            session.flush()

            if solicitud["estado"] == "venta":
                ventas_por_cliente[solicitud["cliente"]] += 1
            print(f"Solicitud {numero + 1} de {conversacion.nombre}: {solicitud['estado']}, prioridad {evaluacion['nivel']}, escalada {motivo or 'no'}")

        for indice, conversacion in enumerate(conversaciones_semilla):
            conversacion.conv_actualizado_en = ultimo_mensaje_por_cliente[indice]
            session.add(conversacion)
        # Un solo commit: si algo falla, la semilla no queda a medias
        session.commit()
        print(f"Semilla cargada: {len(plan)} solicitudes de {len(CLIENTES)} clientes, {escaladas} escaladas.")

def borrar_historia():
    with Session(engine) as session:
        ids_conversaciones = session.exec(select(conversaciones.id_conversacion).where(conversaciones.canal == CANAL_SEMILLA)).all()
        if not ids_conversaciones:
            print("No hay datos de la semilla de historia para borrar.")
            return
        ids_leads = session.exec(select(leads.id_lead).where(leads.id_conversacion.in_(ids_conversaciones))).all()
        # El orden respeta las llaves foraneas: primero lo que apunta a leads y mensajes
        for modelo, filtro in [(evaluaciones_motor, evaluaciones_motor.id_lead.in_(ids_leads)), (items_solicitados, items_solicitados.id_lead.in_(ids_leads)), (mensajes, mensajes.id_conversacion.in_(ids_conversaciones)), (leads, leads.id_lead.in_(ids_leads)), (conversaciones, conversaciones.id_conversacion.in_(ids_conversaciones))]:
            for fila in session.exec(select(modelo).where(filtro)).all():
                session.delete(fila)
            session.flush()
        session.commit()
        print(f"Semilla borrada: {len(ids_leads)} solicitudes de {len(ids_conversaciones)} clientes.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "borrar":
        borrar_historia()
    else:
        poblar_historia()
