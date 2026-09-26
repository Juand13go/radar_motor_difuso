from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
import logging

logger = logging.getLogger(__name__)

autenticacion_basica = HTTPBasic()

def verificar_admin(credenciales: HTTPBasicCredentials = Depends(autenticacion_basica)):
    usuario = os.getenv("ADMIN_USUARIO") or ""
    clave = os.getenv("ADMIN_CLAVE") or ""
    # HTTPException y no una excepcion del dominio, porque HTTPBasic ya responde asi y el navegador necesita el encabezado
    no_autorizado = HTTPException(status_code=401, detail="Credenciales inválidas", headers={"WWW-Authenticate": "Basic"})
    if not usuario or not clave:
        logger.error("Falta ADMIN_USUARIO o ADMIN_CLAVE y se negó el acceso al backoffice")
        raise no_autorizado
    # Las dos comparaciones se calculan siempre, para que el tiempo no revele si fallo el usuario o la clave
    usuario_correcto = secrets.compare_digest(credenciales.username.encode("utf-8"), usuario.encode("utf-8"))
    clave_correcta = secrets.compare_digest(credenciales.password.encode("utf-8"), clave.encode("utf-8"))
    if not (usuario_correcto and clave_correcta):
        raise no_autorizado
