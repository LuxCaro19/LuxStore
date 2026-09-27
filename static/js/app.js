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