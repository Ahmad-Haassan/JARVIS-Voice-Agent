import google.generativeai as genai
import sys
import os

# Add parent dir to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.utils import config as cfg

def list_gemini_models():
    api_key = cfg.get("ai", "gemini_api_key")
    if not api_key:
        print("No Gemini API key found.")
        return

    print(f"Checking models for key: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"SUPPORTED: {m.name}")
    except Exception as e:
        print(f"FAILED to list models: {e}")

if __name__ == "__main__":
    list_gemini_models()
