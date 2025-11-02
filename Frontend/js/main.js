// main.js
// TODO el código debe estar dentro de este bloque
document.addEventListener("DOMContentLoaded", () => {

    //------------------------------------
    // Elementos del DOM
    //------------------------------------
    const chatWindow = document.getElementById("chat-window");
    const resetBtn = document.getElementById("reset-button");
    const manualBtn = document.getElementById("manual-add-button");
    const manualBtnFalla = document.getElementById("manual-add-falla");
    const manualBtnSol = document.getElementById("manual-add-solucion");
    const adminButton = document.getElementById("admin-button");

    // URL base de tu API
    const API_URL = "http://127.0.0.1:8000/api";
    // ID de sesión (simplificado, coincide con el backend)
    const ID_SESION = "default_user";

    //------------------------------------
    // Variables de Estado (Tu lógica)
    //------------------------------------

    /**
     * Almacena la etapa actual del chat para controlar la UI
     * @type {string} Valores: "maquina", "sintoma", "falla"
     */
    let sessionState = '';

    /**
     * Acumula el estado del diagnóstico (el "path" seguido)
     * Usado para mostrar contexto en las ventanas de agregado manual.
     * @type {{maquina: string|null, sintomas: string[], falla_actual: string|null}}
     */
    let cum_state = {
        maquina: null,
        sintomas: [], // El path de atributos seleccionados
        falla_actual: null
    };

    //------------------------------------
    // Función para actualizar botones manuales
    //------------------------------------
    /**
     * Actualiza la visibilidad y el texto de los botones de "Agregar Manualmente"
     * según la etapa actual del diagnóstico.
     * @param {string} etapa - La etapa actual ("maquina", "sintoma", "falla").
     */
    function actualizarBotonManual(etapa) {
        // Ocultar todos primero
        manualBtn.style.display = "none";
        manualBtnFalla.style.display = "none";
        manualBtnSol.style.display = "none";

        if (etapa === "maquina") {
            manualBtn.textContent = "Agregar máquina manualmente";
            manualBtn.style.display = "inline-block";
        } else if (etapa === "sintoma") {
            manualBtn.textContent = "Agregar síntoma manualmente";
            manualBtn.style.display = "inline-block";
        } else if (etapa === "falla") {
            manualBtn.style.display = "none"; // Ocultar el botón genérico
            manualBtnFalla.style.display = "inline-block";
            manualBtnSol.style.display = "inline-block";
        }
    }

    //-----------------------------------------
    // Funciones de Chat (addMessage, addOptions)
    //-----------------------------------------
    
    /**
     * Agrega un mensaje a la ventana del chat.
     * @param {string} text - El contenido del mensaje (puede ser HTML).
     * @param {string} [sender="bot"] - El remitente ("bot" o "user").
     * @returns {HTMLElement} El elemento div del mensaje creado.
     */
    function addMessage(text, sender = "bot") {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        messageDiv.innerHTML = text;
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll al fondo
        return messageDiv;
    }

    /**
     * Muestra una lista de opciones como botones clickeables en el chat.
     * @param {string[]} options - Un array de strings con el texto de cada opción.
     * @param {Function} callback - La función que se ejecutará al hacer clic en un botón,
     * pasando la opción seleccionada como argumento.
     */
    function addOptions(options, callback) {
        const optionsWrapper = document.createElement("div");
        optionsWrapper.classList.add("bot-options");

        if (options.length === 0) {
            addMessage("⚠️ No hay más opciones. Contacte a soporte.");
            actualizarBotonManual("falla"); // Si no hay más opciones, es una falla
            return;
        }

        options.forEach((opt) => {
            const btn = document.createElement("button");
            btn.classList.add("option-btn");
            btn.textContent = opt;
            btn.onclick = () => {
                addMessage(opt, "user"); // Muestra la elección del usuario
                optionsWrapper.remove(); // Elimina los botones
                callback(opt); // Ejecuta la siguiente acción (ej. handleOptionSelection)
            };
            optionsWrapper.appendChild(btn);
        });
        chatWindow.appendChild(optionsWrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    //-----------------------------------------
    // MANEJO DE RESPUESTAS DE LA API
    //-----------------------------------------
    
    /**
     * Procesa la respuesta del backend (engine.py) y decide qué mostrar.
     * Es el despachador principal de la UI del chat.
     * @param {object} response - El objeto JSON de la respuesta del backend.
     */
    function handleApiResponse(response) {
        // Caso 1: El backend devuelve una pregunta y opciones.
        if (response.pregunta && response.opciones) {
            addMessage(response.pregunta);
            // Muestra las opciones y define que al hacer clic se llame a `handleOptionSelection`
            addOptions(response.opciones, handleOptionSelection);
            
            // Actualizar estado de UI
            sessionState = "sintoma";
            actualizarBotonManual(sessionState);
        }
        // Caso 2: El backend devuelve una falla final.
        else if (response.falla && response.soluciones) {
            let solHTML = `<strong>Falla detectada:</strong> ${response.falla}<br>`;
            solHTML += "<strong>Soluciones sugeridas:</strong><ul>";
            response.soluciones.forEach((sol) => {
                solHTML += `<li>${sol}</li>`;
            });
            solHTML += "</ul>";
            if (response.referencia) {
                solHTML += `<em>(Ref: ${response.referencia})</em>`;
            }
            addMessage(solHTML);

            // Actualizar estado de UI
            sessionState = "falla";
            cum_state.falla_actual = response.falla; // Guardar la falla para el contexto
            actualizarBotonManual(sessionState); // Mostrar botones "Agregar Falla/Solución"
            
            addOptions(["🔁 Consultar otra máquina"], startChat);
        }
        // Caso 3: El backend devuelve un mensaje de error o algo inesperado.
        else {
            addMessage(response.mensaje || "Error inesperado en la respuesta.");
            addOptions(["🔁 Consultar otra máquina"], startChat);
        }
    }

    //-----------------------------------------
    // PASO 1: BIENVENIDA Y ELECCIÓN DE MÁQUINA
    //-----------------------------------------
    
    /**
     * Inicia el chat. Limpia la ventana, reinicia los estados,
     * muestra el saludo y obtiene la lista de máquinas del backend.
     */
    async function startChat() {
        chatWindow.innerHTML = "";
        
        // Reiniciar estados
        sessionState = 'maquina';
        cum_state = { maquina: null, sintomas: [], falla_actual: null };
        
        addMessage("👋 ¡Bienvenido a Big Tools! Elige la máquina sobre la que quieres consultar:");
        actualizarBotonManual(sessionState); // Mostrar "Agregar máquina"

        try {
            const response = await fetch(`${API_URL}/maquinas`);
            if (!response.ok) throw new Error("No se pudo obtener la lista de máquinas.");
            const data = await response.json();
            
            // Muestra las máquinas y define que al hacer clic se llame a `handleMachineSelection`
            addOptions(data.maquinas, handleMachineSelection); 
        } catch (error) {
            addMessage(`⚠️ Error al conectarse con el servidor. ${error.message}`);
        }
    }

    //-----------------------------------------
    // PASO 2: INICIAR DIAGNÓSTICO
    //-----------------------------------------
    
    /**
     * Se llama después de que el usuario selecciona una máquina.
     * Guarda la máquina en el estado y llama al endpoint /iniciar
     * para obtener la *primera pregunta* del diagnóstico.
     * @param {string} machineName - El nombre de la máquina seleccionada.
     */
    async function handleMachineSelection(machineName) {
        // Acumular estado
        cum_state.maquina = machineName;
        // Actualizar etapa de sesión
        sessionState = 'sintoma'; 
        
        addMessage(`Iniciando diagnóstico para: <strong>${machineName}</strong>`);
        actualizarBotonManual(sessionState); // Mostrar "Agregar síntoma"

        try {
            // Llama a la ruta /iniciar (como en tu backend simplificado)
            const response = await fetch(
                `${API_URL}/diagnosticar/iniciar/${encodeURIComponent(machineName)}`,
                { method: "POST" }
            );
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Error al iniciar diagnóstico.");
            
            // La respuesta de /iniciar es la primera pregunta.
            // La pasamos al manejador de respuestas.
            handleApiResponse(data); 
        } catch (error) {
            addMessage(`⚠️ Error: ${error.message}`);
            addOptions(["🔁 Consultar otra máquina"], startChat);
        }
    }

    //-----------------------------------------
    // PASO 3: AVANZAR DIAGNÓSTICO
    //-----------------------------------------
    
    /**
     * Se llama CADA VEZ que el usuario selecciona un síntoma (opción).
     * Acumula el síntoma en el estado y llama al endpoint /avanzar
     * para obtener la *siguiente pregunta* o la *falla final*.
     * @param {string} respuesta - El texto del síntoma (opción) seleccionado.
     */
    async function handleOptionSelection(respuesta) {
        // Acumular estado (el síntoma seleccionado)
        cum_state.sintomas.push(respuesta);
        // La etapa sigue siendo "sintoma"
        sessionState = 'sintoma'; 

        if (!cum_state.maquina) { // Chequeo de seguridad
            addMessage("⚠️ Error de sesión (no hay máquina). Por favor, reinicia.");
            startChat();
            return;
        }
        
        try {
            // Llama a la ruta /avanzar con el ID_SESION
            const response = await fetch(
                `${API_URL}/diagnosticar/avanzar/${ID_SESION}`, 
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ respuesta: respuesta })
                }
            );
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Error al avanzar.");
            
            // Procesa la *siguiente* pregunta o la *falla final*
            handleApiResponse(data); 
        } catch (error) {
            addMessage(`⚠️ Error: ${error.message}`);
            addOptions(["🔁 Consultar otra máquina"], startChat);
        }
    }

    //-----------------------------------------
    // LÓGICA PARA BOTONES MANUALES (Ventanas Emergentes)
    //-----------------------------------------

    /**
     * Función genérica para abrir la ventana emergente de agregado manual.
     * Lee las variables 'sessionState' y 'cum_state' para construir el formulario.
     * @param {string} etapa - La etapa que disparó el evento ("maquina", "sintoma", "falla", "solucion").
     */
    function abrirVentanaManual(etapa) {
        const popup = window.open("", `Agregar${etapa}`, "width=500,height=500,scrollbars=yes,resizable=yes");
        if (!popup) {
            alert("Por favor, habilite las ventanas emergentes para esta página.");
            return;
        }
        
        popup.document.write("<html><head><title>Agregar Conocimiento</title>");
        // (Opcional: puedes linkear un CSS simple aquí)
        popup.document.write("</head><body>");
        popup.document.write("<h2>Agregar Nuevo Conocimiento</h2>");
        
        let formHTML = `<form id="addForm">`;

        // --- 1. Mostrar Contexto (usando cum_state) ---
        // Esta sección muestra el "camino" que el usuario ha seguido
        formHTML += "<h4>Contexto Actual:</h4>";
        if (!cum_state.maquina) {
            formHTML += "<p>No se ha seleccionado máquina.</p>";
        } else {
            formHTML += `<p><strong>Máquina:</strong> ${cum_state.maquina}</p>`;
        }
        
        if (cum_state.sintomas && cum_state.sintomas.length > 0) {
            formHTML += `<p><strong>Síntomas seguidos:</strong></p><ol>`;
            cum_state.sintomas.forEach(s => { formHTML += `<li>${s}</li>` });
            formHTML += `</ol>`;
        }

        // Si estamos agregando una solución, mostramos la falla actual
        if (etapa === "solucion" && cum_state.falla_actual) {
             formHTML += `<p><strong>Falla actual:</strong> ${cum_state.falla_actual}</p>`;
        }
        
        formHTML += "<hr><h4>Datos a Agregar:</h4>";

        // --- 2. Mostrar Formulario (según la 'etapa') ---
        if (etapa === "maquina") {
            formHTML += `<label for="nombre">Nombre de la nueva máquina:</label><br>`;
            formHTML += `<input type="text" id="nombre" name="nombre" required style="width: 90%;"><br>`;
        
        } else if (etapa === "sintoma") {
            formHTML += `<p>Agregando un nuevo síntoma (opción) bajo la última pregunta.</p>`;
            formHTML += `<label for="atributo">Texto del nuevo síntoma (la opción):</label><br>`;
            formHTML += `<input type="text" id="atributo" name="atributo" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="pregunta">Pregunta que hará el bot si se elige este síntoma:</label><br>`;
            formHTML += `<input type="text" id="pregunta" name="pregunta" required style="width: 90%;"><br>`;
        
        } else if (etapa === "falla") {
            formHTML += `<p>Agregando una nueva falla (diagnóstico) bajo la última pregunta.</p>`;
            formHTML += `<label for="atributo">Texto del síntoma (la opción que lleva a esta falla):</label><br>`;
            formHTML += `<input type="text" id="atributo" name="atributo" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="falla">Descripción de la falla (el diagnóstico):</label><br>`;
            formHTML += `<input type="text" id="falla" name="falla" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="soluciones">Soluciones (separadas por coma ','):</label><br>`;
            formHTML += `<textarea id="soluciones" name="soluciones" rows="3" style="width: 90%;"></textarea><br><br>`;
            formHTML += `<label for="referencia">Referencia (opcional):</label><br>`;
            formHTML += `<input type="text" id="referencia" name="referencia" style="width: 90%;"><br>`;
        
        } else if (etapa === "solucion") {
            formHTML += `<p>Agregando una nueva solución a la falla actual.</p>`;
            formHTML += `<label for="solucion">Texto de la nueva solución:</label><br>`;
            formHTML += `<input type="text" id="solucion" name="solucion" required style="width: 90%;"><br>`;
        }

        formHTML += `<br><button type="submit">Guardar</button>`;
        formHTML += `</form>`;
        popup.document.write(formHTML);
        popup.document.write("</body></html>");

        // --- 3. Manejar el envío (POST al backend) ---
        // Asigna el listener al formulario DENTRO de la popup
        popup.document.getElementById("addForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            
            let url = "";
            let body = {};
            
            try {
                // Construir la URL y el cuerpo del POST según la etapa
                if (etapa === "maquina") {
                    url = `${API_URL}/agregar/maquina`;
                    body = {
                        nombre: popup.document.getElementById("nombre").value
                    };
                } else if (etapa === "sintoma") {
                    url = `${API_URL}/agregar/sintoma/${ID_SESION}`;
                    body = {
                        atributo: popup.document.getElementById("atributo").value,
                        pregunta: popup.document.getElementById("pregunta").value
                    };
                } else if (etapa === "falla") {
                    url = `${API_URL}/agregar/falla/${ID_SESION}`;
                    const solucionesInput = popup.document.getElementById("soluciones").value;
                    body = {
                        atributo: popup.document.getElementById("atributo").value,
                        falla: popup.document.getElementById("falla").value,
                        soluciones: solucionesInput.split(',').map(s => s.trim()).filter(s => s.length > 0),
                        referencia: popup.document.getElementById("referencia").value || null
                    };
                } else if (etapa === "solucion") {
                    url = `${API_URL}/agregar/solucion/${ID_SESION}`;
                    body = {
                        solucion_nueva: popup.document.getElementById("solucion").value
                    };
                }

                // Enviar los datos al backend (routes.py)
                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(body)
                });
                
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Error desconocido");
                
                // Avisar en el chat principal y cerrar popup
                addMessage(`✅ ${data.message}`, "bot");
                popup.close();
                
                // Reiniciar el chat para que se vean los cambios
                startChat(); 
                
            } catch (error) {
                popup.alert(`Error al guardar: ${error.message}`);
            }
        });
    }

    //-----------------------------------------
    // INICIO Y LISTENERS
    //-----------------------------------------
    
    // Asigna los listeners a los botones
    resetBtn.addEventListener("click", startChat);
    
    // Asignar los nuevos botones manuales
    manualBtn.addEventListener("click", () => {
        // sessionState me dice qué tipo de formulario mostrar ("maquina" o "sintoma")
        abrirVentanaManual(sessionState); 
    });
    manualBtnFalla.addEventListener("click", () => {
        abrirVentanaManual("falla");
    });
    manualBtnSol.addEventListener("click", () => {
        abrirVentanaManual("solucion");
    });
    
    // (Listener para el botón de admin (login)
    // adminButton.addEventListener("click", () => { ... });

    // Inicia el chat
    startChat();

}); // <-- FIN DEL DOMContentLoaded

