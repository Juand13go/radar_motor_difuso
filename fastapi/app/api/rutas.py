from fastapi import APIRouter, Depends
from database import get_session
from app.servicio.conversacion import obtener_o_crear_conversacion, obtener_historial_conversacion, guardado_mensajes, actualizacion_estado, creacion_lead, funcion_listado_asesores
from app.servicio.conversacion import actualizacion_asesor, obtener_nombre_asesor, listar_leads_por_asesor, cambiar_estado_lead_para_cierre
from app.servicio.agente import comunicacion_agente
import uuid
from app.api.schemas import ConversacionCrear, GuardarMensajeEntrada, EstadoEntrada, LeadEntrada, ProcesarEntrada, LeadSalida, LeadsPorAsesor, CerrarLeadSalida
from app.api.schemas import (ConversacionRespuesta, MensajeRespuesta, EstadoSalida, ProcesarSalida, ConfirmacionRespuesta, AsesorSalida, ObtenerAsesorSalida, 
                            CerrarLeadEntrada, AsesorEntrada)

router = APIRouter()

@router.post('/conversacion', response_model=ConversacionRespuesta)
def busqueda_creacion_conversacion(datos: ConversacionCrear, session = Depends(get_session)):
    return obtener_o_crear_conversacion(canal_user_id=datos.canal_user_id, canal=datos.canal, nombre=datos.nombre, session=session)

@router.get('/historial', response_model=list[MensajeRespuesta])
def cargar_historial(id_conversacion: uuid.UUID, session = Depends(get_session)):
    return obtener_historial_conversacion(id_conversacion, session)

@router.post('/guardar_mensaje', response_model=ConfirmacionRespuesta)
def guardar_mensaje(datos: GuardarMensajeEntrada, session = Depends(get_session)):
    guardado_mensajes(id_conversacion=datos.id_conversacion, rol=datos.rol, contenido=datos.contenido, session=session)
    return {"ok": True} 

@router.put('/estado', response_model=EstadoSalida)
def actualizar_estado(datos: EstadoEntrada, session = Depends(get_session)):
    return actualizacion_estado(estado=datos.estado, id_conversacion=datos.id_conversacion, session=session)

@router.post('/crear_lead', response_model=LeadSalida)
def creacion_de_leads(datos: LeadEntrada, session = Depends(get_session)):
    return creacion_lead(id_conversacion=datos.id_conversacion, productos_interes=datos.productos_interes, ciudad=datos.ciudad, session=session)
    
@router.post('/procesar', response_model=ProcesarSalida)
def procesar(datos: ProcesarEntrada,  session = Depends(get_session)):
    return comunicacion_agente(id_conversacion=datos.id_conversacion, session=session)

@router.put('/asignar_asesor', response_model=AsesorSalida)
def asignar_asesor(datos: AsesorEntrada, session = Depends(get_session)):
    return actualizacion_asesor(id_lead=datos.id_lead, session=session)

@router.get('/obtener_asesor', response_model=ObtenerAsesorSalida)
def obtener_asesor(id_asesor: uuid.UUID, session = Depends(get_session)):
    return obtener_nombre_asesor(id_asesor=id_asesor, session=session) 

@router.get('/leads_por_asesor', response_model=list[LeadsPorAsesor])
def leads_por_asesor(id_asesor: uuid.UUID, session = Depends(get_session)):
    return listar_leads_por_asesor(id_asesor=id_asesor, session=session)

@router.put('/cerrar_lead', response_model=CerrarLeadSalida)
def cerrar_lead(datos: CerrarLeadEntrada, session=Depends(get_session)):
    return cambiar_estado_lead_para_cierre(id_lead = datos.id_lead, estado_lead = datos.estado_lead, session=session)

@router.get('/listar_asesores')
def listar_asesores_para_front(session=Depends(get_session)):
    return funcion_listado_asesores(session=session)
