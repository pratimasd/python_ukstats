import os
import time
import logging
import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gemini_console_logs.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gemini_console")

def setup():
    """Setup the Gemini API with the API key from .env file"""
    # Load environment variables
    load_dotenv()
    
    # Configure API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Please set your GOOGLE_API_KEY in the .env file")
        print("Create a .env file in the project root with: GOOGLE_API_KEY=your_key_here")
        return False
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    return True

def log_interaction(request_id, prompt, response=None, error=None, duration=None):
    """Log the interaction with Gemini"""
    # Log the request
    logger.info(f"REQUEST [{request_id}]: {prompt}")
    
    # Log the response or error
    if response:
        logger.info(f"RESPONSE [{request_id}] (took {duration:.2f}s): {response[:100]}...")
    if error:
        logger.error(f"ERROR [{request_id}]: {error}")

def main():
    """Main function to run the Gemini console app"""
    # Setup the API
    if not setup():
        return
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-pro')
    
    print("=" * 50)
    print("Welcome to Gemini Console Interface")
    print("Type 'exit', 'quit', or 'bye' to end the session")
    print("Type 'logs' to view recent logs")
    print("=" * 50)
    
    # Main interaction loop
    while True:
        # Get user input
        print()
        prompt = input("Your prompt > ")
        
        # Check for exit commands
        if prompt.lower() in ["exit", "quit", "bye"]:
            print("Ending session. Goodbye!")
            break
        
        # Check for logs command
        if prompt.lower() == "logs":
            try:
                # Read the last 10 log entries
                with open("gemini_console_logs.log", "r") as f:
                    logs = f.readlines()
                    print("\n=== RECENT LOGS ===")
                    for log in logs[-10:]:
                        print(log.strip())
                    print("==================")
            except Exception as e:
                print(f"Error reading logs: {str(e)}")
            continue
        
        # Generate a unique request ID
        request_id = f"req_{int(time.time())}"
        
        try:
            # Get response from Gemini
            print("Thinking...")
            start_time = time.time()
            response = model.generate_content(prompt)
            response_text = response.text
            end_time = time.time()
            duration = end_time - start_time
            
            # Log the interaction
            log_interaction(request_id, prompt, response=response_text, duration=duration)
            
            # Display the response
            print("\n=== GEMINI RESPONSE ===")
            print(response_text)
            print("======================")
            print(f"Response time: {duration:.2f} seconds")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n{error_msg}")
            log_interaction(request_id, prompt, error=error_msg)

if __name__ == "__main__":
    main() 