from fastapi import APIRouter, Depends
from database import get_session
from app.servicio.conversacion import obtener_historial_conversacion, listar_conversaciones_simulador, obtener_mensajes_simulador, obtener_mensajes_web
from app.servicio.leads import funcion_listado_asesores
from app.servicio.leads import listar_leads_por_asesor, cambiar_estado_lead_para_cierre, listar_leads_sin_asignar, listar_evaluaciones_lead
from app.servicio.mensajes import procesar_mensaje_entrante, procesar_mensaje_web
from app.servicio.analitica import reporte_demanda
import uuid
from app.api.schemas import MensajeRespuesta, LeadsPorAsesor, CerrarLeadSalida, CerrarLeadEntrada
from app.api.schemas import MensajeEntranteEntrada, MensajeEntranteSalida, EvaluacionLeadSalida, DemandaSalida, ConversacionResumenSalida
from app.api.schemas import ChatEntrada, ChatSalida, ChatHistorialEntrada

router = APIRouter()

@router.get('/historial', response_model=list[MensajeRespuesta])
def cargar_historial(id_conversacion: uuid.UUID, session = Depends(get_session)):
    return obtener_historial_conversacion(id_conversacion, session)

@router.get('/conversaciones_simulador', response_model=list[ConversacionResumenSalida])
def conversaciones_simulador(session=Depends(get_session)):
    return listar_conversaciones_simulador(session=session)

@router.get('/mensajes_simulador', response_model=list[MensajeRespuesta])
def mensajes_simulador(id_conversacion: uuid.UUID, session=Depends(get_session)):
    return obtener_mensajes_simulador(id_conversacion=id_conversacion, session=session)

@router.get('/leads_por_asesor', response_model=list[LeadsPorAsesor])
def leads_por_asesor(id_asesor: uuid.UUID, session = Depends(get_session)):
    return listar_leads_por_asesor(id_asesor=id_asesor, session=session)

@router.get('/leads_sin_asignar', response_model=list[LeadsPorAsesor])
def leads_sin_asignar(session=Depends(get_session)):
    return listar_leads_sin_asignar(session=session)

@router.get('/evaluaciones_lead', response_model=list[EvaluacionLeadSalida])
def evaluaciones_lead(id_lead: uuid.UUID, session=Depends(get_session)):
    return listar_evaluaciones_lead(id_lead=id_lead, session=session)

@router.put('/cerrar_lead', response_model=CerrarLeadSalida)
def cerrar_lead(datos: CerrarLeadEntrada, session=Depends(get_session)):
    return cambiar_estado_lead_para_cierre(id_lead = datos.id_lead, estado_lead = datos.estado_lead, session=session)

@router.get('/listar_asesores')
def listar_asesores_para_front(session=Depends(get_session)):
    return funcion_listado_asesores(session=session)

@router.post('/mensaje_entrante', response_model=MensajeEntranteSalida)
def mensaje_entrante(datos: MensajeEntranteEntrada, session=Depends(get_session)):
    return procesar_mensaje_entrante(canal=datos.canal, canal_user_id=datos.canal_user_id, nombre=datos.nombre, texto=datos.texto, session=session)

@router.post('/chat', response_model=ChatSalida)
def chat(datos: ChatEntrada, session=Depends(get_session)):
    return procesar_mensaje_web(canal_user_id=datos.canal_user_id, nombre=datos.nombre, texto=datos.texto, session=session)

@router.post('/chat/historial', response_model=list[MensajeRespuesta])
def chat_historial(datos: ChatHistorialEntrada, session=Depends(get_session)):
    return obtener_mensajes_web(canal_user_id=datos.canal_user_id, session=session)

@router.get('/demanda', response_model=DemandaSalida)
def demanda(dias: int = 30, session=Depends(get_session)):
    return reporte_demanda(dias=dias, session=session)
