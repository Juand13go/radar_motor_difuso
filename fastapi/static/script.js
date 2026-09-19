const btnListarAsesores = document.getElementById("btnListarAsesores");
const contenedorAsesores = document.getElementById("contenedorAsesores");
const inputAsesorId = document.getElementById("inputAsesorId");
const btnBuscarLeads = document.getElementById("btnBuscarLeads");
const contenedorLeads = document.getElementById("contenedorLeads");
const inputSimuladorCliente = document.getElementById("inputSimuladorCliente");
const inputSimuladorNombre = document.getElementById("inputSimuladorNombre");
const inputSimuladorTexto = document.getElementById("inputSimuladorTexto");
const btnEnviarSimulador = document.getElementById("btnEnviarSimulador");
const contenedorSimulador = document.getElementById("contenedorSimulador");

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
    }
}

function renderizarAsesores(listaAsesores){
    contenedorAsesores.innerHTML = "";
    
    if(!listaAsesores || listaAsesores.length === 0){
        contenedorAsesores.innerHTML = "<li>No hay asesores registrados.</li>";
        return; 
    }
    
    listaAsesores.forEach(asesor => {
        const li = document.createElement("li");
        li.textContent = `Asesor: ${asesor.nombre_asesor}, ID: ${asesor.id_asesor}`;
        
        contenedorAsesores.appendChild(li);
    });
}

function renderizarLeads(listaDeLeads){
    contenedorLeads.innerHTML = "";

    if (listaDeLeads.length === 0){
        contenedorLeads.innerHTML = "<li>No hay leads asignados a este asesor.</li>"
        return; 
    }

    listaDeLeads.forEach(lead => {
        const li = document.createElement("li");
        li.textContent = `Lead ID: ${lead.id_lead}, ID Conversacion: ${lead.id_conversacion}, Productos de Interes: ${lead.productos_interes}, Ciudad: ${lead.ciudad}`;
                    
        const btnVenta = document.createElement("button");
        btnVenta.textContent = "Venta";
        btnVenta.style.marginLeft = "10px";
        btnVenta.addEventListener("click", async () => {
            const res = await ejecutarCierreLead(lead.id_lead, "venta");
            if (res) {
                alert(`Lead ${lead.id_lead} cerrado como venta.`);
                refrescarLeads();
            }
        });

        const btnNoVenta = document.createElement("button");
        btnNoVenta.textContent = "No venta";
        btnNoVenta.style.marginLeft = "10px";
        btnNoVenta.addEventListener("click", async () => {
            const res = await ejecutarCierreLead(lead.id_lead, "no_venta");
            if (res) {
                alert(`Lead ${lead.id_lead} cerrado como no venta.`)
                refrescarLeads();
            }
        });
        
        li.appendChild(btnVenta);
        li.appendChild(btnNoVenta);

        contenedorLeads.appendChild(li);
    });
} 

async function refrescarLeads() {
    const idAsesor = inputAsesorId.value.trim();
    if (idAsesor) {
        const leads = await cargarLeadsPorAsesor(idAsesor);
        if (leads) renderizarLeads(leads);
    }
}

btnListarAsesores.addEventListener("click", async () => {
    const asesores = await listarInformacionAsesores();

    if (asesores) {
        renderizarAsesores(asesores);
    }
});

btnBuscarLeads.addEventListener("click", async () => {
    const idAsesor = inputAsesorId.value.trim();

    if(!idAsesor) {
        alert("Por favor ingrese un UUID válido.");
        return; 
    }

    const leads = await cargarLeadsPorAsesor(idAsesor);
    if (leads) {
        renderizarLeads(leads);
    }
});

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
        alert("Por favor ingrese un identificador para el cliente.");
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
