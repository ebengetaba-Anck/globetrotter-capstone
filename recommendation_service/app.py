from flask import Flask, request, jsonify
import json
import os
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

# Base de données des destinations
DESTINATIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "destinations.json")

def read_destinations():
    if not os.path.exists(DESTINATIONS_FILE):
        return []
    with open(DESTINATIONS_FILE, "r") as f:
        return json.load(f)

def get_username_from_token(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        import jwt
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


# ============================================================
# AJOUT DE LA ROUTE /destinations (Pour les cartes du dashboard)
# ============================================================
@app.route("/destinations", methods=["GET"])
def get_all_destinations():
    destinations = read_destinations()
    return jsonify(destinations), 200


# ============================================================
# Route des recommandations (existante)
# ============================================================
@app.route("/recommendations", methods=["GET"])
def get_recommendations():
    auth_header = request.headers.get("Authorization", "")
    username = get_username_from_token(auth_header)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

    # 1. Appeler le User Service pour obtenir les préférences
    try:
        user_response = requests.get(
            "http://127.0.0.1:5001/me",
            headers={"Authorization": auth_header}
        )
        if user_response.status_code != 200:
            return jsonify({"error": "Impossible de récupérer les préférences utilisateur"}), 500
        
        user_data = user_response.json()
        preferences = user_data.get("preferences", [])
    except requests.exceptions.RequestException:
        return jsonify({"error": "User service inaccessible"}), 500

    # 2. Lire les destinations
    destinations = read_destinations()

    # 3. Calculer les recommandations basées sur les préférences
    scored = []
    for d in destinations:
        score = 0
        if d.get('category') in preferences:
            score += 3
        if d.get('tags'):
            for tag in d.get('tags', []):
                if tag in preferences:
                    score += 1
        scored.append((score, d))
    
    scored.sort(key=lambda x: -x[0])
    recommendations = [d for _, d in scored[:6]]

    return jsonify(recommendations), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)