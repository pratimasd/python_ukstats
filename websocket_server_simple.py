import asyncio
import json
import logging
import os
import traceback
import websockets
from gemini_api import GeminiAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store active connections and chat sessions
active_connections = {}
chat_sessions = {}

# Initialize Gemini API
try:
    # Try to get API key from environment
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # Try from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("GOOGLE_API_KEY")
            if api_key:
                logger.info(f"Loaded API key from .env file: {api_key[:5]}...")
            else:
                logger.warning("No API key found in .env file. Using hardcoded key.")
                api_key = "AIzaSyDBGZDFuX4QyBFuyucgZROViXJvOBnCdgY"
        except Exception as e:
            logger.error(f"Error loading .env: {str(e)}")
            api_key = "AIzaSyDBGZDFuX4QyBFuyucgZROViXJvOBnCdgY"
    
    # Initialize the API
    gemini_api = GeminiAPI(api_key=api_key)
    logger.info("Gemini API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API: {str(e)}")
    raise

async def handle_client(websocket, path):
    """Handle websocket connection for each client"""
    # Extract client ID from the path or generate one
    client_id = path.strip("/")
    if not client_id:
        client_id = f"client-{len(active_connections) + 1}"
    
    logger.info(f"New connection from client: {client_id}")
    
    try:
        # Store the connection
        active_connections[client_id] = websocket
        logger.info(f"✅ CLIENT REGISTERED: {client_id} (Total active: {len(active_connections)})")
        
        # Create a chat session for this client
        chat_sessions[client_id] = gemini_api.chat_session()
        logger.info(f"Created chat session for client {client_id}")
        
        # Send welcome message
        welcome_msg = {
            "type": "connected",
            "content": "Connected to Gemini WebSocket Server"
        }
        await websocket.send(json.dumps(welcome_msg))
        logger.info(f"✅ WELCOME MESSAGE SENT: {client_id}")
        
        # Process messages from the client
        async for message in websocket:
            try:
                # Parse the message
                data = json.loads(message)
                logger.info(f"Received message from {client_id}: {data}")
                
                if data.get("type") == "message":
                    content = data.get("content", "")
                    
                    # Send acknowledgment
                    await websocket.send(json.dumps({
                        "type": "status",
                        "content": "Processing your request..."
                    }))
                    logger.info(f"✅ PROCESSING: {client_id} - Message: {content[:30]}...")
                    
                    # Process with Gemini
                    logger.info(f"Processing message: {content[:30]}...")
                    response = chat_sessions[client_id].send_message(content)
                    response_text = response.text
                    
                    # Send response back
                    await websocket.send(json.dumps({
                        "type": "response",
                        "content": response_text
                    }))
                    logger.info(f"✅ RESPONSE SENT: {client_id} - Length: {len(response_text)} chars")
                
                elif data.get("type") == "ping":
                    # Respond to ping
                    await websocket.send(json.dumps({
                        "type": "pong"
                    }))
                    logger.info(f"✅ PING-PONG: {client_id}")
            
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "content": "Invalid message format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "error", 
                    "content": f"Error processing your request: {str(e)}"
                }))
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed for client {client_id}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {str(e)}\n{traceback.format_exc()}")
    
    finally:
        # Clean up
        if client_id in active_connections:
            del active_connections[client_id]
        if client_id in chat_sessions:
            del chat_sessions[client_id]
        logger.info(f"❌ CLIENT DISCONNECTED: {client_id} (Total active: {len(active_connections)})")

async def main():
    # Start websocket server
    host = "127.0.0.1"
    port = 8765
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    async with websockets.serve(handle_client, host, port):
        logger.info(f"✅ SERVER RUNNING: ws://{host}:{port} - Ready to accept connections")
        # Keep the server running
        await asyncio.Future()

if __name__ == "__main__":
    try:
        # Start the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Server stopped by user")
    except Exception as e:
        logger.error(f"⚠️ Server error: {str(e)}")
        traceback.print_exc() 