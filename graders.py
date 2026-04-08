from typing import Tuple, Dict, Any
from models import Email, Action

def safe_score(score):
    try:
        score = float(score)
    except:
        return 0.5
    
    if score <= 0.01:
        return 0.02
    elif score >= 0.99:
        return 0.98
    elif score <= 0:
        return 0.02
    elif score >= 1:
        return 0.98
    return score

def grade_easy(email: Email, action: Action, internal_state: Dict[str, Any]) -> Tuple[float, str]:
    """Easy task: Classify email priority correctly - deterministic grading"""
    if action.action_type != "classify":
        return safe_score(0.01), "wrong action type"
    
    # Deterministic check: Verify email was actually classified in internal state
    email_id = email.email_id
    if email_id not in internal_state.get("classified_emails", []):
        return safe_score(0.01), "email not marked as classified in internal state"
    
    expected = email.expected_priority
    actual = action.content.lower()
    
    if actual == expected:
        return safe_score(0.99), f"correct priority: {expected} (verified in internal state)"
    elif expected in actual or actual in expected:
        return safe_score(0.5), f"partial match: {actual} vs {expected} (verified in internal state)"
    else:
        return safe_score(0.01), f"wrong priority: {actual} vs {expected} (verified in internal state)"

def grade_medium(email: Email, action: Action, internal_state: Dict[str, Any]) -> Tuple[float, str]:
    """Medium task: Generate appropriate reply - deterministic grading"""
    if action.action_type != "reply":
        return safe_score(0.01), "wrong action type"
    
    # Deterministic check: Verify email was actually replied to in internal state
    email_id = email.email_id
    if email_id not in internal_state.get("replied_emails", []):
        return safe_score(0.01), "email not marked as replied in internal state"
    
    reply = action.content.lower()
    subject = email.subject.lower()
    
    # Check for appropriate response content
    if "server down" in subject and any(word in reply for word in ["investigating", "working", "update", "30 minutes"]):
        return safe_score(0.99), "appropriate server issue response (verified in internal state)"
    elif "invoice" in subject and any(word in reply for word in ["invoice", "details", "clarification", "end of day"]):
        return safe_score(0.99), "appropriate invoice response (verified in internal state)"
    elif "bug" in subject and any(word in reply for word in ["logged", "development", "sprint", "progress"]):
        return safe_score(0.99), "appropriate bug report response (verified in internal state)"
    elif len(reply) > 20 and any(word in reply for word in ["hello", "thank", "working", "update"]):
        return safe_score(0.5), "generic but professional response (verified in internal state)"
    else:
        return safe_score(0.01), "inappropriate or insufficient response (verified in internal state)"

def grade_hard(email: Email, action: Action, internal_state: Dict[str, Any]) -> Tuple[float, str]:
    """Hard task: Multi-step workflow with dependency checking - deterministic grading
    
    This implements a multi-step dependency grader that checks:
    1. Correct escalation for urgent items (verifies internal state)
    2. Proper resolution for non-urgent items (verifies internal state)  
    3. Workflow efficiency and decision quality
    """
    
    email_id = email.email_id
    
    # Step 1: Check if action type is appropriate for email type (0.33 points)
    # Deterministic: Check internal state flags rather than just action content
    if email.requires_escalation:
        if action.action_type == "escalate":
            # Verify this email is actually in escalated_emails in internal state
            if email_id in internal_state.get("escalated_emails", []):
                step1_score = safe_score(0.33)
                step1_reason = "correct escalation for urgent item (verified in internal state)"
            else:
                step1_score = safe_score(0.01)
                step1_reason = "escalation action but not in internal state"
        elif action.action_type == "resolve":
            step1_score = safe_score(0.01)
            step1_reason = "failed to escalate urgent item"
        else:
            step1_score = safe_score(0.1)
            step1_reason = "suboptimal action for urgent item"
    else:
        if action.action_type == "resolve":
            # Verify this email is actually in resolved_emails in internal state
            if email_id in internal_state.get("resolved_emails", []):
                step1_score = safe_score(0.33)
                step1_reason = "correct resolution for non-urgent item (verified in internal state)"
            else:
                step1_score = safe_score(0.01)
                step1_reason = "resolution action but not in internal state"
        elif action.action_type == "escalate":
            step1_score = safe_score(0.01)
            step1_reason = "unnecessary escalation of non-urgent item"
        else:
            step1_score = safe_score(0.1)
            step1_reason = "suboptimal action for non-urgent item"
    
    # Step 2: Check content quality and specificity (0.33 points)
    content = action.content.lower()
    step2_score = safe_score(0.01)
    step2_reason = "poor content quality"
    
    if action.action_type == "escalate" and email.requires_escalation:
        # Check for proper escalation content AND verify internal state
        if any(word in content for word in ["critical", "urgent", "immediate", "management", "attention"]):
            if email_id in internal_state.get("escalated_emails", []):
                step2_score = safe_score(0.33)
                step2_reason = "proper escalation justification (verified in internal state)"
            else:
                step2_score = safe_score(0.2)
                step2_reason = "good content but internal state mismatch"
        elif len(content) > 20:
            step2_score = safe_score(0.2)
            step2_reason = "adequate escalation content"
    
    elif action.action_type == "resolve" and not email.requires_escalation:
        # Check for proper resolution content AND verify internal state
        if "invoice" in email.subject.lower():
            if any(word in content for word in ["clarification", "details", "provided", "resolved"]):
                if email_id in internal_state.get("resolved_emails", []):
                    step2_score = safe_score(0.33)
                    step2_reason = "proper invoice resolution (verified in internal state)"
                else:
                    step2_score = safe_score(0.2)
                    step2_reason = "good content but internal state mismatch"
        elif "bug" in email.subject.lower():
            if any(word in content for word in ["logged", "future", "resolution", "minor"]):
                if email_id in internal_state.get("resolved_emails", []):
                    step2_score = safe_score(0.33)
                    step2_reason = "proper bug handling (verified in internal state)"
                else:
                    step2_score = safe_score(0.2)
                    step2_reason = "good content but internal state mismatch"
        elif len(content) > 15:
            step2_score = safe_score(0.2)
            step2_reason = "adequate resolution content"
    
    # Step 3: Check workflow efficiency and decision quality (0.34 points)
    step3_score = safe_score(0.01)
    step3_reason = "inefficient workflow"
    
    # Bonus for quick, appropriate decisions - verify with internal state
    if action.action_type in ["escalate", "resolve"]:
        if email.requires_escalation and action.action_type == "escalate":
            if email_id in internal_state.get("escalated_emails", []):
                step3_score = safe_score(0.34)
                step3_reason = "efficient urgent item handling (verified in internal state)"
        elif not email.requires_escalation and action.action_type == "resolve":
            if email_id in internal_state.get("resolved_emails", []):
                step3_score = safe_score(0.34)
                step3_reason = "efficient routine item handling (verified in internal state)"
    
    # Calculate total score
    total_score = safe_score(step1_score + step2_score + step3_score)
    
    # Combine reasons
    combined_reason = f"Step1({step1_score:.2f}): {step1_reason} | Step2({step2_score:.2f}): {step2_reason} | Step3({step3_score:.2f}): {step3_reason}"
    
    return total_score, combined_reason