from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import sys
import threading
db_lock = threading.Lock()

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "ghost_chat.db")


engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, nullable=True)
    username = Column(String, unique=True, index=True)
    shared_key = Column(String)

class DecryptedMessage(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    telegram_message_id = Column(Integer, unique=True, nullable=True)
    real_content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    is_sent_by_me = Column(Boolean, default=False)


def init_db():
    Base.metadata.create_all(bind=engine)

def save_message(contact_id, text, is_sent_by_me, telegram_id=None):
    with db_lock:
        db = SessionLocal()
        try:
            if telegram_id:
                exists = db.query(DecryptedMessage).filter(DecryptedMessage.telegram_message_id == telegram_id).first()
                if exists:
                    return 

            msg = DecryptedMessage(
                contact_id=contact_id,
                real_content=text,
                is_sent_by_me=is_sent_by_me,
                timestamp=datetime.now(),
                telegram_message_id=telegram_id 
            )
            db.add(msg)
            db.commit()
        except Exception as e:
            print(f"Database Error: {e}")
            db.rollback()
        finally:
            db.close()