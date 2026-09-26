const aviso = document.getElementById("aviso");
const enlaceSalir = document.getElementById("enlaceSalir");

const LARGO_MAXIMO_ETIQUETA = 32;

let temporizadorAviso = null;

function mostrarAviso(texto, tipo) {
    aviso.textContent = texto;
    aviso.className = `aviso aviso--${tipo} aviso--visible`;
    // Un aviso nuevo cancela el temporizador del anterior, asi el que se ve siempre dura sus cuatro segundos
    clearTimeout(temporizadorAviso);
    temporizadorAviso = setTimeout(() => {
        aviso.classList.remove("aviso--visible");
    }, 4000);
}

async function llamarBackend(url, textoAviso, opciones) {
    try {
        const response = await fetch(url, opciones);

        // La sesion vencio o se cerro en otra pestana: no es un error que avisar sino volver a entrar
        if (response.status === 401) {
            window.location.replace("/entrar");
            return;
        }

        if (!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }

        const datos = await response.json();
        console.log(`Respuesta de ${url}: `, datos);
        return datos;
    } catch (error) {
        console.error(`Hubo un error en la petición a ${url}. `, error);
        // Sin textoAviso el error queda solo en la consola, para las recargas que el usuario no pidio
        if (textoAviso) mostrarAviso(textoAviso, "error");
    }
}

async function cerrarSesion() {
    try {
        const response = await fetch('/salir', { method: 'POST' });

        if (!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }
    } catch (error) {
        console.error("Hubo un error en la petición a /salir. ", error);
    }
}

async function salirDelBackoffice(evento) {
    evento.preventDefault();
    await cerrarSesion();
    // Se va a /entrar aunque /salir falle; si la cookie siguiera viva, /entrar devuelve al panel
    window.location.replace("/entrar");
}

function formatearNumero(valor) {
    return Math.round(valor).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function formatearPesos(valor) {
    return `$${formatearNumero(valor)}`;
}

function diasHastaFecha(fechaRequerida) {
    const hoyBogota = new Date().toLocaleDateString("en-CA", { timeZone: "America/Bogota" });
    // Las dos fechas se leen como medianoche UTC para restar dias calendario sin que la hora local mueva el resultado
    return Math.round((Date.parse(fechaRequerida) - Date.parse(hoyBogota)) / 86400000);
}

function recortarEtiqueta(texto) {
    return texto.length > LARGO_MAXIMO_ETIQUETA ? `${texto.slice(0, LARGO_MAXIMO_ETIQUETA - 1)}…` : texto;
}

// Solo existe en las paginas del backoffice; la del cliente tambien carga este archivo
if (enlaceSalir) enlaceSalir.addEventListener("click", salirDelBackoffice);
