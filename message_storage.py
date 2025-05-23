import json
import os
from datetime import datetime

MESSAGES_FILE = "chat_messages.json"

def load_messages():
    """Charge tous les messages depuis le fichier"""
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_messages(messages):
    """Sauvegarde tous les messages dans le fichier"""
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=4)

def add_message(sender, receiver, message, is_group=False):
    """
    Ajoute un message à l'historique
    :param sender: L'expéditeur du message
    :param receiver: Le destinataire ou le nom du groupe
    :param message: Le contenu du message
    :param is_group: True si c'est un message de groupe
    """
    messages = load_messages()
    
    if is_group:
        key = f"group_{receiver}"
    else:
        # Crée une clé unique pour la paire d'utilisateurs (triée alphabétiquement)
        key = f"{sorted([sender, receiver])[0]}_{sorted([sender, receiver])[1]}"
    
    if key not in messages:
        messages[key] = []
    
    messages[key].append({
        "sender": sender,
        "message": message,
        "timestamp": str(datetime.now())  # Optionnel pour l'heure
    })
    
    save_messages(messages)

def get_messages(user1, user2=None, group_name=None):
    """
    Récupère l'historique des messages
    :param user1: Premier utilisateur
    :param user2: Deuxième utilisateur (None pour les groupes)
    :param group_name: Nom du groupe (None pour les conversations privées)
    """
    messages = load_messages()
    
    if group_name:
        key = f"group_{group_name}"
    else:
        key = f"{sorted([user1, user2])[0]}_{sorted([user1, user2])[1]}"
    
    return messages.get(key, [])