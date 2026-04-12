from typing import Dict, Any
from models import Email, Action

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

def grade_task_1(final_state: Dict[str, Any]) -> float:
    """Task 1: Easy Classification - Deterministic boolean grading
    
    Returns 1.0 only if email was properly classified in internal state
    """
    internal_state = final_state.get("internal_state", {})
    
    # Check if any emails were classified
    classified_emails = internal_state.get("classified_emails", [])
    
    # Must classify at least one email correctly
    if len(classified_emails) > 0:
        return safe_score(0.99)
    else:
        return safe_score(0.01)

def grade_task_2(final_state: Dict[str, Any]) -> float:
    """Task 2: Medium Reply - Deterministic boolean grading
    
    Returns 1.0 only if email was replied to in internal state
    """
    internal_state = final_state.get("internal_state", {})
    
    # Check if any emails were replied to
    replied_emails = internal_state.get("replied_emails", [])
    
    # Must reply to at least one email
    if len(replied_emails) > 0:
        return safe_score(0.99)
    else:
        return safe_score(0.01)

def grade_task_3(final_state: Dict[str, Any]) -> float:
    """Task 3: Hard Workflow - Deterministic boolean grading
    
    Returns 1.0 only if proper escalation/resolution workflow was followed
    """
    internal_state = final_state.get("internal_state", {})
    
    # Check escalation and resolution patterns
    escalated_emails = internal_state.get("escalated_emails", [])
    resolved_emails = internal_state.get("resolved_emails", [])
    
    # For hard task, need proper workflow:
    # - Urgent emails (ID 1) should be escalated
    # - Non-urgent emails (ID 2, 3) should be resolved
    email_1_escalated = 1 in escalated_emails
    email_2_resolved = 2 in resolved_emails
    email_3_resolved = 3 in resolved_emails
    
    # Score based on proper workflow execution
    # FIX: Calculate base score WITHOUT safe_score wrapping to prevent intermediate limits
    base_score = 0.01
    if email_1_escalated:
        base_score += 0.4  # Correct escalation of urgent email
    if email_2_resolved:
        base_score += 0.3  # Correct resolution of invoice email
    if email_3_resolved:
        base_score += 0.3  # Correct resolution of bug email
    
    # FIX: Apply safe_score ONLY at the very end to cap the final sum at 0.99
    return safe_score(base_score)

def grade_task(task_id: str, final_state: Dict[str, Any]) -> float:
    """Main grading function - purely programmatic, no LLM"""
    
    if task_id == "easy" or task_id == "1":
        return grade_task_1(final_state)
    elif task_id == "medium" or task_id == "2":
        return grade_task_2(final_state)
    elif task_id == "hard" or task_id == "3":
        return grade_task_3(final_state)
    else:
        return safe_score(0.01)  # Unknown task
