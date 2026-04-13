const filterBtn = document.getElementById("filter-btn");
const clearBtn = document.getElementById("clear-btn");
const nameInput = document.getElementById("id_nombre");
const roomsContainer = document.getElementById("rooms-accordion");
function updateRooms(nameFilter = "") {
      console.log(`Updating rooms with filter: ${nameFilter}`);
  const formData = new FormData();
  formData.append("csrfmiddlewaretoken", csrfToken);
  formData.append("checkin", checkin);
  formData.append("checkout", checkout);
  formData.append("guests", guests);
  formData.append("name_filter", nameFilter);
  // Mostrar loading
  roomsContainer.innerHTML =
    '<div class="text-center p-5"><div class="spinner-border text-primary" role="status"></div><p>Cargando...</p></div>';
  fetch(roomFilterUrl, {
        method: "POST",
    headers: { "X-Requested-With": "XMLHttpRequest" },
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
          if (data.total_rooms.length === 0) {
            roomsContainer.innerHTML =
          '<div class="alert alert-info">No hay habitaciones disponibles con ese nombre</div>';
        return;
      }
      let html = "";
      data.total_rooms.forEach((rt) => {
            const typeRooms = data.rooms.filter(
              (r) => r.room_type_id === rt.room_type_id,
        );
        html += `
          <div class="card mb-3">
            <div id="room-type-${rt.room_type_id}-container" class="card-header">
              <div class="col h5">
                <span>Habitación: </span>
                <span>${rt.room_type_name}</span>
              </div>
              <div class="col">
                <span>Disponibles: </span>
                <span>${rt.total}</span>
              </div>
              <a
                class="btn btn-link"
                data-bs-toggle="collapse"
                href="#collapse-room-${rt.room_type_id}"
              >
                Seleccionar habitaciones disponibles
              </a>
            </div>
            <div
              id="collapse-room-${rt.room_type_id}"
              class="card-body collapse"
              data-bs-parent="#rooms-accordion"
            >
              <div class="card-body">
                <div id="room-type-${rt.room_type_id}-details">
                  ${typeRooms .map( (room) => `
                  <div class="card card-body row mb-2 hover-card bg-tr-250">
                    <div class="row">
                      ${this.escapeHtml ? this.escapeHtml(room.name) : room.name}
                    </div>
                    <div class="row">
                      <div class="col">Tipo de habitación: ${room.room_type_name}</div>
                      <div class="col">Capacidad: ${room.max_guests} persona/s</div>
                      <div class="col">Precio por noche: € ${room.price}</div>
                    </div>
                    <div class="row">
                      <div class="col">
                        Precio total: € ${room.total} x ${data.total_days} día/s
                      </div>
                    </div>
                    <div class="row">
                      <div class="col">
                        <a
                          class="btn btn-outline-primary btn-sm"
                          href="/booking/${room.id}/?{{ url_query }}"
                        >
                          Elegir habitación
                        </a>
                      </div>
                    </div>
                  </div>
                  `, ) .join("")}
                </div>
              </div>
            </div>
          </div>
          `;
      });
      roomsContainer.innerHTML = html;
      // Reinicializar los collapse de Bootstrap
      if (typeof bootstrap !== "undefined") {
            document
          .querySelectorAll('[data-bs-toggle="collapse"]')
          .forEach((el) => {
                el.removeAttribute("data-bs-toggle");
            el.setAttribute("data-bs-toggle", "collapse");
          });
      }
    })
    .catch((error) => {
          console.error("Error:", error);
      roomsContainer.innerHTML =
        '<div class="alert alert-danger">Error al cargar las habitaciones</div>';
    });
}
if (filterBtn) {
      filterBtn.onclick = () => {
        console.log("Filter button clicked");
    updateRooms(nameInput.value);
  };
}
if (clearBtn) {
      clearBtn.onclick = () => {
        nameInput.value = "";
    updateRooms("");
  };
}
if (nameInput) {
      nameInput.onkeypress = (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
      updateRooms(nameInput.value);
    }
  };
}
// Función auxiliar para escapar HTML (opcional)
function escapeHtml(text) {
      const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
