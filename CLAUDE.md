# Instrucciones para trabajar en este repositorio

Este repositorio es Radar, el sistema de triaje de leads comerciales de Halua Studio. El código lo escribe Claude Code, pero las decisiones de arquitectura, los nombres de dominio y las reglas de negocio las toma Juan Diego. Cada cambio tiene que poder leerse como si lo hubiera escrito él: mismo orden, mismos nombres, mismo nivel de detalle. Si algo de este archivo choca con una instrucción puntual, gana la instrucción puntual; si choca con lo que ya está escrito en el código, pregunta antes de decidir.

El orden del trabajo está en PLAN.md. Léelo al empezar cada sesión. Cada instrucción nombra una pieza de ese plan (por ejemplo 2.3) y solo se trabaja esa pieza.

## Cómo se trabaja cada pieza

Cada pieza termina en un solo commit. Antes de modificar cualquier archivo propones un plan corto: qué archivos vas a tocar, qué funciones vas a crear o cambiar y en qué orden. No escribes nada hasta que el plan esté aprobado. Si el plan toca más de cuatro archivos, avisa, porque probablemente la pieza está mal cortada.

Cuando la pieza es lógica pura (el motor difuso o cualquier cálculo que no toque la base de datos), las pruebas van primero. Escribes las pruebas, se corren y fallan, se aprueban, y solo entonces escribes la función. Los valores esperados de las pruebas vienen en la instrucción; no los inventes ni los ajustes para que la prueba pase.

No hagas commits, no hagas push y no crees ramas. El commit lo hace Juan Diego después de revisar el diff.

No toques archivos que la instrucción no menciona. No renombres, no reordenes y no "mejores" código existente que esté fuera del alcance, aunque veas algo mejorable; si lo ves, lo mencionas al final y sigues. No agregues dependencias nuevas sin que estén aprobadas en la instrucción. No adelantes trabajo de piezas siguientes aunque sea poco.

Si algo es ambiguo (un nombre, un valor por defecto, qué hacer en un caso borde), te detienes y preguntas. Es preferible una pregunta a una suposición que después haya que explicar en la feria.

## Arquitectura

La aplicación vive en fastapi/ y está separada en capas dentro de fastapi/app/.

La capa de API (app/api/) tiene rutas.py con los endpoints y schemas.py con los schemas de Pydantic. Una ruta recibe el schema de entrada, llama a una función de servicio pasando los argumentos por nombre, y devuelve lo que esa función retorna. No hay lógica en las rutas.

La capa de servicio (app/servicio/) tiene la lógica de la aplicación en Python nativo. Orquesta: llama a funciones del repositorio, llama al agente, llama al motor. No construye consultas, no usa select, no hace commit; la sesión solo la recibe y la pasa hacia el repositorio. Sus archivos son mensajes.py (orquesta un mensaje entrante de principio a fin), agente.py (cliente del modelo, carga del prompt y herramienta), leads.py (variables del motor, ciclo de la solicitud, escalación y asignación de asesor), analitica.py (consultas de demanda) y conversacion.py (lo que queda de manejo de conversaciones). Mientras las piezas no los creen, el código sigue donde está hoy.

La capa de persistencia (app/persistencia/repositorio.py) tiene todas las consultas y toda la comunicación con la base de datos.

El motor de lógica difusa (app/motor/) es código puro. No importa nada de FastAPI, SQLModel, la base de datos, el cliente del modelo ni os. Recibe números, devuelve un resultado. Por eso se prueba sin levantar Docker. Sus archivos son pertenencia.py, inferencia.py, reglas.py y reglas.yaml.

El prompt del agente vive en fastapi/prompts/agente.md, no dentro del código.

Las excepciones propias del dominio viven en app/excepciones.py y sus manejadores en main.py. models.py, database.py y seed.py siguen en la raíz de fastapi/ y no se mueven.

## Flujo de un mensaje

Python es el orquestador. n8n deja de tener lógica de negocio: recibe el mensaje de Telegram, llama a un solo endpoint, le envía al cliente la respuesta, y si el endpoint devolvió una notificación se la envía al asesor. Nada más. El flujo de n8n lo arma Juan Diego a mano en la interfaz y lo exporta a n8n/; no edites ese JSON.

El endpoint es POST /mensaje_entrante. Recibe canal, canal_user_id, nombre (puede faltar) y texto. Devuelve respuesta_cliente y notificacion_asesor, que es nula cuando no hubo escalación en ese mensaje y, cuando la hubo, trae chat_id y texto. La ruta llama a una sola función de servicio en mensajes.py, que hace estos pasos en este orden.

Primero busca o crea la conversación por canal_user_id y guarda el mensaje del cliente con rol user. Después busca si la conversación tiene un lead abierto (estado_lead en_proceso).

Luego llama al agente con el historial, el catálogo y el estado actual del lead abierto si existe. El agente devuelve la lista completa y actual de ítems, no los cambios desde el mensaje anterior. Cada id_producto se valida contra la base: si no existe, queda nulo y el ítem cuenta como fuera de catálogo. plazo_dias se calcula en Python restando la fecha de hoy a fecha_requerida.

Si hay ítems y no hay lead abierto, se crea el lead. Si hay lead abierto, se actualizan ciudad y fecha_requerida y sus ítems se reemplazan por los nuevos, guardando en cada uno el precio y las existencias del momento. Si no hay ítems y no hay lead abierto, no se crea nada y se salta directo a guardar la respuesta.

Con el lead ya actualizado se calculan las cuatro variables (monto estimado, relación con el cliente, completitud y plazo), se evalúa el motor, se guarda la evaluación en evaluaciones_motor asociada al lead y al mensaje del cliente, y se actualizan monto_estimado, prioridad y nivel_prioridad del lead.

Después se decide la escalación, solo si el lead todavía no está escalado. Se escala si la prioridad supera el umbral definido en reglas.yaml (motivo motor), o si el agente marcó solicita_asesor (motivo solicitud_cliente). Escalar asigna el asesor menos cargado, marca escalado en verdadero, guarda el motivo y escalado_en, arma el texto de notificación para el asesor, y agrega al final de respuesta_cliente una frase fija que le dice al cliente qué asesor lo va a contactar. Un lead ya escalado no vuelve a notificar aunque su prioridad suba; eso se ve en el panel.

Por último se guarda la respuesta con rol assistant y se devuelve la salida.

Si el agente falla, no se evalúa el motor porque no hay datos. Si no había lead abierto se crea uno sin ítems, se escala con motivo fallo_tecnico, la notificación le avisa al asesor que revise la conversación, y el cliente recibe un texto fijo que dice que su solicitud pasó a un asesor. Los fallos transitorios del proveedor se siguen resolviendo con los reintentos del cliente, antes de llegar al except.

Las rutas que quedan son /mensaje_entrante, /historial, /listar_asesores, /leads_por_asesor y /cerrar_lead, más las que agreguen las piezas del panel y de demanda. Las rutas /conversacion, /guardar_mensaje, /procesar, /crear_lead, /estado, /asignar_asesor y /obtener_asesor se retiran en la pieza 4.5, no antes, porque el flujo actual de n8n las usa hasta ese momento. La columna estado de conversaciones deja de escribirse pero no se borra.

## Estilo del código Python

Los nombres de negocio van en español y en snake_case: variables, funciones, tablas, columnas, endpoints. Las construcciones técnicas conservan su nombre en inglés (session, router, logger). Las clases de SQLModel se llaman igual que la tabla, en minúscula (conversaciones, leads); no las cambies a PascalCase.

Los parámetros llevan anotación de tipo y las funciones no llevan anotación de retorno. Los identificadores se anotan como uuid.UUID importando uuid, y la sesión como session: Session.

```python
def obtener_lead_por_id(id_lead: uuid.UUID, session:Session):
    return session.get(leads, id_lead)
```

Al llamar funciones de otra capa se pasan los argumentos por nombre.

```python
return cambiar_estado_lead_para_cierre(id_lead = datos.id_lead, estado_lead = datos.estado_lead, session=session)
```

Los imports se escriben en una línea por módulo, y cuando la línea se alarga se repite el from en otra línea en vez de partirla.

```python
from app.persistencia.repositorio import creacion_conversacion, verificacion_existencia_conversacion, historial_conversacion
from app.persistencia.repositorio import crear_lead, actualizar_estado_conversacion, obtener_productos
```

En el repositorio, las consultas usan session.exec(select(...).where(...)) con .first(), .all() o .one(), o session.get cuando es por llave primaria. Las escrituras siguen siempre el mismo orden: add, commit, refresh y return.

```python
def actualizar_estado_cierre(id_lead: uuid.UUID, estado_lead: str, session: Session):
    lead = session.get(leads, id_lead)
    if not lead:
        raise LeadNoEncontrado
    lead.estado_lead = estado_lead
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead
```

Las validaciones son un if not seguido de raise con una excepción del dominio. Las excepciones nuevas son clases vacías con pass en app/excepciones.py, y cada una tiene su manejador en main.py con un JSONResponse que devuelve detail.

El logging usa logger = logging.getLogger(__name__) al inicio del módulo. Los mensajes son f-strings en español y siempre llevan el identificador de la conversación con este formato: [Conversación ID: {id_conversacion}]. Dentro de un except se usa logger.exception; para un estado anómalo sin excepción, logger.error; para los pasos importantes del flujo (lead creado, motor evaluado con su prioridad, lead escalado con su motivo), logger.info.

No se escriben docstrings. Los comentarios son escasos, en español, cortos, y solo explican una razón que el código no deja ver; nunca describen lo que la línea ya dice. No se deja código comentado. No se usan emojis en el código.

Los schemas de Pydantic terminan en Entrada, Salida o Respuesta según su papel (LeadEntrada, CerrarLeadSalida). Los enumerados heredan de str y Enum y terminan en Enum (EstadoCierreEnum).

En rutas.py las rutas usan comillas simples, declaran response_model y reciben la sesión como session = Depends(get_session).

```python
@router.put('/cerrar_lead', response_model=CerrarLeadSalida)
def cerrar_lead(datos: CerrarLeadEntrada, session=Depends(get_session)):
    return cambiar_estado_lead_para_cierre(id_lead = datos.id_lead, estado_lead = datos.estado_lead, session=session)
```

## Pruebas

Se usa pytest. Las pruebas viven en fastapi/tests/ con la misma forma de carpetas que app/ (las del motor en fastapi/tests/motor/). Son funciones sueltas, sin clases, con nombres en español que dicen el caso: test_triangular_en_el_pico_vale_uno. Cada prueba verifica una sola cosa con assert, y los flotantes se comparan con pytest.approx. No se usan fixtures salvo que la instrucción lo pida. Las pruebas del motor y de las variables se corren desde fastapi/ sin Docker.

## Estilo del frontend

HTML, CSS y JavaScript sin frameworks, en fastapi/static/. Los estilos viven solo en style.css; no agregues estilos en línea ni bloques style en el HTML. Las clases del semáforo (prioridad-critica, prioridad-alta, prioridad-media, prioridad-baja) y de las insignias ya existen.

En script.js los elementos se toman con const y getElementById al inicio del archivo. Cada llamada al backend es una async function con try y catch que revisa response.ok y lanza new Error con un mensaje en español. El render se hace en funciones renderizarAlgo que crean los nodos con createElement y llenan el texto con textContent, nunca con innerHTML a partir de datos del servidor.

## Migraciones

Los cambios de esquema se hacen con Alembic, siempre por agregado salvo que la instrucción diga lo contrario. La migración se genera con autogenerate, se revisa a mano y se nombra en español describiendo el cambio (crear_tabla_items_solicitados). Nunca se edita una migración que ya existe.

## Decisiones vigentes del dominio

La empresa de la demo es Tornalba Suministros Técnicos S.A.S., una distribuidora B2B ficticia de suministros industriales y ferretería técnica.

Una conversación tiene como máximo un lead abierto. El lead se crea con el primer ítem que el cliente menciona, se escale o no, porque lo que no se escala también tiene que dejar rastro.

El agente solo extrae información y nunca decide la escalación. Su herramienta devuelve respuesta_cliente, items (cada uno con id_producto o nulo, descripcion y cantidad), ciudad, fecha_requerida y solicita_asesor. descripcion es un nombre genérico y corto del producto (por ejemplo disco diamantado de 9 pulgadas), para que la demanda fuera de catálogo se pueda agrupar.

La prioridad la calcula el motor con inferencia Sugeno de orden cero y sirve para ordenar la bandeja. La escalación es una decisión distinta que usa la prioridad como uno de sus motivos. motivo_escalacion toma uno de estos valores: motor, solicitud_cliente, fallo_tecnico. nivel_prioridad toma uno de estos: baja, media, alta, critica. estado_lead sigue siendo en_proceso, venta o no_venta.

Tablas y columnas acordadas. En productos: id_producto, referencia, nombre_producto, categoria, unidad, precio_unitario, existencias. En leads se agregan monto_estimado, fecha_requerida, prioridad, nivel_prioridad, escalado, motivo_escalacion, escalado_en y cerrado_en, y ciudad y productos_interes pasan a ser nullable. La tabla items_solicitados tiene id_item, id_lead, id_producto (nullable), descripcion, cantidad, precio_al_momento y existencias_al_momento. La tabla evaluaciones_motor tiene id_evaluacion, id_lead, id_mensaje, monto_estimado, relacion_cliente, completitud, plazo_dias, prioridad, nivel_prioridad, reglas_activadas y creado_en.

Se guardan los datos que necesitan las funciones de trabajo futuro de PLAN.md, pero esas funciones no se construyen.

## Fuera de alcance

Todo lo que PLAN.md lista como trabajo futuro, además de CI/CD, conversión a async y algoritmos evolutivos. Si una solución los necesita, se detiene y se consulta.

## Documentación

README.md y DECISIONES.md van en la redacción de Juan Diego: párrafos corridos, paréntesis para aclarar, sin tablas, sin diagramas en ASCII, sin negritas repartidas, sin emojis y sin guiones largos. Solo se editan cuando la instrucción lo pide.


Las excepciones ConfiguracionMotorInvalida y EntradaMotorInvalida son las únicas que no tienen manejador en main.py, porque son errores de programación o de configuración del motor y deben detectarse en desarrollo, no convertirse en una respuesta HTTP.