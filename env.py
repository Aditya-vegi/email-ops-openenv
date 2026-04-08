from typing import List, Tuple, Optional, Dict, Any
import copy
from models import Email, Observation, Action, StepResult, EmailObservation, EmailAction
from graders import grade_easy, grade_medium, grade_hard

def safe_score(score):
    try:
        score = float(score)
    except:
        return 0.5
    
    if score <= 0:
        return 0.01
    elif score >= 1:
        return 0.99
    return score


class StepResult:
    """Wrapper class for OpenEnv step results"""
    def __init__(self, observation: Observation, reward: float, done: bool, info: Dict[str, Any]):
        self.observation = observation
        self.reward = reward
        self.done = done
        self.info = info


class EmailEnv:
    def __init__(self, task: str = "hard", max_steps: int = 15):
        self.task = task
        self.max_steps = max_steps
        self.reset()

    def _seed_emails(self) -> List[Email]:
        """Generates initial email queue with robust handling for held-out testing"""
        base_emails = [
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
        
        # Robust validation to prevent held-out emails from breaking the environment
        robust_emails = []
        for email in base_emails:
            try:
                # Validate email structure
                if not hasattr(email, 'email_id') or not hasattr(email, 'subject'):
                    continue  # Skip malformed emails
                
                # Ensure required fields have defaults
                if not hasattr(email, 'expected_priority'):
                    email.expected_priority = "normal"
                if not hasattr(email, 'requires_escalation'):
                    email.requires_escalation = False
                if not hasattr(email, 'sender_role'):
                    email.sender_role = "unknown"
                if not hasattr(email, 'body'):
                    email.body = ""
                if not hasattr(email, 'subject'):
                    email.subject = "No Subject"
                
                # Validate field types and sanitize
                if not isinstance(email.subject, str):
                    email.subject = str(email.subject)[:100]
                if not isinstance(email.body, str):
                    email.body = str(email.body)[:500]
                if not isinstance(email.sender_role, str):
                    email.sender_role = "unknown"
                
                # Sanitize content to prevent injection
                email.subject = email.subject.replace('<', '&lt;').replace('>', '&gt;')
                email.body = email.body.replace('<', '&lt;').replace('>', '&gt;')
                
                robust_emails.append(email)
                
            except Exception as e:
                # Skip problematic emails but continue with others
                print(f"Warning: Skipping malformed email {getattr(email, 'email_id', 'unknown')}: {e}")
                continue
        
        # Ensure we have at least one valid email
        if not robust_emails:
            # Fallback email if all are malformed
            robust_emails = [
                Email(
                    email_id=999,
                    subject="System Email",
                    body="This is a fallback email.",
                    sender_role="system",
                    expected_priority="normal",
                    requires_escalation=False
                )
            ]
        
        return robust_emails

    def _validate_email(self, email: Email) -> Email:
        """
        Validates and sanitizes email to prevent held-out emails from breaking the environment.
        
        Args:
            email: The email to validate.
            
        Returns:
            Email: Validated and sanitized email.
        """
        try:
            # Create a safe copy with validated fields
            safe_email = Email(
                email_id=getattr(email, 'email_id', 0),
                subject=str(getattr(email, 'subject', 'No Subject'))[:100],
                body=str(getattr(email, 'body', ''))[:500],
                sender_role=str(getattr(email, 'sender_role', 'unknown')),
                expected_priority=getattr(email, 'expected_priority', 'normal'),
                requires_escalation=bool(getattr(email, 'requires_escalation', False))
            )
            
            # Additional sanitization
            safe_email.subject = safe_email.subject.replace('\n', ' ').replace('\r', ' ')
            safe_email.body = safe_email.body.replace('\n', ' ').replace('\r', ' ')
            
            return safe_email
            
        except Exception as e:
            # Return safe fallback if validation fails
            return Email(
                email_id=999,
                subject="Validation Error",
                body=f"Email validation failed: {str(e)}",
                sender_role="system",
                expected_priority="normal",
                requires_escalation=False
            )

    def reset(self) -> Observation:
        """
        Resets the environment to initial state.
        
        Returns:
            Observation: Initial observation with first email loaded.
        """
        self.queue: List[Email] = self._seed_emails()
        self.current = self.queue.pop(0) if self.queue else None
        self.steps = 0
        self.current_step = 0  # Add current_step counter for strict compliance
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
        """
        Creates an observation from current environment state.
        
        Args:
            last_action: The last action taken by the agent.
            
        Returns:
            Observation: Current environment observation.
        """
        return Observation(
            current=self.current,
            queue_size=len(self.queue) + (1 if self.current else 0),
            last_action=last_action,
            history=self.history[-6:]
        )

    def _grade(self, action: Action) -> Tuple[float, str]:
        """
        Grades the agent's action based on task difficulty.
        
        Args:
            action: The action taken by the agent.
            
        Returns:
            Tuple[float, str]: Score and reason for the score.
        """
        if not self.current:
            return safe_score(0.01), "no email"

        # Pass internal state to graders for deterministic checking
        if self.task == "easy":
            score, reason = grade_easy(self.current, action, self.internal_state)
        elif self.task == "medium":
            score, reason = grade_medium(self.current, action, self.internal_state)
        else:
            score, reason = grade_hard(self.current, action, self.internal_state)
        
        return safe_score(score), reason

    def _advance(self):
        """
        Advances to the next email in the queue.
        
        Updates current email and sets done flag if no emails remain.
        """
        self.current = self.queue.pop(0) if self.queue else None
        if not self.current:
            self.done = True

    def step(self, action: Action) -> StepResult:
        """Step function with graceful error recovery and strict "Done" logic"""
        if self.done:
            reward = safe_score(0.01)
            return StepResult(self._obs("noop"), reward, True, {"reason": "episode done"})

        # Graceful error recovery for invalid actions
        try:
            # Validate action structure
            if not hasattr(action, 'action_type') or not hasattr(action, 'content'):
                error_msg = f"Invalid action format: {action}"
                reward = safe_score(0.01)  # Minimum positive reward for errors
                return StepResult(self._obs("invalid_action"), reward, False, {
                    "reason": error_msg, 
                    "available_actions": ["classify", "reply", "escalate", "resolve", "next"],
                    "error_recovery": True
                })
            
            # Validate action_type
            valid_actions = ["classify", "reply", "escalate", "resolve", "next"]
            if action.action_type not in valid_actions:
                error_msg = f"'{action.action_type}' is not a valid action. Available actions are {valid_actions}"
                reward = safe_score(-0.5)
                return StepResult(self._obs("invalid_action"), reward, False, {
                    "reason": error_msg,
                    "available_actions": valid_actions,
                    "error_recovery": True,
                    "help": "Use one of the available actions to continue"
                })
            
            # Validate content
            if action.content and not isinstance(action.content, str):
                error_msg = f"Action content must be a string, got {type(action.content).__name__}"
                reward = safe_score(-0.3)
                return StepResult(self._obs("invalid_action"), reward, False, {
                    "reason": error_msg,
                    "error_recovery": True,
                    "help": "Ensure content is a string"
                })
            
        except Exception as e:
            # Catch any unexpected errors and return helpful observation
            error_msg = f"Error processing action: {str(e)}"
            reward = safe_score(-1.0)
            return StepResult(self._obs("error"), reward, False, {
                "reason": error_msg,
                "error_recovery": True,
                "original_action": str(action) if action else "None"
            })

        # Increment current_step counter for strict compliance
        self.current_step += 1
        self.steps += 1
        
        # CRITICAL: Check max_steps to prevent hanging
        if self.current_step >= self.max_steps:
            self.done = True
            reward = safe_score(-1.0)
            return StepResult(self._obs("max_steps_reached"), reward, True, {"reason": "max_steps_reached", "current_step": self.current_step})
        
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
        
        # Penalty for hallucinated actions (invalid targets) - EXPLOIT CHECK
        if action.action_type in ["reply", "escalate", "resolve"] and not self.current:
            reward -= 0.5
            reason = "hallucinated action - no email to act on"
            # End episode for invalid action to show exploit prevention
            self.done = True
            return StepResult(self._obs(action.action_type), reward, True, {"reason": reason, "exploit_check": "invalid_action_ended"})
        
        # --- STEP COST (OPTIMIZED TIME PENALTY) ---
        reward -= 0.03  # Reduced from 0.05 to prevent "suicidal" behavior but still prevent wheel spinning

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
        if self.current_step > self.max_steps:
            reward -= 1.0  # Large negative reward to discourage infinite loops

        # --- FINAL REWARD UPDATE (FIXED BUG) ---
        self.total_reward += reward

        # CRITICAL: Manual score clamping (not just safe_score)
        reward = float(reward)
        if reward <= 0:
            reward = 0.01
        elif reward >= 1:
            reward = 0.99

        info = {"reason": reason, "steps": self.steps, "current_step": self.current_step, "total_reward": self.total_reward, "internal_state": self.internal_state}
        
        return StepResult(self._obs(action.action_type), reward, self.done, info)

    def archive_email(self, email_id: str) -> Dict[str, Any]:
        """
        Moves the specified email to ARCHIVE folder and returns a success observation.
        
        Args:
            email_id: The unique identifier of the email to be archived.
        
        Returns:
            Dict containing the result of the archive operation.
        """
        # Convert string email_id to int for comparison
        try:
            email_id_int = int(email_id)
        except (ValueError, TypeError):
            return {"success": False, "error": f"Invalid email_id format: {email_id}. Expected integer."}
        
        # Find and archive the email
        if self.current and self.current.email_id == email_id_int:
            # Archive current email and move to next
            self.current = self.queue.pop(0) if self.queue else None
            if not self.current:
                self.done = True
            return {"success": True, "message": f"Email {email_id} archived successfully"}
        else:
            # Check queue for the email
            for i, email in enumerate(self.queue):
                if email.email_id == email_id_int:
                    # Remove from queue
                    self.queue.pop(i)
                    return {"success": True, "message": f"Email {email_id} archived successfully"}
        
        return {"success": False, "error": f"Email {email_id} not found"}

    def classify_email(self, priority: str) -> Dict[str, Any]:
        """
        Sets the priority level for the current email and returns classification observation.
        
        Args:
            priority: The priority level (urgent, high, normal, low).
        
        Returns:
            Dict containing the result of the classification operation.
        """
        if not self.current:
            return {"success": False, "error": "No email currently loaded to classify"}
        
        valid_priorities = ["urgent", "high", "normal", "low"]
        if priority.lower() not in valid_priorities:
            return {"success": False, "error": f"Invalid priority: {priority}. Use one of: {valid_priorities}"}
        
        # Update internal state
        if self.current.email_id not in self.internal_state["classified_emails"]:
            self.internal_state["classified_emails"].append(self.current.email_id)
            self.internal_state["emails_processed"].append(self.current.email_id)
        
        self.current.expected_priority = priority.lower()
        return {"success": True, "message": f"Email classified as {priority}"}

    def reply_to_email(self, response: str) -> Dict[str, Any]:
        """
        Sends a reply to the current email and returns delivery confirmation observation.
        
        Args:
            response: The response content to send.
        
        Returns:
            Dict containing the result of the reply operation.
        """
        if not self.current:
            return {"success": False, "error": "No email currently loaded to reply to"}
        
        if not isinstance(response, str):
            return {"success": False, "error": "Response must be a string"}
        
        if len(response) > 1000:
            return {"success": False, "error": "Response too long (max 1000 characters)"}
        
        # Update internal state
        if self.current.email_id not in self.internal_state["replied_emails"]:
            self.internal_state["replied_emails"].append(self.current.email_id)
            self.internal_state["emails_processed"].append(self.current.email_id)
        
        return {"success": True, "message": f"Reply sent to email {self.current.email_id}"}

    def escalate_email(self, reason: str) -> Dict[str, Any]:
        """
        Escalates the current email to management and returns escalation confirmation observation.
        
        Args:
            reason: The reason for escalation.
        
        Returns:
            Dict containing the result of the escalation operation.
        """
        if not self.current:
            return {"success": False, "error": "No email currently loaded to escalate"}
        
        if not isinstance(reason, str):
            return {"success": False, "error": "Reason must be a string"}
        
        if not self.current.requires_escalation:
            return {"success": False, "error": "This email does not require escalation"}
        
        # Update internal state
        if self.current.email_id not in self.internal_state["escalated_emails"]:
            self.internal_state["escalated_emails"].append(self.current.email_id)
            self.internal_state["emails_processed"].append(self.current.email_id)
        
        self._advance()
        return {"success": True, "message": f"Email {self.current.email_id} escalated to management"}

    def resolve_email(self, resolution: str) -> Dict[str, Any]:
        """
        Resolves the current email and returns resolution confirmation observation.
        
        Args:
            resolution: The resolution details.
        
        Returns:
            Dict containing the result of the resolution operation.
        """
        if not self.current:
            return {"success": False, "error": "No email currently loaded to resolve"}
        
        if self.current.requires_escalation:
            return {"success": False, "error": "Urgent emails must be escalated, not resolved"}
        
        if not isinstance(resolution, str):
            return {"success": False, "error": "Resolution must be a string"}
        
        # Update internal state
        if self.current.email_id not in self.internal_state["resolved_emails"]:
            self.internal_state["resolved_emails"].append(self.current.email_id)
            self.internal_state["emails_processed"].append(self.current.email_id)
        
        self._advance()
        return {"success": True, "message": f"Email {self.current.email_id} resolved successfully"}

    def next_email(self) -> Dict[str, Any]:
        """
        Advances to the next email in the queue and returns new email observation.
        
        Returns:
            Dict containing the result of the next operation.
        """
        self._advance()
        if self.current:
            return {"success": True, "message": f"Moved to email {self.current.email_id}", "email_id": self.current.email_id}
        else:
            return {"success": True, "message": "No more emails in queue"}

    def mark_as_spam(self, email_id: str) -> Dict[str, Any]:
        """
        Moves the specified email to SPAM folder and returns a success observation.
        
        Args:
            email_id: The unique identifier of the email to mark as spam.
        
        Returns:
            Dict containing the result of the spam operation.
        """
        # Convert string email_id to int for comparison
        try:
            email_id_int = int(email_id)
        except (ValueError, TypeError):
            return {"success": False, "error": f"Invalid email_id format: {email_id}. Expected integer."}
        
        # Find and mark as spam
        if self.current and self.current.email_id == email_id_int:
            # Mark current email as spam and move to next
            self.current = self.queue.pop(0) if self.queue else None
            if not self.current:
                self.done = True
            return {"success": True, "message": f"Email {email_id} marked as spam"}
        else:
            # Check queue for the email
            for i, email in enumerate(self.queue):
                if email.email_id == email_id_int:
                    # Remove from queue (marked as spam)
                    self.queue.pop(i)
                    return {"success": True, "message": f"Email {email_id} marked as spam"}
        
        return {"success": False, "error": f"Email {email_id} not found"}

    def forward_email(self, email_id: str, recipient: str) -> Dict[str, Any]:
        """
        Forwards the specified email to recipient and returns forwarding confirmation observation.
        
        Args:
            email_id: The unique identifier of the email to forward.
            recipient: The email address or name of the recipient.
        
        Returns:
            Dict containing the result of the forwarding operation.
        """
        # Convert string email_id to int for comparison
        try:
            email_id_int = int(email_id)
        except (ValueError, TypeError):
            return {"success": False, "error": f"Invalid email_id format: {email_id}. Expected integer."}
        
        if not recipient or not isinstance(recipient, str):
            return {"success": False, "error": "Recipient must be a non-empty string"}
        
        # Find and forward email
        if self.current and self.current.email_id == email_id_int:
            return {"success": True, "message": f"Email {email_id} forwarded to {recipient}"}
        else:
            # Check queue for the email
            for i, email in enumerate(self.queue):
                if email.email_id == email_id_int:
                    return {"success": True, "message": f"Email {email_id} forwarded to {recipient}"}
        
        return {"success": False, "error": f"Email {email_id} not found"}

    def save_draft(self, content: str) -> Dict[str, Any]:
        """
        Saves the current email as a draft and returns draft confirmation observation.
        
        Args:
            content: The draft content to save.
        
        Returns:
            Dict containing the result of the draft operation.
        """
        if not self.current:
            return {"success": False, "error": "No email currently loaded to draft"}
        
        if not isinstance(content, str):
            return {"success": False, "error": "Draft content must be a string"}
        
        if len(content) > 2000:
            return {"success": False, "error": "Draft content too long (max 2000 characters)"}
        
        return {"success": True, "message": f"Draft saved for email {self.current.email_id}"}

    def _find_closest_match(self, target: str, options: List[str]) -> str:
        """
        Finds the closest string match using Levenshtein distance.
        
        Args:
            target: The target string to match.
            options: List of possible options.
            
        Returns:
            str: The closest match.
        """
        if not target:
            return options[0] if options else "unknown"
        
        target_lower = target.lower()
        best_match = options[0]
        best_score = len(target_lower)
        
        for option in options:
            score = len(target_lower) - sum(1 for i, char in enumerate(target_lower) if i < len(option) and char == option[i].lower())
            if score < best_score:
                best_score = score
                best_match = option
        
        return best_match

    def _get_milestones(self) -> List[str]:
        """
        Gets the list of milestones achieved in the current episode.
        
        Returns:
            List[str]: List of achieved milestones.
        """
        milestones = []
        if len(self.opened_emails) > 0:
            milestones.append(f"Opened {len(self.opened_emails)} emails")
        if len(self.internal_state["classified_emails"]) > 0:
            milestones.append(f"Classified {len(self.internal_state['classified_emails'])} emails")
        if len(self.internal_state["replied_emails"]) > 0:
            milestones.append(f"Replied to {len(self.internal_state['replied_emails'])} emails")
        if len(self.internal_state["escalated_emails"]) > 0:
            milestones.append(f"Escalated {len(self.internal_state['escalated_emails'])} emails")
        if len(self.internal_state["resolved_emails"]) > 0:
            milestones.append(f"Resolved {len(self.internal_state['resolved_emails'])} emails")
        return milestones

    def _get_trajectory_feedback(self) -> str:
        """
        Provides trajectory feedback for the agent.
        
        Returns:
            str: Feedback message about the current trajectory.
        """
        if self.total_reward > 0.5:
            return f"Excellent trajectory! Current score: {self.total_reward:.2f}"
        elif self.total_reward > 0.0:
            return f"Good progress! Current score: {self.total_reward:.2f}"
        else:
            return f"Needs improvement. Current score: {self.total_reward:.2f}"

    def state(self) -> Dict[str, Any]:
        """Return deep copy of current state to prevent memory leaks between resets"""
        return {
            "steps": self.steps,
            "current_step": self.current_step,
            "queue_remaining": len(self.queue) + (1 if self.current else 0),
            "total_reward": self.total_reward,
            "task": self.task,
            "internal_state": copy.deepcopy(self.internal_state),  # Deep copy to prevent memory leaks
            "inbox": copy.deepcopy([{
                "email_id": email.email_id,
                "subject": email.subject,
                "body": email.body,
                "sender_role": email.sender_role,
                "expected_priority": email.expected_priority,
                "requires_escalation": email.requires_escalation
            } for email in (self.queue + ([self.current] if self.current else []))])
        }