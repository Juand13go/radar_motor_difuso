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

### 1.5 Reglas en YAML
Problema: si las reglas viven en el código, cambiarlas exige tocar Python.
Solución: app/motor/reglas.yaml con variables, conjuntos, reglas y umbral, y app/motor/reglas.py que lo carga y valida (toda regla nombra variables y conjuntos que existen). Una configuración inválida lanza una excepción propia del dominio.
Terminada cuando: hay pruebas para un archivo válido y para cada tipo de error.

### 1.6 Resultado explicable
Problema: una prioridad sola no dice por qué.
Solución: la función pública del motor recibe las cuatro variables y devuelve la prioridad, el nivel y las reglas activadas con su grado, ordenadas de mayor a menor.
Terminada cuando: las pruebas pasan con dos o tres leads de ejemplo calculados a mano.

## Fase 2. Esquema y dominio (21 de septiembre)

### 2.1 Catálogo de Tornalba
Problema: el catálogo son colchones de Rambler y no tiene existencias.
Solución: migración que reforma productos (id_producto, referencia, nombre_producto, categoria, unidad, precio_unitario, existencias), el productos.json nuevo y el seed ajustado. Se reinicia el volumen de la base una vez, porque la data anterior es de otro dominio.
Terminada cuando: la base arranca con las 40 referencias de Tornalba.

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
Solución: se evalúa el motor, se guarda la evaluación y se actualiza el lead. Se escala si la prioridad supera el umbral, si el cliente pidió un asesor o si falló el modelo, solo si el lead no estaba escalado. Escalar asigna el asesor menos cargado, marca escalado_en y arma el texto de notificación para el asesor.
Terminada cuando: los tres motivos de escalación se prueban con conversaciones reales.

### 4.4 Endpoint único
Problema: la lógica del flujo está repartida entre nodos de n8n.
Solución: POST /mensaje_entrante, que orquesta un mensaje completo y devuelve la respuesta para el cliente y, si hubo escalación, la notificación para el asesor.
Terminada cuando: el endpoint responde correctamente desde /docs.

### 4.5 n8n reducido y retiro de rutas
Problema: el flujo de n8n y las rutas viejas quedan sobrando.
Solución: Juan Diego arma el flujo nuevo a mano en n8n (disparador de Telegram, llamada al endpoint, respuesta al cliente, y un condicional que envía la notificación al asesor) y lo exporta a n8n/. Se retiran las rutas que ya no se usan.
Terminada cuando: una conversación real por Telegram crea, evalúa y escala un lead.

## Fase 5. Panel (25 al 27 de septiembre)

### 5.1 Selector de asesores
Problema: para ver los leads hay que copiar y pegar un UUID.
Solución: una lista desplegable con los asesores que carga sus leads al elegir.

### 5.2 Bandeja priorizada
Problema: el asesor ve los leads sin orden ni contexto.
Solución: leads_por_asesor devuelve los leads ordenados por prioridad con nivel, monto e ítems, y el panel los muestra con el semáforo y la insignia.

### 5.3 Explicación de la prioridad
Problema: el asesor no sabe por qué un lead está arriba.
Solución: al abrir un lead se ven las reglas activadas con su grado y cómo fue cambiando la prioridad en cada mensaje.

### 5.4 Simulador de chat
Problema: si Telegram falla en la feria, no hay demo.
Solución: una sección del panel con un campo de texto que llama a /mensaje_entrante con canal simulador. Medio día como máximo.

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

## Fase 7. Cierre (29 de septiembre)

### 7.1 README
Actualizar el README al dominio de Tornalba, al flujo nuevo y al motor.

### 7.2 DECISIONES
Juan Diego escribe las entradas nuevas: la solicitud nace con el primer ítem, prioridad y escalación son decisiones separadas, la urgencia se mide en días a partir de una fecha, n8n queda como canal y Python orquesta, y la sección de trabajo futuro.

## Trabajo futuro

No se construye antes de la feria. Los datos que necesita ya quedan guardados.

Tiempo real de respuesta humana. El asesor responde por fuera del sistema, así que hoy no queda registro de cuándo contactó al cliente; hace falta que marque ese momento desde el panel. Con escalado_en y cerrado_en ya se puede medir el tiempo hasta el cierre.

Conversión por segmento: por ciudad, por categoría de producto y por asesor.

Productos que se piden juntos, a partir de los ítems de cada solicitud, para combos, compras y ubicación de mercancía.

Informe mensual de demanda invisible enviado al dueño del negocio.

Búsqueda semántica sobre el catálogo, calibración del motor con los cierres reales, otros canales como WhatsApp, autenticación del panel y despliegue en servidor.

## Limitaciones conocidas

Si un cliente manda dos mensajes casi al mismo tiempo, n8n puede procesarlos en paralelo y crear dos leads. Cada función del repositorio hace su propio commit, así que un fallo a mitad del flujo puede dejar datos parciales.