const formEntrar = document.getElementById("formEntrar");
const usuarioEntrar = document.getElementById("usuarioEntrar");
const claveEntrar = document.getElementById("claveEntrar");
const btnEntrar = document.getElementById("btnEntrar");
const mensajeError = document.getElementById("mensajeError");

async function iniciarSesion(usuario, clave) {
    try {
        const response = await fetch('/entrar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                usuario: usuario,
                clave: clave
            })
        });

        // El 401 es una respuesta esperada del formulario, no un fallo, por eso no pasa por el catch
        if (response.status === 401) return "incorrecta";

        if (!response.ok) {
            throw new Error(`Error en la petición: ${response.status}`);
        }

        return "correcta";
    } catch (error) {
        console.error("Hubo un error en la petición a /entrar. ", error);
        return "sin_conexion";
    }
}

function renderizarError(texto) {
    mensajeError.textContent = texto;
}

async function enviarFormulario(evento) {
    evento.preventDefault();
    renderizarError("");
    btnEntrar.disabled = true;
    btnEntrar.textContent = "Entrando...";

    const resultado = await iniciarSesion(usuarioEntrar.value, claveEntrar.value);

    if (resultado === "correcta") {
        // replace y no href, para que atras desde el panel no vuelva al formulario
        window.location.replace("/panel");
        return;
    }

    if (resultado === "incorrecta") {
        renderizarError("Usuario o clave incorrectos.");
        claveEntrar.value = "";
        claveEntrar.focus();
    } else {
        renderizarError("No se pudo conectar con el sistema. Intente de nuevo.");
    }

    btnEntrar.disabled = false;
    btnEntrar.textContent = "Entrar";
}

formEntrar.addEventListener("submit", enviarFormulario);
