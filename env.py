from typing import List, Tuple
from models import Email, Observation, Action, StepResult
from graders import grade_easy, grade_medium, grade_hard


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

        if self.task == "easy":
            return grade_easy(self.current, action)
        elif self.task == "medium":
            return grade_medium(self.current, action)
        else:
            return grade_hard(self.current, action)

    def _advance(self):
        self.current = self.queue.pop(0) if self.queue else None
        if not self.current:
            self.done = True

    def step(self, action: Action) -> StepResult:
        if self.done:
            return StepResult(
                observation=self._obs("noop"),
                reward=0.0,
                done=True,
                info={}
            )

        self.steps += 1
        score, reason = self._grade(action)

        # --- BASE REWARD ---
        reward = score

        # --- STEP COST ---
        reward -= 0.05

        # --- INVALID ACTION PENALTY ---
        valid_actions = ["classify", "reply", "escalate", "resolve", "next"]
        if action.action_type not in valid_actions:
            reward -= 0.3
            reason = "invalid action"

        # --- SKIP PENALTY ---
        if action.action_type == "next":
            reward -= 0.2

        # --- LOOP/SPAM PENALTY ---
        if len(self.history) >= 2 and self.history[-1] == self.history[-2] == action.action_type:
            reward -= 0.2

        # --- WORKFLOW LOGIC ---
        if self.current:
            if action.action_type == "resolve":
                if self.current.requires_escalation:
                    reward -= 0.4   # wrong resolve
                else:
                    reward += 0.2   # correct resolve
                    self._advance()

            elif action.action_type == "escalate":
                if self.current.requires_escalation:
                    reward += 0.3   # correct escalation
                    self._advance()
                else:
                    reward -= 0.3   # unnecessary escalation

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

        # --- FINAL REWARD UPDATE (FIXED BUG) ---
        self.total_reward += reward

        return StepResult(
            observation=self._obs(action.action_type),
            reward=float(max(-1.0, min(1.0, reward))),
            done=self.done,
            info={"reason": reason}
        )

    def state(self):
        return {
            "steps": self.steps,
            "queue_remaining": len(self.queue) + (1 if self.current else 0),
            "total_reward": self.total_reward,
            "task": self.task
        }