import os
import json
import asyncio
import logging
import websockets
import traceback
import aiohttp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the FastAPI app
app = FastAPI(title="Gemini LLM WebSocket API")

# Configure CORS to allow requests from Streamlit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log all requests and headers
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    return response

# Load API key directly
api_key = "AIzaSyAfaDvmnbsfNAqoBGBIe4muXj3LQELbT4M"  # Hardcoded API key for testing
logger.info("Using hardcoded API key for testing")

# Initialize Gemini API
try:
    from gemini_api import GeminiAPI
    gemini_api = GeminiAPI(api_key=api_key)
    logger.info("Gemini API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API: {str(e)}\n{traceback.format_exc()}")
    raise

# Track active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_sessions: Dict[str, Any] = {}
        self.http_session = None
    
    async def get_http_session(self):
        """Get or create an aiohttp session for API requests"""
        if self.http_session is None or self.http_session.closed:
            self.http_session = aiohttp.ClientSession()
        return self.http_session
    
    async def connect(self, websocket: WebSocket, client_id: str):
        logger.info(f"Connection request headers: {dict(websocket.headers)}")
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.chat_sessions[client_id] = gemini_api.chat_session()
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.chat_sessions:
            del self.chat_sessions[client_id]
    
    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            logger.debug(f"Sending to client {client_id}: {message}")
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)
    
    async def forward_api_request(self, request_data, client_id: str):
        """Forward an API request to the specified endpoint and return the response"""
        try:
            # Extract request details
            endpoint = request_data.get("endpoint")
            method = request_data.get("method", "GET")
            params = request_data.get("params", {})
            headers = request_data.get("headers", {})
            body = request_data.get("body")
            
            logger.info(f"Forwarding API request to {endpoint}")
            logger.info(f"Method: {method}")
            logger.info(f"Params: {params}")
            logger.info(f"Headers: {headers}")
            if body:
                logger.info(f"Body: {body}")
            
            # Get or create HTTP session
            session = await self.get_http_session()
            
            # Prepare request kwargs
            kwargs = {
                "params": params,
                "headers": headers
            }
            
            # Add body for POST/PUT requests
            if body and method in ["POST", "PUT", "PATCH"]:
                if isinstance(body, dict):
                    kwargs["json"] = body
                else:
                    kwargs["data"] = body
            
            # Make the request
            async with session.request(method, endpoint, **kwargs) as response:
                # Get response data
                try:
                    response_json = await response.json()
                    response_data = {
                        "type": "api_response",
                        "status": response.status,
                        "data": response_json,
                        "headers": dict(response.headers)
                    }
                except Exception as e:
                    # If not JSON, get text
                    response_text = await response.text()
                    response_data = {
                        "type": "api_response",
                        "status": response.status,
                        "data": response_text,
                        "headers": dict(response.headers)
                    }
                
                # Log and send response
                logger.info(f"API response status: {response.status}")
                logger.info(f"API response headers: {dict(response.headers)}")
                logger.debug(f"API response data: {response_data['data']}")
                
                await self.send_message(json.dumps(response_data), client_id)
                logger.info(f"Sent API response to client {client_id}")
                
        except Exception as e:
            error_msg = f"Error forwarding API request: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            await self.send_message(
                json.dumps({
                    "type": "api_response",
                    "status": 500,
                    "data": {"error": error_msg}
                }),
                client_id
            )

manager = ConnectionManager()

async def handle_websocket(websocket, path):
    """Handle a WebSocket connection."""
    # Extract client ID from path (e.g., /client123)
    client_id = path.strip("/")
    if not client_id:
        client_id = "anonymous"
    
    logger.info(f"New connection from client: {client_id}")
    logger.info(f"WebSocket headers: {getattr(websocket, 'request_headers', 'Not available')}")
    
    # Store connection
    manager.active_connections[client_id] = websocket
    
    # Create a new chat session for this client
    try:
        manager.chat_sessions[client_id] = gemini_api.chat_session()
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
        
        # Process messages
        async for message in websocket:
            try:
                # Parse the message
                logger.info(f"Received raw message from client {client_id}: {message}")
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
                    logger.info(f"Processing message from {client_id}: {user_message[:100]}...")
                    
                    try:
                        # Get response from Gemini
                        logger.info(f"Sending request to Gemini API for client {client_id}")
                        response = manager.chat_sessions[client_id].send_message(user_message)
                        response_text = response.text
                        
                        # Log full response data for debugging
                        logger.info(f"Full response object from Gemini: {response}")
                        logger.info(f"Response text from Gemini: {response_text[:200]}...")
                        
                        # Create response JSON
                        response_json = {
                            "type": "response",
                            "content": response_text
                        }
                        response_str = json.dumps(response_json)
                        logger.info(f"Formatted JSON response to send: {response_str[:200]}...")
                        
                        # Send the response
                        await websocket.send(response_str)
                        logger.info(f"Sent response to client {client_id}")
                        
                    except Exception as e:
                        error_msg = f"Error processing message: {str(e)}"
                        logger.error(f"{error_msg}\n{traceback.format_exc()}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "content": error_msg
                        }))
                
                elif data.get("type") == "api_request":
                    # Handle API request forwarding
                    logger.info(f"Processing API request from {client_id}")
                    await manager.forward_api_request(data, client_id)
                
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
        # Clean up when connection closes
        if client_id in manager.active_connections:
            del manager.active_connections[client_id]
        if client_id in manager.chat_sessions:
            del manager.chat_sessions[client_id]
        logger.info(f"Connection closed and cleaned up for client {client_id}")

async def main():
    """Start the WebSocket server."""
    host = "127.0.0.1"
    port = 8766  # Changed from 8765 to 8766
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    async with websockets.serve(handle_websocket, host, port):
        logger.info(f"Server started. Listening on {host}:{port}")
        await asyncio.Future()  # Run forever

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    logger.info(f"FastAPI WebSocket connection request from {client_id}")
    logger.info(f"WebSocket headers: {dict(websocket.headers)}")
    
    await manager.connect(websocket, client_id)
    try:
        # Only handle one message for testing
        data = await websocket.receive_text()
        logger.info(f"Raw data received from client {client_id}: {data}")
        
        payload = json.loads(data)
        logger.info(f"Parsed JSON payload from client {client_id}: {payload}")
        
        # Handle different message types
        if payload["type"] == "message":
            user_message = payload["content"]
            
            # Get chat session for this client
            chat_session = manager.chat_sessions[client_id]
            
            # Send acknowledgment
            await manager.send_message(
                json.dumps({"type": "status", "content": "processing"}),
                client_id
            )
            
            # Process the message in a non-blocking way
            try:
                # Start streaming response
                logger.info(f"Sending request to Gemini API for client {client_id}")
                response = chat_session.send_message(user_message)
                response_text = response.text
                
                # Log full response for debugging
                logger.info(f"Full response object from Gemini: {response}")
                logger.info(f"Response text from Gemini: {response_text[:200]}...")
                
                # Create and log response JSON
                response_json = {
                    "type": "response",
                    "content": response_text
                }
                response_str = json.dumps(response_json)
                logger.info(f"Formatted JSON response to send: {response_str[:200]}...")
                
                # Send the complete response
                await manager.send_message(response_str, client_id)
                logger.info(f"Sent response to client {client_id}")
                
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                # Send error message
                await manager.send_message(
                    json.dumps({"type": "error", "content": error_msg}),
                    client_id
                )
        
        elif payload["type"] == "api_request":
            # Handle API request forwarding
            logger.info(f"Processing API request from {client_id}")
            await manager.forward_api_request(payload, client_id)
        
        elif payload["type"] == "ping":
            await manager.send_message(json.dumps({"type": "pong"}), client_id)
        
        # After handling one message, close the websocket (for testing)
        await websocket.close()
        logger.info(f"Closed WebSocket for client {client_id} after one request (test mode)")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for client {client_id}")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error in WebSocket connection for client {client_id}: {str(e)}\n{traceback.format_exc()}")
        manager.disconnect(client_id)

# Regular HTTP endpoint to check server status
@app.get("/")
def read_root():
    return {"status": "Gemini WebSocket Server is running"}

if __name__ == "__main__":
    import uvicorn
    try:
        # Run the FastAPI app using Uvicorn
        logger.info("Starting FastAPI server with Uvicorn")
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}\n{traceback.format_exc()}")

# Clean up aiohttp session on application shutdown
@app.on_event("shutdown")
async def shutdown_event():
    if manager.http_session is not None and not manager.http_session.closed:
        await manager.http_session.close()
        logger.info("Closed aiohttp session on shutdown") 