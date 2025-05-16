import os
import time
import logging
import datetime
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gemini_logs.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gemini_app")

# Load environment variables
load_dotenv()

# Configure API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Please set your GOOGLE_API_KEY in the .env file")
    st.stop()

# Configure the Gemini API
genai.configure(api_key=api_key)

# Set up the model
model = genai.GenerativeModel('gemini-pro')

# Set page config
st.set_page_config(
    page_title="Gemini AI Interface",
    page_icon="🤖",
    layout="wide"
)

# App title
st.title("🤖 Gemini AI Interface")
st.write("Enter your prompt, and Gemini will respond.")

# Create two columns - one for input/response and one for logs
col1, col2 = st.columns([2, 1])

with col1:
    # Input area for user prompt
    user_prompt = st.text_area("Your prompt:", height=150)
    
    # Submit button
    if st.button("Submit to Gemini"):
        if user_prompt:
            # Log the request
            request_id = f"req_{int(time.time())}"
            log_message = f"REQUEST [{request_id}]: {user_prompt}"
            logger.info(log_message)
            
            # Display "Thinking..." while waiting
            with st.spinner("Gemini is thinking..."):
                try:
                    # Get response from Gemini
                    start_time = time.time()
                    response = model.generate_content(user_prompt)
                    response_text = response.text
                    end_time = time.time()
                    
                    # Log the response
                    process_time = round(end_time - start_time, 2)
                    log_message = f"RESPONSE [{request_id}] (took {process_time}s): {response_text[:100]}..."
                    logger.info(log_message)
                    
                    # Display response
                    st.markdown("### Response:")
                    st.markdown(response_text)
                    
                    # Add to session state for logging display
                    if "log_entries" not in st.session_state:
                        st.session_state.log_entries = []
                    
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.log_entries.append({
                        "timestamp": timestamp,
                        "request_id": request_id,
                        "prompt": user_prompt,
                        "response": response_text,
                        "process_time": process_time
                    })
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    logger.error(f"ERROR [{request_id}]: {error_msg}")
                    st.error(error_msg)
        else:
            st.warning("Please enter a prompt first.")

with col2:
    st.markdown("### Logs")
    
    # Add a checkbox to show full responses in logs
    show_full = st.checkbox("Show full responses in logs", value=False)
    
    # Download logs button
    if st.button("Download Logs"):
        with open("gemini_logs.log", "r") as f:
            log_content = f.read()
        
        st.download_button(
            label="Download Log File",
            data=log_content,
            file_name=f"gemini_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            mime="text/plain"
        )
    
    # Display logs from session state
    if "log_entries" in st.session_state and st.session_state.log_entries:
        for entry in reversed(st.session_state.log_entries):
            with st.expander(f"{entry['timestamp']} - ID: {entry['request_id']}"):
                st.markdown("**Prompt:**")
                st.text(entry['prompt'])
                st.markdown("**Response:**")
                if show_full:
                    st.markdown(entry['response'])
                else:
                    st.text(entry['response'][:100] + "..." if len(entry['response']) > 100 else entry['response'])
                st.info(f"Process time: {entry['process_time']} seconds")

# Add information about the .env file
st.sidebar.title("Configuration")
st.sidebar.info(
    """
    ### API Key Configuration
    
    To use this app:
    
    1. Create a `.env` file in the project root directory
    2. Add your Google API key to the file as:
       ```
       GOOGLE_API_KEY=your_key_here
       ```
    3. Restart the application
    
    Get your API key from [Google AI Studio](https://ai.google.dev/)
    """
)

# Add model selection
st.sidebar.title("Model Settings")
model_version = st.sidebar.selectbox(
    "Select Gemini Model",
    ["gemini-pro", "gemini-pro-vision"], 
    index=0
)

if model_version != "gemini-pro":
    st.sidebar.warning("Note: The vision model requires image input which is not supported in this basic UI.")

# Show current status
if api_key:
    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    st.sidebar.success(f"API Key Configured: {masked_key}")
else:
    st.sidebar.error("API Key Not Found") 