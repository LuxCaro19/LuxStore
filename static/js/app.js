document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("product-search");

    if (!searchInput) {
        return;
    }

    const productCards = document.querySelectorAll(
        "[data-product-card]"
    );

    const emptyState = document.getElementById(
        "products-live-empty"
    );


    searchInput.addEventListener("input", () => {

        const search = searchInput.value
            .trim()
            .toLowerCase();

        let visibleProducts = 0;


        productCards.forEach((card) => {

            const name = card.dataset.name || "";
            const code = card.dataset.code || "";

            const matches =
                name.includes(search)
                || code.includes(search);


            if (matches) {

                card.hidden = false;
                visibleProducts++;

            } else {

                card.hidden = true;

            }

        });


        if (emptyState) {
            emptyState.hidden = visibleProducts > 0;
        }

    });

});

document.addEventListener("DOMContentLoaded", () => {

    const precioCompra = document.getElementById(
        "id_precio_compra"
    );

    const porcentajeGanancia = document.getElementById(
        "id_porcentaje_ganancia"
    );

    const precioSugerido = document.getElementById(
        "precio-sugerido"
    );

    if (
        !precioCompra
        || !porcentajeGanancia
        || !precioSugerido
    ) {
        return;
    }


    const calcularPrecioSugerido = () => {

        const compra = Number(
            precioCompra.value || 0
        );

        const porcentaje = Number(
            porcentajeGanancia.value || 0
        );


        if (!precioCompra.value) {

            precioSugerido.textContent = "—";
            return;

        }


        const sugerido = Math.round(
            compra + (
                compra * porcentaje / 100
            )
        );


        precioSugerido.textContent =
            "$" + new Intl.NumberFormat(
                "es-CL"
            ).format(sugerido);

    };


    precioCompra.addEventListener(
        "input",
        calcularPrecioSugerido
    );

    porcentajeGanancia.addEventListener(
        "input",
        calcularPrecioSugerido
    );


    calcularPrecioSugerido();

});

document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById(
        "fiador-search"
    );

    if (!searchInput) {
        return;
    }

    const cards = document.querySelectorAll(
        "[data-fiador-card]"
    );

    const emptyState = document.getElementById(
        "fiadores-live-empty"
    );


    searchInput.addEventListener("input", () => {

        const search = searchInput.value
            .trim()
            .toLowerCase();

        let visibles = 0;


        cards.forEach((card) => {

            const nombre =
                card.dataset.name || "";

            const coincide =
                nombre.includes(search);


            card.hidden = !coincide;

            if (coincide) {
                visibles++;
            }

        });


        if (emptyState) {
            emptyState.hidden = visibles > 0;
        }

    });

});