from flask import Flask, jsonify, request
import sys
import os
import json
import jwt
from datetime import datetime
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'microservices-secret-key-change-in-prod'

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


# ============================================================
# FONCTIONS DE BASE
# ============================================================

def read_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user_from_token():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload.get('sub')
    except:
        return None


def get_user_by_username(username):
    users_file = os.path.join(DATA_DIR, 'users.json')
    users = read_json(users_file)
    for user in users:
        if user.get('username') == username:
            return user
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_user_from_token()
        if not user:
            return jsonify({'error': 'Authentification requise'}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


# ============================================================
# API ROUTES
# ============================================================

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'chat-service'}), 200


@app.route('/api/conversations', methods=['POST'])
@login_required
def create_conversation():
    user_id = request.current_user
    data = request.get_json()
    other_user = data.get('user_id')
    
    if not other_user:
        return jsonify({'error': 'user_id requis'}), 400
    
    if not get_user_by_username(other_user):
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    conv_file = os.path.join(DATA_DIR, 'conversations.json')
    convs = read_json(conv_file)
    
    # Vérifier si une conversation existe déjà
    for conv in convs:
        if user_id in conv.get('members', []) and other_user in conv.get('members', []):
            return jsonify({
                'id': conv.get('id'),
                'type': 'private',
                'other_user': {'username': other_user}
            }), 200
    
    # Créer une nouvelle conversation
    new_conv = {
        'id': str(len(convs) + 1) + '_' + datetime.now().strftime('%Y%m%d%H%M%S'),
        'type': 'private',
        'members': [user_id, other_user],
        'created_at': datetime.now().isoformat(),
        'last_message_preview': '',
        'last_message_at': None
    }
    convs.append(new_conv)
    write_json(conv_file, convs)
    
    return jsonify({
        'id': new_conv['id'],
        'type': 'private',
        'other_user': {'username': other_user}
    }), 201


@app.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    user_id = request.current_user
    conv_file = os.path.join(DATA_DIR, 'conversations.json')
    all_convs = read_json(conv_file)
    
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


@app.route('/api/conversations/<conv_id>/messages', methods=['GET'])
@login_required
def get_messages(conv_id):
    user_id = request.current_user
    conv_file = os.path.join(DATA_DIR, 'conversations.json')
    convs = read_json(conv_file)
    
    conv = None
    for c in convs:
        if c.get('id') == conv_id:
            conv = c
            break
    
    if not conv or user_id not in conv.get('members', []):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    msg_file = os.path.join(DATA_DIR, 'messages.json')
    all_msgs = read_json(msg_file)
    
    conv_msgs = [m for m in all_msgs if m.get('conversation_id') == conv_id]
    conv_msgs.sort(key=lambda x: x.get('created_at', ''))
    
    return jsonify(conv_msgs), 200


@app.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    user_id = request.current_user
    data = request.get_json()
    conv_id = data.get('conversation_id')
    content = data.get('content', '').strip()
    
    if not conv_id or not content:
        return jsonify({'error': 'Données invalides'}), 400
    
    conv_file = os.path.join(DATA_DIR, 'conversations.json')
    convs = read_json(conv_file)
    
    conv = None
    for c in convs:
        if c.get('id') == conv_id:
            conv = c
            break
    
    if not conv or user_id not in conv.get('members', []):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    msg = {
        'id': str(len(read_json(os.path.join(DATA_DIR, 'messages.json'))) + 1),
        'conversation_id': conv_id,
        'sender_id': user_id,
        'content': content,
        'type': 'text',
        'created_at': datetime.now().isoformat()
    }
    
    msg_file = os.path.join(DATA_DIR, 'messages.json')
    all_msgs = read_json(msg_file)
    all_msgs.append(msg)
    write_json(msg_file, all_msgs)
    
    # Mettre à jour la conversation
    for c in convs:
        if c.get('id') == conv_id:
            c['last_message_preview'] = content[:100]
            c['last_message_at'] = msg['created_at']
            break
    write_json(conv_file, convs)
    
    return jsonify(msg), 201


@app.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([]), 200
    
    users_file = os.path.join(DATA_DIR, 'users.json')
    users = read_json(users_file)
    
    results = []
    for user in users:
        username = user.get('username', '')
        if query.lower() in username.lower():
            results.append({'username': username})
    
    return jsonify(results[:20]), 200


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    print("="*50)
    print("🚀 Chat Service Simple - Port 5004")
    print("="*50)
    app.run(host='0.0.0.0', port=5004, debug=True)