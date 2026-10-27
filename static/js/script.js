document.addEventListener("DOMContentLoaded", function () {
    const maxSeats = 6;

    const seatForm = document.getElementById("seatForm");
    const seatCheckboxes = document.querySelectorAll('input[name="seat_ids"]');
    const ticketCountEl = document.getElementById("ticketCount");
    const totalPriceEl = document.getElementById("totalPrice");

    function updateSummary() {
        let selectedSeats = document.querySelectorAll('input[name="seat_ids"]:checked');
        let count = selectedSeats.length;
        let total = 0;

        selectedSeats.forEach(cb => {
            const price = parseInt(cb.dataset.price || "0");
            total += price;
        });

        if (ticketCountEl) {
            ticketCountEl.textContent = `${count} ticket${count !== 1 ? "s" : ""} selected`;
        }

        if (totalPriceEl) {
            totalPriceEl.textContent = `₹${total}`;
        }
    }

    seatCheckboxes.forEach(cb => {
        cb.addEventListener("change", function () {
            const selected = document.querySelectorAll('input[name="seat_ids"]:checked');

            if (selected.length > maxSeats) {
                this.checked = false;
                alert(`You can select maximum ${maxSeats} seats.`);
                return;
            }

            if (this.checked) {
                this.closest(".seat").classList.add("selected");
            } else {
                this.closest(".seat").classList.remove("selected");
            }

            updateSummary();
        });
    });

    if (seatForm) {
        seatForm.addEventListener("submit", function (e) {
            const selected = document.querySelectorAll('input[name="seat_ids"]:checked');
            if (selected.length === 0) {
                e.preventDefault();
                alert("Please select at least one seat.");
            }
        });
    }

    updateSummary();
});

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const movieGrid = document.getElementById("movieGrid");
    const movieCards = Array.from(document.querySelectorAll(".movie-card"));
    const filterCheckboxes = document.querySelectorAll(".filter-chip input");
    const sortSelect = document.querySelector(".sort-select");
    const clearFiltersBtn = document.querySelector(".filter-card a");

    searchInput.addEventListener("input", applyFilters);

    filterCheckboxes.forEach(cb =>
        cb.addEventListener("change", applyFilters)
    );

    sortSelect.addEventListener("change", applySorting);

    clearFiltersBtn.addEventListener("click", (e) => {
        e.preventDefault();
        filterCheckboxes.forEach(cb => cb.checked = false);
        searchInput.value = "";
        sortSelect.selectedIndex = 0;
        applyFilters();
    });

    function applyFilters() {
        const searchText = searchInput.value.toLowerCase();

        const activeFilters = {
            language: [],
            format: [],
            genres: [],
            cert: []
        };

        filterCheckboxes.forEach(cb => {
            if (cb.checked) {
                const text = cb.parentElement.textContent.trim().toLowerCase();
                const section = cb.closest(".mb-3")
                    .querySelector(".filter-title")
                    .textContent.toLowerCase();

                if (section.includes("language")) activeFilters.language.push(text);
                if (section.includes("format")) activeFilters.format.push(text);
                if (section.includes("genres")) activeFilters.genres.push(text);
                if (section.includes("certificate")) activeFilters.cert.push(text);
            }
        });

        movieCards.forEach(card => {
            const title = card.querySelector(".movie-title").textContent.toLowerCase();
            const language = card.dataset.language;
            const format = card.dataset.format;
            const genres = card.dataset.genres;
            const cert = card.dataset.cert;

            let visible = true;

            if (searchText && !title.includes(searchText)) visible = false;
            if (activeFilters.language.length && !activeFilters.language.includes(language)) visible = false;
            if (activeFilters.format.length && !activeFilters.format.some(f => format.includes(f))) visible = false;
            if (activeFilters.genres.length && !activeFilters.genres.some(g => genres.includes(g))) visible = false;
            if (activeFilters.cert.length && !activeFilters.cert.includes(cert)) visible = false;

            card.parentElement.style.display = visible ? "block" : "none";
        });

        applySorting();
    }

    function applySorting() {
        const sortValue = sortSelect.value;
        const visibleCards = movieCards
            .filter(card => card.parentElement.style.display !== "none");

        let sortedCards = [...visibleCards];

        if (sortValue.includes("Title")) {
            sortedCards.sort((a, b) =>
                a.querySelector(".movie-title").textContent
                    .localeCompare(b.querySelector(".movie-title").textContent)
            );
        }

        if (sortValue.includes("High to Low")) {
            sortedCards.sort((a, b) => b.dataset.rating - a.dataset.rating);
        }

        if (sortValue.includes("Low to High")) {
            sortedCards.sort((a, b) => a.dataset.rating - b.dataset.rating);
        }

        sortedCards.forEach(card => {
            movieGrid.appendChild(card.parentElement);
        });
    }
});



 