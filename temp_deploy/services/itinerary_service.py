from flask import Flask, request, jsonify
import json
import os
import jwt
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'microservices-secret-key-change-in-prod'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
ITINERARIES_FILE = os.path.join(DATA_DIR, 'itineraries.json')


def get_itineraries(username=None):
    if os.path.exists(ITINERARIES_FILE):
        with open(ITINERARIES_FILE, 'r', encoding='utf-8') as f:
            all_itineraries = json.load(f)
        if username:
            return [i for i in all_itineraries if i.get('username') == username]
        return all_itineraries
    return []


def save_itinerary(itinerary):
    itineraries = get_itineraries()
    itineraries.append(itinerary)
    with open(ITINERARIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(itineraries, f, indent=2, ensure_ascii=False)


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
    return jsonify({'status': 'ok', 'service': 'itinerary-service'}), 200


@app.route('/itineraries', methods=['GET'])
@login_required
def get_user_itineraries():
    username = getattr(request, 'username', None)
    itineraries = get_itineraries(username)
    return jsonify(itineraries), 200


@app.route('/itineraries', methods=['POST'])
@login_required
def create_itinerary():
    username = getattr(request, 'username', None)
    data = request.get_json()
    
    itinerary = {
        'id': str(len(get_itineraries(username)) + 1),
        'username': username,
        'title': data.get('title', 'Mon itinéraire'),
        'destinations': data.get('destinations', []),
        'budget': data.get('budget', 0),
        'time_available': data.get('time_available', 0),
        'notes': data.get('notes', ''),
        'created_at': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    
    save_itinerary(itinerary)
    return jsonify({'message': 'Itinéraire créé', 'itinerary': itinerary}), 201


@app.route('/itineraries/<itinerary_id>', methods=['DELETE'])
@login_required
def delete_itinerary(itinerary_id):
    username = getattr(request, 'username', None)
    
    if os.path.exists(ITINERARIES_FILE):
        with open(ITINERARIES_FILE, 'r', encoding='utf-8') as f:
            itineraries = json.load(f)
        
        itineraries = [i for i in itineraries if not (i.get('id') == itinerary_id and i.get('username') == username)]
        
        with open(ITINERARIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(itineraries, f, indent=2, ensure_ascii=False)
        
        return jsonify({'message': 'Itinéraire supprimé'}), 200
    
    return jsonify({'error': 'Itinéraire non trouvé'}), 404


@app.route('/itineraries/<itinerary_id>', methods=['PUT'])
@login_required
def update_itinerary(itinerary_id):
    username = getattr(request, 'username', None)
    data = request.get_json()
    
    if os.path.exists(ITINERARIES_FILE):
        with open(ITINERARIES_FILE, 'r', encoding='utf-8') as f:
            itineraries = json.load(f)
        
        for i, it in enumerate(itineraries):
            if it.get('id') == itinerary_id and it.get('username') == username:
                if 'title' in data:
                    it['title'] = data['title']
                if 'destinations' in data:
                    it['destinations'] = data['destinations']
                if 'budget' in data:
                    it['budget'] = data['budget']
                if 'time_available' in data:
                    it['time_available'] = data['time_available']
                if 'notes' in data:
                    it['notes'] = data['notes']
                
                with open(ITINERARIES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(itineraries, f, indent=2, ensure_ascii=False)
                
                return jsonify({'message': 'Itinéraire mis à jour', 'itinerary': it}), 200
        
        return jsonify({'error': 'Itinéraire non trouvé'}), 404
    
    return jsonify({'error': 'Itinéraire non trouvé'}), 404


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    print("="*50)
    print("🚀 Itinerary Service - Port 5002")
    print("="*50)
    app.run(host='0.0.0.0', port=5002, debug=True)