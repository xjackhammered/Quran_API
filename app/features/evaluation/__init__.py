"""
Recitation Evaluation Feature
=============================
Evaluates Quran recitation accuracy by comparing 
transcribed text against the actual Quran text.
"""

from app.features.evaluation.service import RecitationEvaluator, get_evaluator
from app.features.evaluation.router import router

__all__ = ["RecitationEvaluator", "get_evaluator", "router"]
