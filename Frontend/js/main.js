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
     * @type {{maquina: string|null, sintomas: string[], falla_actual: string|null}}
     */
    let cum_state = {
        maquina: null,
        sintomas: [], // El path de atributos seleccionados
        falla_actual: null
    };

    /**
     * Almacena temporalmente los datos de una falla nueva
     * durante el proceso de restructuración.
     * @type {object|null}
     */
    let datosFallaNueva = null;


    //------------------------------------
    // Función para actualizar botones manuales
    //------------------------------------
    /**
     * Actualiza la visibilidad y el texto de los botones de "Agregar Manualmente".
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
        // Si la etapa es "cargando", todos los botones permanecen ocultos.
    }

    //-----------------------------------------
    // Funciones de Chat (addMessage, addOptions)
    //-----------------------------------------
    
    /**
     * Agrega un mensaje a la ventana del chat.
     * @param {string} text - El contenido del mensaje (puede ser HTML).
     * @param {string} [sender="bot"] - El remitente ("bot" o "user").
     */
    function addMessage(text, sender = "bot") {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        messageDiv.innerHTML = text;
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    /**
     * Muestra una lista de opciones como botones clickeables en el chat.
     * @param {string[]} options - Un array de strings con el texto de cada opción.
     * @param {Function} callback - La función que se ejecutará al hacer clic en un botón.
     */
    function addOptions(options, callback) {
        const optionsWrapper = document.createElement("div");
        optionsWrapper.classList.add("bot-options");

        if (!options || options.length === 0) {
            addMessage("⚠️ No hay más opciones de diagnóstico. Puede agregar una falla o solución manualmente.");
            sessionState = "falla"; 
            actualizarBotonManual(sessionState);
            addOptions(["🔁 Consultar otra máquina"], startChat);
            return;
        }

        options.forEach((opt) => {
            const btn = document.createElement("button");
            btn.classList.add("option-btn");
            btn.textContent = opt;
            btn.onclick = () => {
                addMessage(opt, "user"); 
                optionsWrapper.remove(); 
                callback(opt); 
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
     * @param {object} response - El objeto JSON de la respuesta del backend.
     */
    function handleApiResponse(response) {
        datosFallaNueva = null; // Limpiar conflicto en cualquier respuesta exitosa

        if (response.pregunta && response.opciones) {
            addMessage(response.pregunta);
            addOptions(response.opciones, handleOptionSelection);
            sessionState = "sintoma";
            actualizarBotonManual(sessionState);
        }
        else if (response.falla && response.soluciones) {
            let solHTML = `<strong>Falla detectada:</strong> ${response.falla}<br>`;
            solHTML += "<strong>Soluciones sugeridas:</strong><ul>";
            response.soluciones.forEach((sol) => { solHTML += `<li>${sol}</li>`; });
            solHTML += "</ul>";
            if (response.referencia) {
                solHTML += `<em>(Ref: ${response.referencia})</em>`;
            }
            addMessage(solHTML);

            sessionState = "falla";
            cum_state.falla_actual = response.falla;
            actualizarBotonManual(sessionState);
            
            addOptions(["🔁 Consultar otra máquina"], startChat);
        }
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
        
        sessionState = 'maquina';
        cum_state = { maquina: null, sintomas: [], falla_actual: null };
        datosFallaNueva = null;
        
        addMessage("👋 ¡Bienvenido a Big Tools! Elige la máquina sobre la que quieres consultar:");
        actualizarBotonManual(sessionState);

        try {
            const response = await fetch(`${API_URL}/maquinas`);
            if (!response.ok) throw new Error("No se pudo obtener la lista de máquinas.");
            const data = await response.json();
            
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
     * Llama al endpoint /iniciar para obtener la *primera pregunta*.
     * @param {string} machineName - El nombre de la máquina seleccionada.
     */
    async function handleMachineSelection(machineName) {
        cum_state.maquina = machineName;
        sessionState = 'sintoma'; 
        
        addMessage(`Iniciando diagnóstico para: <strong>${machineName}</strong>`);
        actualizarBotonManual("cargando"); 

        try {
            const response = await fetch(
                `${API_URL}/diagnosticar/iniciar/${encodeURIComponent(machineName)}`,
                { method: "POST" }
            );
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Error al iniciar diagnóstico.");
            
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
     * Llama al endpoint /avanzar para obtener la *siguiente pregunta* o la *falla final*.
     * @param {string} respuesta - El texto del síntoma (opción) seleccionado.
     */
    async function handleOptionSelection(respuesta) {
        cum_state.sintomas.push(respuesta);
        sessionState = 'sintoma'; 
        actualizarBotonManual("cargando");

        if (!cum_state.maquina) {
            addMessage("⚠️ Error de sesión (no hay máquina). Por favor, reinicia.");
            startChat();
            return;
        }
        
        try {
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
     * Abre la ventana emergente para AGREGAR MÁQUINA o AGREGAR SÍNTOMA SIMPLE.
     */
    function abrirVentanaAgregarSimple(etapa) {
        const popup = window.open("", `Agregar${etapa}`, "width=500,height=500,scrollbars=yes,resizable=yes");
        if (!popup) { alert("Por favor, habilite las ventanas emergentes."); return; }
        
        popup.document.write("<html><head><title>Agregar Conocimiento</title></head><body>");
        popup.document.write("<h2>Agregar Nuevo Conocimiento</h2>");
        
        let formHTML = `<form id="addForm">`;

        // 1. Mostrar Contexto
        formHTML += "<h4>Contexto Actual:</h4>";
        if (!cum_state.maquina) {
            formHTML += "<p>No se ha seleccionado máquina.</p>";
        } else {
            formHTML += `<p><strong>Máquina:</strong> ${cum_state.maquina}</p>`;
        }
        if (cum_state.sintomas.length > 0) {
            formHTML += `<p><strong>Síntomas seguidos:</strong></p><ol>${cum_state.sintomas.map(s => `<li>${s}</li>`).join('')}</ol>`;
        }
        formHTML += "<hr><h4>Datos a Agregar:</h4>";

        // 2. Mostrar Formulario
        if (etapa === "maquina") {
            formHTML += `<label for="nombre">Nombre de la nueva máquina:</label><br>`;
            formHTML += `<input type="text" id="nombre" name="nombre" required style="width: 90%;"><br>`;
        } else if (etapa === "sintoma") {
            formHTML += `<p>Agregando un nuevo síntoma (opción) bajo la última pregunta.</p>`;
            formHTML += `<label for="atributo">Texto del nuevo síntoma (la opción):</label><br>`;
            formHTML += `<input type="text" id="atributo" name="atributo" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="pregunta">Pregunta que hará el bot si se elige este síntoma:</label><br>`;
            formHTML += `<input type="text" id="pregunta" name="pregunta" required style="width: 90%;"><br>`;
        }

        formHTML += `<br><button type="submit">Guardar</button>`;
        formHTML += `</form></body></html>`;

        // 3. Manejar el envío
        popup.document.getElementById("addForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            let url = "";
            let body = {};
            
            if (etapa === "maquina") {
                url = `${API_URL}/agregar/maquina`;
                body = { nombre: popup.document.getElementById("nombre").value };
            } else if (etapa === "sintoma") {
                url = `${API_URL}/agregar/sintoma/${ID_SESION}`;
                body = {
                    atributo: popup.document.getElementById("atributo").value,
                    pregunta: popup.document.getElementById("pregunta").value
                };
            }

            try {
                const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Error desconocido");
                
                addMessage(`✅ ${data.message}`, "bot");
                popup.close();
                startChat(); // Reiniciar
            } catch (error) {
                popup.alert(`Error al guardar: ${error.message}`);
            }
        });
    }

    /**
     * Inicia el proceso de 2 PASOS para agregar una falla.
     * PASO 1: Pide los datos de la nueva falla.
     */
    function abrirVentanaAgregarFalla_Paso1() {
        const popup = window.open("", "AgregarFalla", "width=500,height=500,scrollbars=yes,resizable=yes");
        if (!popup) { alert("Por favor, habilite las ventanas emergentes."); return; }

        popup.document.write("<html><head><title>Agregar Falla (Paso 1 de 2)</title></head><body>");
        popup.document.write("<h2>Agregar Nueva Falla (Paso 1 de 2)</h2>");
        
        let formHTML = `<form id="addFallaForm">`;

        // 1. Contexto
        formHTML += "<h4>Contexto Actual:</h4>";
        formHTML += `<p><strong>Máquina:</strong> ${cum_state.maquina}</p>`;
        if (cum_state.sintomas.length > 0) {
            formHTML += `<p><strong>Síntomas seguidos:</strong></p><ol>${cum_state.sintomas.map(s => `<li>${s}</li>`).join('')}</ol>`;
        }
        formHTML += "<hr><h4>Datos de la Nueva Falla:</h4>";
        
        // 2. Formulario (Paso 1)
        formHTML += `<p>Está agregando una nueva falla bajo la última pregunta.</p>`;
        formHTML += `<label for="atributo">Texto del síntoma (la opción que lleva a esta falla):</label><br>`;
        formHTML += `<input type="text" id="atributo" name="atributo" required style="width: 90%;"><br><br>`;
        formHTML += `<label for="falla">Descripción de la falla (el diagnóstico):</label><br>`;
        formHTML += `<input type="text" id="falla" name="falla" required style="width: 90%;"><br><br>`;
        formHTML += `<label for="soluciones">Soluciones (separadas por coma ','):</label><br>`;
        formHTML += `<textarea id="soluciones" name="soluciones" rows="3" style="width: 90%;"></textarea><br><br>`;
        formHTML += `<label for="referencia">Referencia (opcional):</label><br>`;
        formHTML += `<input type="text" id="referencia" name="referencia" style="width: 90%;"><br>`;
        
        formHTML += `<br><button type="submit">Siguiente (Verificar)</button>`;
        formHTML += `</form></body></html>`;
        popup.document.write(formHTML);

        // 3. Manejar el envío (Paso 1)
        popup.document.getElementById("addFallaForm").addEventListener("submit", async (e) => {
            e.preventDefault();

            // Guardar los datos de la nueva falla temporalmente
            const solucionesInput = popup.document.getElementById("soluciones").value;
            datosFallaNueva = {
                atributo: popup.document.getElementById("atributo").value,
                falla: popup.document.getElementById("falla").value,
                soluciones: solucionesInput.split(',').map(s => s.trim()).filter(s => s.length > 0),
                referencia: popup.document.getElementById("referencia").value || null
            };

            // ---- REVISAR CONFLICTO CON EL BACKEND ----
            // Intentamos agregarla. Si falla con 409, pasamos al Paso 2.
            try {
                const res = await fetch(`${API_URL}/agregar/falla/${ID_SESION}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(datosFallaNueva)
                });
                
                const data = await res.json();

                if (res.status === 409) {
                    // ¡CONFLICTO! El backend nos dice que ya existe una falla.
                    // Pasamos al Paso 2 de restructuración.
                    addMessage(`⚠️ **Conflicto detectado:** ${data.detail}`);
                    abrirVentanaRestructura_Paso2(popup); // Reutilizamos la misma ventana
                    return; 
                }
                
                if (!res.ok) throw new Error(data.detail || "Error desconocido");

                // Si todo OK (200), significa que era un nodo de pregunta y se agregó bien.
                addMessage(`✅ ${data.message}`, "bot");
                popup.close();
                startChat(); // Reiniciar

            } catch (error) {
                popup.alert(`Error al guardar: ${error.message}`);
            }
        });
    }

    /**
     * PASO 2 de "Agregar Falla": Restructuración.
     * Se llama cuando el backend devuelve 409.
     * @param {Window} popup - La ventana emergente que reutilizaremos.
     */
    function abrirVentanaRestructura_Paso2(popup) {
        if (!datosFallaNueva) {
            alert("Error: No se encontraron datos de la nueva falla.");
            return;
        }

        // Limpiar la ventana y construir el Paso 2
        popup.document.body.innerHTML = ""; 
        popup.document.title = "Restructurar Falla (Paso 2 de 2)";
        
        let formHTML = `<h2>Restructurar Falla (Paso 2 de 2)</h2>`;

        // 1. Contexto
        formHTML += "<h4>Contexto Actual:</h4>";
        formHTML += `<p><strong>Máquina:</strong> ${cum_state.maquina}</p>`;
        formHTML += `<p><strong>Síntomas seguidos:</strong></p><ol>${cum_state.sintomas.map(s => `<li>${s}</li>`).join('')}</ol>`;
        
        // CORRECCIÓN: Usar falla_actual (la que está en pantalla) en lugar de la del path
        let fallaExistenteTexto = cum_state.falla_actual || "la falla existente";
        
        formHTML += `<p>El síntoma <strong>"${cum_state.sintomas[cum_state.sintomas.length - 1]}"</strong> ya conduce a la falla: <strong>"${fallaExistenteTexto}"</strong>.</p>`;
        formHTML += `<p>Para agregar tu nueva falla (<strong>"${datosFallaNueva.falla}"</strong>), debes crear una pregunta que diferencie ambas.</p>`;
        formHTML += "<hr><h4>Datos de Restructuración:</h4>";
        
        // 2. Formulario de Restructuración (como lo pediste)
        formHTML += `<form id="restructuraForm">`;
        formHTML += `<p><strong>1. Falla Existente:</strong> ${fallaExistenteTexto}</p>`;
        formHTML += `<p><strong>2. Falla Nueva:</strong> ${datosFallaNueva.falla}</p><br>`;

        formHTML += `<label for="pregunta_nueva"><strong>3. Nueva Pregunta</strong> (para diferenciar ambas fallas):</label><br>`;
        formHTML += `<input type="text" id="pregunta_nueva" required style="width: 90%;"><br><br>`;
        
        formHTML += `<label for="atributo_existente"><strong>4. Opción que conduce a la Falla EXISTENTE:</strong></label><br>`;
        formHTML += `<input type="text" id="atributo_existente" placeholder="Ej: No, el cable está bien" required style="width: 90%;"><br><br>`;

        formHTML += `<label for="atributo_nuevo"><strong>5. Opción que conduce a la Falla NUEVA:</strong></label><br>`;
        formHTML += `<input type="text" id="atributo_nuevo" value="${datosFallaNueva.atributo}" required style="width: 90%;"><br><br>`;
        
        formHTML += `<br><button type="submit">Guardar Restructuración</button>`;
        formHTML += `</form>`;
        
        popup.document.body.innerHTML = formHTML;

        // 3. Manejar el envío
        popup.document.getElementById("restructuraForm").addEventListener("submit", async (e) => {
            e.preventDefault();

            // Recolectar todos los datos
            const body = {
                pregunta_nueva: popup.document.getElementById("pregunta_nueva").value,
                
                // Datos Falla Nueva (guardados en variable global)
                atributo_nuevo: popup.document.getElementById("atributo_nuevo").value,
                falla_nueva: datosFallaNueva.falla,
                soluciones_nuevas: datosFallaNueva.soluciones,
                referencia_nueva: datosFallaNueva.referencia,

                // Datos Falla Existente
                atributo_existente: popup.document.getElementById("atributo_existente").value
            };

            const url = `${API_URL}/restructurar/falla/${ID_SESION}`;

            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Error desconocido");
                
                addMessage(`✅ ${data.message}`, "bot");
                datosFallaNueva = null; // Limpiar datos temporales
                popup.close();
                startChat(); // Reiniciar
                
            } catch (error) {
                popup.alert(`Error al guardar restructuración: ${error.message}`);
            }
        });
    }

    /**
     * Abre una ventana simple para agregar una solución a la falla diagnosticada.
     */
    function abrirVentanaAgregarSolucion() {
        const popup = window.open("", "AgregarSolucion", "width=500,height=300,scrollbars=yes,resizable=yes");
        if (!popup) { alert("Por favor, habilite las ventanas emergentes."); return; }

        popup.document.write("<html><head><title>Agregar Solución</title></head><body>");
        popup.document.write("<h2>Agregar Nueva Solución</h2>");
        
        let formHTML = `<form id="addForm">`;
        formHTML += "<h4>Contexto Actual:</h4>";
        formHTML += `<p><strong>Máquina:</strong> ${cum_state.maquina}</p>`;
        formHTML += `<p><strong>Síntomas:</strong> ${cum_state.sintomas.join(' -> ')}</p>`;
        formHTML += `<p><strong>Falla actual:</strong> ${cum_state.falla_actual}</p>`;
        formHTML += "<hr><h4>Datos a Agregar:</h4>";
        formHTML += `<label for="solucion">Texto de la nueva solución:</label><br>`;
        formHTML += `<input type="text" id="solucion" name="solucion" required style="width: 90%;"><br>`;
        formHTML += `<br><button type="submit">Guardar Solución</button>`;
        formHTML += `</form></body></html>`;
        
        popup.document.write(formHTML);

        // Manejar el envío
        popup.document.getElementById("addForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const body = {
                solucion_nueva: popup.document.getElementById("solucion").value
            };
            const url = `${API_URL}/agregar/solucion/${ID_SESION}`;

            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Error desconocido");
                
                addMessage(`✅ ${data.message}`, "bot");
                popup.close();
                // No es necesario reiniciar, solo agregamos la solución al chat (opcional)
                // Opcional: actualizar el mensaje de falla en el chat
                
            } catch (error) {
                popup.alert(`Error al guardar: ${error.message}`);
            }
        });
    }

    //-----------------------------------------
    // INICIO Y LISTENERS (CORREGIDO)
    //-----------------------------------------
    
    resetBtn.addEventListener("click", startChat);
    
    // Botón genérico (Máquina o Síntoma)
    manualBtn.addEventListener("click", () => {
        // sessionState me dice qué tipo de formulario mostrar ("maquina" o "sintoma")
        abrirVentanaAgregarSimple(sessionState); 
    });
    
    // Botón de Falla (Inicia el flujo de 2 pasos)
    manualBtn.addEventListener("click", () => {
        // sessionState me dice qué tipo de formulario mostrar ("maquina" o "sintoma")
        abrirVentanaAgregarSimple(sessionState); 
    });
    
    // Botón de Falla (Inicia el flujo de 2 pasos)
    manualBtnFalla.addEventListener("click", () => {
        // --- ESTA ES LA LÓGICA CORREGIDA ---
        // Siempre llamamos al Paso 1.
        // El Paso 1 (abrirVentanaAgregarFalla_Paso1) se encargará de
        // llamar al backend y, SI hay un conflicto (409),
        // llamará a abrirVentanaRestructura_Paso2.
        abrirVentanaAgregarFalla_Paso1();
    });
    
    // Botón de Solución (Simple)
    manualBtnSol.addEventListener("click", () => {
        if (sessionState !== 'falla') {
            alert("Solo puede agregar una solución cuando se ha diagnosticado una falla.");
            return;
        }
        abrirVentanaAgregarSolucion();
    });
    
    // adminButton.addEventListener("click", () => { ... });

    // Inicia el chat al cargar la página
    startChat();

}); // <-- FIN DEL DOMContentLoaded

