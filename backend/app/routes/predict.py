from fastapi import APIRouter, Query
from typing import List, Optional
from app.models.schemas import Prediction
from app.services.predict_svc import predict_service

router = APIRouter(prefix="/predict", tags=["predict"])


@router.get("", response_model=Prediction)
async def get_prediction(
    skills_have: Optional[List[str]] = Query(default=None, description="List of skills the user has"),
    skills_gap: Optional[List[str]] = Query(default=None, description="List of skills the user needs to learn")
) -> Prediction:
    """
    Get prediction for score improvement after completing coaching plan.
    
    Aggregates current store values via query parameters.
    If not provided, uses default values for demo.
    """
    # Use provided values or defaults for demo
    have_skills = skills_have if skills_have else [
        "React", "TypeScript", "Node.js", "JavaScript", "HTML", "CSS"
    ]
    gap_skills = skills_gap if skills_gap else [
        "AWS", "System Design", "GraphQL", "Docker"
    ]
    
    # Compute prediction using logistic formula
    prediction = predict_service.compute_prediction(
        skills_have=have_skills,
        skills_gap=gap_skills
    )
    
    # Validate output via Pydantic (already validated by response_model)
    return prediction

