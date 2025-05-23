import tkinter as tk
from tkinter import ttk, messagebox
from auth import authenticate
from frontend.chat_interface import ChatInterface

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.setup_login_window()

    def setup_login_window(self):
        """Configure la fenêtre de connexion"""
        self.root.title("Connexion au Chat")
        self.root.geometry("350x250")
        self.root.resizable(False, False)
        
        # Style
        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ttk.Label(main_frame, text="Chat Kafka", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        # Champs de connexion
        ttk.Label(main_frame, text="Nom d'utilisateur:").pack(anchor="w")
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.pack(fill="x", pady=5)
        
        ttk.Label(main_frame, text="Mot de passe:").pack(anchor="w")
        self.password_entry = ttk.Entry(main_frame, show="*")
        self.password_entry.pack(fill="x", pady=5)
        
        ttk.Button(
            main_frame, 
            text="Se connecter", 
            command=self.login
        ).pack(pady=15)
        
        # Liaison de la touche Entrée
        self.password_entry.bind("<Return>", lambda event: self.login())

    def login(self):
        """Gère le processus de connexion"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez saisir un nom d'utilisateur et un mot de passe")
            return
        
        try:
            if authenticate(username, password):
                self.root.destroy()
                chat_root = tk.Tk()
                app = ChatInterface(chat_root, username)
                chat_root.mainloop()
            else:
                messagebox.showerror("Erreur", "Identifiants incorrects")
                self.password_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la connexion: {str(e)}")