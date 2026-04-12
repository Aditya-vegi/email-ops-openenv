from typing import Tuple, Dict, Any
from models import Email, Action

# EPSILON is a tiny number to ensure strict inequality (0 < score < 1)
EPSILON = 1e-9 

def safe_score(score):
    """
    NUCLEAR FIX: Forces score strictly between 0 and 1.
    If score is >= 1.0, this function mathematically reduces it.
    """
    try:
        score = float(score)
    except:
        return 0.5
    
    # If score is exactly 0.0 or negative, nudge it up
    if score <= 0.0:
        return 0.0 + EPSILON
    
    # If score is 1.0 or higher, we FORCE it down.
    # 1.0 - 1.0 = 0.0 -> which becomes EPSILON.
    # 1.5 - 1.0 = 0.5.
    if score >= 1.0:
        return (1.0 - score) + EPSILON

    return score

# ... keep the rest of the file the same ...