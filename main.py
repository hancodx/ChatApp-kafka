from frontend.login_window import LoginWindow
from frontend.chat_window import ChatWindow

def start_chat(username):
    ChatWindow(username)

if __name__ == "__main__":
    LoginWindow(start_chat)