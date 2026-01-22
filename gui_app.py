import customtkinter as ctk
import threading
import asyncio
import os
from datetime import datetime
from PIL import Image, ImageTk
import random
import tkinter as tk
from tkinter import messagebox
# استيراد كلاسات الباك-إند
from network.telegram_client import GhostNetwork
from database.models import init_db, SessionLocal, Contact, DecryptedMessage
from core.crypto import CryptoEngine
import ctypes

# هذا الكود يخبر ويندوز أن هذا تطبيق مستقل وليس مجرد سكريبت بايثون
myappid = 'mycompany.ghostchat.gui.1.0' # معرف فريد عشوائي
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# ----------------------------------------------------------------
# 🎨 COLOR PALETTE & CONFIG
# ----------------------------------------------------------------
COLOR_BG = "#0b0b0f"        # Deepest Black
COLOR_SIDEBAR = "#121216"   # Sidebar Background
COLOR_ACCENT = "#00dc82"    # Neon Green (Brand Color)
COLOR_TEXT_MAIN = "#ffffff" 
COLOR_TEXT_DIM = "#8a8a93"  
COLOR_INPUT_BG = "#1e1e24"  
COLOR_BTN_HOVER = "#2a2a35" 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class GhostChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.telegram_loop = None

        self.ghost = GhostNetwork(on_message_received=self.on_incoming_message)

        # Window Setup
        self.title("GhostChat - Stealth Messenger")
        self.geometry("1100x700")
        self.configure(fg_color=COLOR_BG)

        current_dir = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(current_dir, "assets", "app_icon.ico")

        # 2. التأكد من وجود الملف قبل تحميله لتشخيص المشكلة
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        # Database & Backend Setup
        init_db()
        self.current_chat_contact = None 
        
        # Load Images (With Fallback)
        self.assets = {}
        self.load_assets()
        
        # Set Window Icon
        if "app_icon" in self.assets:
             # ملاحظة: CTk لا يدعم وضع الأيقونة مباشرة من كائن الصورة، يحتاج مسار ملف .ico في ويندوز
             try: self.iconbitmap(os.path.join("assets", "app_icon.ico"))
             except: pass

        # Start Backend Thread
        self.ghost = GhostNetwork(on_message_received=self.on_incoming_message)
        self.network_thread = threading.Thread(target=self.start_telegram_client, daemon=True)
        self.network_thread.start()

        # Build UI
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        self.load_contacts()
        self.enable_global_copy_paste()

    def load_assets(self):
        """
        محاولة تحميل الصور. في حال عدم وجود الصورة، نستخدم None 
        ليقوم الكود لاحقاً باستخدام نص بديل (Fallback Text).
        """
        assets_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")
        
        # قائمة الملفات المطلوبة وأحجامها
        files = {
            "logo": ("logo.png", (35, 35)),
            "chat": ("icon_chat.png", (20, 20)),
            "profile": ("icon_profile.png", (20, 20)),
            "settings": ("icon_settings.png", (20, 20)),
            "logout": ("icon_logout.png", (20, 20)),
            "send": ("icon_send.png", (20, 20)),
            "attach": ("icon_attach.png", (24, 24)),
            "mic": ("icon_mic.png", (24, 24)),
            "contact": ("icon_contact.png", (20, 20)), # صورة الشخص
            "plus": ("icon_plus.png", (16, 16)),
            "clear": ("icon_clear.png", (20, 20)), # أيقونة المسح الجديدة
            "cut": ("icon_cut.png", (20, 20)),
            "copy": ("icon_copy.png", (20, 20)),
            "paste": ("icon_paste.png", (20, 20)),
            "select_all": ("icon_select_all.png", (20, 20)),
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
                    print(f"⚠️ Error loading {filename}: {e}")
                    self.assets[key] = None
            else:
                self.assets[key] = None # لم يتم العثور على الملف

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # 1. Logo Section
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="w")
        
        # استخدام صورة الشعار إذا وجدت
        if self.assets["logo"]:
            logo_lbl = ctk.CTkLabel(self.logo_frame, text="", image=self.assets["logo"])
            logo_lbl.pack(side="left")
        else:
            logo_lbl = ctk.CTkLabel(self.logo_frame, text="👻", font=("Arial", 24))
            logo_lbl.pack(side="left")
            
        logo_text = ctk.CTkLabel(self.logo_frame, text="GhostChat", font=("Segoe UI", 18, "bold"), text_color="white")
        logo_text.pack(side="left", padx=10)

        # 2. AI Chat Button (Always Active Visual)
        chat_btn = ctk.CTkButton(self.sidebar, text="  AI Chat", image=self.assets["chat"], compound="left",
                                 anchor="w", fg_color="#1e1e24", text_color="white", hover_color=COLOR_BTN_HOVER,
                                 font=("Segoe UI", 14), height=40, corner_radius=8)
        chat_btn.grid(row=1, column=0, padx=15, pady=2, sticky="ew")

        # 3. Profile Button (Functional)
        self.btn_profile = ctk.CTkButton(
            self.sidebar, 
            text="  Profile", 
            image=self.assets["profile"],
            compound="left", 
            anchor="w", 
            fg_color="transparent", 
            text_color="#8a8a93",
            hover_color=COLOR_BTN_HOVER,
            font=("Segoe UI", 14), height=40, corner_radius=8,
            command=self.open_profile_window  # <--- New Function
        )
        self.btn_profile.grid(row=2, column=0, padx=15, pady=2, sticky="ew")

        # 4. Settings Button (Functional)
        self.btn_settings = ctk.CTkButton(
            self.sidebar, 
            text="  Settings", 
            image=self.assets["settings"],
            compound="left",
            anchor="w", 
            fg_color="transparent", 
            text_color="#8a8a93",
            hover_color=COLOR_BTN_HOVER,
            font=("Segoe UI", 14), height=40, corner_radius=8,
            command=self.open_settings_window # <--- New Function
        )
        self.btn_settings.grid(row=3, column=0, padx=15, pady=2, sticky="ew")

        # 5. Contacts Header
        contact_lbl = ctk.CTkLabel(self.sidebar, text="CONTACTS", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT_DIM, anchor="w")
        contact_lbl.grid(row=8, column=0, padx=25, pady=(20, 10), sticky="w")
        
        self.contacts_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.contacts_frame.grid(row=9, column=0, sticky="nsew", padx=10)

        # 6. Add Contact Button
        img_plus = self.assets.get("plus")
        if img_plus:
            add_btn = ctk.CTkButton(self.sidebar, text="New Contact", image=img_plus, compound="left", 
                                    fg_color=COLOR_BTN_HOVER, command=self.add_contact_dialog, height=35, anchor="center")
        else:
            add_btn = ctk.CTkButton(self.sidebar, text="+ New Contact", fg_color=COLOR_BTN_HOVER, command=self.add_contact_dialog)
            
        add_btn.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        # 7. Logout Button (Functional & Red)
        self.btn_logout = ctk.CTkButton(
            self.sidebar, 
            text="  Log out", 
            image=self.assets["logout"], 
            compound="left",
            anchor="w", 
            fg_color="transparent",           # Dark Red Background
            hover_color="#2C1717",        # Red on Hover
            text_color="#ff6b6b",
            font=("Segoe UI", 14), height=40, corner_radius=8,
            command=self.logout_app       # <--- New Function
        )
        self.btn_logout.grid(row=11, column=0, padx=15, pady=20, sticky="ew")

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self.main_frame, height=60, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        self.header_title = ctk.CTkLabel(self.header, text="AI Ghost Chat", font=("Segoe UI", 16, "bold"), text_color="white")
        self.header_title.pack(side="left")
        
        # --- زر المسح الجديد (أحمر عند الهوفر + أيقونة) ---
        self.clear_button = ctk.CTkButton(
            self.header, 
            text=" Clear",        
            image=self.assets.get("clear"),
            compound="left",      
            width=80,
            height=30,
            fg_color="transparent", 
            border_width=1,
            border_color="#3E3E3E", 
            text_color="#AAAAAA",
            hover_color="#C62828",  # لون أحمر عند التمرير
            command=self.clear_chat_display # سنضيف هذه الدالة بالأسفل
        )
        self.clear_button.pack(side="right")

        # Chat Area
        self.chat_display_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.chat_display_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        
        self.show_hero_section()
        self.create_input_bar()

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
        container = ctk.CTkFrame(self.main_frame, height=80, fg_color="transparent")
        container.grid(row=2, column=0, sticky="ew", padx=30, pady=20)
        
        self.input_bg = ctk.CTkFrame(container, height=55, corner_radius=25, fg_color=COLOR_INPUT_BG)
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
        self.msg_entry.bind("<Return>", self.send_message)

        img_send = self.assets["send"]
        t_send = "" if img_send else "➤"
        self.send_btn = ctk.CTkButton(self.input_bg, text=t_send, image=img_send, width=45, height=35, corner_radius=18,
                                      fg_color=COLOR_ACCENT, hover_color="#00b368", text_color="black", command=self.send_message)
        self.send_btn.pack(side="right", padx=10, pady=10)

    def start_telegram_client(self):
        self.telegram_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.telegram_loop)
        
        self.telegram_loop.run_until_complete(self.ghost.start())

    def load_contacts(self):
        # تنظيف القائمة القديمة
        for w in self.contacts_frame.winfo_children(): 
            w.destroy()
            
        db = SessionLocal()
        contacts = db.query(Contact).all()
        db.close()
        
        # جلب أيقونة الشخص (contact icon)
        img_contact = self.assets.get("contact")

        for c in contacts:
            if img_contact:
                # استخدام الأيقونة
                btn = ctk.CTkButton(
                    self.contacts_frame, 
                    text=f"  {c.username}",   # مسافة جمالية
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
                # استخدام الإيموجي كبديل
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
        self.current_chat_contact = username
        self.header_title.configure(text=f"Secured Channel: @{username}")
        for w in self.chat_display_frame.winfo_children(): w.destroy()
        
        self.chat_display_frame.grid_rowconfigure(0, weight=1)
        self.messages_box = ctk.CTkTextbox(self.chat_display_frame, fg_color="transparent", text_color="white", 
                                           font=("Segoe UI", 14), state="disabled", wrap="word")
        self.messages_box.grid(row=0, column=0, sticky="nsew")
        self.fix_input_field(self.messages_box) # تفعيل القائمة للرسائل أيضاً

        db = SessionLocal()
        contact = db.query(Contact).filter(Contact.username == username).first()
        if contact:
            msgs = db.query(DecryptedMessage).filter(DecryptedMessage.contact_id == contact.id).order_by(DecryptedMessage.timestamp).all()
            for m in msgs:
                sender = "Me" if m.is_sent_by_me else username
                self.append_message_to_ui(sender, m.real_content)
        db.close()

    def append_message_to_ui(self, sender, text):
        if not hasattr(self, 'messages_box'): return
        self.messages_box.configure(state="normal")
        time_str = datetime.now().strftime("%H:%M")
        
        # تنسيق بدائي (CustomTkinter Textbox محدود في الألوان المتعددة داخل نفس النص)
        header = f" ► {sender} [{time_str}]"
        self.messages_box.insert("end", f"\n{header}\n{text}\n\n")
        self.messages_box.see("end")
        self.messages_box.configure(state="disabled")

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

    # ------------------ New Functions ------------------ #
    def clear_chat_display(self):
        """تفريغ الشاشة فقط (بدون حذف من قاعدة البيانات)"""
        if hasattr(self, 'messages_box'):
            self.messages_box.configure(state="normal")
            self.messages_box.delete("1.0", "end")
            self.messages_box.configure(state="disabled")

    def open_profile_window(self):
        """نافذة البروفايل"""
        window = ctk.CTkToplevel(self)
        window.title("My Profile")
        window.geometry("300x250")
        window.attributes("-topmost", True)

        ctk.CTkLabel(window, text="👤 User Profile", font=("Arial", 18, "bold")).pack(pady=20)
        
        info_frame = ctk.CTkFrame(window)
        info_frame.pack(padx=20, fill="x")
        
        # محاولة عرض اسم الجلسة
        session_name = os.getenv('TG_SESSION', 'MyAccount')
        ctk.CTkLabel(info_frame, text=f"Session: {session_name}", anchor="w").pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(info_frame, text="Status: Online 🟢", text_color="green", anchor="w").pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(window, text="Close", command=window.destroy).pack(pady=20)

    def open_settings_window(self):
        """نافذة الإعدادات"""
        window = ctk.CTkToplevel(self)
        window.title("Settings")
        window.geometry("300x300")
        window.attributes("-topmost", True)
        
        ctk.CTkLabel(window, text="⚙️ Settings", font=("Arial", 18, "bold")).pack(pady=20)
        
        def clear_db():
            if messagebox.askyesno("Warning", "Delete all local messages history?"):
                try:
                    if hasattr(self, 'messages_box'):
                        self.messages_box.configure(state="normal")
                        self.messages_box.delete("1.0", "end")
                        self.messages_box.configure(state="disabled")
                    # ملاحظة: لحذف فعلي من DB يجب إضافة كود SQL هنا
                    messagebox.showinfo("Done", "Screen Cleared!")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

        ctk.CTkButton(window, text="🗑️ Clear Screen History", fg_color="#C62828", hover_color="#8B0000", command=clear_db).pack(pady=10)
        ctk.CTkSwitch(window, text="Dark Mode", onvalue="Dark", offvalue="Light", command=lambda: ctk.set_appearance_mode("Dark")).pack(pady=10)

    def logout_app(self):
        """تسجيل الخروج الآمن"""
        msg = messagebox.askyesno("Logout", "Are you sure you want to logout and exit?")
        if not msg:
            return

        print("🔌 Logging out...")
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
        # نافذة تطلب الاسم والمفتاح (اختياري)
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Contact")
        dialog.geometry("400x350")
        dialog.attributes("-topmost", True)
        # 1. حقل الاسم
        ctk.CTkLabel(dialog, text="Telegram Username (No @):").pack(pady=(20, 5))
        username_entry = ctk.CTkEntry(dialog, width=300)
        username_entry.pack(pady=5)
        self.fix_input_field(username_entry)

        # 2. حقل المفتاح (لصق المفتاح الموجود، أو تركه فارغاً للتوليد)
        ctk.CTkLabel(dialog, text="Secret Key (Leave empty to generate new):").pack(pady=(20, 5))
        key_entry = ctk.CTkEntry(dialog, width=300, placeholder_text="Paste key here if friend gave you one...")
        key_entry.pack(pady=5)
        self.fix_input_field(key_entry)

        def save():
            username = username_entry.get()
            manual_key = key_entry.get()
            
            if username:
                # إذا أدخل المستخدم مفتاحاً نستخدمه، وإلا نولد واحداً جديداً
                final_key = manual_key if manual_key.strip() else CryptoEngine.generate_key()
                
                db = SessionLocal()
                # التحقق من عدم وجوده مسبقاً
                if db.query(Contact).filter(Contact.username == username).first():
                    print("Contact already exists!")
                    db.close()
                    dialog.destroy()
                    return

                # حفظ في قاعدة البيانات
                # نستخدم ID وهمي مؤقتاً
                new_contact = Contact(telegram_id=random.randint(1000, 999999), username=username, shared_key=final_key)
                db.add(new_contact)
                db.commit()
                db.close()
                
                self.load_contacts()
                dialog.destroy()
                
                # عرض المفتاح النهائي للمستخدم لنسخه
                if not manual_key:
                    self.show_key_popup(username, final_key)

        ctk.CTkButton(dialog, text="Save Contact", command=save, fg_color=COLOR_ACCENT, text_color="black").pack(pady=30)

    def show_key_popup(self, username, key):
        # نافذة صغيرة لعرض المفتاح الجديد
        win = ctk.CTkToplevel(self)
        win.title("Key Generated")
        win.geometry("400x200")
        win.attributes("-topmost", True)
        ctk.CTkLabel(win, text=f"Share this key SECURELY with {username}:").pack(pady=20)
        e = ctk.CTkEntry(win, width=350)
        e.insert(0, key)
        e.pack(pady=10)
        self.fix_input_field(e)
        ctk.CTkLabel(win, text="Warning: Without this key, they cannot read your messages!", text_color="red").pack()


    def enable_global_copy_paste(self):
        """
        تفعيل اختصارات النسخ واللصق والقص يدوياً لكل حقول التطبيق
        """
        def copy_text(event):
            try:
                # جلب الودجت الذي عليه التركيز حالياً
                widget = self.focus_get()
                # التحقق إذا كان حقلاً نصياً
                if isinstance(widget, (tk.Entry, tk.Text)): 
                    if widget.selection_present():
                        text = widget.selection_get()
                        self.clipboard_clear()
                        self.clipboard_append(text)
                        self.update() # تحديث الحافظة فوراً
                return "break"
            except:
                pass

        def paste_text(event):
            try:
                text = self.clipboard_get()
                widget = self.focus_get()
                if isinstance(widget, (tk.Entry, tk.Text)):
                    # إذا كان text box (مثل الشات)
                    if isinstance(widget, tk.Text):
                        widget.insert("insert", text)
                    # إذا كان entry (مثل حقل الكتابة)
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

        # ربط الاختصارات بالنظام كاملاً
        self.bind_all("<Control-c>", copy_text)
        self.bind_all("<Control-v>", paste_text)
        self.bind_all("<Control-a>", select_all)
        # لنظام الماك (Command Key) احتياطاً
        self.bind_all("<Command-c>", copy_text)
        self.bind_all("<Command-v>", paste_text)
        self.bind_all("<Command-a>", select_all)

    def fix_input_field(self, widget):
        """
        إصلاح الحقول وإضافة قائمة زر يمين احترافية مع أيقونات
        """
        # 1. البحث عن العنصر الحقيقي المخفي
        try:
            target = widget._entry if hasattr(widget, "_entry") else widget._textbox
        except AttributeError:
            target = widget

        # 2. تجهيز مسار مجلد الأيقونات
        # يفترض هذا الكود أن مجلد assets بجانب ملف gui_app.py
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")

        # دالة مساعدة صغيرة لتحميل وتصغير الأيقونة
        def load_icon(filename):
            path = os.path.join(assets_dir, filename)
            if not os.path.exists(path):
                # print(f"⚠️ Icon missing: {filename}")
                return None # تجنب تعليق البرنامج إذا نقصت صورة
            
            # تحميل الصورة وتصغيرها لحجم مناسب للقائمة (مثلاً 20x20)
            pil_img = Image.open(path)
            resized_img = pil_img.resize((20, 20), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(resized_img)

        # 3. إنشاء القائمة
        menu = tk.Menu(target, tearoff=0, bg="white", fg="black") # ألوان اختيارية

        # --- تحميل الأيقونات ---
        # ملاحظة هامة: يجب حفظ مرجع للصور داخل كائن القائمة
        # وإلا سيقوم بايثون بحذفها من الذاكرة ولن تظهر!
        menu.icon_cut = load_icon("icon_cut.png")
        menu.icon_copy = load_icon("icon_copy.png")
        menu.icon_paste = load_icon("icon_paste.png")
        menu.icon_select = load_icon("icon_select_all.png")

        # --- إضافة العناصر مع الأيقونات ---
        # نستخدم compound="left" لوضع الأيقونة يسار النص
        
        menu.add_command(
            label="  Cut",
            image=menu.icon_cut,
            compound="left",
            command=lambda: target.event_generate("<<Cut>>")
        )
        
        menu.add_command(
            label="  Copy",
            image=menu.icon_copy,
            compound="left",
            command=lambda: target.event_generate("<<Copy>>")
        )
        
        menu.add_command(
            label="  Paste",
            image=menu.icon_paste,
            compound="left",
            command=lambda: target.event_generate("<<Paste>>")
        )
        
        menu.add_separator() # خط فاصل أنيق
        
        menu.add_command(
            label="  Select All",
            image=menu.icon_select,
            compound="left",
            command=lambda: target.event_generate("<<SelectAll>>")
        )

        # دالة عرض القائمة عند مكان الماوس
        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)

        # 4. ربط الأحداث (الزر اليمين + اختصارات الكيبورد)
        target.bind("<Button-3>", show_menu) # Windows/Linux Right Click
        if target.winfo_name() != "win": # MacOS أحياناً يستخدم Button-2
             target.bind("<Button-2>", show_menu)
             
        # إجبار اختصارات الكيبورد أيضاً
        target.bind("<Control-c>", lambda e: target.event_generate("<<Copy>>"))
        target.bind("<Control-v>", lambda e: target.event_generate("<<Paste>>"))
        target.bind("<Control-a>", lambda e: target.event_generate("<<SelectAll>>"))
        
if __name__ == "__main__":
    app = GhostChatApp()
    app.mainloop()