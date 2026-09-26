diff --git a/CLAUDE.md b/CLAUDE.md
index b153915..184460c 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -20,9 +20,11 @@ Si algo es ambiguo (un nombre, un valor por defecto, qué hacer en un caso borde
 
 La aplicación vive en fastapi/ y está separada en capas dentro de fastapi/app/.
 
-La capa de API (app/api/) tiene rutas.py con los endpoints y schemas.py con los schemas de Pydantic. Una ruta recibe el schema de entrada, llama a una función de servicio pasando los argumentos por nombre, y devuelve lo que esa función retorna. No hay lógica en las rutas.
+La capa de API (app/api/) tiene rutas.py con los endpoints, schemas.py con los schemas de Pydantic y seguridad.py con la autenticación del backoffice. Una ruta recibe el schema de entrada, llama a una función de servicio pasando los argumentos por nombre, y devuelve lo que esa función retorna. No hay lógica en las rutas.
 
-La capa de servicio (app/servicio/) tiene la lógica de la aplicación en Python nativo. Orquesta: llama a funciones del repositorio, llama al agente, llama al motor. No construye consultas, no usa select, no hace commit; la sesión solo la recibe y la pasa hacia el repositorio. Sus archivos son mensajes.py (orquesta un mensaje entrante de principio a fin), agente.py (cliente del modelo, carga del prompt y herramienta), leads.py (variables del motor, ciclo de la solicitud, escalación y asignación de asesor), analitica.py (consultas de demanda) y conversacion.py (lo que queda de manejo de conversaciones). Mientras las piezas no los creen, el código sigue donde está hoy.
+rutas.py tiene dos routers. router_publico lleva solo lo que usa el cliente sin sesión (/chat, /chat/historial, /entrar y /salir). router_admin lleva todo lo demás y tiene la dependencia verificar_admin, que acepta la cookie firmada radar_sesion o autenticación básica (la que usa n8n). Una ruta nueva va en router_admin salvo que la instrucción diga que es pública. Las páginas del backoffice (/panel, /reporte, /simulador) usan verificar_pagina_admin, que sin sesión redirige a /entrar.
+
+La capa de servicio (app/servicio/) tiene la lógica de la aplicación en Python nativo. Orquesta: llama a funciones del repositorio, llama al agente, llama al motor. No construye consultas, no usa select, no hace commit; la sesión solo la recibe y la pasa hacia el repositorio. Sus archivos son mensajes.py (orquesta un mensaje entrante de principio a fin), agente.py (cliente del modelo, carga del prompt y herramienta), leads.py (variables del motor, ciclo de la solicitud, escalación y asignación de asesor), analitica.py (consultas de demanda), conversacion.py (manejo de conversaciones y mensajes), notificaciones.py (alerta por Telegram del canal web y lectura del token del bot) y voz.py (descarga y transcripción de las notas de voz).
 
 La capa de persistencia (app/persistencia/repositorio.py) tiene todas las consultas y toda la comunicación con la base de datos.
 
@@ -46,13 +48,17 @@ Si hay ítems y no hay lead abierto, se crea el lead. Si hay lead abierto, se ac
 
 Con el lead ya actualizado se calculan las cuatro variables (monto estimado, relación con el cliente, completitud y plazo), se evalúa el motor, se guarda la evaluación en evaluaciones_motor asociada al lead y al mensaje del cliente, y se actualizan monto_estimado, prioridad y nivel_prioridad del lead.
 
-Después se decide la escalación, solo si el lead todavía no está escalado. Se escala si la prioridad alcanza o supera el umbral definido en reglas.yaml (motivo motor), o si el agente marcó solicita_asesor (motivo solicitud_cliente). Escalar asigna el asesor menos cargado, marca escalado en verdadero, guarda el motivo y escalado_en, arma el texto de notificación para el asesor, y agrega al final de respuesta_cliente una frase fija que le dice al cliente qué asesor lo va a contactar. Un lead ya escalado no vuelve a notificar aunque su prioridad suba; eso se ve en el panel.
+Después se decide la escalación, solo si el lead todavía no está escalado. Se escala si la prioridad alcanza o supera el umbral definido en reglas.yaml (motivo motor), o si el agente marcó solicita_asesor (motivo solicitud_cliente). Escalar asigna el asesor menos cargado, marca escalado en verdadero, guarda el motivo y escalado_en, arma el texto de notificación para el asesor, y agrega al principio de respuesta_cliente una frase fija que le dice al cliente qué asesor lo va a contactar. Un lead ya escalado no vuelve a notificar aunque su prioridad suba; eso se ve en el panel.
 
 Por último se guarda la respuesta con rol assistant y se devuelve la salida.
 
-Si el agente falla, no se evalúa el motor porque no hay datos. Si no había lead abierto se crea uno sin ítems, se escala con motivo fallo_tecnico, la notificación le avisa al asesor que revise la conversación, y el cliente recibe un texto fijo que dice que su solicitud pasó a un asesor. Los fallos transitorios del proveedor se siguen resolviendo con los reintentos del cliente, antes de llegar al except.
+Si el agente falla, no se evalúa el motor porque no hay datos. Si no había lead abierto se crea uno sin ítems, se escala con motivo fallo_tecnico, la notificación le avisa al asesor que revise la conversación, y el cliente recibe solo el texto fijo de fallo técnico, sin la frase de confirmación. Si ya había un lead abierto, sus ítems no se tocan. Los fallos transitorios del proveedor se siguen resolviendo con los reintentos del cliente, antes de llegar al except.
+
+Si el mensaje llega sin texto, se responde un texto fijo sin llamar al agente ni guardar nada. Si trae voz_file_id (nota de voz de Telegram), antes se descarga y se transcribe con Whisper, y la transcripción sigue el flujo como si el cliente la hubiera escrito; si no se puede transcribir, se responde otro texto fijo que le pide escribirla.
+
+El canal web no pasa por n8n. Entra por POST /chat, que fija canal = "web" en el servicio, exige un teléfono celular colombiano y nunca devuelve notificacion_asesor al navegador. Si la conversación web escala, FastAPI le manda la alerta al asesor directo por Telegram (notificaciones.py). El canal_user_id del canal web es un uuid que funciona como llave de la conversación: viaja en el cuerpo, nunca en la URL, y no se escribe en los logs.
 
-Las rutas que quedan son /mensaje_entrante, /historial, /listar_asesores, /leads_por_asesor y /cerrar_lead, más las que agreguen las piezas del panel y de demanda. Las rutas /conversacion, /guardar_mensaje, /procesar, /crear_lead, /estado, /asignar_asesor y /obtener_asesor se retiran en la pieza 4.5, no antes, porque el flujo actual de n8n las usa hasta ese momento. La columna estado de conversaciones deja de escribirse pero no se borra.
+Las rutas públicas son /chat, /chat/historial, /entrar y /salir. Las protegidas son /mensaje_entrante, /listar_asesores, /leads_por_asesor, /leads_sin_asignar, /evaluaciones_lead, /cerrar_lead, /demanda, /conversaciones_simulador y /mensajes_simulador, más /docs y /openapi.json. La columna estado de conversaciones y la columna productos_interes de leads ya no se escriben, pero no se borran.
 
 ## Estilo del código Python
 
@@ -75,7 +81,7 @@ Los imports se escriben en una línea por módulo, y cuando la línea se alarga
 
 ```python
 from app.persistencia.repositorio import creacion_conversacion, verificacion_existencia_conversacion, historial_conversacion
-from app.persistencia.repositorio import crear_lead, actualizar_estado_conversacion, obtener_productos
+from app.persistencia.repositorio import obtener_productos_por_ids, reemplazar_items_de_lead, obtener_items_de_lead
 ```
 
 En el repositorio, las consultas usan session.exec(select(...).where(...)) con .first(), .all() o .one(), o session.get cuando es por llave primaria. Las escrituras siguen siempre el mismo orden: add, commit, refresh y return.
@@ -92,9 +98,9 @@ def actualizar_estado_cierre(id_lead: uuid.UUID, estado_lead: str, session: Sess
     return lead
 ```
 
-Las validaciones son un if not seguido de raise con una excepción del dominio. Las excepciones nuevas son clases vacías con pass en app/excepciones.py, y cada una tiene su manejador en main.py con un JSONResponse que devuelve detail.
+Las validaciones son un if not seguido de raise con una excepción del dominio. Las excepciones nuevas son clases vacías con pass en app/excepciones.py, y cada una tiene su manejador en main.py con un JSONResponse que devuelve detail. La excepción es seguridad.py, que usa HTTPException porque así trabaja HTTPBasic de FastAPI, y SesionRequerida, cuyo manejador redirige a /entrar en vez de devolver JSON.
 
-El logging usa logger = logging.getLogger(__name__) al inicio del módulo. Los mensajes son f-strings en español y siempre llevan el identificador de la conversación con este formato: [Conversación ID: {id_conversacion}]. Dentro de un except se usa logger.exception; para un estado anómalo sin excepción, logger.error; para los pasos importantes del flujo (lead creado, motor evaluado con su prioridad, lead escalado con su motivo), logger.info.
+El logging usa logger = logging.getLogger(__name__) al inicio del módulo. Los mensajes son f-strings en español y siempre llevan el identificador de la conversación con este formato: [Conversación ID: {id_conversacion}]. Dentro de un except se usa logger.exception; para un estado anómalo sin excepción, logger.error; para los pasos importantes del flujo (lead creado, motor evaluado con su prioridad, lead escalado con su motivo), logger.info. Cuando todavía no hay conversación (un mensaje sin texto, la configuración del backoffice), el log lleva el canal en su lugar. Nunca se registran el token del bot, la clave del administrador, las URL de la API de Telegram (llevan el token adentro) ni el canal_user_id del canal web. Un error esperado con un motivo claro (por ejemplo, Telegram respondiendo 400) va con logger.error y su motivo, no con logger.exception.
 
 No se escriben docstrings. Los comentarios son escasos, en español, cortos, y solo explican una razón que el código no deja ver; nunca describen lo que la línea ya dice. No se deja código comentado. No se usan emojis en el código.
 
@@ -110,14 +116,16 @@ def cerrar_lead(datos: CerrarLeadEntrada, session=Depends(get_session)):
 
 ## Pruebas
 
-Se usa pytest. Las pruebas viven en fastapi/tests/ con la misma forma de carpetas que app/ (las del motor en fastapi/tests/motor/). Son funciones sueltas, sin clases, con nombres en español que dicen el caso: test_triangular_en_el_pico_vale_uno. Cada prueba verifica una sola cosa con assert, y los flotantes se comparan con pytest.approx. No se usan fixtures salvo que la instrucción lo pida. Las pruebas del motor y de las variables se corren desde fastapi/ sin Docker.
+Se usa pytest. Las pruebas viven en fastapi/tests/ con la misma forma de carpetas que app/ (las del motor en fastapi/tests/motor/, las de servicio en fastapi/tests/servicio/ y las de la API en fastapi/tests/api/). test_reglas_tornalba.py fija el comportamiento de las reglas reales de reglas.yaml; si se cambia una regla, esas pruebas tienen que cambiar con valores calculados a mano. Son funciones sueltas, sin clases, con nombres en español que dicen el caso: test_triangular_en_el_pico_vale_uno. Cada prueba verifica una sola cosa con assert, y los flotantes se comparan con pytest.approx. No se usan fixtures salvo que la instrucción lo pida. Las pruebas del motor y de las variables se corren desde fastapi/ sin Docker.
 Las pruebas se corren dentro del contenedor de FastAPI, que es donde están fijadas las versiones. El código del motor no depende del contenedor y se puede ejecutar con el Python del sistema, pero pytest solo está instalado en la imagen.
 
 ## Estilo del frontend
 
-HTML, CSS y JavaScript sin frameworks, en fastapi/static/. Los estilos viven solo en style.css; no agregues estilos en línea ni bloques style en el HTML. Las clases del semáforo (prioridad-critica, prioridad-alta, prioridad-media, prioridad-baja) y de las insignias ya existen.
+HTML, CSS y JavaScript sin frameworks, en fastapi/static/. Cada página tiene su HTML, su CSS y su JS con el mismo nombre (cliente para index.html, entrar, panel, reporte y simulador), y comun.css y comun.js tienen lo que comparten (variables de color, encabezado, avisos, llamarBackend y la salida del backoffice). No agregues estilos en línea ni bloques style en el HTML. Las clases del semáforo (prioridad-critica, prioridad-alta, prioridad-media, prioridad-baja) y de las insignias ya existen. Las clases siguen la forma bloque__elemento--modificador.
 
-En script.js los elementos se toman con const y getElementById al inicio del archivo. Cada llamada al backend es una async function con try y catch que revisa response.ok y lanza new Error con un mensaje en español. El render se hace en funciones renderizarAlgo que crean los nodos con createElement y llenan el texto con textContent, nunca con innerHTML a partir de datos del servidor.
+La página del cliente (index.html) no enlaza nada del backoffice y le habla al cliente de usted. Las páginas del backoffice llevan la identidad de Radar y la navegación con Salir. Si la API responde 401, el backoffice vuelve a /entrar.
+
+En cada JS los elementos se toman con const y getElementById al inicio del archivo. Cada llamada al backend es una async function con try y catch que revisa response.ok y lanza new Error con un mensaje en español. El render se hace en funciones renderizarAlgo que crean los nodos con createElement y llenan el texto con textContent, nunca con innerHTML a partir de datos del servidor.
 
 ## Migraciones
 
@@ -133,7 +141,9 @@ El agente solo extrae información y nunca decide la escalación. Su herramienta
 
 La prioridad la calcula el motor con inferencia Sugeno de orden cero y sirve para ordenar la bandeja. La escalación es una decisión distinta que usa la prioridad como uno de sus motivos. motivo_escalacion toma uno de estos valores: motor, solicitud_cliente, fallo_tecnico. nivel_prioridad toma uno de estos: baja, media, alta, critica. estado_lead sigue siendo en_proceso, venta o no_venta.
 
-Tablas y columnas acordadas. En productos: id_producto, referencia, nombre_producto, categoria, unidad, precio_unitario, existencias. En leads se agregan monto_estimado, fecha_requerida, prioridad, nivel_prioridad, escalado, motivo_escalacion, escalado_en y cerrado_en, y ciudad y productos_interes pasan a ser nullable. La tabla items_solicitados tiene id_item, id_lead, id_producto (nullable), descripcion, cantidad, precio_al_momento y existencias_al_momento. La tabla evaluaciones_motor tiene id_evaluacion, id_lead, id_mensaje, monto_estimado, relacion_cliente, completitud, plazo_dias, prioridad, nivel_prioridad, reglas_activadas y creado_en.
+El canal web identifica al cliente con un uuid generado en su navegador y le pide un celular colombiano (10 dígitos que empiezan por 3), que se guarda en conversaciones.telefono. El asesor lo contacta por WhatsApp con el enlace https://wa.me/57 más el número. El motor tiene quince reglas.
+
+Tablas y columnas acordadas. En conversaciones se agrega telefono (nullable). En productos: id_producto, referencia, nombre_producto, categoria, unidad, precio_unitario, existencias. En leads se agregan monto_estimado, fecha_requerida, prioridad, nivel_prioridad, escalado, motivo_escalacion, escalado_en y cerrado_en, y ciudad y productos_interes pasan a ser nullable. La tabla items_solicitados tiene id_item, id_lead, id_producto (nullable), descripcion, cantidad, precio_al_momento y existencias_al_momento. La tabla evaluaciones_motor tiene id_evaluacion, id_lead, id_mensaje, monto_estimado, relacion_cliente, completitud, plazo_dias, prioridad, nivel_prioridad, reglas_activadas y creado_en.
 
 Se guardan los datos que necesitan las funciones de trabajo futuro de PLAN.md, pero esas funciones no se construyen.
 
diff --git a/DECISIONES.md b/DECISIONES.md
index 81c8791..303ddd3 100644
--- a/DECISIONES.md
+++ b/DECISIONES.md
@@ -11,6 +11,7 @@ Casi siempre coinciden, pero se separan justo en los casos caros, como un client
 La causa de fondo es que la salida es binaria, y siendo binaria solo se puede elegir entre dos reglas malas: escalar de más e inundar a los asesores, o escalar de menos
 y perder clientes. Con una salida continua la completitud dejaría de ser una compuerta y pasaría a ser una variable más que baja la prioridad, sin bloquear nada.
 Se deja tal cual en esta versión, porque es el comportamiento conocido y documentado del sistema.
+En Radar esa compuerta desapareció. La completitud pasó a ser una de las cuatro variables del motor, que baja o sube la prioridad sin bloquear nada, y la escalación la decide la prioridad junto con otros dos motivos (ver "La prioridad y la escalación son decisiones separadas").
 
 ## Cuando el modelo falla, el lead se escala a un humano
 El bloque except de comunicacion_agente devolvía escalar en False y un mensaje pidiéndole al cliente que volviera a escribir más tarde.
@@ -19,6 +20,7 @@ anterior (ahí se trata de calificar el lead, acá de que el sistema no está fu
 Ahora, ante un fallo del modelo, se escala. Como el schema de entrada de /crear_lead exige que los campos no vengan vacíos, los datos que no se alcanzaron a capturar
 viajan como "Por confirmar", lo que de paso le indica al asesor qué es lo que le falta preguntarle al cliente.
 La regla que queda es que cuando la IA falla el sistema no inventa ni abandona, sino que entrega el caso a una persona.
+En Radar la regla se mantiene, pero ya no hacen falta los "Por confirmar": si no había solicitud abierta se crea una sin ítems, se escala con motivo fallo_tecnico y la alerta le pide al asesor que revise la conversación. Si ya había una solicitud abierta, sus ítems no se tocan, porque una extracción fallida no es confiable y borraría lo que el cliente ya había pedido.
 
 ## El modelo es configuración, no código
 El sistema dejó de funcionar de un día para otro sin que yo hubiera tocado nada: Groq retiró el modelo llama-3.3-70b-versatile y todas las llamadas empezaron a devolver
@@ -57,17 +59,6 @@ Desde el panel, el asesor cierra cada lead como venta o no venta.
 Esto es lo que amarra cada decisión que tomó el sistema con lo que pasó de verdad con ese cliente. Sin ese registro no hay manera de saber si las decisiones automáticas
 estaban bien tomadas, y el sistema termina generando su propio conjunto de datos en vez de depender de datos externos.
 
-## Deuda técnica conocida
-menos_cargado llama a comparacion() una vez por cada asesor, o sea una consulta por asesor. Con cuatro no se nota, con cincuenta sí; se resuelve con una sola consulta
-agrupada.
-catalogo_a_texto consulta la base y arma el texto del catálogo en cada mensaje, cuando se podría cachear.
-Los endpoints del panel no tienen autenticación. Es aceptable corriendo en local, no lo sería en un servidor.
-/procesar consume cuota del proveedor en cada llamada y no tiene un límite de tasa propio.
-productos_interes se guarda como texto libre, sin normalizar contra el catálogo; es lo que resolvería la búsqueda semántica.
-La imagen de n8n está en latest, así que se puede actualizar sola y romper el entorno; convendría fijar la versión.
-El prompt del agente vive dentro de conversacion.py, sin historial propio ni manera de evaluar si un cambio lo mejoró o lo empeoró.
-No hay pruebas automatizadas ni un conjunto de casos para verificar el comportamiento del agente.
-
 ## El backend es síncrono y la concurrencia se resuelve en la base de datos
 Los endpoints de FastAPI están declarados como funciones normales y no como async. FastAPI corre ese tipo de funciones en un grupo de hilos, así que varios mensajes que llegan al mismo tiempo se atienden en paralelo sin que uno bloquee a los demás.
 Casi todo el tiempo de cada mensaje se va en la llamada al modelo (uno o dos segundos), y al volumen de conversaciones que recibe una distribuidora por Telegram los hilos alcanzan de sobra.
@@ -77,4 +68,69 @@ Lo que sí había que resolver es otro problema que suele confundirse con este.
 La solución quedó en PostgreSQL: un índice único parcial sobre id_conversacion para los leads en estado en_proceso. Si la segunda inserción choca con el índice, se deshace y se continúa con el lead que creó el primer mensaje.
 Así, la regla de un lead abierto por conversación no depende de que el código esté bien escrito: la garantiza la base de datos.
 
-Entorno de desarrollo local con las dependencias instaladas fuera de Docker, para correr las pruebas sin levantar los contenedores.
\ No newline at end of file
+## La solicitud nace con el primer producto, se escale o no
+En la versión clásica el lead solo existía si se escalaba, así que todo lo que el sistema atendía sin pasarlo a un asesor desaparecía sin dejar rastro. No había manera de saber cuántas solicitudes llegaban ni qué pedían.
+Ahora la solicitud se crea en cuanto el cliente menciona el primer producto, y cada mensaje siguiente la actualiza: los ítems se reemplazan por la lista completa y actual que devuelve el agente (no por los cambios), guardando el precio y las existencias de ese momento. Sin productos y sin solicitud abierta no se crea nada, para no llenar la base de saludos.
+Una conversación tiene como máximo una solicitud abierta, y eso lo garantiza la base de datos con un índice único parcial (ver la entrada sobre el backend síncrono).
+Esa decisión es la que hace posible el reporte de demanda: lo que no se escala también cuenta.
+
+## La prioridad y la escalación son decisiones separadas
+La prioridad responde en qué orden hay que atender; la escalación responde si hay que meter a una persona ya. Toda solicitud tiene prioridad y aparece ordenada en la bandeja, pero solo algunas se escalan.
+Se escala por uno de tres motivos, revisados en este orden: fallo_tecnico (el modelo falló y no hay datos para calcular nada), solicitud_cliente (el cliente pidió hablar con una persona, sin importar la prioridad) y motor (la prioridad alcanza el umbral, que hoy es 50 y vive en reglas.yaml). Una solicitud que ya se escaló no vuelve a notificar aunque su prioridad suba; eso se ve en el panel.
+El agente no decide nada de esto. Solo extrae qué pidió el cliente, en qué cantidad, para cuándo y desde dónde, y si pidió hablar con alguien. Así la decisión es determinística y se puede explicar regla por regla.
+
+## La urgencia se mide en días a partir de una fecha
+Al modelo no se le pide que califique qué tan urgente es una solicitud, se le pide que extraiga la fecha en que el cliente necesita los productos. Una fecha se puede verificar y una etiqueta como "urgente" no.
+El plazo en días lo calcula Python restando la fecha de hoy a esa fecha. El prompt fija las equivalencias de las expresiones comunes (hoy, ya o lo antes posible es hoy; esta semana es el viernes de esta semana) para que el modelo no las interprete distinto cada vez, y si el cliente no dice ninguna fecha no se inventa ninguna: el plazo queda vacío y las reglas que dependen de él no se activan.
+La fecha se guarda en la solicitud, así que el plazo se recalcula en cada mensaje aunque el cliente no la repita.
+
+## n8n queda como canal y Python orquesta
+En la versión clásica la lógica del flujo estaba repartida entre trece nodos de n8n que llamaban a siete rutas distintas. Probarla, versionarla o explicarla era difícil, porque vivía en una interfaz gráfica.
+Ahora n8n tiene cinco nodos: recibe el mensaje de Telegram, llama a /mensaje_entrante, le responde al cliente y, si hubo escalación, le manda la alerta al asesor. Toda la lógica está en Python, en una sola función de servicio que se puede leer de arriba abajo y probar.
+El canal web ni siquiera pasa por n8n: llama directo a FastAPI, y por eso en ese canal es FastAPI el que le escribe al asesor por Telegram.
+
+## Las fechas se guardan en UTC y se interpretan en la hora de Colombia
+Las marcas de tiempo (cuándo se creó un mensaje, cuándo se escaló o se cerró una solicitud) se guardan en UTC y con zona horaria, para que Postgres devuelva fechas comparables sin ambigüedad.
+Pero el "hoy" del negocio es el de Colombia. Si el plazo se calculara con la fecha UTC, a partir de las siete de la noche el sistema creería que ya es mañana y un pedido "para hoy" saldría vencido. Por eso el plazo, el reporte de demanda y la fecha que ve el agente usan hoy_bogota().
+
+## El cliente web se identifica con un uuid de su navegador
+El chat web no tiene usuarios ni inicio de sesión para el cliente: pedir una cuenta para cotizar unos tornillos haría que nadie escribiera. El navegador genera un uuid la primera vez, lo guarda y lo manda con cada mensaje, y ese uuid es la llave de su conversación.
+Como es lo único que da acceso a la conversación, se genera con el generador criptográfico del navegador (no se puede adivinar), viaja en el cuerpo de la petición y no en la URL (para que no quede escrito en los logs del servidor ni en el historial del navegador), y no se escribe en ningún log de la aplicación.
+El canal web tiene sus propias rutas públicas (/chat y /chat/historial) con el canal fijo en el servidor. /mensaje_entrante, que recibe el canal desde afuera, quedó protegida, porque con ella cualquiera podría escribir en la conversación de otra persona.
+La contracara es que si el cliente borra los datos de su navegador empieza una conversación nueva, y que cada navegador cuenta como un cliente distinto para la relación.
+
+## El cliente web deja su celular y el asesor lo contacta por WhatsApp
+Cuando una conversación web escalaba, el cliente leía que un asesor lo iba a contactar, pero el asesor solo tenía un uuid. La frase era falsa, el mismo tipo de error que ya se había corregido con el texto de la respuesta repetida.
+Por eso el chat web pide un celular colombiano antes del primer mensaje, y el panel y la alerta al asesor muestran un enlace de WhatsApp que abre el chat con ese número.
+Guardar un teléfono es tratar un dato personal, así que junto al campo va el texto de autorización de contacto (Ley 1581 de habeas data), y el teléfono solo se usa para eso.
+
+## En el canal web, FastAPI le escribe directo a Telegram
+Había tres opciones para avisarle al asesor cuando escala una conversación web: que FastAPI le escribiera directo a Telegram, que llamara a un segundo flujo de n8n por webhook, o dejarlo solo en el panel. Elegí la primera porque son pocas líneas con la librería estándar, no agrega dependencias y no abre otro webhook público que habría que proteger. El costo es que el token del bot queda en dos lugares, la credencial de n8n y el .env.
+Dos reglas salieron de ahí. La primera, que el token nunca aparece en un log: la URL de la API de Telegram lo lleva adentro, así que ni la URL ni la petición se registran, y el token se valida antes de armar la URL para que un carácter raro no lo meta en el mensaje de un error. La segunda, que un fallo de Telegram nunca tumba la respuesta al cliente: la alerta es secundaria.
+
+## El backoffice tiene un solo administrador y una sesión firmada
+El único que usa el panel, el reporte y el simulador soy yo, así que no hay tabla de usuarios: el usuario y la clave viven en el .env y se comparan con secrets.compare_digest, que tarda lo mismo acierte o no.
+Primero usé la autenticación básica de HTTP, pero el navegador muestra su propia ventana para pedir la clave y esa ventana no se puede diseñar. Por eso se agregó una página /entrar que, con la clave correcta, deja una cookie firmada con HMAC. La firma usa la clave del administrador como llave, así que nadie puede fabricar una cookie sin conocerla, y cambiar la clave cierra todas las sesiones. La cookie dura doce horas y no la puede leer el JavaScript de la página ni la mandan otros sitios.
+n8n sigue entrando con autenticación básica, porque es un programa y no una persona. Las rutas están separadas en un router público y uno protegido, así que una ruta nueva queda protegida por estar en ese router y no por acordarse de ponerle la dependencia.
+
+## Dos reglas del motor diluían la prioridad
+La agregación Sugeno es un promedio ponderado, y eso tiene una consecuencia que no se ve hasta que se prueban casos concretos: una regla que se activa con una salida baja arrastra el promedio hacia abajo, aunque todas las demás digan que el caso es grave.
+Eso pasaba con solicitud_urgente y cliente_recurrente, dos reglas de una sola condición que proponían media (45). Un pedido grande y urgente de un cliente nuevo sacaba 68,75, menos que el mismo pedido sin fecha (70); uno de un cliente recurrente sacaba 62,5; y un cliente nuevo nunca llegaba a crítica.
+Se eliminaron las dos reglas. Con las quince que quedan, el pedido grande y urgente de un cliente nuevo saca 76,67 (crítica) y el de un cliente recurrente 80. Antes de borrar se escribieron pruebas con el reglas.yaml real que mostraban el problema fallando, y ahora dejan fijado cómo se comporta el motor con las reglas de Tornalba.
+La lección es que en un promedio las reglas no suman: cada regla nueva también puede restar.
+
+## Las notas de voz se transcriben antes de llegar al agente
+En Colombia mucha gente le escribe a un negocio por nota de voz. El agente solo lee texto, así que la voz se convierte en texto antes de entrar al flujo: n8n manda el identificador del archivo, FastAPI lo descarga desde Telegram y lo transcribe con Whisper en Groq, y de ahí en adelante todo sigue igual que con un mensaje escrito.
+El modelo de voz, igual que el del agente, está en una variable de entorno (GROQ_MODELO_VOZ). Transcribir una nota de voz de veinte segundos cuesta una fracción de peso.
+Si la nota no se puede descargar o transcribir, el cliente recibe un texto fijo que le pide escribirla, sin llamar al agente ni guardar nada. Los audios de más de 5 MB no se procesan.
+
+## Deuda técnica y limitaciones conocidas
+La mayor parte de lo que estaba en esta lista en la versión clásica ya se resolvió: n8n está fijado en la versión 2.37.7, el prompt vive en prompts/agente.md, hay 213 pruebas automatizadas, lo que pide el cliente queda estructurado en items_solicitados, el asesor menos cargado sale de una sola consulta agrupada y el backoffice tiene autenticación. Lo que queda:
+catalogo_a_texto consulta la base y arma el texto del catálogo en cada mensaje, cuando se podría cachear; con cientos de referencias habría que pasar a búsqueda semántica.
+Cada función del repositorio hace su propio commit, así que un fallo a mitad del flujo puede dejar datos parciales.
+Una alerta al asesor que falla no se reintenta: la solicitud queda escalada y solo se ve en el panel. La solución sería guardar si la alerta se envió y reintentar las pendientes.
+Con audio en silencio o puro ruido, Whisper puede devolver frases que nadie dijo ("gracias por ver el video"), y esas frases llegan al agente como si el cliente las hubiera escrito.
+El agente solo recibe los últimos diez mensajes de la conversación. Lo pedido no se pierde, porque el estado de la solicitud va aparte en el prompt, pero un detalle mencionado muy atrás sí.
+Las existencias no se descuentan cuando una solicitud cierra en venta.
+/chat es pública y cada mensaje cuesta una llamada al modelo. Está limitado a mil caracteres por mensaje, pero no hay un límite de mensajes por cliente; mientras tanto, la protección es el tope de gasto de la cuenta de Groq.
+Los HTML del backoffice también se sirven desde /static sin clave. Salen vacíos, porque todos los datos vienen de la API y la API pide sesión.
diff --git a/PLAN.md b/PLAN.md
index ad11f96..88b9bae 100644
--- a/PLAN.md
+++ b/PLAN.md
@@ -146,6 +146,14 @@ Solución: leads_por_asesor devuelve los leads ordenados por prioridad con nivel
 Problema: el asesor no sabe por qué un lead está arriba.
 Solución: al abrir un lead se ven las reglas activadas con su grado y cómo fue cambiando la prioridad en cada mensaje.
 
+### 5.5 Rutas del historial del simulador
+Problema: el simulador generaba un identificador al azar en cada carga, así que al recargar la página se perdía la conversación, y /historial solo devolvía los últimos diez mensajes porque es la misma función que arma el contexto del agente.
+Solución: /conversaciones_simulador lista las conversaciones del canal simulador con su último mensaje (una sola consulta con una subconsulta LATERAL) y /mensajes_simulador devuelve el historial completo de una de ellas. El canal queda fijo en el servicio, para que las conversaciones de Telegram no salgan por estas rutas.
+
+### 5.6 Simulador con lista de conversaciones
+Problema: sin una lista no se puede volver a una conversación anterior.
+Solución: el simulador pasa a dos columnas, la lista de conversaciones a la izquierda y el chat a la derecha, con un botón de conversación nueva. Mientras se espera una respuesta o se cargan mensajes, la lista queda bloqueada para que una respuesta no termine pintada en otra conversación.
+
 ## Fase 6. Demanda invisible (28 de septiembre)
 
 ### 6.1 Semilla de historia
@@ -174,6 +182,68 @@ Actualizar el README al dominio de Tornalba, al flujo nuevo y al motor.
 Juan Diego escribe las entradas nuevas: la solicitud nace con el primer ítem, prioridad y escalación son decisiones separadas, la urgencia se mide en días a partir de una fecha, n8n queda como canal y Python orquesta, las fechas se guardan en UTC y se interpretan en la zona de Colombia, y la sección de trabajo futuro.
 También se reescribe la sección de deuda técnica conocida, que hoy describe un estado que ya cambió: n8n ya no está en latest, el prompt ya no vive en conversacion.py, ya hay pruebas automatizadas y productos_interes ya no es el único registro de lo que pidió el cliente.
 
+## Fase 8. Separación del cliente y el backoffice (25 y 26 de septiembre)
+
+El sistema se va a desplegar en un servidor y los clientes van a entrar desde el celular. Hasta aquí todo vivía en páginas abiertas: cualquiera con la URL veía el panel, el reporte y las conversaciones de los demás. Esta fase separa lo que ve el cliente (solo su chat) de lo que ve el administrador (el backoffice).
+
+### 8.1 Canal web
+Problema: la única entrada era /mensaje_entrante, que recibe el canal desde afuera y permitiría escribir en conversaciones ajenas.
+Solución: rutas públicas propias, POST /chat y POST /chat/historial, con el canal web fijo en el servidor. El identificador del cliente es un uuid que genera su navegador y llega en el cuerpo, nunca en la URL, para que no quede escrito en los logs. La ruta pública nunca devuelve la notificación del asesor, porque trae datos internos.
+
+### 8.2 Simulador en el backoffice
+Problema: el simulador con lista de conversaciones es una herramienta del administrador, no la página del cliente.
+Solución: se muda a /simulador con la identidad de Radar. index.html se deja igual hasta la 8.3 para que la raíz nunca quede rota entre commits.
+
+### 8.3 Página del cliente
+Problema: el cliente necesita un chat simple, pensado para el celular, que le muestre solo su conversación.
+Solución: index.html queda con la identidad de Tornalba, sin navegación al backoffice y con una sola columna. El identificador se guarda en localStorage (con respaldo en memoria si el navegador no lo permite) y se genera con crypto.randomUUID o, por http, con crypto.getRandomValues.
+
+### 8.4 Celular del cliente web
+Problema: un cliente web no tenía cómo ser contactado. El asesor solo veía un uuid, pero al escalar el cliente recibía "lo va a contactar en breve".
+Solución: columna telefono en conversaciones (8.4a) y teléfono opcional en /chat conectado hasta la conversación (8.4b). Solo celulares colombianos de diez dígitos que empiezan por 3. Se escribe al crear la conversación y no se reemplaza después.
+
+### 8.5 Campo de celular y autorización
+Problema: el teléfono tenía que pedirse en la página y volverse obligatorio sin romper a los clientes que ya habían chateado.
+Solución: el campo aparece mientras el navegador no tenga un teléfono guardado, haya historial o no. El navegador lo limpia (espacios, guiones, paréntesis, el más y el 57) antes de enviarlo. Junto al campo va el texto de autorización de contacto por WhatsApp. En el mismo commit el teléfono pasa a ser obligatorio en /chat.
+
+### 8.6 WhatsApp en el panel y en la alerta
+Problema: el asesor no veía el canal ni el teléfono.
+Solución: enlace_whatsapp arma https://wa.me/57 más el número. El panel muestra el canal, el teléfono en lugar del uuid y el botón Escribir por WhatsApp, y la alerta al asesor abre con el celular y trae el enlace.
+
+### 8.7 Alerta por Telegram para el canal web
+Problema: el chat web no pasa por n8n, así que cuando una conversación web escalaba nadie se enteraba por Telegram.
+Solución: FastAPI le escribe directo a Telegram con sendMessage y el token del bot en TELEGRAM_BOT_TOKEN, usando urllib de la librería estándar. El token nunca aparece en los logs y un fallo de Telegram nunca tumba la respuesta al cliente.
+
+### 8.8 Backoffice protegido
+Problema: cualquiera podía abrir el panel, el reporte, la documentación y todas las rutas internas.
+Solución: autenticación básica con usuario y clave en ADMIN_USUARIO y ADMIN_CLAVE, comparados con secrets.compare_digest. Las rutas se separan en router_publico (/chat, /chat/historial) y router_admin (todo lo demás), así que una ruta nueva queda protegida por estar en el router y no por acordarse de ponerle la dependencia. n8n llama a /mensaje_entrante con una credencial Basic.
+
+### 8.9 Despliegue
+Problema: el sistema solo corre mientras el computador de Juan Diego está encendido, y la URL del túnel cambia en cada reinicio.
+Solución: servidor en Hetzner, dominio en Cloudflare y un túnel con nombre fijo. docker-compose de producción sin recarga automática, sin montar el código y sin exponer el puerto 8000.
+Pendiente del pago del servidor y del dominio.
+
+### 8.10 Sesión del administrador
+Problema: la ventana de usuario y clave que dibuja el navegador con la autenticación básica no se puede estilizar y da impresión de producto sin terminar.
+Solución: una sesión con cookie firmada con HMAC-SHA256 (usando ADMIN_CLAVE como llave) que dura doce horas, es HttpOnly, SameSite=Strict y Secure (8.10a); la página /entrar con la identidad de Radar (8.10b); y el botón Salir, más la vuelta a /entrar cuando la sesión vence con una página abierta (8.10c). La API dejó de mandar WWW-Authenticate para que el navegador no vuelva a mostrar su ventana. n8n sigue entrando con Basic.
+
+## Fase 9. Ajustes antes de la feria (26 de septiembre)
+
+### 9.1 Reglas que diluían la prioridad
+Problema: la agregación Sugeno es un promedio, y las reglas de una sola condición solicitud_urgente y cliente_recurrente (las dos con salida media) metían un 45 justo donde la prioridad tenía que subir. Un pedido grande y urgente de un cliente nuevo sacaba 68,75, menos que uno grande sin fecha (70), y un cliente nuevo nunca llegaba a crítica.
+Solución: se eliminaron esas dos reglas y quedaron quince. Grande, urgente y de cliente nuevo pasa a 76,67 (crítica). Se agregaron pruebas con el reglas.yaml real, que antes no tenía ninguna.
+
+### 9.2 Mensajes sin texto y frase duplicada
+Problema: un audio, un sticker o una foto por Telegram llegaba sin texto, /mensaje_entrante respondía 422 y el cliente se quedaba sin respuesta. Además, cuando fallaba el modelo el cliente leía dos veces que un asesor lo iba a contactar.
+Solución: el texto pasa a ser opcional en /mensaje_entrante y un mensaje sin texto recibe una respuesta fija sin llamar al agente. Con fallo técnico la respuesta es solo el texto de fallo.
+
+### 9.3 Limpieza
+Retiro de código sin uso (crear_lead, actualizar_estado_conversacion y la ruta /historial), argumentos por nombre y anotaciones de tipo que habían quedado desactualizadas (9.3a). En el frontend, chat.js y chat.css pasan a llamarse simulador.js y simulador.css, y Enter avanza entre los campos del chat del cliente (9.3b).
+
+### 9.4 Notas de voz por Telegram
+Problema: en Colombia la gente escribe mucho por nota de voz, y el sistema solo entendía texto.
+Solución: n8n manda el file_id de la nota de voz. FastAPI la descarga desde Telegram (máximo 5 MB), la transcribe con Whisper en Groq (modelo en GROQ_MODELO_VOZ) y sigue el flujo como si el cliente la hubiera escrito. Si no se puede transcribir, el cliente recibe un texto fijo que le pide escribirla.
+
 ## Trabajo futuro
 
 No se construye antes de la feria. Los datos que necesita ya quedan guardados.
@@ -192,10 +262,26 @@ Una herramienta de exploración de datos conectada a la base, para que el client
 
 Entorno de desarrollo local con las dependencias instaladas fuera de Docker, para correr las pruebas sin levantar los contenedores.
 
-Búsqueda semántica sobre el catálogo, calibración del motor con los cierres reales, otros canales como WhatsApp, autenticación del panel y despliegue en servidor.
+Búsqueda semántica sobre el catálogo, calibración del motor con los cierres reales y otros canales como WhatsApp.
+
+Reintento de las alertas al asesor que fallan: hoy el lead queda escalado aunque Telegram no haya recibido la alerta.
+
+Identificar al cliente por su NIT o su teléfono y no por el canal, para que la misma persona por Telegram y por la web sea un solo cliente y su historial de compras cuente para la relación.
+
+Descontar las existencias cuando un lead cierra en venta.
+
+Notas de voz en el chat web y un filtro para las frases que Whisper inventa con audio en silencio.
 
 ## Limitaciones conocidas
 
 Cada función del repositorio hace su propio commit, así que un fallo a mitad del flujo puede dejar datos parciales.
 
+Una alerta al asesor que falla (Telegram caído, token mal cargado) no se reintenta. El lead queda escalado y solo se ve en el panel.
+
+Con audio en silencio o puro ruido, Whisper puede devolver frases que nadie dijo, y esas frases llegan al agente como si el cliente las hubiera escrito.
+
+La relación con el cliente se cuenta por conversación, así que en la web cada navegador es un cliente nuevo.
+
+Los archivos HTML del backoffice también se sirven desde /static sin clave. Salen vacíos, porque todos los datos vienen de la API y la API pide sesión.
+
 Las pruebas solo corren dentro del contenedor de FastAPI. El Python del sistema es 3.14 y no trae pip ni ensurepip, y las versiones del proyecto están fijadas contra la 3.11 de la imagen.
\ No newline at end of file
diff --git a/README.md b/README.md
index 383bf33..ca4a72d 100644
--- a/README.md
+++ b/README.md
@@ -1,10 +1,11 @@
-# TRIAJE LEADS COMERCIALES/RADAR
+# RADAR
 Este sistema plantea la automatización de la atención y la clasificación de las solicitudes comerciales que le entran a una empresa por sus canales de mensajería.
-El flujo inicia con un mensaje del cliente por alguno de los canales de la empresa (actualmente Telegram), n8n lo recibe y llama a un único endpoint de FastAPI, que es
-donde vive toda la lógica. Ahí se guarda la conversación, el agente de IA lee el mensaje con el catálogo al frente y extrae lo que el cliente está pidiendo (los productos
+El flujo inicia con un mensaje del cliente por alguno de los canales de la empresa. Hoy son dos: Telegram (donde n8n recibe el mensaje, escrito o como nota de voz, y
+llama a un único endpoint de FastAPI) y el chat web de la empresa (que llama directo a FastAPI). En los dos casos toda la lógica vive en FastAPI. Ahí se guarda la conversación, el agente de IA lee el mensaje con el catálogo al frente y extrae lo que el cliente está pidiendo (los productos
 con su cantidad, la ciudad y para cuándo lo necesita), y con esos datos el sistema arma la solicitud, la valora contra el catálogo y la pasa por un motor de lógica difusa
 que calcula su prioridad. Si esa prioridad alcanza el umbral, si el cliente pidió hablar con una persona o si el modelo falló, la solicitud se escala: se le asigna el
-asesor menos cargado y se le avisa por Telegram. Al cliente se le responde por el mismo canal por el que escribió. Cuando el asesor termina de atender el lead lo cierra
+asesor menos cargado y se le avisa por Telegram (si el cliente escribió por la web, la alerta trae su celular con un enlace de WhatsApp para contactarlo). Al cliente se
+le responde por el mismo canal por el que escribió. Cuando el asesor termina de atender el lead lo cierra
 desde el panel como venta o no venta, y ese resultado también queda guardado, de manera que cada decisión que tomó el sistema queda ligada a lo que pasó realmente con ese
 cliente.
 La diferencia con la versión anterior es dónde se decide. Antes el modelo decía si el lead debía escalarse; ahora el modelo solo extrae información y la decisión la toma
@@ -17,7 +18,7 @@ La relación con el cliente sale de cuántas solicitudes anteriores de esa misma
 La completitud mide cuántos datos llegaron (si hay productos del catálogo, si tienen cantidad y si se conoce la ciudad).
 El plazo en días se calcula en Python restando la fecha que pidió el cliente contra la fecha de hoy en Colombia. Al modelo no se le pide que califique la urgencia, se le
 pide que extraiga una fecha, porque una fecha se puede verificar y una etiqueta no.
-Las funciones de pertenencia, los conjuntos de cada variable, las salidas, los cortes entre niveles, el umbral de escalación y las diecisiete reglas viven en
+Las funciones de pertenencia, los conjuntos de cada variable, las salidas, los cortes entre niveles, el umbral de escalación y las quince reglas viven en
 app/motor/reglas.yaml, fuera del código. Cambiar qué es un monto alto para otra empresa no exige tocar Python ni reconstruir la imagen.
 La inferencia es Sugeno de orden cero: cada regla activa aporta su salida ponderada por su grado de activación, y la prioridad es el promedio ponderado de todas. Antes de
 calcular las pertenencias, cada entrada se recorta a su universo, de modo que un plazo vencido cuenta como cero días y un monto por encima del máximo cuenta como el máximo.
@@ -34,8 +35,10 @@ Migraciones con Alembic
 Schemas de Pydantic (Validación de los datos que entran y salen)
 SQLModel (ORM - Definición de las tablas y comunicación con PostgreSQL)
 Cloudfared (Proxy inverso para exponer n8n por HTTPS y recibir el webhook de Telegram)
-Frontend (HTML, CSS y JS sin frameworks) con tres páginas: el chat del cliente, el panel de los asesores y el reporte de demanda
-pytest (Pruebas automatizadas del motor y de la lógica de servicio)
+Whisper en Groq (Transcripción de las notas de voz de Telegram; el modelo se define en la variable GROQ_MODELO_VOZ)
+Frontend (HTML, CSS y JS sin frameworks) separado en dos partes: la página del cliente, que solo tiene el chat, y el backoffice (panel de los asesores, reporte de demanda y
+simulador de conversaciones), protegido con usuario y clave
+pytest (Pruebas automatizadas del motor, de la lógica de servicio y de la sesión del administrador)
 
 ## Requisitos
 El sistema corre en Docker, esta tecnología se encarga de que el sistema funcione sin tener que instalar nada; las dependencias del proyecto están en el
@@ -45,15 +48,19 @@ Necesitas: Docker y Docker Compose, un bot de Telegram (creado con @BotFather) y
 ## Configuración
 En la raíz del proyecto está el archivo .env.example con todas las variables que necesita el sistema, sin valores. Se copia como .env y se completa:
 POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD (PostgreSQL)
-N8N_DB, N8N_USER, N8N_PASSWORD (Base de datos y credenciales de n8n)
+N8N_DB (Base de datos de n8n, separada de las tablas del negocio)
 WEBHOOK_URL (URL HTTPS que entrega cloudfare)
 GROQ_API_KEY (Agente IA)
 GROQ_MODEL (Modelo que usa el agente; está por fuera del código para poder cambiarlo sin tocar nada ni reconstruir la imagen)
-TELEGRAM_BOT_TOKEN (Token del bot)
+GROQ_MODELO_VOZ (Modelo que transcribe las notas de voz, por ejemplo whisper-large-v3-turbo)
+TELEGRAM_BOT_TOKEN (Token del bot; lo usa FastAPI para la alerta del canal web y para descargar las notas de voz)
+ADMIN_USUARIO, ADMIN_CLAVE (Usuario y clave del backoffice; la clave también firma la sesión, así que cambiarla cierra todas las sesiones abiertas)
 COMPOSE_PROJECT_NAME (Nombre del proyecto en Docker; fija los nombres de los volúmenes para que renombrar o mover la carpeta no rompa la persistencia de la BD)
 
 El .env nunca se sube al repositorio, por eso existe el .env.example: documenta qué hace falta sin exponer los valores.
-El token del bot de Telegram se configura como credencial dentro de n8n.
+El token del bot de Telegram se configura además como credencial dentro de n8n, y el usuario y la clave del backoffice como una credencial de autenticación básica
+en el nodo que llama a FastAPI.
+Después de cambiar cualquier variable del .env hay que recrear los contenedores con "docker compose up -d" (un restart no vuelve a leer el .env).
 
 ## Cómo levantar el entorno
 Clonar el repositorio
@@ -61,9 +68,9 @@ Crear el .env a partir del .env.example (ver sección de configuración)
 Para el proxy inverso con cloudfare: "cloudflared tunnel --url http://localhost:5678" (Recibirás una URL HTTPS como esta: "https://vitamin-barrier-odds-performing.trycloudflare.com", colócala en la variable WEBHOOK_URL del .env)
 docker compose up (al arrancar se ejecutan automáticamente las migraciones con Alembic y el seed.py que puebla el catálogo de productos y los asesores)
 Abrir n8n en la URL de cloudfare (HTTPS) e importar el archivo con el flujo (carpeta n8n/)
-Configurar la credencial de Telegram en n8n y activar el flujo
-El chat del cliente queda en http://localhost:8000/, el panel de los asesores en http://localhost:8000/panel, el reporte de demanda en http://localhost:8000/reporte y la
-documentación interactiva de la API en http://localhost:8000/docs
+Configurar en n8n la credencial de Telegram y la de autenticación básica (con ADMIN_USUARIO y ADMIN_CLAVE) en el nodo que llama a FastAPI, y activar el flujo
+El chat del cliente queda en http://localhost:8000/. El backoffice se abre entrando por http://localhost:8000/entrar con el usuario y la clave del .env, y desde ahí
+quedan el panel de los asesores (/panel), el reporte de demanda (/reporte), el simulador de conversaciones (/simulador) y la documentación interactiva de la API (/docs)
 Si quieres ver el reporte con datos, el script fastapi/semilla_historia.py carga unas semanas de solicitudes cerradas de ejemplo; se ejecuta con
 "docker exec -w /app radar_fastapi python semilla_historia.py" y se borra con el mismo comando agregando "borrar"
 
@@ -71,18 +78,22 @@ Si quieres ver el reporte con datos, el script fastapi/semilla_historia.py carga
 El Dockerfile construye el servicio de FastAPI.
 La estructura de este proyecto está guiada por 3 capas (Servicio, Persistencia y API), y las tres viven dentro de fastapi/app/. En la capa de servicio encuentras toda la
 lógica de la aplicación (en Python nativo): mensajes.py orquesta un mensaje entrante de principio a fin, agente.py tiene la comunicación con el modelo y su herramienta,
-leads.py arma las variables del motor y decide la escalación, analitica.py tiene las consultas de demanda y conversacion.py lo que queda del manejo de conversaciones y
-mensajes. En la capa de persistencia encuentras todos los queries y la comunicación de la aplicación con la base de datos (repositorio.py); y finalmente tenemos la capa de
-API con todos los endpoints de FastAPI (rutas.py) y los schemas de Pydantic (schemas.py). Aparte de las tres capas está app/motor/, que es el motor de lógica difusa
+leads.py arma las variables del motor y decide la escalación, analitica.py tiene las consultas de demanda, conversacion.py el manejo de conversaciones y mensajes,
+notificaciones.py la alerta por Telegram del canal web y voz.py la descarga y transcripción de las notas de voz. En la capa de persistencia encuentras todos los queries y la comunicación de la aplicación con la base de datos (repositorio.py); y finalmente tenemos la capa de
+API con todos los endpoints de FastAPI (rutas.py), los schemas de Pydantic (schemas.py) y la autenticación del backoffice (seguridad.py). Aparte de las tres capas está app/motor/, que es el motor de lógica difusa
 (pertenencia.py, inferencia.py, reglas.py y reglas.yaml) y no depende de nada de la aplicación. En esa misma carpeta app/ está excepciones.py, donde se definen las
 excepciones propias del dominio.
-Los endpoints expuestos son: /mensaje_entrante (recibe un mensaje de cualquier canal y ejecuta todo el flujo), /historial (mensajes de una conversación), /listar_asesores,
-/leads_por_asesor (los leads asignados a un asesor, ordenados por prioridad), /leads_sin_asignar (las solicitudes que el sistema atendió sin escalar), /evaluaciones_lead
-(el historial de cómo fue cambiando la prioridad de un lead), /cerrar_lead (registra el cierre como venta o no venta) y /demanda (el reporte del periodo).
+Los endpoints públicos son /chat (un mensaje del chat web, con el canal fijo en el servidor), /chat/historial (la conversación de ese cliente, identificado por el
+uuid que guarda su navegador), /entrar y /salir (abren y cierran la sesión del administrador).
+Los endpoints protegidos son /mensaje_entrante (recibe un mensaje de Telegram o del simulador y ejecuta todo el flujo), /listar_asesores, /leads_por_asesor (los leads
+asignados a un asesor, ordenados por prioridad), /leads_sin_asignar (las solicitudes que el sistema atendió sin escalar), /evaluaciones_lead (el historial de cómo fue
+cambiando la prioridad de un lead), /cerrar_lead (registra el cierre como venta o no venta), /demanda (el reporte del periodo), /conversaciones_simulador y
+/mensajes_simulador (la lista y el historial del simulador). Aceptan la cookie de sesión del administrador o, para n8n, autenticación básica.
 En la raíz de fastapi/ están models.py (definición de las tablas con SQLModel), database.py (conexión a la BD), seed.py (inyección del catálogo desde productos.json y de
 los asesores desde asesores.json), semilla_historia.py (historia de ejemplo para el reporte), main.py (punto de entrada de la aplicación), la carpeta prompts/ con el
-prompt del agente por fuera del código, la carpeta alembic/ con las migraciones, la carpeta tests/ con las pruebas y la carpeta static/ con el frontend (index.html para el
-chat, panel.html, reporte.html y sus CSS y JS separados por página).
+prompt del agente por fuera del código, la carpeta alembic/ con las migraciones, la carpeta tests/ con las pruebas y la carpeta static/ con el frontend (index.html y cliente.js para el
+chat del cliente, entrar.html para la entrada al backoffice, panel.html, reporte.html y simulador.html, cada uno con su CSS y su JS, y comun.css y comun.js con lo que
+comparten).
 docker-compose.yml: Configuración del Docker y comandos de arranque y montaje de la BD (creación del esquema, inyección de datos a la BD (seed.py), arranque de la aplicación).
 Los volúmenes y la red están declarados con nombre explícito para que no dependan del nombre de la carpeta.
 init.sql: Crea la base de datos exclusiva de n8n al levantar PostgreSQL por primera vez.
@@ -98,8 +109,9 @@ lean con escala. El reporte habla solo de lo que entra por mensajería: el siste
 
 ## Pruebas
 Las pruebas se corren dentro del contenedor de FastAPI, que es donde están fijadas las versiones, con "docker exec -w /app radar_fastapi python -m pytest".
-Cubren el motor completo (funciones de pertenencia, operadores, activación de reglas, agregación, carga y validación del YAML y la evaluación con su explicación) y las
-funciones puras de la capa de servicio (las cuatro variables, la validación de lo que devuelve el modelo y la decisión de escalación).
+Son 213. Cubren el motor completo (funciones de pertenencia, operadores, activación de reglas, agregación, carga y validación del YAML, la evaluación con su explicación y
+el comportamiento de las quince reglas reales de Tornalba), las funciones puras de la capa de servicio (las cuatro variables, la validación de lo que devuelve el modelo, la
+decisión de escalación, el texto de la alerta con el enlace de WhatsApp y la respuesta al cliente) y la firma de la sesión del administrador.
 Las pruebas del motor se escribieron antes que las funciones, con los valores calculados a mano.
 
 ## Estado del proyecto
@@ -119,6 +131,10 @@ lo que pidió queda guardado de forma estructurada con el precio y las existenci
 momento, y el panel muestra la bandeja ordenada por prioridad con la explicación de cada
 decisión.
 
+En la última etapa el sistema se preparó para salir del computador de desarrollo: la página del cliente quedó separada del
+backoffice, el chat web pide el celular para que el asesor lo contacte por WhatsApp, el backoffice quedó detrás de una sesión de administrador, el bot entiende notas de
+voz y se corrigieron dos reglas del motor que diluían la prioridad. El detalle de cada pieza está en PLAN.md (fases 8 y 9).
+
 Este desarrollo es el entregable del diplomado en Inteligencia Artificial Avanzada y
 Aplicada de la Universidad EIA para la Cámara de Comercio Aburrá Sur.