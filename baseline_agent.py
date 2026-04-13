#!/usr/bin/env python3
"""
Baseline Agent for Email Operations Environment
Implements rule-based strategies for different task difficulties
"""

import requests
import json
from typing import Dict, List, Optional
import time

# UNIVERSAL CLAMP - Use this everywhere
UNIVERSAL_EPSILON = 1e-9

def clamp_score(value):
    """
    Forces any number to be strictly between 0 and 1.
    If input is 1.0, output is 0.999999999.
    If input is 0.0, output is 0.000000001.
    """
    try:
        val = float(value)
    except:
        return 0.5
    
    # Aggressive clamping to prevent ANY edge case
    if val <= 0.0:
        return 0.0 + UNIVERSAL_EPSILON
    if val >= 1.0:
        return 1.0 - UNIVERSAL_EPSILON
    return val

class LLMAgent:
    """Base class for LLM-based agents"""
    
    def __init__(self, name: str, base_url: str = "http://127.0.0.1:8000"):
        self.name = name
        self.base_url = base_url
        self.episode_history = []
    
    def reset_environment(self) -> Dict:
        """Reset environment"""
        response = requests.post(f"{self.base_url}/reset")
        return response.json() if response.status_code == 200 else {}
    
    def take_action(self, action: Dict) -> Dict:
        """Take an action in environment"""
        response = requests.post(f"{self.base_url}/step", json=action)
        return response.json() if response.status_code == 200 else {}
    
    def generate_action(self, obs: Dict, task: str) -> Dict:
        """Generate action based on observation - to be overridden"""
        raise NotImplementedError
    
    def run_episode(self, task: str = "hard", max_steps: int = 10) -> Dict:
        """Run a single episode"""
        obs = self.reset_environment()
        total_reward = 0
        steps = 0
        
        while steps < max_steps:
            action = self.generate_action(obs, task)
            result = self.take_action(action)
            
            reward = result.get("reward", 0)
            done = result.get("done", False)
            obs = result.get("observation", {})
            
            total_reward += reward
            steps += 1
            
            if done:
                break
        
        return {
            "agent": self.name,
            "task": task,
            "total_reward": total_reward,
            "steps": steps,
            "success": total_reward > 0.5
        }

class BaselineAgent(LLMAgent):
    """Baseline agent implementing rule-based strategies"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        super().__init__("BaselineAgent", base_url)
    
    def generate_action(self, obs: Dict, task: str) -> Dict:
        """Generate action based on observation and task type"""
        if not obs.get("current"):
            return {"action_type": "next", "content": "Next email"}
        
        email = obs["current"]
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()
        
        if task == "easy":
            return self._handle_easy_task(email, subject, body)
        elif task == "medium":
            return self._handle_medium_task(email, subject, body)
        else:  # hard
            return self._handle_hard_task(email, subject, body)
    
    def _handle_easy_task(self, email: Dict, subject: str, body: str) -> Dict:
        """Handle easy task: Classify email priority"""
        # Rule-based priority classification
        if any(keyword in subject + body for keyword in ["down", "asap", "urgent", "production", "server"]):
            priority = "urgent"
        elif any(keyword in subject + body for keyword in ["invoice", "payment", "clarification"]):
            priority = "normal"
        elif any(keyword in subject + body for keyword in ["minor", "ui", "bug", "alignment"]):
            priority = "low"
        else:
            priority = "normal"
        
        return {"action_type": "classify", "content": priority}
    
    def _handle_medium_task(self, email: Dict, subject: str, body: str) -> Dict:
        """Handle medium task: Generate polite, informative replies"""
        # Generate context-aware replies
        if "server down" in subject or "production" in subject:
            reply = "Hello, I'm investigating the server issue immediately. Our team is working on a resolution and I'll provide an update within 30 minutes."
        elif "invoice" in subject:
            reply = "Hello, thank you for your inquiry about invoice. I'm reviewing the details and will get back to you with the clarification you need by end of day."
        elif "bug" in subject:
            reply = "Hello, thank you for reporting the UI bug. I've logged this issue and our development team will investigate it in our next sprint. I'll keep you updated on the progress."
        else:
            reply = "Hello, I've received your message and I'm working on it. I'll provide you with an update soon."
        
        return {"action_type": "reply", "content": reply}
    
    def _handle_hard_task(self, email: Dict, subject: str, body: str) -> Dict:
        """Handle hard task: Multi-step workflow with escalation decisions"""
        sender = email.get("sender_role", "").lower()
        
        # Complex decision-making workflow
        if sender == "boss" or any(keyword in subject + body for keyword in ["production", "server", "down", "asap"]):
            # High-priority items requiring escalation
            return {"action_type": "escalate", "content": "Critical issue requiring immediate management attention and resource allocation"}
        elif any(keyword in subject + body for keyword in ["invoice", "payment", "clarification"]):
            # Client communications that can be resolved
            return {"action_type": "resolve", "content": "Providing detailed invoice clarification and resolving client inquiry"}
        elif any(keyword in subject + body for keyword in ["minor", "ui", "alignment"]):
            # Low-priority bugs that can be resolved
            return {"action_type": "resolve", "content": "Logging minor UI bug for future resolution, no immediate action required"}
        else:
            # Default to classification for unknown items
            return {"action_type": "classify", "content": "normal"}
    
    def evaluate_all_tasks(self, episodes_per_task: int = 3) -> Dict:
        """Evaluate baseline agent across all tasks"""
        print("=" * 60)
        print("BASELINE AGENT EVALUATION")
        print("=" * 60)
        
        tasks = ["easy", "medium", "hard"]
        results = {}
        
        for task in tasks:
            task_results = []
            print(f"\nEvaluating {task} task ({episodes_per_task} episodes)...")
            
            for episode in range(episodes_per_task):
                result = self.run_episode(task)
                task_results.append(result)
                time.sleep(0.5)  # Brief pause between episodes
            
            # Calculate task statistics
            rewards = [r["total_reward"] for r in task_results]
            success_rate = sum(1 for r in task_results if r["success"]) / len(task_results)
            
            results[task] = {
                "episodes": task_results,
                "mean_reward": clamp_score(sum(rewards) / len(rewards)),
                "max_reward": max(rewards),
                "min_reward": min(rewards),
                "success_rate": clamp_score(success_rate),
                "mean_steps": sum(r["steps"] for r in task_results) / len(task_results)
            }
            
            print(f"{task.upper()} RESULTS:")
            print(f"  Mean Reward: {results[task]['mean_reward']:.3f}")
            print(f"  Success Rate: {results[task]['success_rate']:.1%}")
            print(f"  Mean Steps: {results[task]['mean_steps']:.1f}")
        
        # Overall statistics
        all_rewards = []
        for task_data in results.values():
            all_rewards.extend([r["total_reward"] for r in task_data["episodes"]])
        
        overall_stats = {
            "overall_mean_reward": clamp_score(sum(all_rewards) / len(all_rewards)),
            "overall_success_rate": clamp_score(sum(1 for r in all_rewards if r > 0.5) / len(all_rewards)),
            "task_results": results
        }
        
        print(f"\nOVERALL RESULTS:")
        print(f"  Mean Reward: {overall_stats['overall_mean_reward']:.3f}")
        print(f"  Success Rate: {overall_stats['overall_success_rate']:.1%}")
        
        return overall_stats

def main():
    """Run baseline agent evaluation"""
    try:
        agent = BaselineAgent()
        results = agent.evaluate_all_tasks(episodes_per_task=3)
        
        # Save results for later comparison
        with open("baseline_results.json", "w") as f:
            # Convert non-serializable objects
            serializable_results = {
                "overall_mean_reward": results["overall_mean_reward"],
                "overall_success_rate": results["overall_success_rate"],
                "task_summary": {}
            }
            
            for task, data in results["task_results"].items():
                serializable_results["task_summary"][task] = {
                    "mean_reward": data["mean_reward"],
                    "max_reward": data["max_reward"],
                    "min_reward": data["min_reward"],
                    "success_rate": data["success_rate"],
                    "mean_steps": data["mean_steps"]
                }
            
            json.dump(serializable_results, f, indent=2)
        
        print(f"\nBaseline evaluation complete! Results saved to baseline_results.json")
        print("Ready for Phase 2: Agentic Evaluation")
        
    except Exception as e:
        print(f"Error running baseline agent: {e}")
        print("Make sure to start the environment server first: python app.py")

if __name__ == "__main__":
    main()
