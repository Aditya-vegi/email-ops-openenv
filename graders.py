from typing import Tuple, Dict, Any
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

# Renamed functions to force cache refresh in the evaluation system
def grade_easy_v2(email: Email, action: Action, internal_state: Dict[str, Any]) -> Tuple[float, str]:
    """Easy task: Classify email priority correctly"""
    if action.action_type != "classify":
        return clamp_score(0.01), "wrong action type"
    
    email_id = email.email_id
    if email_id not in internal_state.get("classified_emails", []):
        return clamp_score(0.01), "email not marked as classified in internal state"
    
    expected = email.expected_priority
    actual = action.content.lower()
    
    if actual == expected:
        return clamp_score(0.99), f"correct priority: {expected}"
    elif expected in actual or actual in expected:
        return clamp_score(0.5), f"partial match: {actual} vs {expected}"
    else:
        return clamp_score(0.01), f"wrong priority: {actual} vs {expected}"

def grade_medium_v2(email: Email, action: Action, internal_state: Dict[str, Any]) -> Tuple[float, str]:
    """Medium task: Generate appropriate reply"""
    if action.action_type != "reply":
        return clamp_score(0.01), "wrong action type"
    
    email_id = email.email_id
    if email_id not in internal_state.get("replied_emails", []):
        return clamp_score(0.01), "email not marked as replied in internal state"
    
    reply = action.content.lower()
    subject = email.subject.lower()
    
    if "server down" in subject and any(word in reply for word in ["investigating", "working", "update", "30 minutes"]):
        return clamp_score(0.99), "appropriate server issue response"
    elif "invoice" in subject and any(word in reply for word in ["invoice", "details", "clarification", "end of day"]):
        return clamp_score(0.99), "appropriate invoice response"
    elif "bug" in subject and any(word in reply for word in ["logged", "development", "sprint", "progress"]):
        return clamp_score(0.99), "appropriate bug report response"
    elif len(reply) > 20 and any(word in reply for word in ["hello", "thank", "working", "update"]):
        return clamp_score(0.5), "generic but professional response"
    else:
        return clamp_score(0.01), "inappropriate or insufficient response"

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
    
    # Apply clamp_score ONLY once at the end
    final_score = clamp_score(total_score)
    
    combined_reason = f"Step1({step1_score:.2f}): {step1_reason} | Step2({step2_score:.2f}): {step2_reason} | Step3({step3_score:.2f}): {step3_reason}"
    
    return final_score, combined_reason