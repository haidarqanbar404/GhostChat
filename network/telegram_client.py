import os
import asyncio
from telethon import TelegramClient, events, sync
from dotenv import load_dotenv

from core.crypto import CryptoEngine
from core.steganography import SteganographyEngine
from core.ai_camouflage import AICamouflage
from database.models import SessionLocal, Contact, DecryptedMessage

load_dotenv()

class GhostNetwork:
    def __init__(self, on_message_received=None):
        self.api_id = os.getenv("TG_API_ID")
        self.api_hash = os.getenv("TG_API_HASH")
        
        if not self.api_id or not self.api_hash:
            print("There are No Telegram API Keys in .env")
        self.client = TelegramClient('ghost_session', self.api_id, self.api_hash)
        self.ai = AICamouflage()
        self.on_message_received = on_message_received
        
        self.client.add_event_handler(self.incoming_message_handler, events.NewMessage(incoming=True))
        

    async def start(self):
        print("Connecting to Telegram...")
        await self.client.start()
        print("Connected! Waiting for messages...")
        await self.client.run_until_disconnected()

    async def send_ghost_message(self, username: str, real_text: str):
        db = SessionLocal()
        try:
            contact = db.query(Contact).filter(Contact.username == username).first()
            
            if not contact:
                print(f"Error: Contact {username} not found in DB. Add them first!")
                return

            crypto = CryptoEngine(contact.shared_key)
            encrypted_bytes = crypto.encrypt(real_text)
            hidden_payload = SteganographyEngine.bytes_to_invisible(encrypted_bytes)
            cover_text = self.ai.generate_cover_text(context_history=[])
            final_message = cover_text + hidden_payload
            
            sent_msg = await self.client.send_message(username, final_message)
            
            new_record = DecryptedMessage(
                telegram_message_id=sent_msg.id,
                contact_id=contact.id,
                real_content=real_text,
                is_sent_by_me=True
            )
            db.add(new_record)
            db.commit()
            
            print(f"Sent to {username}: [Cover: {cover_text}] [Hidden: {real_text}]")

        except Exception as e:
            print(f"Failed to send: {e}")
        finally:
            db.close()

    async def incoming_message_handler(self, event):
        if not SteganographyEngine.contains_hidden_msg(event.raw_text):
            return 
        
        if self.on_message_received:
            self.on_message_received(sender_username, decrypted_text)

        sender = await event.get_sender()
        sender_username = sender.username
        
        print(f"\nDetected Ghost Message from @{sender_username}!")

        db = SessionLocal()
        try:
            contact = db.query(Contact).filter(Contact.username == sender_username).first()
            
            if not contact:
                print(f"Message from unknown contact {sender_username}. Cannot decrypt.")
                return

            crypto = CryptoEngine(contact.shared_key)
            
            hidden_bytes = SteganographyEngine.invisible_to_bytes(event.raw_text)
            
            decrypted_text = crypto.decrypt(hidden_bytes)
            
            print(f"DECRYPTED: {decrypted_text}")
            
            new_record = DecryptedMessage(
                telegram_message_id=event.id,
                contact_id=contact.id,
                real_content=decrypted_text,
                is_sent_by_me=False
            )
            db.add(new_record)
            db.commit()

        except Exception as e:
            print(f"Error processing incoming message: {e}")
        finally:
            db.close()