import sys
import os

# Add parent directory to path to import the GeminiAPI class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_api import GeminiAPI

def main():
    """
    Example of using Gemini in a chat session.
    """
    try:
        # Initialize the API
        api = GeminiAPI()
        
        # Start a chat session
        chat = api.chat_session()
        
        print("Starting chat with Gemini. Type 'exit' to quit.")
        print("-" * 40)
        
        while True:
            # Get user input
            user_input = input("You: ")
            
            # Check if user wants to exit
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Ending chat session.")
                break
                
            # Send user input to Gemini and get response
            response = chat.send_message(user_input)
            
            # Print the response
            print("\nGemini:", response.text)
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 