"""
BiasGuard Recruiting Module
A minimal recruiting software module that integrates with the BiasGuard bias auditing system.
"""
from recruiting.models import Job, Candidate, Application, init_db, get_db
from recruiting.scoring import score_candidate, calculate_model_score, make_decision

__all__ = [
    'Job',
    'Candidate', 
    'Application',
    'init_db',
    'get_db',
    'score_candidate',
    'calculate_model_score',
    'make_decision'
]
