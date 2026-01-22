from cryptography.fernet import Fernet
import zlib
import base64

class CryptoEngine:
    def __init__(self, key: str):
        try:
            self.fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise ValueError(f"Invalid Key: {e}")

    @staticmethod
    def generate_key() -> str:
        return Fernet.generate_key().decode()

    def encrypt(self, plain_text: str) -> bytes:
        data = plain_text.encode('utf-8')
        compressed_data = zlib.compress(data, level=9)
        encrypted_token = self.fernet.encrypt(compressed_data)
        return encrypted_token

    def decrypt(self, encrypted_token: bytes) -> str:

        try:
            decrypted_compressed = self.fernet.decrypt(encrypted_token)
            decompressed_data = zlib.decompress(decrypted_compressed)
            return decompressed_data.decode('utf-8')
        except Exception as e:
            raise ValueError("Decryption failed. Data might be corrupted or key is wrong.") from e

if __name__ == "__main__":
    my_key = CryptoEngine.generate_key()
    print(f"Generated Key: {my_key}")
    
    engine = CryptoEngine(my_key)
    
    original_msg = "اذهب إلى المقهى القديم عند الساعة الخامسة."
    print(f"Original: {original_msg}")
    
    enc = engine.encrypt(original_msg)
    print(f"Encrypted (Bytes): {len(enc)} bytes -> {enc[:20]}...")
    
    dec = engine.decrypt(enc)
    print(f"Decrypted: {dec}")
    
    assert original_msg == dec
    print("✅ Test Passed")