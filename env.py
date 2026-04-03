from typing import List, Tuple, Optional, Dict, Any
from models import Email, Observation, Action, StepResult, EmailObservation, EmailAction
from graders import grade_easy, grade_medium, grade_hard


class StepResult:
    """Wrapper class for OpenEnv step results"""
    def __init__(self, observation: Observation, reward: float, done: bool, info: Dict[str, Any]):
        self.observation = observation
        self.reward = reward
        self.done = done
        self.info = info


class EmailEnv:
    def __init__(self, task: str = "hard", max_steps: int = 8):
        self.task = task
        self.max_steps = max_steps
        self.reset()

    def _seed_emails(self) -> List[Email]:
        return [
            Email(
                email_id=1,
                subject="Production server down",
                body="Prod is down. Fix ASAP.",
                sender_role="boss",
                expected_priority="urgent",
                requires_escalation=True
            ),
            Email(
                email_id=2,
                subject="Invoice clarification",
                body="Need details on last invoice.",
                sender_role="client",
                expected_priority="normal",
                requires_escalation=False
            ),
            Email(
                email_id=3,
                subject="Minor UI bug",
                body="Alignment issue on mobile.",
                sender_role="client",
                expected_priority="low",
                requires_escalation=False
            ),
        ]

    def reset(self) -> Observation:
        self.queue: List[Email] = self._seed_emails()
        self.current = self.queue.pop(0) if self.queue else None
        self.steps = 0
        self.done = False
        self.history: List[str] = []
        self.total_reward = 0.0
        self.opened_emails = set()  # Track which emails have been opened
        
        # Internal state tracking for deterministic grading
        self.internal_state = {
            "emails_processed": [],
            "escalated_emails": [],
            "resolved_emails": [],
            "classified_emails": [],
            "replied_emails": []
        }
        
        return self._obs(last_action=None)

    def _obs(self, last_action: str | None) -> Observation:
        return Observation(
            current=self.current,
            queue_size=len(self.queue) + (1 if self.current else 0),
            last_action=last_action,
            history=self.history[-6:]
        )

    def _grade(self, action: Action) -> Tuple[float, str]:
        if not self.current:
            return 0.0, "no email"

        # Pass internal state to gradaders for deterministic checking
        if self.task == "easy":
            return grade_easy(self.current, action, self.internal_state)
        elif self.task == "medium":
            return grade_medium(self.current, action, self.internal_state)
        else:
            return grade_hard(self.current, action, self.internal_state)

    def _advance(self):
        self.current = self.queue.pop(0) if self.queue else None
        if not self.current:
            self.done = True

    def step(self, action: Action) -> StepResult:
        """Step function returning StepResult object for OpenEnv compliance"""
        if self.done:
            return StepResult(self._obs("noop"), 0.0, True, {"reason": "episode done"})

        self.steps += 1
        score, reason = self._grade(action)

        # --- ENHANCED REWARD SIGNAL ---
        reward = 0.0
        
        # Reward for opening unread email (first interaction)
        if self.current and self.current.email_id not in self.opened_emails:
            reward += 0.1
            self.opened_emails.add(self.current.email_id)
            reason = f"opened email: {reason}"
        
        # Base score from grader
        reward += score
        
        # Bonus for correct category identification
        if action.action_type == "classify" and score > 0.5:
            reward += 0.4
            reason = f"correct classification: {reason}"
        
        # Penalty for hallucinating actions (invalid targets) - EXPLOIT CHECK
        if action.action_type in ["reply", "escalate", "resolve"] and not self.current:
            reward -= 0.5
            reason = "hallucinated action - no email to act on"
            # End episode for invalid action to show exploit prevention
            self.done = True
            return StepResult(self._obs(action.action_type), reward, True, {"reason": reason, "exploit_check": "invalid_action_ended"})
        
        # --- STEP COST (OPTIMIZED TIME PENALTY) ---
        reward -= 0.03  # Reduced from 0.05 to prevent "suicidal" behavior but still prevent wheel spinning

        # --- INVALID ACTION PENALTY ---
        valid_actions = ["classify", "reply", "escalate", "resolve", "next"]
        if action.action_type not in valid_actions:
            reward -= 0.5  # Increased penalty for invalid actions
            reason = "invalid action type"
            # End episode for invalid action to show exploit prevention
            self.done = True
            return StepResult(self._obs(action.action_type), reward, True, {"reason": reason, "exploit_check": "invalid_action_ended"})
            # Log security violation attempt
            print(f"SECURITY: Invalid action attempted: {action.action_type}")

        # --- CONTENT VALIDATION ---
        if action.content:
            # Check for potential injection attempts
            if len(action.content) > 500:  # Reasonable content length limit
                reward -= 0.3
                reason = "content too long - potential injection"
            # Check for suspicious patterns
            suspicious_patterns = ["<script>", "javascript:", "eval(", "exec("]
            if any(pattern in action.content.lower() for pattern in suspicious_patterns):
                reward -= 0.8
                reason = "suspicious content detected"
                print(f"SECURITY: Suspicious content detected: {action.content[:100]}")

        # --- LOOP/SPAM PENALTY ---
        if len(self.history) >= 3 and self.history[-1] == self.history[-2] == self.history[-3]:
            reward -= 0.5  # Increased penalty for repeated actions
            reason = "excessive repetition detected"

        # --- WORKFLOW LOGIC & INTERNAL STATE UPDATES ---
        if self.current:
            email_id = self.current.email_id
            
            if action.action_type == "classify":
                # Update internal state for deterministic grading
                if email_id not in self.internal_state["classified_emails"]:
                    self.internal_state["classified_emails"].append(email_id)
                    self.internal_state["emails_processed"].append(email_id)
                
                if self.current.requires_escalation:
                    reward -= 0.4   # wrong action for urgent email
                else:
                    reward += 0.2   # correct for routine email
                    
            elif action.action_type == "reply":
                # Update internal state
                if email_id not in self.internal_state["replied_emails"]:
                    self.internal_state["replied_emails"].append(email_id)
                    self.internal_state["emails_processed"].append(email_id)
                
                if self.current.requires_escalation:
                    reward -= 0.3   # wrong action for urgent email
                else:
                    reward += 0.2   # appropriate for routine email
                    
            elif action.action_type == "escalate":
                # Update internal state for deterministic checking
                if email_id not in self.internal_state["escalated_emails"]:
                    self.internal_state["escalated_emails"].append(email_id)
                    self.internal_state["emails_processed"].append(email_id)
                
                if self.current.requires_escalation:
                    reward += 0.3   # correct escalation
                    self._advance()
                else:
                    reward -= 0.3   # unnecessary escalation
                    
            elif action.action_type == "resolve":
                # Update internal state
                if email_id not in self.internal_state["resolved_emails"]:
                    self.internal_state["resolved_emails"].append(email_id)
                    self.internal_state["emails_processed"].append(email_id)
                
                if self.current.requires_escalation:
                    reward -= 0.4   # wrong resolve
                else:
                    reward += 0.2   # correct resolve
                    self._advance()

        # --- TRACK HISTORY ---
        self.history.append(action.action_type)

        # --- EPISODE END ---
        if self.steps >= self.max_steps or not self.current:
            self.done = True

            # success / failure bonus
            if self.total_reward > 1.5:
                reward += 0.3
            else:
                reward -= 0.2
        
        # --- LARGE PENALTY FOR EXCEEDING MAX STEPS ---
        if self.steps > self.max_steps:
            reward -= 1.0  # Large negative reward to discourage infinite loops

        # --- FINAL REWARD UPDATE (FIXED BUG) ---
        self.total_reward += reward

        # Clamp reward to reasonable range
        reward = max(-1.0, min(1.0, reward))

        info = {"reason": reason, "steps": self.steps, "total_reward": self.total_reward, "internal_state": self.internal_state}
        
        return StepResult(self._obs(action.action_type), reward, self.done, info)

    def state(self) -> Dict[str, Any]:
        return {
            "steps": self.steps,
            "queue_remaining": len(self.queue) + (1 if self.current else 0),
            "total_reward": self.total_reward,
            "task": self.task,
            "internal_state": self.internal_state
        }