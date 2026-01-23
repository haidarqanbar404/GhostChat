import json
import urllib.request
import random

class AIEngine:
    def __init__(self, model="qwen2.5:0.5b"):
        self.model = model
        self.api_url = "http://localhost:11434/api/generate"
        
        # قائمة ردود جاهزة وسريعة جداً (لحل مشكلة البطء والركاكة)
        self.quick_replies = [
            "هلا والله، كيفك اليوم؟",
            "إي تمام، وأنت شو أخبارك؟",
            "والله ماشي الحال، عم ندفش بهالحياة.",
            "يا زلمة وين هالغيبة؟",
            "شو رأيك نطلع شي مشوار؟",
            "هههههه إي والله معك حق.",
            "روق وهدي البال، كله بيتحلل.",
            "صباحو يا غالي.",
            "تمام، خبرني شو بيصير معك."
        ]

    def generate_cover_text(self, context_history=None):
        """
        يحاول استخدام الذكاء الاصطناعي، وإذا تأخر أو فشل يستخدم رداً جاهزاً.
        """
        # 1. نسبة 50% نستخدم رداً جاهزاً لزيادة السرعة وضمان اللهجة
        if random.random() < 0.5 or not context_history:
            print("⚡ Using Quick Reply (Speed Mode)")
            return random.choice(self.quick_replies)

        # 2. إذا قررنا استخدام AI، نستخدم برومبت بسيط جداً
        chat_context = "\n".join(context_history[-2:]) # نأخذ آخر رسالتين فقط للتخفيف

        system_prompt = f"""
        Conversation:
        {chat_context}
        
        Task: You are a Syrian guy from Damascus. Reply to the last message in Syrian dialect (Shami).
        Constraint: Keep it very short (max 5 words). Do not translate. Arabic only.
        
        Reply:
        """

        payload = {
            "model": self.model,
            "prompt": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.5, 
                "num_predict": 15,   # تقليل عدد الكلمات لزيادة السرعة
                "top_k": 20
            }
        }

        try:
            # Timeout سريع (3 ثواني) إذا تأخر الـ AI ننتقل للرد الجاهز فوراً
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(self.api_url, data=data, headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req, timeout=3) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result.get("response", "").strip()
                
                # تنظيف النص
                clean_text = text.replace('"', '').replace("'", "").split('\n')[0]
                
                # إذا كان الرد فارغاً أو إنجليزياً، نستخدم الجاهز
                if not clean_text or len(clean_text) < 2:
                    return random.choice(self.quick_replies)
                    
                return clean_text

        except Exception as e:
            print(f"⚠️ AI Timeout/Error: {e} -> Switching to fallback.")
            return random.choice(self.quick_replies)