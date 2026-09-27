const listaCatalogo = document.getElementById("listaCatalogo");

async function solicitarProductos() {
    return llamarBackend('/catalogo/productos', "No se pudo cargar el catálogo. Intente de nuevo en un momento.");
}

// La API ya los entrega ordenados por categoria; el Map conserva ese orden
function agruparPorCategoria(productos) {
    const grupos = new Map();
    productos.forEach(producto => {
        if (!grupos.has(producto.categoria)) {
            grupos.set(producto.categoria, []);
        }
        grupos.get(producto.categoria).push(producto);
    });
    return grupos;
}

function enlacePreguntar(producto) {
    return `/?mensaje=${encodeURIComponent(`Me interesa el ${producto.nombre_producto} (${producto.referencia})`)}`;
}

function renderizarProducto(producto) {
    const li = document.createElement("li");
    li.className = "tarjeta catalogo__producto";

    const nombre = document.createElement("h3");
    nombre.className = "catalogo__nombre";
    nombre.textContent = producto.nombre_producto;

    const detalle = document.createElement("p");
    detalle.className = "catalogo__detalle";
    detalle.textContent = `${producto.referencia} · ${producto.unidad}`;

    const precio = document.createElement("p");
    precio.className = "catalogo__precio";
    precio.textContent = formatearPesos(producto.precio_unitario);

    const preguntar = document.createElement("a");
    preguntar.className = "catalogo__preguntar";
    preguntar.href = enlacePreguntar(producto);
    preguntar.textContent = "Preguntar por este producto";

    li.append(nombre, detalle, precio, preguntar);
    return li;
}

function renderizarCategoria(categoria, productos) {
    const seccion = document.createElement("section");
    seccion.className = "catalogo__categoria";

    const titulo = document.createElement("h2");
    titulo.className = "catalogo__titulo-categoria";
    titulo.textContent = categoria;

    const lista = document.createElement("ul");
    lista.className = "catalogo__productos";
    productos.forEach(producto => lista.appendChild(renderizarProducto(producto)));

    seccion.append(titulo, lista);
    return seccion;
}

function renderizarCatalogo(productos) {
    listaCatalogo.replaceChildren();
    agruparPorCategoria(productos).forEach((productosCategoria, categoria) => {
        listaCatalogo.appendChild(renderizarCategoria(categoria, productosCategoria));
    });
}

async function iniciarCatalogo() {
    const productos = await solicitarProductos();

    if (!productos) {
        return;
    }

    renderizarCatalogo(productos);
}

iniciarCatalogo();
