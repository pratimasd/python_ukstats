import os
import json
import uuid
import asyncio
import streamlit as st
from dotenv import load_dotenv
import websockets
from websockets.exceptions import ConnectionClosed
import threading

# Load environment variables
load_dotenv()

# Configuration
websocket_url = "ws://localhost:8000/ws"

# Streamlit UI
st.title("Gemini AI WebSocket Chat")
st.write("Ask Gemini anything with real-time responses!")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Generate a unique client ID if not already present
if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())

# WebSocket connection status
if "ws_connected" not in st.session_state:
    st.session_state.ws_connected = False

# Track the WebSocket connection
if "ws_connection" not in st.session_state:
    st.session_state.ws_connection = None

# Create placeholder for status messages
status_placeholder = st.empty()

# Process received messages
async def listen_for_messages():
    if not st.session_state.ws_connected:
        return
    
    client_id = st.session_state.client_id
    full_url = f"{websocket_url}/{client_id}"
    
    try:
        async with websockets.connect(full_url) as websocket:
            while True:
                try:
                    # Receive message from server
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Handle different message types
                    if data["type"] == "response":
                        # Add assistant message to chat history
                        st.session_state.messages.append({"role": "assistant", "content": data["content"]})
                        # Force a rerun to update the UI
                        st.rerun()
                    
                    elif data["type"] == "status":
                        # Update status message
                        status_placeholder.write(f"Status: {data['content']}")
                    
                    elif data["type"] == "error":
                        # Show error message
                        st.error(f"Error: {data['content']}")
                        # Force a rerun to update the UI
                        st.rerun()
                
                except ConnectionClosed:
                    st.session_state.ws_connected = False
                    break
    
    except Exception as e:
        st.session_state.ws_connected = False
        status_placeholder.write(f"Connection error: {str(e)}")

# Connect to WebSocket server
def connect_to_websocket():
    if not st.session_state.ws_connected:
        status_placeholder.write("Connecting to server...")
        
        # Start WebSocket connection in a separate thread
        def start_connection():
            asyncio.run(listen_for_messages())
        
        threading.Thread(target=start_connection, daemon=True).start()
        st.session_state.ws_connected = True
        status_placeholder.write("Connected to server")

# Send message to WebSocket server
async def send_message(prompt):
    client_id = st.session_state.client_id
    full_url = f"{websocket_url}/{client_id}"
    
    try:
        async with websockets.connect(full_url) as websocket:
            # Prepare message payload
            payload = {
                "type": "message",
                "content": prompt
            }
            
            # Send message to server
            await websocket.send(json.dumps(payload))
            
            # For demo purposes, wait for the initial acknowledgment
            # In a production app, you'd handle this in the listener
            message = await websocket.recv()
            data = json.loads(message)
            if data["type"] == "status":
                status_placeholder.write(f"Status: {data['content']}")
    
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        st.session_state.ws_connected = False

# Connect to WebSocket on app load
connect_to_websocket()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
prompt = st.chat_input("Enter your message here...")

# Process user input
if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Check if connected to WebSocket server
    if not st.session_state.ws_connected:
        connect_to_websocket()
    
    # Send message to WebSocket server
    asyncio.run(send_message(prompt))
    
    # Show a temporary processing message
    with st.chat_message("assistant"):
        st.write("Processing...")
    
    # Force a rerun to update the UI
    st.rerun() 