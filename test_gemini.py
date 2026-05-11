import google.generativeai as genai
import sys
import os
import json

# Add parent dir to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.utils import config as cfg

def test_gemini():
    api_key = cfg.get("ai", "gemini_api_key")
    if not api_key:
        print("No Gemini API key found.")
        return

    print(f"Testing Gemini API Key: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    
    models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
    
    for m in models:
        try:
            print(f"Trying model: {m}")
            model = genai.GenerativeModel(m)
            response = model.generate_content("Say hello")
            print(f"SUCCESS with {m}: {response.text.strip()}")
            return m
        except Exception as e:
            print(f"FAILED with {m}: {e}")
    
    return None

if __name__ == "__main__":
    working_model = test_gemini()
    if working_model:
        print(f"\nRecommended model: {working_model}")
    else:
        print("\nAll Gemini models failed. Please check your API key or billing status.")
