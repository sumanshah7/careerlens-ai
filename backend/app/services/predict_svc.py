"""
Prediction service for computing score predictions using logistic formula
"""
import math
from typing import List
from app.models.schemas import Prediction


class PredictService:
    def __init__(self):
        # Fixed constants for logistic formula
        self.a = 0.15  # Weight for skills have
        self.b = 0.20  # Weight for skills gap
    
    def _sigmoid(self, x: float) -> float:
        """
        Sigmoid function: 1 / (1 + e^(-x))
        Maps any real number to a value between 0 and 1
        """
        return 1 / (1 + math.exp(-x))
    
    def _sigmoid_scaled(self, x: float, scale: float = 100.0) -> float:
        """
        Scaled sigmoid function to map to 0-100 range
        """
        return self._sigmoid(x) * scale
    
    def compute_prediction(self, skills_have: List[str], skills_gap: List[str]) -> Prediction:
        """
        Compute prediction using logistic formula.
        
        Formula:
        - baseline = sigmoid(a * have_count - b * gap_count) * 100
        - afterPlan = sigmoid(a * (have_count + 2) - b * (gap_count - 2)) * 100
        - delta = afterPlan - baseline
        
        Args:
            skills_have: List of skills the user has
            skills_gap: List of skills the user needs to learn
            
        Returns:
            Prediction with baseline, afterPlan, and delta
        """
        have_count = len(skills_have)
        gap_count = len(skills_gap)
        
        # Compute baseline score
        baseline_input = self.a * have_count - self.b * gap_count
        baseline = self._sigmoid_scaled(baseline_input)
        
        # Compute afterPlan score (assuming 2 more skills learned, 2 gaps closed)
        after_plan_have = have_count + 2
        after_plan_gap = max(0, gap_count - 2)  # Ensure non-negative
        after_plan_input = self.a * after_plan_have - self.b * after_plan_gap
        after_plan = self._sigmoid_scaled(after_plan_input)
        
        # Compute delta
        delta = after_plan - baseline
        
        # Ensure values are in valid range
        baseline = max(0.0, min(100.0, baseline))
        after_plan = max(0.0, min(100.0, after_plan))
        
        return Prediction(
            baseline=round(baseline, 2),
            afterPlan=round(after_plan, 2),
            delta=round(delta, 2)
        )


# Global instance
predict_service = PredictService()

