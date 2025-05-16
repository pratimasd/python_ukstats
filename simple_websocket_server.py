import os
import json
import asyncio
import logging
import websockets
import traceback
from dotenv import load_dotenv
from gemini_api import GeminiAPI

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Gemini API
try:
    gemini_api = GeminiAPI()
    logger.info("Gemini API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API: {str(e)}")
    raise

# Store active connections and chat sessions
active_connections = {}
chat_sessions = {}

async def handle_websocket(websocket, path):
    """Handle a WebSocket connection."""
    # Extract client ID from path (e.g., /ws/client123)
    client_id = path.strip("/")
    if not client_id:
        client_id = "anonymous"
    
    logger.info(f"New connection from client: {client_id}")
    
    # Store connection
    active_connections[client_id] = websocket
    
    # Create a new chat session for this client
    try:
        chat_sessions[client_id] = gemini_api.chat_session()
        logger.info(f"Created chat session for client {client_id}")
    except Exception as e:
        logger.error(f"Failed to create chat session for client {client_id}: {str(e)}")
        # Send error to client
        await websocket.send(json.dumps({
            "type": "error",
            "content": f"Failed to create chat session: {str(e)}"
        }))
        return
    
    try:
        # Send welcome message
        logger.info(f"Sending welcome message to client {client_id}")
        await websocket.send(json.dumps({
            "type": "connected",
            "content": "Connected to Gemini WebSocket Server"
        }))
        
        # Keep the connection open with periodic pings
        ping_task = asyncio.create_task(periodic_ping(websocket, client_id))
        
        # Process messages
        async for message in websocket:
            try:
                # Parse the message
                logger.debug(f"Received raw message from client {client_id}: {message}")
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                # Handle different message types
                if data.get("type") == "message":
                    user_message = data.get("content", "")
                    
                    # Send acknowledgment
                    await websocket.send(json.dumps({
                        "type": "status",
                        "content": "processing"
                    }))
                    
                    # Process the message
                    logger.info(f"Processing message from {client_id}: {user_message[:30]}...")
                    
                    try:
                        # Get response from Gemini
                        response = chat_sessions[client_id].send_message(user_message)
                        response_text = response.text
                        
                        logger.info(f"Got response from Gemini for client {client_id}")
                        
                        # Send the response
                        await websocket.send(json.dumps({
                            "type": "response",
                            "content": response_text
                        }))
                        logger.info(f"Sent response to client {client_id}")
                        
                    except Exception as e:
                        error_msg = f"Error processing message: {str(e)}"
                        logger.error(f"{error_msg}\n{traceback.format_exc()}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "content": error_msg
                        }))
                
                elif data.get("type") == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))
                    logger.debug(f"Received ping from client {client_id}, sent pong")
            
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "content": "Invalid JSON message"
                }))
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {str(e)}\n{traceback.format_exc()}")
                try:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "content": f"Server error: {str(e)}"
                    }))
                except:
                    pass
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed for client {client_id}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in WebSocket handler for client {client_id}: {str(e)}\n{traceback.format_exc()}")
    
    finally:
        # Cancel ping task
        try:
            ping_task.cancel()
        except:
            pass
        
        # Clean up when connection closes
        if client_id in active_connections:
            del active_connections[client_id]
        if client_id in chat_sessions:
            del chat_sessions[client_id]
        logger.info(f"Connection closed and cleaned up for client {client_id}")

async def periodic_ping(websocket, client_id):
    """Send periodic pings to keep the connection alive"""
    try:
        while True:
            await asyncio.sleep(30)  # Send ping every 30 seconds
            if client_id in active_connections:
                try:
                    await websocket.send(json.dumps({"type": "ping"}))
                    logger.debug(f"Sent ping to client {client_id}")
                except:
                    logger.warning(f"Failed to send ping to client {client_id}")
                    break
            else:
                break
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error in periodic ping for client {client_id}: {str(e)}")

async def main():
    """Start the WebSocket server."""
    host = "127.0.0.1"
    port = 8765
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    async with websockets.serve(handle_websocket, host, port):
        logger.info(f"Server started. Listening on {host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}\n{traceback.format_exc()}") 