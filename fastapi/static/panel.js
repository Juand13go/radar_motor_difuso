const selectAsesor = document.getElementById("selectAsesor");
const btnActualizarLeads = document.getElementById("btnActualizarLeads");
const contenedorLeads = document.getElementById("contenedorLeads");
const contenedorSinAsignar = document.getElementById("contenedorSinAsignar");

const MOTIVOS_ESCALACION = {
    motor: "prioridad calculada por el motor",
    solicitud_cliente: "el cliente pidió hablar con un asesor",
    fallo_tecnico: "fallo técnico del asistente"
};

async function listarInformacionAsesores() {
    return llamarBackend('/listar_asesores', "No se pudieron cargar los asesores.");
}

async function cargarLeadsPorAsesor(idAsesor) {
    return llamarBackend(`/leads_por_asesor?id_asesor=${idAsesor}`, "No se pudieron cargar los leads del asesor.");
}

async function ejecutarCierreLead(idLead, estado) {
    return llamarBackend('/cerrar_lead', "No se pudo cerrar el lead. Intente de nuevo.", {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id_lead: idLead,
            estado_lead: estado
        })
    });
}

async function cargarLeadsSinAsignar() {
    return llamarBackend('/leads_sin_asignar', "No se pudieron cargar las solicitudes sin asignar.");
}

async function cargarEvaluacionesLead(idLead) {
    return llamarBackend(`/evaluaciones_lead?id_lead=${idLead}`, "No se pudo cargar la explicación del lead.");
}

function formatearFecha(textoFecha) {
    return new Date(textoFecha).toLocaleString("es-CO", { timeZone: "America/Bogota", dateStyle: "short", timeStyle: "short" });
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
    selectAsesor.addEventListener("change", refrescarLeads);

    btnActualizarLeads.addEventListener("click", refrescarLeads);

    const asesores = await listarInformacionAsesores();
    if (asesores) renderizarOpcionesAsesores(asesores);
    refrescarLeads();
}

// Solo arranca en la pagina que tiene las bandejas, asi este archivo no busca elementos que no existen
if (selectAsesor && btnActualizarLeads && contenedorLeads && contenedorSinAsignar) {
    iniciarPanel();
}
