import random

class SteganographyEngine:
    def __init__(self):
        # نستخدم أحرف "صفرية العرض" (غير مرئية) لتمثيل البتات 0 و 1
        self.ZERO = '\u200b' # Zero Width Space
        self.ONE = '\u200c'  # Zero Width Non-Joiner

    def text_to_binary(self, text):
        """تحويل النص إلى سلسلة من البتات 0101"""
        return ''.join(format(ord(char), '08b') for char in text)

    def binary_to_text(self, binary):
        """تحويل البتات 0101 مرة أخرى إلى نص"""
        chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
        return ''.join(chr(int(char, 2)) for char in chars)

    def hide_data(self, secret_text, context_list=None):
        """إخفاء النص السري داخل نص غطاء (Cover Text)"""
        # 1. تحويل السر إلى ثنائي
        binary_secret = self.text_to_binary(secret_text)
        
        # 2. تحويل الثنائي إلى أحرف غير مرئية
        zwc_secret = ''.join(self.ONE if bit == '1' else self.ZERO for bit in binary_secret)
        
        # 3. اختيار نص غطاء عشوائي
        if context_list and isinstance(context_list, list) and len(context_list) > 0:
            cover = random.choice(context_list)
        else:
            cover = "Hello" # نص افتراضي في حال عدم وجود سياق
            
        # 4. دمج السر (في المنتصف لزيادة التمويه)
        if len(cover) > 1:
            position = 1 # بعد الحرف الأول
            return cover[:position] + zwc_secret + cover[position:]
        else:
            return cover + zwc_secret

    def reveal_data(self, cover_text):
        """استخراج النص السري من النص الغطاء"""
        # استخراج الأحرف غير المرئية فقط
        binary_extracted = ''
        for char in cover_text:
            if char == self.ZERO:
                binary_extracted += '0'
            elif char == self.ONE:
                binary_extracted += '1'
        
        if not binary_extracted:
            return None
            
        # التأكد من أن الطول يقبل القسمة على 8 (بايت كامل)
        if len(binary_extracted) % 8 != 0:
            return None
            
        try:
            return self.binary_to_text(binary_extracted)
        except:
            return None