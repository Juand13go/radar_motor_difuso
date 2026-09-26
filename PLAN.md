# Plan de construcción

Este archivo ordena el trabajo del motor de lógica difusa y de todo lo que se construye alrededor de él. Cada pieza tiene un identificador (por ejemplo 2.3), el problema que resuelve, la solución acordada y cuándo se considera terminada. Una pieza es un commit. Las instrucciones para Claude Code siempre nombran la pieza que se está trabajando, y no se adelanta trabajo de piezas siguientes.

La fecha límite es el 2 de octubre de 2026. Del 30 de septiembre en adelante no entra código nuevo.

## Fase 0. Preparación (16 y 17 de septiembre)

### 0.1 Limpieza y errores menores
Problema: hay código muerto (menos_cargado comentado, una línea comentada en seed.py), index.html repite dentro de un bloque style todo el contenido de style.css, poblar_asesores usa la variable existe sin definirla cuando un asesor llega sin id, el logging está en nivel ERROR y oculta todos los logs informativos, el mensaje de fallo técnico le pide al cliente que escriba más tarde mientras el sistema escala, y GROQ_MODEL falta en .env.example.
Solución: borrar el código muerto y el bloque style, definir existe antes del if, subir el logging a INFO, cambiar el texto de fallo por uno que diga que la solicitud pasó a un asesor, y agregar GROQ_MODEL al .env.example.
Terminada cuando: el sistema levanta igual que antes y el panel se ve igual sin el bloque style.

### 0.2 Infraestructura
Problema: la imagen de n8n está en latest y ya se actualizó sola; WEBHOOK_URL está deprecada; las variables N8N_BASIC_AUTH ya no hacen nada; el docker-compose.yml tiene un comentario por línea que no aporta.
Solución: fijar la versión exacta de n8n que está corriendo, usar N8N_WEBHOOK_URL tomando el mismo valor del .env, quitar las variables de basic auth y dejar solo los comentarios que explican una decisión.
Terminada cuando: docker compose up levanta sin el aviso de WEBHOOK_URL y el flujo de Telegram sigue respondiendo.

### 0.3 Base para las pruebas
Problema: no hay pruebas automatizadas ni forma de correrlas.
Solución: agregar pytest y pyyaml con versión fija a requirements.txt, crear fastapi/pytest.ini con pythonpath en la carpeta actual, y crear fastapi/tests/motor/.
Terminada cuando: pytest corre desde fastapi/ y reporta cero pruebas sin error.

## Fase 1. Motor de lógica difusa (17 al 20 de septiembre)

El motor vive en app/motor/ y es código puro. Antes de cada pieza, Juan Diego calcula a mano los valores esperados y esos valores son las pruebas.

### 1.1 Funciones de pertenencia
Problema: el motor necesita convertir un valor numérico en un grado de pertenencia entre 0 y 1.
Solución: funciones triangular y trapezoidal en app/motor/pertenencia.py, cubriendo los bordes (valores fuera del soporte, el pico, y los hombros abiertos a izquierda y derecha).
Terminada cuando: las pruebas de pertenencia pasan con los valores calculados a mano.

### 1.2 Operadores y activación de reglas
Problema: una regla combina varias condiciones y hay que saber con qué grado se cumple.
Solución: el operador Y como mínimo, y una función que recibe los grados de las condiciones de una regla y devuelve su grado de activación, en app/motor/inferencia.py.
Terminada cuando: las pruebas de activación pasan, incluida una regla con una sola condición.

### 1.3 Agregación Sugeno y niveles
Problema: varias reglas activas proponen salidas distintas y hay que llegar a una sola prioridad.
Solución: promedio ponderado de las salidas constantes de las reglas por su grado de activación. Si ninguna regla se activa, el motor no divide por cero (el comportamiento se define en la instrucción). La prioridad continua se mapea a baja, media, alta o critica.
Terminada cuando: las pruebas pasan, incluido el caso sin reglas activas.

### 1.4 Diseño de variables y reglas
Problema: las funciones existen pero falta el contenido de negocio.
Solución: sesión en el chat, sin código. Se definen los universos y conjuntos de monto estimado, relación con el cliente, completitud y plazo en días (incluido qué pasa cuando no hay fecha), las salidas de cada nivel, entre quince y veinte reglas, y el umbral de escalación.
Terminada cuando: el contenido está escrito y aprobado para pasarlo a YAML.
Con la escala decidida, se agrega a la validación de la 1.5 que los valores de salidas, cortes y umbral_escalacion sean números dentro de esa escala.

### 1.5 Reglas en YAML
Problema: si las reglas viven en el código, cambiarlas exige tocar Python.
Solución: app/motor/reglas.yaml con variables, conjuntos, reglas y umbral, y app/motor/reglas.py que lo carga y valida (toda regla nombra variables y conjuntos que existen). Una configuración inválida lanza una excepción propia del dominio.
Terminada cuando: hay pruebas para un archivo válido y para cada tipo de error.
Cada variable declara su universo con un mínimo y un máximo.

### 1.6 Resultado explicable
Problema: una prioridad sola no dice por qué.
Solución: la función pública del motor recibe las cuatro variables y devuelve la prioridad, el nivel y las reglas activadas con su grado, ordenadas de mayor a menor.
Terminada cuando: las pruebas pasan con dos o tres leads de ejemplo calculados a mano.
Antes de calcular pertenencias, cada entrada se recorta a su universo, de modo que un plazo vencido cuenta como cero días y un monto por encima del máximo cuenta como el máximo.

## Fase 2. Esquema y dominio (21 de septiembre)

### 2.1 Catálogo de Tornalba
Problema: el catálogo son colchones de Rambler y no tiene existencias.
Solución: migración que reforma productos (id_producto, referencia, nombre_producto, categoria, unidad, precio_unitario, existencias), el productos.json nuevo y el seed ajustado. Se reinicia el volumen de la base una vez, porque la data anterior es de otro dominio.
Terminada cuando: la base arranca con las 40 referencias de Tornalba.
Hecha, dentro del commit de la fase 0.

### 2.2 Leads por agregado
Problema: el lead solo guarda texto libre y no tiene cómo registrar prioridad, escalación ni tiempos.
Solución: agregar monto_estimado, fecha_requerida, prioridad, nivel_prioridad, escalado, motivo_escalacion, escalado_en y cerrado_en; ciudad y productos_interes pasan a nullable. cerrar_lead empieza a registrar cerrado_en.
Terminada cuando: la migración corre sobre la base y cerrar un lead guarda la fecha.
Se agrega un índice único parcial sobre id_conversacion para las filas con estado_lead en_proceso, de modo que la base de datos impida dos leads abiertos para la misma conversación.

### 2.3 Ítems solicitados
Problema: lo que pidió el cliente no queda estructurado, así que la demanda no se puede contar.
Solución: tabla items_solicitados con id_item, id_lead, id_producto (nullable, nulo significa fuera de catálogo), descripcion, cantidad, precio_al_momento y existencias_al_momento.
Terminada cuando: la migración corre y el repositorio puede reemplazar los ítems de un lead.

### 2.4 Evaluaciones del motor
Problema: sin historial no se puede explicar cómo cambió la prioridad.
Solución: tabla evaluaciones_motor con id_evaluacion, id_lead, id_mensaje, las cuatro variables, prioridad, nivel_prioridad, reglas_activadas y creado_en.
Terminada cuando: la migración corre y el repositorio puede guardar y listar evaluaciones de un lead.

## Fase 3. Agente (22 de septiembre)

### 3.1 Prompt fuera del código
Problema: el prompt vive dentro de conversacion.py, habla de Rambler y no se puede revisar por separado.
Solución: fastapi/prompts/agente.md con el dominio de Tornalba, la fecha actual como variable, el estado actual de la solicitud abierta, la instrucción de preguntar la fecha cuando hay ítems y no hay plazo, y equivalencias fijas para expresiones como hoy, ya o esta semana.
Terminada cuando: agente.py carga el prompt desde el archivo.

### 3.2 Nueva herramienta y validación
Problema: la herramienta actual devuelve campos pensados para la escalación binaria y deja que el modelo decida.
Solución: comunicacion_agente pasa a app/servicio/agente.py con una herramienta que devuelve respuesta_cliente, items (id_producto o nulo, descripcion, cantidad), ciudad, fecha_requerida y solicita_asesor. El modelo devuelve siempre la lista completa y actual de ítems, no los cambios. Python valida que cada id_producto exista (si no existe, queda nulo) y calcula plazo_dias a partir de la fecha.
Terminada cuando: diez frases de prueba devuelven la extracción esperada.

## Fase 4. Orquestación en Python (23 y 24 de septiembre)

### 4.1 Variables del motor
Problema: el motor recibe números, y hay que calcularlos a partir de los datos.
Solución: funciones puras en app/servicio/leads.py que calculan monto estimado, relación con el cliente, completitud y plazo, con pruebas. Los datos los trae el repositorio y se les pasan ya cargados.
Terminada cuando: las pruebas de las cuatro variables pasan.

### 4.2 Ciclo de la solicitud
Problema: hoy se crea un lead nuevo cada vez que el modelo decide escalar.
Solución: una conversación tiene máximo un lead en_proceso. Si llegan ítems y no hay lead abierto se crea; si hay lead abierto se actualiza y sus ítems se reemplazan con la foto de precio y existencias. Sin ítems y sin lead no se crea nada.
Terminada cuando: una conversación de varios mensajes deja un solo lead con los ítems del último mensaje.
Si la creación del lead falla por el índice único, se hace rollback, se busca el lead abierto existente y se continúa con ese.

### 4.3 Evaluación y escalación
Problema: la decisión de escalar tiene que ser del motor y quedar registrada con su motivo.
Solución: se evalúa el motor, se guarda la evaluación y se actualiza el lead. Se escala si la prioridad alcanza o supera el umbral, si el cliente pidió un asesor o si falló el modelo, solo si el lead no estaba escalado. Escalar asigna el asesor menos cargado, marca escalado_en y arma el texto de notificación para el asesor.
Terminada cuando: los tres motivos de escalación se prueban con conversaciones reales.
Los leads que el motor deja en verde y nunca se escalan se cierran a mano desde el panel, porque el asesor puede cerrar cualquier lead y no solo los suyos. El cierre automático por inactividad queda como trabajo futuro.

### 4.4 Endpoint único
Problema: la lógica del flujo está repartida entre nodos de n8n.
Solución: POST /mensaje_entrante, que orquesta un mensaje completo y devuelve la respuesta para el cliente y, si hubo escalación, la notificación para el asesor.
Terminada cuando: el endpoint responde correctamente desde /docs.

### 4.5 n8n reducido y retiro de rutas
Problema: el flujo de n8n y las rutas viejas quedan sobrando.
Solución: Juan Diego arma el flujo nuevo a mano en n8n (disparador de Telegram, llamada al endpoint, respuesta al cliente, y un condicional que envía la notificación al asesor) y lo exporta a n8n/. Se retiran las rutas que ya no se usan.
Terminada cuando: una conversación real por Telegram crea, evalúa y escala un lead.

### 4.6 WhatsApp como segundo canal (opcional)
Problema: demostrar que el canal es intercambiable.
Solución: un disparador de WhatsApp en n8n que llama al mismo endpoint con canal whatsapp, usando el número de prueba de Meta, que es gratis y no exige verificación del negocio pero solo habla con cinco destinatarios cargados de antemano. Por ese límite no reemplaza a Telegram en la feria.
Solo se hace si la 4.5 cerró el 24 de septiembre. Si no, se descarta sin reemplazo.

## Fase 5. Panel (25 al 27 de septiembre)

### 5.1 Simulador de chat
Problema: hasta que el canal esté reconectado no hay forma de mostrar el sistema, y en la feria Telegram depende del túnel y del wifi.
Solución: una sección del panel con un campo de texto que llama a /mensaje_entrante con canal simulador. Medio día como máximo.

### 5.2 Selector de asesores
Problema: para ver los leads hay que copiar y pegar un UUID.
Solución: una lista desplegable con los asesores que carga sus leads al elegir.

### 5.3 Bandeja priorizada
Problema: el asesor ve los leads sin orden ni contexto.
Solución: leads_por_asesor devuelve los leads ordenados por prioridad con nivel, monto e ítems, y el panel los muestra con el semáforo y la insignia.

### 5.4 Explicación de la prioridad
Problema: el asesor no sabe por qué un lead está arriba.
Solución: al abrir un lead se ven las reglas activadas con su grado y cómo fue cambiando la prioridad en cada mensaje.

### 5.5 Rutas del historial del simulador
Problema: el simulador generaba un identificador al azar en cada carga, así que al recargar la página se perdía la conversación, y /historial solo devolvía los últimos diez mensajes porque es la misma función que arma el contexto del agente.
Solución: /conversaciones_simulador lista las conversaciones del canal simulador con su último mensaje (una sola consulta con una subconsulta LATERAL) y /mensajes_simulador devuelve el historial completo de una de ellas. El canal queda fijo en el servicio, para que las conversaciones de Telegram no salgan por estas rutas.

### 5.6 Simulador con lista de conversaciones
Problema: sin una lista no se puede volver a una conversación anterior.
Solución: el simulador pasa a dos columnas, la lista de conversaciones a la izquierda y el chat a la derecha, con un botón de conversación nueva. Mientras se espera una respuesta o se cargan mensajes, la lista queda bloqueada para que una respuesta no termine pintada en otra conversación.

## Fase 6. Demanda invisible (28 de septiembre)

### 6.1 Semilla de historia
Problema: una pantalla de demanda vacía no demuestra nada.
Solución: un script que carga unas semanas de solicitudes cerradas con ítems cubiertos, sin existencias y fuera de catálogo.

### 6.2 Consultas de demanda
Problema: el distribuidor sabe qué vendió pero no qué le pidieron y no tenía.
Solución: tres consultas en app/servicio/analitica.py y el repositorio. Demanda no cubierta por existencias (veces, unidades y monto estimado). Demanda fuera de catálogo (veces y unidades, agrupada por descripción; no tiene monto porque no hay precio). Sobrestock (existencias altas sin solicitudes en el periodo).

### 6.3 Pantalla de demanda
Problema: las consultas no sirven si nadie las ve.
Solución: una sección del panel con las tres listas.
Arriba de las tres listas va una franja de contexto con las solicitudes recibidas, cuántas se escalaron, cuántas cerraron en venta y el monto total pedido, para que los montos no cubiertos se lean con escala. El encabezado dice de qué habla el reporte (solicitudes recibidas por mensajería en el periodo), porque el sistema no ve las ventas de mostrador ni las compras a proveedores.

### 6.4 Gráficos e impresión
Problema: tres listas de números no se leen de un vistazo, y el reporte mensual tiene que poder entregarse.
Solución: barras horizontales dibujadas como SVG generado en JavaScript, sin librerías ni CDN, y una hoja de estilos de impresión que esconde la navegación para exportar a PDF desde el navegador. Se descarta si el calendario aprieta.

## Fase 7. Cierre (29 de septiembre)

### 7.1 README
Actualizar el README al dominio de Tornalba, al flujo nuevo y al motor.

### 7.2 DECISIONES
Juan Diego escribe las entradas nuevas: la solicitud nace con el primer ítem, prioridad y escalación son decisiones separadas, la urgencia se mide en días a partir de una fecha, n8n queda como canal y Python orquesta, las fechas se guardan en UTC y se interpretan en la zona de Colombia, y la sección de trabajo futuro.
También se reescribe la sección de deuda técnica conocida, que hoy describe un estado que ya cambió: n8n ya no está en latest, el prompt ya no vive en conversacion.py, ya hay pruebas automatizadas y productos_interes ya no es el único registro de lo que pidió el cliente.

## Fase 8. Separación del cliente y el backoffice (25 y 26 de septiembre)

El sistema se va a desplegar en un servidor y los clientes van a entrar desde el celular. Hasta aquí todo vivía en páginas abiertas: cualquiera con la URL veía el panel, el reporte y las conversaciones de los demás. Esta fase separa lo que ve el cliente (solo su chat) de lo que ve el administrador (el backoffice).

### 8.1 Canal web
Problema: la única entrada era /mensaje_entrante, que recibe el canal desde afuera y permitiría escribir en conversaciones ajenas.
Solución: rutas públicas propias, POST /chat y POST /chat/historial, con el canal web fijo en el servidor. El identificador del cliente es un uuid que genera su navegador y llega en el cuerpo, nunca en la URL, para que no quede escrito en los logs. La ruta pública nunca devuelve la notificación del asesor, porque trae datos internos.

### 8.2 Simulador en el backoffice
Problema: el simulador con lista de conversaciones es una herramienta del administrador, no la página del cliente.
Solución: se muda a /simulador con la identidad de Radar. index.html se deja igual hasta la 8.3 para que la raíz nunca quede rota entre commits.

### 8.3 Página del cliente
Problema: el cliente necesita un chat simple, pensado para el celular, que le muestre solo su conversación.
Solución: index.html queda con la identidad de Tornalba, sin navegación al backoffice y con una sola columna. El identificador se guarda en localStorage (con respaldo en memoria si el navegador no lo permite) y se genera con crypto.randomUUID o, por http, con crypto.getRandomValues.

### 8.4 Celular del cliente web
Problema: un cliente web no tenía cómo ser contactado. El asesor solo veía un uuid, pero al escalar el cliente recibía "lo va a contactar en breve".
Solución: columna telefono en conversaciones (8.4a) y teléfono opcional en /chat conectado hasta la conversación (8.4b). Solo celulares colombianos de diez dígitos que empiezan por 3. Se escribe al crear la conversación y no se reemplaza después.

### 8.5 Campo de celular y autorización
Problema: el teléfono tenía que pedirse en la página y volverse obligatorio sin romper a los clientes que ya habían chateado.
Solución: el campo aparece mientras el navegador no tenga un teléfono guardado, haya historial o no. El navegador lo limpia (espacios, guiones, paréntesis, el más y el 57) antes de enviarlo. Junto al campo va el texto de autorización de contacto por WhatsApp. En el mismo commit el teléfono pasa a ser obligatorio en /chat.

### 8.6 WhatsApp en el panel y en la alerta
Problema: el asesor no veía el canal ni el teléfono.
Solución: enlace_whatsapp arma https://wa.me/57 más el número. El panel muestra el canal, el teléfono en lugar del uuid y el botón Escribir por WhatsApp, y la alerta al asesor abre con el celular y trae el enlace.

### 8.7 Alerta por Telegram para el canal web
Problema: el chat web no pasa por n8n, así que cuando una conversación web escalaba nadie se enteraba por Telegram.
Solución: FastAPI le escribe directo a Telegram con sendMessage y el token del bot en TELEGRAM_BOT_TOKEN, usando urllib de la librería estándar. El token nunca aparece en los logs y un fallo de Telegram nunca tumba la respuesta al cliente.

### 8.8 Backoffice protegido
Problema: cualquiera podía abrir el panel, el reporte, la documentación y todas las rutas internas.
Solución: autenticación básica con usuario y clave en ADMIN_USUARIO y ADMIN_CLAVE, comparados con secrets.compare_digest. Las rutas se separan en router_publico (/chat, /chat/historial) y router_admin (todo lo demás), así que una ruta nueva queda protegida por estar en el router y no por acordarse de ponerle la dependencia. n8n llama a /mensaje_entrante con una credencial Basic.

### 8.9 Despliegue
Problema: el sistema solo corre mientras el computador de Juan Diego está encendido, y la URL del túnel cambia en cada reinicio.
Solución: servidor en Hetzner, dominio en Cloudflare y un túnel con nombre fijo. docker-compose de producción sin recarga automática, sin montar el código y sin exponer el puerto 8000.
Pendiente del pago del servidor y del dominio.

### 8.10 Sesión del administrador
Problema: la ventana de usuario y clave que dibuja el navegador con la autenticación básica no se puede estilizar y da impresión de producto sin terminar.
Solución: una sesión con cookie firmada con HMAC-SHA256 (usando ADMIN_CLAVE como llave) que dura doce horas, es HttpOnly, SameSite=Strict y Secure (8.10a); la página /entrar con la identidad de Radar (8.10b); y el botón Salir, más la vuelta a /entrar cuando la sesión vence con una página abierta (8.10c). La API dejó de mandar WWW-Authenticate para que el navegador no vuelva a mostrar su ventana. n8n sigue entrando con Basic.

## Fase 9. Ajustes antes de la feria (26 de septiembre)

### 9.1 Reglas que diluían la prioridad
Problema: la agregación Sugeno es un promedio, y las reglas de una sola condición solicitud_urgente y cliente_recurrente (las dos con salida media) metían un 45 justo donde la prioridad tenía que subir. Un pedido grande y urgente de un cliente nuevo sacaba 68,75, menos que uno grande sin fecha (70), y un cliente nuevo nunca llegaba a crítica.
Solución: se eliminaron esas dos reglas y quedaron quince. Grande, urgente y de cliente nuevo pasa a 76,67 (crítica). Se agregaron pruebas con el reglas.yaml real, que antes no tenía ninguna.

### 9.2 Mensajes sin texto y frase duplicada
Problema: un audio, un sticker o una foto por Telegram llegaba sin texto, /mensaje_entrante respondía 422 y el cliente se quedaba sin respuesta. Además, cuando fallaba el modelo el cliente leía dos veces que un asesor lo iba a contactar.
Solución: el texto pasa a ser opcional en /mensaje_entrante y un mensaje sin texto recibe una respuesta fija sin llamar al agente. Con fallo técnico la respuesta es solo el texto de fallo.

### 9.3 Limpieza
Retiro de código sin uso (crear_lead, actualizar_estado_conversacion y la ruta /historial), argumentos por nombre y anotaciones de tipo que habían quedado desactualizadas (9.3a). En el frontend, chat.js y chat.css pasan a llamarse simulador.js y simulador.css, y Enter avanza entre los campos del chat del cliente (9.3b).

### 9.4 Notas de voz por Telegram
Problema: en Colombia la gente escribe mucho por nota de voz, y el sistema solo entendía texto.
Solución: n8n manda el file_id de la nota de voz. FastAPI la descarga desde Telegram (máximo 5 MB), la transcribe con Whisper en Groq (modelo en GROQ_MODELO_VOZ) y sigue el flujo como si el cliente la hubiera escrito. Si no se puede transcribir, el cliente recibe un texto fijo que le pide escribirla.

## Trabajo futuro

No se construye antes de la feria. Los datos que necesita ya quedan guardados.

Tiempo real de respuesta humana. El asesor responde por fuera del sistema, así que hoy no queda registro de cuándo contactó al cliente; hace falta que marque ese momento desde el panel. Con escalado_en y cerrado_en ya se puede medir el tiempo hasta el cierre.

Cierre automático de los leads que quedan abiertos sin actividad.

Conversión por segmento: por ciudad, por categoría de producto y por asesor.

Productos que se piden juntos, a partir de los ítems de cada solicitud, para combos, compras y ubicación de mercancía.

Informe mensual de demanda invisible enviado al dueño del negocio.

Una herramienta de exploración de datos conectada a la base, para que el cliente arme sus propios reportes.

Entorno de desarrollo local con las dependencias instaladas fuera de Docker, para correr las pruebas sin levantar los contenedores.

Búsqueda semántica sobre el catálogo, calibración del motor con los cierres reales y otros canales como WhatsApp.

Reintento de las alertas al asesor que fallan: hoy el lead queda escalado aunque Telegram no haya recibido la alerta.

Identificar al cliente por su NIT o su teléfono y no por el canal, para que la misma persona por Telegram y por la web sea un solo cliente y su historial de compras cuente para la relación.

Descontar las existencias cuando un lead cierra en venta.

Notas de voz en el chat web y un filtro para las frases que Whisper inventa con audio en silencio.

## Limitaciones conocidas

Cada función del repositorio hace su propio commit, así que un fallo a mitad del flujo puede dejar datos parciales.

Una alerta al asesor que falla (Telegram caído, token mal cargado) no se reintenta. El lead queda escalado y solo se ve en el panel.

Con audio en silencio o puro ruido, Whisper puede devolver frases que nadie dijo, y esas frases llegan al agente como si el cliente las hubiera escrito.

La relación con el cliente se cuenta por conversación, así que en la web cada navegador es un cliente nuevo.

Los archivos HTML del backoffice también se sirven desde /static sin clave. Salen vacíos, porque todos los datos vienen de la API y la API pide sesión.

Las pruebas solo corren dentro del contenedor de FastAPI. El Python del sistema es 3.14 y no trae pip ni ensurepip, y las versiones del proyecto están fijadas contra la 3.11 de la imagen.