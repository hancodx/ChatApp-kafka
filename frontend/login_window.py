import tkinter as tk
from tkinter import ttk, messagebox
from backend.auth_manager import authenticate

class LoginWindow:
    def __init__(self, on_login_success):
        self.on_login_success = on_login_success
        self.setup_login_window()

    def setup_login_window(self):
        """Configure la fenêtre de connexion"""
        self.login_root = tk.Tk()
        self.login_root.title("Connexion au Chat")
        self.login_root.geometry("350x250")
        self.login_root.resizable(False, False)
        
        main_frame = ttk.Frame(self.login_root)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ttk.Label(main_frame, text="Chat Kafka", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        ttk.Label(main_frame, text="Nom d'utilisateur:").pack(anchor="w")
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.pack(fill="x", pady=5)
        
        ttk.Label(main_frame, text="Mot de passe:").pack(anchor="w")
        self.password_entry = ttk.Entry(main_frame, show="*")
        self.password_entry.pack(fill="x", pady=5)
        
        ttk.Button(main_frame, text="Se connecter", command=self.login).pack(pady=15)
        
        self.login_root.mainloop()

    def login(self):
        """Gère le processus de connexion"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if authenticate(username, password):
            self.login_root.destroy()
            self.on_login_success(username)
        else:
            messagebox.showerror("Erreur", "Identifiants incorrects")