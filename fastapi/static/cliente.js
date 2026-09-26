const conversacionCliente = document.getElementById("conversacionCliente");
const inputClienteNombre = document.getElementById("inputClienteNombre");
const inputClienteTexto = document.getElementById("inputClienteTexto");
const btnEnviarCliente = document.getElementById("btnEnviarCliente");

const CLAVE_ID_CLIENTE = "radar_canal_user_id";
const TEXTO_BIENVENIDA = "Bienvenido a Tornalba Suministros Técnicos. Cuéntenos qué productos necesita, en qué cantidades y para cuándo.";
const TEXTO_ERROR_CLIENTE = "No pudimos procesar su mensaje. Por favor intente de nuevo en un momento.";
const FORMA_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

let idCliente = null;
let esperandoRespuesta = false;

function generarUuid() {
    if (crypto.randomUUID) {
        return crypto.randomUUID();
    }

    // randomUUID solo existe en HTTPS o localhost; por http el uuid v4 se arma a mano
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function obtenerIdCliente() {
    if (idCliente) {
        return idCliente;
    }

    try {
        idCliente = localStorage.getItem(CLAVE_ID_CLIENTE);
    } catch (error) {
        console.warn("No se pudo leer el identificador guardado del cliente", error);
    }

    // Un valor dañado haria que el backend respondiera 422 en cada mensaje de este navegador
    if (!idCliente || !FORMA_UUID.test(idCliente)) {
        idCliente = generarUuid();
        try {
            localStorage.setItem(CLAVE_ID_CLIENTE, idCliente);
        } catch (error) {
            console.warn("No se pudo guardar el identificador del cliente; la conversación dura lo que dure la pestaña", error);
        }
    }

    return idCliente;
}

async function solicitarHistorialCliente() {
    return llamarBackend('/chat/historial', "No se pudo cargar su conversación.", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            canal_user_id: obtenerIdCliente()
        })
    });
}

// No usa llamarBackend porque el error se muestra dentro de la conversacion
async function enviarChatCliente(nombre, texto) {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                canal_user_id: obtenerIdCliente(),
                nombre: nombre || null,
                texto: texto
            })
        });

        if (!response.ok) {
            throw new Error(`El sistema no pudo responder. Status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Error al enviar el mensaje del cliente", error);
        return { error: error.message };
    }
}

function renderizarMensajeCliente(texto, autor) {
    const li = document.createElement("li");
    li.className = `chat-cliente__mensaje chat-cliente__mensaje--${autor}`;
    li.textContent = texto;
    conversacionCliente.appendChild(li);
    // La conversacion no tiene scroll propio: baja la pagina para que el ultimo mensaje quede sobre los controles
    window.scrollTo({ top: document.documentElement.scrollHeight });
    return li;
}

function ocultarCampoNombre() {
    inputClienteNombre.hidden = true;
}

function bloquearCliente(bloqueado) {
    esperandoRespuesta = bloqueado;
    inputClienteTexto.disabled = bloqueado;
    btnEnviarCliente.disabled = bloqueado;
}

async function cargarHistorialCliente() {
    // Bloqueado mientras carga, para que un mensaje enviado antes no quede arriba del historial
    bloquearCliente(true);
    const mensajes = await solicitarHistorialCliente();
    bloquearCliente(false);

    if (!mensajes) {
        return;
    }

    if (mensajes.length === 0) {
        renderizarMensajeCliente(TEXTO_BIENVENIDA, "sistema");
        return;
    }

    ocultarCampoNombre();
    mensajes.forEach(mensaje => renderizarMensajeCliente(mensaje.contenido, mensaje.rol === "user" ? "cliente" : "sistema"));
}

async function enviarMensajeCliente() {
    const texto = inputClienteTexto.value.trim();

    if (!texto || esperandoRespuesta) {
        return;
    }

    // El backend solo guarda el nombre al crear la conversacion
    const nombre = inputClienteNombre.hidden ? null : inputClienteNombre.value.trim();

    renderizarMensajeCliente(texto, "cliente");
    inputClienteTexto.value = "";
    bloquearCliente(true);
    const pendiente = renderizarMensajeCliente("Escribiendo...", "pendiente");

    const resultado = await enviarChatCliente(nombre, texto);

    pendiente.remove();
    bloquearCliente(false);
    inputClienteTexto.focus();

    if (resultado.error) {
        renderizarMensajeCliente(TEXTO_ERROR_CLIENTE, "error");
        inputClienteTexto.value = texto;
        return;
    }

    ocultarCampoNombre();
    renderizarMensajeCliente(resultado.respuesta_cliente, "sistema");
}

function iniciarCliente() {
    btnEnviarCliente.addEventListener("click", enviarMensajeCliente);

    inputClienteTexto.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") {
            enviarMensajeCliente();
        }
    });

    cargarHistorialCliente();
}

iniciarCliente();
