from flask import Flask, request, jsonify
import json
import os
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'microservices-secret-key-change-in-prod'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')


def get_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def get_user(username):
    for user in get_users():
        if user.get('username') == username:
            return user
    return None


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
    return jsonify({'status': 'ok', 'service': 'user-service'}), 200


@app.route('/register', methods=['POST'])
def register():
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
        'preferences': data.get('preferences', []),
        'created_at': datetime.now().isoformat()
    })
    save_users(users)

    return jsonify({'message': 'Compte créé avec succès !'}), 201


@app.route('/login', methods=['POST'])
def login():
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


@app.route('/me', methods=['GET'])
@login_required
def get_me():
    username = getattr(request, 'username', None)
    user = get_user(username)
    if user:
        safe = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify(safe), 200
    return jsonify({'error': 'Utilisateur non trouvé'}), 404


@app.route('/users', methods=['GET'])
def get_all_users():
    users = get_users()
    safe_users = [{k: v for k, v in u.items() if k != 'password_hash'} for u in users]
    return jsonify(safe_users), 200


@app.route('/users/<username>', methods=['GET'])
def get_user_by_username(username):
    user = get_user(username)
    if user:
        safe = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify(safe), 200
    return jsonify({'error': 'Utilisateur non trouvé'}), 404


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    print("="*50)
    print("🚀 User Service - Port 5001")
    print("="*50)
    app.run(host='0.0.0.0', port=5001, debug=True)