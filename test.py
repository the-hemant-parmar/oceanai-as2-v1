import google.generativeai as genai
import os

# Replace with your actual API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# List all available models
for m in genai.list_models():
    print(f"Model Name: {m.name}, Supported Methods: {m.supported_generation_methods}")

# You can also check for specific models or capabilities
# For example, to check if a model supports text generation:
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"{m.name} supports text generation.")