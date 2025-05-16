import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiAPI:
    def __init__(self, api_key=None):
        """
        Initialize the Gemini API client.
        
        Args:
            api_key: Optional API key. If not provided, will look for GOOGLE_API_KEY in environment.
        """
        # Load from environment if not provided
        if not api_key:
            load_dotenv()
            api_key = os.getenv("GOOGLE_API_KEY")
            
        if not api_key:
            raise ValueError("No API key provided. Set GOOGLE_API_KEY in .env file or pass as parameter.")
            
        # Configure the API
        genai.configure(api_key=api_key)
        
        # List available models
        available_models = []
        try:
            models = genai.list_models()
            print("Available models:")
            for model in models:
                model_name = model.name
                available_models.append(model_name)
                print(f"- {model_name}")
        except Exception as e:
            print(f"Error listing models: {str(e)}")
        
        # Initialize models with fallbacks - USING FLASH MODEL INSTEAD OF PRO FOR HIGHER QUOTAS
        if 'models/gemini-1.5-flash' in available_models:
            self.text_model = genai.GenerativeModel('gemini-1.5-flash')
        elif 'models/gemini-1.5-pro' in available_models:
            self.text_model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            print("Falling back to gemini-pro model")
            self.text_model = genai.GenerativeModel('gemini-pro')
            
        if 'models/gemini-1.5-pro-vision' in available_models:
            self.vision_model = genai.GenerativeModel('gemini-1.5-pro-vision')
        else:
            print("Falling back to gemini-pro-vision model")
            self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        
    def generate_text(self, prompt):
        """
        Generate text from a prompt.
        
        Args:
            prompt: Text prompt for generation
            
        Returns:
            Generated text response
        """
        try:
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Error generating text: {str(e)}")
    
    def generate_with_image(self, prompt, image_data):
        """
        Generate text from a prompt and image.
        
        Args:
            prompt: Text prompt for generation
            image_data: Image data (either file path or binary data)
            
        Returns:
            Generated text response
        """
        try:
            # Create multimodal prompt with image and text
            if isinstance(image_data, str):  # If image_data is a file path
                image = genai.upload_file(image_data)
            else:  # If image_data is binary data
                image = image_data
                
            response = self.vision_model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            raise Exception(f"Error generating from image: {str(e)}")
            
    def chat_session(self):
        """
        Create and return a chat session.
        
        Returns:
            Chat session object
        """
        return self.text_model.start_chat(history=[]) 