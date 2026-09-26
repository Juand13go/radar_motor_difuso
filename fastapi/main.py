from fastapi import FastAPI, Request, Depends, Cookie
from app.api.rutas import router_publico, router_admin
from app.api.seguridad import verificar_admin, verificar_pagina_admin, sesion_actual_valida
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from app.excepciones import ConversacionNoEncontrada, LeadNoEncontrado, AsesorNoEncontrado, SinAsesoresDisponibles, SesionRequerida
from typing import Optional
import logging
from fastapi.responses import FileResponse


logging.basicConfig(level=logging.INFO)

# La documentacion automatica no acepta dependencias, asi que se apaga y se sirve abajo con clave
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(router_publico)
app.include_router(router_admin)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/panel", dependencies=[Depends(verificar_pagina_admin)])
def panel():
    return FileResponse("static/panel.html")

@app.get("/reporte", dependencies=[Depends(verificar_pagina_admin)])
def reporte():
    return FileResponse("static/reporte.html")

@app.get("/simulador", dependencies=[Depends(verificar_pagina_admin)])
def simulador():
    return FileResponse("static/simulador.html")

@app.get("/entrar")
def pagina_entrar(radar_sesion: Optional[str] = Cookie(default=None)):
    if sesion_actual_valida(radar_sesion=radar_sesion):
        return RedirectResponse("/panel", status_code=303)
    return FileResponse("static/entrar.html")

@app.get("/openapi.json", include_in_schema=False, dependencies=[Depends(verificar_admin)])
def openapi():
    return app.openapi()

@app.get("/docs", include_in_schema=False, dependencies=[Depends(verificar_admin)])
def docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Radar - Documentación")

@app.exception_handler(ConversacionNoEncontrada)
def manejar_conversacion_no_encontrada(request: Request, exc: ConversacionNoEncontrada):
    return JSONResponse(status_code=404, content={"detail":"Conversación No Encontrada"})

@app.exception_handler(LeadNoEncontrado)
def manejar_lead_no_encontrado(request: Request, exc: LeadNoEncontrado):
    return JSONResponse(status_code=404, content={"detail":"Lead No Encontrado"})

@app.exception_handler(AsesorNoEncontrado)
def manejar_asesor_no_encontrado(request: Request, exc: AsesorNoEncontrado):
    return JSONResponse(status_code=404, content={"detail":"Asesor No Encontrado"})

@app.exception_handler(SinAsesoresDisponibles)
def manejar_sin_asesores_disponibles(request: Request, exc: SinAsesoresDisponibles):
    return JSONResponse(status_code=503, content={"detail":"No hay asesores disponibles"})

@app.exception_handler(SesionRequerida)
def manejar_sesion_requerida(request: Request, exc: SesionRequerida):
    return RedirectResponse("/entrar", status_code=303)
