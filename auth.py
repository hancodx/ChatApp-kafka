users = {
    "Hind": {"password": "123", "friends": ["Hadil"]},
    "Hadil": {"password": "456", "friends": ["Hind"]}
}

def authenticate(username, password):
    user = users.get(username)
    return user and user["password"] == password

def get_friends(username):
    return users.get(username, {}).get("friends", [])