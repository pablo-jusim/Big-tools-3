// ------------------------------------
// Big Tools - Chatbot (Conectado a FastAPI)
// ------------------------------------

// Elementos del DOM
const chatWindow = document.getElementById("chat-window");
// URL base de tu API
const API_URL = "http://127.0.0.1:8000/api";

// Estado de la sesión (para saber a qué máquina/categoría avanzar)
let sessionState = {
  maquina: null,
  categoria: null,
};

// -----------------------------------------
// FUNCIÓN PRINCIPAL PARA AGREGAR MENSAJES
// -----------------------------------------
function addMessage(text, sender = "bot") {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);
  messageDiv.innerHTML = text; // Usamos innerHTML para renderizar <strong>, <ul>, etc.
  chatWindow.appendChild(messageDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return messageDiv;
}

// -----------------------------------------
// FUNCIÓN PARA MOSTRAR BOTONES
// -----------------------------------------
function addOptions(options, callback) {
  const optionsWrapper = document.createElement("div");
  optionsWrapper.classList.add("bot-options");

  if (options.length === 0) {
    addMessage("⚠️ No hay más opciones. Contacte a soporte.");
    return;
  }

  options.forEach((opt) => {
    const btn = document.createElement("button");
    btn.classList.add("option-btn");
    btn.textContent = opt;
    btn.onclick = () => {
      // Añadir mensaje del usuario
      addMessage(opt, "user");
      // Eliminar los botones actuales
      optionsWrapper.remove();
      // Ejecutar callback
      callback(opt);
    };
    optionsWrapper.appendChild(btn);
  });

  chatWindow.appendChild(optionsWrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// -----------------------------------------
// MANEJO DE RESPUESTAS DE LA API
// -----------------------------------------
function handleApiResponse(response) {
  // Caso 1: Es una pregunta con opciones
  if (response.pregunta && response.opciones) {
    addMessage(response.pregunta);
    addOptions(response.opciones, handleOptionSelection);
  }
  // Caso 2: Es un resultado final (falla)
  else if (response.falla && response.soluciones) {
    let solHTML = `<strong>Falla detectada:</strong> ${response.falla}<br>`;
    solHTML += "<strong>Soluciones sugeridas:</strong><ul>";
    response.soluciones.forEach((sol) => {
      solHTML += `<li>${sol}</li>`;
    });
    solHTML += "</ul>";
    
    if (response.referencia) {
        solHTML += `<br><em>(Ref: ${response.referencia})</em>`;
    }
    
    addMessage(solHTML);
    // Ofrecer reinicio
    addOptions(["🔁 Consultar otra máquina"], startChat);
  }
  // Caso 3: Es un mensaje simple o error
  else {
    addMessage(response.mensaje || "Error inesperado en la respuesta.");
    addOptions(["🔁 Consultar otra máquina"], startChat);
  }
}

// -----------------------------------------
// PASO 1: BIENVENIDA Y ELECCIÓN DE MÁQUINA
// -----------------------------------------
async function startChat() {
  // --- LÍNEA AGREGADA ---
  chatWindow.innerHTML = ""; // Limpia la ventana de chat
  // --- FIN LÍNEA AGREGADA ---

  addMessage("👋 ¡Bienvenido a Big Tools! Elige la máquina sobre la que quieres consultar:");
  
  try {
    const response = await fetch(`${API_URL}/maquinas`);
    if (!response.ok) throw new Error("No se pudo obtener la lista de máquinas.");
    
    const data = await response.json();
    sessionState = { maquina: null, categoria: null }; // Reiniciar sesión
    addOptions(data.maquinas, handleMachineSelection);

  } catch (error) {
    addMessage(`⚠️ Error al conectarse con el servidor para obtener máquinas. ${error.message}`);
  }
}

// -----------------------------------------
// PASO 2: ELECCIÓN DE CATEGORÍA
// -----------------------------------------
async function handleMachineSelection(machine) {
  sessionState.maquina = machine;
  addMessage(`Elegiste <strong>${machine}</strong>. Ahora selecciona una categoría:`);

  try {
    const response = await fetch(`${API_URL}/categorias/${machine}`);
    if (!response.ok) throw new Error("No se pudo obtener la lista de categorías.");

    const data = await response.json();
    addOptions(data.categorias, handleCategorySelection);

  } catch (error) {
    addMessage(`⚠️ Error al obtener categorías: ${error.message}`);
  }
}

// -----------------------------------------
// PASO 3: INICIAR DIAGNÓSTICO
// -----------------------------------------
async function handleCategorySelection(category) {
  sessionState.categoria = category;
  addMessage(`Iniciando diagnóstico para: <strong>${category}</strong>`);

  try {
    const response = await fetch(
      `${API_URL}/diagnosticar/iniciar/${sessionState.maquina}/${sessionState.categoria}`,
      {
        method: "POST",
      }
    );
    
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al iniciar diagnóstico.");

    handleApiResponse(data);

  } catch (error) {
    addMessage(`⚠️ Error: ${error.message}`);
    addOptions(["🔁 Consultar otra máquina"], startChat);
  }
}

// -----------------------------------------
// PASO 4: AVANZAR DIAGNÓSTICO
// -----------------------------------------
async function handleOptionSelection(respuesta) {
  if (!sessionState.maquina || !sessionState.categoria) {
    addMessage("⚠️ Error de sesión. Por favor, reinicia.");
    startChat();
    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/diagnosticar/avanzar/${sessionState.maquina}/${sessionState.categoria}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ respuesta: respuesta }), // Enviar respuesta como JSON
      }
    );

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al avanzar.");

    handleApiResponse(data);

  } catch (error) {
    addMessage(`⚠️ Error: ${error.message}`);
    addOptions(["🔁 Consultar otra máquina"], startChat);
  }
}

// -----------------------------------------
// INICIO AUTOMÁTICO DEL CHAT
// -----------------------------------------
document.addEventListener("DOMContentLoaded", startChat);