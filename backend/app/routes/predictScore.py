"""
Predictive Resume Score endpoint
Computes 0-100 score using weighted skill overlap
"""
from fastapi import APIRouter, HTTPException, Response, Query
from pydantic import BaseModel
from app.services.job_scoring_svc import JobScoringService
from app.services.amplitude import amplitude_service
import hashlib

router = APIRouter(prefix="/api/predictScore", tags=["predict"])


class PredictScoreRequest(BaseModel):
    resume_text: str
    target_role: str | None = None


class PredictScoreResponse(BaseModel):
    score: int  # 0-100
    debug: dict


def compute_resume_score(resume_text: str, target_role: str | None = None) -> int:
    """
    Compute resume score (0-100) using weighted skill overlap
    
    Algorithm:
    - Extract skills from resume (core, adjacent, advanced)
    - Build candidate skill vector
    - Score based on skill coverage and strengths/gaps ratio
    - Normalize to 0-100
    """
    scoring_service = JobScoringService()
    
    # Extract skills from resume (simplified - in production, use analysis)
    resume_lower = resume_text.lower()
    
    # Common tech skills to look for
    tech_skills = [
        "python", "java", "javascript", "typescript", "react", "node", "sql",
        "aws", "docker", "kubernetes", "git", "html", "css", "mongodb",
        "postgresql", "pandas", "numpy", "tensorflow", "pytorch", "machine learning",
        "ai", "data science", "tableau", "power bi", "excel", "agile", "scrum",
    ]
    
    # Build candidate skill vector
    candidate_skills = {
        "core": [],
        "adjacent": [],
        "advanced": [],
    }
    
    # Detect skills in resume
    for skill in tech_skills:
        skill_lower = skill.lower()
        if skill_lower in resume_lower:
            # Determine skill level based on context
            if any(word in resume_lower for word in ["expert", "proficient", "strong", "extensive"]):
                candidate_skills["core"].append(skill)
            elif any(word in resume_lower for word in ["familiar", "basic", "some"]):
                candidate_skills["adjacent"].append(skill)
            else:
                candidate_skills["advanced"].append(skill)
    
    # Build analysis data structure for scoring
    analysis_data = {
        "skills": candidate_skills,
        "keywords_detected": candidate_skills["core"] + candidate_skills["adjacent"] + candidate_skills["advanced"],
        "strengths": [],
    }
    
    # Build candidate skill vector
    candidate_vector = scoring_service.build_candidate_skill_vector(analysis_data)
    
    # Build target role skill vector (if target_role provided)
    if target_role:
        # Use target role as JD text for comparison
        jd_text = f"{target_role} requirements: {target_role.lower()} skills"
        jd_vector = scoring_service.extract_jd_skills(jd_text)
        
        # Score match
        match_score, _, _ = scoring_service.score_job_match(
            candidate_vector,
            jd_vector,
            resume_text
        )
        
        # Normalize to 0-100
        score = max(0, min(100, match_score))
    else:
        # Score based on skill coverage alone
        core_count = len(candidate_skills["core"])
        adjacent_count = len(candidate_skills["adjacent"])
        advanced_count = len(candidate_skills["advanced"])
        
        # Weighted score: core (50%) + adjacent (30%) + advanced (20%)
        score = min(100, int(
            (core_count * 10) +  # 10 points per core skill
            (adjacent_count * 5) +  # 5 points per adjacent skill
            (advanced_count * 3)  # 3 points per advanced skill
        ))
    
    return score


@router.post("")
async def predict_score(
    request: PredictScoreRequest,
    response: Response,
    hash: str | None = Query(None, description="Resume hash for cache busting")
):
    """
    Compute predictive resume score (0-100) using skill overlap
    """
    try:
        # Compute resume hash
        resume_hash = hashlib.sha256(request.resume_text.encode('utf-8')).hexdigest()
        debug_hash = resume_hash[:8]
        
        # Add Cache-Control header
        response.headers["Cache-Control"] = "no-store"
        
        # Compute score
        score = compute_resume_score(request.resume_text, request.target_role)
        
        # Send Amplitude event (only hash, score, no raw text)
        amplitude_service.track(
            event_type="score_predicted",
            event_properties={
                "hash": debug_hash,
                "score": score,
                "has_target_role": request.target_role is not None,
            }
        )
        
        return PredictScoreResponse(
            score=score,
            debug={
                "hash": debug_hash,
                "provider": "rule-based",
            }
        )
    except Exception as e:
        print(f"[PredictScore] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to compute score: {str(e)}")

