from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import uuid
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

# Base de données simulée (fichier JSON partagé)
USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")

def read_users():
    import json
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def write_users(users):
    import json
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# Route : Inscription
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip()
    gender = data.get("gender", "masculin")

    if not username or not password:
        return jsonify({"error": "Nom d'utilisateur et mot de passe requis"}), 400

    users = read_users()
    for u in users:
        if u.get("username") == username:
            return jsonify({"error": "Ce nom d'utilisateur existe déjà"}), 409

    new_user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": generate_password_hash(password),
        "email": email,
        "gender": gender,
        "preferences": []
    }
    users.append(new_user)
    write_users(users)

    return jsonify({"message": "Compte créé avec succès !", "username": username}), 201

# Route : Connexion
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Nom d'utilisateur et mot de passe requis"}), 400

    users = read_users()
    user = None
    for u in users:
        if u.get("username") == username:
            user = u
            break

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Identifiants invalides"}), 401

    token = jwt.encode({
        "sub": username,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }, app.config["SECRET_KEY"], algorithm="HS256")

    return jsonify({"token": token}), 200

# Route : Profil utilisateur
@app.route("/me", methods=["GET"])
def get_me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Non authentifié"}), 401

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload.get("sub")
    except jwt.PyJWTError:
        return jsonify({"error": "Token invalide"}), 401

    users = read_users()
    for u in users:
        if u.get("username") == username:
            return jsonify({
                "username": u["username"],
                "gender": u.get("gender", "masculin"),
                "preferences": u.get("preferences", [])
            }), 200

    return jsonify({"error": "Utilisateur introuvable"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)