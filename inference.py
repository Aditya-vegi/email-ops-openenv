import os, asyncio
from typing import List
from openai import OpenAI
import requests

API_BASE = os.getenv("SPACE_URL", "https://ADITYA-VEGI-email-ops-openenv.hf.space")
MODEL = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
client = OpenAI(base_url=os.getenv("API_BASE_URL"), api_key=os.getenv("HF_TOKEN"))

MAX_STEPS = 8

def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error):
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error or 'null'}", flush=True)

def log_end(success, steps, rewards):
    rs = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rs}", flush=True)

def choose_action(obs) -> dict:
    # simple policy (deterministic baseline)
    cur = obs.get("current")
    if not cur:
        return {"action_type":"next","content":"move next"}

    body = (cur.get("body") or "").lower()
    if "down" in body or "asap" in body:
        return {"action_type":"classify","content":"urgent"}
    return {"action_type":"reply","content":"Hello, we are working on this with the team and will update soon."}

async def main():
    log_start("email_ops", "openenv", MODEL)
    rewards: List[float] = []
    steps = 0
    success = False
    try:
        r = requests.post(f"{API_BASE}/reset").json()
        for i in range(1, MAX_STEPS+1):
            a = choose_action(r)
            resp = requests.post(f"{API_BASE}/step", json=a).json()
            rew = float(resp.get("reward") or 0.0)
            done = bool(resp.get("done"))
            rewards.append(rew)
            steps = i
            log_step(i, f"{a['action_type']}:{a['content']}", rew, done, None)
            r = resp.get("observation") or {}
            if done:
                break
        score = sum(rewards) / max(1, len(rewards))
        success = score >= 0.5
    finally:
        log_end(success, steps, rewards)

if __name__ == "__main__":
    asyncio.run(main())