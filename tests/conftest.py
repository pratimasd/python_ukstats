import os
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import websockets

def make_mock_gemini_response():
    response = MagicMock()
    response.text = "This is a mock response from the Gemini API."
    return response

def make_mock_chat_session():
    session = MagicMock()
    session.send_message = MagicMock(return_value=make_mock_gemini_response())
    return session

def make_mock_aiohttp_response():
    response = AsyncMock()
    response.status = 200
    response.headers = {"Content-Type": "application/json"}
    response.json = AsyncMock(return_value={"data": "Test data"})
    response.text = AsyncMock(return_value=json.dumps({"data": "Test data"}))
    return response

@pytest.fixture
def mock_gemini_api():
    """Mock the GeminiAPI class"""
    with patch('gemini_api.GeminiAPI') as mock_api:
        instance = mock_api.return_value
        instance.chat_session.return_value = make_mock_chat_session()
        instance.generate_text.return_value = "Mock generated text"
        yield instance

@pytest.fixture
def mock_websocket():
    websocket = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock(side_effect=[
        json.dumps({
            "type": "message",
            "content": "Hello, Gemini!"
        }),
        json.dumps({
            "type": "ping"
        }),
        Exception("Connection closed")
    ])
    websocket.headers = {
        "user-agent": "Test Client",
        "host": "localhost:8000"
    }
    return websocket

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession"""
    session = AsyncMock()
    
    # Configure context manager behavior
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = make_mock_aiohttp_response()
    session.request.return_value = context_manager
    
    return session 