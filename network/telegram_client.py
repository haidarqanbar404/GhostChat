import os
import sys
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv
from core.steganography import SteganographyEngine
from core.crypto import CryptoEngine
from core.ai import AIEngine
from database.models import SessionLocal, Contact, DecryptedMessage, save_message
import time
from tkinter import simpledialog

load_dotenv()

class GhostNetwork:
    def __init__(self, on_message_received=None, session_name="ghost_session", config=None, gui_instance=None):
        self.session_name = session_name
        self.gui_instance = gui_instance
        self.config = config
        
        self.api_id = config.get("api_id") if config else os.getenv("TG_API_ID")
        self.api_hash = config.get("api_hash") if config else os.getenv("TG_API_HASH")
        self.phone = config.get("phone") if config else os.getenv("TG_PHONE")
        
        try: api_id_int = int(self.api_id)
        except: api_id_int = 0

        # --- التعديل الجذري: تحديد مسار مطلق لملف الجلسة ---
        # هذا يضمن أن البرنامج يجد ملف الجلسة دائماً في المجلد الرئيسي للمشروع
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            # نعود خطوة للوراء لأننا داخل مجلد network
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        # دمج المسار مع اسم الجلسة
        session_path = os.path.join(base_path, self.session_name)

        # نمرر المسار الكامل للعميل
        self.client = TelegramClient(
            session_path,  # <--- هنا التغيير المهم
            api_id_int, 
            self.api_hash,
            system_version="4.16.30-vxCUSTOM"
        )

        self.stego = SteganographyEngine()
        self.crypto = CryptoEngine()
        self.ai = AIEngine()
        self.on_message_received = on_message_received
        self._user_input_result = None

    async def start(self):
        print(f"Connecting to Telegram...")
        
        def safe_input_request(prompt_title, prompt_text, is_password=False):
            if not self.gui_instance: return input(f"{prompt_text}: ")
            self._user_input_result = None
            def ask():
                if is_password: self._user_input_result = simpledialog.askstring(prompt_title, prompt_text, show='*', parent=self.gui_instance)
                else: self._user_input_result = simpledialog.askstring(prompt_title, prompt_text, parent=self.gui_instance)
                if self._user_input_result is None: self._user_input_result = "CANCELLED"
            self.gui_instance.after(0, ask)
            while self._user_input_result is None:
                time.sleep(0.1)
                try: 
                    if not self.gui_instance.winfo_exists(): raise InterruptedError("App Closed")
                except: raise InterruptedError("App Closed")
            if self._user_input_result == "CANCELLED": raise ValueError("User cancelled.")
            return self._user_input_result

        def phone_callback(): return self.phone if self.phone else safe_input_request("Login", "Phone:")
        def code_callback(): return safe_input_request("Code", "Code:")
        def password_callback(): return safe_input_request("Password", "Password:", True)

        await self.client.start(phone=phone_callback, code_callback=code_callback, password=password_callback)
        print("✅ Connected successfully!")
        self.client.add_event_handler(self.handle_incoming_message, events.NewMessage(incoming=True))
        await self.client.run_until_disconnected()

    async def send_ghost_message(self, username, secret_text):
        try:
            db = SessionLocal()
            contact = db.query(Contact).filter(Contact.username == username).first()
            if not contact:
                print(f"❌ Error: Contact {username} not found.")
                db.close(); return

            shared_key = contact.shared_key
            db.close()

            encrypted_data = self.crypto.encrypt(secret_text, shared_key)
            
            # جلب السياق والذكاء الاصطناعي
            history = []
            try:
                async for message in self.client.iter_messages(username, limit=3):
                    sender = "أنا" if message.out else "صديقي"
                    if message.text: history.append(f"{sender}: {message.text}")
                history.reverse()
            except: pass

            loop = asyncio.get_event_loop()
            cover_text = await loop.run_in_executor(None, self.ai.generate_cover_text, history)
            
            final_message = self.stego.hide_data(encrypted_data, [cover_text])

            await self.client.send_message(username, final_message)
            print(f"📤 Sent: {cover_text} (Hidden sent)")
            save_message(contact.id, secret_text, is_sent_by_me=True)

        except Exception as e:
            print(f"⚠️ Send Error: {e}")

    async def handle_incoming_message(self, event):
        try:
            sender = await event.get_sender()
            if not sender or not sender.username: return
            username = sender.username
            
            db = SessionLocal()
            contact = db.query(Contact).filter(Contact.username == username).first()
            if not contact: db.close(); return
            
            shared_key = contact.shared_key
            db.close()

            encrypted_payload = self.stego.reveal_data(event.raw_text)
            if encrypted_payload:
                decrypted = self.crypto.decrypt(encrypted_payload, shared_key)
                if decrypted:
                    print(f"📩 Decrypted from @{username}: {decrypted}")
                    save_message(contact.id, decrypted, is_sent_by_me=False)
                    if self.on_message_received:
                        self.on_message_received(username, decrypted)
        except Exception as e:
            print(f"Incoming Error: {e}")