// ------------------------------------
// Big Tools - Panel de Administración
// admin.js
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

// -----------------------------------------
// GESTIÓN DE AUTENTICACIÓN
// -----------------------------------------

// Verificar si hay sesión activa al cargar la página
function verificarSesion() {
  const token = localStorage.getItem("chatbot_token");
  const username = localStorage.getItem("chatbot_username");
  const role = localStorage.getItem("chatbot_role");

  if (!token || !username) {
    // No hay sesión, redirigir al login principal
    alert("ADVERTENCIA: Debes iniciar sesión primero");
    window.location.href = "/";
    return;
  }

  // Verificar que sea admin
  if (role !== "admin") {
    alert("ACCESO DENEGADO: Solo administradores pueden acceder al dashboard.");
    window.location.href = "/";
    return;
  }

  // Usuario admin autenticado, mostrar dashboard
  mostrarDashboard(username);
  cargarEstadisticas();
}

function mostrarDashboard(username) {
  dashboard.style.display = "block";
  usernameDisplay.textContent = `Usuario: ${username}`;
}

// -----------------------------------------
// MANEJO DE LOGOUT
// -----------------------------------------

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

    // Limpiar localStorage
    localStorage.removeItem("chatbot_token");
    localStorage.removeItem("chatbot_username");
    localStorage.removeItem("chatbot_role");

    // Redirigir al login principal
    window.location.href = "/";
  }
});

// -----------------------------------------
// CARGAR ESTADÍSTICAS
// -----------------------------------------

async function cargarEstadisticas() {
  const token = localStorage.getItem("chatbot_token");

  if (!token) {
    alert("ADVERTENCIA: Sesión expirada");
    window.location.href = "/";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/admin/stats`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Error al cargar estadísticas");
    }

    const stats = await response.json();

    // Actualizar las estadísticas en el DOM
    actualizarEstadisticas(stats);
    
  } catch (error) {
    console.error("Error al cargar estadísticas:", error);
    alert("ERROR: No se pudieron cargar las estadísticas");
  }
}

// -----------------------------------------
// ACTUALIZAR ESTADÍSTICAS EN EL DOM
// -----------------------------------------

function actualizarEstadisticas(stats) {
  // Guardar estadísticas globalmente para exportar a PDF
  estadisticasActuales = stats;
  
  // Total de diagnósticos
  document.getElementById("total-diagnosticos").textContent =
    stats.total_diagnosticos || 0;

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

  // Top categorías
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
  
  // Crear gráficos con un pequeño delay para asegurar que el DOM esté listo
  setTimeout(() => {
    crearGraficos(stats);
  }, 100);
}

// -----------------------------------------
// GRAFICOS CON CHART.JS
// -----------------------------------------

let chartMaquinas, chartCategorias, chartTendencia;

function crearGraficos(stats) {
  // Verificar que Chart.js esté cargado
  if (typeof Chart === 'undefined') {
    return;
  }

  // Destruir gráficos anteriores si existen
  if (chartMaquinas) chartMaquinas.destroy();
  if (chartCategorias) chartCategorias.destroy();
  if (chartTendencia) chartTendencia.destroy();

  // Verificar que los canvas existan
  const canvasMaquinas = document.getElementById('chartMaquinas');
  const canvasCategorias = document.getElementById('chartCategorias');
  const canvasTendencia = document.getElementById('chartTendencia');
  
  if (!canvasMaquinas || !canvasCategorias || !canvasTendencia) {
    return;
  }

  // Gráfico de Máquinas (Barras)
  const ctxMaquinas = canvasMaquinas.getContext('2d');
  const maquinasData = stats.top_maquinas || [];
  
  chartMaquinas = new Chart(ctxMaquinas, {
    type: 'bar',
    data: {
      labels: maquinasData.map(item => item.maquina),
      datasets: [{
        label: 'Diagnosticos',
        data: maquinasData.map(item => item.cantidad),
        backgroundColor: [
          'rgba(211, 47, 47, 0.7)',
          'rgba(33, 33, 33, 0.7)',
          'rgba(245, 124, 0, 0.7)',
          'rgba(56, 142, 60, 0.7)'
        ],
        borderColor: [
          'rgba(211, 47, 47, 1)',
          'rgba(33, 33, 33, 1)',
          'rgba(245, 124, 0, 1)',
          'rgba(56, 142, 60, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      }
    }
  });

  // Gráfico de Categorías (Dona)
  const ctxCategorias = canvasCategorias.getContext('2d');
  const categoriasData = stats.top_categorias || [];
  
  chartCategorias = new Chart(ctxCategorias, {
    type: 'doughnut',
    data: {
      labels: categoriasData.map(item => item.categoria),
      datasets: [{
        data: categoriasData.map(item => item.cantidad),
        backgroundColor: [
          'rgba(211, 47, 47, 0.7)',
          'rgba(33, 33, 33, 0.7)',
          'rgba(245, 124, 0, 0.7)',
          'rgba(56, 142, 60, 0.7)',
          'rgba(25, 118, 210, 0.7)'
        ],
        borderColor: [
          'rgba(211, 47, 47, 1)',
          'rgba(33, 33, 33, 1)',
          'rgba(245, 124, 0, 1)',
          'rgba(56, 142, 60, 1)',
          'rgba(25, 118, 210, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right'
        }
      }
    }
  });

  // Gráfico de Tendencia (Línea)
  const ctxTendencia = canvasTendencia.getContext('2d');
  const historialData = stats.historial_reciente || [];
  
  // Agrupar por fecha
  const diagnosticosPorFecha = {};
  historialData.forEach(item => {
    const fecha = new Date(item.timestamp).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    diagnosticosPorFecha[fecha] = (diagnosticosPorFecha[fecha] || 0) + 1;
  });
  
  // Ordenar fechas cronológicamente
  const fechasOrdenadas = Object.keys(diagnosticosPorFecha).sort((a, b) => {
    const [diaA, mesA, anioA] = a.split('/');
    const [diaB, mesB, anioB] = b.split('/');
    return new Date(anioA, mesA - 1, diaA) - new Date(anioB, mesB - 1, diaB);
  });
  
  // Tomar las últimas 10 fechas
  const fechas = fechasOrdenadas.slice(-10);
  const cantidades = fechas.map(fecha => diagnosticosPorFecha[fecha]);
  
  // Si no hay datos, mostrar un punto de ejemplo
  if (fechas.length === 0) {
    fechas.push('Sin datos');
    cantidades.push(0);
  }
  
  // Determinar el tipo de gráfico según la cantidad de datos
  const tipoGrafico = fechas.length === 1 ? 'bar' : 'line';
  
  chartTendencia = new Chart(ctxTendencia, {
    type: tipoGrafico,
    data: {
      labels: fechas,
      datasets: [{
        label: 'Diagnosticos',
        data: cantidades,
        borderColor: 'rgba(211, 47, 47, 1)',
        backgroundColor: tipoGrafico === 'bar' ? 'rgba(211, 47, 47, 0.8)' : 'rgba(211, 47, 47, 0.1)',
        tension: 0.3,
        fill: true,
        pointBackgroundColor: 'rgba(211, 47, 47, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 3,
        pointRadius: 8,
        pointHoverRadius: 10,
        borderWidth: 3,
        barThickness: 80
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            precision: 0
          },
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.1)'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      }
    }
  });
}

// -----------------------------------------
// UTILIDADES
// -----------------------------------------

function formatearFecha(isoString) {
  const fecha = new Date(isoString);
  const dia = String(fecha.getDate()).padStart(2, "0");
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const anio = fecha.getFullYear();
  const horas = String(fecha.getHours()).padStart(2, "0");
  const minutos = String(fecha.getMinutes()).padStart(2, "0");
  return `${dia}/${mes}/${anio} ${horas}:${minutos}`;
}

// -----------------------------------------
// BOTÓN DE ACTUALIZACIÓN
// -----------------------------------------

refreshButton.addEventListener("click", async () => {
  const token = localStorage.getItem("chatbot_token");
  if (token) {
    // Deshabilitar botón y mostrar feedback
    refreshButton.disabled = true;
    refreshButton.textContent = "Actualizando...";
    
    try {
      await cargarEstadisticas();
      
      // Mostrar mensaje de éxito
      refreshButton.textContent = "Actualizado";
      refreshButton.style.backgroundColor = "#4caf50";
      
      // Restaurar botón después de 1 segundo
      setTimeout(() => {
        refreshButton.textContent = "Actualizar Estadísticas";
        refreshButton.style.backgroundColor = "";
        refreshButton.disabled = false;
      }, 1000);
      
    } catch (error) {
      // Mostrar error
      refreshButton.textContent = "Error al actualizar";
      refreshButton.style.backgroundColor = "#f44336";
      
      setTimeout(() => {
        refreshButton.textContent = "Actualizar Estadísticas";
        refreshButton.style.backgroundColor = "";
        refreshButton.disabled = false;
      }, 2000);
    }
  } else {
    alert("No hay sesión activa. Por favor, inicie sesión.");
  }
});

// -----------------------------------------
// GESTIÓN DE PESTAÑAS
// -----------------------------------------

function inicializarPestanas() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      // Remover clase active de todos los botones y contenidos
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      // Agregar clase active al botón clickeado
      btn.classList.add("active");

      // Mostrar el contenido correspondiente
      const tabName = btn.getAttribute("data-tab");
      const tabContent = document.getElementById(`tab-${tabName}`);
      if (tabContent) {
        tabContent.classList.add("active");
      }

      // Si se abre la pestaña de manuales, cargar la lista
      if (tabName === "manuales") {
        cargarListaManuales();
      }
    });
  });
}

// -----------------------------------------
// GESTIÓN DE MANUALES
// -----------------------------------------

function cargarListaManuales() {
  const manualesLista = document.getElementById("manuales-lista");
  
  // Manuales actuales (simulado - en producción vendría del backend)
  const manuales = [
    {
      nombre: "HIDROLAVADORA.pdf",
      maquina: "Hidrolavadora Kärcher",
      tamano: "2.5 MB",
      fecha: "2024-01-15"
    },
    {
      nombre: "Generac_Manual_Usuario_Guardian_Series (1).pdf",
      maquina: "Generador Generac Guardian",
      tamano: "8.3 MB",
      fecha: "2024-01-10"
    },
    {
      nombre: "MANUAL CUMMINS 2.pdf",
      maquina: "Motor Cummins",
      tamano: "15.7 MB",
      fecha: "2024-01-05"
    },
    {
      nombre: "ranger_305d.pdf",
      maquina: "Soldadora Miller Ranger 305D",
      tamano: "4.2 MB",
      fecha: "2024-01-01"
    }
  ];

  if (manuales.length === 0) {
    manualesLista.innerHTML = "<p class='no-data'>No hay manuales disponibles</p>";
    return;
  }

  manualesLista.innerHTML = manuales
    .map(
      (manual) => `
    <div class="manual-item">
      <div class="manual-info">
        <h4>${manual.nombre}</h4>
        <p>Máquina: ${manual.maquina} | Tamaño: ${manual.tamano} | Fecha: ${manual.fecha}</p>
      </div>
      <div class="manual-actions">
        <button class="manual-btn view" onclick="abrirManual('${manual.nombre}')">
          Ver
        </button>
        <button class="manual-btn delete" onclick="confirmarEliminarManual('${manual.nombre}')">
          Eliminar
        </button>
      </div>
    </div>
  `
    )
    .join("");
}

function abrirManual(nombreArchivo) {
  const rutaPDF = `/manuales/${nombreArchivo}`;
  window.open(rutaPDF, "_blank");
}

function confirmarEliminarManual(nombreArchivo) {
  if (confirm(`¿Estás seguro de que deseas eliminar el manual "${nombreArchivo}"?\n\nEsta acción no se puede deshacer.`)) {
    eliminarManual(nombreArchivo);
  }
}

function eliminarManual(nombreArchivo) {
  // En producción, esto haría una petición al backend
  alert(`Funcionalidad de eliminación:\n\nPara eliminar el manual "${nombreArchivo}", ve a:\nBackend/data/manuales_pdf/\n\ny elimina el archivo manualmente.`);
  
  // Recargar la lista
  cargarListaManuales();
}

// -----------------------------------------
// SUBIDA DE MANUALES
// -----------------------------------------

function inicializarFormularioSubida() {
  const form = document.getElementById("upload-manual-form");
  const statusDiv = document.getElementById("upload-status");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nombreManual = document.getElementById("manual-nombre").value.trim();
    const fileInput = document.getElementById("manual-file");
    const descripcion = document.getElementById("manual-descripcion").value.trim();
    const file = fileInput.files[0];

    if (!nombreManual) {
      mostrarEstadoSubida("error", "Por favor ingresa el nombre del manual");
      return;
    }

    if (!file) {
      mostrarEstadoSubida("error", "Por favor selecciona un archivo PDF");
      return;
    }

    if (file.type !== "application/pdf") {
      mostrarEstadoSubida("error", "Solo se permiten archivos PDF");
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      // 50MB
      mostrarEstadoSubida("error", "El archivo es demasiado grande (máximo 50MB)");
      return;
    }

    // Mostrar progreso
    mostrarEstadoSubida("info", "Subiendo archivo...");
    const uploadBtn = form.querySelector(".upload-btn");
    uploadBtn.disabled = true;

    // Simular subida (en producción, esto sería una petición al backend)
    setTimeout(() => {
      mostrarEstadoSubida(
        "success",
        `Manual "${file.name}" subido correctamente para "${nombreManual}"`
      );
      
      // Mostrar instrucciones
      setTimeout(() => {
        mostrarEstadoSubida(
          "info",
          `El archivo se guardó en: Backend/data/manuales_pdf/${file.name}\n\n` +
          `Nombre del manual: ${nombreManual}\n` +
          (descripcion ? `Descripción: ${descripcion}\n\n` : '\n') +
          `Para que esté disponible en el sistema, copia manualmente el archivo a esa ubicación.`
        );
      }, 2000);

      // Limpiar formulario
      form.reset();
      uploadBtn.disabled = false;

      // Recargar lista
      setTimeout(() => {
        cargarListaManuales();
      }, 3000);
    }, 2000);
  });
}

function mostrarEstadoSubida(tipo, mensaje) {
  const statusDiv = document.getElementById("upload-status");
  statusDiv.className = `upload-status ${tipo}`;
  statusDiv.textContent = mensaje;
  statusDiv.style.display = "block";
}

function getNombreAmigable(nombreTecnico) {
  const nombres = {
    hidrolavadora_karcher: "Hidrolavadora Kärcher",
    generador_generac: "Generador Generac Guardian",
    motor_cummins: "Motor Cummins",
    soldadora_miller_ranger: "Soldadora Miller Ranger 305D"
  };
  return nombres[nombreTecnico] || nombreTecnico;
}

// -----------------------------------------
// EXPORTAR ESTADÍSTICAS A PDF
// -----------------------------------------

async function exportarEstadisticasAPDF() {
  if (!estadisticasActuales) {
    alert("No hay estadisticas disponibles. Por favor, actualiza primero.");
    return;
  }

  if (typeof jspdf === 'undefined') {
    alert("Cargando libreria PDF...");
    return;
  }

  const { jsPDF } = jspdf;
  const doc = new jsPDF();
  let y = 20;

  // Título principal
  doc.setFontSize(22);
  doc.setTextColor(211, 47, 47);
  doc.text("Big Tools - Reporte de Estadisticas", 20, y);
  y += 5;

  // Línea separadora
  doc.setDrawColor(211, 47, 47);
  doc.setLineWidth(0.5);
  doc.line(20, y, 190, y);
  y += 10;

  // Fecha y hora del reporte
  doc.setFontSize(10);
  doc.setTextColor(100, 100, 100);
  const fecha = new Date().toLocaleString('es-ES');
  doc.text(`Generado: ${fecha}`, 20, y);
  y += 10;

  // Total de diagnósticos
  doc.setFontSize(16);
  doc.setTextColor(0, 0, 0);
  doc.text("Resumen General", 20, y);
  y += 8;

  doc.setFontSize(12);
  doc.text(`Total de Diagnosticos: ${estadisticasActuales.total_diagnosticos || 0}`, 20, y);
  y += 12;

  // Top Máquinas
  doc.setFontSize(14);
  doc.setTextColor(211, 47, 47);
  doc.text("Maquinas Mas Consultadas", 20, y);
  y += 8;

  doc.setFontSize(11);
  doc.setTextColor(0, 0, 0);
  if (estadisticasActuales.top_maquinas && estadisticasActuales.top_maquinas.length > 0) {
    estadisticasActuales.top_maquinas.forEach((item, index) => {
      doc.text(`${index + 1}. ${item.maquina}: ${item.cantidad} consultas`, 25, y);
      y += 6;
    });
  } else {
    doc.text("No hay datos disponibles", 25, y);
    y += 6;
  }
  y += 6;

  // Top Categorías
  doc.setFontSize(14);
  doc.setTextColor(211, 47, 47);
  doc.text("Categorias Mas Consultadas", 20, y);
  y += 8;

  doc.setFontSize(11);
  doc.setTextColor(0, 0, 0);
  if (estadisticasActuales.top_categorias && estadisticasActuales.top_categorias.length > 0) {
    estadisticasActuales.top_categorias.forEach((item, index) => {
      const categoriaTexto = `${index + 1}. ${item.categoria}: ${item.cantidad} consultas`;
      const lineas = doc.splitTextToSize(categoriaTexto, 170);
      lineas.forEach(linea => {
        if (y > 270) {
          doc.addPage();
          y = 20;
        }
        doc.text(linea, 25, y);
        y += 6;
      });
    });
  } else {
    doc.text("No hay datos disponibles", 25, y);
    y += 6;
  }
  y += 6;

  // Verificar si necesitamos nueva página para el historial
  if (y > 200) {
    doc.addPage();
    y = 20;
  }

  // Historial Reciente
  doc.setFontSize(14);
  doc.setTextColor(211, 47, 47);
  doc.text("Historial Reciente", 20, y);
  y += 8;

  doc.setFontSize(9);
  doc.setTextColor(0, 0, 0);
  
  if (estadisticasActuales.historial_reciente && estadisticasActuales.historial_reciente.length > 0) {
    // Encabezados de tabla
    doc.setFont("helvetica", "bold");
    doc.text("Fecha", 20, y);
    doc.text("Maquina", 55, y);
    doc.text("Categoria", 120, y);
    y += 6;
    doc.setFont("helvetica", "normal");

    // Línea debajo de encabezados
    doc.setDrawColor(200, 200, 200);
    doc.setLineWidth(0.3);
    doc.line(20, y - 2, 190, y - 2);

    // Filas de datos
    estadisticasActuales.historial_reciente.slice(0, 20).forEach((item) => {
      if (y > 270) {
        doc.addPage();
        y = 20;
      }

      const fechaObj = new Date(item.timestamp);
      const fechaFormato = fechaObj.toLocaleDateString('es-ES', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      doc.text(fechaFormato, 20, y);
      
      const maquinaTexto = doc.splitTextToSize(item.maquina || "N/A", 60);
      doc.text(maquinaTexto[0], 55, y);
      
      const categoriaTexto = doc.splitTextToSize(item.categoria || "N/A", 65);
      doc.text(categoriaTexto[0], 120, y);
      
      y += 6;
    });
  } else {
    doc.text("No hay historial disponible", 25, y);
  }

  // Pie de página
  const totalPages = doc.internal.pages.length - 1;
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.text(`Pagina ${i} de ${totalPages}`, 170, 285);
    doc.text("Big Tools - Sistema Experto de Diagnostico", 20, 285);
  }

  // Guardar el PDF
  const nombreArchivo = `estadisticas_bigtools_${Date.now()}.pdf`;
  doc.save(nombreArchivo);
}

// Event listener para el botón de exportar PDF
if (exportPdfButton) {
  exportPdfButton.addEventListener("click", exportarEstadisticasAPDF);
}

// -----------------------------------------
// INICIALIZACIÓN
// -----------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  verificarSesion();
  inicializarPestanas();
  inicializarFormularioSubida();
});

