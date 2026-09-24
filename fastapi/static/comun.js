const aviso = document.getElementById("aviso");

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

        if (!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }

        const datos = await response.json();
        console.log(`Respuesta de ${url}: `, datos);
        return datos;
    } catch (error) {
        console.error(`Hubo un error en la petición a ${url}. `, error);
        mostrarAviso(textoAviso, "error");
    }
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
