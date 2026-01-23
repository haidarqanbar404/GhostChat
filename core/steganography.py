import random

class SteganographyEngine:
    def __init__(self):
        self.ZERO = '\u200b' # Zero Width Space
        self.ONE = '\u200c'  # Zero Width Non-Joiner

    def text_to_binary(self, text):
        return ''.join(format(ord(char), '08b') for char in text)

    def binary_to_text(self, binary):
        chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
        return ''.join(chr(int(char, 2)) for char in chars)

    def hide_data(self, secret_text, context_list=None):
        binary_secret = self.text_to_binary(secret_text)
        zwc_secret = ''.join(self.ONE if bit == '1' else self.ZERO for bit in binary_secret)
        
        if context_list and isinstance(context_list, list) and len(context_list) > 0:
            cover = random.choice(context_list)
        else:
            cover = "اهلين" 
            
        if len(cover) > 1:
            return cover[0] + zwc_secret + cover[1:]
        else:
            return cover + zwc_secret

    def reveal_data(self, cover_text):
        binary_extracted = ''
        for char in cover_text:
            if char == self.ZERO:
                binary_extracted += '0'
            elif char == self.ONE:
                binary_extracted += '1'
        
        if not binary_extracted:
            return None
            
        if len(binary_extracted) % 8 != 0:
            return None
            
        try:
            return self.binary_to_text(binary_extracted)
        except:
            return None