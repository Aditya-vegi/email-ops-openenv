import os
from openai import OpenAI
import requests

API_BASE = "https://ADITYA-VEGI-email-ops-openenv.hf.space"

print("[START] task=email_ops env=openenv model=test-model")

rewards = []

# reset
res = requests.post(f"{API_BASE}/reset").json()

for step in range(1, 4):
    action = {
        "action_type": "reply",
        "content": "This is urgent, we are fixing with the team"
    }

    r = requests.post(f"{API_BASE}/step", json=action).json()

    reward = r["reward"]
    done = r["done"]

    rewards.append(reward)

    print(f"[STEP] step={step} action=reply reward={reward:.2f} done={str(done).lower()} error=null")

    if done:
        break

score = sum(rewards) / len(rewards)
success = score > 0.5

print(f"[END] success={str(success).lower()} steps={len(rewards)} rewards={','.join([f'{r:.2f}' for r in rewards])}")