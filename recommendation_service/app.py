from flask import Flask, request, jsonify
import json
import os
import requests
import jwt
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

DESTINATIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "destinations.json")

def read_destinations():
    if not os.path.exists(DESTINATIONS_FILE):
        return []
    try:
        with open(DESTINATIONS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return []

def get_username_from_token(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
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


# ============================================================
# MOTEUR DE RECOMMANDATION AVEC "BON PLAN AMOUREUX"
# ============================================================

def get_destination_by_id(dest_id):
    destinations = read_destinations()
    return next((d for d in destinations if d.get('id') == dest_id), None)

@app.route("/api/build-itinerary", methods=["POST"])
def build_itinerary():
    data = request.get_json(silent=True) or {}
    mood = data.get("mood", "")
    search = data.get("search", "")
    time = data.get("time", "")
    budget = data.get("budget", "")
    surprise = data.get("surprise", "non")

    destinations = read_destinations()

    # =============================================================
    # 1. SI L'UTILISATEUR CHOISIT ROMANTIQUE + WEEKEND + MOYEN/PREMIUM
    #    ON LUI PROPOSE LE "BON PLAN AMOUREUX" PRÉ-DÉFINI
    # =============================================================
    if mood == 'romantique' and time == 'weekend' and budget in ['moyen', 'premium']:
        # Lieux du plan amoureux
        les_mangroves = get_destination_by_id('dla-151')
        one_rooftop = get_destination_by_id('dla-153')
        nshi_pool_bar = get_destination_by_id('dla-152')
        
        # On ne garde que les lieux qui existent
        romantic_plan = []
        if les_mangroves: romantic_plan.append(les_mangroves)
        if one_rooftop: romantic_plan.append(one_rooftop)
        if nshi_pool_bar: romantic_plan.append(nshi_pool_bar)
        
        # Si on a au moins 2 lieux, on retourne ce plan spécial
        if len(romantic_plan) >= 2:
            return jsonify({
                "type": "romantic_plan",
                "plan": romantic_plan
            }), 200

    # =============================================================
    # 2. SI CE N'EST PAS UN PLAN AMOUREUX, ON UTILISE LE MOTEUR CLASSIQUE
    # =============================================================
    # Filtrer par MOOD
    mood_results = []
    for d in destinations:
        if d.get('mood') and mood in d['mood']:
            mood_results.append(d)

    # Filtrer par SEARCH
    search_results = []
    if search:
        for d in mood_results:
            if d.get('search') and search in d['search']:
                search_results.append(d)
        if not search_results:
            search_results = mood_results
    else:
        search_results = mood_results

    # Filtrer par BUDGET
    budget_results = []
    for d in search_results:
        level = d.get('budget_level', 'moyen')
        if budget == 'petit':
            if level in ['economique', 'moyen']:
                budget_results.append(d)
        elif budget == 'moyen':
            if level in ['economique', 'moyen', 'plaisir']:
                budget_results.append(d)
        elif budget == 'premium':
            if level in ['plaisir', 'premium']:
                budget_results.append(d)
        else:
            budget_results.append(d)

    # Surprise
    final_results = budget_results[:6]
    if surprise == 'oui' and len(budget_results) > 6:
        remaining = [d for d in budget_results if d not in final_results]
        if remaining:
            surprise_place = random.choice(remaining)
            final_results.append(surprise_place)

    return jsonify({
        "type": "classic",
        "plan": final_results[:6]
    }), 200


# ============================================================
# ROUTE REPLACE SUGGESTION
# ============================================================

@app.route("/api/replace-suggestion", methods=["POST"])
def replace_suggestion():
    data = request.get_json(silent=True) or {}
    current_id = data.get("current_id", "")
    mood = data.get("mood", "")
    search = data.get("search", "")
    budget = data.get("budget", "")

    destinations = read_destinations()

    mood_results = []
    for d in destinations:
        if d.get('mood') and mood in d['mood']:
            mood_results.append(d)

    search_results = []
    if search:
        for d in mood_results:
            if d.get('search') and search in d['search']:
                search_results.append(d)
        if not search_results:
            search_results = mood_results
    else:
        search_results = mood_results

    budget_results = []
    for d in search_results:
        level = d.get('budget_level', 'moyen')
        if budget == 'petit':
            if level in ['economique', 'moyen']:
                budget_results.append(d)
        elif budget == 'moyen':
            if level in ['economique', 'moyen', 'plaisir']:
                budget_results.append(d)
        elif budget == 'premium':
            if level in ['plaisir', 'premium']:
                budget_results.append(d)
        else:
            budget_results.append(d)

    candidates = [d for d in budget_results if d.get('id') != current_id]

    if candidates:
        replacement = random.choice(candidates)
        return jsonify(replacement), 200
    else:
        return jsonify({"error": "Aucune autre suggestion"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)