from pydantic import BaseModel
from typing import Optional

class Observation(BaseModel):
    email_id: int
    subject: str
    body: str
    sender_role: str

class Action(BaseModel):
    action_type: str  # classify / reply / escalate
    content: str

class Reward(BaseModel):
    score: float
    feedback: Optional[str] = None