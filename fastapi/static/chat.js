const inputSimuladorNombre = document.getElementById("inputSimuladorNombre");
const inputSimuladorTexto = document.getElementById("inputSimuladorTexto");
const btnEnviarSimulador = document.getElementById("btnEnviarSimulador");
const btnNuevaConversacion = document.getElementById("btnNuevaConversacion");
const listaConversaciones = document.getElementById("listaConversaciones");
const contenedorSimulador = document.getElementById("contenedorSimulador");

let conversacionActiva = null;
let esperandoRespuesta = false;

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

        if (response.status === 401) {
            window.location.replace("/entrar");
            return null;
        }

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

async function cargarConversacionesSimulador(avisarError) {
    return llamarBackend('/conversaciones_simulador', avisarError ? "No se pudieron cargar las conversaciones." : null);
}

async function cargarMensajesSimulador(idConversacion) {
    return llamarBackend(`/mensajes_simulador?id_conversacion=${idConversacion}`, "No se pudo abrir la conversación.");
}

function generarCanalUserId() {
    return `simulador-${Math.floor(Math.random() * 1000000)}`;
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

function marcarConversacionActiva() {
    listaConversaciones.querySelectorAll(".simulador__item").forEach(boton => {
        boton.classList.toggle("simulador__item--activo", boton.dataset.canalUserId === conversacionActiva.canal_user_id);
    });
}

function renderizarConversacionSimulador(conversacion) {
    const li = document.createElement("li");

    const boton = document.createElement("button");
    boton.className = "simulador__item";
    boton.dataset.canalUserId = conversacion.canal_user_id;
    boton.disabled = esperandoRespuesta;

    const nombre = document.createElement("span");
    nombre.className = "simulador__nombre";
    nombre.textContent = conversacion.nombre || "Cliente sin nombre";

    const ultimoMensaje = document.createElement("span");
    ultimoMensaje.className = "simulador__ultimo";
    ultimoMensaje.textContent = recortarEtiqueta(conversacion.ultimo_mensaje);

    boton.appendChild(nombre);
    boton.appendChild(ultimoMensaje);
    boton.addEventListener("click", () => abrirConversacion(conversacion));

    li.appendChild(boton);
    return li;
}

function renderizarListaConversaciones(conversaciones) {
    listaConversaciones.replaceChildren();
    conversaciones.forEach(conversacion => listaConversaciones.appendChild(renderizarConversacionSimulador(conversacion)));
    marcarConversacionActiva();
}

async function recargarListaConversaciones(avisarError) {
    const conversaciones = await cargarConversacionesSimulador(avisarError);
    if (conversaciones) {
        renderizarListaConversaciones(conversaciones);
    }
}

function bloquearSimulador(bloqueado) {
    esperandoRespuesta = bloqueado;
    btnEnviarSimulador.disabled = bloqueado;
    btnNuevaConversacion.disabled = bloqueado;
    listaConversaciones.querySelectorAll(".simulador__item").forEach(boton => {
        boton.disabled = bloqueado;
    });
}

async function abrirConversacion(conversacion) {
    if (esperandoRespuesta) {
        return;
    }

    const abierta = { canal_user_id: conversacion.canal_user_id, nombre: conversacion.nombre, nueva: false };
    conversacionActiva = abierta;
    contenedorSimulador.replaceChildren();
    marcarConversacionActiva();
    bloquearSimulador(true);

    const mensajes = await cargarMensajesSimulador(conversacion.id_conversacion);

    // Si mientras llegaban los mensajes se abrio otra conversacion, estos ya no son los de la pantalla y el desbloqueo le toca a esa apertura
    if (conversacionActiva !== abierta) {
        return;
    }

    bloquearSimulador(false);

    if (!mensajes) {
        return;
    }

    mensajes.forEach(mensaje => renderizarMensajeSimulador(mensaje.contenido, mensaje.rol === "user" ? "cliente" : "sistema"));
}

function iniciarNuevaConversacion() {
    if (esperandoRespuesta) {
        return;
    }

    conversacionActiva = { canal_user_id: generarCanalUserId(), nombre: inputSimuladorNombre.value.trim(), nueva: true };
    contenedorSimulador.replaceChildren();
    marcarConversacionActiva();
    inputSimuladorTexto.focus();
}

async function enviarDesdeSimulador() {
    const texto = inputSimuladorTexto.value.trim();

    if (!texto || esperandoRespuesta) {
        return;
    }

    // El backend solo guarda el nombre al crear la conversacion, por eso se sigue leyendo del campo mientras sea nueva
    if (conversacionActiva.nueva) {
        conversacionActiva.nombre = inputSimuladorNombre.value.trim();
    }

    renderizarMensajeSimulador(texto, "cliente");
    inputSimuladorTexto.value = "";
    bloquearSimulador(true);
    const pendiente = renderizarMensajeSimulador("El sistema está respondiendo...", "pendiente");

    const resultado = await enviarMensajeSimulador(conversacionActiva.canal_user_id, conversacionActiva.nombre, texto);

    // Sin resultado la pagina ya va camino a /entrar, asi que se deja como esta
    if (!resultado) return;

    pendiente.remove();
    bloquearSimulador(false);
    inputSimuladorTexto.focus();

    if (resultado.error) {
        renderizarMensajeSimulador(`No se pudo obtener respuesta: ${resultado.error}`, "error");
        return;
    }

    conversacionActiva.nueva = false;
    renderizarMensajeSimulador(resultado.respuesta_cliente, "sistema");

    if (resultado.notificacion_asesor) {
        renderizarNotificacionSimulador(resultado.notificacion_asesor);
    }

    await recargarListaConversaciones(false);
}

function iniciarSimulador() {
    iniciarNuevaConversacion();

    btnEnviarSimulador.addEventListener("click", enviarDesdeSimulador);
    btnNuevaConversacion.addEventListener("click", iniciarNuevaConversacion);

    inputSimuladorTexto.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") {
            enviarDesdeSimulador();
        }
    });

    recargarListaConversaciones(true);
}

// Solo arranca en la pagina que tiene el simulador, asi este archivo no busca elementos que no existen
if (inputSimuladorNombre && inputSimuladorTexto && btnEnviarSimulador && btnNuevaConversacion && listaConversaciones && contenedorSimulador) {
    iniciarSimulador();
}
