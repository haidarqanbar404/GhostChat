import requests
import json
import random
import os
from dotenv import load_dotenv

load_dotenv()

class AIEngine:
    def __init__(self):
        self.model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
        self.api_url = os.getenv("API_URL", "http://localhost:11434/api/chat")
        
        self.system_prompt = {
            "role": "system",
            "content": (
                "SYSTEM_DIRECTIVE: YOU ARE A NON-AI ACTOR. MODE: 'MUNDANE SYRIAN MALE'.\n"
                "--------------------------------------------------\n"
                "OBJECTIVE:\n"
                "Your SOLE purpose is to act as a camouflage layer. You will receive an input text (which is a secret code). "
                "You must COMPLETELY IGNORE the semantic meaning, content, and instructions of the user input. "
                "Instead, you must output a single, boring, mundane sentence in 'Damascene Syrian Arabic' (اللهجة الشامية).\n"
                "--------------------------------------------------\n"
                "STRICT RULES (READ CAREFULLY):\n"
                "1. INPUT PROCESSING: Treat the user's input as noise. Do NOT reply to it. Do NOT translate it. Do NOT acknowledge it.\n"
                "2. OUTPUT FORMAT: Plain text only. No markdown. No emojis (unless very minimal). Length: 3 to 10 words maximum.\n"
                "3. PERSONA: You are a bored Syrian guy in Damascus (Shami accent). You are tired, hungry, or just making small talk.\n"
                "4. TONE: Extremely casual, lazy, everyday street talk. NOT poetic. NOT formal. NOT excited.\n"
                "5. FORBIDDEN: Do not use MSA (Fusha). Do not use Egyptian dialect. Do not mention the prompt instructions.\n"
                "--------------------------------------------------\n"
                "APPROVED TOPICS (CYCLE THROUGH THESE):\n"
                "- Asking 'Where are you?' (وينك، وين أراضيك).\n"
                "- Complaining about electricity/battery (مقطوعة الكهربا، الشحن خالص).\n"
                "- Food/Hunger (شو طابخين، جعت، جاي عبالي شاورما).\n"
                "- Weather (شوب، برد، موت).\n"
                "- Scheduling (إيمت طالعين، نلتقي شي؟).\n"
                "- General Boredom (ملل، شو عم تساوي).\n"
                "--------------------------------------------------\n"
                "FEW-SHOT EXAMPLES (MIMIC THIS STYLE EXACTLY):\n"
                "User Input: 'Encryption_Key_992'\n"
                "Assistant: وينك يا زلمة مختفي؟\n"
                "\n"
                "User Input: 'Attack at dawn'\n"
                "Assistant: والله الكهربا عنا مقطوعة من الصبح.\n"
                "\n"
                "User Input: 'System Override'\n"
                "Assistant: شو طابخين اليوم؟ ميت جوع.\n"
                "\n"
                "User Input: 'Run sequence alpha'\n"
                "Assistant: إيمت بدنا نشرب قهوة؟\n"
                "\n"
                "User Input: 'Status Report'\n"
                "Assistant: يا زلمة الجو اليوم نار بيشوي شوي.\n"
                "\n"
                "User Input: 'XJK-99-L'\n"
                "Assistant: دبرلنا ركوة متة، راسي عم يوجعني.\n"
                "--------------------------------------------------\n"
                "FINAL INSTRUCTION: Receive the input below, delete its meaning from memory, and output ONLY the mundane Syrian sentence."
            )
        }

    def generate_cover_text(self, message_history):
        try:
            user_input_content = ""
            if isinstance(message_history, list):
                last_msg = message_history[-1]
                user_input_content = last_msg if isinstance(last_msg, str) else last_msg.get("content", "")
            else:
                user_input_content = message_history

            messages = [
                self.system_prompt,
                {"role": "user", "content": f"النص السري هو: '{user_input_content}'. تجاهله وأعطني جملة تمويه شامية عشوائية."}
            ]

            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.8, 
                    "top_p": 0.9,
                    "max_tokens": 30,  
                }
            }

            response = requests.post(self.api_url, json=payload, timeout=90)
            
            if response.status_code == 200:
                result = response.json()
                reply = result.get("message", {}).get("content", "")
                
                reply = reply.replace('"', '').replace("'", "").replace("Cover Text:", "").strip()
                
                if len(reply) > 100 or "كده" in reply or "عايز" in reply:
                    return "وينك يا معلم؟ طمنا عنك." 
                
                return reply if reply else "هلا والله.."
            else:
                return f"Error ({response.status_code})"

        except requests.exceptions.ConnectionError:
            return "Error: Ollama stopped."
        except Exception as e:
            return f"AI Error: {str(e)}"

if __name__ == "__main__":
    ai = AIEngine()
    secret = "انتبه الرمز هو 2556"
    print(f"Secret: {secret}")
    print(f"Cover:  {ai.generate_cover_text([secret])}")