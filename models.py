from pydantic import BaseModel
from typing import List, Optional, Literal

Priority = Literal["low", "normal", "high", "urgent"]
ActionType = Literal["classify", "reply", "escalate", "resolve", "next"]

class Email(BaseModel):
    email_id: int
    subject: str
    body: str
    sender_role: str  # boss/client/vendor
    expected_priority: Priority
    requires_escalation: bool

class Observation(BaseModel):
    current: Optional[Email]
    queue_size: int
    last_action: Optional[str] = None
    history: List[str] = []

class Action(BaseModel):
    action_type: ActionType
    content: str  # free text (classification label / reply / reason)

class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict = {}