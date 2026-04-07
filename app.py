from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from env import EmailEnv, StepResult as EnvStepResult
from models import Action, StepResult, Observation

app = FastAPI(title="Email Ops OpenEnv", description="Email operations environment")

# Global environment instance
env = EmailEnv()

class StepRequest(BaseModel):
    action: Action

class ResetRequest(BaseModel):
    task: Optional[str] = "hard"

@app.get("/")
def root():
    return {"message": "Email Ops OpenEnv - Email triage and response environment"}

@app.post("/reset")
def reset(params: Optional[ResetRequest] = None):
    """Reset environment and return initial observation"""
    # Handle different request formats
    task = None
    if params and params.task:
        task = params.task
    
    # Create new environment instance
    global env
    env = EmailEnv(task=task) if task else EmailEnv()
    
    obs = env.reset()
    return obs.dict()

@app.post("/step")
def step(request: StepRequest):
    """Take action in environment"""
    # Use the environment's step function that returns StepResult object
    result = env.step(request.action)
    
    # Convert to dict for API response
    return {
        "observation": result.observation.dict(),
        "reward": result.reward,
        "done": result.done,
        "info": result.info
    }

@app.get("/state")
def state():
    """Get current environment state"""
    return env.state()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)