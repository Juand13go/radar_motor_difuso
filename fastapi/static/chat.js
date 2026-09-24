const inputSimuladorCliente = document.getElementById("inputSimuladorCliente");
const inputSimuladorNombre = document.getElementById("inputSimuladorNombre");
const inputSimuladorTexto = document.getElementById("inputSimuladorTexto");
const btnEnviarSimulador = document.getElementById("btnEnviarSimulador");
const contenedorSimulador = document.getElementById("contenedorSimulador");

// No usa llamarBackend porque el mensaje del error se muestra dentro de la conversacion
async function enviarMensajeSimulador(canalUserId, nombre, texto) {
    try {
        const response = await fetch('/mensaje_entrante', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                canal: "simulador",
                canal_user_id: canalUserId,
                nombre: nombre || null,
                texto: texto
            })
        });

        if (!response.ok) {
            throw new Error(`El sistema no pudo responder. Status: ${response.status}`);
        }

        const resultado = await response.json();
        console.log("Respuesta del simulador: ", resultado);
        return resultado;
    } catch (error) {
        console.error("Error al enviar el mensaje del simulador", error);
        mostrarAviso("El chat no pudo obtener respuesta del sistema.", "error");
        return { error: error.message };
    }
}

function agregarAlSimulador(elemento) {
    contenedorSimulador.appendChild(elemento);
    contenedorSimulador.scrollTop = contenedorSimulador.scrollHeight;
    return elemento;
}

function renderizarMensajeSimulador(texto, autor) {
    const li = document.createElement("li");
    li.className = `mensaje mensaje--${autor}`;
    li.textContent = texto;
    return agregarAlSimulador(li);
}

function renderizarNotificacionSimulador(notificacion) {
    const li = document.createElement("li");
    li.className = "mensaje mensaje--notificacion";

    const titulo = document.createElement("span");
    titulo.className = "mensaje__titulo";
    titulo.textContent = `Notificación para ${notificacion.nombre_asesor}`;

    const texto = document.createElement("span");
    texto.textContent = notificacion.texto;

    li.appendChild(titulo);
    li.appendChild(texto);
    agregarAlSimulador(li);
}

async function enviarDesdeSimulador() {
    const texto = inputSimuladorTexto.value.trim();
    const canalUserId = inputSimuladorCliente.value.trim();

    if (!texto || btnEnviarSimulador.disabled) {
        return;
    }

    if (!canalUserId) {
        mostrarAviso("Ingrese la identificación de la conversación antes de enviar.", "error");
        return;
    }

    renderizarMensajeSimulador(texto, "cliente");
    inputSimuladorTexto.value = "";
    btnEnviarSimulador.disabled = true;
    const pendiente = renderizarMensajeSimulador("El sistema está respondiendo...", "pendiente");

    const resultado = await enviarMensajeSimulador(canalUserId, inputSimuladorNombre.value.trim(), texto);

    pendiente.remove();
    btnEnviarSimulador.disabled = false;
    inputSimuladorTexto.focus();

    if (resultado.error) {
        renderizarMensajeSimulador(`No se pudo obtener respuesta: ${resultado.error}`, "error");
        return;
    }

    renderizarMensajeSimulador(resultado.respuesta_cliente, "sistema");

    if (resultado.notificacion_asesor) {
        renderizarNotificacionSimulador(resultado.notificacion_asesor);
    }
}

function iniciarSimulador() {
    // Cada carga de la pagina es un cliente nuevo; cambiar el identificador a mano es empezar como otro cliente
    inputSimuladorCliente.value = `simulador-${Math.floor(Math.random() * 1000000)}`;

    btnEnviarSimulador.addEventListener("click", enviarDesdeSimulador);

    inputSimuladorTexto.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") {
            enviarDesdeSimulador();
        }
    });

    inputSimuladorCliente.addEventListener("change", () => {
        contenedorSimulador.replaceChildren();
    });
}

// Solo arranca en la pagina que tiene el simulador, asi este archivo no busca elementos que no existen
if (inputSimuladorCliente && inputSimuladorNombre && inputSimuladorTexto && btnEnviarSimulador && contenedorSimulador) {
    iniciarSimulador();
}
