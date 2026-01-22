from sqlalchemy import create_engine, String, Integer, Boolean, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, echo=False) 
SessionLocal = sessionmaker(bind=engine)

if not DB_URL:
    raise ValueError("CRITICAL ERROR: DATABASE_URL not found in .env file!")

class Base(DeclarativeBase):
    pass

class Contact(Base):

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False) 
    username: Mapped[str] = mapped_column(String(50), nullable=True)
    
    shared_key: Mapped[str] = mapped_column(String, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    messages: Mapped[list["DecryptedMessage"]] = relationship(back_populates="contact", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Contact(name={self.username}, id={self.telegram_id})>"

class DecryptedMessage(Base):

    __tablename__ = "decrypted_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    telegram_message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    contact: Mapped["Contact"] = relationship(back_populates="messages")
    
    real_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    is_sent_by_me: Mapped[bool] = mapped_column(Boolean, default=False)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        sender = "Me" if self.is_sent_by_me else "Friend"
        return f"<{sender}: {self.real_content[:20]}...>"

def init_db():
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()