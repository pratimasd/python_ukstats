import os
import json
from flask import Flask, request, jsonify

# Configure Flask
app = Flask(__name__)

# Load API key - handle dotenv errors gracefully
api_key = None
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"Loaded API key from .env file: {api_key[:5]}...")
except Exception as e:
    print(f"Error loading .env: {str(e)}")
    # Try to get API key directly from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"Found API key in environment variables: {api_key[:5]}...")

# Check if API key is available
if not api_key:
    print("Warning: No API key found. Please set GOOGLE_API_KEY in .env file or environment variables.")
    # For testing only - you should remove this in production
    api_key = "AIzaSyDBGZDFuX4QyBFuyucgZROViXJvOBnCdgY"
    print("Using hardcoded API key for testing")

# Initialize Gemini API
try:
    from gemini_api import GeminiAPI
    gemini_api = GeminiAPI(api_key=api_key)
    print("Gemini API initialized successfully")
except Exception as e:
    print(f"Failed to initialize Gemini API: {str(e)}")
    raise

# Store chat sessions
chat_sessions = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    client_id = data.get('client_id', 'anonymous')
    message = data.get('message')
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    # Create a new chat session if one doesn't exist
    if client_id not in chat_sessions:
        chat_sessions[client_id] = gemini_api.chat_session()
        print(f"Created new chat session for client {client_id}")
    
    try:
        # Get response from Gemini
        print(f"Processing message from {client_id}: {message[:30]}...")
        response = chat_sessions[client_id].send_message(message)
        response_text = response.text
        
        print(f"Got response from Gemini for client {client_id}")
        
        return jsonify({
            "response": response_text,
            "client_id": client_id
        })
    
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """Index route"""
    return "Gemini API Server is running"

if __name__ == '__main__':
    port = 5000
    print(f"Starting API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 