from sqlmodel import Session
from app.persistencia.repositorio import consultar_demanda_no_cubierta, consultar_demanda_fuera_de_catalogo, consultar_sobrestock, consultar_resumen_periodo
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from models import hoy_bogota

DIAS_POR_DEFECTO = 30

# El rango llega en dias de Bogota y el fin se incluye completo
def limites_del_rango(inicio: date, fin: date):
    zona = ZoneInfo("America/Bogota")
    return datetime.combine(inicio, time.min, tzinfo=zona), datetime.combine(fin + timedelta(days=1), time.min, tzinfo=zona)

def demanda_no_cubierta(inicio: date, fin: date, session: Session):
    desde, hasta = limites_del_rango(inicio=inicio, fin=fin)
    return [dict(fila._mapping) for fila in consultar_demanda_no_cubierta(desde=desde, hasta=hasta, session=session)]

def demanda_fuera_de_catalogo(inicio: date, fin: date, session: Session):
    desde, hasta = limites_del_rango(inicio=inicio, fin=fin)
    return [dict(fila._mapping) for fila in consultar_demanda_fuera_de_catalogo(desde=desde, hasta=hasta, session=session)]

def sobrestock(inicio: date, fin: date, session: Session):
    desde, hasta = limites_del_rango(inicio=inicio, fin=fin)
    return [dict(fila._mapping) for fila in consultar_sobrestock(desde=desde, hasta=hasta, session=session)]

def resumen_periodo(inicio: date, fin: date, session: Session):
    desde, hasta = limites_del_rango(inicio=inicio, fin=fin)
    return dict(consultar_resumen_periodo(desde=desde, hasta=hasta, session=session)._mapping)

def reporte_demanda(dias: int, session: Session):
    if dias <= 0:
        dias = DIAS_POR_DEFECTO
    # El periodo incluye hoy: treinta dias son hoy y los veintinueve anteriores
    fin = hoy_bogota()
    inicio = fin - timedelta(days=dias - 1)
    return {
        "inicio": inicio,
        "fin": fin,
        "resumen": resumen_periodo(inicio=inicio, fin=fin, session=session),
        "no_cubierta": demanda_no_cubierta(inicio=inicio, fin=fin, session=session),
        "fuera_de_catalogo": demanda_fuera_de_catalogo(inicio=inicio, fin=fin, session=session),
        "sobrestock": sobrestock(inicio=inicio, fin=fin, session=session)
    }
