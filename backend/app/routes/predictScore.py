"""
Predictive Resume Score endpoint
Computes 0-100 score using weighted skill overlap
"""
from fastapi import APIRouter, HTTPException, Response, Query
from pydantic import BaseModel
from app.services.job_scoring_svc import JobScoringService
from app.services.amplitude import amplitude_service
from app.routes.analyze import ROLE_COMPETENCY_MATRIX
import hashlib
from typing import Dict, Any, List

router = APIRouter(prefix="/api/predictScore", tags=["predict"])


class PredictScoreRequest(BaseModel):
    resume_text: str
    target_role: str | None = None
    analysis_data: Dict[str, Any] | None = None  # Optional: use actual analysis data instead of re-detecting


class PredictScoreResponse(BaseModel):
    score: int  # 0-100
    debug: dict


def build_target_role_skill_vector(target_role: str) -> Dict[str, float]:
    """
    Build target role skill vector from ROLE_COMPETENCY_MATRIX
    Returns: {skill: weight} where weight indicates importance (1.0 = required, 0.7 = important, 0.5 = nice-to-have)
    """
    target_role_lower = target_role.lower()
    jd_vector = {}
    
    # Find matching role in ROLE_COMPETENCY_MATRIX
    matching_role = None
    for role_name in ROLE_COMPETENCY_MATRIX.keys():
        if role_name.lower() in target_role_lower or target_role_lower in role_name.lower():
            matching_role = role_name
            break
    
    if not matching_role:
        # If no exact match, try to infer from target_role
        if "ai" in target_role_lower or "ml" in target_role_lower or "machine learning" in target_role_lower:
            matching_role = "AI Engineer"
        elif "data analyst" in target_role_lower:
            matching_role = "Data Analyst"
        elif "frontend" in target_role_lower:
            matching_role = "Frontend Engineer"
        elif "backend" in target_role_lower:
            matching_role = "Backend Engineer"
        elif "devops" in target_role_lower or "dev ops" in target_role_lower:
            matching_role = "DevOps"
        else:
            # Default: use a generic skill list
            return {}
    
    # Get competency matrix for this role
    matrix = ROLE_COMPETENCY_MATRIX.get(matching_role, {})
    
    # Build skill vector from competency matrix
    # Core skills (first 3-4 areas) get weight 1.0
    # Important skills (middle areas) get weight 0.7
    # Nice-to-have skills (last areas) get weight 0.5
    skill_areas = list(matrix.keys())
    for i, (skill_area, required_keywords) in enumerate(matrix.items()):
        # Determine weight based on position (earlier = more important)
        if i < min(3, len(skill_areas) // 2):
            weight = 1.0  # Core/required
        elif i < len(skill_areas) - 1:
            weight = 0.7  # Important
        else:
            weight = 0.5  # Nice-to-have
        
        # Add each keyword with the determined weight
        for keyword in required_keywords:
            keyword_lower = keyword.lower().strip()
            # Use max weight if keyword already exists (don't downgrade)
            if keyword_lower not in jd_vector or jd_vector[keyword_lower] < weight:
                jd_vector[keyword_lower] = weight
    
    return jd_vector


def compute_resume_score(resume_text: str, target_role: str | None = None, analysis_data: Dict[str, Any] | None = None) -> int:
    """
    Compute resume score (0-100) using weighted skill overlap
    
    Algorithm:
    - Use analysis_data if provided (actual skills from analysis)
    - Otherwise, extract skills from resume (fallback)
    - Build candidate skill vector
    - Build target role skill vector from ROLE_COMPETENCY_MATRIX
    - Score based on skill overlap
    - Normalize to 0-100
    """
    scoring_service = JobScoringService()
    
    # Use analysis_data if provided, otherwise extract from resume text
    if analysis_data:
        # Use actual analysis data (skills from analysis endpoint)
        candidate_analysis = {
            "skills": analysis_data.get("skills", {}),
            "keywords_detected": analysis_data.get("keywords_detected", []),
            "strengths": analysis_data.get("strengths", []),
        }
    else:
        # Fallback: extract skills from resume text (simplified)
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
        
        candidate_analysis = {
            "skills": candidate_skills,
            "keywords_detected": candidate_skills["core"] + candidate_skills["adjacent"] + candidate_skills["advanced"],
            "strengths": [],
        }
    
    # Build candidate skill vector
    candidate_vector = scoring_service.build_candidate_skill_vector(candidate_analysis)
    
    # Build target role skill vector (if target_role provided)
    if target_role:
        # Use ROLE_COMPETENCY_MATRIX to build target role skill vector
        jd_vector = build_target_role_skill_vector(target_role)
        
        if not jd_vector:
            # Fallback: use generic JD extraction
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
        skills = candidate_analysis.get("skills", {})
        core_count = len(skills.get("core", []))
        adjacent_count = len(skills.get("adjacent", []))
        advanced_count = len(skills.get("advanced", []))
        
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
        
        # Compute score (use analysis_data if provided)
        score = compute_resume_score(
            request.resume_text, 
            request.target_role,
            request.analysis_data
        )
        
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

