// main.js
document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chat-window");
    const userInput = document.getElementById("user-input");
    const sendButton = document.querySelector("#chat-form button");
    const adminButton = document.getElementById("admin-btn");
    const chatForm = document.getElementById("chat-form");

    let step = "cargando_maquinas";
    let maquinaActual = "";
    let maquinasDisponibles = [];

    // -------------------------------------------------------
    // Agregar mensaje al chat
    // -------------------------------------------------------
    function addMessage(sender, text) {
        const msg = document.createElement("div");
        msg.classList.add("chat-message", sender); // coincide con CSS
        msg.innerText = text;
        chatWindow.appendChild(msg);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // -------------------------------------------------------
    // Mostrar select de máquinas
    // -------------------------------------------------------
    function mostrarSelectMaquinas() {
        const select = document.createElement("select");
        select.id = "select-maquina";

        maquinasDisponibles.forEach(m => {
            const option = document.createElement("option");
            option.value = m;
            option.innerText = m;
            select.appendChild(option);
        });

        const enviarBtn = document.createElement("button");
        enviarBtn.innerText = "Seleccionar";
        enviarBtn.addEventListener("click", () => {
            maquinaActual = select.value;
            addMessage("user", maquinaActual);
            addMessage("bot", `Perfecto, vamos a diagnosticar la máquina "${maquinaActual}". Ingresa el problema que detectaste:`);

            step = "pedir_problema";
            select.remove();
            enviarBtn.remove();
            userInput.disabled = false;
            userInput.focus();
        });

        chatWindow.appendChild(select);
        chatWindow.appendChild(enviarBtn);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // -------------------------------------------------------
    // Obtener máquinas desde backend
    // -------------------------------------------------------
    async function obtenerMaquinas() {
        try {
            const res = await fetch("http://127.0.0.1:8000/api/maquinas");
            const data = await res.json();
            if (data.maquinas && data.maquinas.length > 0) {
                maquinasDisponibles = data.maquinas;
                addMessage("bot", "¡Bienvenido a Big Tools! Elige la máquina sobre la que quieres consultar:");
                mostrarSelectMaquinas();
            } else {
                addMessage("bot", "No hay máquinas disponibles en la base de conocimiento.");
            }
        } catch (error) {
            addMessage("bot", "Error al conectarse con el servidor para obtener máquinas.");
            console.error(error);
        }
    }

    // -------------------------------------------------------
    // Manejar input del usuario
    // -------------------------------------------------------
    async function handleUserInput() {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage("user", text);
        userInput.value = "";

        if (step === "pedir_problema") {
            try {
                const response = await fetch(`http://127.0.0.1:8000/api/diagnosticar/${encodeURIComponent(maquinaActual)}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ problema: text })
                });

                const data = await response.json();

                if (data.resultado) {
                    mostrarResultado(data.resultado);
                } else {
                    addMessage("bot", "No se pudo determinar la falla. Intenta con otra descripción.");
                }
            } catch (error) {
                addMessage("bot", "Error al comunicarse con el servidor.");
                console.error(error);
            }
        }
    }

    // -------------------------------------------------------
    // Mostrar resultados del motor de inferencia
    // -------------------------------------------------------
    function mostrarResultado(resultado) {
        if (typeof resultado === "string") {
            addMessage("bot", resultado);
        } else if (resultado.falla) {
            addMessage("bot", `❗ Falla detectada: ${resultado.falla}`);
            if (resultado.soluciones) {
                addMessage("bot", "Posibles soluciones:");
                resultado.soluciones.forEach((s, i) => {
                    addMessage("bot", `  ${i + 1}. ${s}`);
                });
            }
        } else if (resultado.mensaje) {
            addMessage("bot", resultado.mensaje);
        }
        step = "fin";
    }

    // -------------------------------------------------------
    // Inicializar
    // -------------------------------------------------------
    userInput.disabled = true;
    obtenerMaquinas();

    if (chatForm) {
        chatForm.addEventListener("submit", e => {
            e.preventDefault();
            handleUserInput();
        });
    }

    userInput.addEventListener("keypress", e => {
        if (e.key === "Enter") handleUserInput();
    });

    // -------------------------------------------------------
    // Modo administración
    // -------------------------------------------------------
    adminButton.addEventListener("click", () => {
        const loginWindow = window.open("", "AdminLogin", "width=400,height=300");
        loginWindow.document.write(`
      <h3>Login Administrador</h3>
      <label>Usuario:</label><input type="text" id="admin-user"><br>
      <label>Contraseña:</label><input type="password" id="admin-pass"><br>
      <button id="login-btn">Ingresar</button>
      <div id="login-msg" style="color:red;"></div>
    `);

        loginWindow.document.getElementById("login-btn").addEventListener("click", async () => {
            const user = loginWindow.document.getElementById("admin-user").value;
            const pass = loginWindow.document.getElementById("admin-pass").value;

            try {
                const res = await fetch(`http://127.0.0.1:8000/api/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username: user, password: pass })
                });
                const data = await res.json();

                if (data.success) {
                    loginWindow.close();
                    abrirPanelAdmin();
                } else {
                    loginWindow.document.getElementById("login-msg").innerText = "Usuario o contraseña incorrectos";
                }
            } catch (error) {
                loginWindow.document.getElementById("login-msg").innerText = "Error de conexión al servidor";
            }
        });
    });

    // -------------------------------------------------------
    // Panel de administración
    // -------------------------------------------------------
    function abrirPanelAdmin() {
        const panel = window.open("", "PanelAdmin", "width=600,height=400");
        panel.document.write(`
      <h2>Panel de Administración</h2>
      <button id="btn-usuarios">Gestionar usuarios</button>
      <button id="btn-manuales">Gestionar manuales</button>
      <button id="btn-reglas">Gestionar reglas</button>
      <button id="btn-historial">Ver historial de consultas</button>
      <div id="admin-content" style="margin-top:20px;"></div>
    `);

        panel.document.getElementById("btn-reglas").addEventListener("click", () => {
            const content = panel.document.getElementById("admin-content");
            content.innerHTML = `
        <h3>Agregar nueva regla</h3>
        <label>Máquina:</label><input type="text" id="regla-maquina"><br>
        <label>Nombre nodo:</label><input type="text" id="regla-nodo"><br>
        <label>Pregunta:</label><input type="text" id="regla-pregunta"><br>
        <label>Falla:</label><input type="text" id="regla-falla"><br>
        <label>Soluciones (separadas por comas):</label><input type="text" id="regla-soluciones"><br>
        <button id="guardar-regla">Guardar regla</button>
      `;

            panel.document.getElementById("guardar-regla").addEventListener("click", async () => {
                const maquina = panel.document.getElementById("regla-maquina").value;
                const nodo = panel.document.getElementById("regla-nodo").value;
                const pregunta = panel.document.getElementById("regla-pregunta").value;
                const falla = panel.document.getElementById("regla-falla").value;
                const soluciones = panel.document.getElementById("regla-soluciones").value.split(",").map(s => s.trim());

                try {
                    const res = await fetch(`http://127.0.0.1:8000/api/agregar_regla`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ maquina, nodo, pregunta, falla, soluciones })
                    });
                    const data = await res.json();
                    alert(data.message || "Regla agregada");
                } catch (error) {
                    alert("Error al agregar regla");
                }
            });
        });
    }
});
