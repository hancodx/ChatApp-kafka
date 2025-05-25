import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from backend.auth_manager import get_friends, get_user_groups, create_group
from backend.kafka_manager import KafkaManager
import base64
from io import BytesIO
from PIL import Image, ImageTk

class ChatWindow:
    def __init__(self, username):
        self.username = username
        self.kafka_manager = KafkaManager(username)
        self.setup_chat_interface()

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
        
        ttk.Label(contacts_tab, text="Contacts", font=("Helvetica", 12, "bold")).pack(pady=10)
        
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
            relief="flat"
        )
        self.contacts_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        friends = get_friends(self.username)
        for i, friend in enumerate(friends):
            emojis = ["👤", "👩", "👨", "👧", "🧑"]
            emoji = emojis[i % len(emojis)]
            self.contacts_list.insert(tk.END, f"{emoji} {friend}")
            if i < len(friends) - 1:
                self.contacts_list.insert(tk.END, "─" * 20)
                self.contacts_list.itemconfig(tk.END, fg="gray")
        
        self.contacts_list.bind("<<ListboxSelect>>", lambda e: self.select_contact_or_group("contact"))
        
        groups_tab = ttk.Frame(self.contacts_notebook)
        self.contacts_notebook.add(groups_tab, text="Groupes")
        
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
            relief="flat"
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
            yscrollcommand=scrollbar.set,
            background="white"
        )
        self.message_display.pack(fill="both", expand=True)
        scrollbar.config(command=self.message_display.yview)
        
        self.message_display.tag_config("sent", foreground="blue", justify="right")
        self.message_display.tag_config("received", foreground="green", justify="left")
        self.message_display.tag_config("sent_group", foreground="#5555FF", justify="right")
        
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=10)
        
        self.image_button = ttk.Button(
            input_frame,
            text="📷",
            command=self.select_and_send_image,
            state="disabled"
        )
        self.image_button.pack(side="left", padx=5)
        
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
        """Met à jour la liste des groupes"""
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
        widget = self.contacts_list if type_ == "contact" else self.groups_list
        
        selection = widget.curselection()
        if selection:
            selected = widget.get(selection[0])
            if "─" not in selected:
                if type_ == "group":
                    selected = selected.replace("📢 ", "")
                elif type_ == "contact":
                    selected = selected.split(" ")[1]
                self.start_chat(selected, type_)

    def start_chat(self, target, type_):
        """Démarre une conversation"""
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
        self.image_button.config(state="normal")
        
        self.kafka_manager.start_consumer(
            target, 
            type_ == "group", 
            self.handle_incoming_message
        )

    def send_message(self):
        """Envoie un message texte"""
        message = self.message_input.get()
        if not message or not self.current_chat:
            return
        
        is_group = self.current_chat_type == "group"
        self.kafka_manager.send_message(self.current_chat, message, is_group)
        
        if is_group:
            self.display_message(f"Vous (groupe): {message}", "sent_group")
        else:
            self.display_message(f"Vous: {message}", "sent")
        
        self.message_input.delete(0, tk.END)

    def select_and_send_image(self):
        """Sélectionne et envoie une image"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner une image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if not file_path:
            return
        
        try:
            img = Image.open(file_path)
            img.thumbnail((400, 400))
            
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            is_group = self.current_chat_type == "group"
            self.kafka_manager.send_image(self.current_chat, img_str, is_group)
            self.display_image_message("Vous", img_str)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'envoyer l'image: {str(e)}")

    def handle_incoming_message(self, message):
        """Traite les messages entrants"""
        if message.startswith("IMAGE:"):
            _, sender, img_data = message.split(":", 2)
            if sender != self.username:
                self.display_image_message(sender, img_data)
        elif message.startswith("GROUP_IMAGE:"):
            _, group_info, img_data = message.split(":", 2)
            if not group_info.startswith(f"[{self.current_chat}] {self.username}"):
                sender = group_info.split(" ")[-1]
                self.display_image_message(f"{sender} (groupe)", img_data)
        elif not message.startswith(f"[{self.current_chat}] {self.username}:") and not message.startswith(f"{self.username}:"):
            self.display_message(message, "received")

    def display_image_message(self, sender, image_data):
        """Affiche une image dans le chat"""
        try:
            img_data = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_data))
            img.thumbnail((400, 400))
            
            photo = ImageTk.PhotoImage(img)
            
            self.message_display.config(state="normal")
            
            frame = tk.Frame(self.message_display, bd=0, relief="flat", bg="white")
            
            if sender != "Vous":
                label = tk.Label(
                    frame, 
                    text=sender,
                    font=("Helvetica", 9, "italic"),
                    bg="white",
                    fg="#666666"
                )
                label.pack(anchor="w", padx=5, pady=(5,0))
            
            label_img = tk.Label(
                frame, 
                image=photo, 
                bd=1,
                relief="solid",
                bg="white"
            )
            label_img.image = photo
            label_img.pack(padx=5, pady=5)
            
            self.message_display.window_create(tk.END, window=frame)
            self.message_display.insert(tk.END, "\n")
            
            self.message_display.config(state="disabled")
            self.message_display.see(tk.END)
            
        except Exception as e:
            self.display_message(f"{sender} a envoyé une image (erreur d'affichage)", "received")

    def display_message(self, message, msg_type):
        """Affiche un message texte dans le chat"""
        self.message_display.config(state="normal")
        
        if not self.message_display.get("end-2c", "end-1c") == "\n":
            self.message_display.insert(tk.END, "\n")
        
        self.message_display.insert(tk.END, message + "\n", msg_type)
        
        self.message_display.config(state="disabled")
        self.message_display.see(tk.END)

    def on_closing(self):
        """Nettoyage avant fermeture"""
        self.kafka_manager.stop_consumer()
        self.root.destroy()