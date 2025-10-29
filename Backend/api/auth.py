# Backend/api/auth.py
import json
import hashlib
from pathlib import Path

USERS_FILE = Path(__file__).parent.parent / "data" / "users.json"

def cargar_usuarios():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def validar_usuario(username: str, password: str) -> bool:
    """
    Valida usuario y contraseña.
    Para demo: contraseña en texto plano.
    Para producción: usar hash (sha256, bcrypt, etc.)
    """
    usuarios = cargar_usuarios()
    # Ejemplo hash: password = hashlib.sha256(password.encode()).hexdigest()
    for u in usuarios:
        if u["username"] == username and u["password"] == password:
            return True
    return False
