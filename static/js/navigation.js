document.addEventListener("DOMContentLoaded", () => {
    const nav = document.querySelector("[data-nav-root]");
    const toggle = document.querySelector("[data-nav-toggle]");

    if (!nav || !toggle) {
        return;
    }

    const mobileQuery = window.matchMedia("(max-width: 768px)");

    const setMenuState = (isOpen) => {
        nav.classList.toggle("is-open", isOpen);
        toggle.classList.toggle("is-active", isOpen);
        toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        toggle.setAttribute(
            "aria-label",
            isOpen ? "Fechar menu de navegacao" : "Abrir menu de navegacao"
        );
    };

    const closeMenu = () => {
        setMenuState(false);
    };

    nav.classList.add("nav-ready");
    closeMenu();

    toggle.addEventListener("click", () => {
        if (!mobileQuery.matches) {
            return;
        }

        setMenuState(!nav.classList.contains("is-open"));
    });

    nav.querySelectorAll("[data-nav-link]").forEach((link) => {
        link.addEventListener("click", () => {
            if (mobileQuery.matches) {
                closeMenu();
            }
        });
    });

    const handleViewportChange = (event) => {
        if (!event.matches) {
            closeMenu();
        }
    };

    if (typeof mobileQuery.addEventListener === "function") {
        mobileQuery.addEventListener("change", handleViewportChange);
    } else if (typeof mobileQuery.addListener === "function") {
        mobileQuery.addListener(handleViewportChange);
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeMenu();
        }
    });
});
