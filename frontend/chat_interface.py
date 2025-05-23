import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from backend.kafka_manager import KafkaManager
from backend.message_storage import MessageStorage
from auth import get_friends, get_user_groups, create_group
import threading

class ChatInterface:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.message_storage = MessageStorage()
        self.kafka_manager = KafkaManager(username, self.display_received_message)
        self.current_chat = None
        self.current_chat_type = None
        
        self.setup_ui()
        self.setup_bindings()
        self.refresh_contacts()
        self.refresh_groups()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.root.title(f"Chat Kafka - {self.username}")
        self.root.geometry("1000x700")
        
        # Configuration du style
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TButton", padding=5)
        self.style.configure("TNotebook.Tab", padding=[10, 5])
        
        # Cadre principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Panneau des contacts (25% de la largeur)
        contacts_frame = ttk.Frame(main_frame, width=250)
        contacts_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # Onglets pour contacts et groupes
        self.contacts_notebook = ttk.Notebook(contacts_frame)
        self.contacts_notebook.pack(fill="both", expand=True)
        
        # Onglet Contacts
        contacts_tab = ttk.Frame(self.contacts_notebook)
        self.contacts_notebook.add(contacts_tab, text="Contacts")
        
        # Liste des contacts
        ttk.Label(contacts_tab, text="Contacts", font=("Helvetica", 12, "bold")).pack(pady=10)
        self.contacts_list = tk.Listbox(
            contacts_tab,
            selectmode=tk.SINGLE,
            font=("Helvetica", 11),
            borderwidth=0,
            highlightthickness=0
        )
        self.contacts_list.pack(fill="both", expand=True, pady=5)
        
        # Onglet Groupes
        groups_tab = ttk.Frame(self.contacts_notebook)
        self.contacts_notebook.add(groups_tab, text="Groupes")
        
        # Frame pour le bouton de création de groupe
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
            highlightthickness=0
        )
        self.groups_list.pack(fill="both", expand=True, pady=5)
        
        # Panneau de conversation
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(side="right", fill="both", expand=True)
        
        # En-tête de conversation
        self.chat_header = ttk.Label(
            chat_frame,
            text="Sélectionnez un contact ou un groupe",
            font=("Helvetica", 12, "bold")
        )
        self.chat_header.pack(pady=10)
        
        # Zone de messages avec scrollbar
        self.message_display = scrolledtext.ScrolledText(
            chat_frame,
            state="disabled",
            wrap=tk.WORD,
            font=("Helvetica", 11),
            padx=10,
            pady=10,
            width=60,
            height=20
        )
        self.message_display.pack(fill="both", expand=True)
        
        # Zone d'envoi
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=10)
        
        self.message_input = ttk.Entry(
            input_frame,
            state="disabled"
        )
        self.message_input.pack(side="left", fill="x", expand=True, padx=5)
        
        self.send_button = ttk.Button(
            input_frame,
            text="Envoyer",
            state="disabled",
            command=self.send_message
        )
        self.send_button.pack(side="right", padx=5)

    def setup_bindings(self):
        """Configure les liaisons d'événements"""
        self.contacts_list.bind("<<ListboxSelect>>", lambda e: self.select_contact_or_group("contact"))
        self.groups_list.bind("<<ListboxSelect>>", lambda e: self.select_contact_or_group("group"))
        self.message_input.bind("<Return>", lambda e: self.send_message())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def refresh_contacts(self):
        """Actualise la liste des contacts"""
        self.contacts_list.delete(0, tk.END)
        for friend in get_friends(self.username):
            self.contacts_list.insert(tk.END, friend)

    def refresh_groups(self):
        """Actualise la liste des groupes"""
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
        
        # Fenêtre pour sélectionner les membres
        member_selection = tk.Toplevel(self.root)
        member_selection.title(f"Ajouter des membres à {group_name}")
        member_selection.geometry("300x400")
        
        # Liste des amis disponibles
        friends = get_friends(self.username)
        selected_members = []
        
        # Liste avec cases à cocher
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
        
        # Bouton de confirmation
        def confirm_group():
            members = [friend for friend, var in selected_members if var.get() == 1]
            if create_group(group_name, self.username, members):
                self.refresh_groups()
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
            if type_ == "group":
                selected = selected.replace("📢 ", "")
            self.start_chat(selected, type_)

    def start_chat(self, target, type_):
        """Démarre une conversation avec un contact ou un groupe"""
        self.current_chat = target
        self.current_chat_type = type_
        
        if type_ == "contact":
            self.chat_header.config(text=f"Conversation avec {target}")
            messages = self.message_storage.get_messages(self.username, target)
        else:
            self.chat_header.config(text=f"Groupe: {target}")
            messages = self.message_storage.get_messages(self.username, group_name=target)
        
        self.message_display.config(state="normal")
        self.message_display.delete("1.0", tk.END)
        
        for msg in messages:
            if msg["sender"] == self.username:
                prefix = "Vous: " if type_ == "contact" else "Vous (groupe): "
                self.display_message(f"{prefix}{msg['message']}", "sent")
            else:
                if type_ == "contact":
                    self.display_message(f"{msg['sender']}: {msg['message']}", "received")
                else:
                    self.display_message(f"[{target}] {msg['sender']}: {msg['message']}", "received")
        
        self.message_input.config(state="normal")
        self.send_button.config(state="normal")
        self.kafka_manager.start_consumer(target, type_ == "group")

    def send_message(self):
        """Envoie un message"""
        message = self.message_input.get().strip()
        if not message or not self.current_chat:
            return
        
        try:
            if self.current_chat_type == "contact":
                self.kafka_manager.send_message(self.current_chat, message)
                self.message_storage.add_message(self.username, self.current_chat, message)
                self.display_message(f"Vous: {message}", "sent")
            else:
                self.kafka_manager.send_message(self.current_chat, message, is_group=True)
                self.message_storage.add_message(self.username, self.current_chat, message, is_group=True)
                self.display_message(f"Vous (groupe): {message}", "sent")
            
            self.message_input.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'envoi du message: {str(e)}")

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

    def display_received_message(self, message):
        """Affiche un message reçu"""
        self.message_display.config(state="normal")
        self.message_display.insert(tk.END, message + "\n", "received")
        self.message_display.config(state="disabled")
        self.message_display.see(tk.END)
        
        # Stocker le message si nécessaire
        if self.current_chat:
            if self.current_chat_type == "contact":
                sender = message.split(":")[0]
                msg_content = ":".join(message.split(":")[1:]).strip()
                self.message_storage.add_message(sender, self.username, msg_content)
            else:
                parts = message.split("] ")
                sender = parts[1].split(":")[0]
                msg_content = ":".join(parts[1].split(":")[1:]).strip()
                group_name = parts[0][1:]
                self.message_storage.add_message(sender, group_name, msg_content, is_group=True)

    def on_closing(self):
        """Nettoyage avant fermeture"""
        self.kafka_manager.stop()
        self.root.destroy()