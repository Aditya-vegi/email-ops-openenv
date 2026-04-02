from models import Observation, Action
from graders import grade_easy, grade_medium, grade_hard

class EmailEnv:

    def __init__(self, task="easy"):
        self.task = task
        self.step_count = 0
        self.done = False

    def reset(self):
        self.step_count = 0
        self.done = False

        self.current_email = Observation(
            email_id=1,
            subject="Server Down",
            body="Production server is down. Fix ASAP.",
            sender_role="boss"
        )
        return self.current_email

    def step(self, action: Action):
        self.step_count += 1

        if self.task == "easy":
            reward = grade_easy(action)
        elif self.task == "medium":
            reward = grade_medium(action)
        else:
            reward = grade_hard(action)

        if self.step_count >= 3:
            self.done = True

        return self.current_email, reward, self.done, {}
    
    def state(self):
        return {
            "step": self.step_count,
            "task": self.task
        }