# Big Tools - Sistema Experto de Diagnóstico

Sistema experto para diagnóstico de fallas en máquinas industriales con dashboard administrativo.

## Requisitos Previos

Antes de ejecutar el sistema, asegúrate de tener instalado:

1. **Python 3.8 o superior**
   - Descarga desde: https://www.python.org/downloads/
   - Durante la instalación, marca la opción "Add Python to PATH"

2. **Git** (opcional, solo si clonas desde GitHub)
   - Descarga desde: https://git-scm.com/downloads

## Instalación

### Opción 1: Descargar desde GitHub

```bash
git clone https://github.com/Yansol23/Big-Tools-Sistema-Experto.git
cd Big-Tools-Sistema-Experto
```

### Opción 2: Descargar desde Drive o ZIP

1. Descarga la carpeta del proyecto
2. Descomprime el archivo ZIP (si aplica)
3. Abre PowerShell o Terminal
4. Navega a la carpeta del proyecto:
   ```bash
   cd "ruta/donde/descargaste/Big-Tools-Sistema-Experto"
   ```

## Inicio Rapido

### Pasos para Ejecutar el Sistema

#### 1. Instalar Dependencias (solo la primera vez)
```bash
pip install -r requirements.txt
```

**Nota:** Si `pip` no funciona, intenta con `pip3` o `python -m pip install -r requirements.txt`

#### 2. Navegar a la Carpeta Backend
```bash
cd Backend
```

#### 3. Iniciar el Servidor
```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

#### 4. Abrir el Navegador
Abre tu navegador y ve a:
```
http://127.0.0.1:8000
```

#### 5. Iniciar Sesion
Ingresa las credenciales (ver seccion Credenciales abajo)

### URLs del Sistema

Una vez que el servidor este corriendo:

- **Chatbot Principal:** `http://127.0.0.1:8000/`
- **Dashboard Admin:** `http://127.0.0.1:8000/admin`
- **Documentacion API:** `http://127.0.0.1:8000/docs`

### Notas Importantes

- NO cierres la ventana de PowerShell/Terminal mientras uses el sistema
- Para detener el servidor: presiona `CTRL+C`
- Para reiniciar: vuelve a ejecutar el comando del paso 3
- El servidor se reiniciara automaticamente si cambias el codigo (flag `--reload`)

## Credenciales

El sistema cuenta con **dos tipos de usuarios** con diferentes niveles de acceso:

### Administrador (Acceso Completo)
- **Usuario:** `admin`
- **Contraseña:** `1234`
- **Permisos:** 
  - ✅ Acceso al chatbot de diagnóstico
  - ✅ Acceso al dashboard administrativo
  - ✅ Visualización de estadísticas
  - ✅ Gestión de manuales

### Tecnico (Solo Chatbot)
- **Usuario:** `tecnico`
- **Contraseña:** `1234`
- **Permisos:**
  - ✅ Acceso al chatbot de diagnóstico
  - ❌ Sin acceso al dashboard (botón oculto)

**Nota:** El sistema recordará tu sesión. El botón "Modo Administración" solo es visible para usuarios admin.

## Caracteristicas

### Para Técnicos
- Chatbot inteligente para diagnóstico
- Interfaz intuitiva con opciones múltiples
- Soluciones detalladas paso a paso
- Acceso directo a manuales PDF
- Sistema de login seguro con persistencia de sesión

### Para Administradores
- **Todo lo anterior, más:**
- Dashboard con estadísticas en tiempo real
- Gestión de manuales PDF
- Historial de consultas
- Top máquinas y categorías consultadas
- Control total del sistema

## 🔧 Máquinas Disponibles

1. **Hidrolavadora Kärcher** - 5 categorías de diagnóstico
2. **Generador Generac Guardian** - 3 categorías
3. **Motor Cummins** - 5 categorías
4. **Soldadora Miller Ranger 305D** - 6 categorías

## 📁 Estructura

```
Big-tools-3/
├── Backend/
│   ├── app.py                 # Aplicación FastAPI
│   ├── api/
│   │   ├── auth.py           # Autenticación
│   │   ├── routes.py         # Endpoints
│   │   ├── stats.py          # Estadísticas
│   │   ├── engine.py         # Motor de inferencia
│   │   └── base_conocimiento.py
│   └── data/
│       ├── base_conocimiento.json
│       ├── stats.json
│       ├── users.json
│       └── manuales_pdf/
│
├── Frontend/
│   ├── index.html            # Chatbot
│   ├── admin.html            # Dashboard
│   ├── css/
│   └── js/
│
├── test_backend.bat          # Iniciar backend (Windows)
├── run_simple.py             # Iniciar todo (Python)
└── requirements.txt          # Dependencias
```

## 🛠️ Instalación

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Iniciar backend
```bash
cd Backend
python -m uvicorn app:app --reload
```

### 3. Abrir frontend
Abre `Frontend/index.html` en tu navegador.

## 📊 Endpoints API

### Públicos
- `GET /api/maquinas` - Lista de máquinas
- `GET /api/categorias/{maquina}` - Categorías por máquina
- `POST /api/diagnosticar/iniciar/{maquina}/{categoria}` - Iniciar diagnóstico
- `POST /api/diagnosticar/avanzar/{maquina}/{categoria}` - Avanzar diagnóstico

### Administrativos (requieren token)
- `POST /api/admin/login` - Login
- `POST /api/admin/logout` - Logout
- `GET /api/admin/stats` - Estadísticas

## 🎯 Uso

### Chatbot
1. Abre `Frontend/index.html`
2. Selecciona una máquina
3. Elige una categoría
4. Responde las preguntas
5. Obtén diagnóstico y soluciones
6. Accede al manual PDF si está disponible

### Dashboard
1. Abre `Frontend/admin.html`
2. Login: admin / 1234
3. Ver estadísticas o gestionar manuales
4. Actualizar datos en tiempo real

## 📚 Gestión de Manuales

Los manuales PDF se encuentran en:
```
Backend/data/manuales_pdf/
```

Para agregar un manual:
1. Copia el PDF a la carpeta `manuales_pdf/`
2. El sistema lo detectará automáticamente
3. Aparecerá en los diagnósticos correspondientes

## 🔒 Seguridad

- Contraseñas hasheadas con SHA256
- Tokens de sesión únicos
- CORS configurado
- Validación de entrada

## 🛠️ Tecnologías

- **Backend:** Python 3, FastAPI, Uvicorn
- **Frontend:** HTML5, CSS3, JavaScript
- **Autenticación:** SHA256, Tokens
- **Almacenamiento:** JSON

## 🆘 Solución de Problemas

### Error: "Python no reconocido como comando"
**Solución:** Python no está en el PATH del sistema
1. Reinstala Python desde https://www.python.org/downloads/
2. Marca la opción "Add Python to PATH" durante la instalación
3. Reinicia PowerShell/Terminal

### Error: "pip no reconocido como comando"
**Solución:** Usa una de estas alternativas:
```bash
python -m pip install -r requirements.txt
# o
pip3 install -r requirements.txt
```

### Error: "No module named 'fastapi'"
**Solución:** Las dependencias no están instaladas
```bash
pip install -r requirements.txt
```

### Backend no inicia
**Solución:**
```bash
# Asegúrate de estar en la carpeta correcta
cd Backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Frontend no conecta
**Solución:**
- Verifica que el backend esté corriendo en `http://127.0.0.1:8000`
- Abre la consola del navegador (F12) para ver errores
- Haz un hard refresh: `CTRL + SHIFT + R` o `CTRL + F5`

### Login no funciona
**Solución:**
- Verifica las credenciales:
  - Usuario: `admin` o `tecnico`
  - Contraseña: `1234`
- Haz un hard refresh del navegador
- Revisa la consola del navegador (F12)

### Puerto 8000 ya está en uso
**Solución:**
```bash
# Usa otro puerto
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8001
```
Luego abre: `http://127.0.0.1:8001`

### Los gráficos no se ven
**Solución:**
- Haz un hard refresh: `CTRL + SHIFT + R`
- Verifica tu conexión a internet (Chart.js se carga desde CDN)
- Revisa la consola del navegador (F12)

## 📝 Notas

- Los manuales se abren en nueva pestaña
- Las estadísticas se actualizan en tiempo real
- El sistema soporta múltiples sesiones simultáneas
- Compatible con Chrome, Firefox, Edge

---

**Desarrollado para Big Tools** - Sistema de Diagnóstico Industrial
