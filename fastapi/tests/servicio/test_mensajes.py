from app.servicio.mensajes import es_mensaje_sin_texto, armar_respuesta_cliente
from app.servicio.mensajes import elegir_texto_entrante, respuesta_sin_contenido, TEXTO_VOZ_NO_ENTENDIDA, TEXTO_SOLO_TEXTO
from app.servicio.agente import TEXTO_FALLO_TECNICO

def test_texto_nulo_es_mensaje_sin_texto():
    assert es_mensaje_sin_texto(texto=None) is True

def test_texto_solo_con_espacios_es_mensaje_sin_texto():
    assert es_mensaje_sin_texto(texto="   ") is True

def test_texto_con_contenido_no_es_mensaje_sin_texto():
    assert es_mensaje_sin_texto(texto="hola") is False

def test_respuesta_escalada_sin_fallo_lleva_la_confirmacion_arriba():
    assert armar_respuesta_cliente(respuesta="¿Para cuándo lo necesita?", escalado=True, fallo_tecnico=False, nombre_asesor="Natalia Ramírez Rendón") == "Su solicitud ya quedó en manos de Natalia Ramírez Rendón, que lo va a contactar en breve.\n¿Para cuándo lo necesita?"

def test_respuesta_con_fallo_tecnico_es_solo_el_texto_de_fallo():
    assert armar_respuesta_cliente(respuesta=TEXTO_FALLO_TECNICO, escalado=True, fallo_tecnico=True, nombre_asesor="Natalia Ramírez Rendón") == TEXTO_FALLO_TECNICO

def test_respuesta_sin_escalacion_queda_igual():
    assert armar_respuesta_cliente(respuesta="Hola, ¿qué necesita?", escalado=False, fallo_tecnico=False, nombre_asesor=None) == "Hola, ¿qué necesita?"

def test_texto_con_contenido_se_usa_sin_transcripcion():
    assert elegir_texto_entrante(texto="hola", transcripcion=None) == "hola"

def test_sin_texto_se_usa_la_transcripcion():
    assert elegir_texto_entrante(texto=None, transcripcion="necesito tornillos") == "necesito tornillos"

def test_texto_solo_con_espacios_se_reemplaza_por_la_transcripcion():
    assert elegir_texto_entrante(texto="   ", transcripcion="necesito tornillos") == "necesito tornillos"

def test_transcripcion_solo_con_espacios_no_da_texto():
    assert elegir_texto_entrante(texto=None, transcripcion="   ") is None

def test_sin_texto_ni_transcripcion_no_da_texto():
    assert elegir_texto_entrante(texto=None, transcripcion=None) is None

def test_sin_contenido_con_voz_pide_escribir_la_nota():
    assert respuesta_sin_contenido(hubo_voz=True) == TEXTO_VOZ_NO_ENTENDIDA

def test_sin_contenido_sin_voz_responde_solo_texto():
    assert respuesta_sin_contenido(hubo_voz=False) == TEXTO_SOLO_TEXTO
