from flask import Flask, request, jsonify
import json
import os
import requests
import jwt
import random
from datetime import datetime

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
# SMART PLANNER ENGINE
# ============================================================

# Matrice Mood / Période (score de compatibilité)
MOOD_TIME_MATRIX = {
    "relax":    {"matin": 5, "apres_midi": 5, "soir": 4, "nuit": 2},
    "ambiance": {"matin": 1, "apres_midi": 2, "soir": 5, "nuit": 5},
    "decouverte": {"matin": 5, "apres_midi": 5, "soir": 3, "nuit": 1},
    "romantique": {"matin": 3, "apres_midi": 4, "soir": 5, "nuit": 4},
    "famille":  {"matin": 5, "apres_midi": 5, "soir": 3, "nuit": 0},
    "amis":     {"matin": 3, "apres_midi": 4, "soir": 5, "nuit": 5},
    "food":     {"matin": 4, "apres_midi": 4, "soir": 5, "nuit": 3},
    "evasion":  {"matin": 4, "apres_midi": 5, "soir": 4, "nuit": 2}
}

def get_period_from_time(time_str):
    if time_str == '2h' or time_str == 'soir':
        return 'soir'
    if time_str == 'nuit':
        return 'nuit'
    # Pour les autres cas, on déduit par la suite
    return None

@app.route("/api/build-itinerary", methods=["POST"])
def build_itinerary():
    data = request.get_json(silent=True) or {}
    mood = data.get("mood", "")
    search = data.get("search", "")
    time = data.get("time", "")
    budget = data.get("budget", "")
    surprise = data.get("surprise", "non")

    destinations = read_destinations()
    current_hour = datetime.now().hour

    # =============================================================
    # ÉTAPE 1 : FILTRE DUR (Élimination des lieux impossibles)
    # =============================================================
    
    candidates = []
    for d in destinations:
        # 1. Vérifier si le lieu est ouvert à cette heure
        opening = d.get('opening_hours', '')
        if opening and opening != '00:00-23:59':
            try:
                open_start, open_end = opening.split('-')
                open_hour = int(open_start.split(':')[0])
                close_hour = int(open_end.split(':')[0])
                if not (open_hour <= current_hour < close_hour):
                    continue
            except:
                pass

        # 2. Vérifier la compatibilité MOOD (via mood_scores)
        mood_scores = d.get('mood_scores', {})
        if mood_scores.get(mood, 0) < 20:
            continue

        # 3. Vérifier le BUDGET (via budget_min / budget_max)
        budget_min = d.get('budget_min', 0)
        budget_max = d.get('budget_max', 999999)
        if budget == 'petit' and budget_min > 2000:
            continue
        if budget == 'moyen' and budget_max < 2000 and budget_min > 10000:
            continue
        if budget == 'premium' and budget_max < 5000:
            continue

        # 4. Vérifier la DURÉE
        duration_min = d.get('duration_min', 0)
        duration_max = d.get('duration_max', 999)
        if time == '2h' and duration_max > 180:
            continue
        if time == 'demi' and duration_max > 240:
            continue

        # 5. Règle d'exclusion : Ambiance + Matin → pas de lieux culturels
        if mood == 'ambiance' and 6 <= current_hour < 12:
            if d.get('type') == 'decouvrir' or not d.get('is_nightlife', False):
                continue

        # 6. Règle d'exclusion : Famille + Nuit → éliminé
        if mood == 'famille' and current_hour >= 22:
            continue

        candidates.append(d)

    # =============================================================
    # ÉTAPE 2 : SCORE (Classement des lieux restants)
    # =============================================================

    # Déterminer la période
    period = 'matin'
    if current_hour >= 18:
        period = 'soir'
    elif current_hour >= 22:
        period = 'nuit'
    elif current_hour >= 12:
        period = 'apres_midi'

    scored = []
    for d in candidates:
        score = 0
        
        # Score Mood (35%) : basé sur les mood_scores
        mood_score = d.get('mood_scores', {}).get(mood, 0)
        score += mood_score * 0.35

        # Score Période (20%) : basé sur la matrice
        time_score = d.get('time_scores', {}).get(period, 50)
        score += time_score * 0.20

        # Score Budget (10%)
        budget_min = d.get('budget_min', 0)
        budget_max = d.get('budget_max', 999999)
        if budget == 'petit' and budget_min <= 2000:
            score += 10
        elif budget == 'moyen' and budget_min <= 10000:
            score += 8
        elif budget == 'premium' and budget_min > 5000:
            score += 10
        else:
            score += 5

        # Score Activité (15%)
        if d.get('activities') and len(d.get('activities', [])) > 0:
            score += 15

        # Score Popularité (5%)
        score += min(d.get('reviews', 0) / 100 * 5, 5)

        # Score Distance (10%) : fictif, car on n'a pas de GPS en temps réel
        score += 10

        scored.append((score, d))

    scored.sort(key=lambda x: -x[0])

    # =============================================================
    # ÉTAPE 3 : CONSTRUCTION DU PROGRAMME
    # =============================================================

    # Si c'est un plan romantique spécial
    if mood == 'romantique' and time == 'weekend' and budget in ['moyen', 'premium']:
        # On force les lieux romantiques à être en haut du classement
        romantic_ids = ['dla-132', 'dla-133', 'dla-134', 'dla-135', 'dla-136']
        romantic_candidates = [d for d in candidates if d.get('id') in romantic_ids]
        if len(romantic_candidates) >= 2:
            return jsonify({
                "type": "romantic_plan",
                "time": time,
                "plan": romantic_candidates[:3]
            }), 200

    # Si c'est 2h, on ne garde qu'un seul lieu (ou 2 max)
    if time == '2h':
        final_results = [d for _, d in scored[:2]]
    else:
        final_results = [d for _, d in scored[:6]]

    # Surprise
    if surprise == 'oui' and len(candidates) > len(final_results):
        remaining = [d for d in candidates if d not in final_results]
        if remaining:
            surprise_place = random.choice(remaining)
            final_results.append(surprise_place)

    # Vérification finale : est-ce réalisable ?
    if not final_results:
        return jsonify({"type": "classic", "time": time, "plan": []}), 200

    return jsonify({
        "type": "classic",
        "time": time,
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
    current_hour = datetime.now().hour

    mood_results = []
    for d in destinations:
        mood_scores = d.get('mood_scores', {})
        if mood_scores.get(mood, 0) >= 20:
            mood_results.append(d)

    budget_results = []
    for d in mood_results:
        budget_min = d.get('budget_min', 0)
        budget_max = d.get('budget_max', 999999)
        if budget == 'petit' and budget_min > 2000:
            continue
        if budget == 'moyen' and budget_max < 2000 and budget_min > 10000:
            continue
        if budget == 'premium' and budget_max < 5000:
            continue
        budget_results.append(d)

    candidates = [d for d in budget_results if d.get('id') != current_id]

    if candidates:
        replacement = random.choice(candidates)
        return jsonify(replacement), 200
    else:
        return jsonify({"error": "Aucune autre suggestion"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)