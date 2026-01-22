import asyncio
import sys
from network.telegram_client import GhostNetwork
from database.models import init_db, SessionLocal, Contact
from core.crypto import CryptoEngine

init_db()

async def interactive_mode(ghost):
    """واجهة تفاعلية بسيطة"""
    print("\n--- GhostChat Interactive Mode --- ")
    print("1. Add a new Contact (Setup Keys)")
    print("2. Send a Secret Message")
    print("3. Start Listening (Receive Mode)")
    print("4. Exit")
    
    while True:
        choice = input("\n Select option: ")
        
        if choice == '1':
            username = input("Enter Telegram Username (without @): ")
            key = CryptoEngine.generate_key()
            
            db = SessionLocal()
            existing = db.query(Contact).filter(Contact.username == username).first()
            if existing:
                print(f"Contact {username} already exists!")
            else:
                fake_id = 12345 
                
                new_contact = Contact(telegram_id=fake_id, username=username, shared_key=key)
                db.add(new_contact)
                db.commit()
                print(f"Added {username}.")
                print(f" SHARE THIS KEY WITH THEM SECURELY: {key}")
            db.close()

        elif choice == '2':
            username = input("To (Username): ")
            msg = input("Secret Message: ")
            print("⏳ Sending...")
            # إرسال الرسالة باستخدام عميل الشبكة
            await ghost.send_ghost_message(username, msg)

        elif choice == '3':
            print("Listening for incoming messages... (Press Ctrl+C to stop)")
            await ghost.start()

        elif choice == '4':
            print("Bye!")
            sys.exit()

if __name__ == "__main__":
    ghost = GhostNetwork()
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(interactive_mode(ghost))