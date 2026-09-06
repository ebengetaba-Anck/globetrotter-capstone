"""
app/chat.py - Blueprint pour le système de messagerie
"""
from flask import Blueprint, render_template, request, jsonify, current_app
import jwt
from functools import wraps
from app.chat_models import *
from app.models import get_user_by_username, get_all_users

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


def get_current_user():
    """Récupérer l'utilisateur courant à partir du token JWT"""
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '')
    if not token:
        token = request.cookies.get('token')
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload.get('sub')
    except:
        return None


def login_required_api(f):
    """Décorateur pour protéger les routes API"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentification requise'}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


# ============================================================
# ROUTES PAGE
# ============================================================

@chat_bp.route('/')
def chat_page():
    """Page principale du chat"""
    user = get_current_user()
    if not user:
        return render_template('login.html')
    return render_template('chat.html')


# ============================================================
# API - CONVERSATIONS
# ============================================================

@chat_bp.route('/api/conversations', methods=['GET'])
@login_required_api
def api_get_conversations():
    """Récupérer toutes les conversations de l'utilisateur"""
    user_id = request.current_user
    
    # Récupérer les utilisateurs pour les noms
    from app.models import get_user_by_username
    user_obj = get_user_by_username(user_id)
    if not user_obj:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    conversations = get_conversations(user_id)
    
    # Enrichir avec les infos des autres participants
    result = []
    for conv in conversations:
        conv_data = dict(conv)
        conv_data['unread_count'] = get_unread_count(conv['id'], user_id)
        
        # Pour les conversations privées, ajouter l'autre participant
        if conv['type'] == 'private':
            other_member = None
            for member in conv['members']:
                if member != user_id:
                    other_member = member
                    break
            if other_member:
                other_user = get_user_by_username(other_member)
                conv_data['other_user'] = {
                    'username': other_member,
                    'avatar': '/static/images/default-avatar.png'
                }
                if other_user:
                    conv_data['other_user']['username'] = other_user.get('username', other_member)
        
        result.append(conv_data)
    
    return jsonify(result), 200


@chat_bp.route('/api/conversations', methods=['POST'])
@login_required_api
def api_create_conversation():
    """Créer une nouvelle conversation"""
    user_id = request.current_user
    data = request.get_json()
    
    other_user = data.get('user_id')
    if not other_user:
        return jsonify({'error': 'user_id requis'}), 400
    
    # Vérifier que l'autre utilisateur existe
    from app.models import get_user_by_username
    if not get_user_by_username(other_user):
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    # Vérifier si une conversation privée existe déjà
    existing = get_private_conversation(user_id, other_user)
    if existing:
        return jsonify(existing), 200
    
    # Créer une nouvelle conversation
    conv = create_conversation([user_id, other_user], type='private')
    return jsonify(conv), 201


@chat_bp.route('/api/conversations/<conversation_id>/messages', methods=['GET'])
@login_required_api
def api_get_messages(conversation_id):
    """Récupérer les messages d'une conversation"""
    user_id = request.current_user
    
    # Vérifier que l'utilisateur est membre de la conversation
    conv = get_conversation(conversation_id)
    if not conv:
        return jsonify({'error': 'Conversation non trouvée'}), 404
    
    if user_id not in conv.get('members', []):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    # Récupérer les messages
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    messages = get_messages(conversation_id, limit, offset)
    
    # Marquer les messages comme lus
    for msg in messages:
        if msg.get('sender_id') != user_id:
            mark_message_read(msg['id'], user_id)
    
    return jsonify(messages), 200


@chat_bp.route('/api/conversations/<conversation_id>/unread', methods=['GET'])
@login_required_api
def api_get_unread_count(conversation_id):
    """Récupérer le nombre de messages non lus"""
    user_id = request.current_user
    
    conv = get_conversation(conversation_id)
    if not conv:
        return jsonify({'error': 'Conversation non trouvée'}), 404
    
    if user_id not in conv.get('members', []):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    count = get_unread_count(conversation_id, user_id)
    return jsonify({'unread_count': count}), 200


# ============================================================
# API - MESSAGES
# ============================================================

@chat_bp.route('/api/messages', methods=['POST'])
@login_required_api
def api_send_message():
    """Envoyer un message"""
    user_id = request.current_user
    data = request.get_json()
    
    conversation_id = data.get('conversation_id')
    content = data.get('content', '').strip()
    message_type = data.get('type', 'text')
    destination_id = data.get('destination_id')
    
    if not conversation_id:
        return jsonify({'error': 'conversation_id requis'}), 400
    
    # Vérifier que l'utilisateur est membre de la conversation
    conv = get_conversation(conversation_id)
    if not conv:
        return jsonify({'error': 'Conversation non trouvée'}), 404
    
    if user_id not in conv.get('members', []):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    # Vérifier les blocages
    for member in conv.get('members', []):
        if member != user_id and is_user_blocked(user_id, member):
            return jsonify({'error': 'Utilisateur bloqué'}), 403
    
    # Limiter la taille du message
    if len(content) > 10000:
        return jsonify({'error': 'Message trop long'}), 400
    
    # Créer le message
    message = create_message(
        conversation_id=conversation_id,
        sender_id=user_id,
        content=content,
        type=message_type,
        destination_id=destination_id
    )
    
    # Mettre à jour la conversation
    update_conversation(conversation_id, {
        'last_message_id': message['id'],
        'last_message_preview': content[:100] if content else '',
        'last_message_at': message['created_at']
    })
    
    return jsonify(message), 201


@chat_bp.route('/api/messages/<message_id>', methods=['DELETE'])
@login_required_api
def api_delete_message(message_id):
    """Supprimer un message"""
    user_id = request.current_user
    
    message = get_message(message_id)
    if not message:
        return jsonify({'error': 'Message non trouvé'}), 404
    
    # Seul l'expéditeur peut supprimer son message
    if message.get('sender_id') != user_id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    if delete_message(message_id, user_id):
        return jsonify({'message': 'Message supprimé'}), 200
    
    return jsonify({'error': 'Erreur lors de la suppression'}), 500


# ============================================================
# API - RÉACTIONS
# ============================================================

@chat_bp.route('/api/messages/<message_id>/reactions', methods=['POST'])
@login_required_api
def api_add_reaction(message_id):
    """Ajouter une réaction à un message"""
    user_id = request.current_user
    data = request.get_json()
    reaction = data.get('reaction', '').strip()
    
    if not reaction or len(reaction) > 2:
        return jsonify({'error': 'Réaction invalide'}), 400
    
    if add_reaction(message_id, user_id, reaction):
        return jsonify({'message': 'Réaction ajoutée'}), 200
    
    return jsonify({'error': 'Erreur'}), 500


# ============================================================
# API - BLOCAGES
# ============================================================

@chat_bp.route('/api/users/<user_id>/block', methods=['POST'])
@login_required_api
def api_block_user(user_id):
    """Bloquer un utilisateur"""
    blocker_id = request.current_user
    
    if blocker_id == user_id:
        return jsonify({'error': 'Vous ne pouvez pas vous bloquer vous-même'}), 400
    
    if block_user(blocker_id, user_id):
        return jsonify({'message': 'Utilisateur bloqué'}), 200
    
    return jsonify({'error': 'Erreur'}), 500


@chat_bp.route('/api/users/<user_id>/unblock', methods=['POST'])
@login_required_api
def api_unblock_user(user_id):
    """Débloquer un utilisateur"""
    blocker_id = request.current_user
    
    if unblock_user(blocker_id, user_id):
        return jsonify({'message': 'Utilisateur débloqué'}), 200
    
    return jsonify({'error': 'Erreur'}), 500


# ============================================================
# API - SIGNALEMENTS
# ============================================================

@chat_bp.route('/api/reports', methods=['POST'])
@login_required_api
def api_create_report():
    """Signaler un message ou un utilisateur"""
    reporter_id = request.current_user
    data = request.get_json()
    
    reported_user_id = data.get('reported_user_id')
    message_id = data.get('message_id')
    reason = data.get('reason', '').strip()
    description = data.get('description', '').strip()
    
    if not reported_user_id and not message_id:
        return jsonify({'error': 'reported_user_id ou message_id requis'}), 400
    
    if not reason:
        return jsonify({'error': 'Motif requis'}), 400
    
    report = create_report(reporter_id, reported_user_id, message_id, reason, description)
    return jsonify(report), 201


@chat_bp.route('/api/users/search', methods=['GET'])
@login_required_api
def api_search_users():
    """Rechercher des utilisateurs"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([]), 200
    
    from app.models import get_all_users
    users = get_all_users()
    
    results = []
    for user in users:
        username = user.get('username', '')
        if query.lower() in username.lower():
            results.append({
                'username': username,
                'avatar': '/static/images/default-avatar.png'
            })
    
    return jsonify(results[:20]), 200