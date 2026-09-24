const btnDemanda30 = document.getElementById("btnDemanda30");
const btnDemanda7 = document.getElementById("btnDemanda7");
const textoPeriodoDemanda = document.getElementById("textoPeriodoDemanda");
const contenedorResumenDemanda = document.getElementById("contenedorResumenDemanda");
const contenedorNoCubierta = document.getElementById("contenedorNoCubierta");
const contenedorFueraCatalogo = document.getElementById("contenedorFueraCatalogo");
const contenedorSobrestock = document.getElementById("contenedorSobrestock");
const graficoNoCubierta = document.getElementById("graficoNoCubierta");
const graficoFueraCatalogo = document.getElementById("graficoFueraCatalogo");
const graficoSobrestock = document.getElementById("graficoSobrestock");
const btnImprimirDemanda = document.getElementById("btnImprimirDemanda");
const pieImpresion = document.getElementById("pieImpresion");

const SVG_NS = "http://www.w3.org/2000/svg";
const ALTO_FILA_GRAFICO = 30;
const ALTO_BARRA_GRAFICO = 16;

async function cargarDemanda(dias) {
    return llamarBackend(`/demanda?dias=${dias}`, "No se pudo cargar el reporte de demanda.");
}

function renderizarCifraResumen(valor, etiqueta) {
    const cifra = document.createElement("div");
    cifra.className = "franja-demanda__cifra";

    const numero = document.createElement("span");
    numero.className = "franja-demanda__numero";
    numero.textContent = valor;

    const texto = document.createElement("span");
    texto.className = "franja-demanda__etiqueta";
    texto.textContent = etiqueta;

    cifra.append(numero, texto);
    return cifra;
}

function renderizarResumenDemanda(resumen) {
    contenedorResumenDemanda.replaceChildren(
        renderizarCifraResumen(formatearNumero(resumen.solicitudes), "solicitudes recibidas"),
        renderizarCifraResumen(formatearNumero(resumen.escaladas), "escaladas a un asesor"),
        renderizarCifraResumen(formatearNumero(resumen.ventas), "cerradas en venta"),
        renderizarCifraResumen(formatearNumero(resumen.no_ventas), "cerradas en no venta"),
        renderizarCifraResumen(formatearPesos(resumen.monto_total), "monto total pedido")
    );
}

// columnas es una lista de [encabezado, funcion que saca el texto de la fila, si es la cifra destacada]
function renderizarTablaDemanda(filas, columnas, contenedor, textoVacio) {
    if (filas.length === 0) {
        const vacio = document.createElement("p");
        vacio.className = "bandeja__vacia";
        vacio.textContent = textoVacio;
        contenedor.replaceChildren(vacio);
        return;
    }

    const tabla = document.createElement("table");
    tabla.className = "tabla-demanda";

    const encabezado = document.createElement("tr");
    for (const [titulo, , destacada] of columnas) {
        const celda = document.createElement("th");
        celda.textContent = titulo;
        if (destacada) celda.className = "tabla-demanda__destacada";
        encabezado.appendChild(celda);
    }
    const thead = document.createElement("thead");
    thead.appendChild(encabezado);

    const tbody = document.createElement("tbody");
    for (const fila of filas) {
        const tr = document.createElement("tr");
        for (const [, obtenerTexto, destacada] of columnas) {
            const celda = document.createElement("td");
            celda.textContent = obtenerTexto(fila);
            if (destacada) celda.className = "tabla-demanda__destacada";
            tr.appendChild(celda);
        }
        tbody.appendChild(tr);
    }

    tabla.append(thead, tbody);
    contenedor.replaceChildren(tabla);
}

function crearNodoSvg(etiqueta, atributos) {
    const nodo = document.createElementNS(SVG_NS, etiqueta);
    for (const [nombre, valor] of Object.entries(atributos)) {
        nodo.setAttribute(nombre, valor);
    }
    return nodo;
}

// Las posiciones van en porcentaje para que el grafico ocupe el ancho del bloque sin recalcular al cambiar la ventana:
// la etiqueta vive en el primer 32%, la barra entre el 33% y el 82%, y el valor queda alineado al borde derecho
function renderizarGraficoDemanda(filas, obtenerEtiqueta, obtenerValor, formatearValor, variante, contenedor) {
    if (filas.length === 0) {
        contenedor.replaceChildren();
        return;
    }

    const maximo = Math.max(...filas.map(obtenerValor));
    const svg = crearNodoSvg("svg", { width: "100%", height: filas.length * ALTO_FILA_GRAFICO, role: "img" });
    svg.classList.add("grafico-demanda__svg", `grafico-demanda__svg--${variante}`);

    filas.forEach((fila, indice) => {
        const centro = indice * ALTO_FILA_GRAFICO + ALTO_FILA_GRAFICO / 2;
        const etiqueta = obtenerEtiqueta(fila);
        const valor = obtenerValor(fila);
        const ancho = maximo > 0 ? (valor / maximo) * 49 : 0;

        const texto = crearNodoSvg("text", { x: "0", y: centro, "dominant-baseline": "middle", class: "grafico-demanda__etiqueta" });
        texto.textContent = recortarEtiqueta(etiqueta);
        const titulo = crearNodoSvg("title", {});
        titulo.textContent = etiqueta;
        texto.appendChild(titulo);

        const barra = crearNodoSvg("rect", { x: "33%", y: centro - ALTO_BARRA_GRAFICO / 2, width: `${ancho}%`, height: ALTO_BARRA_GRAFICO, class: "grafico-demanda__barra" });

        const cifra = crearNodoSvg("text", { x: "100%", y: centro, "dominant-baseline": "middle", "text-anchor": "end", class: "grafico-demanda__valor" });
        cifra.textContent = formatearValor(valor);

        svg.append(texto, barra, cifra);
    });

    contenedor.replaceChildren(svg);
}

// Las fechas llegan como AAAA-MM-DD; se leen en UTC para que la zona del navegador no corra el dia
function formatearFechaLarga(textoFecha, conAnio) {
    const opciones = { timeZone: "UTC", day: "numeric", month: "long" };
    if (conAnio) opciones.year = "numeric";
    return new Date(`${textoFecha}T00:00:00Z`).toLocaleDateString("es-CO", opciones);
}

function renderizarPeriodoDemanda(inicio, fin) {
    const mismoAnio = inicio.slice(0, 4) === fin.slice(0, 4);
    textoPeriodoDemanda.textContent = `del ${formatearFechaLarga(inicio, !mismoAnio)} al ${formatearFechaLarga(fin, true)}`;
}

function renderizarDemanda(demanda) {
    renderizarPeriodoDemanda(demanda.inicio, demanda.fin);
    renderizarResumenDemanda(demanda.resumen);

    renderizarTablaDemanda(demanda.no_cubierta, [
        ["Referencia", (fila) => fila.referencia, false],
        ["Producto", (fila) => fila.nombre_producto, false],
        ["Veces", (fila) => formatearNumero(fila.veces), false],
        ["Unidades pedidas", (fila) => formatearNumero(fila.unidades_pedidas), false],
        ["Unidades que faltaron", (fila) => formatearNumero(fila.unidades_faltantes), false],
        ["Monto que faltó", (fila) => formatearPesos(fila.monto_faltante), true]
    ], contenedorNoCubierta, "En este periodo no se pidió nada que faltara en existencias.");
    renderizarGraficoDemanda(demanda.no_cubierta, (fila) => fila.nombre_producto, (fila) => fila.monto_faltante, formatearPesos, "no-cubierta", graficoNoCubierta);

    renderizarTablaDemanda(demanda.fuera_de_catalogo, [
        ["Descripción", (fila) => fila.descripcion, false],
        ["Veces", (fila) => formatearNumero(fila.veces), true],
        ["Unidades", (fila) => formatearNumero(fila.unidades), false]
    ], contenedorFueraCatalogo, "En este periodo no se pidieron productos fuera del catálogo.");
    renderizarGraficoDemanda(demanda.fuera_de_catalogo, (fila) => fila.descripcion, (fila) => fila.veces, formatearNumero, "fuera-catalogo", graficoFueraCatalogo);

    renderizarTablaDemanda(demanda.sobrestock, [
        ["Referencia", (fila) => fila.referencia, false],
        ["Producto", (fila) => fila.nombre_producto, false],
        ["Existencias", (fila) => formatearNumero(fila.existencias), false],
        ["Precio unitario", (fila) => formatearPesos(fila.precio_unitario), false],
        ["Capital inmovilizado", (fila) => formatearPesos(fila.capital_inmovilizado), true]
    ], contenedorSobrestock, "En este periodo todos los productos con existencias tuvieron al menos una solicitud.");
    renderizarGraficoDemanda(demanda.sobrestock, (fila) => fila.nombre_producto, (fila) => fila.capital_inmovilizado, formatearPesos, "sobrestock", graficoSobrestock);
}

async function mostrarDemanda(dias, botonActivo) {
    btnDemanda30.classList.remove("boton--periodo-activo");
    btnDemanda7.classList.remove("boton--periodo-activo");
    botonActivo.classList.add("boton--periodo-activo");

    const demanda = await cargarDemanda(dias);
    if (demanda) renderizarDemanda(demanda);
}

function iniciarReporte() {
    btnDemanda30.addEventListener("click", () => mostrarDemanda(30, btnDemanda30));

    btnDemanda7.addEventListener("click", () => mostrarDemanda(7, btnDemanda7));

    btnImprimirDemanda.addEventListener("click", () => window.print());

    // Se llena al imprimir y no al cargar, para que la fecha sea la de la impresion aunque la pagina lleve horas abierta
    window.addEventListener("beforeprint", () => {
        const fecha = new Date().toLocaleDateString("es-CO", { timeZone: "America/Bogota", day: "numeric", month: "long", year: "numeric" });
        pieImpresion.textContent = `Radar, de Halua Studio · Impreso el ${fecha}`;
    });

    mostrarDemanda(30, btnDemanda30);
}

// Solo arranca en la pagina que tiene el reporte, asi este archivo no busca elementos que no existen
if (btnDemanda30 && btnDemanda7 && textoPeriodoDemanda && contenedorResumenDemanda && contenedorNoCubierta && contenedorFueraCatalogo && contenedorSobrestock && graficoNoCubierta && graficoFueraCatalogo && graficoSobrestock && btnImprimirDemanda && pieImpresion) {
    iniciarReporte();
}
