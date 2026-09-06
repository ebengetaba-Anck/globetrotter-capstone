"""
app/chat_models.py - Modèles de données pour le système de messagerie
"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Fichiers de données
CONVERSATIONS_FILE = os.path.join(DATA_DIR, 'conversations.json')
MESSAGES_FILE = os.path.join(DATA_DIR, 'messages.json')
MESSAGE_READS_FILE = os.path.join(DATA_DIR, 'message_reads.json')
MESSAGE_REACTIONS_FILE = os.path.join(DATA_DIR, 'message_reactions.json')
USER_BLOCKS_FILE = os.path.join(DATA_DIR, 'user_blocks.json')
REPORTS_FILE = os.path.join(DATA_DIR, 'reports.json')


def _read_json(filepath: str) -> list:
    """Lire un fichier JSON"""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return []


def _write_json(filepath: str, data: list) -> None:
    """Écrire un fichier JSON"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# CONVERSATIONS
# ============================================================

def get_conversations(user_id: str) -> List[Dict]:
    """Récupérer toutes les conversations d'un utilisateur"""
    all_convs = _read_json(CONVERSATIONS_FILE)
    user_convs = []
    
    for conv in all_convs:
        members = conv.get('members', [])
        if user_id in members:
            user_convs.append(conv)
    
    return user_convs


def get_conversation(conversation_id: str) -> Optional[Dict]:
    """Récupérer une conversation par son ID"""
    all_convs = _read_json(CONVERSATIONS_FILE)
    for conv in all_convs:
        if conv.get('id') == conversation_id:
            return conv
    return None


def get_private_conversation(user1_id: str, user2_id: str) -> Optional[Dict]:
    """Récupérer une conversation privée entre deux utilisateurs"""
    all_convs = _read_json(CONVERSATIONS_FILE)
    for conv in all_convs:
        if conv.get('type') != 'private':
            continue
        members = conv.get('members', [])
        if user1_id in members and user2_id in members and len(members) == 2:
            return conv
    return None


def create_conversation(user_ids: List[str], name: str = None, type: str = 'private') -> Dict:
    """Créer une nouvelle conversation"""
    conv = {
        'id': str(uuid.uuid4()),
        'type': type,
        'name': name or '',
        'members': user_ids,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'last_message_id': None,
        'last_message_preview': '',
        'last_message_at': None
    }
    
    conversations = _read_json(CONVERSATIONS_FILE)
    conversations.append(conv)
    _write_json(CONVERSATIONS_FILE, conversations)
    return conv


def update_conversation(conversation_id: str, updates: Dict) -> Optional[Dict]:
    """Mettre à jour une conversation"""
    conversations = _read_json(CONVERSATIONS_FILE)
    for i, conv in enumerate(conversations):
        if conv.get('id') == conversation_id:
            conv.update(updates)
            conv['updated_at'] = datetime.now().isoformat()
            conversations[i] = conv
            _write_json(CONVERSATIONS_FILE, conversations)
            return conv
    return None


def add_member_to_conversation(conversation_id: str, user_id: str) -> bool:
    """Ajouter un membre à une conversation"""
    conv = get_conversation(conversation_id)
    if not conv:
        return False
    if user_id not in conv.get('members', []):
        conv['members'].append(user_id)
        _write_json(CONVERSATIONS_FILE, _read_json(CONVERSATIONS_FILE))
        return True
    return False


# ============================================================
# MESSAGES
# ============================================================

def get_messages(conversation_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
    """Récupérer les messages d'une conversation"""
    all_messages = _read_json(MESSAGES_FILE)
    conv_messages = [m for m in all_messages if m.get('conversation_id') == conversation_id]
    conv_messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return conv_messages[offset:offset + limit]


def get_message(message_id: str) -> Optional[Dict]:
    """Récupérer un message par son ID"""
    all_messages = _read_json(MESSAGES_FILE)
    for msg in all_messages:
        if msg.get('id') == message_id:
            return msg
    return None


def create_message(
    conversation_id: str,
    sender_id: str,
    content: str,
    type: str = 'text',
    media_url: str = None,
    mime_type: str = None,
    file_size: int = None,
    duration: int = None,
    destination_id: str = None,
    latitude: float = None,
    longitude: float = None,
    reply_to_message_id: str = None
) -> Dict:
    """Créer un nouveau message"""
    message = {
        'id': str(uuid.uuid4()),
        'conversation_id': conversation_id,
        'sender_id': sender_id,
        'type': type,
        'content': content,
        'media_url': media_url,
        'thumbnail_url': None,
        'mime_type': mime_type,
        'file_size': file_size,
        'duration': duration,
        'destination_id': destination_id,
        'latitude': latitude,
        'longitude': longitude,
        'reply_to_message_id': reply_to_message_id,
        'created_at': datetime.now().isoformat(),
        'edited_at': None,
        'deleted_at': None
    }
    
    messages = _read_json(MESSAGES_FILE)
    messages.append(message)
    _write_json(MESSAGES_FILE, messages)
    
    # Mettre à jour la conversation
    update_conversation(conversation_id, {
        'last_message_id': message['id'],
        'last_message_preview': content[:100] if content else '',
        'last_message_at': message['created_at']
    })
    
    return message


def delete_message(message_id: str, user_id: str, hard_delete: bool = False) -> bool:
    """Supprimer un message (soft delete par défaut)"""
    messages = _read_json(MESSAGES_FILE)
    for i, msg in enumerate(messages):
        if msg.get('id') == message_id:
            if msg.get('sender_id') != user_id:
                return False
            if hard_delete:
                messages.pop(i)
            else:
                msg['deleted_at'] = datetime.now().isoformat()
                msg['content'] = '[Ce message a été supprimé]'
                messages[i] = msg
            _write_json(MESSAGES_FILE, messages)
            return True
    return False


# ============================================================
# MESSAGES LUS
# ============================================================

def mark_message_read(message_id: str, user_id: str) -> bool:
    """Marquer un message comme lu"""
    reads = _read_json(MESSAGE_READS_FILE)
    
    # Vérifier si déjà lu
    for read in reads:
        if read.get('message_id') == message_id and read.get('user_id') == user_id:
            return True
    
    read = {
        'id': str(uuid.uuid4()),
        'message_id': message_id,
        'user_id': user_id,
        'read_at': datetime.now().isoformat()
    }
    reads.append(read)
    _write_json(MESSAGE_READS_FILE, reads)
    return True


def get_message_reads(message_id: str) -> List[Dict]:
    """Récupérer les lectures d'un message"""
    all_reads = _read_json(MESSAGE_READS_FILE)
    return [r for r in all_reads if r.get('message_id') == message_id]


def get_unread_count(conversation_id: str, user_id: str) -> int:
    """Récupérer le nombre de messages non lus dans une conversation"""
    messages = get_messages(conversation_id, limit=1000)
    reads = _read_json(MESSAGE_READS_FILE)
    
    unread = 0
    for msg in messages:
        if msg.get('sender_id') == user_id:
            continue
        read = any(r.get('message_id') == msg.get('id') and r.get('user_id') == user_id for r in reads)
        if not read:
            unread += 1
    return unread


# ============================================================
# RÉACTIONS
# ============================================================

def add_reaction(message_id: str, user_id: str, reaction: str) -> bool:
    """Ajouter une réaction à un message"""
    reactions = _read_json(MESSAGE_REACTIONS_FILE)
    
    # Supprimer une réaction existante du même utilisateur
    for r in reactions:
        if r.get('message_id') == message_id and r.get('user_id') == user_id:
            reactions.remove(r)
    
    # Ajouter la nouvelle réaction
    new_reaction = {
        'id': str(uuid.uuid4()),
        'message_id': message_id,
        'user_id': user_id,
        'reaction': reaction,
        'created_at': datetime.now().isoformat()
    }
    reactions.append(new_reaction)
    _write_json(MESSAGE_REACTIONS_FILE, reactions)
    return True


def get_message_reactions(message_id: str) -> List[Dict]:
    """Récupérer les réactions d'un message"""
    all_reactions = _read_json(MESSAGE_REACTIONS_FILE)
    return [r for r in all_reactions if r.get('message_id') == message_id]


# ============================================================
# BLOCAGES
# ============================================================

def block_user(blocker_id: str, blocked_id: str) -> bool:
    """Bloquer un utilisateur"""
    if blocker_id == blocked_id:
        return False
    
    blocks = _read_json(USER_BLOCKS_FILE)
    
    # Vérifier si déjà bloqué
    for b in blocks:
        if b.get('blocker_id') == blocker_id and b.get('blocked_id') == blocked_id:
            return True
    
    block = {
        'id': str(uuid.uuid4()),
        'blocker_id': blocker_id,
        'blocked_id': blocked_id,
        'created_at': datetime.now().isoformat()
    }
    blocks.append(block)
    _write_json(USER_BLOCKS_FILE, blocks)
    return True


def unblock_user(blocker_id: str, blocked_id: str) -> bool:
    """Débloquer un utilisateur"""
    blocks = _read_json(USER_BLOCKS_FILE)
    new_blocks = [b for b in blocks if not (b.get('blocker_id') == blocker_id and b.get('blocked_id') == blocked_id)]
    if len(new_blocks) != len(blocks):
        _write_json(USER_BLOCKS_FILE, new_blocks)
        return True
    return False


def is_user_blocked(blocker_id: str, blocked_id: str) -> bool:
    """Vérifier si un utilisateur est bloqué"""
    blocks = _read_json(USER_BLOCKS_FILE)
    for b in blocks:
        if b.get('blocker_id') == blocker_id and b.get('blocked_id') == blocked_id:
            return True
        if b.get('blocker_id') == blocked_id and b.get('blocked_id') == blocker_id:
            return True
    return False


# ============================================================
# SIGNALEMENTS
# ============================================================

def create_report(
    reporter_id: str,
    reported_user_id: str = None,
    message_id: str = None,
    reason: str = '',
    description: str = ''
) -> Dict:
    """Créer un signalement"""
    report = {
        'id': str(uuid.uuid4()),
        'reporter_id': reporter_id,
        'reported_user_id': reported_user_id,
        'message_id': message_id,
        'reason': reason,
        'description': description,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'resolved_at': None
    }
    
    reports = _read_json(REPORTS_FILE)
    reports.append(report)
    _write_json(REPORTS_FILE, reports)
    return report


def get_reports(status: str = None) -> List[Dict]:
    """Récupérer les signalements"""
    reports = _read_json(REPORTS_FILE)
    if status:
        return [r for r in reports if r.get('status') == status]
    return reports


def resolve_report(report_id: str) -> bool:
    """Résoudre un signalement"""
    reports = _read_json(REPORTS_FILE)
    for r in reports:
        if r.get('id') == report_id:
            r['status'] = 'resolved'
            r['resolved_at'] = datetime.now().isoformat()
            _write_json(REPORTS_FILE, reports)
            return True
    return False