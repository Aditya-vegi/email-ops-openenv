from fastapi import FastAPI
from models import Action
from env import EmailEnv

app = FastAPI()
env = EmailEnv(task="hard")

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/reset")
def reset():
    obs = env.reset()
    return obs.dict()

@app.post("/step")
def step(action: Action):
    res = env.step(action)
    return {
        "observation": res.observation.dict() if res.observation else None,
        "reward": res.reward,
        "done": res.done,
        "info": res.info
    }

@app.get("/state")
def state():
    return env.state()