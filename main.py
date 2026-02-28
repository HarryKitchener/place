from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
import redis
import uuid


class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.connections:
            await connection.send_json(message)


redis_client = redis.Redis(host='redis', port=6379, db=0)
app = FastAPI()
manager = ConnectionManager()

CANVAS_WIDTH = 500
CANVAS_HEIGHT = 500


@app.get("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    pass


@app.get("/pixels")
def get_pixels():
    """
    GET request to get the current state of the canvas from redis
    Returns:
        A dictionary of the current state of the canvas
    """
    pixels = redis_client.hgetall('pixels')
    return pixels


@app.post("/pixels")
def post_pixels(loc_x: int, loc_y: int, colour: str, session_id: str):
    """
    POST request to post a pixel change to redis

    Args:
        loc_x (int): The x coordinate of the pixel
        loc_y (int): The y coordinate of the pixel
        colour (str): The colour of the pixel in hex format
        session_id (str): The session id of the user making the change

    Returns:
        A dictionary of the pixel change that was made
    """
    # Check if the session id is valid
    redis_session = redis_client.get(f'session:{session_id}')
    if not redis_session:
        raise HTTPException(
            status_code=401,
            detail="Session ID is not valid"
        )

    # Check the if the user has changed a pixel in the last 30 seconds
    pixel_session = redis_client.get(f'pixel:{session_id}')
    ttl_session = redis_client.ttl(f'pixel:{session_id}')
    if pixel_session:
        raise HTTPException(
            status_code=429,
            detail=(
                "You can only change one pixel every 30 seconds."
                f" {ttl_session} seconds remaining."
            )
        )

    # Set the pixel change in redis and set a timeout for the session
    redis_client.hset('pixels', f'{loc_x},{loc_y}', colour)
    redis_client.set(f'pixel:{session_id}', 1, ex=30)

    return {
        'loc_x': loc_x,
        'loc_y': loc_y,
        'colour': colour
    }


@app.post("/session")
def post_session():
    """
    POST request to create a new session id for a user

    Returns:
        A dictionary containing the new session id
    """
    session_id = str(uuid.uuid4())
    redis_client.set(f'session:{session_id}', 1, ex=3600)

    return {
        'session_id': session_id
    }
