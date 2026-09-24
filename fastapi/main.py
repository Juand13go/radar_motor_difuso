from fastapi import FastAPI, Request
from app.api.rutas import router
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.excepciones import ConversacionNoEncontrada, LeadNoEncontrado, AsesorNoEncontrado, SinAsesoresDisponibles
import logging
from fastapi.responses import FileResponse


logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/panel")
def panel():
    return FileResponse("static/panel.html")

@app.get("/reporte")
def reporte():
    return FileResponse("static/reporte.html")

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
