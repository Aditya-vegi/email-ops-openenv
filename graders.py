def grade_easy(action):
    if "urgent" in action.content.lower():
        return 1.0
    return 0.3

def grade_medium(action):
    if "fixing" in action.content.lower():
        return 1.0
    return 0.5

def grade_hard(action):
    score = 0.0
    if "urgent" in action.content.lower():
        score += 0.4
    if "fix" in action.content.lower():
        score += 0.4
    if "team" in action.content.lower():
        score += 0.2
    return score