from fastapi import Depends, HTTPException, Cookie, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.excepciones import SesionRequerida
from typing import Optional
import secrets
import hmac
import hashlib
import time
import os
import logging

logger = logging.getLogger(__name__)

autenticacion_basica = HTTPBasic(auto_error=False)

DURACION_SESION = 12 * 60 * 60

def firmar_sesion(expira: int, clave: str):
    firma = hmac.new(clave.encode("utf-8"), str(expira).encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{expira}.{firma}"

def sesion_valida(valor: str, clave: str, ahora: int):
    if not valor or "." not in valor:
        return False
    expira, firma = valor.split(".", 1)
    firma_esperada = hmac.new(clave.encode("utf-8"), expira.encode("utf-8"), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(firma.encode("utf-8"), firma_esperada.encode("utf-8")):
        return False
    # Solo se convierte a int despues de verificar la firma, porque entonces el texto lo genero firmar_sesion
    return ahora < int(expira)

def credenciales_validas(usuario: str, clave: str):
    usuario_admin = os.getenv("ADMIN_USUARIO") or ""
    clave_admin = os.getenv("ADMIN_CLAVE") or ""
    if not usuario_admin or not clave_admin:
        logger.error("Falta ADMIN_USUARIO o ADMIN_CLAVE y se negó el acceso al backoffice")
        return False
    # Las dos comparaciones se calculan siempre, para que el tiempo no revele si fallo el usuario o la clave
    usuario_correcto = secrets.compare_digest(usuario.encode("utf-8"), usuario_admin.encode("utf-8"))
    clave_correcta = secrets.compare_digest(clave.encode("utf-8"), clave_admin.encode("utf-8"))
    return usuario_correcto and clave_correcta

def sesion_actual_valida(radar_sesion: Optional[str]):
    clave_admin = os.getenv("ADMIN_CLAVE") or ""
    if not clave_admin:
        logger.error("Falta ADMIN_CLAVE y se negó la sesión del backoffice")
        return False
    return sesion_valida(valor=radar_sesion, clave=clave_admin, ahora=int(time.time()))

def verificar_admin(radar_sesion: Optional[str] = Cookie(default=None), credenciales: Optional[HTTPBasicCredentials] = Depends(autenticacion_basica)):
    if radar_sesion and sesion_actual_valida(radar_sesion=radar_sesion):
        return
    if credenciales and credenciales_validas(usuario=credenciales.username, clave=credenciales.password):
        return
    raise HTTPException(status_code=401, detail="Credenciales inválidas")

def verificar_pagina_admin(radar_sesion: Optional[str] = Cookie(default=None)):
    if not sesion_actual_valida(radar_sesion=radar_sesion):
        raise SesionRequerida

def abrir_sesion(usuario: str, clave: str, response: Response):
    if not credenciales_validas(usuario=usuario, clave=clave):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    valor = firmar_sesion(expira=int(time.time()) + DURACION_SESION, clave=os.getenv("ADMIN_CLAVE"))
    response.set_cookie("radar_sesion", valor, max_age=DURACION_SESION, path="/", httponly=True, samesite="strict", secure=True)
    return {"ok": True}

def cerrar_sesion(response: Response):
    response.delete_cookie("radar_sesion", path="/", httponly=True, samesite="strict", secure=True)
    return {"ok": True}
