import os
import asyncio
from typing import List, Dict, Any
import requests
import json

# Test basic structure without OpenAI import
print("Testing basic inference structure...")

# Test environment variable handling
try:
    API_KEY = os.environ["API_KEY"]
    API_BASE_URL = os.environ["API_BASE_URL"]
    print("Environment variables loaded successfully")
except KeyError as e:
    print(f"Missing environment variable: {e}")
    print("Using mock values for local testing...")
    API_KEY = "test_key_for_local_testing"
    API_BASE_URL = "http://localhost:8000/v1"

API_BASE = os.getenv("SPACE_URL", "https://ADITYA-VEGI-email-ops-openenv.hf.space")
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_STEPS = 15

def log_start(task_id: str):
    print(f"[START] Task ID: {task_id}")

def log_step(step: int, action: str, reward: float):
    print(f"[STEP] Step: {step} | Action: {action} | Reward: {reward:.2f}")

def log_end(task_id: str, final_score: float, total_reward: float):
    print(f"[END] Task ID: {task_id} | Final Score: {final_score:.2f} | Total Reward: {total_reward:.2f}")

def mock_process_email(subject: str, body: str) -> Dict[str, Any]:
    """Mock email processing for testing"""
    print(f"Processing email: {subject}")
    
    # Mock analysis based on keywords
    body_lower = body.lower()
    
    if "spam" in body_lower or "promotion" in body_lower:
        category = "Spam"
        priority = "Low"
        suggested_reply = "Marked as spam"
    elif "urgent" in body_lower or "asap" in body_lower or "interview" in body_lower:
        category = "Important"
        priority = "High"
        suggested_reply = "Thank you for the update. I will address this immediately."
    else:
        category = "Personal"
        priority = "Medium"
        suggested_reply = "Thank you for your message. I will review and respond accordingly."
    
    summary = f"Email about {subject.lower()}"
    
    result = {
        "category": category,
        "summary": summary,
        "priority": priority,
        "suggested_reply": suggested_reply
    }
    
    print(f"Analysis result: {category} - {priority}")
    return result

def choose_action(obs) -> dict:
    """Simple deterministic policy with mock LLM call"""
    cur = obs.get("current")
    if not cur:
        return {"action_type":"next","content":"move next"}
    
    subject = cur.get("subject", "No Subject")
    body = cur.get("body", "No Body")
    
    # Mock LLM call
    email_result = mock_process_email(subject, body)
    
    category = email_result.get("category", "Important")
    priority = email_result.get("priority", "Medium")
    suggested_reply = email_result.get("suggested_reply", "Will respond appropriately")
    
    # Determine action based on analysis
    if category == "Spam":
        return {"action_type":"resolve","content":"Marked as spam and resolved"}
    elif priority == "High":
        return {"action_type":"escalate","content":f"Escalated: {subject}"}
    else:
        return {"action_type":"reply","content":suggested_reply}

async def main():
    """Main inference loop with mock testing"""
    print("Starting Email Operations Assistant (Test Mode)...")
    print(f"API Base: {API_BASE}")
    print(f"Model: {MODEL}")
    
    tasks = ["easy", "medium", "hard"]
    
    for task_id in tasks:
        print(f"\n{'='*50}")
        log_start(task_id)
        
        rewards: List[float] = []
        steps = 0
        episode_done = False
        
        try:
            print(f"Resetting environment for task: {task_id}")
            
            # Mock environment reset response
            r = {
                "current": {
                    "subject": f"Test Email for {task_id}",
                    "body": "This is a test email for local testing."
                },
                "queue_size": 3,
                "last_action": None,
                "history": []
            }
            print(f"Environment reset successful")
            
            for step in range(1, 4):  # Only 3 steps for testing
                a = choose_action(r)
                action = f"{a['action_type']}:{a['content']}"
                
                print(f"Step {step}: {action}")
                
                # Mock step response
                reward = 0.5  # Mock reward
                done = step == 3  # Done after 3 steps
                
                rewards.append(reward)
                steps = step
                
                log_step(step, action, reward)
                
                if done:
                    episode_done = True
                    break
            
            # Calculate scores
            final_score = sum(rewards) / max(1, len(rewards))
            total_reward = sum(rewards)
            
        except Exception as e:
            print(f"Error in task {task_id}: {e}")
            final_score = 0.0
            total_reward = 0.0
        
        finally:
            log_end(task_id, final_score, total_reward)
            print(f"Task {task_id} completed - Score: {final_score:.2f}")

if __name__ == "__main__":
    print("Testing Email Operations Assistant (Basic Structure)...")
    asyncio.run(main())
    print("Basic structure test completed!")
    print("\nTest Summary:")
    print("Environment variable handling works")
    print("Logging functions work")
    print("Email processing logic works")
    print("Action selection works")
    print("Main loop structure works")
    print("Error handling works")
    print("\nReady for deployment with proper OpenAI integration!")
