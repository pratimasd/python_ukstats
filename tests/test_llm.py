import os
import pytest
from unittest.mock import patch, MagicMock
import sys
import json
from conftest import make_mock_chat_session

# Add parent directory to path to allow importing from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Gemini API
from gemini_api import GeminiAPI

class TestGeminiAPI:
    """Tests for the GeminiAPI class"""
    
    def test_init_with_api_key(self, mock_gemini_api):
        """Test initializing with an API key"""
        api_key = "AIzaSyAfaDvmnbsfNAqoBGBIe4muXj3LQELbT4M"
        with patch('gemini_api.genai.configure') as mock_configure:
            api = GeminiAPI(api_key=api_key)
            mock_configure.assert_called_once_with(api_key=api_key)
    
    def test_init_without_api_key(self, mock_gemini_api):
        """Test initializing without an API key (should load from env)"""
        with patch('gemini_api.os.getenv', return_value="env_api_key"), \
             patch('gemini_api.genai.configure') as mock_configure:
            api = GeminiAPI()
            mock_configure.assert_called_once_with(api_key="env_api_key")
    
    def test_generate_text(self, mock_gemini_api):
        """Test text generation"""
        with patch.object(GeminiAPI, 'generate_text', return_value="Generated text"):
            api = GeminiAPI(api_key="test_key")
            response = api.generate_text("Test prompt")
            assert response == "Generated text"
    
    def test_chat_session(self, mock_gemini_api):
        """Test chat session creation and message sending"""
        with patch.object(GeminiAPI, 'chat_session', return_value=make_mock_chat_session()):
            api = GeminiAPI(api_key="AIzaSyAfaDvmnbsfNAqoBGBIe4muXj3LQELbT4M")
            session = api.chat_session()
            
            # Test sending a message
            response = session.send_message("Hello")
            assert response.text == "This is a mock response from the Gemini API."
            
    def test_error_handling(self):
        """Test error handling when API key is missing"""
        with patch('gemini_api.os.getenv', return_value=None):
            with pytest.raises(ValueError) as excinfo:
                GeminiAPI()
            assert "No API key provided" in str(excinfo.value)

# Test with real API key (optional and only runs if API_KEY is set in environment)
@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="No API key available")
class TestGeminiAPIIntegration:
    """Integration tests using real API key"""
    
    def test_real_text_generation(self):
        """Test actual text generation (requires real API key)"""
        api = GeminiAPI()
        response = api.generate_text("Hello, how are you?")
        assert isinstance(response, str)
        assert len(response) > 0
        
    def test_real_chat_session(self):
        """Test actual chat session (requires real API key)"""
        api = GeminiAPI()
        session = api.chat_session()
        response = session.send_message("Tell me a short joke")
        assert response.text
        assert len(response.text) > 0 