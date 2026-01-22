import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: API Key not found in .env")
else:
    genai.configure(api_key=api_key)
    print("🔍 Searching for available models for your API Key...\n")
    try:
        found = False
        for m in genai.list_models():
            # نبحث فقط عن الموديلات التي تدعم توليد النصوص
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ Available: {m.name}")
                found = True
        
        if not found:
            print("⚠️ No content generation models found. Check your API Key permissions.")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")