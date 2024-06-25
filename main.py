import uvicorn
import socketio
from fastapi import FastAPI, File, UploadFile
from typing import Dict, List
from data.csv_loader import load_csv_to_weaviate
from weaviate import setup_weaviate_interface
from openai import OpenAI
from dotenv import load_dotenv
import os
import datetime
from weaviate.http_client import HttpClient, HttpHandler
from weaviate.weaviate_client import WeaviateClient




load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
weaviate_url = os.getenv("WEAVIATE_URL", "http://0.0.0.0:8080")
http_client = HttpClient(base_url="http://localhost:8080", headers={"X-OpenAI-Api-Key": openai_key})
http_handler = HttpHandler(http_client)

weaviate_client = WeaviateClient(http_handler)
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

csv_file_path = '/home/lillian/tenacious/team-mate/data/cleaned_csvfile.csv'



openai_client = OpenAI()

# scheduler = AsyncIOScheduler()

# def scheduled_data_loading():
#     asyncio.run(load_csv_data())

# @app.on_event("startup")
# async def schedule_jobs():
#     scheduler.add_job(scheduled_data_loading, 'interval', hours=24)
#     scheduler.start()
# Print {"Hello":"World"} on localhost:7777
# @app.on_event("startup")
# async def startup_event():
    
#     csv_file_path = '/home/lillian/tenacious/team-mate/data/all_nov_jobs.csv'

#     await load_csv_to_weaviate(csv_file_path, weaviate_interface.client)
    
#     total_records = await weaviate_interface.get_object_count("JobPosting")
#     print(f"Total records uploaded: {total_records}")

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
        job_keywords = ['job', 'hiring', 'career', 'vacancy', 'employment']

        if any(keyword in received_message["message"].lower() for keyword in job_keywords):
            job_prompt = (
              "Give me the title of the job the user wants."
                f"\n\nUser message: {data.get('message')}"
            )
            response = openai_client.completions.create(
                model="gpt-3.5-turbo-instruct",  
                prompt=job_prompt,
                max_tokens=150
            )
            print("Here is the answer from the response", response)
            job_needed = response.choices[0].text.strip()
            query_body = f"""
                {{
                    Get {{
                        JobPosting(
                            where: {{
                                operator: Like,
                                path: ["description"]
                                valueString: "{job_needed}"  
                            }},
                            limit: 3
                        ) {{
                            title
                            description
                            company 
                            location
                        }}
                    }}
                }}
                """
            final_response = await weaviate_client.run_query(query_body)
            jobs = final_response['data']['Get']['JobPosting']
            job_list = []
            for job in jobs:
                job_title = job['title']
                job_description = job['description']
                job_company = job['company']
                job_location = job.get('location', 'No location specified')  

                job_info = {
                    'Title': job_title,
                    'Description': job_description,
                    'Company': job_company,
                    'Location': job_location
                }

                job_list.append(job_info)
            formatted_job_list = "\n".join([
                f"Title: {job['Title']}, Company: {job['Company']}, Location: {job['Location']}\nDescription: {job['Description'][:100]}..." 
                for job in job_list
                    ])
            completion_2 = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that aids in educational and training activities I want you to give this list to the user with your insight inputs to it."},
                    {"role": "user", "content": formatted_job_list}
                ]
            )
            openai_response = completion_2.choices[0].message.content
            

            response_message = {
            "id": data.get("id") + "_response",
            "textResponse":  f"Here are some jobs you can check:\n{openai_response}",
            "isUserMessage": False,
            "timestamp": "today",
            "isComplete": True,
              }
            await sio.emit("textResponse", response_message, room=sid)
            sessions[session_id].append(response_message)
        else:
            prompt = (
              "You are an AI-based personalized agent designed to optimize trainee time and focus. Your scope includes providing personalized interactions, adaptive learning and support, proactive planning and scheduling, blocker resolution, and enhancing collaboration among other trainees."
                f"\n\nUser message: {data.get('message')}"
            )

            completion = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that aids in educational and training activities, these are jobs from a dataset I want you to display it in a readable format for the user and give him some suggestions about these vacancies as well"},
                    {"role": "user", "content": prompt}
                ]
            )
            openai_response = completion.choices[0].message.content
            print("type of openai response", openai_response)
            response_message = {
                "id": data.get("id") + "_response",
                "textResponse": openai_response,
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
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6789, lifespan="on", reload=True)
