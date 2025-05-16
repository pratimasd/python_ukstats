import streamlit as st
import json
import uuid
import threading
import time
import websocket
from queue import Queue

# Create a thread-safe message queue outside of session state
global_message_queue = Queue()
global_ws_connected = False

# Set page config
st.set_page_config(
    page_title="Gemini WebSocket Chat", 
    page_icon="💬",
    layout="centered"
)

# WebSocket connection info
WS_SERVER = "ws://127.0.0.1:8765"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())

if "ws_client" not in st.session_state:
    st.session_state.ws_client = None

# UI Elements
st.title("Gemini WebSocket Chat")
st.markdown("This demo shows WebSocket integration with Gemini LLM")

status_container = st.empty()

# Initialize global variables
global_needs_rerun = False

# WebSocket Callbacks - These run in a separate thread and use the global queue
def on_message(ws, message):
    try:
        # Parse the message
        data = json.loads(message)
        print(f"Received WebSocket message: {data}")
        
        # Add to global queue instead of session state
        global_message_queue.put(data)
        
        # Signal that we need a rerun, will be picked up in the main thread
        global global_needs_rerun
        global_needs_rerun = True
    except Exception as e:
        print(f"Error processing message: {str(e)}")

def on_error(ws, error):
    print(f"WebSocket error: {str(error)}")
    # Don't try to modify session state here
    global global_ws_connected
    global_ws_connected = False

def on_close(ws, close_status_code, close_reason):
    print(f"WebSocket connection closed: {close_status_code} - {close_reason}")
    # Don't try to modify session state here
    global global_ws_connected
    global_ws_connected = False

def on_open(ws):
    print("WebSocket connection opened")
    # Don't try to modify session state here
    global global_ws_connected
    global_ws_connected = True
    global_message_queue.put({"type": "connected", "content": "Connected to server"})

# WebSocket connection management
def connect_to_websocket():
    # Create WebSocket connection
    client_id = st.session_state.client_id
    ws_url = f"{WS_SERVER}/{client_id}"
    
    try:
        status_container.info("Connecting to WebSocket server...")
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # Start WebSocket connection in a thread
        ws_thread = threading.Thread(target=lambda: ws.run_forever())
        ws_thread.daemon = True
        ws_thread.start()
        
        # Store the WebSocket client
        st.session_state.ws_client = ws
        
        # Wait a bit for connection to establish
        time.sleep(1)
        
        # Check the global connection flag
        global global_ws_connected
        if global_ws_connected:
            status_container.success("Connected to Gemini WebSocket Server")
            return True
        else:
            status_container.error("Failed to connect to WebSocket server")
            return False
            
    except Exception as e:
        status_container.error(f"Error connecting to WebSocket server: {str(e)}")
        return False

# Send message to WebSocket server
def send_message(text):
    if st.session_state.ws_client is None:
        if not connect_to_websocket():
            return False
    
    # Prepare message
    message = {
        "type": "message",
        "content": text
    }
    
    # Send message
    try:
        st.session_state.ws_client.send(json.dumps(message))
        return True
    except Exception as e:
        status_container.error(f"Error sending message: {str(e)}")
        return False

# Process messages from queue (runs in main thread)
def process_messages():
    global global_needs_rerun
    needs_update = False
    
    # Process any messages in the global queue
    while not global_message_queue.empty():
        try:
            data = global_message_queue.get_nowait()
            print(f"Processing queue message: {data}")
            
            # Handle different message types
            if data.get("type") == "response":
                # Add the response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": data.get("content", "")
                })
                needs_update = True
                print(f"Added response to messages: {data.get('content', '')[:30]}...")
                
            elif data.get("type") == "status":
                status_container.info(data.get("content", "Processing..."))
                
            elif data.get("type") == "error":
                status_container.error(data.get("content", "An error occurred"))
                
            elif data.get("type") == "connected":
                status_container.success(data.get("content", "Connected to server"))
                
        except Exception as e:
            print(f"Error processing message from queue: {str(e)}")
    
    # Check if we need to update the UI
    if needs_update or global_needs_rerun:
        global_needs_rerun = False
        print("Triggering UI update with experimental_rerun")
        st.experimental_rerun()

# Connect to WebSocket on page load
if st.session_state.ws_client is None:
    connect_to_websocket()

# Process any pending messages
process_messages()

# Display WebSocket connection status
conn_status = st.sidebar.container()
if global_ws_connected:
    conn_status.success("✅ WebSocket Connected")
else:
    conn_status.error("❌ WebSocket Disconnected")

# Add a reconnect button
if st.sidebar.button("Reconnect WebSocket"):
    st.session_state.ws_client = None
    connect_to_websocket()
    st.experimental_rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input
prompt = st.chat_input("Type your message here...")

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in the chat
    with st.chat_message("user"):
        st.write(prompt)
    
    # Process with WebSocket
    if send_message(prompt):
        # Show a temporary processing message
        with st.chat_message("assistant"):
            st.write("Processing...")
        
    # Force an update
    st.experimental_rerun() 