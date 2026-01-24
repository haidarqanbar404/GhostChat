import customtkinter as ctk
import threading
import asyncio
import os
from datetime import datetime
from PIL import Image, ImageTk
import random
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import json
import webbrowser

from network.telegram_client import GhostNetwork
from database.models import init_db, SessionLocal, Contact, DecryptedMessage
from core.crypto import CryptoEngine

import ctypes
import sys
import subprocess

myappid = 'mycompany.ghostchat.gui.1.0' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

COLOR_BG = "#0b0b0f"       
COLOR_SIDEBAR = "#121216"   
COLOR_ACCENT = "#00dc82"  
COLOR_TEXT_MAIN = "#ffffff" 
COLOR_TEXT_DIM = "#8a8a93"  
COLOR_INPUT_BG = "#1e1e24"  
COLOR_BTN_HOVER = "#2a2a35" 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "user_config.json")

CONFIG_PATH = get_config_path()

class GhostChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GhostChat - Stealth Messenger")
        self.geometry("1100x700")
        self.configure(fg_color=COLOR_BG)

        try:
            icon_path = resource_path(os.path.join("assets", "app_icon.ico"))
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except: pass
            
        self.assets = {}
        self.load_assets()
        

        self.user_config = self.load_or_ask_credentials()

        self.telegram_loop = None
        init_db()
        self.current_chat_contact = None 
        self.active_view = "dashboard" 
        threading.Thread(target=self.check_and_pull_model, daemon=True).start()
        # self.check_and_pull_model() 

        self.ghost = GhostNetwork(
            on_message_received=self.on_incoming_message, 
            config=self.user_config,
            gui_instance=self 
        )

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        self.load_contacts()
        self.enable_global_copy_paste()

        self.launch_telegram_thread()

    def launch_telegram_thread(self):
        self.network_thread = threading.Thread(target=self.start_telegram_client, daemon=True)
        self.network_thread.start()


        
        try:
            self.telegram_loop.run_until_complete(self.ghost.start())
        except Exception as e:
            print(f"Telegram Client Error: {e}")

    def load_or_ask_credentials(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    return json.load(f)
            except:
                pass 
        
        return self.show_setup_wizard()

    def show_setup_wizard(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("First Run Setup")
        dialog.geometry("400x500")
        dialog.attributes("-topmost", True)
        
        self.setup_finished = False 

        def on_close():
            dialog.destroy()
            
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        
        ctk.CTkLabel(dialog, text="Welcome to GhostChat!", font=("Arial", 20, "bold")).pack(pady=(30, 10))
        
        ctk.CTkButton(dialog, text="Get them from: my.telegram.org", 
                      command=lambda: webbrowser.open("https://my.telegram.org"),
                      fg_color="transparent", text_color="#3B8ED0").pack(pady=5)

        ctk.CTkLabel(dialog, text="API ID:").pack(anchor="w", padx=30)
        entry_api_id = ctk.CTkEntry(dialog); entry_api_id.pack(fill="x", padx=30, pady=5)
        self.fix_input_field(entry_api_id, dialog)

        ctk.CTkLabel(dialog, text="API HASH:").pack(anchor="w", padx=30)
        entry_api_hash = ctk.CTkEntry(dialog); entry_api_hash.pack(fill="x", padx=30, pady=5)
        self.fix_input_field(entry_api_hash, dialog)

        ctk.CTkLabel(dialog, text="Phone (+963...):").pack(anchor="w", padx=30)
        entry_phone = ctk.CTkEntry(dialog); entry_phone.pack(fill="x", padx=30, pady=5)
        self.fix_input_field(entry_phone, dialog)

        self.setup_result = {}

        def save():
            api_id = entry_api_id.get().strip()
            api_hash = entry_api_hash.get().strip()
            phone = entry_phone.get().strip()

            if not api_id or not api_hash or not phone:
                messagebox.showerror("Error", "Required!", parent=dialog)
                return
            
            self.setup_result = {"api_id": api_id, "api_hash": api_hash, "phone": phone}
            
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.setup_result, f)
            
            self.setup_finished = True 
            dialog.destroy()

        ctk.CTkButton(dialog, text="Save & Start", command=save, fg_color="#00dc82").pack(pady=30)
        
        self.wait_window(dialog)
        
        if not self.setup_finished and not self.setup_result:
            sys.exit(0)
            
        return self.setup_result
        
        icon_path = resource_path(os.path.join("assets", "app_icon.ico"))
        if os.path.exists(icon_path):
            dialog.after(200, lambda: dialog.iconbitmap(icon_path))

        ctk.CTkLabel(dialog, text="Welcome to GhostChat!", font=("Arial", 20, "bold")).pack(pady=(30, 10))
        ctk.CTkLabel(dialog, text="Please enter your Telegram API details.", text_color="gray").pack()
        
        link_btn = ctk.CTkButton(dialog, text="Get them from: my.telegram.org", 
                                 command=lambda: webbrowser.open("https://my.telegram.org"),
                                 fg_color="transparent", text_color="#3B8ED0", hover_color="#1e1e24")
        link_btn.pack(pady=5)

        ctk.CTkLabel(dialog, text="API ID:").pack(anchor="w", padx=30, pady=(10, 0))
        entry_api_id = ctk.CTkEntry(dialog, placeholder_text="e.g. 123456")
        entry_api_id.pack(fill="x", padx=30, pady=5)
        self.fix_input_field(entry_api_id, root_window=dialog) 

        ctk.CTkLabel(dialog, text="API HASH:").pack(anchor="w", padx=30)
        entry_api_hash = ctk.CTkEntry(dialog, placeholder_text="e.g. a1b2c3d4...")
        entry_api_hash.pack(fill="x", padx=30, pady=5)
        self.fix_input_field(entry_api_hash, root_window=dialog) 

        ctk.CTkLabel(dialog, text="Phone Number:").pack(anchor="w", padx=30)
        entry_phone = ctk.CTkEntry(dialog, placeholder_text="+9639...")
        entry_phone.pack(fill="x", padx=30, pady=5)
        self.fix_input_field(entry_phone, root_window=dialog) 

        self.setup_result = {}

        def save_and_close():
            api_id = entry_api_id.get().strip()
            api_hash = entry_api_hash.get().strip()
            phone = entry_phone.get().strip()

            if not api_id or not api_hash or not phone:
                messagebox.showerror("Error", "All fields are required!", parent=dialog)
                return
            
            self.setup_result["api_id"] = api_id
            self.setup_result["api_hash"] = api_hash
            self.setup_result["phone"] = phone
            
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.setup_result, f)
            
            dialog.destroy()

        ctk.CTkButton(dialog, text="Save & Start", command=save_and_close, fg_color="#00dc82").pack(pady=30)
        
        self.wait_window(dialog)
        
        if not self.setup_result:
            sys.exit(0)
            
        return self.setup_result
    def setup_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: widget.event_generate("<<SelectAll>>"))

        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)

        widget.bind("<Button-3>", show_menu)
        
        widget.bind("<Control-a>", lambda e: widget.event_generate("<<SelectAll>>"))

    def load_assets(self):
        assets_dir = resource_path("assets")
        
        files = {
            "logo": ("logo.png", (35, 35)),
            "chat": ("icon_chat.png", (20, 20)),
            "profile": ("icon_profile.png", (20, 20)),
            "settings": ("icon_settings.png", (20, 20)),
            "logout": ("icon_logout.png", (20, 20)),
            "send": ("icon_send.png", (20, 20)),
            "attach": ("icon_attach.png", (24, 24)),
            "mic": ("icon_mic.png", (24, 24)),
            "contact": ("icon_contact.png", (20, 20)),
            "plus": ("icon_plus.png", (16, 16)),
            "clear": ("icon_clear.png", (20, 20)), 
            "cut": ("icon_cut.png", (20, 20)),
            "copy": ("icon_copy.png", (20, 20)),
            "paste": ("icon_paste.png", (20, 20)),
            "select_all": ("icon_select_all.png", (20, 20)),
            "dashboard": ("icon_dashboard.png", (20,20)),
            "ai": ("icon_ai.png", (20,20)),
            
        }

        for key, (filename, size) in files.items():
            path = os.path.join(assets_dir, filename)
            if os.path.exists(path):
                try:
                    self.assets[key] = ctk.CTkImage(
                        light_image=Image.open(path),
                        dark_image=Image.open(path),
                        size=size
                    )
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    self.assets[key] = None
            else:
                self.assets[key] = None

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="w")
        
        if self.assets.get("logo"):
            logo_lbl = ctk.CTkLabel(self.logo_frame, text="", image=self.assets["logo"])
            logo_lbl.pack(side="left")
        else:
            logo_lbl = ctk.CTkLabel(self.logo_frame, text="👻", font=("Arial", 24))
            logo_lbl.pack(side="left")
            
        logo_text = ctk.CTkLabel(self.logo_frame, text="GhostChat", font=("Segoe UI", 18, "bold"), text_color="white")
        logo_text.pack(side="left", padx=10)

        ctk.CTkButton(
            self.sidebar, 
            text="Dashboard", 
            image=self.assets.get("dashboard"),
            compound="left",
            fg_color="transparent", 
            text_color="#8a8a93",
            hover_color=COLOR_BTN_HOVER,
            height=40, anchor="w", font=("Segoe UI", 14),
            command=self.show_dashboard
        ).grid(row=1, column=0, padx=15, pady=2, sticky="ew")
        
        ctk.CTkButton(
            self.sidebar, 
            text="AI Lab",
            image=self.assets.get("ai"),
            compound="left", 
            fg_color="transparent", 
            text_color="#8a8a93",
            hover_color=COLOR_BTN_HOVER,
            height=40, anchor="w", font=("Segoe UI", 14),
            command=self.show_ai_playground
        ).grid(row=2, column=0, padx=15, pady=2, sticky="ew")
        
        self.btn_profile = ctk.CTkButton(
            self.sidebar, 
            text="  Profile", 
            image=self.assets.get("profile"),
            compound="left", 
            anchor="w", 
            fg_color="transparent", 
            text_color="#8a8a93",
            hover_color=COLOR_BTN_HOVER,
            font=("Segoe UI", 14), height=40, corner_radius=8,
            command=self.open_profile_window  
        )
        self.btn_profile.grid(row=3, column=0, padx=15, pady=2, sticky="ew")

        self.btn_settings = ctk.CTkButton(
            self.sidebar, 
            text="  Settings", 
            image=self.assets.get("settings"),
            compound="left",
            anchor="w", 
            fg_color="transparent", 
            text_color="#8a8a93",
            hover_color=COLOR_BTN_HOVER,
            font=("Segoe UI", 14), height=40, corner_radius=8,
            command=self.open_settings_window 
        )
        self.btn_settings.grid(row=4, column=0, padx=15, pady=2, sticky="ew")

        contact_lbl = ctk.CTkLabel(self.sidebar, text="CONTACTS", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT_DIM, anchor="w")
        contact_lbl.grid(row=8, column=0, padx=25, pady=(20, 10), sticky="w")
        
        self.contacts_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.contacts_frame.grid(row=9, column=0, sticky="nsew", padx=10)

        img_plus = self.assets.get("plus")
        if img_plus:
            add_btn = ctk.CTkButton(self.sidebar, text="New Contact", image=img_plus, compound="left", 
                                    fg_color=COLOR_BTN_HOVER, command=self.add_contact_dialog, height=35, anchor="center")
        else:
            add_btn = ctk.CTkButton(self.sidebar, text="+ New Contact", fg_color=COLOR_BTN_HOVER, command=self.add_contact_dialog)
            
        add_btn.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        self.btn_logout = ctk.CTkButton(
            self.sidebar, 
            text="  Log out", 
            image=self.assets.get("logout"), 
            compound="left",
            anchor="w", 
            fg_color="transparent",           
            hover_color="#2C1717",       
            text_color="#ff6b6b",
            font=("Segoe UI", 14), height=40, corner_radius=8,
            command=self.logout_app   
        )
        self.btn_logout.grid(row=11, column=0, padx=15, pady=20, sticky="ew")

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1); self.main_frame.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(self.main_frame, height=60, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        self.header_title = ctk.CTkLabel(self.header_frame, text="Dashboard", font=("Segoe UI", 20, "bold"), text_color="white")
        self.header_title.pack(side="left")
        
        self.clear_btn = ctk.CTkButton(self.header_frame, text="Clear", width=60, fg_color="transparent", border_width=1, hover_color="#C62828", command=self.clear_chat_display)
        
        self.chat_display_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.chat_display_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        
        self.create_input_bar()
        
        self.show_dashboard()

    def show_hero_section(self):
        for w in self.chat_display_frame.winfo_children(): w.destroy()
        self.chat_display_frame.grid_rowconfigure(0, weight=1)
        self.chat_display_frame.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(self.chat_display_frame, fg_color="transparent")
        hero.grid(row=0, column=0)

        ctk.CTkLabel(hero, text="📺", font=("Arial", 80)).pack(pady=(0, 20))
        ctk.CTkLabel(hero, text="Your Stealth AI Buddy", font=("Segoe UI", 32, "bold"), text_color="white").pack(pady=5)
        ctk.CTkLabel(hero, text="Steganography • Encryption • Privacy", font=("Segoe UI", 16), text_color=COLOR_TEXT_DIM).pack(pady=(0, 30))

    def create_input_bar(self):
        self.input_container = ctk.CTkFrame(self.main_frame, height=80, fg_color="transparent")
        # container = ctk.CTkFrame(self.main_frame, height=80, fg_color="transparent")
        # container.grid(row=2, column=0, sticky="ew", padx=30, pady=20)
        
        self.input_bg = ctk.CTkFrame(self.input_container, height=55, corner_radius=25, fg_color=COLOR_INPUT_BG)
        self.input_bg.pack(fill="x", side="bottom")

        img_attach = self.assets["attach"]
        t_attach = "" if img_attach else "📎"
        ctk.CTkButton(self.input_bg, text=t_attach, image=img_attach, width=40, fg_color="transparent", hover_color=COLOR_BTN_HOVER).pack(side="left", padx=(10,0))

        img_mic = self.assets["mic"]
        t_mic = "" if img_mic else "🎙️"
        ctk.CTkButton(self.input_bg, text=t_mic, image=img_mic, width=40, fg_color="transparent", hover_color=COLOR_BTN_HOVER).pack(side="left")

        self.msg_entry = ctk.CTkEntry(self.input_bg, placeholder_text="Type a hidden message...", border_width=0, 
                                      fg_color="transparent", text_color="white", font=("Segoe UI", 14), height=40)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.msg_entry.bind("<Return>", self.handle_send_action)

        self.fix_input_field(self.msg_entry)

        img_send = self.assets["send"]
        t_send = "" if img_send else "➤"
        self.send_btn = ctk.CTkButton(self.input_bg, text=t_send, image=img_send, width=45, height=35, corner_radius=18,
                                      fg_color=COLOR_ACCENT, hover_color="#00b368", text_color="black", command=self.send_message)
        self.send_btn.pack(side="right", padx=10, pady=10)

    def show_dashboard(self):
        self.active_view = "dashboard"
        self.current_chat_contact = None
        self.header_title.configure(text="System Status")
        
        if hasattr(self, 'clear_btn'): self.clear_btn.pack_forget()
        
        if hasattr(self, 'input_container'): 
            self.input_container.grid_forget()

        for w in self.chat_display_frame.winfo_children(): w.destroy()
        
        self.chat_display_frame.grid_rowconfigure(0, weight=1)
        self.chat_display_frame.grid_columnconfigure(0, weight=1)

        try:
            db = SessionLocal()
            contacts_count = db.query(Contact).count()
            messages_count = db.query(DecryptedMessage).count()
            db.close()
        except:
            contacts_count = 0
            messages_count = 0

        dash = ctk.CTkFrame(self.chat_display_frame, fg_color="transparent")
        dash.grid(row=0, column=0, sticky="nsew")
        
        center_box = ctk.CTkFrame(dash, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.45, anchor="center")

        if "logo" in self.assets and self.assets["logo"]:
            logo_label = ctk.CTkLabel(center_box, text="", image=self.assets["logo"])
            logo_label.pack(pady=(0, 10))
        else:
            ctk.CTkLabel(center_box, text="👻",image=self.assets.get("app_icon"), 
            compound="left", font=("Arial", 90)).pack(pady=(0, 10))

        ctk.CTkLabel(center_box, text="GhostChat Active", font=("Segoe UI", 32, "bold"), text_color="#00dc82").pack(pady=10)
        
        status_box = ctk.CTkFrame(center_box, fg_color="#1e1e24", corner_radius=15, width=400)
        status_box.pack(pady=20, ipadx=30, ipady=20)
        
        grid_stats = ctk.CTkFrame(status_box, fg_color="transparent")
        grid_stats.pack(pady=10)
        
        c_frame = ctk.CTkFrame(grid_stats, fg_color="transparent")
        c_frame.pack(side="left", padx=20)
        ctk.CTkLabel(c_frame, text=f"{contacts_count}", font=("Segoe UI", 24, "bold"), text_color="white").pack()
        ctk.CTkLabel(c_frame, text="Contacts", font=("Segoe UI", 12), text_color="gray").pack()

        ctk.CTkFrame(grid_stats, width=1, height=40, fg_color="gray").pack(side="left")

        m_frame = ctk.CTkFrame(grid_stats, fg_color="transparent")
        m_frame.pack(side="left", padx=20)
        ctk.CTkLabel(m_frame, text=f"{messages_count}", font=("Segoe UI", 24, "bold"), text_color="white").pack()
        ctk.CTkLabel(m_frame, text="Messages", font=("Segoe UI", 12), text_color="gray").pack()

        ctk.CTkLabel(status_box, text="_________________", text_color="#333333").pack(pady=5)
        ctk.CTkLabel(status_box, text="🟢 System: Online", font=("Segoe UI", 14), text_color="#00dc82").pack(pady=5)
        ctk.CTkLabel(status_box, text="🔒 Security: AES-256", font=("Segoe UI", 14), text_color="#aaaaaa").pack(pady=2)

    def show_ai_playground(self):
        self.active_view = "ai_lab"
        self.current_chat_contact = None
        self.header_title.configure(text="🤖 AI Simulation Lab")
        if hasattr(self, 'clear_btn'): self.clear_btn.pack(side="right")        
        for w in self.chat_display_frame.winfo_children(): w.destroy()
        self.chat_display_frame.grid_rowconfigure(0, weight=1)
        
        self.messages_box = ctk.CTkTextbox(self.chat_display_frame, fg_color="transparent", text_color="white", state="disabled", wrap="word", font=("Segoe UI", 14))
        self.messages_box.grid(row=0, column=0, sticky="nsew")
        self.fix_input_field(self.messages_box)
        
        self.append_message_to_ui("System", "Welcome to AI Lab! Type anything to test the Syrian AI cover text generator.")
        
        self.input_container.grid(row=2, column=0, sticky="ew", padx=30, pady=20)
        self.msg_entry.focus()

    def start_telegram_client(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.telegram_loop = loop
        
        try:
            loop.run_until_complete(self.ghost.start())
        except Exception as e:
            print(f"Telegram Client Error: {e}")
        finally:
            loop.close()

    def load_contacts(self):
        for w in self.contacts_frame.winfo_children(): 
            w.destroy()
            
        db = SessionLocal()
        contacts = db.query(Contact).all()
        db.close()
        
        img_contact = self.assets.get("contact")

        for c in contacts:
            if img_contact:
                btn = ctk.CTkButton(
                    self.contacts_frame, 
                    text=f"  {c.username}",  
                    image=img_contact, 
                    compound="left", 
                    fg_color="transparent", 
                    anchor="w", 
                    height=35,
                    text_color=COLOR_TEXT_DIM, 
                    hover_color=COLOR_BTN_HOVER, 
                    command=lambda u=c.username: self.select_contact(u)
                )
            else:
                btn = ctk.CTkButton(
                    self.contacts_frame, 
                    text=f"👤  {c.username}", 
                    fg_color="transparent", 
                    anchor="w", 
                    height=35,
                    text_color=COLOR_TEXT_DIM, 
                    hover_color=COLOR_BTN_HOVER, 
                    command=lambda u=c.username: self.select_contact(u)
                )
            
            btn.pack(pady=2, fill="x")

    def select_contact(self, username):
        self.active_view = "chat"
        self.current_chat_contact = username
        self.header_title.configure(text=f"Secured Channel: @{username}")

        if hasattr(self, 'clear_btn'): self.clear_btn.pack(side="right")

        for w in self.chat_display_frame.winfo_children(): w.destroy()
        
        self.chat_display_frame.grid_rowconfigure(0, weight=1)
        

        self.chat_scroll = ctk.CTkScrollableFrame(self.chat_display_frame, fg_color="transparent")
        self.chat_scroll.grid(row=0, column=0, sticky="nsew")

        if hasattr(self, 'input_container'):
            self.input_container.grid(row=2, column=0, sticky="ew", padx=30, pady=20)
        self.msg_entry.focus()

        db = SessionLocal()
        contact = db.query(Contact).filter(Contact.username == username).first()
        if contact:
            msgs = db.query(DecryptedMessage).filter(
                DecryptedMessage.contact_id == contact.id
            ).order_by(
                DecryptedMessage.telegram_message_id.asc(),
                DecryptedMessage.id.asc()
            ).all()
            
            for m in msgs:
                if hasattr(self, 'append_message_bubble'):
                    self.append_message_bubble(m.is_sent_by_me, m.real_content, m.timestamp)
                else:
                    sender = "Me" if m.is_sent_by_me else username
                    self.append_message_to_ui(sender, m.real_content)
        db.close()
        
        if hasattr(self, 'scroll_to_bottom'): self.scroll_to_bottom()


    def append_message_bubble(self, is_me, text, timestamp=None):
        if not hasattr(self, 'chat_scroll') or not self.chat_scroll.winfo_exists(): return
        
        if is_me:
            align_anchor = "e"   
            bubble_color = COLOR_ACCENT 
            text_color = "black"    
            justify = "left"        
        else:
            align_anchor = "w"      
            bubble_color = "#2b2b2b" 
            text_color = "white"
            justify = "left"

        if timestamp is None: timestamp = datetime.now()
        time_str = timestamp.strftime('%H:%M')

        msg_container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        msg_container.pack(fill="x", pady=5, padx=10)

        bubble = ctk.CTkFrame(msg_container, fg_color=bubble_color, corner_radius=15)
        bubble.pack(anchor=align_anchor, padx=5)

        label = ctk.CTkLabel(bubble, text=text, text_color=text_color, font=("Segoe UI", 14), 
                             wraplength=400, justify=justify)
        label.pack(padx=15, pady=(10, 5))

        time_lbl = ctk.CTkLabel(bubble, text=time_str, text_color=text_color, font=("Arial", 10))
        time_lbl.pack(anchor="e" if is_me else "w", padx=15, pady=(0, 5))

        if hasattr(self, 'enable_bubble_copy'):
            self.enable_bubble_copy(label, text)
            self.enable_bubble_copy(bubble, text)

        if hasattr(self, 'scroll_to_bottom'):
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        if hasattr(self, 'chat_scroll') and self.chat_scroll.winfo_exists():
            try:
                self.chat_scroll.update_idletasks()
                self.chat_scroll._parent_canvas.yview_moveto(1.0)
            except: pass

    def handle_send_action(self, event=None):
        text = self.msg_entry.get().strip()
        if not text: return
        self.msg_entry.delete(0, "end")

        if self.active_view == "chat" and self.current_chat_contact:
            self.append_message_to_ui("Me", text)
            threading.Thread(target=self._run_async_send, args=(self.current_chat_contact, text)).start()
        
        elif self.active_view == "ai_lab":
            self.append_message_to_ui("Me (Test)", text)
            threading.Thread(target=self._run_ai_simulation, args=(text,)).start()

    def _run_ai_simulation(self, user_text):
        fake_history = [f"صديقي: {user_text}"]
        
        self.after(0, lambda: self.header_title.configure(text="🤖 AI is generating..."))
        
        try:
            response = self.ghost.ai.generate_cover_text(fake_history)
            self.after(0, lambda: self.append_message_to_ui("AI Cover", f"Original: (Hidden)\nCover Text: {response}"))
        except Exception as e:
            self.after(0, lambda: self.append_message_to_ui("System", f"Error: {e}"))
        finally:
            self.after(0, lambda: self.header_title.configure(text="🤖 AI Simulation Lab"))

    def append_message_to_ui(self, sender, text):
        is_me = True if sender.startswith("Me") else False
        if self.active_view == "ai_lab" and hasattr(self, 'messages_box'):
             self.messages_box.configure(state="normal")
             time_str = datetime.now().strftime('%H:%M')
             if sender == "AI Cover":
                 self.messages_box.insert("end", f"\n──────────────\n🤖 {sender} [{time_str}]\n{text}\n──────────────\n")
             else:
                 self.messages_box.insert("end", f"\n ► {sender} [{time_str}]\n{text}\n\n")
             self.messages_box.see("end")
             self.messages_box.configure(state="disabled")
        else:
             self.append_message_bubble(is_me, text)

    def enable_bubble_copy(self, widget, text_to_copy):
        menu = tk.Menu(widget, tearoff=0, bg="white", fg="black")
        menu.add_command(label="📋 Copy Message", command=lambda: self.clipboard_clear() or self.clipboard_append(text_to_copy))
        
        def show_menu(event):
            try: menu.tk_popup(event.x_root, event.y_root)
            finally: menu.grab_release()

        widget.bind("<Button-3>", show_menu)
        if sys.platform == "darwin": widget.bind("<Button-2>", show_menu)


    

    def send_message(self, event=None):
        text = self.msg_entry.get()
        if not text or not self.current_chat_contact: return
        self.append_message_to_ui("Me", text)
        self.msg_entry.delete(0, "end")
        threading.Thread(target=self._run_async_send, args=(self.current_chat_contact, text)).start()

    def _run_async_send(self, username, text):
        if self.telegram_loop and self.telegram_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.ghost.send_ghost_message(username, text), 
                self.telegram_loop
            )
        else:
            print("Telegram loop is not ready yet!")

    def on_incoming_message(self, sender, text):
        if self.current_chat_contact == sender:
            self.append_message_to_ui(sender, text)

    def clear_chat_display(self):
        if hasattr(self, 'chat_scroll') and self.chat_scroll.winfo_exists():
            for child in self.chat_scroll.winfo_children():
                child.destroy()
        
        if hasattr(self, 'messages_box') and self.messages_box.winfo_exists():
            self.messages_box.configure(state="normal")
            self.messages_box.delete("1.0", "end")
            self.messages_box.configure(state="disabled")

    def open_profile_window(self):
        window = ctk.CTkToplevel(self)
        window.title("My Profile")
        window.geometry("300x250")
        window.attributes("-topmost", True)
        try:
            icon_path = resource_path(os.path.join("assets", "app_icon.ico"))
            if os.path.exists(icon_path):
                window.after(200, lambda: window.iconbitmap(icon_path))
        except: pass

        ctk.CTkLabel(window, text="User Profile",image=self.assets["profile"], compound="left", font=("Arial", 18, "bold")).pack(pady=20)
        
        info_frame = ctk.CTkFrame(window)
        info_frame.pack(padx=20, fill="x")
        
        session_name = os.getenv('TG_SESSION', 'MyAccount')
        ctk.CTkLabel(info_frame, text=f"Session: {session_name}", anchor="w").pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(info_frame, text="Status: Online 🟢", text_color="green", anchor="w").pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(window, text="Close", command=window.destroy).pack(pady=20)

    def open_settings_window(self):
        window = ctk.CTkToplevel(self)
        window.title("Settings")
        window.geometry("300x300")
        window.attributes("-topmost", True)
        try:
            icon_path = resource_path(os.path.join("assets", "app_icon.ico"))
            if os.path.exists(icon_path):
                window.after(200, lambda: window.iconbitmap(icon_path))
        except: pass

        ctk.CTkLabel(window, 
                     text=" Settings",          
                     image=self.assets["settings"],   
                     compound="left",                 
                     font=("Arial", 18, "bold")).pack(pady=20)
        
        def clear_db():
            if messagebox.askyesno("Warning", "Delete all local messages history?"):
                try:
                    if hasattr(self, 'messages_box'):
                        self.messages_box.configure(state="normal")
                        self.messages_box.delete("1.0", "end")
                        self.messages_box.configure(state="disabled")
                    messagebox.showinfo("Done", "Screen Cleared!")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

        ctk.CTkButton(window, text="Clear Screen History", fg_color="#C62828", hover_color="#8B0000", command=clear_db).pack(pady=10)
        ctk.CTkSwitch(window, text="Dark Mode", onvalue="Dark", offvalue="Light", command=lambda: ctk.set_appearance_mode("Dark")).pack(pady=10)

    def logout_app(self):
        msg = messagebox.askyesno("Logout", "Are you sure you want to logout and exit?")
        if not msg:
            return

        print("Logging out...")
        try:
            if self.telegram_loop and self.telegram_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.ghost.client.log_out(), 
                    self.telegram_loop
                )
                try: future.result(timeout=3)
                except: pass
        except Exception as e:
            print(f"Error during logout: {e}")

        self.destroy()
        os._exit(0)

    def add_contact_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Contact")
        dialog.geometry("400x350")
        dialog.attributes("-topmost", True)
        try:
            icon_path = resource_path(os.path.join("assets", "app_icon.ico"))
            if os.path.exists(icon_path):
                dialog.after(200, lambda: dialog.iconbitmap(icon_path))
        except: pass

        ctk.CTkLabel(dialog, text="Telegram Username (No @):").pack(pady=(20, 5))
        username_entry = ctk.CTkEntry(dialog, width=300)
        username_entry.pack(pady=5)
        self.fix_input_field(username_entry, root_window=dialog)

        ctk.CTkLabel(dialog, text="Secret Key (Leave empty to generate new):").pack(pady=(20, 5))
        key_entry = ctk.CTkEntry(dialog, width=300, placeholder_text="Paste key here if friend gave you one...")
        key_entry.pack(pady=5)
        self.fix_input_field(key_entry, root_window=dialog)

        def save():
            username = username_entry.get()
            manual_key = key_entry.get()
            
            if username:
                final_key = manual_key if manual_key.strip() else CryptoEngine.generate_key()
                
                db = SessionLocal()
                if db.query(Contact).filter(Contact.username == username).first():
                    print("Contact already exists!")
                    db.close()
                    dialog.destroy()
                    return

                new_contact = Contact(telegram_id=random.randint(1000, 999999), username=username, shared_key=final_key)
                db.add(new_contact)
                db.commit()
                db.close()
                
                self.load_contacts()
                dialog.destroy()
                
                if not manual_key:
                    self.show_key_popup(username, final_key)

        ctk.CTkButton(dialog, text="Save Contact", command=save, fg_color=COLOR_ACCENT, text_color="black").pack(pady=30)

    def show_key_popup(self, username, key):
        win = ctk.CTkToplevel(self)
        win.title("Key Generated")
        win.geometry("400x200")
        win.attributes("-topmost", True)
        ctk.CTkLabel(win, text=f"Share this key SECURELY with {username}:").pack(pady=20)
        e = ctk.CTkEntry(win, width=350)
        e.insert(0, key)
        e.pack(pady=10)
        self.fix_input_field(e, root_window=win)
        ctk.CTkLabel(win, text="Warning: Without this key, they cannot read your messages!", text_color="red").pack()


    def enable_global_copy_paste(self):
        def copy_text(event):
            try:
                widget = self.focus_get()
                if isinstance(widget, (tk.Entry, tk.Text)): 
                    if widget.selection_present():
                        text = widget.selection_get()
                        self.clipboard_clear()
                        self.clipboard_append(text)
                        self.update() 
                return "break"
            except:
                pass

        def paste_text(event):
            try:
                text = self.clipboard_get()
                widget = self.focus_get()
                if isinstance(widget, (tk.Entry, tk.Text)):
                    if isinstance(widget, tk.Text):
                        widget.insert("insert", text)
                    elif isinstance(widget, tk.Entry):
                        widget.insert("insert", text)
                return "break"
            except:
                pass

        def select_all(event):
            try:
                widget = self.focus_get()
                if isinstance(widget, tk.Entry):
                    widget.select_range(0, 'end')
                    widget.icursor('end')
                elif isinstance(widget, tk.Text):
                    widget.tag_add('sel', '1.0', 'end')
                return "break"
            except:
                pass

        self.bind_all("<Control-c>", copy_text)
        self.bind_all("<Control-v>", paste_text)
        self.bind_all("<Control-a>", select_all)
        self.bind_all("<Command-c>", copy_text)
        self.bind_all("<Command-v>", paste_text)
        self.bind_all("<Command-a>", select_all)

    def fix_input_field(self, widget, root_window=None):
        try:
            target = widget._entry if hasattr(widget, "_entry") else widget._textbox
        except AttributeError:
            target = widget

        assets_dir = resource_path("assets")
        
        image_master = root_window if root_window else self

        def load_icon(filename):
            path = os.path.join(assets_dir, filename)
            if not os.path.exists(path):
                return None 
            
            pil_img = Image.open(path)
            resized_img = pil_img.resize((20, 20), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(resized_img, master=image_master)

        menu = tk.Menu(target, tearoff=0, bg="white", fg="black")

        menu.icon_cut = load_icon("icon_cut.png")
        menu.icon_copy = load_icon("icon_copy.png")
        menu.icon_paste = load_icon("icon_paste.png")
        menu.icon_select = load_icon("icon_select_all.png")

        menu.add_command(
            label="✂️  Cut", 
            image=menu.icon_cut,
            compound="left",
            command=lambda: target.event_generate("<<Cut>>")
        )
        
        menu.add_command(
            label="📄  Copy",
            image=menu.icon_copy,
            compound="left",
            command=lambda: target.event_generate("<<Copy>>")
        )
        
        menu.add_command(
            label="📋  Paste",
            image=menu.icon_paste,
            compound="left",
            command=lambda: target.event_generate("<<Paste>>")
        )
        
        menu.add_separator() 
        
        menu.add_command(
            label="✅  Select All",
            image=menu.icon_select,
            compound="left",
            command=lambda: target.event_generate("<<SelectAll>>")
        )

        def show_menu(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        target.bind("<Button-3>", show_menu) 
        
        if sys.platform == "darwin": 
             target.bind("<Button-2>", show_menu)
             
        target.bind("<Control-c>", lambda e: target.event_generate("<<Copy>>"))
        target.bind("<Control-v>", lambda e: target.event_generate("<<Paste>>"))
        target.bind("<Control-a>", lambda e: target.event_generate("<<SelectAll>>"))

    def check_and_pull_model(self):
        model = "qwen2.5:0.5b"
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
            if model not in result.stdout:
                messagebox.showinfo("Setup", "First run setup: Downloading AI Model...")
                subprocess.run(["ollama", "pull", model], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showerror("Error", "Ollama is not installed or not running. Please install it from ollama.com")
        except Exception as e:
            print(f"Ollama Check Error: {e}")
        
if __name__ == "__main__":
    app = GhostChatApp()
    app.mainloop()