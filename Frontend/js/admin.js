// ------------------------------------
// Big Tools - Panel de Administración
// admin.js robusto y seguro + UI relogueo en botones
// ------------------------------------

const API_URL = "http://127.0.0.1:8000/api";

// Elementos del DOM
const dashboard = document.getElementById("dashboard");
const usernameDisplay = document.getElementById("username-display");
const logoutButton = document.getElementById("logout-button");
const refreshButton = document.getElementById("refresh-button");
const exportPdfButton = document.getElementById("export-pdf-button");

// Variable global para almacenar las estadísticas actuales
let estadisticasActuales = null;

// ------ Helper para forzar relogueo en botones ------
function forzarReLoginSiSesionInvalida(mensajeExtra = "") {
  const aviso = "Debes volver a iniciar sesión para usar esta función." + (mensajeExtra ? "\n\n" + mensajeExtra : "");
  if (confirm(aviso + "\n¿Deseas cerrar la sesión ahora?")) {
    localStorage.removeItem('chatbot_token');
    localStorage.removeItem('chatbot_username');
    localStorage.removeItem('chatbot_role');
    window.location.href = "/";
    return true;
  }
  return false; // Si cancela
}

// ------ Protección de Botones Clave -------
function protegerBotonPorId(botonId, mensaje) {
  const btn = document.getElementById(botonId);
  if (btn) {
    btn.onclick = (e) => {
      const token = localStorage.getItem("chatbot_token");
      const username = localStorage.getItem("chatbot_username");
      if (!token || !username) {
        forzarReLoginSiSesionInvalida(mensaje);
        e.preventDefault();
        return false;
      }
      // Si la sesión es válida, sigue con la lógica normal (customizar aquí si necesitas)
    };
  }
}

// Panel admin (por si vuelves a dashboard)
protegerBotonPorId("admin-button", "Para ver el Panel de Administración debes volver a iniciar sesión.");

// Botones de agregar
protegerBotonPorId("manual-add-button", "Debes volver a iniciar sesión para agregar una máquina.");
protegerBotonPorId("manual-add-sintoma", "Debes volver a iniciar sesión para agregar un síntoma.");
protegerBotonPorId("manual-add-falla", "Debes volver a iniciar sesión para agregar una falla.");
protegerBotonPorId("manual-add-solucion", "Debes volver a iniciar sesión para agregar una solución.");

// ------ GESTIÓN DE AUTENTICACIÓN -------
function verificarSesion() {
  const token = localStorage.getItem("chatbot_token");
  const username = localStorage.getItem("chatbot_username");
  const role = localStorage.getItem("chatbot_role");

  if (!token || !username) {
    forzarReLoginSiSesionInvalida("No hay sesión activa.");
    return;
  }

  if (role !== "admin") {
    forzarReLoginSiSesionInvalida("Solo administradores pueden acceder al dashboard.");
    return;
  }

  mostrarDashboard(username);
  cargarEstadisticas();
}

function mostrarDashboard(username) {
  dashboard.style.display = "block";
  usernameDisplay.textContent = `Usuario: ${username}`;
}

// ------ MANEJO DE LOGOUT -------
logoutButton.addEventListener("click", async () => {
  if (confirm("¿Deseas cerrar sesión y volver al chatbot?")) {
    const token = localStorage.getItem("chatbot_token");
    if (token) {
      try {
        await fetch(`${API_URL}/admin/logout`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });
      } catch (error) {
        console.error("Error al cerrar sesión:", error);
      }
    }
    localStorage.removeItem("chatbot_token");
    localStorage.removeItem("chatbot_username");
    localStorage.removeItem("chatbot_role");
    window.location.href = "/";
  }
});

// ------ CARGAR ESTADÍSTICAS -------
async function cargarEstadisticas() {
  const token = localStorage.getItem("chatbot_token");
  if (!token) {
    forzarReLoginSiSesionInvalida("Sesión expirada.");
    return;
  }
  try {
    const response = await fetch(`${API_URL}/admin/stats`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Error al cargar estadísticas");
    const stats = await response.json();
    actualizarEstadisticas(stats);
  } catch (error) {
    console.error("Error al cargar estadísticas:", error);
    alert("ERROR: No se pudieron cargar las estadísticas");
  }
}

// ------ ACTUALIZAR ESTADÍSTICAS EN EL DOM -------
function actualizarEstadisticas(stats) {
  estadisticasActuales = stats;
  document.getElementById("total-diagnosticos").textContent = stats.total_diagnosticos || 0;
  // Top máquinas
  const topMaquinasDiv = document.getElementById("top-maquinas");
  if (stats.top_maquinas && stats.top_maquinas.length > 0) {
    topMaquinasDiv.innerHTML = stats.top_maquinas
      .map(
        (item, index) => `
        <div class="stat-item">
          <span class="stat-rank">${index + 1}.</span>
          <span class="stat-name">${item.maquina}</span>
          <span class="stat-value">${item.cantidad} consultas</span>
        </div>
      `
      )
      .join("");
  } else {
    topMaquinasDiv.innerHTML = "<p class='no-data'>No hay datos disponibles</p>";
  }
  // Top categorías/fallas
  const topCategoriasDiv = document.getElementById("top-categorias");
  if (stats.top_categorias && stats.top_categorias.length > 0) {
    topCategoriasDiv.innerHTML = stats.top_categorias
      .map(
        (item, index) => `
        <div class="stat-item">
          <span class="stat-rank">${index + 1}.</span>
          <span class="stat-name">${item.categoria}</span>
          <span class="stat-detail">(${item.maquina})</span>
          <span class="stat-value">${item.cantidad} consultas</span>
        </div>
      `
      )
      .join("");
  } else {
    topCategoriasDiv.innerHTML = "<p class='no-data'>No hay datos disponibles</p>";
  }
  // Historial reciente
  const historialDiv = document.getElementById("historial-reciente");
  if (stats.historial_reciente && stats.historial_reciente.length > 0) {
    historialDiv.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Fecha/Hora</th>
            <th>Máquina</th>
            <th>Categoría</th>
            <th>Estado</th>
            <th>Falla Detectada</th>
          </tr>
        </thead>
        <tbody>
          ${stats.historial_reciente
            .map(
              (item) => `
            <tr>
              <td>${formatearFecha(item.timestamp)}</td>
              <td>${item.maquina}</td>
              <td>${item.categoria}</td>
              <td>
                <span class="badge ${item.completado ? "completed" : "pending"}">
                  ${item.completado ? "Completado" : "En proceso"}
                </span>
              </td>
              <td>${item.falla || "-"}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;
  } else {
    historialDiv.innerHTML = "<p class='no-data'>No hay historial disponible</p>";
  }
  setTimeout(() => {
    crearGraficos(stats);
  }, 100);
}

// ------ GRAFICOS CON CHART.JS etc. ------
/* (NO CAMBIAN, el resto de tu admin.js va aquí: 
    - crearGraficos
    - utilidades
    - exportar a PDF, inicialización, etc)
*/

// Botón Actualizar
refreshButton.addEventListener("click", async () => {
  const token = localStorage.getItem("chatbot_token");
  if (!token) {
    forzarReLoginSiSesionInvalida("No hay sesión activa.");
    return;
  }
  refreshButton.disabled = true;
  refreshButton.textContent = "Actualizando...";
  try {
    await cargarEstadisticas();
    refreshButton.textContent = "Actualizado";
    refreshButton.style.backgroundColor = "#4caf50";
    setTimeout(() => {
      refreshButton.textContent = "Actualizar Estadísticas";
      refreshButton.style.backgroundColor = "";
      refreshButton.disabled = false;
    }, 1000);
  } catch (error) {
    refreshButton.textContent = "Error al actualizar";
    refreshButton.style.backgroundColor = "#f44336";
    setTimeout(() => {
      refreshButton.textContent = "Actualizar Estadísticas";
      refreshButton.style.backgroundColor = "";
      refreshButton.disabled = false;
    }, 2000);
  }
});

// ------ INICIALIZACIÓN ------
document.addEventListener("DOMContentLoaded", () => {
  verificarSesion();
  // inicializarPestanas();
  // inicializarFormularioSubida();
});
