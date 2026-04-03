from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple, Literal

class EmailObservation(BaseModel):
    inbox_count: int
    current_email_body: Optional[str]
    folders: List[str]

class EmailAction(BaseModel):
    action_type: str  # e.g., "MOVE", "REPLY", "DELETE"
    target_id: str
    payload: Optional[str] = None

# Legacy models for backward compatibility
class Email(BaseModel):
    email_id: int
    subject: str
    body: str
    sender_role: str
    expected_priority: Optional[str] = None
    requires_escalation: Optional[bool] = None

class Observation(BaseModel):
    current: Optional[Email] = None
    queue_size: int = 0
    last_action: Optional[str] = None
    history: List[str] = []

ActionType = Literal["classify", "reply", "escalate", "resolve", "next"]

class Action(BaseModel):
    action_type: ActionType
    content: str

class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]