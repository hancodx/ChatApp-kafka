import json
import os
from datetime import datetime

class MessageStorage:
    def __init__(self):
        self.MESSAGES_FILE = "chat_messages.json"
        self.ensure_storage_file()

    def ensure_storage_file(self):
        """Crée le fichier de stockage s'il n'existe pas"""
        if not os.path.exists(self.MESSAGES_FILE):
            with open(self.MESSAGES_FILE, 'w') as f:
                json.dump({}, f)

    def load_messages(self):
        """Charge tous les messages depuis le fichier"""
        try:
            with open(self.MESSAGES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_messages(self, messages):
        """Sauvegarde tous les messages dans le fichier"""
        with open(self.MESSAGES_FILE, 'w') as f:
            json.dump(messages, f, indent=4)

    def add_message(self, sender, receiver, message, is_group=False):
        """Ajoute un message à l'historique"""
        messages = self.load_messages()
        
        if is_group:
            key = f"group_{receiver}"
        else:
            key = f"{sorted([sender, receiver])[0]}_{sorted([sender, receiver])[1]}"
        
        if key not in messages:
            messages[key] = []
        
        messages[key].append({
            "sender": sender,
            "message": message,
            "timestamp": str(datetime.now())
        })
        
        self.save_messages(messages)

    def get_messages(self, user1, user2=None, group_name=None):
        """Récupère l'historique des messages"""
        messages = self.load_messages()
        
        if group_name:
            key = f"group_{group_name}"
        else:
            key = f"{sorted([user1, user2])[0]}_{sorted([user1, user2])[1]}"
        
        return messages.get(key, [])

    def clear_history(self, user1, user2=None, group_name=None):
        """Efface l'historique d'une conversation"""
        messages = self.load_messages()
        
        if group_name:
            key = f"group_{group_name}"
        else:
            key = f"{sorted([user1, user2])[0]}_{sorted([user1, user2])[1]}"
        
        if key in messages:
            del messages[key]
            self.save_messages(messages)
            return True
        return False