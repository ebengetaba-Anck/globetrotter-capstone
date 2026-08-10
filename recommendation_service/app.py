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
    # CORRECTION ICI : On précise encoding="utf-8" pour lire les accents correctement
    with open(DESTINATIONS_FILE, "r", encoding="utf-8") as f:
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


@app.route("/destinations", methods=["GET"])
def get_all_destinations():
    destinations = read_destinations()
    return jsonify(destinations), 200


@app.route("/recommendations", methods=["GET"])
def get_recommendations():
    auth_header = request.headers.get("Authorization", "")
    username = get_username_from_token(auth_header)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

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

    destinations = read_destinations()

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


@app.route("/api/gallery/<dest_id>")
def api_gallery_images(dest_id):
    folder_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "images", dest_id)
    
    if not os.path.isdir(folder_path):
        return jsonify([])
    
    valid_ext = (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".avi")
    files = sorted([
        f for f in os.listdir(folder_path) 
        if f.lower().endswith(valid_ext)
    ])
    
    urls = [f"/static/images/{dest_id}/{f}" for f in files]
    return jsonify(urls)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)