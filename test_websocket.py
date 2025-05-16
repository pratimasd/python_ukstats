import asyncio
import json
import websockets

"""
Simple test script to verify WebSocket connectivity and response handling
without relying on Streamlit.
"""

async def test_websocket():
    # Connect to the WebSocket server
    uri = "ws://127.0.0.1:8765/test-client"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("\n✅ CONNECTED to server")
            
            # Wait for welcome message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"👋 Got welcome message: {data}")
            
            # Send a test message
            test_message = {
                "type": "message",
                "content": "Hello, are you working correctly?"
            }
            
            print(f"\n📤 Sending message: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for status message
            print("\nWaiting for processing status...")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"🔄 Got status: {data}")
            
            # Wait for final response
            print("\nWaiting for final response...")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Got response: {data}")
            
            # Send a ping message
            print("\n📤 Sending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Wait for pong
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Got pong: {data}")
            
            print("\n✅ TEST COMPLETED SUCCESSFULLY!")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 