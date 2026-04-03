from typing import Tuple
from models import Email, Action

def grade_easy(email: Email, action: Action) -> Tuple[float, str]:
    """Easy task: Classify email priority correctly"""
    if action.action_type != "classify":
        return 0.0, "wrong action type"
    
    expected = email.expected_priority
    actual = action.content.lower()
    
    if actual == expected:
        return 1.0, f"correct priority: {expected}"
    elif expected in actual or actual in expected:
        return 0.5, f"partial match: {actual} vs {expected}"
    else:
        return 0.0, f"wrong priority: {actual} vs {expected}"

def grade_medium(email: Email, action: Action) -> Tuple[float, str]:
    """Medium task: Generate appropriate reply"""
    if action.action_type != "reply":
        return 0.0, "wrong action type"
    
    reply = action.content.lower()
    subject = email.subject.lower()
    
    # Check for appropriate response content
    if "server down" in subject and any(word in reply for word in ["investigating", "working", "update", "30 minutes"]):
        return 1.0, "appropriate server issue response"
    elif "invoice" in subject and any(word in reply for word in ["invoice", "details", "clarification", "end of day"]):
        return 1.0, "appropriate invoice response"
    elif "bug" in subject and any(word in reply for word in ["logged", "development", "sprint", "progress"]):
        return 1.0, "appropriate bug report response"
    elif len(reply) > 20 and any(word in reply for word in ["hello", "thank", "working", "update"]):
        return 0.5, "generic but professional response"
    else:
        return 0.0, "inappropriate or insufficient response"

def grade_hard(email: Email, action: Action) -> Tuple[float, str]:
    """Hard task: Multi-step workflow with dependency checking
    
    This implements a multi-step dependency grader that checks:
    1. Correct escalation for urgent items
    2. Proper resolution for non-urgent items  
    3. Workflow efficiency and decision quality
    """
    
    # Step 1: Check if action type is appropriate for email type (0.33 points)
    if email.requires_escalation:
        if action.action_type == "escalate":
            step1_score = 0.33
            step1_reason = "correct escalation for urgent item"
        elif action.action_type == "resolve":
            step1_score = 0.0
            step1_reason = "failed to escalate urgent item"
        else:
            step1_score = 0.1
            step1_reason = "suboptimal action for urgent item"
    else:
        if action.action_type == "resolve":
            step1_score = 0.33
            step1_reason = "correct resolution for non-urgent item"
        elif action.action_type == "escalate":
            step1_score = 0.0
            step1_reason = "unnecessary escalation of non-urgent item"
        else:
            step1_score = 0.1
            step1_reason = "suboptimal action for non-urgent item"
    
    # Step 2: Check content quality and specificity (0.33 points)
    content = action.content.lower()
    step2_score = 0.0
    step2_reason = "poor content quality"
    
    if action.action_type == "escalate" and email.requires_escalation:
        # Check for proper escalation content
        if any(word in content for word in ["critical", "urgent", "immediate", "management", "attention"]):
            step2_score = 0.33
            step2_reason = "proper escalation justification"
        elif len(content) > 20:
            step2_score = 0.2
            step2_reason = "adequate escalation content"
    
    elif action.action_type == "resolve" and not email.requires_escalation:
        # Check for proper resolution content
        if "invoice" in email.subject.lower():
            if any(word in content for word in ["clarification", "details", "provided", "resolved"]):
                step2_score = 0.33
                step2_reason = "proper invoice resolution"
        elif "bug" in email.subject.lower():
            if any(word in content for word in ["logged", "future", "resolution", "minor"]):
                step2_score = 0.33
                step2_reason = "proper bug handling"
        elif len(content) > 15:
            step2_score = 0.2
            step2_reason = "adequate resolution content"
    
    # Step 3: Check workflow efficiency and decision quality (0.34 points)
    step3_score = 0.0
    step3_reason = "inefficient workflow"
    
    # Bonus for quick, appropriate decisions
    if action.action_type in ["escalate", "resolve"]:
        if email.requires_escalation and action.action_type == "escalate":
            step3_score = 0.34
            step3_reason = "efficient urgent item handling"
        elif not email.requires_escalation and action.action_type == "resolve":
            step3_score = 0.34
            step3_reason = "efficient routine item handling"
    
    # Calculate total score
    total_score = step1_score + step2_score + step3_score
    
    # Combine reasons
    combined_reason = f"Step1({step1_score:.2f}): {step1_reason} | Step2({step2_score:.2f}): {step2_reason} | Step3({step3_score:.2f}): {step3_reason}"
    
    return total_score, combined_reason
