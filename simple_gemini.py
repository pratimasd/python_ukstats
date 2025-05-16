import google.generativeai as genai

# Set your API key directly
API_KEY = "AIzaSyDBGZDFuX4QyBFuyucgZROViXJvOBnCdgY"  # Your API key

# Configure the Gemini API
genai.configure(api_key=API_KEY)

def main():
    # Initialize the model - using Gemini 1.5 Flash which is available
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("=" * 50)
    print("Welcome to Simple Gemini Console")
    print("Type 'exit' to end the session")
    print("=" * 50)
    
    # Main interaction loop
    while True:
        # Get user input
        print()
        prompt = input("Your prompt > ")
        
        # Check for exit command
        if prompt.lower() in ["exit", "quit", "bye"]:
            print("Ending session. Goodbye!")
            break
        
        try:
            # Get response from Gemini
            print("Thinking...")
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Display the response
            print("\n=== GEMINI RESPONSE ===")
            print(response_text)
            print("======================")
            
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main() 