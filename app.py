from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Simple action model
class Action(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/reset")
def reset():
    return {
        "email_id": 1,
        "subject": "Server Down",
        "body": "Fix immediately",
        "sender_role": "boss"
    }

@app.post("/step")
def step(action: Action):
    return {
        "observation": {
            "email_id": 2,
            "subject": "Next Task",
            "body": "Continue processing",
            "sender_role": "client"
        },
        "reward": 0.5,
        "done": False,
        "info": {}
    }

@app.get("/state")
def state():
    return {"state": "running"}