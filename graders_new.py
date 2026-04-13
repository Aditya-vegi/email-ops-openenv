from typing import Dict, Any
from models import Email, Action

# UNIVERSAL CLAMP - Use this everywhere
UNIVERSAL_EPSILON = 1e-9 

def clamp_score(value):
    """
    Forces any number to be strictly between 0 and 1.
    If input is 1.0, output is 0.999999999.
    If input is 0.0, output is 0.000000001.
    """
    try:
        val = float(value)
    except:
        return 0.5
    
    # Aggressive clamping to prevent ANY edge case
    if val <= 0.0:
        return 0.0 + UNIVERSAL_EPSILON
    if val >= 1.0:
        return 1.0 - UNIVERSAL_EPSILON
    return val

def grade_task_1(final_state: Dict[str, Any]) -> float:
    """Task 1: Easy Classification"""
    internal_state = final_state.get("internal_state", {})
    classified_emails = internal_state.get("classified_emails", [])
    
    if len(classified_emails) > 0:
        return clamp_score(0.99)
    else:
        return clamp_score(0.01)

def grade_task_2(final_state: Dict[str, Any]) -> float:
    """Task 2: Medium Reply"""
    internal_state = final_state.get("internal_state", {})
    replied_emails = internal_state.get("replied_emails", [])
    
    if len(replied_emails) > 0:
        return clamp_score(0.99)
    else:
        return clamp_score(0.01)

def grade_task_3(final_state: Dict[str, Any]) -> float:
    """Task 3: Hard Workflow"""
    internal_state = final_state.get("internal_state", {})
    
    escalated_emails = internal_state.get("escalated_emails", [])
    resolved_emails = internal_state.get("resolved_emails", [])
    
    email_1_escalated = 1 in escalated_emails
    email_2_resolved = 2 in resolved_emails
    email_3_resolved = 3 in resolved_emails
    
    # Calculate base score. Max possible is 1.0 (0.4+0.3+0.3)
    base_score = 0.01
    if email_1_escalated:
        base_score += 0.4
    if email_2_resolved:
        base_score += 0.3
    if email_3_resolved:
        base_score += 0.3
    
    # FIX: If the agent gets everything perfect, base_score is 1.0.
    # We MUST apply clamp_score here to clamp it to 0.999999999
    return clamp_score(base_score)

def grade_task(task_id: str, final_state: Dict[str, Any]) -> float:
    """Main grading function"""
    if task_id == "easy" or task_id == "1":
        return grade_task_1(final_state)
    elif task_id == "medium" or task_id == "2":
        return grade_task_2(final_state)
    elif task_id == "hard" or task_id == "3":
        return grade_task_3(final_state)
    else:
        return clamp_score(0.01)
