from sqlmodel import Session
from app.persistencia.repositorio import consultar_demanda_no_cubierta, consultar_demanda_fuera_de_catalogo, consultar_sobrestock, consultar_resumen_periodo
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

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
