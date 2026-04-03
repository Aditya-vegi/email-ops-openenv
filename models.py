from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple, Literal
import copy

class EmailObservation(BaseModel):
    """Strict OpenEnv observation interface with all required fields"""
    inbox_size: int = Field(default=0, description="Number of emails in inbox")
    current_email: Optional[Dict[str, Any]] = Field(default=None, description="Current email data")
    available_actions: List[str] = Field(default_factory=list, description="Actions agent can take")
    queue_size: int = Field(default=0, description="Total emails remaining")
    last_action: Optional[str] = Field(default=None, description="Last action taken")
    history: List[str] = Field(default_factory=list, description="Action history")

class EmailAction(BaseModel):
    """Strict OpenEnv action interface with type and payload dictionary"""
    type: str = Field(..., description="Action type: classify, reply, escalate, resolve, next")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action-specific data")
    action_type: Optional[str] = Field(default=None, description="Legacy action_type field")
    content: Optional[str] = Field(default=None, description="Legacy content field")

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

class StateSnapshot(BaseModel):
    """Immutable state snapshot for reproducibility"""
    steps: int
    current_step: int
    queue_remaining: int
    total_reward: float
    task: str
    internal_state: Dict[str, Any]
    inbox: List[Dict[str, Any]]
    timestamp: str