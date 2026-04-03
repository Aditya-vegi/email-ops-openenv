#!/usr/bin/env python3
"""
Agentic Evaluation Script for Phase 2
Tests standard LLM agents against the environment
"""

import json
import time
from typing import Dict, List, Optional
import requests
from baseline_agent import BaselineAgent

class LLMAgent:
    """Base class for LLM-based agents"""
    
    def __init__(self, name: str, base_url: str = "http://127.0.0.1:8000"):
        self.name = name
        self.base_url = base_url
        self.episode_history = []
    
    def reset_environment(self) -> Dict:
        """Reset the environment"""
        response = requests.post(f"{self.base_url}/reset")
        return response.json() if response.status_code == 200 else {}
    
    def take_action(self, action: Dict) -> Dict:
        """Take an action in the environment"""
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

class RuleBasedAgent(LLMAgent):
    """Simple rule-based agent as a comparison baseline"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        super().__init__("RuleBased", base_url)
    
    def generate_action(self, obs: Dict, task: str) -> Dict:
        if not obs.get("current"):
            return {"action_type": "next", "content": "Next email"}
        
        email = obs["current"]
        subject = email.get("subject", "").lower()
        
        if task == "easy":
            # Simple priority classification
            if "urgent" in subject or "down" in subject:
                return {"action_type": "classify", "content": "urgent"}
            elif "invoice" in subject:
                return {"action_type": "classify", "content": "normal"}
            else:
                return {"action_type": "classify", "content": "low"}
        
        elif task == "medium":
            # Simple reply generation
            return {"action_type": "reply", "content": "Thank you for your message. I am working on it."}
        
        else:  # hard
            # Simple escalation logic
            if email.get("sender_role") == "boss":
                return {"action_type": "escalate", "content": "Escalating to management"}
            else:
                return {"action_type": "resolve", "content": "Resolving this issue"}

class RandomAgent(LLMAgent):
    """Random action agent for variance testing"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        super().__init__("Random", base_url)
        import random
        self.random = random
    
    def generate_action(self, obs: Dict, task: str) -> Dict:
        import random
        
        actions = ["classify", "reply", "escalate", "resolve", "next"]
        action_type = random.choice(actions)
        
        if action_type == "classify":
            content = random.choice(["urgent", "high", "normal", "low"])
        elif action_type == "reply":
            content = "Generic response message"
        elif action_type == "escalate":
            content = "Needs escalation"
        elif action_type == "resolve":
            content = "Issue resolved"
        else:
            content = "Next email"
        
        return {"action_type": action_type, "content": content}

class AgenticEvaluator:
    """Main evaluator for Phase 2 agentic evaluation"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.agents = [
            RuleBasedAgent(base_url),
            RandomAgent(base_url)
        ]
    
    def evaluate_agent(self, agent: LLMAgent, episodes_per_task: int = 5) -> Dict:
        """Evaluate a single agent across all tasks"""
        print(f"\nEvaluating {agent.name}...")
        
        tasks = ["easy", "medium", "hard"]
        all_results = []
        
        for task in tasks:
            task_results = []
            
            for episode in range(episodes_per_task):
                result = agent.run_episode(task)
                task_results.append(result)
                time.sleep(0.1)  # Brief pause
            
            # Calculate task statistics
            rewards = [r["total_reward"] for r in task_results]
            task_stats = {
                "task": task,
                "episodes": task_results,
                "mean_reward": sum(rewards) / len(rewards),
                "max_reward": max(rewards),
                "min_reward": min(rewards),
                "success_rate": sum(1 for r in task_results if r["success"]) / len(task_results),
                "std_dev": self._std_dev(rewards)
            }
            all_results.append(task_stats)
            
            print(f"  {task}: {task_stats['mean_reward']:.3f} ± {task_stats['std_dev']:.3f}")
        
        # Overall statistics
        all_rewards = [r["total_reward"] for task_result in all_results for r in task_result["episodes"]]
        
        return {
            "agent_name": agent.name,
            "task_results": all_results,
            "overall_mean_reward": sum(all_rewards) / len(all_rewards),
            "overall_success_rate": sum(1 for r in all_rewards if r > 0.5) / len(all_rewards),
            "overall_std_dev": self._std_dev(all_rewards),
            "total_episodes": len(all_rewards)
        }
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def run_full_evaluation(self, episodes_per_task: int = 5) -> Dict:
        """Run full agentic evaluation"""
        print("=" * 60)
        print("PHASE 2: AGENTIC EVALUATION")
        print("=" * 60)
        
        # Evaluate baseline agent first
        print("\n1. Evaluating Baseline Agent...")
        baseline_agent = BaselineAgent()
        baseline_results = baseline_agent.evaluate_all_tasks(episodes_per_task)
        
        # Evaluate other agents
        agent_results = {}
        for agent in self.agents:
            agent_results[agent.name] = self.evaluate_agent(agent, episodes_per_task)
        
        # Score variance check
        print("\n2. Score Variance Analysis...")
        all_agent_scores = []
        
        # Add baseline scores
        for task_data in baseline_results["task_results"].values():
            all_agent_scores.extend([r["total_reward"] for r in task_data["episodes"]])
        
        # Add other agent scores
        for agent_data in agent_results.values():
            for task_result in agent_data["task_results"]:
                all_agent_scores.extend([r["total_reward"] for r in task_result["episodes"]])
        
        overall_variance = self._std_dev(all_agent_scores)
        print(f"Overall Score Variance: {overall_variance:.3f}")
        
        # Comparison analysis
        print("\n3. Agent Comparison Analysis...")
        comparison = self._compare_agents(baseline_results, agent_results)
        
        results = {
            "baseline_results": baseline_results,
            "agent_results": agent_results,
            "variance_analysis": {
                "overall_std_dev": overall_variance,
                "all_scores": all_agent_scores
            },
            "comparison": comparison,
            "evaluation_metadata": {
                "episodes_per_task": episodes_per_task,
                "tasks_evaluated": ["easy", "medium", "hard"],
                "total_agents": len(self.agents) + 1  # +1 for baseline
            }
        }
        
        # Save results
        with open("agentic_evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nAgentic evaluation complete! Results saved to agentic_evaluation_results.json")
        print("Ready for Phase 3: Human Review")
        
        return results
    
    def _compare_agents(self, baseline: Dict, agents: Dict) -> Dict:
        """Compare performance between agents"""
        comparison = {}
        
        # Extract baseline overall score
        baseline_score = baseline["overall_mean_reward"]
        
        comparison["baseline_score"] = baseline_score
        comparison["agent_rankings"] = []
        
        # Rank agents by performance
        agent_scores = [(name, data["overall_mean_reward"]) for name, data in agents.items()]
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (name, score) in enumerate(agent_scores, 1):
            comparison["agent_rankings"].append({
                "rank": rank,
                "agent": name,
                "score": score,
                "difference_from_baseline": score - baseline_score
            })
        
        return comparison

def main():
    """Run agentic evaluation"""
    try:
        evaluator = AgenticEvaluator()
        results = evaluator.run_full_evaluation(episodes_per_task=3)
        
        print("\n" + "=" * 60)
        print("PHASE 2 EVALUATION SUMMARY")
        print("=" * 60)
        
        print(f"Baseline Performance: {results['baseline_results']['overall_mean_reward']:.3f}")
        print(f"Best Agent Performance: {results['comparison']['agent_rankings'][0]['score']:.3f}")
        print(f"Score Variance: {results['variance_analysis']['overall_std_dev']:.3f}")
        
        if results['comparison']['agent_rankings'][0]['score'] > results['baseline_results']['overall_mean_reward']:
            print("✓ Some agents outperform baseline - good for evaluation")
        else:
            print("⚠ Baseline remains strongest - consider more sophisticated agents")
        
    except Exception as e:
        print(f"Error running agentic evaluation: {e}")
        print("Make sure the environment server is running on http://127.0.0.1:8000")

if __name__ == "__main__":
    main()
