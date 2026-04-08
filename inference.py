import os
import asyncio
from typing import List, Dict, Any
import requests
import json

# EXACT OpenAI client initialization as required
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["API_KEY"],
    base_url=os.environ["API_BASE_URL"]
)

API_BASE = os.getenv("SPACE_URL", "https://ADITYA-VEGI-email-ops-openenv.hf.space")
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_STEPS = 15

def log_start(task_id: str):
    """Helper function to ensure exact logging format"""
    print(f"[START] Task ID: {task_id}")

def log_step(step: int, action: str, reward: float):
    """Helper function to ensure exact logging format"""
    print(f"[STEP] Step: {step} | Action: {action} | Reward: {reward:.2f}")

def log_end(task_id: str, final_score: float, total_reward: float):
    """Helper function to ensure exact logging format"""
    print(f"[END] Task ID: {task_id} | Final Score: {final_score:.2f} | Total Reward: {total_reward:.2f}")

def process_email_with_llm(subject: str, body: str) -> Dict[str, Any]:
    """
    Process email using LLM with strict error handling
    CRITICAL: This function MUST execute at least one API call
    """
    
    # Create the prompt for email processing
    prompt = f"""You are an email operations assistant. Analyze the following email and provide a structured response.

Email Subject: {subject}
Email Body: {body}

Classify this email into one category: Important, Spam, Promotion, or Personal
Generate a concise summary (max 50 words)
Assign priority: High, Medium, or Low
Generate a professional suggested reply

Return ONLY a JSON object with this exact format:
{{
    "category": "Important/Spam/Promotion/Personal",
    "summary": "concise summary",
    "priority": "High/Medium/Low", 
    "suggested_reply": "context-aware reply"
}}"""
    
    # Wrap ONLY API CALLS in try/except (NOT client initialization)
    try:
        # CRITICAL: This API call MUST execute
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an email operations assistant that returns structured JSON responses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        # Extract and parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to parse as JSON
        try:
            result = json.loads(content)
            # Validate required fields
            required_fields = ["category", "summary", "priority", "suggested_reply"]
            for field in required_fields:
                if field not in result:
                    result[field] = f"Missing {field}"
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails - but still return structured response
            return {
                "category": "Error",
                "summary": "Failed to parse LLM response",
                "priority": "Low",
                "suggested_reply": "System temporarily unavailable"
            }
            
    except Exception as e:
        # MANDATORY: Graceful error handling for API call failures
        return {
            "category": "Error",
            "summary": f"LLM call failed: {str(e)}",
            "priority": "Low",
            "suggested_reply": "System temporarily unavailable"
        }

def choose_action(obs) -> dict:
    """
    Simple deterministic policy that ALWAYS makes at least one LLM call
    """
    cur = obs.get("current")
    if not cur:
        return {"action_type":"next","content":"move next"}
    
    # CRITICAL: Extract email data and process with LLM
    subject = cur.get("subject", "No Subject")
    body = cur.get("body", "No Body")
    
    # ALWAYS make an LLM call - NO CONDITIONAL SKIPPING
    email_result = process_email_with_llm(subject, body)
    
    # Convert LLM result to action
    category = email_result.get("category", "Important")
    priority = email_result.get("priority", "Medium")
    suggested_reply = email_result.get("suggested_reply", "Will respond appropriately")
    
    # Determine action based on analysis
    if category == "Spam":
        return {"action_type":"resolve","content":"Marked as spam and resolved"}
    elif priority == "High" or "urgent" in body.lower() or "asap" in body.lower():
        return {"action_type":"escalate","content":f"Escalated: {subject}"}
    else:
        return {"action_type":"reply","content":suggested_reply}

async def main():
    """
    Main inference loop with strict compliance to all requirements
    """
    # Run through all 3 tasks
    tasks = ["easy", "medium", "hard"]
    
    for task_id in tasks:
        # MUST Print [START] Task ID: {id}
        log_start(task_id)
        
        rewards: List[float] = []
        steps = 0
        success = False
        episode_done = False
        
        try:
            # Reset environment for this task
            print(f"Resetting environment for task: {task_id}")
            r = requests.post(f"{API_BASE}/reset", json={"task": task_id}, timeout=30).json()
            print(f"Environment reset successful")
            
            for step in range(1, MAX_STEPS+1):
                a = choose_action(r)
                action = f"{a['action_type']}:{a['content']}"
                
                print(f"Step {step}: {action}")
                
                resp = requests.post(f"{API_BASE}/step", json=a, timeout=30).json()
                reward = float(resp.get("reward") or 0.0)
                done = bool(resp.get("done"))
                
                rewards.append(reward)
                steps = step
                
                # MUST print [STEP] Step: {n} | Action: {act} | Reward: {r:.2f}
                log_step(step, action, reward)
                
                r = resp.get("observation") or {}
                if done:
                    episode_done = True
                    break
            
            # CRITICAL: If agent doesn't finish in max_steps, manually print [END] tag
            if not episode_done:
                # Force end episode if max_steps reached
                try:
                    requests.post(f"{API_BASE}/step", json={"action_type":"next","content":"force_end"}, timeout=30).json()
                except:
                    pass  # Ignore errors for forced end
            
            # Calculate scores
            final_score = sum(rewards) / max(1, len(rewards))
            total_reward = sum(rewards)
            success = final_score >= 0.5
            
        except Exception as e:
            print(f"Error in task {task_id}: {e}")
            final_score = 0.0
            total_reward = 0.0
            success = False
            # Only log errors if absolutely necessary - validator doesn't like extra logs
            pass
        
        finally:
            # MUST print [END] Task ID: {id} | Final Score: {s:.2f} | Total Reward: {tr:.2f}
            log_end(task_id, final_score, total_reward)

if __name__ == "__main__":
    asyncio.run(main())
