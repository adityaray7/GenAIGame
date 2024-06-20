import asyncio
import websockets
from dotenv import load_dotenv
import os
load_dotenv()

connected_clients = set()

async def echo(websocket, path):
    # Add the client to the set of connected clients
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Echo the message to all connected clients
            for client in connected_clients:
                await client.send(message)
    finally:
        # Remove the client from the set of connected clients when the connection is closed
        connected_clients.remove(websocket)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

host = "0.0.0.0"

start_server = websockets.serve(echo,host, os.getenv("WEBSOCKET_PORT"))

print(f'Server started at ws://{host}:' + os.getenv("WEBSOCKET_PORT"))
loop.run_until_complete(start_server)
loop.run_forever()
