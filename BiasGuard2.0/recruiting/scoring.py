"""
Scoring model for the recruiting module.
This is modular so it can be replaced with a real ML model later.
"""

from typing import Dict, Any


# Education level weights
EDUCATION_WEIGHTS = {
    'High School': 1,
    'Bachelor': 2,
    'Master': 3,
    'PhD': 4
}


def calculate_education_score(education_level: str) -> float:
    """Convert education level to numeric score"""
    return EDUCATION_WEIGHTS.get(education_level, 1)


def calculate_model_score(
    skill_score: int,
    experience: int,
    education_level: str,
    job_required_skill: int,
    job_required_experience: int
) -> float:
    """
    Calculate the hiring model score.
    
    Formula:
    model_score = 
        0.4 * skill_score +
        0.3 * experience +
        0.2 * education_level +
        0.1 * job_match_bonus
    
    Args:
        skill_score: Candidate's skill score (0-100)
        experience: Years of experience
        education_level: Education level
        job_required_skill: Job's required skill score
        job_required_experience: Job's required experience
    
    Returns:
        model_score: Calculated score (0-100 scale)
    """
    
    # Base scores (normalized to 0-100)
    skill_component = skill_score * 0.4
    
    # Experience component (cap at 20 years for scoring)
    experience_component = min(experience, 20) * 5 * 0.3  # Max 30 points
    
    # Education component (normalized to 0-100)
    education_component = calculate_education_score(education_level) * 25 * 0.2  # Max 20 points
    
    # Job match bonus (if candidate exceeds requirements)
    skill_bonus = max(0, (skill_score - job_required_skill)) * 0.5
    experience_bonus = max(0, (experience - job_required_experience)) * 1
    job_match_bonus = (skill_bonus + experience_bonus) * 0.1
    
    # Calculate total score
    model_score = skill_component + experience_component + education_component + job_match_bonus
    
    # Cap at 100
    return min(model_score, 100.0)


def make_decision(model_score: float, threshold: float = 50.0) -> int:
    """
    Make hiring decision based on model score.
    
    Args:
        model_score: The calculated model score
        threshold: Minimum score to be shortlisted
    
    Returns:
        0 = rejected, 1 = shortlisted
    """
    return 1 if model_score >= threshold else 0


def score_candidate(
    candidate_data: Dict[str, Any],
    job_data: Dict[str, Any],
    threshold: float = 50.0
) -> Dict[str, Any]:
    """
    Score a candidate and make a hiring decision.
    
    This is the main scoring function that can be called by the routes.
    It calculates the model score and makes a decision.
    
    Args:
        candidate_data: Dictionary with candidate info
        job_data: Dictionary with job requirements
        threshold: Minimum score to be shortlisted
    
    Returns:
        Dictionary with model_score and decision
    """
    
    model_score = calculate_model_score(
        skill_score=candidate_data.get('skill_score', 0),
        experience=candidate_data.get('experience', 0),
        education_level=candidate_data.get('education_level', 'High School'),
        job_required_skill=job_data.get('required_skill_score', 0),
        job_required_experience=job_data.get('required_experience', 0)
    )
    
    decision = make_decision(model_score, threshold)
    
    return {
        'model_score': round(model_score, 2),
        'decision': decision,
        'threshold': threshold
    }


# This can be replaced with a real ML model
def predict_with_ml_model(candidate_features, model) -> float:
    """
    Placeholder for real ML model integration.
    
    Args:
        candidate_features: Feature vector for candidate
        model: Trained ML model
    
    Returns:
        Predicted score or probability
    """
    # This would use a real scikit-learn or other ML model
    # For now, return a placeholder
    return 0.0
