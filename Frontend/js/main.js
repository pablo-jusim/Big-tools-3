/**
 * main.js - Controlador completo 2025
 * Manejo de sesión, autenticación y edición manual con popups
 * FIX: Los botones admin/manuales solo funcionan si la sesión ES válida en backend.
 */

document.addEventListener("DOMContentLoaded", () => {
    // ---- Elementos del DOM ----
    const chatWindow     = document.getElementById("chat-window");
    const resetBtn       = document.getElementById("reset-button");
    const manualBtn      = document.getElementById("manual-add-button");
    const manualBtnFalla = document.getElementById("manual-add-falla");
    const manualBtnSol   = document.getElementById("manual-add-solucion");
    const adminButton    = document.getElementById("admin-button");
    const logoutBtn      = document.getElementById("logout-button");

    // API y Sesión
    const API_URL  = "http://127.0.0.1:8000/api";
    const ID_SESION = "default_user";
    let sessionAdmin = { token: null, username: null, role: null };
    let sessionState = '';   // "maquina", "sintoma", "falla"
    let cum_state = { maquina: null, sintomas: [], falla_actual: null };
    let datosFallaNueva = null, datosFallaExistente = null;

    // ========== SESIÓN Y LOGIN / LOGOUT ROBUSTOS =========
    function recuperarSesion() {
        sessionAdmin.token = localStorage.getItem('chatbot_token');
        sessionAdmin.username = localStorage.getItem('chatbot_username');
        sessionAdmin.role = localStorage.getItem('chatbot_role') || 'tecnico';
        return (sessionAdmin.token && sessionAdmin.username);
    }
    function sesionInvalida() {
        return !(sessionAdmin.token && sessionAdmin.username);
    }
    function cerrarSesionTotal(mensaje = null) {
        localStorage.clear();
        sessionAdmin = { token: null, username: null, role: null };
        sessionState = '';
        chatWindow.innerHTML = '';
        if (mensaje) alert(mensaje);
        mostrarLogin();
    }
    function forzarReLoginSiSesionInvalida(mensajeExtra = "") {
        const aviso = "Debes volver a iniciar sesión para usar esta función." + (mensajeExtra ? "\n\n" + mensajeExtra : "");
        if (confirm(aviso + "\n¿Deseas cerrar la sesión ahora?")) {
            cerrarSesionTotal();
            return true;
        }
        return false;
    }
    function mostrarLogin() {
        document.getElementById('login-modal').style.display = 'flex';
        document.getElementById('main-container').style.display = 'none';
    }
    function mostrarChatbot() {
        document.getElementById('login-modal').style.display = 'none';
        document.getElementById('main-container').style.display = 'block';
        document.getElementById('user-display').textContent = `Usuario: ${sessionAdmin.username}`;
        adminButton.style.display = sessionAdmin.role === 'admin' ? 'inline-block' : 'none';
        if (chatWindow.children.length === 0) startChat();
    }
    function headersAdmin() {
        return sessionAdmin.token
            ? { "Content-Type": "application/json", "Authorization": `Bearer ${sessionAdmin.token}` }
            : { "Content-Type": "application/json" };
    }

    // ========== VALIDA SESIÓN CON BACKEND ==========
    async function validarSesionConBackend() {
        if (sesionInvalida()) return false;
        try {
            const res = await fetch(`${API_URL}/admin/stats`, {
                method: 'GET',
                headers: headersAdmin()
            });
            if (res.status === 401 || res.status === 403) return false;
            return true;
        } catch {
            return false;
        }
    }

    // ========== PROTECCIÓN ROBUSTA DE BOTONES ==========
    function protegerBotonAsync(boton, mensaje, accionSiValida) {
        if (!boton) return;
        boton.onclick = async (e) => {
            recuperarSesion();
            const esValida = await validarSesionConBackend();
            if (!esValida) {
                cerrarSesionTotal(mensaje);
                e.preventDefault();
                return false;
            }
            if (typeof accionSiValida === "function") accionSiValida();
        };
    }
    protegerBotonAsync(
        adminButton,
        "Para ver el Panel de Administración debes volver a iniciar sesión.",
        () => { window.location.href = "/admin"; }
    );
    protegerBotonAsync(
        manualBtn,
        "Debes volver a iniciar sesión para agregar una máquina.",
        () => abrirVentanaAgregarSimple(sessionState)
    );
    protegerBotonAsync(
        manualBtnFalla,
        "Debes volver a iniciar sesión para agregar una falla.",
        abrirVentanaAgregarFalla_Paso1
    );
    protegerBotonAsync(
        manualBtnSol,
        "Debes volver a iniciar sesión para agregar una solución.",
        () => {
            if (sessionState !== 'falla') {
                alert("Solo puede agregar una solución cuando se ha diagnosticado una falla.");
                return;
            }
            abrirVentanaAgregarSolucion();
        }
    );

    // ========== LOGIN Y LOGOUT =========
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorMsg = document.getElementById('login-error');
        try {
            const response = await fetch(`${API_URL}/login_admin`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok && data.token) {
                localStorage.setItem('chatbot_token', data.token);
                localStorage.setItem('chatbot_username', username);
                localStorage.setItem('chatbot_role', data.role || 'tecnico');
                errorMsg.textContent = '';
                recuperarSesion();
                mostrarChatbot();
            } else {
                errorMsg.textContent = 'Error: Usuario o contraseña incorrectos';
            }
        } catch (error) {
            errorMsg.textContent = 'Error: No se pudo conectar con el servidor';
        }
    });
    if (logoutBtn) logoutBtn.addEventListener("click", cerrarSesion);

    function cerrarSesion() {
        if (confirm('¿Estás seguro de que deseas cerrar sesión?')) {
            fetch(`${API_URL}/logout_admin`, {
                method: 'POST',
                headers: {'Authorization': `Bearer ${sessionAdmin.token}` }
            }).catch(() => { });
            cerrarSesionTotal();
        }
    }

    // ========== FLUJO PRINCIPAL Y POPUPS IGUAL QUE SIEMPRE =========
    function actualizarBotonManual(etapa) {
        manualBtn.style.display       = "none";
        manualBtnFalla.style.display = "none";
        manualBtnSol.style.display   = "none";
        if (sessionAdmin.role !== "admin") return;
        if (etapa === "maquina") {
            manualBtn.textContent = "Agregar máquina manualmente";
            manualBtn.style.display = "inline-block";
        } else if (etapa === "sintoma") {
            manualBtn.textContent = "Agregar síntoma manualmente";
            manualBtn.style.display = "inline-block";
        } else if (etapa === "falla") {
            manualBtnFalla.style.display = "inline-block";
            manualBtnSol.style.display   = "inline-block";
        }
    }

    function addMessage(text, sender = "bot") {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        messageDiv.innerHTML = text;
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
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
        options.forEach(opt => {
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
    function handleApiResponse(response) {
        datosFallaNueva = null;
        datosFallaExistente = null;
        if (response.pregunta && response.opciones) {
            addMessage(response.pregunta);
            addOptions(response.opciones, handleOptionSelection);
            sessionState = "sintoma";
            actualizarBotonManual(sessionState);
        }
        else if (response.falla && response.soluciones) {
            let solHTML = `<strong>Falla detectada:</strong> ${response.falla}<br>`;
            solHTML += "<strong>Soluciones sugeridas:</strong><ul>";
            response.soluciones.forEach(sol => { solHTML += `<li>${sol}</li>`; });
            solHTML += "</ul>";
            if (response.referencia)
                solHTML += `<em>(Ref: ${response.referencia})</em>`;
            addMessage(solHTML);
            sessionState = "falla";
            cum_state.falla_actual = response.falla;
            datosFallaExistente = {
                falla: response.falla,
                soluciones: response.soluciones,
                referencia: response.referencia
            };
            actualizarBotonManual(sessionState);
            addOptions(["🔁 Consultar otra máquina"], startChat);
        }
        else {
            addMessage(response.mensaje || "Error inesperado en la respuesta.");
            addOptions(["🔁 Consultar otra máquina"], startChat);
        }
    }
    async function startChat() {
        chatWindow.innerHTML = "";
        sessionState = 'maquina';
        cum_state = { maquina: null, sintomas: [], falla_actual: null };
        datosFallaNueva = null;
        datosFallaExistente = null;
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
    async function handleMachineSelection(machineName) {
        cum_state.maquina = machineName;
        cum_state.sintomas = [];
        sessionState = 'sintoma';
        addMessage(`Iniciando diagnóstico para: <strong>${machineName}</strong>`);
        actualizarBotonManual(sessionState);
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
    async function handleOptionSelection(respuesta) {
        cum_state.sintomas.push(respuesta);
        sessionState = 'sintoma';
        actualizarBotonManual(sessionState);
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
    // === Popups y edición manual, completos ===
    function getAgregarSimpleFormHTML(etapa) {
        let formHTML = `<form id="addForm">`;
        formHTML += "<h4>Contexto Actual:</h4>";
        if (!cum_state.maquina && etapa !== "maquina") {
            formHTML += "<p>No se ha seleccionado máquina.</p>";
        } else if (cum_state.maquina) {
            formHTML += `<p><strong>Máquina:</strong> ${cum_state.maquina}</p>`;
        }
        if (cum_state.sintomas.length > 0 && etapa !== "maquina") {
            formHTML += `<p><strong>Síntomas seguidos:</strong></p><ol>${cum_state.sintomas.map(s => `<li>${s}</li>`).join('')}</ol>`;
        }
        formHTML += "<hr><h4>Datos a Agregar:</h4>";
        if (etapa === "maquina") {
            formHTML += `<label for="nombre">Nombre de la nueva máquina:</label><br>`;
            formHTML += `<input type="text" id="nombre" name="nombre" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="atributo">Primer síntoma principal (atributo):</label><br>`;
            formHTML += `<input type="text" id="atributo" name="atributo" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="falla">Primera falla (descripción):</label><br>`;
            formHTML += `<input type="text" id="falla" name="falla" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="soluciones">Soluciones (separadas por coma ','):</label><br>`;
            formHTML += `<textarea id="soluciones" name="soluciones" rows="3" style="width: 90%;"></textarea><br>`;
            formHTML += `<label for="referencia">Referencia (opcional):</label><br>`;
            formHTML += `<input type="text" id="referencia" name="referencia" style="width: 90%;"><br>`;
        } else if (etapa === "sintoma") {
            formHTML += `<label for="atributo">Texto de la opción (atributo):</label><br>`;
            formHTML += `<input type="text" id="atributo" name="atributo" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="falla">Descripción de la falla (diagnóstico terminal):</label><br>`;
            formHTML += `<input type="text" id="falla" name="falla" required style="width: 90%;"><br><br>`;
            formHTML += `<label for="soluciones">Soluciones (separadas por coma ','):</label><br>`;
            formHTML += `<textarea id="soluciones" name="soluciones" rows="3" style="width: 90%;"></textarea><br>`;
            formHTML += `<label for="referencia">Referencia (opcional):</label><br>`;
            formHTML += `<input type="text" id="referencia" name="referencia" style="width: 90%;"><br>`;
        }
        formHTML += `<br><button type="submit">Guardar</button>`;
        formHTML += `</form>`;
        return formHTML;
    }
    function abrirVentanaAgregarSimple(etapa) {
        const popup = window.open("", `Agregar${etapa}`, "width=500,height=600,scrollbars=yes,resizable=yes");
        if (!popup) { alert("Por favor, habilite las ventanas emergentes."); return; }
        popup.document.write("<html><head><title>Agregar Conocimiento</title></head><body>");
        popup.document.write("<h2>Agregar Nuevo Conocimiento</h2>");
        popup.document.write(getAgregarSimpleFormHTML(etapa));
        popup.document.getElementById("addForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            let url = "", body = {};
            function referenciaFinal(userRefValue) {
                let userValue = userRefValue ? userRefValue.trim() : "";
                return userValue ? ("Ingresado por usuario: " + userValue) : "Ingresado por usuario";
            }
            if (etapa === "maquina") {
                url = `${API_URL}/agregar/maquina`;
                let atributo = popup.document.getElementById("atributo").value;
                let falla    = popup.document.getElementById("falla").value;
                let soluciones = popup.document.getElementById("soluciones").value.split(',').map(s => s.trim()).filter(s => s);
                let nombre   = popup.document.getElementById("nombre").value;
                let refUser  = popup.document.getElementById("referencia").value;
                let referencia = referenciaFinal(refUser);
                body = {
                    nombre: nombre,
                    primer_rama: {
                        atributo: atributo,
                        falla: falla,
                        soluciones: soluciones,
                        referencia: referencia
                    }
                };
            } else if (etapa === "sintoma") {
                url = `${API_URL}/agregar/sintoma/${ID_SESION}`;
                let refUser  = popup.document.getElementById("referencia").value;
                let referencia = referenciaFinal(refUser);
                body = {
                    atributo: popup.document.getElementById("atributo").value,
                    falla: popup.document.getElementById("falla").value,
                    soluciones: popup.document.getElementById("soluciones").value.split(',').map(s => s.trim()).filter(s => s),
                    referencia: referencia
                };
            }
            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: headersAdmin(),
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Error desconocido");
                addMessage(`✅ ${data.message}`, "bot");
                popup.close();
                startChat();
            } catch (error) {
                popup.alert(`Error al guardar: ${error.message}`);
            }
        });
    }
    function abrirVentanaAgregarFalla_Paso1() {
        if (!cum_state.falla_actual || !datosFallaExistente) {
            alert("Para restructurar debe estar viendo una falla existente.");
            return;
        }
        const popup = window.open("", "AgregarFalla", "width=500,height=500,scrollbars=yes,resizable=yes");
        if (!popup) { alert("Por favor, habilite las ventanas emergentes."); return; }
        popup.document.write("<html><head><title>Agregar Falla (Paso 1 de 2)</title></head><body>");
        popup.document.write("<h2>Agregar Nueva Falla (Paso 1 de 2)</h2>");
        let formHTML = `<form id="addFallaForm">`;
        formHTML += "<h4>Contexto Actual:</h4>";
        formHTML += `<p><strong>Máquina:</strong> ${cum_state.maquina}</p>`;
        if (cum_state.sintomas.length > 0) {
            formHTML += `<p><strong>Síntomas seguidos:</strong></p><ol>${cum_state.sintomas.map(s => `<li>${s}</li>`).join('')}</ol>`;
        }
        formHTML += "<hr><h4>Datos de la Nueva Falla:</h4>";
        formHTML += `<label for="atributo">Texto del síntoma (la opción que llevará a esta nueva falla):</label><br>`;
        formHTML += `<input type="text" id="atributo" name="atributo" required style="width: 90%;"><br><br>`;
        formHTML += `<label for="falla">Descripción de la falla (el diagnóstico):</label><br>`;
        formHTML += `<input type="text" id="falla" name="falla" required style="width: 90%;"><br><br>`;
        formHTML += `<label for="soluciones">Soluciones (separadas por coma ','):</label><br>`;
        formHTML += `<textarea id="soluciones" name="soluciones" rows="3" style="width: 90%;"></textarea><br><br>`;
        formHTML += `<label for="referencia">Referencia (opcional):</label><br>`;
        formHTML += `<input type="text" id="referencia" name="referencia" style="width: 90%;"><br>`;
        formHTML += `<br><button type="submit">Siguiente (Preguntar)</button>`;
        formHTML += `</form></body></html>`;
        popup.document.write(formHTML);
        popup.document.getElementById("addFallaForm").addEventListener("submit", (e) => {
            e.preventDefault();
            let refUser  = popup.document.getElementById("referencia").value;
            let referencia = refUser && refUser.trim() ? ("Ingresado por usuario: " + refUser.trim()) : "Ingresado por usuario";
            datosFallaNueva = {
                falla: popup.document.getElementById("falla").value,
                soluciones: popup.document.getElementById("soluciones").value.split(',').map(s => s.trim()).filter(s => s),
                referencia: referencia,
                atributo: popup.document.getElementById("atributo").value
            };
            abrirVentanaRestructura_Paso2(popup);
        });
    }
    function abrirVentanaRestructura_Paso2(popup) {
        popup.document.body.innerHTML = "";
        popup.document.title = "Restructurar Falla (Paso 2 de 2)";
        let formHTML = `<h2>Restructurar Falla (Paso 2 de 2)</h2>`;
        formHTML += "<h4>Contexto Actual:</h4>";
        formHTML += `<p><strong>Máquina:</strong> ${cum_state.maquina}</p>`;
        formHTML += `<p><strong>Síntomas seguidos:</strong></p><ol>${cum_state.sintomas.map(s => `<li>${s}</li>`).join('')}</ol>`;
        let fallaExistenteTexto = cum_state.falla_actual || "la falla existente";
        formHTML += `<p>El síntoma <strong>"${cum_state.sintomas[cum_state.sintomas.length - 1]}"</strong> tiene asociada la falla: <strong>"${fallaExistenteTexto}"</strong>.</p>`;
        formHTML += "<hr><h4>Construir nueva pregunta y opciones:</h4>";
        formHTML += `<form id="restructuraForm">`;
        formHTML += `<label for="pregunta_nueva"><strong>1. Nueva pregunta diferenciadora:</strong></label><br>`;
        formHTML += `<input type="text" id="pregunta_nueva" required style="width: 90%;"><br><br>`;
        formHTML += `<label for="atributo_existente"><strong>2. Opción para la falla EXISTENTE:</strong></label><br>`;
        formHTML += `<input type="text" id="atributo_existente" required style="width: 90%;" value=""><br><br>`;
        formHTML += `<label for="atributo_nuevo"><strong>3. Opción para la nueva falla:</strong></label><br>`;
        formHTML += `<input type="text" id="atributo_nuevo" value="${datosFallaNueva.atributo}" required style="width: 90%;"><br><br>`;
        formHTML += `<br><button type="submit">Guardar restructuración</button>`;
        formHTML += `</form>`;
        popup.document.body.innerHTML = formHTML;
        popup.document.getElementById("restructuraForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            const body = {
                pregunta_nueva: popup.document.getElementById("pregunta_nueva").value,
                atributo_existente: popup.document.getElementById("atributo_existente").value,
                falla_existente: datosFallaExistente.falla,
                soluciones_existente: datosFallaExistente.soluciones,
                referencia_existente: datosFallaExistente.referencia,
                atributo_nuevo: popup.document.getElementById("atributo_nuevo").value,
                falla_nueva: datosFallaNueva.falla,
                soluciones_nuevas: datosFallaNueva.soluciones,
                referencia_nueva: datosFallaNueva.referencia
            };
            const url = `${API_URL}/restructurar/falla/${ID_SESION}`;
            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: headersAdmin(),
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Error desconocido");
                addMessage(`✅ ${data.message}`, "bot");
                datosFallaNueva = null;
                datosFallaExistente = null;
                popup.close();
                startChat();
            } catch (error) {
                popup.alert(`Error al guardar restructuración: ${error.message}`);
            }
        });
    }
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
        popup.document.getElementById("addForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            const body = { solucion_nueva: popup.document.getElementById("solucion").value };
            const url = `${API_URL}/agregar/solucion/${ID_SESION}`;
            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: headersAdmin(),
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Error desconocido");
                addMessage(`✅ ${data.message}`, "bot");
                popup.close();
                startChat();
            } catch (error) {
                popup.alert(`Error al guardar: ${error.message}`);
            }
        });
    }
    if (resetBtn) resetBtn.addEventListener("click", () => startChat());
});
