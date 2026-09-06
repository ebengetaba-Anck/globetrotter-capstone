"""
app/chat_events.py - Gestionnaires WebSocket pour le chat
"""
from flask_socketio import emit, join_room, leave_room, disconnect
from app.chat_models import (
    get_conversation, get_message, create_message,
    mark_message_read, get_unread_count,
    is_user_blocked, update_conversation
)
from app.models import get_user_by_username

# Stockage temporaire des utilisateurs connectés
connected_users = {}
typing_users = {}


def register_socket_handlers(socketio):
    """Enregistrer tous les gestionnaires Socket.IO"""

    @socketio.on('connect')
    def handle_connect():
        """Un utilisateur se connecte"""
        from flask import request
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return False
        
        try:
            import jwt
            from flask import current_app
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            username = payload.get('sub')
            
            if username:
                connected_users[username] = request.sid
                print(f"🟢 {username} connecté")
                
                # Notifier les autres utilisateurs
                emit('user_online', {'username': username}, broadcast=True)
                return True
        except:
            return False
        
        return False

    @socketio.on('disconnect')
    def handle_disconnect():
        """Un utilisateur se déconnecte"""
        from flask import request
        username = None
        for user, sid in connected_users.items():
            if sid == request.sid:
                username = user
                break
        
        if username:
            del connected_users[username]
            print(f"🔴 {username} déconnecté")
            emit('user_offline', {'username': username}, broadcast=True)

    @socketio.on('join_conversation')
    def handle_join_conversation(data):
        """Rejoindre une conversation"""
        from flask import request
        
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return
        
        # Vérifier que l'utilisateur est membre
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return
        
        try:
            import jwt
            from flask import current_app
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            username = payload.get('sub')
            
            if not username:
                return
            
            conv = get_conversation(conversation_id)
            if not conv or username not in conv.get('members', []):
                return
            
            join_room(conversation_id)
            print(f"📥 {username} a rejoint la conversation {conversation_id}")
            
            # Envoyer le statut des messages non lus
            unread = get_unread_count(conversation_id, username)
            emit('unread_count', {'conversation_id': conversation_id, 'count': unread}, room=request.sid)
            
        except Exception as e:
            print(f"Erreur join_conversation: {e}")

    @socketio.on('leave_conversation')
    def handle_leave_conversation(data):
        """Quitter une conversation"""
        conversation_id = data.get('conversation_id')
        if conversation_id:
            leave_room(conversation_id)
            print(f"📤 Utilisateur a quitté la conversation {conversation_id}")

    @socketio.on('send_message')
    def handle_send_message(data):
        """Envoyer un message"""
        from flask import request
        
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        message_type = data.get('type', 'text')
        destination_id = data.get('destination_id')
        
        if not conversation_id or not content:
            emit('error', {'message': 'Données invalides'})
            return
        
        # Vérifier l'utilisateur
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            emit('error', {'message': 'Non authentifié'})
            return
        
        try:
            import jwt
            from flask import current_app
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            username = payload.get('sub')
            
            if not username:
                emit('error', {'message': 'Utilisateur invalide'})
                return
            
            # Vérifier la conversation
            conv = get_conversation(conversation_id)
            if not conv or username not in conv.get('members', []):
                emit('error', {'message': 'Accès non autorisé'})
                return
            
            # Vérifier les blocages
            for member in conv.get('members', []):
                if member != username and is_user_blocked(username, member):
                    emit('error', {'message': 'Utilisateur bloqué'})
                    return
            
            # Créer le message
            message = create_message(
                conversation_id=conversation_id,
                sender_id=username,
                content=content,
                type=message_type,
                destination_id=destination_id
            )
            
            # Mettre à jour la conversation
            update_conversation(conversation_id, {
                'last_message_id': message['id'],
                'last_message_preview': content[:100],
                'last_message_at': message['created_at']
            })
            
            # Ajouter le nom de l'expéditeur
            message['sender_name'] = username
            
            # Envoyer à tous les membres de la conversation
            emit('new_message', message, room=conversation_id)
            
            # Envoyer un accusé de réception à l'expéditeur
            emit('message_delivered', {'message_id': message['id']}, room=request.sid)
            
        except Exception as e:
            print(f"❌ Erreur send_message: {e}")
            emit('error', {'message': 'Erreur lors de l\'envoi'})

    @socketio.on('typing_start')
    def handle_typing_start(data):
        """L'utilisateur commence à taper"""
        from flask import request
        
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return
        
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return
        
        try:
            import jwt
            from flask import current_app
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            username = payload.get('sub')
            
            if not username:
                return
            
            conv = get_conversation(conversation_id)
            if not conv or username not in conv.get('members', []):
                return
            
            # Envoyer à tous les membres sauf l'expéditeur
            emit('typing', {'user': username, 'conversation_id': conversation_id}, room=conversation_id, include_self=False)
            
        except Exception as e:
            print(f"Erreur typing_start: {e}")

    @socketio.on('typing_stop')
    def handle_typing_stop(data):
        """L'utilisateur arrête de taper"""
        from flask import request
        
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return
        
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return
        
        try:
            import jwt
            from flask import current_app
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            username = payload.get('sub')
            
            if not username:
                return
            
            # Envoyer à tous les membres sauf l'expéditeur
            emit('typing_stop', {'user': username, 'conversation_id': conversation_id}, room=conversation_id, include_self=False)
            
        except Exception as e:
            print(f"Erreur typing_stop: {e}")

    @socketio.on('mark_read')
    def handle_mark_read(data):
        """Marquer un message comme lu"""
        from flask import request
        
        message_id = data.get('message_id')
        if not message_id:
            return
        
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return
        
        try:
            import jwt
            from flask import current_app
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            username = payload.get('sub')
            
            if not username:
                return
            
            message = get_message(message_id)
            if not message:
                return
            
            conv = get_conversation(message.get('conversation_id'))
            if not conv or username not in conv.get('members', []):
                return
            
            mark_message_read(message_id, username)
            
            # Notifier les autres membres
            emit('message_read', {'message_id': message_id, 'user': username}, room=message.get('conversation_id'), include_self=False)
            
        except Exception as e:
            print(f"Erreur mark_read: {e}")