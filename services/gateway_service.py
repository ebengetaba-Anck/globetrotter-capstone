from flask import Flask, request, jsonify, render_template, send_from_directory
from functools import wraps
import os
import requests
import json
import jwt
from datetime import datetime

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "templates"),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static"))

app.config['SECRET_KEY'] = 'microservices-secret-key-change-in-prod'

USER_SERVICE = "http://localhost:5001"
ITINERARY_SERVICE = "http://localhost:5002"
RECOMMENDATION_SERVICE = "http://localhost:5003"


def route_request(url, method='GET', data=None, headers=None, params=None):
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        else:
            return jsonify({'error': 'Méthode non supportée'}), 405
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Service non disponible'}), 503


# ============================================================
# CHAT INTÉGRÉ (Directement dans le gateway)
# ============================================================

CHAT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


def chat_read_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def chat_write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def chat_get_user_from_token():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload.get('sub')
    except:
        return None


def chat_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = chat_get_user_from_token()
        if not user:
            return jsonify({'error': 'Authentification requise'}), 401
        request.chat_user = user
        return f(*args, **kwargs)
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


@app.route('/recommendations')
def recommendations_page():
    return render_template('recommendations.html')


@app.route('/destination')
def destination_detail():
    dest_id = request.args.get('id')
    return render_template('destination_details.html', destination={'id': dest_id})


@app.route('/chat')
def chat_page():
    """Page de messagerie"""
    return render_template('chat.html')


@app.route('/gallery/<dest_id>')
def gallery_page(dest_id):
    return render_template('gallery.html', destination={'id': dest_id})


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ============================================================
# ROUTES API
# ============================================================

@app.route('/api/register', methods=['POST'])
def api_register():
    return route_request(f"{USER_SERVICE}/register", 'POST', request.get_json())


@app.route('/api/login', methods=['POST'])
def api_login():
    return route_request(f"{USER_SERVICE}/login", 'POST', request.get_json())


@app.route('/api/me', methods=['GET'])
def api_me():
    return route_request(f"{USER_SERVICE}/me", 'GET', headers=request.headers)


@app.route('/api/destinations', methods=['GET'])
def api_destinations():
    return route_request(f"{RECOMMENDATION_SERVICE}/destinations", 'GET')


@app.route('/api/recommendations', methods=['GET'])
def api_recommendations():
    return route_request(f"{RECOMMENDATION_SERVICE}/recommendations", 'GET', headers=request.headers)


@app.route('/api/recommendations/personalized', methods=['GET'])
def api_recommendations_personalized():
    return route_request(f"{RECOMMENDATION_SERVICE}/recommendations/personalized", 'GET', headers=request.headers)


@app.route('/api/itineraries', methods=['GET', 'POST'])
def api_itineraries():
    if request.method == 'GET':
        return route_request(f"{ITINERARY_SERVICE}/itineraries", 'GET', headers=request.headers)
    else:
        return route_request(f"{ITINERARY_SERVICE}/itineraries", 'POST', request.get_json(), request.headers)


@app.route('/api/itineraries/<itinerary_id>', methods=['DELETE', 'PUT'])
def api_itinerary_detail(itinerary_id):
    if request.method == 'DELETE':
        return route_request(f"{ITINERARY_SERVICE}/itineraries/{itinerary_id}", 'DELETE', headers=request.headers)
    else:
        return route_request(f"{ITINERARY_SERVICE}/itineraries/{itinerary_id}", 'PUT', request.get_json(), request.headers)


@app.route('/api/reviews', methods=['GET', 'POST'])
def api_reviews():
    if request.method == 'GET':
        return route_request(f"{RECOMMENDATION_SERVICE}/reviews", 'GET', params=request.args)
    else:
        return route_request(f"{RECOMMENDATION_SERVICE}/reviews", 'POST', request.get_json(), request.headers)


@app.route('/api/build-itinerary', methods=['POST'])
def api_build_itinerary():
    return route_request(f"{RECOMMENDATION_SERVICE}/build-itinerary", 'POST', request.get_json(), request.headers)


# ============================================================
# ROUTES CHAT (intégrées - PAS DE SERVICE EXTERNE)
# ============================================================

@app.route('/api/chat/conversations', methods=['POST'])
@chat_login_required
def chat_create_conversation():
    user_id = request.chat_user
    data = request.get_json()
    other_user = data.get('user_id')
    
    if not other_user:
        return jsonify({'error': 'user_id requis'}), 400
    
    users = chat_read_json(os.path.join(CHAT_DATA_DIR, 'users.json'))
    found = False
    for u in users:
        if u.get('username') == other_user:
            found = True
            break
    if not found:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    conv_file = os.path.join(CHAT_DATA_DIR, 'conversations.json')
    convs = chat_read_json(conv_file)
    
    for conv in convs:
        if user_id in conv.get('members', []) and other_user in conv.get('members', []):
            return jsonify({
                'id': conv.get('id'),
                'type': 'private',
                'other_user': {'username': other_user}
            }), 200
    
    import time
    new_conv = {
        'id': str(int(time.time() * 1000)),
        'type': 'private',
        'members': [user_id, other_user],
        'created_at': datetime.now().isoformat(),
        'last_message_preview': '',
        'last_message_at': None
    }
    convs.append(new_conv)
    chat_write_json(conv_file, convs)
    
    return jsonify({
        'id': new_conv['id'],
        'type': 'private',
        'other_user': {'username': other_user}
    }), 201


@app.route('/api/chat/conversations', methods=['GET'])
@chat_login_required
def chat_get_conversations():
    user_id = request.chat_user
    conv_file = os.path.join(CHAT_DATA_DIR, 'conversations.json')
    all_convs = chat_read_json(conv_file)
    
    result = []
    for conv in all_convs:
        if user_id in conv.get('members', []):
            other = None
            for m in conv.get('members', []):
                if m != user_id:
                    other = m
                    break
            result.append({
                'id': conv.get('id'),
                'type': conv.get('type', 'private'),
                'other_user': {'username': other} if other else None,
                'last_message_preview': conv.get('last_message_preview', ''),
                'last_message_at': conv.get('last_message_at'),
                'unread_count': 0
            })
    
    return jsonify(result), 200


@app.route('/api/chat/conversations/<conv_id>/messages', methods=['GET'])
@chat_login_required
def chat_get_messages(conv_id):
    user_id = request.chat_user
    
    conv_file = os.path.join(CHAT_DATA_DIR, 'conversations.json')
    convs = chat_read_json(conv_file)
    conv = None
    for c in convs:
        if c.get('id') == conv_id:
            conv = c
            break
    
    if not conv or user_id not in conv.get('members', []):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    msg_file = os.path.join(CHAT_DATA_DIR, 'messages.json')
    all_msgs = chat_read_json(msg_file)
    
    conv_msgs = [m for m in all_msgs if m.get('conversation_id') == conv_id]
    conv_msgs.sort(key=lambda x: x.get('created_at', ''))
    
    return jsonify(conv_msgs), 200


@app.route('/api/chat/messages', methods=['POST'])
@chat_login_required
def chat_send_message():
    user_id = request.chat_user
    data = request.get_json()
    conv_id = data.get('conversation_id')
    content = data.get('content', '').strip()
    
    if not conv_id or not content:
        return jsonify({'error': 'Données invalides'}), 400
    
    conv_file = os.path.join(CHAT_DATA_DIR, 'conversations.json')
    convs = chat_read_json(conv_file)
    conv = None
    for c in convs:
        if c.get('id') == conv_id:
            conv = c
            break
    
    if not conv or user_id not in conv.get('members', []):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    msg = {
        'id': str(int(datetime.now().timestamp() * 1000)),
        'conversation_id': conv_id,
        'sender_id': user_id,
        'content': content,
        'type': 'text',
        'created_at': datetime.now().isoformat()
    }
    
    msg_file = os.path.join(CHAT_DATA_DIR, 'messages.json')
    all_msgs = chat_read_json(msg_file)
    all_msgs.append(msg)
    chat_write_json(msg_file, all_msgs)
    
    for c in convs:
        if c.get('id') == conv_id:
            c['last_message_preview'] = content[:100]
            c['last_message_at'] = msg['created_at']
            break
    chat_write_json(conv_file, convs)
    
    return jsonify(msg), 201


@app.route('/api/chat/users/search', methods=['GET'])
@chat_login_required
def chat_search_users():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([]), 200
    
    users_file = os.path.join(CHAT_DATA_DIR, 'users.json')
    users = chat_read_json(users_file)
    
    results = []
    for user in users:
        username = user.get('username', '')
        if query.lower() in username.lower():
            results.append({'username': username})
    
    return jsonify(results[:20]), 200

@app.route('/api/chat/messages/<message_id>', methods=['DELETE'])
@chat_login_required
def chat_delete_message(message_id):
    user_id = request.chat_user
    
    # Lire tous les messages
    msg_file = os.path.join(CHAT_DATA_DIR, 'messages.json')
    all_msgs = chat_read_json(msg_file)
    
    # Trouver le message
    for i, msg in enumerate(all_msgs):
        if msg.get('id') == message_id:
            # Seul l'expéditeur peut supprimer son message
            if msg.get('sender_id') != user_id:
                return jsonify({'error': 'Non autorisé'}), 403
            
            # Supprimer le message (soft delete)
            all_msgs[i]['deleted'] = True
            all_msgs[i]['content'] = '[Message supprimé]'
            chat_write_json(msg_file, all_msgs)
            return jsonify({'message': 'Message supprimé'}), 200
    
    return jsonify({'error': 'Message non trouvé'}), 404

# ============================================================
# ROUTES CHAT - FONCTIONNALITÉS SUPPLÉMENTAIRES
# ============================================================

@app.route('/api/chat/messages/<message_id>/read', methods=['POST'])
@chat_login_required
def chat_mark_read(message_id):
    user_id = request.chat_user
    from app.chat_models import mark_message_read
    if mark_message_read(message_id, user_id):
        return jsonify({'message': 'Marqué comme lu'}), 200
    return jsonify({'error': 'Erreur'}), 500


@app.route('/api/chat/conversations/<conv_id>/read', methods=['POST'])
@chat_login_required
def chat_mark_all_read(conv_id):
    user_id = request.chat_user
    from app.chat_models import mark_all_read
    if mark_all_read(conv_id, user_id):
        return jsonify({'message': 'Tous les messages sont lus'}), 200
    return jsonify({'error': 'Erreur'}), 500

if __name__ == '__main__':
    print("="*60)
    print("🚀 API GATEWAY - Port 5000")
    print("🌐 http://localhost:5000")
    print("📋 Services: User(5001), Itinerary(5002), Recommendation(5003)")
    print("📋 Chat intégré (pas de service externe)")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True)