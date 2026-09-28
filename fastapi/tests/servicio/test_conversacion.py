from app.servicio.conversacion import telefono_desde_whatsapp

def test_telefono_desde_whatsapp_quita_el_indicativo():
    assert telefono_desde_whatsapp(canal_user_id="573116347499") == "3116347499"

def test_telefono_desde_whatsapp_extranjero_es_nulo():
    assert telefono_desde_whatsapp(canal_user_id="13055551234") is None

def test_telefono_desde_whatsapp_fijo_colombiano_es_nulo():
    assert telefono_desde_whatsapp(canal_user_id="576041234567") is None

def test_telefono_desde_whatsapp_incompleto_es_nulo():
    assert telefono_desde_whatsapp(canal_user_id="5731163474") is None

def test_telefono_desde_whatsapp_con_letras_es_nulo():
    assert telefono_desde_whatsapp(canal_user_id="57311634749a") is None
