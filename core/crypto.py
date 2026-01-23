from cryptography.fernet import Fernet
import base64
import os

class CryptoEngine:
    def __init__(self):
        pass

    @staticmethod
    def generate_key() -> str:
        """توليد مفتاح جديد وإرجاعه كنص"""
        key = Fernet.generate_key()
        return key.decode()

    def encrypt(self, message: str, key: str) -> str:
        """تشفير الرسالة باستخدام مفتاح محدد"""
        try:
            f = Fernet(key.encode())
            encrypted_bytes = f.encrypt(message.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            print(f"Encryption Error: {e}")
            return ""

    def decrypt(self, encrypted_token: str, key: str) -> str:
        """فك تشفير الرسالة باستخدام مفتاح محدد"""
        try:
            f = Fernet(key.encode())
            decrypted_bytes = f.decrypt(encrypted_token.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            # print(f"Decryption Error: {e}") 
            return None