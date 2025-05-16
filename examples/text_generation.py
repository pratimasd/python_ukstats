import sys
import os

# Add parent directory to path to import the GeminiAPI class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_api import GeminiAPI

def main():
    """
    Example of generating text using Gemini API.
    """
    try:
        # Initialize the API
        api = GeminiAPI()
        
        # Example prompt
        prompt = "Explain quantum computing in simple terms"
        
        print(f"Asking Gemini: {prompt}")
        print("-" * 40)
        
        # Generate response
        response = api.generate_text(prompt)
        
        print(response)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 