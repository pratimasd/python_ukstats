import google.generativeai as genai

# Set your API key directly
API_KEY = "AIzaSyDBGZDFuX4QyBFuyucgZROViXJvOBnCdgY"

# Configure the Gemini API
genai.configure(api_key=API_KEY)

try:
    # List available models
    print("Attempting to list available models...")
    for model in genai.list_models():
        print(f"Model name: {model.name}")
        print(f"Display name: {model.display_name}")
        print(f"Supported generation methods: {model.supported_generation_methods}")
        print("-" * 50)
except Exception as e:
    print(f"Error listing models: {str(e)}") 