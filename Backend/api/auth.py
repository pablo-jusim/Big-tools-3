# Backend/api/auth.py
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

USERS_FILE = Path(__file__).parent.parent / "data" / "users.json"

# Almacenamiento simple de tokens en memoria (para producción usar Redis o DB)
active_tokens = {}

def cargar_usuarios():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def hash_password(password: str) -> str:
    """
    Genera hash SHA256 de una contraseña.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def validar_usuario(username: str, password: str) -> Optional[dict]:
    """
    Valida usuario y contraseña usando hash SHA256.
    Retorna el usuario completo (con rol) si es válido, None si no.
    """
    usuarios = cargar_usuarios()
    password_hash = hash_password(password)
    
    for u in usuarios:
        if u["username"] == username and u["password"] == password_hash:
            return {
                "username": u["username"],
                "role": u.get("role", "tecnico")  # Por defecto es técnico
            }
    return None

def crear_token(username: str, role: str = "tecnico") -> str:
    """
    Crea un token de sesión simple para el usuario.
    """
    token = secrets.token_urlsafe(32)
    active_tokens[token] = {
        "username": username,
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    return token

def validar_token(token: str) -> Optional[dict]:
    """
    Valida un token y retorna los datos del usuario si es válido, None si no.
    """
    if token in active_tokens:
        return active_tokens[token]
    return None

def eliminar_token(token: str):
    """
    Elimina un token (logout).
    """
    if token in active_tokens:
        del active_tokens[token]
