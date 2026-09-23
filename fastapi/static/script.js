const selectAsesor = document.getElementById("selectAsesor");
const btnActualizarLeads = document.getElementById("btnActualizarLeads");
const contenedorLeads = document.getElementById("contenedorLeads");
const contenedorSinAsignar = document.getElementById("contenedorSinAsignar");
const inputSimuladorCliente = document.getElementById("inputSimuladorCliente");
const inputSimuladorNombre = document.getElementById("inputSimuladorNombre");
const inputSimuladorTexto = document.getElementById("inputSimuladorTexto");
const btnEnviarSimulador = document.getElementById("btnEnviarSimulador");
const contenedorSimulador = document.getElementById("contenedorSimulador");
const aviso = document.getElementById("aviso");
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

let temporizadorAviso = null;

const MOTIVOS_ESCALACION = {
    motor: "prioridad calculada por el motor",
    solicitud_cliente: "el cliente pidió hablar con un asesor",
    fallo_tecnico: "fallo técnico del asistente"
};

function mostrarAviso(texto, tipo) {
    aviso.textContent = texto;
    aviso.className = `aviso aviso--${tipo} aviso--visible`;
    // Un aviso nuevo cancela el temporizador del anterior, asi el que se ve siempre dura sus cuatro segundos
    clearTimeout(temporizadorAviso);
    temporizadorAviso = setTimeout(() => {
        aviso.classList.remove("aviso--visible");
    }, 4000);
}

async function listarInformacionAsesores(){
    try {
        const response = await fetch(`/listar_asesores`);

        if(!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }

        const asesores = await response.json();
        console.log("Lista de asesores obtenida: ", asesores);
        return asesores;
    }catch(error){
        console.error("Hubo un error al cargar los asesores. ", error);
        mostrarAviso("No se pudieron cargar los asesores.", "error");
    }
}

async function cargarLeadsPorAsesor(idAsesor) {
    try {
        const response = await fetch(`/leads_por_asesor?id_asesor=${idAsesor}`);

        if(!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }

        const leads = await response.json();

        console.log("Lista de leads obtenida: ", leads);
        return leads;
    }catch(error){
        console.error("Hubo un error al cargar los leads. ", error);
        mostrarAviso("No se pudieron cargar los leads del asesor.", "error");
    }
}

async function ejecutarCierreLead(idLead, estado) {
    try{
        const response = await fetch('/cerrar_lead', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id_lead: idLead,
                estado_lead: estado
            })
        });

        if(!response.ok){
            throw new Error(`No se pudo cerrar el lead. Status: ${response.status}`);
        }

        const resultado = await response.json();

        console.log("Lead cerrado exitosamente: ", resultado);
        return resultado
    } catch(error) {
        console.error("Error al cerrar el lead", error);
        mostrarAviso("No se pudo cerrar el lead. Intente de nuevo.", "error");
    }
}

async function cargarLeadsSinAsignar() {
    try {
        const response = await fetch('/leads_sin_asignar');

        if (!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }

        const leads = await response.json();
        console.log("Lista de leads sin asignar obtenida: ", leads);
        return leads;
    } catch (error) {
        console.error("Hubo un error al cargar los leads sin asignar. ", error);
        mostrarAviso("No se pudieron cargar las solicitudes sin asignar.", "error");
    }
}

async function cargarEvaluacionesLead(idLead) {
    try {
        const response = await fetch(`/evaluaciones_lead?id_lead=${idLead}`);

        if (!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }

        const evaluaciones = await response.json();
        console.log("Evaluaciones del lead obtenidas: ", evaluaciones);
        return evaluaciones;
    } catch (error) {
        console.error("Hubo un error al cargar las evaluaciones del lead. ", error);
        mostrarAviso("No se pudo cargar la explicación del lead.", "error");
    }
}

function formatearPesos(valor) {
    return `$${Math.round(valor).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".")}`;
}

function formatearFecha(textoFecha) {
    return new Date(textoFecha).toLocaleString("es-CO", { timeZone: "America/Bogota", dateStyle: "short", timeStyle: "short" });
}

function diasHastaFecha(fechaRequerida) {
    const hoyBogota = new Date().toLocaleDateString("en-CA", { timeZone: "America/Bogota" });
    // Las dos fechas se leen como medianoche UTC para restar dias calendario sin que la hora local mueva el resultado
    return Math.round((Date.parse(fechaRequerida) - Date.parse(hoyBogota)) / 86400000);
}

function textoPlazo(fechaRequerida) {
    const dias = diasHastaFecha(fechaRequerida);
    if (dias === 0) return "hoy";
    if (dias === 1) return "mañana";
    if (dias === -1) return "vencida hace 1 día";
    if (dias < 0) return `vencida hace ${-dias} días`;
    return `en ${dias} días`;
}

function renderizarEtiqueta(texto, variante) {
    const etiqueta = document.createElement("span");
    etiqueta.className = `etiqueta ${variante}`;
    etiqueta.textContent = texto;
    return etiqueta;
}

function renderizarDatoLead(nombre, valor) {
    const dato = document.createElement("span");
    if (valor) {
        dato.textContent = `${nombre}: ${valor}`;
    } else {
        dato.className = "tarjeta-lead__falta";
        dato.textContent = `${nombre}: falta este dato`;
    }
    return dato;
}

function renderizarItemLead(item) {
    const li = document.createElement("li");
    li.className = "item-lead";
    const cantidad = item.cantidad === null ? "Sin cantidad:" : `${item.cantidad} ×`;
    li.textContent = `${cantidad} ${item.descripcion}`;

    if (item.id_producto === null) {
        li.appendChild(renderizarEtiqueta("Fuera de catálogo", "etiqueta--fuera-catalogo"));
    }

    // Lo que se pidio por encima de las existencias es la demanda que no se pudo cubrir
    if (item.cantidad !== null && item.existencias_al_momento !== null && item.cantidad > item.existencias_al_momento) {
        li.classList.add("item-lead--faltante");
        li.appendChild(renderizarEtiqueta(`Faltaban ${item.cantidad - item.existencias_al_momento} unidades`, "etiqueta--faltante"));
    }
    return li;
}

function renderizarTituloExplicacion(texto) {
    const titulo = document.createElement("h4");
    titulo.className = "explicacion__titulo";
    titulo.textContent = texto;
    return titulo;
}

function renderizarListaExplicacion(lineas) {
    const lista = document.createElement("ul");
    lista.className = "explicacion__lista";
    lineas.forEach(linea => {
        const li = document.createElement("li");
        li.textContent = linea;
        lista.appendChild(li);
    });
    return lista;
}

function renderizarExplicacion(contenedor, evaluaciones) {
    contenedor.replaceChildren();

    if (!evaluaciones) {
        contenedor.appendChild(renderizarListaExplicacion(["No se pudo cargar la explicación."]));
        return;
    }

    if (evaluaciones.length === 0) {
        contenedor.appendChild(renderizarListaExplicacion(["Este lead todavía no tiene evaluaciones del motor."]));
        return;
    }

    const ultima = evaluaciones[evaluaciones.length - 1];

    const reglas = ultima.reglas_activadas.length === 0
        ? ["Ninguna regla se activó."]
        : ultima.reglas_activadas.map(regla => `${regla.nombre} · grado ${regla.grado.toFixed(2)} → ${regla.entonces}`);

    const variables = [
        `Monto estimado: ${ultima.monto_estimado === null ? "sin estimar" : formatearPesos(ultima.monto_estimado)}`,
        `Relación con el cliente: ${Math.round(ultima.relacion_cliente)} ventas cerradas`,
        `Completitud: ${Math.round(ultima.completitud * 100)} %`,
        `Plazo: ${ultima.plazo_dias === null ? "sin fecha requerida" : `${ultima.plazo_dias} días`}`
    ];

    const evolucion = evaluaciones.map(evaluacion => {
        const resultado = evaluacion.prioridad === null ? "sin clasificar" : `prioridad ${evaluacion.prioridad.toFixed(1)} · ${evaluacion.nivel_prioridad}`;
        return `${formatearFecha(evaluacion.creado_en)} · ${resultado}`;
    });

    contenedor.append(
        renderizarTituloExplicacion("Reglas activadas en la última evaluación"),
        renderizarListaExplicacion(reglas),
        renderizarTituloExplicacion("Variables con las que se evaluó"),
        renderizarListaExplicacion(variables),
        renderizarTituloExplicacion("Evolución de la prioridad"),
        renderizarListaExplicacion(evolucion)
    );
}

function renderizarBotonCierre(lead, estado, texto) {
    const boton = document.createElement("button");
    boton.className = `boton-tarjeta boton-tarjeta--${estado.replace("_", "-")}`;
    boton.textContent = texto;
    boton.addEventListener("click", async () => {
        const res = await ejecutarCierreLead(lead.id_lead, estado);
        if (res) {
            const cliente = lead.nombre_cliente && lead.nombre_cliente.trim() ? lead.nombre_cliente : lead.canal_user_id;
            mostrarAviso(`El lead de ${cliente} se cerró como ${estado.replace("_", " ")}.`, "exito");
            refrescarLeads();
        }
    });
    return boton;
}

function renderizarTarjetaLead(lead) {
    const li = document.createElement("li");
    li.className = lead.nivel_prioridad ? `tarjeta-lead prioridad-${lead.nivel_prioridad}` : "tarjeta-lead tarjeta-lead--sin-clasificar";

    const cliente = document.createElement("div");
    cliente.className = "tarjeta-lead__cliente";
    const tieneNombre = lead.nombre_cliente && lead.nombre_cliente.trim();
    cliente.textContent = tieneNombre ? `${lead.nombre_cliente} · ${lead.canal_user_id}` : lead.canal_user_id;

    const encabezado = document.createElement("div");
    encabezado.className = "tarjeta-lead__encabezado";

    const insignia = document.createElement("span");
    const prioridad = document.createElement("span");
    prioridad.className = "tarjeta-lead__prioridad";
    if (lead.nivel_prioridad) {
        insignia.className = `insignia insignia--${lead.nivel_prioridad}`;
        insignia.textContent = lead.nivel_prioridad;
        prioridad.textContent = `Prioridad ${lead.prioridad.toFixed(1)}`;
    } else {
        insignia.className = "insignia insignia--sin-clasificar";
        insignia.textContent = "sin clasificar";
        prioridad.textContent = "No fue clasificado por el motor";
    }

    const monto = document.createElement("span");
    monto.className = "tarjeta-lead__monto";
    monto.textContent = lead.monto_estimado === null ? "Monto sin estimar" : formatearPesos(lead.monto_estimado);

    encabezado.append(insignia, prioridad, monto);

    const datos = document.createElement("div");
    datos.className = "tarjeta-lead__datos";
    const fechaRequerida = lead.fecha_requerida ? `${lead.fecha_requerida} (${textoPlazo(lead.fecha_requerida)})` : null;
    datos.append(renderizarDatoLead("Ciudad", lead.ciudad), renderizarDatoLead("Fecha requerida", fechaRequerida));
    if (lead.escalado) {
        datos.appendChild(renderizarDatoLead("Escalado por", MOTIVOS_ESCALACION[lead.motivo_escalacion] || lead.motivo_escalacion));
    }

    const items = document.createElement("ul");
    items.className = "tarjeta-lead__items";
    if (lead.items.length === 0) {
        const vacio = document.createElement("li");
        vacio.className = "tarjeta-lead__falta";
        vacio.textContent = "Sin productos registrados";
        items.appendChild(vacio);
    }
    lead.items.forEach(item => items.appendChild(renderizarItemLead(item)));

    const explicacion = document.createElement("div");
    explicacion.className = "explicacion";

    const btnExplicacion = document.createElement("button");
    btnExplicacion.className = "boton-tarjeta";
    btnExplicacion.textContent = "Ver explicación";
    btnExplicacion.addEventListener("click", async () => {
        if (explicacion.classList.contains("explicacion--abierta")) {
            explicacion.classList.remove("explicacion--abierta");
            btnExplicacion.textContent = "Ver explicación";
            return;
        }
        btnExplicacion.disabled = true;
        const evaluaciones = await cargarEvaluacionesLead(lead.id_lead);
        btnExplicacion.disabled = false;
        renderizarExplicacion(explicacion, evaluaciones);
        explicacion.classList.add("explicacion--abierta");
        btnExplicacion.textContent = "Ocultar explicación";
    });

    const acciones = document.createElement("div");
    acciones.className = "tarjeta-lead__acciones";
    acciones.append(btnExplicacion, renderizarBotonCierre(lead, "venta", "Venta"), renderizarBotonCierre(lead, "no_venta", "No venta"));

    li.append(cliente, encabezado, datos, items, acciones, explicacion);
    return li;
}

function renderizarLeads(listaDeLeads, contenedor, textoVacio) {
    contenedor.replaceChildren();

    if (listaDeLeads.length === 0) {
        const vacio = document.createElement("li");
        vacio.className = "bandeja__vacia";
        vacio.textContent = textoVacio;
        contenedor.appendChild(vacio);
        return;
    }

    listaDeLeads.forEach(lead => contenedor.appendChild(renderizarTarjetaLead(lead)));
}

function renderizarOpcionesAsesores(listaAsesores) {
    listaAsesores.forEach(asesor => {
        const opcion = document.createElement("option");
        opcion.value = asesor.id_asesor;
        opcion.textContent = asesor.nombre_asesor;
        selectAsesor.appendChild(opcion);
    });
}

async function refrescarLeads() {
    const idAsesor = selectAsesor.value;
    if (idAsesor) {
        const leads = await cargarLeadsPorAsesor(idAsesor);
        if (leads) renderizarLeads(leads, contenedorLeads, "Este asesor no tiene leads abiertos.");
    } else {
        contenedorLeads.replaceChildren();
    }

    const sinAsignar = await cargarLeadsSinAsignar();
    if (sinAsignar) renderizarLeads(sinAsignar, contenedorSinAsignar, "No hay solicitudes sin asignar.");
}

async function iniciarPanel() {
    const asesores = await listarInformacionAsesores();
    if (asesores) renderizarOpcionesAsesores(asesores);
    refrescarLeads();
}

selectAsesor.addEventListener("change", refrescarLeads);

btnActualizarLeads.addEventListener("click", refrescarLeads);

iniciarPanel();

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
        mostrarAviso("El simulador no pudo obtener respuesta del sistema.", "error");
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
        mostrarAviso("Ingrese un identificador para el cliente antes de enviar.", "error");
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

    // Cada mensaje puede crear, reclasificar o escalar un lead: las bandejas se ponen al dia solas
    refrescarLeads();
}

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

async function cargarDemanda(dias) {
    try {
        const response = await fetch(`/demanda?dias=${dias}`);

        if (!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }

        const demanda = await response.json();
        console.log("Reporte de demanda obtenido: ", demanda);
        return demanda;
    } catch (error) {
        console.error("Hubo un error al cargar el reporte de demanda. ", error);
        mostrarAviso("No se pudo cargar el reporte de demanda.", "error");
    }
}

function formatearNumero(valor) {
    return Math.round(valor).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
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

const SVG_NS = "http://www.w3.org/2000/svg";
const ALTO_FILA_GRAFICO = 30;
const ALTO_BARRA_GRAFICO = 16;
const LARGO_MAXIMO_ETIQUETA = 32;

function crearNodoSvg(etiqueta, atributos) {
    const nodo = document.createElementNS(SVG_NS, etiqueta);
    for (const [nombre, valor] of Object.entries(atributos)) {
        nodo.setAttribute(nombre, valor);
    }
    return nodo;
}

function recortarEtiqueta(texto) {
    return texto.length > LARGO_MAXIMO_ETIQUETA ? `${texto.slice(0, LARGO_MAXIMO_ETIQUETA - 1)}…` : texto;
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

btnDemanda30.addEventListener("click", () => mostrarDemanda(30, btnDemanda30));

btnDemanda7.addEventListener("click", () => mostrarDemanda(7, btnDemanda7));

btnImprimirDemanda.addEventListener("click", () => window.print());

// Se llena al imprimir y no al cargar, para que la fecha sea la de la impresion aunque la pagina lleve horas abierta
window.addEventListener("beforeprint", () => {
    const fecha = new Date().toLocaleDateString("es-CO", { timeZone: "America/Bogota", day: "numeric", month: "long", year: "numeric" });
    pieImpresion.textContent = `Radar, de Halua Studio · Impreso el ${fecha}`;
});

mostrarDemanda(30, btnDemanda30);
