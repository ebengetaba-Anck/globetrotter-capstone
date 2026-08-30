import uuid
import datetime
import json
import os
from flask import Blueprint, request, jsonify, current_app, render_template
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(BASE_DIR, "data", "users.json")


def get_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except:
        return []


def save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def get_user_by_username(username):
    users = get_users()
    for user in users:
        if user.get("username") == username:
            return user
    return None


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip()

    if not username or not password:
        return jsonify({"error": "Nom d'utilisateur et mot de passe requis"}), 400

    if get_user_by_username(username):
        return jsonify({"error": "Ce nom d'utilisateur existe déjà"}), 409

    users = get_users()
    new_user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": generate_password_hash(password),
        "email": email,
        "preferences": data.get("preferences", []),
        "created_at": datetime.datetime.now().isoformat()
    }
    users.append(new_user)
    save_users(users)

    return jsonify({"message": "Compte créé avec succès !", "username": username}), 201


@auth_bp.route("/api/login", methods=["POST"])
def login():
    import jwt
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Identifiants requis"}), 400

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "Identifiants invalides"}), 401

    if not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"error": "Identifiants invalides"}), 401

    token = jwt.encode(
        {"sub": username, "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)},
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    return jsonify({"token": token, "username": username}), 200