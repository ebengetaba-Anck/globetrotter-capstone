from flask import Flask, request, jsonify
import json
import os
import requests
from datetime import datetime
from functools import wraps
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'microservices-secret-key-change-in-prod'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DESTINATIONS_FILE = os.path.join(DATA_DIR, 'destinations.json')
REVIEWS_FILE = os.path.join(DATA_DIR, 'reviews.json')

USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://localhost:5001')
ITINERARY_SERVICE_URL = os.environ.get('ITINERARY_SERVICE_URL', 'http://localhost:5002')

def get_destinations():
    if os.path.exists(DESTINATIONS_FILE):
        with open(DESTINATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def get_reviews():
    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_review(review):
    reviews = get_reviews()
    reviews.append(review)
    with open(REVIEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentification requise'}), 401
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.username = payload.get('sub')
            return f(*args, **kwargs)
        except:
            return jsonify({'error': 'Token invalide'}), 401
    return decorated


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'recommendation-service'}), 200


@app.route('/destinations', methods=['GET'])
def get_all_destinations():
    return jsonify(get_destinations()), 200


@app.route('/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    username = getattr(request, 'username', None)
    
    # Récupérer les préférences depuis User Service
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{username}")
        user_data = user_response.json() if user_response.status_code == 200 else {}
        preferences = user_data.get('preferences', [])
    except:
        preferences = []
    
    # Récupérer les itinéraires de l'utilisateur
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    headers = {'Authorization': f'Bearer {token}'}
    try:
        itinerary_response = requests.get(f"{ITINERARY_SERVICE_URL}/itineraries", headers=headers)
        itineraries = itinerary_response.json() if itinerary_response.status_code == 200 else []
    except:
        itineraries = []
    
    # Récupérer les destinations déjà visitées
    visited_ids = []
    for it in itineraries:
        visited_ids.extend(it.get('destinations', []))
    
    # Filtrer les destinations
    all_destinations = get_destinations()
    recommendations = [d for d in all_destinations if str(d.get('id')) not in visited_ids]
    
    # Trier par note
    recommendations.sort(key=lambda x: x.get('rating', 0), reverse=True)
    
    return jsonify(recommendations[:10]), 200


@app.route('/reviews', methods=['GET'])
def get_reviews_by_destination():
    destination_id = request.args.get('destination_id')
    if not destination_id:
        return jsonify({'error': 'destination_id requis'}), 400
    
    all_reviews = get_reviews()
    filtered = [r for r in all_reviews if str(r.get('destination_id')) == str(destination_id)]
    return jsonify(filtered), 200


@app.route('/reviews', methods=['POST'])
@login_required
def post_review():
    username = getattr(request, 'username', None)
    data = request.get_json()
    
    review = {
        'id': str(len(get_reviews()) + 1),
        'destination_id': data.get('destination_id'),
        'username': username,
        'rating': data.get('rating'),
        'comment': data.get('comment', ''),
        'created_at': datetime.now().strftime('%d/%m/%Y')
    }
    
    save_review(review)
    return jsonify({'message': 'Avis publié'}), 201


@app.route('/recommendations/personalized', methods=['GET'])
@login_required
def get_personalized_recommendations():
    username = getattr(request, 'username', None)
    
    # Récupérer les préférences
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{username}")
        user_data = user_response.json() if user_response.status_code == 200 else {}
        preferences = user_data.get('preferences', [])
    except:
        preferences = []
    
    # Récupérer les itinéraires
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    headers = {'Authorization': f'Bearer {token}'}
    try:
        itinerary_response = requests.get(f"{ITINERARY_SERVICE_URL}/itineraries", headers=headers)
        itineraries = itinerary_response.json() if itinerary_response.status_code == 200 else []
    except:
        itineraries = []
    
    visited_ids = []
    for it in itineraries:
        visited_ids.extend(it.get('destinations', []))
    
    all_destinations = get_destinations()
    
    # Filtrer les destinations non visitées
    recommendations = [d for d in all_destinations if str(d.get('id')) not in visited_ids]
    
    # Personnaliser selon les préférences
    if preferences:
        scored = []
        for d in recommendations:
            score = 0
            tags = [t.lower() for t in d.get('tags', [])]
            for pref in preferences:
                if pref.lower() in tags:
                    score += 2
            score += d.get('rating', 0) / 5
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        recommendations = [d for _, d in scored]
    
    return jsonify(recommendations[:10]), 200

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    print("="*50)
    print("🚀 Recommendation Service - Port 5003")
    print("="*50)
    app.run(host='0.0.0.0', port=5003, debug=True)