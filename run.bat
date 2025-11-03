@echo off
echo ========================================
echo    Big Tools - Sistema Experto
echo ========================================
echo.
echo Iniciando el sistema...
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instala Python desde https://www.python.org/
    pause
    exit /b 1
)

REM Verificar si las dependencias están instaladas
echo [1/3] Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las dependencias
        pause
        exit /b 1
    )
) else (
    echo Dependencias verificadas correctamente
)

echo.
echo [2/3] Iniciando Backend (FastAPI)...
echo Backend ejecutándose en: http://127.0.0.1:8000
echo.

REM Iniciar el backend en una nueva ventana
start "Big Tools - Backend" cmd /k "cd Backend && python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000"

REM Esperar 3 segundos para que el backend inicie
timeout /t 3 /nobreak >nul

echo [3/3] Abriendo Frontend en el navegador...
echo.

REM Abrir el frontend en el navegador predeterminado
start "" "http://127.0.0.1:8000/../Frontend/index.html"
start "" "%CD%\Frontend\index.html"

echo.
echo ========================================
echo  Sistema iniciado correctamente!
echo ========================================
echo.
echo  - Backend (API): http://127.0.0.1:8000
echo  - Frontend (Chatbot): Frontend/index.html
echo  - Dashboard Admin: Frontend/admin.html
echo.
echo  Credenciales de Admin:
echo    Usuario: admin
echo    Contraseña: 1234
echo.
echo ========================================
echo.
echo Presiona cualquier tecla para detener el sistema...
pause >nul

REM Matar el proceso de uvicorn
taskkill /FI "WINDOWTITLE eq Big Tools - Backend*" /T /F >nul 2>&1

echo.
echo Sistema detenido.
pause

