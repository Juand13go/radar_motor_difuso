# TRIAJE LEADS COMERCIALES/RADAR
Este sistema plantea la automatización de la atención y la clasificación de las solicitudes comerciales que le entran a una empresa por sus canales de mensajería.
El flujo inicia con un mensaje del cliente por alguno de los canales de la empresa (actualmente Telegram), n8n lo recibe y llama a un único endpoint de FastAPI, que es
donde vive toda la lógica. Ahí se guarda la conversación, el agente de IA lee el mensaje con el catálogo al frente y extrae lo que el cliente está pidiendo (los productos
con su cantidad, la ciudad y para cuándo lo necesita), y con esos datos el sistema arma la solicitud, la valora contra el catálogo y la pasa por un motor de lógica difusa
que calcula su prioridad. Si esa prioridad alcanza el umbral, si el cliente pidió hablar con una persona o si el modelo falló, la solicitud se escala: se le asigna el
asesor menos cargado y se le avisa por Telegram. Al cliente se le responde por el mismo canal por el que escribió. Cuando el asesor termina de atender el lead lo cierra
desde el panel como venta o no venta, y ese resultado también queda guardado, de manera que cada decisión que tomó el sistema queda ligada a lo que pasó realmente con ese
cliente.
La diferencia con la versión anterior es dónde se decide. Antes el modelo decía si el lead debía escalarse; ahora el modelo solo extrae información y la decisión la toma
el motor, que es determinístico y devuelve, junto con la prioridad, las reglas que se activaron y con qué grado.

## El motor de lógica difusa
El motor recibe cuatro variables y devuelve una prioridad continua de 0 a 100, su nivel (baja, media, alta o crítica) y las reglas que se activaron.
El monto estimado sale de cruzar lo que el cliente pidió contra el catálogo por su cantidad, así que es un número de la base de datos y no una estimación del modelo.
La relación con el cliente sale de cuántas solicitudes anteriores de esa misma conversación cerraron en venta.
La completitud mide cuántos datos llegaron (si hay productos del catálogo, si tienen cantidad y si se conoce la ciudad).
El plazo en días se calcula en Python restando la fecha que pidió el cliente contra la fecha de hoy en Colombia. Al modelo no se le pide que califique la urgencia, se le
pide que extraiga una fecha, porque una fecha se puede verificar y una etiqueta no.
Las funciones de pertenencia, los conjuntos de cada variable, las salidas, los cortes entre niveles, el umbral de escalación y las diecisiete reglas viven en
app/motor/reglas.yaml, fuera del código. Cambiar qué es un monto alto para otra empresa no exige tocar Python ni reconstruir la imagen.
La inferencia es Sugeno de orden cero: cada regla activa aporta su salida ponderada por su grado de activación, y la prioridad es el promedio ponderado de todas. Antes de
calcular las pertenencias, cada entrada se recorta a su universo, de modo que un plazo vencido cuenta como cero días y un monto por encima del máximo cuenta como el máximo.
El motor es código puro: no importa FastAPI, ni la base de datos, ni el cliente del modelo. Recibe números y devuelve un resultado, y por eso se puede probar solo.

## Arquitectura
PostgreSQL BD (Sistema gestor de datos, almacena conversaciones, mensajes, leads, ítems solicitados, evaluaciones del motor, asesores y el catálogo de productos)
n8n (Automatización de flujos; acá queda solo como canal, recibe el mensaje de Telegram y llama al endpoint)
FastAPI - Python (Framework - Usado para la lógica del proyecto y para orquestar todo el flujo de un mensaje)
Motor de lógica difusa propio (Python puro, con sus reglas en un archivo YAML)
Groq API (LLM, agente IA - con tool calling para extraer los datos de la solicitud; el modelo se define en la variable de entorno GROQ_MODEL y no está escrito dentro del código)
Docker (Herramienta esencial para mantenibilidad, una arquitectura limpia y para fácil acceso al proyecto en cualquier máquina)
Migraciones con Alembic
Schemas de Pydantic (Validación de los datos que entran y salen)
SQLModel (ORM - Definición de las tablas y comunicación con PostgreSQL)
Cloudfared (Proxy inverso para exponer n8n por HTTPS y recibir el webhook de Telegram)
Frontend (HTML, CSS y JS sin frameworks) con tres páginas: el chat del cliente, el panel de los asesores y el reporte de demanda
pytest (Pruebas automatizadas del motor y de la lógica de servicio)

## Requisitos
El sistema corre en Docker, esta tecnología se encarga de que el sistema funcione sin tener que instalar nada; las dependencias del proyecto están en el
requirements.txt.
Necesitas: Docker y Docker Compose, un bot de Telegram (creado con @BotFather) y una API Key de Groq.

## Configuración
En la raíz del proyecto está el archivo .env.example con todas las variables que necesita el sistema, sin valores. Se copia como .env y se completa:
POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD (PostgreSQL)
N8N_DB, N8N_USER, N8N_PASSWORD (Base de datos y credenciales de n8n)
WEBHOOK_URL (URL HTTPS que entrega cloudfare)
GROQ_API_KEY (Agente IA)
GROQ_MODEL (Modelo que usa el agente; está por fuera del código para poder cambiarlo sin tocar nada ni reconstruir la imagen)
TELEGRAM_BOT_TOKEN (Token del bot)
COMPOSE_PROJECT_NAME (Nombre del proyecto en Docker; fija los nombres de los volúmenes para que renombrar o mover la carpeta no rompa la persistencia de la BD)

El .env nunca se sube al repositorio, por eso existe el .env.example: documenta qué hace falta sin exponer los valores.
El token del bot de Telegram se configura como credencial dentro de n8n.

## Cómo levantar el entorno
Clonar el repositorio
Crear el .env a partir del .env.example (ver sección de configuración)
Para el proxy inverso con cloudfare: "cloudflared tunnel --url http://localhost:5678" (Recibirás una URL HTTPS como esta: "https://vitamin-barrier-odds-performing.trycloudflare.com", colócala en la variable WEBHOOK_URL del .env)
docker compose up (al arrancar se ejecutan automáticamente las migraciones con Alembic y el seed.py que puebla el catálogo de productos y los asesores)
Abrir n8n en la URL de cloudfare (HTTPS) e importar el archivo con el flujo (carpeta n8n/)
Configurar la credencial de Telegram en n8n y activar el flujo
El chat del cliente queda en http://localhost:8000/, el panel de los asesores en http://localhost:8000/panel, el reporte de demanda en http://localhost:8000/reporte y la
documentación interactiva de la API en http://localhost:8000/docs
Si quieres ver el reporte con datos, el script fastapi/semilla_historia.py carga unas semanas de solicitudes cerradas de ejemplo; se ejecuta con
"docker exec -w /app radar_fastapi python semilla_historia.py" y se borra con el mismo comando agregando "borrar"

## Estructura del proyecto
El Dockerfile construye el servicio de FastAPI.
La estructura de este proyecto está guiada por 3 capas (Servicio, Persistencia y API), y las tres viven dentro de fastapi/app/. En la capa de servicio encuentras toda la
lógica de la aplicación (en Python nativo): mensajes.py orquesta un mensaje entrante de principio a fin, agente.py tiene la comunicación con el modelo y su herramienta,
leads.py arma las variables del motor y decide la escalación, analitica.py tiene las consultas de demanda y conversacion.py lo que queda del manejo de conversaciones y
mensajes. En la capa de persistencia encuentras todos los queries y la comunicación de la aplicación con la base de datos (repositorio.py); y finalmente tenemos la capa de
API con todos los endpoints de FastAPI (rutas.py) y los schemas de Pydantic (schemas.py). Aparte de las tres capas está app/motor/, que es el motor de lógica difusa
(pertenencia.py, inferencia.py, reglas.py y reglas.yaml) y no depende de nada de la aplicación. En esa misma carpeta app/ está excepciones.py, donde se definen las
excepciones propias del dominio.
Los endpoints expuestos son: /mensaje_entrante (recibe un mensaje de cualquier canal y ejecuta todo el flujo), /historial (mensajes de una conversación), /listar_asesores,
/leads_por_asesor (los leads asignados a un asesor, ordenados por prioridad), /leads_sin_asignar (las solicitudes que el sistema atendió sin escalar), /evaluaciones_lead
(el historial de cómo fue cambiando la prioridad de un lead), /cerrar_lead (registra el cierre como venta o no venta) y /demanda (el reporte del periodo).
En la raíz de fastapi/ están models.py (definición de las tablas con SQLModel), database.py (conexión a la BD), seed.py (inyección del catálogo desde productos.json y de
los asesores desde asesores.json), semilla_historia.py (historia de ejemplo para el reporte), main.py (punto de entrada de la aplicación), la carpeta prompts/ con el
prompt del agente por fuera del código, la carpeta alembic/ con las migraciones, la carpeta tests/ con las pruebas y la carpeta static/ con el frontend (index.html para el
chat, panel.html, reporte.html y sus CSS y JS separados por página).
docker-compose.yml: Configuración del Docker y comandos de arranque y montaje de la BD (creación del esquema, inyección de datos a la BD (seed.py), arranque de la aplicación).
Los volúmenes y la red están declarados con nombre explícito para que no dependan del nombre de la carpeta.
init.sql: Crea la base de datos exclusiva de n8n al levantar PostgreSQL por primera vez.

## El reporte de demanda
Como cada solicitud queda registrada con lo que el cliente pidió y con las existencias que había en ese momento, el sistema puede responder tres preguntas que antes no
tenían respuesta en ninguna parte.
Qué le pidieron y no había, con las veces, las unidades que faltaron y el monto que eso representa.
Qué le piden y no maneja, agrupado por la descripción del producto, sin monto porque no hay precio contra el cual calcularlo.
Qué mercancía tiene parada, es decir productos con existencias que nadie pidió en el periodo, con el capital que eso inmoviliza.
Arriba va el resumen del periodo (solicitudes recibidas, cuántas se escalaron, cuántas cerraron en venta y en no venta, y el monto total pedido), para que esas cifras se
lean con escala. El reporte habla solo de lo que entra por mensajería: el sistema no ve las ventas de mostrador ni las compras a proveedores.

## Pruebas
Las pruebas se corren dentro del contenedor de FastAPI, que es donde están fijadas las versiones, con "docker exec -w /app radar_fastapi python -m pytest".
Cubren el motor completo (funciones de pertenencia, operadores, activación de reglas, agregación, carga y validación del YAML y la evaluación con su explicación) y las
funciones puras de la capa de servicio (las cuatro variables, la validación de lo que devuelve el modelo y la decisión de escalación).
Las pruebas del motor se escribieron antes que las funciones, con los valores calculados a mano.

## Estado del proyecto

Este repositorio es la continuación de https://github.com/Juand13go/triaje_leads_comerciales,
que quedó congelado en la versión v1.0.0 con el sistema de triaje funcionando y la
escalación resuelta con una condición binaria.

Lo que se construyó acá es el motor de lógica difusa que reemplaza esa condición: en vez de
decidir sí o no, calcula una prioridad continua a partir de cuatro variables del lead y
devuelve, junto con el resultado, las reglas que se activaron y con qué grado. Cuando
alguien pregunta por qué se priorizó un lead sobre otro, el sistema responde.

Alrededor del motor cambió el resto del sistema: el agente dejó de decidir la escalación,
la solicitud se registra desde el primer producto que menciona el cliente (se escale o no),
lo que pidió queda guardado de forma estructurada con el precio y las existencias del
momento, y el panel muestra la bandeja ordenada por prioridad con la explicación de cada
decisión.

Este desarrollo es el entregable del diplomado en Inteligencia Artificial Avanzada y
Aplicada de la Universidad EIA para la Cámara de Comercio Aburrá Sur.

Las decisiones de diseño que se tomaron durante el desarrollo, con la razón de cada una,
están en DECISIONES.md. El orden en que se construyó cada pieza está en PLAN.md.

## Levantamiento
La primera vez: 
git clone https://github.com/Juand13go/radar_motor_difuso.git
cd radar_motor_difuso
cp .env.example .env

Cada sesion (3 terminales Ubuntu): 
1a terminal: cloudflared tunnel --url http://localhost:5678
2da terminal: cd ~/radar_motor_difuso
              nano .env          
              docker compose up
3ra terminal: cd ~/radar_motor_difuso
              code .