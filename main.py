import tkinter as tk
import logging
from frontend.login_window import LoginWindow

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chat_app.log'),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    configure_logging()
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()