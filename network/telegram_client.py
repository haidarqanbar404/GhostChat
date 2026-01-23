import os
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv
from core.steganography import SteganographyEngine
from core.crypto import CryptoEngine
from database.models import SessionLocal, Contact, DecryptedMessage, save_message
import tkinter as tk
from tkinter import simpledialog
import time

load_dotenv()

class GhostNetwork:
    # التعديل هنا: أضفنا config كمعامل
    def __init__(self, on_message_received=None, session_name="ghost_session", config=None, gui_instance=None):
        self.session_name = session_name
        self.gui_instance = gui_instance
        self.config = config
        
        # الأولوية للكونفيج القادم من الواجهة، ثم لملف .env
        self.api_id = config.get("api_id") if config else os.getenv("TG_API_ID")
        self.api_hash = config.get("api_hash") if config else os.getenv("TG_API_HASH")
        self.phone = config.get("phone") if config else os.getenv("TG_PHONE")

        if not self.api_id or not self.api_hash:
            print("⚠️ Warning: API ID or HASH missing.")

        # التأكد من أن ID رقم صحيح
        try:
            real_api_id = int(self.api_id)
        except:
            real_api_id = 0

        self.client = TelegramClient(
            self.session_name, 
            real_api_id, 
            self.api_hash,
            system_version="4.16.30-vxCUSTOM"
        )

        self.stego = SteganographyEngine()
        self.crypto = CryptoEngine()
        self.on_message_received = on_message_received
        self._user_input_result = None

    async def start(self):
        print(f"Connecting to Telegram as '{self.session_name}'...")
        
        # دالة طلب الإدخال من الواجهة
        def safe_input_request(prompt_title, prompt_text, is_password=False):
            if not self.gui_instance:
                return input(f"{prompt_text}: ")

            self._user_input_result = None
            
            def ask():
                if is_password:
                    self._user_input_result = simpledialog.askstring(prompt_title, prompt_text, show='*', parent=self.gui_instance)
                else:
                    self._user_input_result = simpledialog.askstring(prompt_title, prompt_text, parent=self.gui_instance)
                
                if self._user_input_result is None:
                    self._user_input_result = "CANCELLED"

            self.gui_instance.after(0, ask)
            
            while self._user_input_result is None:
                time.sleep(0.1)
                try:
                    if not self.gui_instance.winfo_exists():
                        raise InterruptedError("App Closed")
                except:
                    raise InterruptedError("App Closed")
            
            if self._user_input_result == "CANCELLED":
                raise ValueError("User cancelled the input.")
                
            return self._user_input_result

        # نستخدم البيانات المخزنة إذا وجدت، وإلا نطلبها
        def phone_callback():
            if self.phone: return self.phone
            return safe_input_request("Telegram Login", "Enter your Phone Number:")

        def code_callback():
            return safe_input_request("Verification Code", "Enter the code you received:")

        def password_callback():
            return safe_input_request("2FA Password", "Enter your password:", is_password=True)

        await self.client.start(
            phone=phone_callback,
            code_callback=code_callback,
            password=password_callback
        )
        
        print("✅ Connected successfully!")
        
        self.client.add_event_handler(self.handle_incoming_message, events.NewMessage(incoming=True))
        await self.client.run_until_disconnected()

    async def send_ghost_message(self, username, secret_text):
        try:
            db = SessionLocal()
            contact = db.query(Contact).filter(Contact.username == username).first()
            
            if not contact:
                print(f"❌ Error: Contact {username} not found.")
                db.close()
                return

            shared_key = contact.shared_key
            db.close()

            # التشفير (تأكدنا من core/crypto.py الخاص بك وهو سليم)
            encrypted_data = self.crypto.encrypt(secret_text, shared_key)
            
            context = ["مرحبا", "كيف الحال", "السلام عليكم"] 
            cover_text = self.stego.hide_data(encrypted_data, context)

            await self.client.send_message(username, cover_text)
            print(f"📤 Sent hidden message to @{username}")
            
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
            if not contact:
                db.close(); return

            shared_key = contact.shared_key
            db.close()

            encrypted_payload = self.stego.reveal_data(event.raw_text)
            if encrypted_payload:
                decrypted_text = self.crypto.decrypt(encrypted_payload, shared_key)
                if decrypted_text:
                    print(f"📩 Message from @{username}: {decrypted_text}")
                    save_message(contact.id, decrypted_text, is_sent_by_me=False)
                    if self.on_message_received:
                        self.on_message_received(username, decrypted_text)
        except Exception as e:
            print(f"⚠️ Incoming Handler Error: {e}")