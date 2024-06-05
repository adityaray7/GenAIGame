# client.py
import asyncio
import websockets
from dotenv import load_dotenv
import os
load_dotenv()

async def hello(message):
    async with websockets.connect(f"ws://localhost:{os.getenv('WEBSOCKET_PORT')}") as websocket:
        await websocket.send(message)
        response = await websocket.recv()
        # print(f"Received from server: {response}")

def send(message):
    asyncio.get_event_loop().run_until_complete(hello(message))

if __name__ == "__main__":
    send("Hello, Server!")