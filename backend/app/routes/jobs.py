from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import List
from app.models.schemas import Job
from app.services.dedalus_svc import dedalus_service
from app.services.amplitude import amplitude_service
import hashlib

router = APIRouter(prefix="/jobs", tags=["jobs"])


class AutoResearchRequest(BaseModel):
    target_role: str
    resume_summary: str
    resume_text: str | None = None  # Full resume text for hashing


@router.post("/autoResearch")
async def auto_research(
    request: AutoResearchRequest,
    response: Response,
    hash: str | None = Query(None, description="Resume hash for cache busting")
):
    """
    Auto-research jobs using Dedalus or fallback heuristics.
    Returns normalized Job[] with progress logging.
    Only returns jobs with valid URLs.
    """
    # Use resume_text if provided, otherwise use resume_summary
    resume_text = request.resume_text or request.resume_summary
    
    # Compute resume hash
    resume_hash = hashlib.sha256(resume_text.encode('utf-8')).hexdigest()
    debug_hash = resume_hash[:8]
    
    # Add Cache-Control header
    response.headers["Cache-Control"] = "no-store"
    
    # Extract top skills from resume_text using keyword groups
    from app.routes.analyze import DOMAIN_KEYWORDS, extract_keywords, classify_domain
    
    domain, _ = classify_domain(resume_text)
    top_skills = extract_keywords(resume_text, domain)[:6]  # Top 6 skills for job search
    
    # Check if Dedalus is available
    dedalus_available = bool(dedalus_service.dedalus_api_key and dedalus_service.dedalus_api_key.strip())
    mcp_available = bool(dedalus_service.dedalus_mcp_service and dedalus_service.dedalus_mcp_service.mcp_available)
    
    # If no Dedalus and no MCP, return empty with clear message
    if not dedalus_available and not mcp_available:
        print(f"[Jobs] No Dedalus API key available: hash={debug_hash}")
        return {
            "items": [],
            "debug": {
                "hash": debug_hash,
                "source": "none",
                "count": 0
            }
        }
    
    try:
        # Progress callback for logging (can be extended to SSE/WebSocket)
        progress_logs = []
        
        def progress_callback(message: str):
            progress_logs.append(message)
            print(f"[Progress] {message}")
        
        # Call Dedalus service with resume_text for better matching
        jobs = dedalus_service.run_job_research(
            target_role=request.target_role,
            resume_summary=request.resume_summary,
            progress_callback=progress_callback
        )
        
        # Annotate jobs with source if not already set
        for job in jobs:
            if not job.source:
                if mcp_available:
                    job.source = "dedalus-mcp"
                elif dedalus_available:
                    job.source = "dedalus"
                else:
                    job.source = "fallback"
        
        # Filter out jobs without valid URLs
        valid_jobs = []
        for job in jobs:
            # Check if job has a valid URL (not empty, not Google search, not example.com)
            job_url_str = str(job.jdUrl) if job.jdUrl else ""
            if job_url_str and job_url_str != "" and "google.com/search" not in job_url_str and "example.com" not in job_url_str:
                valid_jobs.append(job)
        
        # Convert to dicts
        items = [job.model_dump() for job in valid_jobs]
        
        # Determine source - check MCP first, then legacy
        if mcp_available:
            source = "dedalus-mcp"
        elif dedalus_available:
            source = "dedalus"
        else:
            source = "fallback"
        
        # Send Amplitude event (only hash/counts/source, no raw text)
        amplitude_service.track(
            event_type="jobs_fetched_server",
            event_properties={
                "hash": debug_hash,
                "source": source,
                "count": len(items),
            }
        )
        
        # Log only hash, count, source (no resume text)
        print(f"[Jobs] Completed: hash={debug_hash}, source={source}, count={len(items)}")
        
        # Return response with items array and debug info
        return {
            "items": items,
            "debug": {
                "hash": debug_hash,
                "source": source,
                "count": len(items)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job research failed: {str(e)}")

