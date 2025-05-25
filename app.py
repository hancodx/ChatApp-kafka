import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from confluent_kafka import Producer, Consumer, KafkaException
from auth import authenticate, get_friends, get_user_groups, create_group
from config import KAFKA_BROKER, BASE_TOPIC

class ChatApplication:
    def __init__(self):
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
        
        ttk.Button(
            main_frame, 
            text="Se connecter", 
            command=self.login
        ).pack(pady=15)
        
        self.login_root.mainloop()

    def login(self):
        """Gère le processus de connexion"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if authenticate(username, password):
            self.login_root.destroy()
            self.username = username
            self.setup_chat_interface()
        else:
            messagebox.showerror("Erreur", "Identifiants incorrects")

    def setup_chat_interface(self):
        """Configure l'interface de chat principale"""
        self.root = tk.Tk()
        self.root.title(f"Chat Kafka - {self.username}")
        self.root.geometry("1000x700")
        
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TButton", padding=5)
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        contacts_frame = ttk.Frame(main_frame, width=250)
        contacts_frame.pack(side="left", fill="y", padx=(0, 10))
        
        self.contacts_notebook = ttk.Notebook(contacts_frame)
        self.contacts_notebook.pack(fill="both", expand=True)
        
        contacts_tab = ttk.Frame(self.contacts_notebook)
        self.contacts_notebook.add(contacts_tab, text="Contacts")
        
        groups_tab = ttk.Frame(self.contacts_notebook)
        self.contacts_notebook.add(groups_tab, text="Groupes")
        
        ttk.Label(contacts_tab, text="Contacts", font=("Helvetica", 12, "bold")).pack(pady=10)
        
        # Frame intermédiaire pour la liste des contacts
        contacts_list_frame = ttk.Frame(contacts_tab)
        contacts_list_frame.pack(fill="both", expand=True, pady=5)
        
        self.contacts_list = tk.Listbox(
            contacts_list_frame,
            selectmode=tk.SINGLE,
            font=("Helvetica", 11),
            borderwidth=0,
            highlightthickness=0,
            background="#f5f5f5",
            selectbackground="#e1e1e1",
            selectforeground="black",
            relief="flat",
            highlightcolor="#d9d9d9"
        )
        self.contacts_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Ajout des contacts avec emojis et séparateurs
        friends = get_friends(self.username)
        for i, friend in enumerate(friends):
            emojis = ["👤", "👩", "👨", "👧", "🧑"]  # Liste d'emojis
            emoji = emojis[i % len(emojis)]  # Sélection cyclique
            self.contacts_list.insert(tk.END, f"{emoji} {friend}")
            
            # Ajouter un séparateur après chaque contact sauf le dernier
            if i < len(friends) - 1:
                self.contacts_list.insert(tk.END, "─" * 20)  # Ligne de séparation
                self.contacts_list.itemconfig(tk.END, fg="gray")  # Couleur grise pour le séparateur
        
        self.contacts_list.bind("<<ListboxSelect>>", lambda e: self.select_contact_or_group("contact"))
        
        ttk.Label(groups_tab, text="Groupes", font=("Helvetica", 12, "bold")).pack(pady=10)
        
        group_buttons_frame = ttk.Frame(groups_tab)
        group_buttons_frame.pack(fill="x", pady=5)
        
        ttk.Button(
            group_buttons_frame,
            text="Créer un groupe",
            command=self.create_new_group
        ).pack(side="left", padx=5)
        
        self.groups_list = tk.Listbox(
            groups_tab,
            selectmode=tk.SINGLE,
            font=("Helvetica", 11),
            borderwidth=0,
            highlightthickness=0,
            background="#f5f5f5",
            selectbackground="#e1e1e1",
            selectforeground="black",
            relief="flat",
            highlightcolor="#d9d9d9"
        )
        self.groups_list.pack(fill="both", expand=True, pady=5)
        
        self.refresh_groups_list()
        self.groups_list.bind("<<ListboxSelect>>", lambda e: self.select_contact_or_group("group"))
        
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(side="right", fill="both", expand=True)
        
        self.chat_header = ttk.Label(
            chat_frame,
            text="Sélectionnez un contact ou un groupe",
            font=("Helvetica", 12, "bold")
        )
        self.chat_header.pack(pady=10)
        
        message_frame = ttk.Frame(chat_frame)
        message_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(message_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.message_display = tk.Text(
            message_frame,
            state="disabled",
            wrap=tk.WORD,
            font=("Helvetica", 11),
            padx=10,
            pady=10,
            yscrollcommand=scrollbar.set
        )
        self.message_display.pack(fill="both", expand=True)
        scrollbar.config(command=self.message_display.yview)
        
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=10)
        
        self.message_input = ttk.Entry(
            input_frame,
            state="disabled"
        )
        self.message_input.pack(side="left", fill="x", expand=True, padx=5)
        self.message_input.bind("<Return>", lambda e: self.send_message())
        
        self.send_button = ttk.Button(
            input_frame,
            text="Envoyer",
            state="disabled",
            command=self.send_message
        )
        self.send_button.pack(side="right", padx=5)
        
        self.current_chat = None
        self.current_chat_type = None
        self.running = True
        self.consumer_thread = None
        
        self.periodic_refresh()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def periodic_refresh(self):
        """Actualise périodiquement la liste des groupes"""
        if hasattr(self, 'groups_list'):
            current_selection = self.groups_list.curselection()
            self.refresh_groups_list()
            if current_selection:
                self.groups_list.selection_set(current_selection)
        
        self.root.after(5000, self.periodic_refresh)

    def refresh_groups_list(self):
        """Met à jour la liste des groupes dans l'interface"""
        self.groups_list.delete(0, tk.END)
        for group in get_user_groups(self.username):
            self.groups_list.insert(tk.END, f"📢 {group}")

    def create_new_group(self):
        """Crée un nouveau groupe"""
        group_name = simpledialog.askstring(
            "Créer un groupe",
            "Nom du groupe:",
            parent=self.root
        )
        
        if not group_name:
            return
        
        member_selection = tk.Toplevel(self.root)
        member_selection.title(f"Ajouter des membres à {group_name}")
        member_selection.geometry("300x400")
        
        friends = get_friends(self.username)
        selected_members = []
        
        for friend in friends:
            var = tk.IntVar()
            chk = tk.Checkbutton(
                member_selection,
                text=friend,
                variable=var,
                onvalue=1,
                offvalue=0
            )
            chk.pack(anchor="w", padx=20, pady=2)
            selected_members.append((friend, var))
        
        def confirm_group():
            members = [friend for friend, var in selected_members if var.get() == 1]
            if create_group(group_name, self.username, members):
                self.refresh_groups_list()
                member_selection.destroy()
                messagebox.showinfo("Succès", f"Groupe {group_name} créé avec succès!")
            else:
                messagebox.showerror("Erreur", "Ce nom de groupe existe déjà")
        
        ttk.Button(
            member_selection,
            text="Créer le groupe",
            command=confirm_group
        ).pack(pady=10)
    
    def select_contact_or_group(self, type_):
        """Gère la sélection d'un contact ou d'un groupe"""
        if type_ == "contact":
            widget = self.contacts_list
        else:
            widget = self.groups_list
        
        selection = widget.curselection()
        if selection:
            selected = widget.get(selection[0])
            # Ignorer les séparateurs
            if "─" not in selected:
                if type_ == "group":
                    selected = selected.replace("📢 ", "")
                elif type_ == "contact":
                    selected = selected.split(" ")[1]  # Enlever l'emoji
                self.start_chat(selected, type_)

    def start_chat(self, target, type_):
        """Démarre une conversation sans historique"""
        self.current_chat = target
        self.current_chat_type = type_
        
        if type_ == "contact":
            self.chat_header.config(text=f"Conversation avec {target}")
        else:
            self.chat_header.config(text=f"Groupe: {target}")
        
        self.message_display.config(state="normal")
        self.message_display.delete("1.0", tk.END)
        self.message_display.config(state="disabled")
        
        self.message_input.config(state="normal")
        self.send_button.config(state="normal")
        
        if self.consumer_thread:
            self.running = False
            self.consumer_thread.join()
        
        self.running = True
        self.consumer_thread = threading.Thread(
            target=self.receive_messages,
            args=(target, type_),
            daemon=True
        )
        self.consumer_thread.start()

    def send_message(self):
        """Envoie un message sans sauvegarde"""
        message = self.message_input.get()
        if not message or not self.current_chat:
            return
        
        producer = Producer({"bootstrap.servers": KAFKA_BROKER})
        
        if self.current_chat_type == "contact":
            topic = f"{BASE_TOPIC}-{self.username}-{self.current_chat}"
            full_message = f"{self.username}: {message}"
            producer.produce(topic, full_message.encode("utf-8"))
            self.display_message(f"Vous: {message}", "sent")
        else:
            topic = f"{BASE_TOPIC}-group-{self.current_chat}"
            full_message = f"[{self.current_chat}] {self.username}: {message}"
            producer.produce(topic, full_message.encode("utf-8"))
            self.display_message(f"Vous (groupe): {message}", "sent")
        
        producer.flush()
        self.message_input.delete(0, tk.END)

    def receive_messages(self, target, type_):
        """Reçoit les messages du contact ou du groupe"""
        if type_ == "contact":
            topic = f"{BASE_TOPIC}-{target}-{self.username}"
        else:
            topic = f"{BASE_TOPIC}-group-{target}"
        
        consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": f"{self.username}-group",
            "auto.offset.reset": "latest"
        })
        consumer.subscribe([topic])
        
        while self.running:
            msg = consumer.poll(1.0)
            
            if msg and not msg.error():
                message = msg.value().decode("utf-8")
                if not message.startswith(f"[{target}] {self.username}:") and not message.startswith(f"{self.username}:"):
                    self.display_message(message, "received")
        
        consumer.close()

    def display_message(self, message, msg_type):
        """Affiche un message dans la conversation"""
        self.message_display.config(state="normal")
        
        if msg_type == "sent":
            tag = "sent_group" if self.current_chat_type == "group" else "sent"
            self.message_display.insert(tk.END, message + "\n", tag)
            self.message_display.tag_config(tag, foreground="blue", justify="right")
        else:
            self.message_display.insert(tk.END, message + "\n", "received")
            self.message_display.tag_config("received", foreground="green", justify="left")
        
        self.message_display.config(state="disabled")
        self.message_display.see(tk.END)

    def on_closing(self):
        """Nettoyage avant fermeture"""
        self.running = False
        if self.consumer_thread:
            self.consumer_thread.join()
        self.root.destroy()

if __name__ == "__main__":
    app = ChatApplication()