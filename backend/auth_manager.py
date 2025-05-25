import json
import os

# Fichier pour stocker les groupes
GROUPS_FILE = "groups.json"

# Base de données des utilisateurs
users = {
    "Hind": {
        "password": "123",
        "friends": ["Hadil", "Malak", "Haythem"]
    },
    "Hadil": {
        "password": "456",
        "friends": ["Hind", "Malak", "Haythem"]
    },
    "Malak": {
        "password": "789",
        "friends": ["Hind", "Hadil", "Haythem"]
    },
    "Haythem": {
        "password": "101",
        "friends": ["Hind", "Hadil", "Malak"]
    }
}

def load_groups():
    """Charge les groupes depuis le fichier"""
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_groups(groups):
    """Sauvegarde les groupes dans le fichier"""
    with open(GROUPS_FILE, 'w') as f:
        json.dump(groups, f, indent=4)

# Initialisation des groupes
groups = load_groups()

def authenticate(username, password):
    """Vérifie les identifiants de connexion"""
    user = users.get(username)
    return user and user["password"] == password

def get_friends(username):
    """Retourne la liste d'amis d'un utilisateur"""
    return users.get(username, {}).get("friends", [])

def get_user_groups(username):
    """Retourne la liste des groupes auxquels appartient l'utilisateur"""
    return [group_name for group_name, members in groups.items() if username in members]

def create_group(group_name, creator, members):
    """Crée un nouveau groupe avec les membres spécifiés"""
    global groups
    
    if group_name in groups:
        return False
    
    if creator not in members:
        members.append(creator)
    
    groups[group_name] = members
    save_groups(groups)
    return True