import os
import asyncio
from typing import List
from openai import OpenAI
import requests

# MUST use the OpenAI client with these variables
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("API_BASE_URL"))

API_BASE = os.getenv("SPACE_URL", "https://ADITYA-VEGI-email-ops-openenv.hf.space")
MODEL = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
MAX_STEPS = 8

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
    # Run through all 3 tasks
    tasks = ["easy", "medium", "hard"]
    
    for task_id in tasks:
        # LOGGING FORMAT (Crucial)
        print(f"[START] Task ID: {task_id}")
        
        rewards: List[float] = []
        steps = 0
        success = False
        
        try:
            # Reset environment for this task
            r = requests.post(f"{API_BASE}/reset", json={"task": task_id}).json()
            
            for i in range(1, MAX_STEPS+1):
                a = choose_action(r)
                action = f"{a['action_type']}:{a['content']}"
                
                resp = requests.post(f"{API_BASE}/step", json=a).json()
                reward = float(resp.get("reward") or 0.0)
                done = bool(resp.get("done"))
                
                rewards.append(reward)
                steps = i
                
                # ... inside loop ...
                print(f"[STEP] Step: {i} | Action: {action} | Reward: {reward}")
                
                r = resp.get("observation") or {}
                if done:
                    break
            
            score = sum(rewards) / max(1, len(rewards))
            total = sum(rewards)
            success = score >= 0.5
            
        except Exception as e:
            score = 0.0
            total = 0.0
            success = False
            print(f"Error in task {task_id}: {e}")
        
        finally:
            # ... end of task ...
            print(f"[END] Task ID: {task_id} | Final Score: {score} | Total Reward: {total}")

if __name__ == "__main__":
    asyncio.run(main())