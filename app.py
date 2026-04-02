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
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.dict(),
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state")
def state():
    return env.state()