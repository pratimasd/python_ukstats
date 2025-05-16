# Python Gemini Integration

A Python project integrating Google's Gemini AI models for text generation, chat, and multimodal tasks.

## Features

- Text generation with Gemini Pro
- Chat functionality
- Image + text multimodal capabilities
- Streamlit web interface with request/response logging
- Console-based interface with logging

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Get a Google API key for Gemini from [Google AI Studio](https://ai.google.dev/)
4. Create a `.env` file in the project root and add your API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## Running the Applications

### Web Interfaces

To run the enhanced Streamlit web interface with request/response logging:

```
streamlit run gemini_ui.py
```

To run the basic Streamlit chat app:

```
streamlit run app.py
```

### Console Application

For a simple console-based interface with logging:

```
python console_app.py
```

### Command Line Examples

To run the text generation example:

```
python examples/text_generation.py
```

To run the chat example:

```
python examples/chat_example.py
```

## Logs and Monitoring

Both the web and console applications include detailed logging:

- **Web UI Logs**: Available in the sidebar of the gemini_ui.py application
- **Console Logs**: Type 'logs' in the console application to see recent interactions
- **Log Files**: 
  - `gemini_logs.log` - Web UI logs
  - `gemini_console_logs.log` - Console application logs

## Project Structure

- `app.py` - Basic Streamlit web application
- `gemini_ui.py` - Enhanced Streamlit UI with logs
- `console_app.py` - Console-based interface with logging
- `gemini_api.py` - Wrapper class for Gemini API
- `examples/` - Example scripts demonstrating API usage
  - `text_generation.py` - Basic text generation example
  - `chat_example.py` - Interactive chat example

## Requirements

- Python 3.7+
- google-generativeai
- python-dotenv
- streamlit

## License

MIT 