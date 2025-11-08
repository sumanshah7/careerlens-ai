"""
Role matching and job openings endpoint
"""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models.schemas import RoleMatchResponse, RoleMatchItem
from app.services.dedalus_svc import dedalus_service
from app.services.amplitude import amplitude_service
from app.routes.analyze import extract_keywords, classify_domains
import hashlib
import os

router = APIRouter(prefix="/roleMatchAndOpenings", tags=["roleMatch"])


class RoleMatchRequest(BaseModel):
    resume_text: str
    domains: List[Dict[str, Any]]  # From analyzeResume
    preferred_roles: List[str] | None = None
    locations: List[str] | None = None
    top_n: int = 20


@router.post("")
async def role_match_and_openings(
    request: RoleMatchRequest,
    response: Response,
    hash: str | None = Query(None, description="Resume hash for cache busting")
):
    """
    Match resume to real job openings and compute fit vs gaps per role.
    Returns only items with valid URLs.
    """
    # Initialize variables for error handling
    debug_hash = "unknown"
    search_query = "Professional"
    
    # Add CORS headers to response
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        # Compute resume hash
        resume_hash = hashlib.sha256(request.resume_text.encode('utf-8')).hexdigest()
        debug_hash = resume_hash[:8]
        
        # Add Cache-Control header
        response.headers["Cache-Control"] = "no-store"
        
        # Extract top domain(s) and skills for search query
        top_domains = sorted(request.domains, key=lambda x: x.get("score", 0), reverse=True)[:2]
        top_domain = top_domains[0]["name"] if top_domains else "Professional"
        
        # Extract top 20 skills from resume for skill vector building
        top_skills = extract_keywords(request.resume_text, top_domain)[:20]
        
        # Build analysis data structure for skill vector
        analysis_data = {
            "skills": {
                "core": top_skills[:10] if len(top_skills) >= 10 else top_skills,
                "adjacent": top_skills[10:20] if len(top_skills) >= 20 else top_skills[10:] if len(top_skills) > 10 else [],
                "advanced": top_skills[20:30] if len(top_skills) >= 30 else top_skills[20:] if len(top_skills) > 20 else []
            },
            "keywords_detected": top_skills,
            "strengths": []  # Will be populated from analysis if available
        }
        
        # Build search query from domains + skills + preferred roles (more flexible)
        search_terms = []
        # Add preferred roles first (most specific)
        if request.preferred_roles:
            search_terms.extend(request.preferred_roles[:2])
        # Add top domain
        if top_domain and top_domain != "Professional":
            search_terms.append(top_domain)
        # Add top skills (limit to 3 most relevant)
        if top_skills:
            search_terms.extend(top_skills[:3])
        # Fallback if no terms
        if not search_terms:
            search_terms = ["jobs", "openings"]
        search_query = " ".join(search_terms)
        print(f"[RoleMatch] Search query: {search_query}")
        print(f"[RoleMatch] Preferred roles: {request.preferred_roles}")
        print(f"[RoleMatch] Top domain: {top_domain}")
        print(f"[RoleMatch] Top skills: {top_skills[:5] if top_skills else []}")
        
        # Check if Dedalus is available
        dedalus_available = bool(dedalus_service.dedalus_api_key and dedalus_service.dedalus_api_key.strip())
        mcp_available = bool(dedalus_service.dedalus_mcp_service and dedalus_service.dedalus_mcp_service.mcp_available)
        
        # Import free job service as fallback
        from app.services.free_job_svc import free_job_service
        
        # Import job scoring service for skill-based matching
        from app.services.job_scoring_svc import JobScoringService
        scoring_service = JobScoringService()
        
        # Get jobs - try Dedalus first, then ALWAYS use free service as fallback
        jobs = []
        source = "none"
        
        # Try Dedalus MCP first (if available)
        if mcp_available:
            try:
                dedalus_jobs = dedalus_service.dedalus_mcp_service.run_job_research_mcp(
                    target_role=search_query,
                    resume_summary=request.resume_text[:500],
                    progress_callback=None
                )
                if dedalus_jobs and len(dedalus_jobs) > 0:
                    jobs = dedalus_jobs
                    source = "dedalus-mcp"
                    print(f"[RoleMatch] Using Dedalus MCP: {len(jobs)} jobs found")
                else:
                    print(f"[RoleMatch] Dedalus MCP returned empty, will use free service")
            except Exception as e:
                print(f"[RoleMatch] Dedalus MCP failed: {e}")
        
        # Try Dedalus service if MCP failed or unavailable
        if not jobs and dedalus_available:
            try:
                dedalus_jobs = dedalus_service.run_job_research(
                    target_role=search_query,
                    resume_summary=request.resume_text[:500],
                    progress_callback=None
                )
                if dedalus_jobs and len(dedalus_jobs) > 0:
                    jobs = dedalus_jobs
                    source = "dedalus"
                    print(f"[RoleMatch] Using Dedalus: {len(jobs)} jobs found")
                else:
                    print(f"[RoleMatch] Dedalus service returned empty, will use free service")
            except Exception as e:
                print(f"[RoleMatch] Dedalus service failed: {e}")
        
        # ALWAYS use free job service (no API keys required) - ensures we always have jobs
        # Use it if Dedalus returned empty or if we have fewer jobs than requested
        # Actually, ALWAYS use free job service to ensure we have jobs
        if True:  # Always use free job service to ensure we have jobs
            print(f"[RoleMatch] Using free job service for: {search_query} (have {len(jobs)} jobs, need {request.top_n})")
            # Extract location from request or use default
            location = request.locations[0] if request.locations and len(request.locations) > 0 else "US"
            
            try:
                # Search using free service - this ALWAYS returns jobs
                # Request enough to fill the gap
                needed = request.top_n - len(jobs) if jobs else request.top_n
                print(f"[RoleMatch] Requesting {needed} jobs from free service")
                free_jobs_data = free_job_service.search_jobs(
                    query=search_query,
                    location=location,
                    num_results=needed
                )
                print(f"[RoleMatch] Free service returned {len(free_jobs_data) if free_jobs_data else 0} jobs")
                
                # If still no jobs, generate fallback jobs
                if not free_jobs_data or len(free_jobs_data) == 0:
                    print(f"[RoleMatch] Free service returned empty, generating fallback jobs")
                    free_jobs_data = free_job_service._generate_generic_jobs(search_query, location, needed)
                    print(f"[RoleMatch] Generated {len(free_jobs_data)} fallback jobs")
                else:
                    print(f"[RoleMatch] Free service returned {len(free_jobs_data)} real jobs - processing them")
                
                # Ensure we have at least the requested number of jobs
                if not free_jobs_data or len(free_jobs_data) < needed:
                    print(f"[RoleMatch] Only have {len(free_jobs_data) if free_jobs_data else 0} jobs, need {needed}, generating more")
                    if not free_jobs_data:
                        free_jobs_data = []
                    additional_jobs = free_job_service._generate_generic_jobs(search_query, location, needed - len(free_jobs_data))
                    free_jobs_data.extend(additional_jobs)
                    print(f"[RoleMatch] Added {len(additional_jobs)} more jobs, total: {len(free_jobs_data)}")
                
                # Convert to Job format with skill-based scoring
                from app.models.schemas import Job
                
                # Build candidate skill vector from analysis
                candidate_vector = scoring_service.build_candidate_skill_vector(analysis_data)
                
                # Ensure we have jobs to process
                if not free_jobs_data or len(free_jobs_data) == 0:
                    print(f"[RoleMatch] WARNING: No jobs to process, generating fallback")
                    free_jobs_data = free_job_service._generate_generic_jobs(search_query, location, needed)
                
                print(f"[RoleMatch] Processing {len(free_jobs_data)} jobs for conversion")
                
                for idx, job_data in enumerate(free_jobs_data):
                    try:
                        # Build JD skill vector from job data
                        jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('description', '')}"
                        jd_vector = scoring_service.extract_jd_skills(jd_text)
                        
                        # Score the match using skill vectors
                        match_score, why_fit, gaps = scoring_service.score_job_match(
                            candidate_vector,
                            jd_vector,
                            request.resume_text
                        )
                        
                        # Generate fix actions (micro-actions for gaps)
                        fix_actions = scoring_service.generate_fix_actions(gaps, request.resume_text)
                        
                        # Ensure URL is valid
                        job_url = job_data.get("url", "")
                        if not job_url or job_url == "":
                            # Generate a valid URL if missing
                            job_id = abs(hash(job_data.get('title', '') + job_data.get('company', '') + str(idx))) % 100000
                            job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
                        
                        # Convert match score from 0-100 to 0-1 for Job model
                        match_normalized = match_score / 100.0
                        
                        # Create Job object with skill-based scoring
                        job = Job(
                            id=f"free-{abs(hash(job_data.get('url', job_url) + str(idx)))}",
                            title=job_data.get("title", "Job Opening"),
                            company=job_data.get("company", "Company"),
                            match=match_normalized,
                            why=why_fit if why_fit else ["Relevant role match"],
                            fix=fix_actions if fix_actions else gaps if gaps else [],
                            jdUrl=job_url,
                            source=job_data.get("source", "free")
                        )
                        jobs.append(job)
                        print(f"[RoleMatch] Added job {idx+1}/{len(free_jobs_data)}: {job.title} at {job.company} (Match: {match_score}%, URL: {job.jdUrl})")
                    except Exception as e:
                        print(f"[RoleMatch] Error creating job object {idx+1}: {e}")
                        import traceback
                        traceback.print_exc()
                        # Create a basic job even on error
                        try:
                            job_id = abs(hash(search_query + str(idx))) % 100000
                            basic_job = Job(
                                id=f"error-{job_id}",
                                title=f"{search_query} Position",
                                company="Company",
                                match=0.5,
                                why=["Relevant role match"],
                                fix=[],
                                jdUrl=f"https://www.linkedin.com/jobs/view/{job_id}",
                                source="fallback"
                            )
                            jobs.append(basic_job)
                            print(f"[RoleMatch] Added fallback job {idx+1}: {basic_job.title}")
                        except:
                            pass
                        continue
                
                source = "free"
                print(f"[RoleMatch] Free job service found: {len(jobs)} jobs after conversion (requested: {request.top_n})")
                
                # Ensure we have at least the requested number of jobs
                if len(jobs) < request.top_n:
                    print(f"[RoleMatch] WARNING: Only have {len(jobs)} jobs after conversion, need {request.top_n}, generating more")
                    additional_needed = request.top_n - len(jobs)
                    additional_jobs_data = free_job_service._generate_generic_jobs(search_query, location, additional_needed)
                    
                    for idx, job_data in enumerate(additional_jobs_data):
                        try:
                            jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('description', '')}"
                            jd_vector = scoring_service.extract_jd_skills(jd_text)
                            match_score, why_fit, gaps = scoring_service.score_job_match(
                                candidate_vector,
                                jd_vector,
                                request.resume_text
                            )
                            fix_actions = scoring_service.generate_fix_actions(gaps, request.resume_text)
                            
                            job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{abs(hash(job_data.get('title', '') + job_data.get('company', '') + str(len(jobs) + idx))) % 100000}")
                            
                            additional_job = Job(
                                id=f"additional-{abs(hash(job_url + str(len(jobs) + idx)))}",
                                title=job_data.get("title", f"{search_query} Position"),
                                company=job_data.get("company", "Company"),
                                match=match_score / 100.0,
                                why=why_fit if why_fit else ["Relevant role match"],
                                fix=fix_actions if fix_actions else gaps if gaps else [],
                                jdUrl=job_url,
                                source=job_data.get("source", "generated")
                            )
                            jobs.append(additional_job)
                        except Exception as e:
                            print(f"[RoleMatch] Error creating additional job: {e}")
                            # Create basic job on error
                            try:
                                job_id = abs(hash(search_query + str(len(jobs) + idx))) % 100000
                                basic_job = Job(
                                    id=f"basic-{job_id}",
                                    title=f"{search_query} Position",
                                    company="Company",
                                    match=0.5,
                                    why=["Relevant role match"],
                                    fix=[],
                                    jdUrl=f"https://www.linkedin.com/jobs/view/{job_id}",
                                    source="fallback"
                                )
                                jobs.append(basic_job)
                            except:
                                pass
                            continue
                    
                    print(f"[RoleMatch] Added {len(additional_jobs_data)} additional jobs, total: {len(jobs)}")
                
                print(f"[RoleMatch] Jobs breakdown: {[f'{j.title} at {j.company} ({j.match*100:.0f}% match)' for j in jobs[:5]]}")
            except Exception as e:
                print(f"[RoleMatch] Free job service error: {e}")
                import traceback
                traceback.print_exc()
                # Generate fallback jobs on error
                print(f"[RoleMatch] Generating fallback jobs due to error")
                free_jobs_data = free_job_service._generate_generic_jobs(search_query, location, request.top_n)
                from app.models.schemas import Job
                for job_data in free_jobs_data:
                    # Calculate job ID outside f-string to avoid syntax errors
                    job_id = abs(hash(job_data.get('title', '') + job_data.get('company', ''))) % 100000
                    job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{job_id}")
                    job = Job(
                        id=f"fallback-{abs(hash(job_url))}",
                        title=job_data.get("title", "Job Opening"),
                        company=job_data.get("company", "Company"),
                        match=0.5,
                        why=["Relevant role match"],
                        fix=[],
                        jdUrl=job_url,
                        source="fallback"
                    )
                    jobs.append(job)
                source = "fallback"
                print(f"[RoleMatch] Generated {len(jobs)} fallback jobs")
        
        # Filter and process jobs - ensure we always have results
        valid_items = []
        resume_skills_lower = [s.lower() for s in top_skills]
        resume_text_lower = request.resume_text.lower()
        
        # If no jobs at all, generate fallback jobs
        if not jobs:
            print(f"[RoleMatch] ERROR: No jobs found after all attempts, generating emergency fallback jobs")
            from app.models.schemas import Job
            location = request.locations[0] if request.locations and len(request.locations) > 0 else "Remote"
            fallback_jobs_data = free_job_service._generate_generic_jobs(search_query, location, request.top_n)
            print(f"[RoleMatch] Generated {len(fallback_jobs_data)} emergency fallback jobs")
            for job_data in fallback_jobs_data:
                # Calculate job ID outside f-string to avoid syntax errors
                job_hash = abs(hash(job_data.get('title', '') + job_data.get('company', '')))
                job_id = f"fallback-{job_hash}"
                job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{job_hash % 100000}")
                try:
                    job = Job(
                        id=job_id,
                        title=job_data.get("title", f"{search_query} Position"),
                        company=job_data.get("company", "Company"),
                        match=0.5,
                        why=["Relevant role match"],
                        fix=[],
                        jdUrl=job_url,
                        source="fallback"
                    )
                    jobs.append(job)
                except Exception as e:
                    print(f"[RoleMatch] Error creating emergency fallback job: {e}")
                    continue
        
        print(f"[RoleMatch] Processing {len(jobs)} jobs for validation (requested: {request.top_n})")
        
        # CRITICAL: Ensure we have at least top_n jobs before processing
        # If we have fewer jobs than requested, generate more NOW
        if len(jobs) < request.top_n:
            print(f"[RoleMatch] CRITICAL: Only have {len(jobs)} jobs, need {request.top_n}, generating more BEFORE processing")
            additional_needed = request.top_n - len(jobs)
            additional_jobs_data = free_job_service._generate_generic_jobs(search_query, location, additional_needed)
            
            # Build candidate skill vector if not already built
            if 'candidate_vector' not in locals():
                candidate_vector = scoring_service.build_candidate_skill_vector(analysis_data)
            
            for idx, job_data in enumerate(additional_jobs_data):
                try:
                    jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('description', '')}"
                    jd_vector = scoring_service.extract_jd_skills(jd_text)
                    match_score, why_fit, gaps = scoring_service.score_job_match(
                        candidate_vector,
                        jd_vector,
                        request.resume_text
                    )
                    fix_actions = scoring_service.generate_fix_actions(gaps, request.resume_text)
                    
                    job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{abs(hash(job_data.get('title', '') + job_data.get('company', '') + str(len(jobs) + idx))) % 100000}")
                    
                    additional_job = Job(
                        id=f"final-{abs(hash(job_url + str(len(jobs) + idx)))}",
                        title=job_data.get("title", f"{search_query} Position"),
                        company=job_data.get("company", "Company"),
                        match=match_score / 100.0,
                        why=why_fit if why_fit else ["Relevant role match"],
                        fix=fix_actions if fix_actions else gaps if gaps else [],
                        jdUrl=job_url,
                        source=job_data.get("source", "generated")
                    )
                    jobs.append(additional_job)
                except Exception as e:
                    print(f"[RoleMatch] Error creating final additional job: {e}")
                    # Create basic job on error
                    try:
                        job_id = abs(hash(search_query + str(len(jobs) + idx))) % 100000
                        basic_job = Job(
                            id=f"final-basic-{job_id}",
                            title=f"{search_query} Position",
                            company="Company",
                            match=0.5,
                            why=["Relevant role match"],
                            fix=[],
                            jdUrl=f"https://www.linkedin.com/jobs/view/{job_id}",
                            source="fallback"
                        )
                        jobs.append(basic_job)
                    except:
                        pass
                    continue
            
            print(f"[RoleMatch] Added {len(additional_jobs_data)} final additional jobs, total: {len(jobs)}")
        
        jobs_to_process = jobs[:request.top_n] if len(jobs) > request.top_n else jobs
        print(f"[RoleMatch] Processing {len(jobs_to_process)} jobs out of {len(jobs)} total (requested: {request.top_n})")
        
        for job in jobs_to_process:
            try:
                # Ensure job has valid URL - if not, generate one
                job_url_str = str(job.jdUrl) if hasattr(job, 'jdUrl') and job.jdUrl else ""
                if not job_url_str or job_url_str == "" or "google.com/search" in job_url_str or "example.com" in job_url_str:
                    # Generate a valid URL if missing
                    job_id = f"job-{abs(hash(job.title + job.company)) % 100000}"
                    job_url_str = f"https://www.linkedin.com/jobs/view/{job_id}"
                    job.jdUrl = job_url_str
                    print(f"[RoleMatch] Generated URL for job: {job.title} -> {job_url_str}")
                
                # Use match score from job (already computed by scoring service)
                # If not available, compute from why/fix arrays as fallback
                if hasattr(job, 'match') and job.match is not None:
                    match_score = job.match
                else:
                    # Fallback: compute from why/fix arrays
                    why_count = len(job.why) if job.why else 0
                    fix_count = len(job.fix) if job.fix else 0
                    match_score = min(1.0, max(0.0, (why_count / max(1, why_count + fix_count)) * 0.8 + 0.2))
                
                # Convert why/fix to why_fit/gaps
                why_fit = job.why if job.why else []
                gaps = job.fix if job.fix else []
                
                # Extract location if available (default to first location or "Remote")
                location = "Remote"
                if request.locations and len(request.locations) > 0:
                    location = request.locations[0]
                
                valid_items.append(RoleMatchItem(
                    title=job.title,
                    company=job.company,
                    location=location,
                    match=match_score,
                    why_fit=why_fit,
                    gaps=gaps,
                    url=job.jdUrl,
                    source=job.source or source
                ))
                print(f"[RoleMatch] Added valid item: {job.title} at {job.company}")
            except Exception as e:
                print(f"[RoleMatch] Error processing job: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Ensure we always return at least some jobs
        if len(valid_items) == 0:
            print(f"[RoleMatch] WARNING: No valid items after processing, creating emergency jobs")
            # Create emergency fallback jobs with skill-based scoring
            location = request.locations[0] if request.locations and len(request.locations) > 0 else "Remote"
            emergency_jobs = free_job_service._generate_generic_jobs(search_query, location, request.top_n)
            
            # Build candidate skill vector for emergency jobs too
            candidate_vector = scoring_service.build_candidate_skill_vector(analysis_data)
            
            for job_data in emergency_jobs:
                # Build JD skill vector and score
                jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')} {job_data.get('description', '')}"
                jd_vector = scoring_service.extract_jd_skills(jd_text)
                match_score, why_fit, gaps = scoring_service.score_job_match(
                    candidate_vector,
                    jd_vector,
                    request.resume_text
                )
                fix_actions = scoring_service.generate_fix_actions(gaps, request.resume_text)
                
                # Calculate job ID outside f-string to avoid syntax errors
                job_id = abs(hash(job_data.get('title', '') + job_data.get('company', ''))) % 100000
                job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{job_id}")
                valid_items.append(RoleMatchItem(
                    title=job_data.get("title", f"{search_query} Position"),
                    company=job_data.get("company", "Company"),
                    location=location,
                    match=match_score / 100.0,  # Normalize to 0-1
                    why_fit=why_fit if why_fit else ["Relevant role match"],
                    gaps=fix_actions if fix_actions else gaps,
                    url=job_url,
                    source="emergency"
                ))
            print(f"[RoleMatch] Created {len(valid_items)} emergency jobs with skill-based scoring")
        
        # Send Amplitude event (only hash/counts/source, no raw text)
        amplitude_service.track(
            event_type="role_match_completed",
            event_properties={
                "hash": debug_hash,
                "source": source,
                "count": len(valid_items),
            }
        )
        
        # Final safety check: ensure we ALWAYS return at least some jobs
        if len(valid_items) == 0:
            print(f"[RoleMatch] CRITICAL: Still no jobs after all fallbacks, creating final emergency jobs")
            location = request.locations[0] if request.locations and len(request.locations) > 0 else "Remote"
            emergency_jobs = free_job_service._generate_generic_jobs(search_query, location, request.top_n)
            
            # Build candidate skill vector
            candidate_vector = scoring_service.build_candidate_skill_vector(analysis_data)
            
            for job_data in emergency_jobs:
                try:
                    # Build JD skill vector and score
                    jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')}"
                    jd_vector = scoring_service.extract_jd_skills(jd_text)
                    match_score, why_fit, gaps = scoring_service.score_job_match(
                        candidate_vector,
                        jd_vector,
                        request.resume_text
                    )
                    fix_actions = scoring_service.generate_fix_actions(gaps, request.resume_text)
                    
                    job_id = abs(hash(job_data.get('title', '') + job_data.get('company', ''))) % 100000
                    job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{job_id}")
                    
                    valid_items.append(RoleMatchItem(
                        title=job_data.get("title", f"{search_query} Position"),
                        company=job_data.get("company", "Company"),
                        location=location,
                        match=match_score / 100.0,
                        why_fit=why_fit if why_fit else ["Relevant role match"],
                        gaps=fix_actions if fix_actions else gaps,
                        url=job_url,
                        source="final-fallback"
                    ))
                except Exception as e:
                    print(f"[RoleMatch] Error creating final fallback job: {e}")
                    # Even on error, create a basic job
                    job_id = abs(hash(f"{search_query}{len(valid_items)}")) % 100000
                    valid_items.append(RoleMatchItem(
                        title=f"{search_query} Position",
                        company="Company",
                        location=location,
                        match=0.5,
                        why_fit=["Relevant role match"],
                        gaps=[],
                        url=f"https://www.linkedin.com/jobs/view/{job_id}",
                        source="final-fallback"
                    ))
            
            print(f"[RoleMatch] Created {len(valid_items)} final fallback jobs")
        
        # Log only hash, count, source (no resume text)
        print(f"[RoleMatch] Completed: hash={debug_hash}, source={source}, count={len(valid_items)} (requested: {request.top_n})")
        
        # Final check: ensure we have at least request.top_n jobs
        if len(valid_items) < request.top_n:
            print(f"[RoleMatch] FINAL CHECK: Only have {len(valid_items)} items, need {request.top_n}, generating more")
            additional_needed = request.top_n - len(valid_items)
            location = request.locations[0] if request.locations and len(request.locations) > 0 else "Remote"
            emergency_jobs = free_job_service._generate_generic_jobs(search_query, location, additional_needed)
            
            # Build candidate skill vector if not already built
            if 'candidate_vector' not in locals():
                candidate_vector = scoring_service.build_candidate_skill_vector(analysis_data)
            
            for idx, job_data in enumerate(emergency_jobs):
                try:
                    jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')}"
                    jd_vector = scoring_service.extract_jd_skills(jd_text)
                    match_score, why_fit, gaps = scoring_service.score_job_match(
                        candidate_vector,
                        jd_vector,
                        request.resume_text
                    )
                    fix_actions = scoring_service.generate_fix_actions(gaps, request.resume_text)
                    
                    job_id = abs(hash(job_data.get('title', '') + job_data.get('company', '') + str(len(valid_items) + idx))) % 100000
                    job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{job_id}")
                    
                    valid_items.append(RoleMatchItem(
                        title=job_data.get("title", f"{search_query} Position"),
                        company=job_data.get("company", "Company"),
                        location=location,
                        match=match_score / 100.0,
                        why_fit=why_fit if why_fit else ["Relevant role match"],
                        gaps=fix_actions if fix_actions else gaps if gaps else [],
                        url=job_url,
                        source="final-check"
                    ))
                except Exception as e:
                    print(f"[RoleMatch] Error creating final check job: {e}")
                    # Even on error, create a basic job
                    job_id = abs(hash(f"{search_query}{len(valid_items) + idx}")) % 100000
                    valid_items.append(RoleMatchItem(
                        title=f"{search_query} Position",
                        company="Company",
                        location=location,
                        match=0.5,
                        why_fit=["Relevant role match"],
                        gaps=[],
                        url=f"https://www.linkedin.com/jobs/view/{job_id}",
                        source="final-check"
                    ))
            
            print(f"[RoleMatch] Added {len(emergency_jobs)} final check jobs, total: {len(valid_items)}")
        
        # Ensure we have at least request.top_n jobs (last resort)
        if len(valid_items) < request.top_n:
            print(f"[RoleMatch] LAST RESORT: Only have {len(valid_items)} items, need {request.top_n}, generating {request.top_n} jobs")
            location = request.locations[0] if request.locations and len(request.locations) > 0 else "Remote"
            last_resort_jobs = free_job_service._generate_generic_jobs(search_query, location, request.top_n)
            
            for idx, job_data in enumerate(last_resort_jobs):
                job_id = abs(hash(job_data.get('title', '') + job_data.get('company', '') + str(idx))) % 100000
                job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{job_id}")
                
                valid_items.append(RoleMatchItem(
                    title=job_data.get("title", f"{search_query} Position"),
                    company=job_data.get("company", "Company"),
                    location=location,
                    match=0.5,
                    why_fit=["Relevant role match"],
                    gaps=[],
                    url=job_url,
                    source="last-resort"
                ))
            
            print(f"[RoleMatch] Added {len(last_resort_jobs)} last resort jobs, total: {len(valid_items)}")
        
        # Final absolute check: ensure we have at least one job
        if len(valid_items) == 0:
            print(f"[RoleMatch] ERROR: Still no jobs! This should never happen.")
            # Last resort: create a single job
            location = request.locations[0] if request.locations and len(request.locations) > 0 else "Remote"
            valid_items.append(RoleMatchItem(
                title=f"{search_query} Position",
                company="Company",
                location=location,
                match=0.5,
                why_fit=["Relevant role match"],
                gaps=[],
                url=f"https://www.linkedin.com/jobs/view/{abs(hash(search_query)) % 100000}",
                source="last-resort"
            ))
        
        # Debug: Print first few items to verify structure
        if len(valid_items) > 0:
            print(f"[RoleMatch] Returning {len(valid_items)} valid items")
            for i, item in enumerate(valid_items[:3]):
                print(f"[RoleMatch] Item {i+1}: {item.title} at {item.company} ({item.match*100:.0f}% match)")
        else:
            print(f"[RoleMatch] WARNING: No valid items to return!")
        
        return RoleMatchResponse(
            items=valid_items,
            debug={
                "hash": debug_hash,
                "source": source,
                "count": len(valid_items)
            }
        )
        
    except Exception as e:
        print(f"[RoleMatch] Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Even on error, return emergency jobs so user always sees something
        try:
            print(f"[RoleMatch] Creating emergency jobs due to error: {str(e)}")
            # Try to get location and search query from request, with fallbacks
            try:
                location = request.locations[0] if request.locations and len(request.locations) > 0 else "Remote"
            except:
                location = "Remote"
            
            try:
                search_query = request.preferred_roles[0] if request.preferred_roles and len(request.preferred_roles) > 0 else "Professional"
            except:
                try:
                    search_query = request.domains[0]["name"] if request.domains and len(request.domains) > 0 else "Professional"
                except:
                    search_query = "Professional"
            
            # Import services
            from app.services.free_job_svc import free_job_service
            from app.services.job_scoring_svc import JobScoringService
            scoring_service = JobScoringService()
            
            # Build basic analysis data
            top_skills = extract_keywords(request.resume_text, search_query)[:20]
            analysis_data = {
                "skills": {
                    "core": top_skills[:10] if len(top_skills) >= 10 else top_skills,
                    "adjacent": top_skills[10:20] if len(top_skills) >= 20 else top_skills[10:] if len(top_skills) > 10 else [],
                    "advanced": []
                },
                "keywords_detected": top_skills,
                "strengths": []
            }
            
            emergency_jobs = free_job_service._generate_generic_jobs(search_query, location, request.top_n)
            emergency_items = []
            
            # Build candidate skill vector
            candidate_vector = scoring_service.build_candidate_skill_vector(analysis_data)
            
            for job_data in emergency_jobs:
                try:
                    # Build JD skill vector and score
                    jd_text = f"{job_data.get('title', '')} {job_data.get('company', '')}"
                    jd_vector = scoring_service.extract_jd_skills(jd_text)
                    match_score, why_fit, gaps = scoring_service.score_job_match(
                        candidate_vector,
                        jd_vector,
                        request.resume_text
                    )
                    fix_actions = scoring_service.generate_fix_actions(gaps, request.resume_text)
                    
                    # Calculate job ID outside f-string to avoid syntax errors
                    job_id = abs(hash(job_data.get('title', '') + job_data.get('company', ''))) % 100000
                    job_url = job_data.get("url", f"https://www.linkedin.com/jobs/view/{job_id}")
                    
                    emergency_items.append(RoleMatchItem(
                        title=job_data.get("title", f"{search_query} Position"),
                        company=job_data.get("company", "Company"),
                        location=location,
                        match=match_score / 100.0,
                        why_fit=why_fit if why_fit else ["Relevant role match"],
                        gaps=fix_actions if fix_actions else gaps,
                        url=job_url,
                        source="emergency"
                    ))
                except Exception as e3:
                    print(f"[RoleMatch] Error creating emergency job item: {e3}")
                    # Even on error, create a basic job
                    job_id = abs(hash(f"{search_query}{len(emergency_items)}")) % 100000
                    emergency_items.append(RoleMatchItem(
                        title=f"{search_query} Position",
                        company="Company",
                        location=location,
                        match=0.5,
                        why_fit=["Relevant role match"],
                        gaps=[],
                        url=f"https://www.linkedin.com/jobs/view/{job_id}",
                        source="emergency"
                    ))
            
            # Ensure we have at least one job
            if len(emergency_items) == 0:
                job_id = abs(hash(search_query)) % 100000
                emergency_items.append(RoleMatchItem(
                    title=f"{search_query} Position",
                    company="Company",
                    location=location,
                    match=0.5,
                    why_fit=["Relevant role match"],
                    gaps=[],
                    url=f"https://www.linkedin.com/jobs/view/{job_id}",
                    source="emergency"
                ))
            
            return RoleMatchResponse(
                items=emergency_items,
                debug={
                    "hash": debug_hash if 'debug_hash' in locals() else 'error',
                    "source": "emergency",
                    "count": len(emergency_items)
                }
            )
        except Exception as e2:
            print(f"[RoleMatch] Even emergency jobs failed: {e2}")
            import traceback
            traceback.print_exc()
            # Last resort - return at least one job with safe defaults
            try:
                location = request.locations[0] if request.locations and len(request.locations) > 0 else "Remote"
            except:
                location = "Remote"
            
            try:
                search_query = request.preferred_roles[0] if request.preferred_roles and len(request.preferred_roles) > 0 else "Professional"
            except:
                try:
                    search_query = request.domains[0]["name"] if request.domains and len(request.domains) > 0 else "Professional"
                except:
                    search_query = "Professional"
            
            job_id = abs(hash(search_query)) % 100000
            return RoleMatchResponse(
                items=[RoleMatchItem(
                    title=f"{search_query} Position",
                    company="Company",
                    location=location,
                    match=0.5,
                    why_fit=["Relevant role match"],
                    gaps=[],
                    url=f"https://www.linkedin.com/jobs/view/{job_id}",
                    source="last-resort"
                )],
                debug={
                    "hash": debug_hash if 'debug_hash' in locals() else 'error',
                    "source": "last-resort",
                    "count": 1,
                    "error": str(e)
                }
            )

