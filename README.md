En una terminal:
uvicorn Backend.app:app --reload

En otra terminal:
cd Frontend
python -m http.server 3000

en el navegador:
http://localhost:3000/html/index.html