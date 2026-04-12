from typing import Tuple, Dict, Any
from models import Email, Action

# EPSILON is a tiny number to ensure strict inequality (0 < score < 1)
EPSILON = 1e-9 

def safe_score(score):
    """Ensures the score is strictly between 0 and 1."""
    try:
        score = float(score)
    except:
        return 0.5
    
    # Use EPSILON to handle edge cases where score is exactly 0.0 or 1.0
    if score <= 0.0:
        return 0.0 + EPSILON  # Returns 0.000000001
    elif score >= 1.0:
        return 1.0 - EPSILON  # Returns 0.999999999
    return score

# Renamed functions to force cache refresh in the evaluation system
def grade_easy_v2(email: Email, action: Action, internal_state: Dict[str, Any]) -> Tuple[float, str]:
    """Easy task: Classify email priority correctly"""
    if action.action_type != "classify":
        return safe_score(0.01), "wrong action type"
    
    email_id = email.email_id
    if email_id not in internal_state.get("classified_emails", []):
        return safe_score(0.01), "email not marked as classified in internal state"
    
    expected = email.expected_priority
    actual = action.content.lower()
    
    if actual == expected:
        return safe_score(0.99), f"correct priority: {expected}"
    elif expected in actual or actual in expected:
        return safe_score(0.5), f"partial match: {actual} vs {expected}"
    else:
        return safe_score(0.01), f"wrong priority: {actual} vs {expected}"

def grade_medium_v2(email: Email, action: Action, internal_state: Dict[str, Any]) -> Tuple[float, str]:
    """Medium task: Generate appropriate reply"""
    if action.action_type != "reply":
        return safe_score(0.01), "wrong action type"
    
    email_id = email.email_id
    if email_id not in internal_state.get("replied_emails", []):
        return safe_score(0.01), "email not marked as replied in internal state"
    
    reply = action.content.lower()
    subject = email.subject.lower()
    
    if "server down" in subject and any(word in reply for word in ["investigating", "working", "update", "30 minutes"]):
        return safe_score(0.99), "appropriate server issue response"
    elif "invoice" in subject and any(word in reply for word in ["invoice", "details", "clarification", "end of day"]):
        return safe_score(0.99), "appropriate invoice response"
    elif "bug" in subject and any(word in reply for word in ["logged", "development", "sprint", "progress"]):
        return safe_score(0.99), "appropriate bug report response"
    elif len(reply) > 20 and any(word in reply for word in ["hello", "thank", "working", "update"]):
        return safe_score(0.5), "generic but professional response"
    else:
        return safe_score(0.01), "inappropriate or insufficient response"

def grade_hard_v2(email: Email, action: Action, internal_state: Dict[str, Any]) -> Tuple[float, str]:
    """Hard task: Multi-step workflow with dependency checking"""
    
    email_id = email.email_id
    step1_score = 0.0
    step2_score = 0.0
    step3_score = 0.0
    step1_reason = "N/A"
    step2_reason = "N/A"
    step3_reason = "N/A"
    
    # --- Step 1: Correct Action Type (Max 0.33) ---
    if email.requires_escalation:
        if action.action_type == "escalate":
            if email_id in internal_state.get("escalated_emails", []):
                step1_score = 0.33
                step1_reason = "correct escalation for urgent item"
            else:
                step1_score = 0.01
                step1_reason = "escalation action but not in internal state"
        elif action.action_type == "resolve":
            step1_score = 0.01
            step1_reason = "failed to escalate urgent item"
        else:
            step1_score = 0.1
            step1_reason = "suboptimal action for urgent item"
    else:
        if action.action_type == "resolve":
            if email_id in internal_state.get("resolved_emails", []):
                step1_score = 0.33
                step1_reason = "correct resolution for non-urgent item"
            else:
                step1_score = 0.01
                step1_reason = "resolution action but not in internal state"
        elif action.action_type == "escalate":
            step1_score = 0.01
            step1_reason = "unnecessary escalation of non-urgent item"
        else:
            step1_score = 0.1
            step1_reason = "suboptimal action for non-urgent item"
    
    # --- Step 2: Content Quality (Max 0.33) ---
    content = action.content.lower()
    
    if action.action_type == "escalate" and email.requires_escalation:
        if any(word in content for word in ["critical", "urgent", "immediate", "management", "attention"]):
            if email_id in internal_state.get("escalated_emails", []):
                step2_score = 0.33
                step2_reason = "proper escalation justification"
            else:
                step2_score = 0.2
                step2_reason = "good content but internal state mismatch"
        elif len(content) > 20:
            step2_score = 0.2
            step2_reason = "adequate escalation content"
    
    elif action.action_type == "resolve" and not email.requires_escalation:
        if "invoice" in email.subject.lower():
            if any(word in content for word in ["clarification", "details", "provided", "resolved"]):
                if email_id in internal_state.get("resolved_emails", []):
                    step2_score = 0.33
                    step2_reason = "proper invoice resolution"
                else:
                    step2_score = 0.2
                    step2_reason = "good content but internal state mismatch"
        elif "bug" in email.subject.lower():
            if any(word in content for word in ["logged", "future", "resolution", "minor"]):
                if email_id in internal_state.get("resolved_emails", []):
                    step2_score = 0.33
                    step2_reason = "proper bug handling"
                else:
                    step2_score = 0.2
                    step2_reason = "good content but internal state mismatch"
        elif len(content) > 15:
            step2_score = 0.2
            step2_reason = "adequate resolution content"
    
    # --- Step 3: Workflow Efficiency (Max 0.33) ---
    # Max sum is 0.99 (0.33 + 0.33 + 0.33)
    if action.action_type in ["escalate", "resolve"]:
        if email.requires_escalation and action.action_type == "escalate":
            if email_id in internal_state.get("escalated_emails", []):
                step3_score = 0.33
                step3_reason = "efficient urgent item handling"
        elif not email.requires_escalation and action.action_type == "resolve":
            if email_id in internal_state.get("resolved_emails", []):
                step3_score = 0.33
                step3_reason = "efficient routine item handling"
    
    # --- Final Calculation ---
    # Sum is at most 0.99
    total_score = step1_score + step2_score + step3_score
    
    # Apply safe_score ONLY once at the end
    final_score = safe_score(total_score)
    
    combined_reason = f"Step1({step1_score:.2f}): {step1_reason} | Step2({step2_score:.2f}): {step2_reason} | Step3({step3_score:.2f}): {step3_reason}"
    
    return final_score, combined_reason