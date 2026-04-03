from typing import Dict, Any
from models import Email, Action

def grade_task_1(final_state: Dict[str, Any]) -> float:
    """Task 1: Easy Classification - Deterministic boolean grading
    
    Returns 1.0 only if email was properly classified in internal state
    """
    internal_state = final_state.get("internal_state", {})
    
    # Check if any emails were classified
    classified_emails = internal_state.get("classified_emails", [])
    
    # Must classify at least one email correctly
    if len(classified_emails) > 0:
        return 1.0
    else:
        return 0.0

def grade_task_2(final_state: Dict[str, Any]) -> float:
    """Task 2: Medium Reply - Deterministic boolean grading
    
    Returns 1.0 only if email was replied to in internal state
    """
    internal_state = final_state.get("internal_state", {})
    
    # Check if any emails were replied to
    replied_emails = internal_state.get("replied_emails", [])
    
    # Must reply to at least one email
    if len(replied_emails) > 0:
        return 1.0
    else:
        return 0.0

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
    score = 0.0
    if email_1_escalated:
        score += 0.4  # Correct escalation of urgent email
    if email_2_resolved:
        score += 0.3  # Correct resolution of invoice email
    if email_3_resolved:
        score += 0.3  # Correct resolution of bug email
    
    return score

def grade_task(task_id: str, final_state: Dict[str, Any]) -> float:
    """Main grading function - purely programmatic, no LLM"""
    
    if task_id == "easy" or task_id == "1":
        return grade_task_1(final_state)
    elif task_id == "medium" or task_id == "2":
        return grade_task_2(final_state)
    elif task_id == "hard" or task_id == "3":
        return grade_task_3(final_state)
    else:
        return 0.0  # Unknown task
