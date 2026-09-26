# Decisiones de diseño
Acá quedan escritas las decisiones importantes que tomé durante el desarrollo y la razón de cada una. La idea es poder explicar más adelante por qué el sistema quedó
así y no de otra forma, y no tener que reconstruirlo de memoria.

## La escalación se decide por la completitud del lead
Después de que el modelo decide si el lead debe escalarse, el código sobrescribe esa decisión: si falta la ciudad o faltan los productos de interés, no se escala.
La razón es evitar que los asesores reciban todo. Si se escalara cada mensaje donde el cliente se muestra molesto o pide hablar con alguien, la automatización no
aportaría nada y el asesor terminaría atendiendo lo mismo que antes; la compuerta garantiza que solo suba lead calificado.
El problema de esa regla es que está usando una pregunta para responder otra: mide si el lead está completo, pero lo que quiere decidir es si el caso necesita un humano.
Casi siempre coinciden, pero se separan justo en los casos caros, como un cliente con clara intención de compra que todavía no ha soltado sus datos.
La causa de fondo es que la salida es binaria, y siendo binaria solo se puede elegir entre dos reglas malas: escalar de más e inundar a los asesores, o escalar de menos
y perder clientes. Con una salida continua la completitud dejaría de ser una compuerta y pasaría a ser una variable más que baja la prioridad, sin bloquear nada.
Se deja tal cual en esta versión, porque es el comportamiento conocido y documentado del sistema.
En Radar esa compuerta desapareció. La completitud pasó a ser una de las cuatro variables del motor, que baja o sube la prioridad sin bloquear nada, y la escalación la decide la prioridad junto con otros dos motivos (ver "La prioridad y la escalación son decisiones separadas").

## Cuando el modelo falla, el lead se escala a un humano
El bloque except de comunicacion_agente devolvía escalar en False y un mensaje pidiéndole al cliente que volviera a escribir más tarde.
Eso no estaba filtrando un lead malo: estaba perdiendo un cliente porque la infraestructura falló, y sin que nadie se enterara. Es un problema distinto al de la decisión
anterior (ahí se trata de calificar el lead, acá de que el sistema no está funcionando) y por eso merece la respuesta contraria.
Ahora, ante un fallo del modelo, se escala. Como el schema de entrada de /crear_lead exige que los campos no vengan vacíos, los datos que no se alcanzaron a capturar
viajan como "Por confirmar", lo que de paso le indica al asesor qué es lo que le falta preguntarle al cliente.
La regla que queda es que cuando la IA falla el sistema no inventa ni abandona, sino que entrega el caso a una persona.
En Radar la regla se mantiene, pero ya no hacen falta los "Por confirmar": si no había solicitud abierta se crea una sin ítems, se escala con motivo fallo_tecnico y la alerta le pide al asesor que revise la conversación. Si ya había una solicitud abierta, sus ítems no se tocan, porque una extracción fallida no es confiable y borraría lo que el cliente ya había pedido.

## El modelo es configuración, no código
El sistema dejó de funcionar de un día para otro sin que yo hubiera tocado nada: Groq retiró el modelo llama-3.3-70b-versatile y todas las llamadas empezaron a devolver
404 model_not_found.
Por eso el identificador del modelo salió del código a la variable de entorno GROQ_MODEL. Cambiar de modelo ahora no implica editar un archivo, reconstruir la imagen ni
hacer un commit.
El modelo que quedó es openai/gpt-oss-20b. La tarea que hace el agente (leer un mensaje corto y devolver cuatro campos estructurados) no necesita un modelo grande, y la
latencia sí importa porque el cliente está esperando la respuesta en el chat.
La lección que dejó el incidente es que el proveedor del modelo es una dependencia externa que puede cambiar sin avisar, y que todo lo que determina el comportamiento del
agente (el modelo, el prompt, la definición de las herramientas) debería poder cambiarse sin desplegar.

## No todos los fallos son iguales
Haciendo varias peticiones seguidas, el proveedor respondió con un límite de tasa. Esa excepción caía en el mismo except que atrapa cualquier otro error, así que el
sistema reaccionó como si el fallo fuera permanente.
Pero un límite de tasa y un modelo retirado no son lo mismo. El primero es transitorio y lo correcto es reintentar; el segundo es permanente y lo correcto es escalar.
Atrapar los dos con el mismo except obliga a elegir una sola respuesta que necesariamente está mal para uno de los dos casos.
La solución fue que los fallos transitorios se resuelvan antes de llegar al except, usando los reintentos con espera exponencial del propio cliente (max_retries=4) y un
timeout para no dejar al cliente esperando indefinidamente. Así el except recupera su significado: si se ejecuta, el fallo es real y corresponde escalar.
Y hay algo de producto ahí también: un límite de peticiones por minuto es un acuerdo entre el sistema y su proveedor. El cliente que está escribiendo por Telegram no
tiene por qué enterarse de eso, y absorberlo es responsabilidad del sistema.

## Sin fine-tuning, porque el problema es de conocimiento y no de estilo
No se entrena ni se ajusta ningún modelo. Lo que el agente necesita es conocer el catálogo, no cambiar su forma de escribir, y para eso lo correcto es darle acceso a la
información, no reentrenarlo. Hacer fine-tuning habría sido más caro y habría resuelto el problema equivocado.
Hoy el catálogo completo se arma como texto y se inyecta dentro del prompt del sistema en cada mensaje. Esto funciona bien con un catálogo pequeño, pero con cientos de
referencias el costo por mensaje crece y se llega al límite de contexto; la salida a eso sería una búsqueda semántica sobre el catálogo.

## El agente responde solamente sobre su dominio
El agente no conversa de temas ajenos al negocio. Un asistente comercial que responde de cualquier cosa es imposible de acotar y de evaluar, y además abre la puerta a
que diga cosas que la empresa no quiere decir.
La restricción está diseñada como parte del producto y no como un rechazo: ante una pregunta que se sale del dominio, el agente lo reconoce, lo acota y ofrece el
contacto con un asesor.

## El sistema registra el resultado de cada decisión
Desde el panel, el asesor cierra cada lead como venta o no venta.
Esto es lo que amarra cada decisión que tomó el sistema con lo que pasó de verdad con ese cliente. Sin ese registro no hay manera de saber si las decisiones automáticas
estaban bien tomadas, y el sistema termina generando su propio conjunto de datos en vez de depender de datos externos.

## El backend es síncrono y la concurrencia se resuelve en la base de datos
Los endpoints de FastAPI están declarados como funciones normales y no como async. FastAPI corre ese tipo de funciones en un grupo de hilos, así que varios mensajes que llegan al mismo tiempo se atienden en paralelo sin que uno bloquee a los demás.
Casi todo el tiempo de cada mensaje se va en la llamada al modelo (uno o dos segundos), y al volumen de conversaciones que recibe una distribuidora por Telegram los hilos alcanzan de sobra.
Pasar a async no es cambiar def por async def: exige cambiar el driver de PostgreSQL, las sesiones, cada función del repositorio y el cliente del modelo. Y hacerlo a medias es peor que no hacerlo, porque una función async que llama algo síncrono bloquea el servidor completo mientras espera. Por eso no se hizo.
El motor difuso tampoco ganaría nada, porque es cálculo puro sin esperas de red ni de disco, que es lo único que async acelera.
Lo que sí había que resolver es otro problema que suele confundirse con este. Si un cliente manda dos mensajes casi al mismo tiempo, las dos solicitudes pueden buscar el lead abierto, no encontrarlo y crear cada una el suyo. Eso es una condición de carrera y async no la evita, porque con async las solicitudes también se intercalan.
La solución quedó en PostgreSQL: un índice único parcial sobre id_conversacion para los leads en estado en_proceso. Si la segunda inserción choca con el índice, se deshace y se continúa con el lead que creó el primer mensaje.
Así, la regla de un lead abierto por conversación no depende de que el código esté bien escrito: la garantiza la base de datos.

## La solicitud nace con el primer producto, se escale o no
En la versión clásica el lead solo existía si se escalaba, así que todo lo que el sistema atendía sin pasarlo a un asesor desaparecía sin dejar rastro. No había manera de saber cuántas solicitudes llegaban ni qué pedían.
Ahora la solicitud se crea en cuanto el cliente menciona el primer producto, y cada mensaje siguiente la actualiza: los ítems se reemplazan por la lista completa y actual que devuelve el agente (no por los cambios), guardando el precio y las existencias de ese momento. Sin productos y sin solicitud abierta no se crea nada, para no llenar la base de saludos.
Una conversación tiene como máximo una solicitud abierta, y eso lo garantiza la base de datos con un índice único parcial (ver la entrada sobre el backend síncrono).
Esa decisión es la que hace posible el reporte de demanda: lo que no se escala también cuenta.

## La prioridad y la escalación son decisiones separadas
La prioridad responde en qué orden hay que atender; la escalación responde si hay que meter a una persona ya. Toda solicitud tiene prioridad y aparece ordenada en la bandeja, pero solo algunas se escalan.
Se escala por uno de tres motivos, revisados en este orden: fallo_tecnico (el modelo falló y no hay datos para calcular nada), solicitud_cliente (el cliente pidió hablar con una persona, sin importar la prioridad) y motor (la prioridad alcanza el umbral, que hoy es 50 y vive en reglas.yaml). Una solicitud que ya se escaló no vuelve a notificar aunque su prioridad suba; eso se ve en el panel.
El agente no decide nada de esto. Solo extrae qué pidió el cliente, en qué cantidad, para cuándo y desde dónde, y si pidió hablar con alguien. Así la decisión es determinística y se puede explicar regla por regla.

## La urgencia se mide en días a partir de una fecha
Al modelo no se le pide que califique qué tan urgente es una solicitud, se le pide que extraiga la fecha en que el cliente necesita los productos. Una fecha se puede verificar y una etiqueta como "urgente" no.
El plazo en días lo calcula Python restando la fecha de hoy a esa fecha. El prompt fija las equivalencias de las expresiones comunes (hoy, ya o lo antes posible es hoy; esta semana es el viernes de esta semana) para que el modelo no las interprete distinto cada vez, y si el cliente no dice ninguna fecha no se inventa ninguna: el plazo queda vacío y las reglas que dependen de él no se activan.
La fecha se guarda en la solicitud, así que el plazo se recalcula en cada mensaje aunque el cliente no la repita.

## n8n queda como canal y Python orquesta
En la versión clásica la lógica del flujo estaba repartida entre trece nodos de n8n que llamaban a siete rutas distintas. Probarla, versionarla o explicarla era difícil, porque vivía en una interfaz gráfica.
Ahora n8n tiene cinco nodos: recibe el mensaje de Telegram, llama a /mensaje_entrante, le responde al cliente y, si hubo escalación, le manda la alerta al asesor. Toda la lógica está en Python, en una sola función de servicio que se puede leer de arriba abajo y probar.
El canal web ni siquiera pasa por n8n: llama directo a FastAPI, y por eso en ese canal es FastAPI el que le escribe al asesor por Telegram.

## Las fechas se guardan en UTC y se interpretan en la hora de Colombia
Las marcas de tiempo (cuándo se creó un mensaje, cuándo se escaló o se cerró una solicitud) se guardan en UTC y con zona horaria, para que Postgres devuelva fechas comparables sin ambigüedad.
Pero el "hoy" del negocio es el de Colombia. Si el plazo se calculara con la fecha UTC, a partir de las siete de la noche el sistema creería que ya es mañana y un pedido "para hoy" saldría vencido. Por eso el plazo, el reporte de demanda y la fecha que ve el agente usan hoy_bogota().

## El cliente web se identifica con un uuid de su navegador
El chat web no tiene usuarios ni inicio de sesión para el cliente: pedir una cuenta para cotizar unos tornillos haría que nadie escribiera. El navegador genera un uuid la primera vez, lo guarda y lo manda con cada mensaje, y ese uuid es la llave de su conversación.
Como es lo único que da acceso a la conversación, se genera con el generador criptográfico del navegador (no se puede adivinar), viaja en el cuerpo de la petición y no en la URL (para que no quede escrito en los logs del servidor ni en el historial del navegador), y no se escribe en ningún log de la aplicación.
El canal web tiene sus propias rutas públicas (/chat y /chat/historial) con el canal fijo en el servidor. /mensaje_entrante, que recibe el canal desde afuera, quedó protegida, porque con ella cualquiera podría escribir en la conversación de otra persona.
La contracara es que si el cliente borra los datos de su navegador empieza una conversación nueva, y que cada navegador cuenta como un cliente distinto para la relación.

## El cliente web deja su celular y el asesor lo contacta por WhatsApp
Cuando una conversación web escalaba, el cliente leía que un asesor lo iba a contactar, pero el asesor solo tenía un uuid. La frase era falsa, el mismo tipo de error que ya se había corregido con el texto de la respuesta repetida.
Por eso el chat web pide un celular colombiano antes del primer mensaje, y el panel y la alerta al asesor muestran un enlace de WhatsApp que abre el chat con ese número.
Guardar un teléfono es tratar un dato personal, así que junto al campo va el texto de autorización de contacto (Ley 1581 de habeas data), y el teléfono solo se usa para eso.

## En el canal web, FastAPI le escribe directo a Telegram
Había tres opciones para avisarle al asesor cuando escala una conversación web: que FastAPI le escribiera directo a Telegram, que llamara a un segundo flujo de n8n por webhook, o dejarlo solo en el panel. Elegí la primera porque son pocas líneas con la librería estándar, no agrega dependencias y no abre otro webhook público que habría que proteger. El costo es que el token del bot queda en dos lugares, la credencial de n8n y el .env.
Dos reglas salieron de ahí. La primera, que el token nunca aparece en un log: la URL de la API de Telegram lo lleva adentro, así que ni la URL ni la petición se registran, y el token se valida antes de armar la URL para que un carácter raro no lo meta en el mensaje de un error. La segunda, que un fallo de Telegram nunca tumba la respuesta al cliente: la alerta es secundaria.

## El backoffice tiene un solo administrador y una sesión firmada
El único que usa el panel, el reporte y el simulador soy yo, así que no hay tabla de usuarios: el usuario y la clave viven en el .env y se comparan con secrets.compare_digest, que tarda lo mismo acierte o no.
Primero usé la autenticación básica de HTTP, pero el navegador muestra su propia ventana para pedir la clave y esa ventana no se puede diseñar. Por eso se agregó una página /entrar que, con la clave correcta, deja una cookie firmada con HMAC. La firma usa la clave del administrador como llave, así que nadie puede fabricar una cookie sin conocerla, y cambiar la clave cierra todas las sesiones. La cookie dura doce horas y no la puede leer el JavaScript de la página ni la mandan otros sitios.
n8n sigue entrando con autenticación básica, porque es un programa y no una persona. Las rutas están separadas en un router público y uno protegido, así que una ruta nueva queda protegida por estar en ese router y no por acordarse de ponerle la dependencia.

## Dos reglas del motor diluían la prioridad
La agregación Sugeno es un promedio ponderado, y eso tiene una consecuencia que no se ve hasta que se prueban casos concretos: una regla que se activa con una salida baja arrastra el promedio hacia abajo, aunque todas las demás digan que el caso es grave.
Eso pasaba con solicitud_urgente y cliente_recurrente, dos reglas de una sola condición que proponían media (45). Un pedido grande y urgente de un cliente nuevo sacaba 68,75, menos que el mismo pedido sin fecha (70); uno de un cliente recurrente sacaba 62,5; y un cliente nuevo nunca llegaba a crítica.
Se eliminaron las dos reglas. Con las quince que quedan, el pedido grande y urgente de un cliente nuevo saca 76,67 (crítica) y el de un cliente recurrente 80. Antes de borrar se escribieron pruebas con el reglas.yaml real que mostraban el problema fallando, y ahora dejan fijado cómo se comporta el motor con las reglas de Tornalba.
La lección es que en un promedio las reglas no suman: cada regla nueva también puede restar.

## Las notas de voz se transcriben antes de llegar al agente
En Colombia mucha gente le escribe a un negocio por nota de voz. El agente solo lee texto, así que la voz se convierte en texto antes de entrar al flujo: n8n manda el identificador del archivo, FastAPI lo descarga desde Telegram y lo transcribe con Whisper en Groq, y de ahí en adelante todo sigue igual que con un mensaje escrito.
El modelo de voz, igual que el del agente, está en una variable de entorno (GROQ_MODELO_VOZ). Transcribir una nota de voz de veinte segundos cuesta una fracción de peso.
Si la nota no se puede descargar o transcribir, el cliente recibe un texto fijo que le pide escribirla, sin llamar al agente ni guardar nada. Los audios de más de 5 MB no se procesan.

## Deuda técnica y limitaciones conocidas
La mayor parte de lo que estaba en esta lista en la versión clásica ya se resolvió: n8n está fijado en la versión 2.37.7, el prompt vive en prompts/agente.md, hay 213 pruebas automatizadas, lo que pide el cliente queda estructurado en items_solicitados, el asesor menos cargado sale de una sola consulta agrupada y el backoffice tiene autenticación. Lo que queda:
catalogo_a_texto consulta la base y arma el texto del catálogo en cada mensaje, cuando se podría cachear; con cientos de referencias habría que pasar a búsqueda semántica.
Cada función del repositorio hace su propio commit, así que un fallo a mitad del flujo puede dejar datos parciales.
Una alerta al asesor que falla no se reintenta: la solicitud queda escalada y solo se ve en el panel. La solución sería guardar si la alerta se envió y reintentar las pendientes.
Con audio en silencio o puro ruido, Whisper puede devolver frases que nadie dijo ("gracias por ver el video"), y esas frases llegan al agente como si el cliente las hubiera escrito.
El agente solo recibe los últimos diez mensajes de la conversación. Lo pedido no se pierde, porque el estado de la solicitud va aparte en el prompt, pero un detalle mencionado muy atrás sí.
Las existencias no se descuentan cuando una solicitud cierra en venta.
/chat es pública y cada mensaje cuesta una llamada al modelo. Está limitado a mil caracteres por mensaje, pero no hay un límite de mensajes por cliente; mientras tanto, la protección es el tope de gasto de la cuenta de Groq.
Los HTML del backoffice también se sirven desde /static sin clave. Salen vacíos, porque todos los datos vienen de la API y la API pide sesión.