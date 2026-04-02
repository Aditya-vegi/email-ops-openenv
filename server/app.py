import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from env import EmailEnv
from models import Action

app = FastAPI(
    title="Email Ops OpenEnv",
    description="Email triage automation environment",
    version="0.1.0"
)

env = EmailEnv()

@app.get("/")
def root():
    return {"status": "running", "service": "email-ops-openenv"}

@app.post("/reset")
async def reset():
    obs = await env.reset()
    return obs.__dict__

@app.post("/step")
async def step(action: Action):
    result = await env.step(action)
    return {
        "observation": result.observation.__dict__ if result.observation else None,
        "reward": result.reward,
        "done": result.done,
        "info": {}
    }

@app.get("/state")
async def state():
    obs = await env.state()
    return obs.__dict__

def main():
    """Main entry point for the server"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
