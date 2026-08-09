"""
app/auth.py

User registration, login, password reset, and JWT handling.

Routes
------
GET  /login            - Afficher la page de connexion (page HTML)
POST /register        - create a new user account
POST /login            - authenticate and return a JWT token
POST /reset-password   - reset a user's password (demo only)
"""
import uuid
import datetime

import jwt
from flask import Blueprint, request, jsonify, current_app, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import get_user_by_username, save_user, get_all_users, _write_json, USERS_FILE

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Helper - JWT utilities
# ---------------------------------------------------------------------------

def create_token(username: str, secret: str) -> str:
    """Return a signed JWT for *username* valid for 24 hours."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict:
    """Decode and verify *token*. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, secret, algorithms=["HS256"])


def get_current_user(request_obj) -> str | None:
    """Extract and validate the JWT from the Authorization header.

    Returns the username (subject claim) or None if the token is missing /
    invalid.
    """
    auth_header = request_obj.headers.get("Authorization", "")
    if not auth_header:
        return None
    
    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        return None

    try:
        payload = decode_token(token, current_app.config["SECRET_KEY"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET"])
def show_login_page():
    return render_template("login.html")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    preferences = data.get("preferences", [])
    gender = data.get("gender", "").strip()  # RÉCUPÉRATION DU GENRE

    if not username or not password:
        return jsonify({"error": "Nom d'utilisateur et mot de passe requis"}), 400
    if get_user_by_username(username):
        return jsonify({"error": "Ce nom d'utilisateur existe déjà"}), 409

    # Si le genre n'est pas sélectionné, on met une valeur par défaut
    if not gender:
        gender = "masculin"

    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": generate_password_hash(password),
        "email": email,
        "phone": phone,
        "gender": gender,  # AJOUT DU GENRE DANS L'OBJET
        "preferences": preferences,
    }
    save_user(user)
    return jsonify({"message": "Compte créé avec succès !", "username": username}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Nom d'utilisateur et mot de passe requis"}), 400

    user = get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Identifiants invalides"}), 401

    token = create_token(username, current_app.config["SECRET_KEY"])
    return jsonify({"token": token}), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    new_password = data.get("new_password", "")

    if not username or not new_password:
        return jsonify({"error": "Nom d'utilisateur et nouveau mot de passe requis"}), 400

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    users = get_all_users()
    for u in users:
        if u.get("username") == username:
            u["password_hash"] = generate_password_hash(new_password)
    _write_json(USERS_FILE, users)

    return jsonify({"message": "Mot de passe réinitialisé avec succès"}), 200