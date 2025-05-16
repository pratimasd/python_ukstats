import streamlit as st
import json
import uuid
import requests

# Set page config
st.set_page_config(page_title="Gemini API Chat", page_icon="💬")

# Streamlit UI
st.title("Gemini AI Chat")
st.write("A simple interface using API instead of WebSockets")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())

# Status container
status = st.empty()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Ask anything...")

# Process user input
if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # URL for API access
    api_url = "http://127.0.0.1:5000/api/chat"
    
    # Show processing message
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.info("Processing your request...")
    
    try:
        # Process with API
        response = requests.post(
            api_url,
            json={
                "message": user_input,
                "client_id": st.session_state.client_id
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response", "Sorry, I couldn't process that.")
            
            # Add AI response to chat history
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
            # Update the placeholder with the actual response
            message_placeholder.empty()
            with st.chat_message("assistant"):
                st.markdown(ai_response)
        else:
            message_placeholder.error(f"Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        message_placeholder.error("Connection error: Could not connect to the API server. Please make sure the server is running.")
    except Exception as e:
        message_placeholder.error(f"Error: {str(e)}") 