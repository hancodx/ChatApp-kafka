import threading
import tkinter as tk
from tkinter import ttk, messagebox, font
from confluent_kafka import Producer, Consumer, KafkaException
from auth import authenticate, get_friends
from config import KAFKA_BROKER, BASE_TOPIC

class ChatApp:
    def __init__(self):
        self.setup_login_window()

    def setup_login_window(self):
        self.login_root = tk.Tk()
        self.login_root.title("Connexion")
        self.login_root.geometry("350x250")
        
        # Style
        self.login_root.configure(bg="#f5f5f5")
        title_font = font.Font(size=12, weight="bold")
        
        ttk.Label(self.login_root, text="Chat Kafka", font=title_font, background="#f5f5f5").pack(pady=15)
        
        frame = ttk.Frame(self.login_root)
        frame.pack(pady=20, padx=20)
        
        ttk.Label(frame, text="Utilisateur:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Mot de passe:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(frame, show="*", width=25)
        self.password_entry.grid(row=1, column=1, pady=5)
        
        ttk.Button(self.login_root, text="Se connecter", command=self.login).pack(pady=15)
        
        self.login_root.mainloop()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if authenticate(username, password):
            self.login_root.destroy()
            self.setup_chat_window(username)
        else:
            messagebox.showerror("Erreur", "Identifiants incorrects")

    def setup_chat_window(self, username):
        self.username = username
        self.friends = get_friends(username)
        self.current_chat = None
        self.running = True
        
        # Fenêtre principale
        self.root = tk.Tk()
        self.root.title(f"Chat Kafka - {self.username}")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f2f5")
        
        # Police
        self.font = font.Font(family="Helvetica", size=10)
        self.bold_font = font.Font(family="Helvetica", size=10, weight="bold")
        
        # Cadre des contacts
        contacts_frame = tk.Frame(self.root, bg="#e1e4e8", width=200)
        contacts_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        tk.Label(contacts_frame, text="Contacts", bg="#e1e4e8", font=self.bold_font).pack(pady=10)
        
        # Liste des amis
        self.friends_buttons = []
        for friend in self.friends:
            btn = tk.Button(
                contacts_frame,
                text=friend,
                bg="#e1e4e8",
                fg="black",
                bd=0,
                padx=20,
                pady=10,
                font=self.font,
                command=lambda f=friend: self.start_chat(f),
                anchor="w"
            )
            btn.pack(fill="x")
            self.friends_buttons.append(btn)
        
        # Cadre de chat
        chat_frame = tk.Frame(self.root, bg="white")
        chat_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Zone de messages
        self.chat_display = tk.Text(
            chat_frame,
            bg="white",
            fg="black",
            font=self.font,
            wrap=tk.WORD,
            state="disabled",
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill="both", expand=True)
        
        # Zone d'envoi
        input_frame = tk.Frame(chat_frame, bg="white")
        input_frame.pack(fill="x", pady=10)
        
        self.message_entry = tk.Entry(
            input_frame,
            bg="#f0f2f5",
            fg="black",
            font=self.font,
            relief=tk.FLAT
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        send_button = tk.Button(
            input_frame,
            text="Envoyer",
            bg="#0084ff",
            fg="white",
            font=self.bold_font,
            relief=tk.FLAT,
            command=self.send_message
        )
        send_button.pack(side="right", padx=5)
        
        # Désactiver initialement
        self.message_entry.config(state="disabled")
        send_button.config(state="disabled")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def start_chat(self, friend):
        self.current_chat = friend
        self.message_entry.config(state="normal")
        
        # Mettre à jour l'interface
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.insert(tk.END, f"Conversation avec {friend}\n\n", "info")
        self.chat_display.tag_config("info", foreground="gray")
        self.chat_display.config(state="disabled")
        
        # Démarrer le consommateur Kafka
        if hasattr(self, 'consumer_thread'):
            self.running = False
            self.consumer_thread.join()
        
        self.running = True
        self.consumer_thread = threading.Thread(
            target=self.receive_messages,
            args=(friend,)
        )
        self.consumer_thread.daemon = True
        self.consumer_thread.start()

    def send_message(self):
        if not self.current_chat or not self.message_entry.get():
            return
        
        message = self.message_entry.get()
        topic = f"{BASE_TOPIC}-{self.username}-{self.current_chat}"
        
        producer = Producer({"bootstrap.servers": KAFKA_BROKER})
        producer.produce(topic, f"{self.username}: {message}".encode("utf-8"))
        producer.flush()
        
        self.display_message(f"Vous: {message}", "sent")
        self.message_entry.delete(0, tk.END)

    def receive_messages(self, friend):
        topic = f"{BASE_TOPIC}-{friend}-{self.username}"
        
        consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": f"{self.username}-group",
            "auto.offset.reset": "earliest"
        })
        consumer.subscribe([topic])
        
        while self.running:
            msg = consumer.poll(1.0)
            
            if msg and not msg.error():
                message = msg.value().decode("utf-8")
                self.display_message(message, "received")
        
        consumer.close()

    def display_message(self, message, msg_type):
        self.chat_display.config(state="normal")
        
        if msg_type == "sent":
            self.chat_display.insert(tk.END, message + "\n\n", "sent")
            self.chat_display.tag_config("sent", foreground="#0084ff", justify="right")
        else:
            self.chat_display.insert(tk.END, message + "\n\n", "received")
            self.chat_display.tag_config("received", foreground="black", justify="left")
        
        self.chat_display.config(state="disabled")
        self.chat_display.see(tk.END)

    def on_closing(self):
        self.running = False
        if hasattr(self, 'consumer_thread'):
            self.consumer_thread.join()
        self.root.destroy()

if __name__ == "__main__":
    app = ChatApp()