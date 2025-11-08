"""
LinkedIn Job Search endpoint using RapidAPI LinkedIn Job Search API
"""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.schemas import LinkedInJobSearchItem, LinkedInJobSearchResponse
from app.config import settings
from app.services.amplitude import amplitude_service
import httpx
import hashlib
import re
from datetime import datetime
from collections import Counter

router = APIRouter(prefix="/api/jobs", tags=["linkedin-jobs"])


class JobSearchParams(BaseModel):
    role: str
    location: Optional[str] = "US-Remote"
    radius_km: Optional[int] = Field(default=50, ge=1, le=200)
    remote: Optional[bool] = False
    limit: Optional[int] = Field(default=15, ge=1, le=50)
    cursor: Optional[str] = None


def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills/keywords from text"""
    if not text:
        return []
    
    # Common tech skills
    tech_skills = [
        "python", "javascript", "typescript", "react", "node", "java", "c++", "c#",
        "sql", "mongodb", "postgresql", "aws", "docker", "kubernetes", "git",
        "html", "css", "angular", "vue", "express", "django", "flask", "spring",
        "machine learning", "ai", "data science", "analytics", "tableau", "power bi",
        "agile", "scrum", "ci/cd", "devops", "microservices", "rest api", "graphql"
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in tech_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills


def compute_match_score(
    resume_skills: List[str],
    job_keywords: List[str],
    job_title: str,
    job_description: str
) -> tuple[int, List[str], List[str]]:
    """
    Compute match score based on skills overlap.
    Returns: (matchScore 0-100, reasons, gaps)
    """
    if not resume_skills:
        return 50, ["Relevant role match"], []
    
    # Normalize to lowercase sets
    resume_set = {s.lower().strip() for s in resume_skills if s.strip()}
    job_set = {k.lower().strip() for k in job_keywords if k.strip()}
    
    # Also extract skills from job text
    job_text = f"{job_title} {job_description}".lower()
    job_skills = extract_skills_from_text(job_text)
    job_set.update({s.lower().strip() for s in job_skills})
    
    # Compute overlap
    overlap = resume_set.intersection(job_set)
    total_resume_skills = len(resume_set)
    
    if total_resume_skills == 0:
        match_score = 50
    else:
        # Match score: overlap ratio * 100, capped at 100
        match_score = min(100, round((len(overlap) / max(1, total_resume_skills)) * 100))
    
    # Generate reasons (top 3 matching skills)
    reasons = []
    if overlap:
        reasons = list(overlap)[:3]
        reasons = [f"Strong experience with {r.title()}" for r in reasons]
    else:
        reasons = ["Relevant role match"]
    
    # Generate gaps (top 3 missing skills)
    gaps = []
    missing = job_set - resume_set
    if missing:
        gaps = list(missing)[:3]
        gaps = [f"Consider learning {g.title()}" for g in gaps]
    
    return match_score, reasons, gaps


def map_rapidapi_response_to_job(
    job_data: Dict[str, Any],
    resume_skills: List[str]
) -> LinkedInJobSearchItem:
    """Map RapidAPI response to LinkedInJobSearchItem"""
    # Extract fields (adjust based on actual API response structure)
    job_id = job_data.get("id", "") or job_data.get("job_id", "") or str(hash(str(job_data)))
    title = job_data.get("title", "") or job_data.get("job_title", "") or job_data.get("name", "") or "Job Opening"
    company = job_data.get("company", "") or job_data.get("company_name", "") or job_data.get("employer", "") or "Company"
    location = job_data.get("location", "") or job_data.get("job_location", "") or "Remote"
    url = job_data.get("url", "") or job_data.get("job_url", "") or job_data.get("apply_url", "")
    description = job_data.get("description", "") or job_data.get("job_description", "") or ""
    listed_at = job_data.get("listed_at", "") or job_data.get("posted_at", "") or job_data.get("created_at", "") or datetime.now().isoformat()
    
    # Generate URL if missing - build LinkedIn search URL
    if not url or url == "" or "expired_jd_redirect" in url:
        # Build a LinkedIn search URL from title, company, and location
        from urllib.parse import quote
        search_params = f"{quote(title)}%20{quote(company)}"
        if location:
            search_params += f"%20{quote(location)}"
        url = f"https://www.linkedin.com/jobs/search/?keywords={search_params}"
    
    # Extract keywords from job
    job_keywords = extract_skills_from_text(f"{title} {description}")
    
    # Compute match score
    match_score, reasons, gaps = compute_match_score(
        resume_skills,
        job_keywords,
        title,
        description
    )
    
    # Generate ID if missing
    if not job_id or job_id == "":
        job_id = f"linkedin-{abs(hash(f'{title}{company}{url}'))}"
    
    return LinkedInJobSearchItem(
        id=job_id,
        title=title,
        company=company,
        location=location,
        url=url,
        listed_at=listed_at,
        source="linkedin",
        description_snippet=description[:200] + "..." if len(description) > 200 else description,
        matchScore=match_score,
        reasons=reasons,
        gaps=gaps
    )


@router.get("/search")
async def search_linkedin_jobs(
    role: str = Query(..., description="Job role/title to search for"),
    location: str = Query("US-Remote", description="Location for job search"),
    radius_km: int = Query(50, ge=1, le=200, description="Search radius in kilometers"),
    remote: bool = Query(False, description="Filter for remote jobs only"),
    limit: int = Query(15, ge=1, le=50, description="Maximum number of jobs to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    response: Response = None
):
    """
    Search LinkedIn jobs using RapidAPI LinkedIn Job Search API (Ultra - Get Jobs Hourly)
    """
    # Set cache control
    response.headers["Cache-Control"] = "no-store"
    
    # Get resume skills from stored analysis (if available)
    # For now, extract from role - in production, get from user's stored analysis
    resume_skills = [role.lower()]  # Placeholder - should come from stored analysis
    
    # Check if RapidAPI key is available - if not, use free job service
    if not settings.rapidapi_key or not settings.rapidapi_key.strip():
        print("[LinkedInJobs] RAPIDAPI_KEY not set, falling back to free job service")
        from app.services.free_job_svc import free_job_service
        from app.services.job_scoring_svc import JobScoringService
        
        # Use free job service
        free_jobs_data = free_job_service.search_jobs(role, location, limit)
        
        # Initialize scoring service
        scoring_service = JobScoringService()
        candidate_vector = scoring_service.build_candidate_skill_vector({
            "skills": {"core": resume_skills, "adjacent": [], "advanced": []}
        })
        
        jobs = []
        for job_data in free_jobs_data:
            jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('description', '')}"
            jd_vector = scoring_service.extract_jd_skills(jd_text)
            match_score, reasons, gaps = scoring_service.score_job_match(
                candidate_vector,
                jd_vector,
                ""
            )
            
            jobs.append(LinkedInJobSearchItem(
                id=job_data.get("id", f"free-{abs(hash(job_data.get('url', '') + job_data.get('title', '')))}"),
                title=job_data.get("title", "Job Opening"),
                company=job_data.get("company", "Company"),
                location=job_data.get("location", location),
                url=job_data.get("url", "https://example.com/job"),
                listed_at=datetime.now().isoformat(),
                source=job_data.get("source", "free-fallback"),
                description_snippet=job_data.get("description", "")[:200] if job_data.get("description") else None,
                matchScore=int(match_score),
                reasons=reasons,
                gaps=gaps
            ))
        
        debug_hash = hashlib.sha256(role.encode()).hexdigest()[:8]
        amplitude_service.track(
            event_type="linkedin_jobs_searched",
            event_properties={
                "hash": debug_hash,
                "count": len(jobs),
                "source": "free-fallback"
            }
        )
        
        return LinkedInJobSearchResponse(
            jobs=jobs,
            nextCursor=None,
            debug={
                "source": "free-fallback",
                "count": len(jobs),
                "hash": debug_hash,
                "message": "RAPIDAPI_KEY not set, using free job service"
            }
        )
    
    try:
        # Build RapidAPI request
        url = f"{settings.linkedin_base_url}/active-jb-1h"
        headers = {
            "X-RapidAPI-Key": settings.rapidapi_key,
            "X-RapidAPI-Host": settings.rapidapi_host,
        }
        
        # Build query parameters
        params = {
            "offset": "0",
            "description_type": "text",
        }
        
        # Add search query
        search_query = role
        if location and location != "US-Remote":
            search_query = f"{role} {location}"
        
        if search_query:
            params["query"] = search_query
        
        # Add location filters if not remote
        if not remote and location and location != "US-Remote":
            params["location"] = location
            params["radius"] = str(radius_km)
        
        # Add pagination cursor if provided
        if cursor:
            params["cursor"] = cursor
        
        # Make request with timeout and retry
        timeout = httpx.Timeout(15.0, connect=5.0)
        jobs = []
        next_cursor = None
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response_api = await client.get(url, headers=headers, params=params)
                response_api.raise_for_status()
                
                data = response_api.json()
                
                # Parse response (adjust based on actual API structure)
                job_list = data.get("jobs", []) or data.get("data", []) or data.get("results", [])
                
                if not job_list:
                    # Return empty response
                    return LinkedInJobSearchResponse(
                        jobs=[],
                        nextCursor=None,
                        debug={
                            "source": "linkedin-rapidapi",
                            "count": 0,
                            "message": "No jobs found"
                        }
                    )
                
                # Extract next cursor from response if available
                next_cursor = data.get("next_cursor") or data.get("nextCursor") or data.get("cursor") or None
                
                # Map and filter jobs - process up to limit
                processed_count = 0
                for job_data in job_list:
                    if processed_count >= limit:
                        break
                    
                    try:
                        # Filter out expired LinkedIn redirects
                        job_url = job_data.get("url", "") or job_data.get("job_url", "") or ""
                        if job_url and "expired_jd_redirect" in job_url:
                            continue
                        
                        # Map to our schema
                        job_item = map_rapidapi_response_to_job(job_data, resume_skills)
                        jobs.append(job_item)
                        processed_count += 1
                    except Exception as e:
                        print(f"[LinkedIn Jobs] Error mapping job: {e}")
                        continue
                
            except httpx.HTTPStatusError as e:
                print(f"[LinkedIn Jobs] HTTP error: {e.response.status_code} - {e.response.text[:200]}")
                # Fall back to free job service on HTTP errors
                print("[LinkedIn Jobs] Falling back to free job service due to HTTP error")
                from app.services.free_job_svc import free_job_service
                from app.services.job_scoring_svc import JobScoringService
                
                free_jobs_data = free_job_service.search_jobs(role, location, limit)
                scoring_service = JobScoringService()
                candidate_vector = scoring_service.build_candidate_skill_vector({
                    "skills": {"core": resume_skills, "adjacent": [], "advanced": []}
                })
                
                jobs = []
                for job_data in free_jobs_data:
                    jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('description', '')}"
                    jd_vector = scoring_service.extract_jd_skills(jd_text)
                    match_score, reasons, gaps = scoring_service.score_job_match(
                        candidate_vector,
                        jd_vector,
                        ""
                    )
                    
                    jobs.append(LinkedInJobSearchItem(
                        id=job_data.get("id", f"free-error-{abs(hash(job_data.get('url', '') + job_data.get('title', '')))}"),
                        title=job_data.get("title", "Job Opening"),
                        company=job_data.get("company", "Company"),
                        location=job_data.get("location", location),
                        url=job_data.get("url", "https://example.com/job"),
                        listed_at=datetime.now().isoformat(),
                        source=job_data.get("source", "free-fallback-error"),
                        description_snippet=job_data.get("description", "")[:200] if job_data.get("description") else None,
                        matchScore=int(match_score),
                        reasons=reasons,
                        gaps=gaps
                    ))
                
                debug_hash = hashlib.sha256(role.encode()).hexdigest()[:8]
                amplitude_service.track(
                    event_type="linkedin_jobs_searched",
                    event_properties={
                        "hash": debug_hash,
                        "count": len(jobs),
                        "source": "free-fallback-error"
                    }
                )
                
                return LinkedInJobSearchResponse(
                    jobs=jobs,
                    nextCursor=None,
                    debug={
                        "source": "free-fallback-error",
                        "count": len(jobs),
                        "hash": debug_hash,
                        "message": f"RapidAPI HTTP error {e.response.status_code}, using free job service"
                    }
                )
            except httpx.TimeoutException:
                print("[LinkedIn Jobs] Request timeout - falling back to free job service")
                from app.services.free_job_svc import free_job_service
                from app.services.job_scoring_svc import JobScoringService
                
                free_jobs_data = free_job_service.search_jobs(role, location, limit)
                scoring_service = JobScoringService()
                candidate_vector = scoring_service.build_candidate_skill_vector({
                    "skills": {"core": resume_skills, "adjacent": [], "advanced": []}
                })
                
                jobs = []
                for job_data in free_jobs_data:
                    jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('description', '')}"
                    jd_vector = scoring_service.extract_jd_skills(jd_text)
                    match_score, reasons, gaps = scoring_service.score_job_match(
                        candidate_vector,
                        jd_vector,
                        ""
                    )
                    
                    jobs.append(LinkedInJobSearchItem(
                        id=job_data.get("id", f"free-timeout-{abs(hash(job_data.get('url', '') + job_data.get('title', '')))}"),
                        title=job_data.get("title", "Job Opening"),
                        company=job_data.get("company", "Company"),
                        location=job_data.get("location", location),
                        url=job_data.get("url", "https://example.com/job"),
                        listed_at=datetime.now().isoformat(),
                        source=job_data.get("source", "free-fallback-timeout"),
                        description_snippet=job_data.get("description", "")[:200] if job_data.get("description") else None,
                        matchScore=int(match_score),
                        reasons=reasons,
                        gaps=gaps
                    ))
                
                debug_hash = hashlib.sha256(role.encode()).hexdigest()[:8]
                amplitude_service.track(
                    event_type="linkedin_jobs_searched",
                    event_properties={
                        "hash": debug_hash,
                        "count": len(jobs),
                        "source": "free-fallback-timeout"
                    }
                )
                
                return LinkedInJobSearchResponse(
                    jobs=jobs,
                    nextCursor=None,
                    debug={
                        "source": "free-fallback-timeout",
                        "count": len(jobs),
                        "hash": debug_hash,
                        "message": "RapidAPI timeout, using free job service"
                    }
                )
            except Exception as e:
                print(f"[LinkedIn Jobs] Request error: {e} - falling back to free job service")
                from app.services.free_job_svc import free_job_service
                from app.services.job_scoring_svc import JobScoringService
                
                free_jobs_data = free_job_service.search_jobs(role, location, limit)
                scoring_service = JobScoringService()
                candidate_vector = scoring_service.build_candidate_skill_vector({
                    "skills": {"core": resume_skills, "adjacent": [], "advanced": []}
                })
                
                jobs = []
                for job_data in free_jobs_data:
                    jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('description', '')}"
                    jd_vector = scoring_service.extract_jd_skills(jd_text)
                    match_score, reasons, gaps = scoring_service.score_job_match(
                        candidate_vector,
                        jd_vector,
                        ""
                    )
                    
                    jobs.append(LinkedInJobSearchItem(
                        id=job_data.get("id", f"free-exception-{abs(hash(job_data.get('url', '') + job_data.get('title', '')))}"),
                        title=job_data.get("title", "Job Opening"),
                        company=job_data.get("company", "Company"),
                        location=job_data.get("location", location),
                        url=job_data.get("url", "https://example.com/job"),
                        listed_at=datetime.now().isoformat(),
                        source=job_data.get("source", "free-fallback-exception"),
                        description_snippet=job_data.get("description", "")[:200] if job_data.get("description") else None,
                        matchScore=int(match_score),
                        reasons=reasons,
                        gaps=gaps
                    ))
                
                debug_hash = hashlib.sha256(role.encode()).hexdigest()[:8]
                amplitude_service.track(
                    event_type="linkedin_jobs_searched",
                    event_properties={
                        "hash": debug_hash,
                        "count": len(jobs),
                        "source": "free-fallback-exception"
                    }
                )
                
                return LinkedInJobSearchResponse(
                    jobs=jobs,
                    nextCursor=None,
                    debug={
                        "source": "free-fallback-exception",
                        "count": len(jobs),
                        "hash": debug_hash,
                        "message": f"RapidAPI error: {str(e)}, using free job service"
                    }
                )
        
        # Track event (only hash/counts, no PII)
        debug_hash = hashlib.sha256(role.encode()).hexdigest()[:8]
        amplitude_service.track(
            event_type="linkedin_jobs_searched",
            event_properties={
                "hash": debug_hash,
                "count": len(jobs),
                "source": "linkedin-rapidapi"
            }
        )
        
        return LinkedInJobSearchResponse(
            jobs=jobs,
            nextCursor=next_cursor,
            debug={
                "source": "linkedin-rapidapi",
                "count": len(jobs),
                "hash": debug_hash
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LinkedIn Jobs] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

