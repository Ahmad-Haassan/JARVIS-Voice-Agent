import google.generativeai as genai
import json
import os

try:
    with open('config.json') as f:
        config = json.load(f)
    
    api_key = config['ai']['gemini_api_key']
    if not api_key:
        print("No API key found.")
    else:
        genai.configure(api_key=api_key)
        print("Available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
