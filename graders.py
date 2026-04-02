from typing import Tuple
from models import Email, Action

def _norm(s: str) -> str:
    return (s or "").lower()

def grade_easy(email: Email, action: Action) -> Tuple[float, str]:
    # Expect: classify priority
    txt = _norm(action.content)
    score = 0.0

    if action.action_type != "classify":
        return 0.0, "wrong action_type"

    # exact or synonym matches
    if email.expected_priority in txt:
        score = 1.0
    else:
        # partial: urgency cues
        if "urgent" in txt or "asap" in txt:
            score = 0.6 if email.expected_priority in ["high","urgent"] else 0.2
        elif "low" in txt:
            score = 0.6 if email.expected_priority == "low" else 0.2
        elif "normal" in txt:
            score = 0.6 if email.expected_priority == "normal" else 0.2

    return score, "priority grading"

def grade_medium(email: Email, action: Action) -> Tuple[float, str]:
    # Expect: polite, informative reply
    txt = _norm(action.content)
    if action.action_type != "reply":
        return 0.0, "wrong action_type"

    score = 0.0
    # tone
    if any(k in txt for k in ["hi", "hello", "thanks", "thank you"]):
        score += 0.2
    # acknowledgement + action
    if any(k in txt for k in ["working", "fix", "investigat", "looking into"]):
        score += 0.4
    # timeline / ownership
    if any(k in txt for k in ["soon", "timeline", "update", "team"]):
        score += 0.2
    # relevance to severity
    if email.expected_priority in ["high","urgent"] and any(k in txt for k in ["urgent","asap","priority"]):
        score += 0.2

    return min(score, 1.0), "reply grading"

def grade_hard(email: Email, action: Action) -> Tuple[float, str]:
    # Expect: correct decision flow across steps
    txt = _norm(action.content)
    score = 0.0

    if action.action_type == "classify":
        if email.expected_priority in txt:
            score += 0.4
        elif "urgent" in txt and email.expected_priority in ["high","urgent"]:
            score += 0.2

    elif action.action_type == "reply":
        if any(k in txt for k in ["working","fix","investigat"]):
            score += 0.3
        if any(k in txt for k in ["team","update","timeline"]):
            score += 0.2

    elif action.action_type == "escalate":
        if email.requires_escalation:
            score += 0.5
        else:
            score -= 0.3

    elif action.action_type == "resolve":
        # only correct if not requiring escalation
        if not email.requires_escalation:
            score += 0.4
        else:
            score -= 0.4

    return max(0.0, min(score, 1.0)), "workflow grading"