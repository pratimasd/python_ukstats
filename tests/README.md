# Test Framework for Python-Gemini Project

This directory contains test files for the Python-Gemini project, which integrates with Google's Gemini LLM API and provides WebSocket communication.

## Test Structure

- `conftest.py` - Contains shared fixtures used across all test files
- `test_llm.py` - Tests for the Gemini LLM API integration
- `test_websocket.py` - Tests for WebSocket server functionality and API request forwarding

## Running Tests

To run all tests:

```bash
pytest
```

To run specific test categories:

```bash
# Run only LLM-related tests
pytest tests/test_llm.py

# Run only WebSocket-related tests
pytest tests/test_websocket.py

# Run tests with specific markers
pytest -m llm
pytest -m websocket
pytest -m api
```

## Mocking Approach

The test framework uses pytest fixtures to provide mock implementations of:

1. **Gemini API**: Mock responses from the LLM service
2. **WebSocket connections**: Simulate client-server communication
3. **HTTP requests**: Mock API calls for API request forwarding

## Test Categories

### LLM Tests (`test_llm.py`)

These tests verify that the Gemini API integration works correctly:

- Initializing the API client
- Generating text
- Managing chat sessions
- Handling errors

### WebSocket Tests (`test_websocket.py`)

These tests verify WebSocket functionality:

- Connection management
- Message handling
- AI response processing
- API request forwarding to external services

### Integration Tests

Tests marked with `@pytest.mark.integration` require a running server instance and may interact with real APIs if credentials are provided.

## Required Environment Variables

For running tests that interact with real services:

- `GOOGLE_API_KEY` - Google API key for Gemini API

For local testing, mock implementations are provided so these are not required.

## Adding New Tests

1. Add new test functions to existing files following the naming convention `test_*`
2. For new test categories, create a new file following the naming convention `test_*.py`
3. If needed, add new fixtures to `conftest.py` for shared functionality 