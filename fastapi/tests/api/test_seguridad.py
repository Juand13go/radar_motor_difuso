from app.api.seguridad import firmar_sesion, sesion_valida

def test_sesion_firmada_con_la_misma_clave_es_valida():
    assert sesion_valida(firmar_sesion(expira=2000, clave="k1"), clave="k1", ahora=1000) is True

def test_sesion_validada_con_otra_clave_no_es_valida():
    assert sesion_valida(firmar_sesion(expira=2000, clave="k1"), clave="k2", ahora=1000) is False

def test_sesion_en_el_instante_de_expirar_no_es_valida():
    assert sesion_valida(firmar_sesion(expira=2000, clave="k1"), clave="k1", ahora=2000) is False

def test_sesion_con_expira_alterado_no_es_valida():
    firma = firmar_sesion(expira=2000, clave="k1").split(".")[1]
    assert sesion_valida(f"3000.{firma}", clave="k1", ahora=1000) is False

def test_valor_sin_punto_no_es_valido():
    assert sesion_valida("abc", clave="k1", ahora=1000) is False

def test_valor_vacio_no_es_valido():
    assert sesion_valida("", clave="k1", ahora=1000) is False

def test_valor_nulo_no_es_valido():
    assert sesion_valida(None, clave="k1", ahora=1000) is False
