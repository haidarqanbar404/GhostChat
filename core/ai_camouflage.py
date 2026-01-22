import ollama
import random
import os
from dotenv import load_dotenv

load_dotenv()

class AICamouflage:
    def __init__(self):
        self.model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
        
        # --- القائمة الذهبية للجمل السورية (Database) ---
        # هذه الجمل مضمونة 100% ولن يخطئ فيها الموديل
        self.responses = {
            "greeting": [
                "اهلين يا غالي", "هلا والله", "يا مية هلا", 
                "اهلين، نورت", "هلا شريك", "مراحب"
            ],
            "status": [
                "تمام الحمدلله", "ماشية الامور", "نشكر الله", 
                "بخير، انت كيفك؟", "رواق", "صافية وافية"
            ],
            "location": [
                "بالبيت قاعد", "بالشغل", "طالع مشوار", 
                "بالطريق", "عند الشباب", "عم اتمشى"
            ],
            "busy": [
                "مشغول شوي", "بحاكيك بعدين", "معجوق والله", 
                "اي شوي تانية", "عم اشتغل"
            ],
            "agreement": [
                "اي اكيد", "تم يا معلم", "على راسي", 
                "ولا يهمك", "توكل ع الله", "اي صاير"
            ],
            "closing": [
                "يلا سلام", "بشوفك", "باي", 
                "تصبح ع خير", "الله معك"
            ],
            "unknown": [
                "شو القصة؟", "اي تمام", "حلو", 
                "اي سيدي", "وبعدين؟", "شو الاخبار؟"
            ]
        }

    def generate_cover_text(self, context_history: list[str]) -> str:
        """
        نظام 'المصنف الذكي': الموديل يفهم المعنى، والبايثون يختار الرد.
        """
        try:
            last_msg = context_history[-1] if context_history else "مرحبا"
            
            # 1. نطلب من الموديل تصنيف الرسالة فقط (مهمة سهلة جداً عليه)
            prompt = f"""
            Classify the following message into one category.
            Message: "{last_msg}"
            
            Categories:
            - greeting (if saying hi/hello)
            - status (if asking how are you)
            - location (if asking where are you)
            - busy (if asking are you busy/what doing)
            - closing (if saying bye)
            - other (anything else)

            Reply with ONE word only (the category name).
            """
            
            response = ollama.generate(
                model=self.model_name, 
                prompt=prompt,
                options={"temperature": 0.1} # حرارة منخفضة جداً للدقة
            )
            
            category = response['response'].strip().lower()
            
            # تنظيف رد الموديل
            for key in self.responses.keys():
                if key in category:
                    category = key
                    break
            else:
                category = "unknown"

            # 2. نختار جملة عشوائية من الفئة الصحيحة
            reply = random.choice(self.responses.get(category, self.responses["unknown"]))
            
            print(f"🧠 AI Logic: Detected '{category}' -> Reply: '{reply}'")
            return reply

        except Exception as e:
            print(f"⚠️ AI Error: {e}")
            return random.choice(self.responses["unknown"])