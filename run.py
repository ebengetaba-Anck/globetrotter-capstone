from flask import Flask, jsonify, render_template, send_from_directory, request, redirect
import os
import json
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "templates"),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static"))

app.config['SECRET_KEY'] = 'microservices-secret-key-change-in-prod'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')


# ============================================================
# FONCTIONS
# ============================================================

def get_users():
    filepath = os.path.join(DATA_DIR, 'users.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_users(users):
    filepath = os.path.join(DATA_DIR, 'users.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def get_user(username):
    for user in get_users():
        if user.get('username') == username:
            return user
    return None


def get_destinations():
    filepath = os.path.join(DATA_DIR, 'destinations.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def get_reviews(destination_id):
    filepath = os.path.join(DATA_DIR, 'reviews.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            all_reviews = json.load(f)
        return [r for r in all_reviews if str(r.get('destination_id')) == str(destination_id)]
    return []


def save_review(review):
    filepath = os.path.join(DATA_DIR, 'reviews.json')
    reviews = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
    reviews.append(review)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)


def get_itineraries(username):
    filepath = os.path.join(DATA_DIR, 'itineraries.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            all_itineraries = json.load(f)
        return [i for i in all_itineraries if i.get('username') == username]
    return []


def save_itinerary(itinerary):
    filepath = os.path.join(DATA_DIR, 'itineraries.json')
    itineraries = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            itineraries = json.load(f)
    itineraries.append(itinerary)
    with open(filepath, 'w', encoding='utf-8') as f:
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
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expiré, veuillez vous reconnecter'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401
        except Exception as e:
            return jsonify({'error': 'Erreur d\'authentification: ' + str(e)}), 401
    return decorated


# ============================================================
# ROUTES PAGES
# ============================================================

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/destinations')
def destinations_page():
    return render_template('destinations.html')


@app.route('/transport')
def transport_page():
    return render_template('transport.html')


@app.route('/my-favorites')
def favorites_page():
    return render_template('my_favorites.html')


@app.route('/my-itineraries')
def my_itineraries_page():
    return render_template('my_itineraries.html')


@app.route('/destination')
def destination_detail():
    dest_id = request.args.get('id')
    destinations = get_destinations()
    destination = next((d for d in destinations if str(d.get('id')) == str(dest_id)), None)
    if not destination:
        return redirect('/destinations')
    return render_template('destination_details.html', destination=destination)


@app.route('/gallery/<dest_id>')
def gallery_page(dest_id):
    destinations = get_destinations()
    destination = next((d for d in destinations if str(d.get('id')) == str(dest_id)), None)
    if not destination:
        return redirect('/destinations')
    return render_template('gallery.html', destination=destination)


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ============================================================
# API - AUTHENTIFICATION
# ============================================================

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '')

    if not username or not password:
        return jsonify({'error': 'Nom d\'utilisateur et mot de passe requis'}), 400

    if get_user(username):
        return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 409

    users = get_users()
    users.append({
        'id': str(len(users) + 1),
        'username': username,
        'password_hash': generate_password_hash(password),
        'email': email,
        'created_at': datetime.now().isoformat()
    })
    save_users(users)

    return jsonify({'message': 'Compte créé avec succès !'}), 201


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Identifiants requis'}), 400

    user = get_user(username)
    if not user or not check_password_hash(user.get('password_hash', ''), password):
        return jsonify({'error': 'Identifiants invalides'}), 401

    token = jwt.encode(
        {'sub': username, 'exp': datetime.now() + timedelta(hours=24)},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )

    return jsonify({'token': token, 'username': username}), 200


@app.route('/api/me', methods=['GET'])
def api_me():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Non authentifié'}), 401
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = get_user(payload.get('sub'))
        if user:
            safe = {k: v for k, v in user.items() if k != 'password_hash'}
            return jsonify(safe), 200
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    except:
        return jsonify({'error': 'Token invalide'}), 401


@app.route('/api/destinations', methods=['GET'])
def api_destinations():
    return jsonify(get_destinations()), 200


@app.route('/api/logout', methods=['POST'])
def api_logout():
    return jsonify({'message': 'Déconnexion réussie'}), 200


# ============================================================
# API - AVIS
# ============================================================

@app.route('/api/reviews', methods=['GET'])
def api_get_reviews():
    destination_id = request.args.get('destination_id')
    if not destination_id:
        return jsonify({'error': 'destination_id requis'}), 400
    
    reviews = get_reviews(destination_id)
    for review in reviews:
        user = get_user(review.get('username'))
        review['author_name'] = user.get('username', 'Anonyme') if user else 'Anonyme'
    
    return jsonify(reviews), 200


@app.route('/api/reviews', methods=['POST'])
@login_required
def api_post_review():
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Utilisateur non identifié'}), 401
    
    data = request.get_json()
    destination_id = data.get('destination_id')
    rating = data.get('rating')
    comment = data.get('comment', '').strip()
    
    if not destination_id:
        return jsonify({'error': 'destination_id requis'}), 400
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'La note doit être entre 1 et 5'}), 400
    
    if not comment:
        return jsonify({'error': 'Veuillez écrire un commentaire'}), 400
    
    review = {
        'id': str(len(get_reviews(destination_id)) + 1),
        'destination_id': str(destination_id),
        'username': username,
        'rating': rating,
        'comment': comment,
        'created_at': datetime.now().strftime('%d/%m/%Y')
    }
    
    save_review(review)
    return jsonify({'message': 'Avis publié avec succès !', 'review': review}), 201


# ============================================================
# API - ITINERAIRES
# ============================================================

@app.route('/api/itineraries', methods=['GET'])
@login_required
def api_get_itineraries():
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Utilisateur non identifié'}), 401
    
    itineraries = get_itineraries(username)
    all_destinations = get_destinations()
    
    for it in itineraries:
        total_cost = 0
        for dest_id in it.get('destinations', []):
            dest = next((d for d in all_destinations if str(d.get('id')) == str(dest_id)), None)
            if dest:
                total_cost += dest.get('avg_cost', 0)
        it['total_cost'] = total_cost
    
    return jsonify(itineraries), 200


@app.route('/api/itineraries', methods=['POST'])
@login_required
def api_create_itinerary():
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Utilisateur non identifié'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données invalides'}), 400
    
    title = data.get('title', 'Mon itinéraire')
    destination_ids = data.get('destinations', [])
    budget = data.get('budget', 0)
    time_available = data.get('time_available', 0)
    notes = data.get('notes', '')
    
    if not destination_ids:
        return jsonify({'error': 'Ajoutez au moins une destination'}), 400
    
    all_destinations = get_destinations()
    total_cost = 0
    for dest_id in destination_ids:
        dest = next((d for d in all_destinations if str(d.get('id')) == str(dest_id)), None)
        if dest:
            total_cost += dest.get('avg_cost', 0)
    
    if budget > 0 and total_cost > budget:
        return jsonify({
            'error': f'Le coût total ({total_cost} FCFA) dépasse votre budget ({budget} FCFA)',
            'total_cost': total_cost,
            'budget': budget
        }), 400
    
    itinerary = {
        'id': str(len(get_itineraries(username)) + 1),
        'username': username,
        'title': title,
        'destinations': destination_ids,
        'budget': budget,
        'time_available': time_available,
        'total_cost': total_cost,
        'notes': notes,
        'created_at': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    
    save_itinerary(itinerary)
    return jsonify({'message': 'Itinéraire créé avec succès !', 'itinerary': itinerary}), 201


@app.route('/api/itineraries/<itinerary_id>', methods=['DELETE'])
@login_required
def api_delete_itinerary(itinerary_id):
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Utilisateur non identifié'}), 401
    
    filepath = os.path.join(DATA_DIR, 'itineraries.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            itineraries = json.load(f)
        
        original_count = len(itineraries)
        itineraries = [i for i in itineraries if not (i.get('id') == itinerary_id and i.get('username') == username)]
        
        if len(itineraries) == original_count:
            return jsonify({'error': 'Itinéraire non trouvé'}), 404
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(itineraries, f, indent=2, ensure_ascii=False)
        
        return jsonify({'message': 'Itinéraire supprimé'}), 200
    
    return jsonify({'error': 'Itinéraire non trouvé'}), 404


@app.route('/api/itineraries/<itinerary_id>', methods=['PUT'])
@login_required
def api_update_itinerary(itinerary_id):
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Utilisateur non identifié'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données invalides'}), 400
    
    filepath = os.path.join(DATA_DIR, 'itineraries.json')
    if not os.path.exists(filepath):
        return jsonify({'error': 'Itinéraire non trouvé'}), 404
    
    with open(filepath, 'r', encoding='utf-8') as f:
        itineraries = json.load(f)
    
    for i, it in enumerate(itineraries):
        if it.get('id') == itinerary_id and it.get('username') == username:
            if 'title' in data:
                it['title'] = data['title']
            if 'destinations' in data:
                it['destinations'] = data['destinations']
                all_destinations = get_destinations()
                total_cost = 0
                for dest_id in it['destinations']:
                    dest = next((d for d in all_destinations if str(d.get('id')) == str(dest_id)), None)
                    if dest:
                        total_cost += dest.get('avg_cost', 0)
                it['total_cost'] = total_cost
            if 'budget' in data:
                it['budget'] = data['budget']
            if 'time_available' in data:
                it['time_available'] = data['time_available']
            if 'notes' in data:
                it['notes'] = data['notes']
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(itineraries, f, indent=2, ensure_ascii=False)
            
            return jsonify({'message': 'Itinéraire mis à jour', 'itinerary': it}), 200
    
    return jsonify({'error': 'Itinéraire non trouvé'}), 404


# ============================================================
# CREER LE COMPTE DE TEST
# ============================================================

def create_test_user():
    users = get_users()
    if not users:
        test_user = {
            'id': '1',
            'username': 'admin',
            'password_hash': generate_password_hash('admin123'),
            'email': 'admin@test.com',
            'created_at': datetime.now().isoformat()
        }
        users.append(test_user)
        save_users(users)
        print("✅ Compte de test: admin / admin123")


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    
    for filename in ['reviews.json', 'itineraries.json']:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    create_test_user()
    print("="*60)
    print("🚀 Ô'MBOA")
    print("🌐 http://localhost:5000")
    print("📋 Compte de test: admin / admin123")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True)