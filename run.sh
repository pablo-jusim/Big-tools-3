#!/bin/bash

echo "========================================"
echo "    Big Tools - Sistema Experto"
echo "========================================"
echo ""
echo "Iniciando el sistema..."
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no está instalado"
    echo "Por favor instala Python desde https://www.python.org/"
    exit 1
fi

# Verificar si las dependencias están instaladas
echo "[1/3] Verificando dependencias..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Instalando dependencias..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudieron instalar las dependencias"
        exit 1
    fi
else
    echo "Dependencias verificadas correctamente"
fi

echo ""
echo "[2/3] Iniciando Backend (FastAPI)..."
echo "Backend ejecutándose en: http://127.0.0.1:8000"
echo ""

# Iniciar el backend en segundo plano
cd Backend
python3 -m uvicorn app:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

# Esperar 3 segundos para que el backend inicie
sleep 3

echo "[3/3] Abriendo Frontend en el navegador..."
echo ""

# Abrir el frontend en el navegador
if command -v xdg-open &> /dev/null; then
    xdg-open "Frontend/index.html"
elif command -v open &> /dev/null; then
    open "Frontend/index.html"
else
    echo "Por favor abre manualmente: Frontend/index.html"
fi

echo ""
echo "========================================"
echo "  Sistema iniciado correctamente!"
echo "========================================"
echo ""
echo "  - Backend (API): http://127.0.0.1:8000"
echo "  - Frontend (Chatbot): Frontend/index.html"
echo "  - Dashboard Admin: Frontend/admin.html"
echo ""
echo "  Credenciales de Admin:"
echo "    Usuario: admin"
echo "    Contraseña: 1234"
echo ""
echo "========================================"
echo ""
echo "Presiona Ctrl+C para detener el sistema..."
echo ""

# Función para limpiar al salir
cleanup() {
    echo ""
    echo "Deteniendo el sistema..."
    kill $BACKEND_PID 2>/dev/null
    echo "Sistema detenido."
    exit 0
}

# Capturar Ctrl+C
trap cleanup INT TERM

# Mantener el script corriendo
wait $BACKEND_PID

