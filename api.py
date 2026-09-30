import os
import json
import asyncio
import threading
import queue
import sys
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from research_crew import OptumStrategicCrew

app = FastAPI(title="Optum Strategic Alpha API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MissionRequest(BaseModel):
    topic: str

# In-memory store for mission logs
missions = {}

class LogCapture:
    def __init__(self, mission_id):
        self.mission_id = mission_id
        self.queue = queue.Queue()

    def write(self, message):
        if message.strip():
            self.queue.put(message)

    def flush(self):
        pass

def run_crew_job(mission_id, topic):
    # Capture stdout
    original_stdout = sys.stdout
    capture = LogCapture(mission_id)
    sys.stdout = capture
    missions[mission_id]["status"] = "running"
    missions[mission_id]["capture"] = capture
    
    try:
        crew_instance = OptumStrategicCrew(topic)
        result = crew_instance.kickoff()
        missions[mission_id]["result"] = str(result)
        missions[mission_id]["status"] = "completed"
        capture.write("MISSION_COMPLETE: Process finished successfully.")
    except Exception as e:
        missions[mission_id]["status"] = "failed"
        capture.write(f"MISSION_FAILED: {str(e)}")
    finally:
        sys.stdout = original_stdout

@app.post("/run-mission")
async def run_mission(request: MissionRequest):
    mission_id = f"mission_{int(asyncio.get_event_loop().time())}"
    missions[mission_id] = {"topic": request.topic, "status": "pending", "result": None}
    
    # Start the crew in a background thread
    thread = threading.Thread(target=run_crew_job, args=(mission_id, request.topic))
    thread.start()
    
    return {"mission_id": mission_id}

@app.get("/stream/{mission_id}")
async def stream_mission(mission_id: str):
    if mission_id not in missions:
        return {"error": "Mission not found"}

    async def event_generator():
        capture = missions[mission_id].get("capture")
        if not capture:
            yield f"data: {json.dumps({'message': 'Initializing agents...'})}\n\n"
        
        while missions[mission_id]["status"] == "running" or not capture.queue.empty():
            try:
                # Non-blocking get from queue
                message = capture.queue.get_nowait()
                yield f"data: {json.dumps({'message': message})}\n\n"
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue
        
        if missions[mission_id]["status"] == "completed":
            yield f"data: {json.dumps({'status': 'completed', 'result': missions[mission_id]['result']})}\n\n"
        elif missions[mission_id]["status"] == "failed":
            yield f"data: {json.dumps({'status': 'failed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/reports")
async def get_reports():
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return []
    
    files = os.listdir(reports_dir)
    report_list = []
    for f in files:
        if f.endswith(".md"):
            with open(os.path.join(reports_dir, f), "r", encoding="utf-8") as file:
                content = file.read()
                report_list.append({"filename": f, "content": content})
    return report_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
