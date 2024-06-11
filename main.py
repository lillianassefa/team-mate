import httpx
import uvicorn
import socketio
from fastapi import FastAPI, File, UploadFile
from typing import Dict, List
from chat.csv_loader import load_csv_to_weaviate
from weaviate import setup_weaviate_interface
from openai import OpenAI
from dotenv import load_dotenv
import os
import datetime
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
weaviate_url = os.getenv("WEAVIATE_URL", "http://0.0.0.0:8080")
# FastAPI application
app = FastAPI()

# Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")

# Wrap with ASGI application
socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)

# Dictionary to store session data
sessions: Dict[str, List[Dict[str, str]]] = {}

# Weaviate Interface
weaviate_interface = setup_weaviate_interface()

# OpenAI client
openai_client = OpenAI()

# Print {"Hello":"World"} on localhost:7777
@app.get("/")
def read_root():
    return {"Hello": "World"}

@sio.on("connect")
async def connect(sid, env):
    print("New Client Connected to This id :" + " " + str(sid))

@sio.on("disconnect")
async def disconnect(sid):
    print("Client Disconnected: " + " " + str(sid))

@sio.on("connectionInit")
async def handle_connection_init(sid):
    await sio.emit("connectionAck", room=sid)

@sio.on("sessionInit")
async def handle_session_init(sid, data):
    print(f"===> Session {sid} initialized")
    session_id = data.get("sessionId")
    if session_id not in sessions:
        sessions[session_id] = []
    print(f"**** Session {session_id} initialized for {sid} session data: {sessions[session_id]}")
    await sio.emit("sessionInit", {"sessionId": session_id, "chatHistory": sessions[session_id]}, room=sid)

# Handle incoming chat messages
@sio.on("textMessage")
async def handle_chat_message(sid, data):
    print(f"Message from {sid}: {data}")
    session_id = data.get("sessionId")
    if session_id:
        if session_id not in sessions:
            raise Exception(f"Session {session_id} not found")
        received_message = {
            "id": data.get("id"),
            "message": data.get("message"),
            "isUserMessage": True,
            "timestamp": data.get("timestamp"),
        }
        sessions[session_id].append(received_message)
        
       
        prompt = (
          "You are an AI-based personalized agent designed to optimize trainee time and focus. Your scope includes providing personalized interactions, adaptive learning and support, proactive planning and scheduling, blocker resolution, and enhancing collaboration among other trainees."
            f"\n\nUser message: {data.get('message')}"
        )
        
        
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that aids in educational and training activities."},
                {"role": "user", "content": prompt}
            ]
        )
        openai_response = completion.choices[0].message.content
        print("type of openai respons", openai_response)
        response_message = {
            "id": data.get("id") + "_response",
            "textResponse":  openai_response,
            "isUserMessage": False,
            "timestamp": "today",
            "isComplete": True,
        }
        print("here is the response message", response_message)
        await sio.emit("textResponse", response_message, room=sid)
        sessions[session_id].append(response_message)

        print(f"Message from {sid} in session {session_id}: {openai_response}")

    else:
        print(f"No session ID provided by {sid}")
@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())

        # Process the CSV file and upload data to Weaviate
        await load_csv_to_weaviate(file_location)
        return {"status": "success", "detail": "CSV file processed and data uploaded to Weaviate."}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
async def call_upload_csv(csv_file_path: str):
    url = "http://0.0.0.0:6789/upload_csv"
    files = {'file': open(csv_file_path, 'rb')}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, files=files)
        print(response.json())


@app.on_event("startup")
async def trigger_csv_upload():
    csv_file_path = "/home/lillian/tenacious/team-mate/chat/all_nov_jobs.csv" 
    await call_upload_csv(csv_file_path)
    return {"status": "success", "detail": "CSV upload triggered."}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6789, lifespan="on", reload=True)
