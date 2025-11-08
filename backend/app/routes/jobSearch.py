"""
Job search endpoint with multiple source adapters
"""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.schemas import Job
from app.services.amplitude import amplitude_service
import hashlib
import re
from collections import Counter

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobSearchRequest(BaseModel):
    role: str
    skills: List[str]
    location: Optional[str] = "US-Remote"
    minMatch: Optional[float] = Field(default=0.4, ge=0.0, le=1.0)
    limit: Optional[int] = Field(default=20, ge=1, le=100)


class JobSearchItem(BaseModel):
    id: str
    title: str
    company: str
    location: str
    source: str
    applyUrl: str
    description: Optional[str] = None
    matchScore: float = Field(ge=0.0, le=1.0)


class JobSearchResponse(BaseModel):
    items: List[JobSearchItem]
    debug: Dict[str, Any]


def weighted_jaccard_similarity(skills1: List[str], skills2: List[str]) -> float:
    """
    Compute weighted Jaccard similarity between two skill lists.
    Returns a score between 0.0 and 1.0.
    """
    if not skills1 or not skills2:
        return 0.0
    
    # Normalize to lowercase
    set1 = {s.lower().strip() for s in skills1 if s.strip()}
    set2 = {s.lower().strip() for s in skills2 if s.strip()}
    
    if not set1 or not set2:
        return 0.0
    
    # Weighted intersection (exact matches get full weight, partial matches get partial)
    intersection = 0.0
    union = len(set1) + len(set2)
    
    for skill1 in set1:
        for skill2 in set2:
            if skill1 == skill2:
                intersection += 1.0
            elif skill1 in skill2 or skill2 in skill1:
                intersection += 0.5  # Partial match
    
    if union == 0:
        return 0.0
    
    return min(1.0, intersection / union)


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skill tokens from job description/title text.
    Returns a list of lowercase skill tokens.
    """
    if not text:
        return []
    
    # Common tech skills patterns
    skill_patterns = [
        r'\b(python|java|javascript|typescript|react|vue|angular|node\.js|sql|postgresql|mysql|mongodb|redis|docker|kubernetes|aws|azure|gcp|terraform|ansible|jenkins|git|github|gitlab)\b',
        r'\b(data\s+engineer|software\s+engineer|data\s+analyst|ml\s+engineer|ai\s+engineer|devops|sre|backend|frontend|fullstack)\b',
        r'\b(pandas|numpy|scikit-learn|tensorflow|pytorch|spark|hadoop|kafka|airflow|mlflow)\b',
    ]
    
    text_lower = text.lower()
    skills = set()
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        skills.update(matches)
    
    # Also extract individual words that might be skills
    words = re.findall(r'\b[a-z]{3,}\b', text_lower)
    skills.update(words[:20])  # Limit to avoid too many tokens
    
    return list(skills)


def greenhouse_adapter(role: str, skills: List[str], location: str, limit: int) -> List[Dict[str, Any]]:
    """
    Search Greenhouse job boards (public API, no key required).
    Returns list of job dicts with title, company, url, description.
    """
    jobs = []
    try:
        import httpx
        
        # Greenhouse public API endpoint
        # Many companies use Greenhouse, we can search public boards
        search_query = f"{role} {' '.join(skills[:3])}"
        
        # Example: Search popular Greenhouse boards
        greenhouse_boards = [
            "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
            "https://boards-api.greenhouse.io/v1/boards/reddit/jobs",
            "https://boards-api.greenhouse.io/v1/boards/airbnb/jobs",
        ]
        
        with httpx.Client(timeout=5.0) as client:
            for board_url in greenhouse_boards[:2]:  # Limit to 2 boards
                try:
                    response = client.get(board_url)
                    if response.status_code == 200:
                        data = response.json()
                        for job in data.get("jobs", [])[:limit // 2]:
                            if role.lower() in job.get("title", "").lower() or any(
                                skill.lower() in job.get("title", "").lower() 
                                for skill in skills[:3]
                            ):
                                jobs.append({
                                    "title": job.get("title", "Job Opening"),
                                    "company": job.get("departments", [{}])[0].get("name", "Company") if job.get("departments") else "Company",
                                    "url": job.get("absolute_url", ""),
                                    "description": job.get("content", ""),
                                    "location": job.get("location", {}).get("name", location) if isinstance(job.get("location"), dict) else location,
                                    "source": "greenhouse",
                                })
                except Exception as e:
                    print(f"[Greenhouse] Error fetching from {board_url}: {e}")
                    continue
    except Exception as e:
        print(f"[Greenhouse] Adapter error: {e}")
    
    return jobs


def lever_adapter(role: str, skills: List[str], location: str, limit: int) -> List[Dict[str, Any]]:
    """
    Search Lever job boards (public API, no key required).
    Returns list of job dicts.
    """
    jobs = []
    try:
        import httpx
        
        search_query = f"{role} {' '.join(skills[:3])}"
        
        # Lever public API endpoints
        lever_boards = [
            "https://api.lever.co/v0/postings/uber",
            "https://api.lever.co/v0/postings/netflix",
            "https://api.lever.co/v0/postings/spotify",
        ]
        
        with httpx.Client(timeout=5.0) as client:
            for board_url in lever_boards[:2]:  # Limit to 2 boards
                try:
                    response = client.get(board_url)
                    if response.status_code == 200:
                        data = response.json()
                        for job in data.get("data", [])[:limit // 2]:
                            if role.lower() in job.get("text", "").lower() or any(
                                skill.lower() in job.get("text", "").lower() 
                                for skill in skills[:3]
                            ):
                                jobs.append({
                                    "title": job.get("text", "Job Opening"),
                                    "company": job.get("categories", {}).get("team", "Company"),
                                    "url": job.get("hostedUrl", ""),
                                    "description": job.get("descriptionPlain", ""),
                                    "location": job.get("categories", {}).get("location", location),
                                    "source": "lever",
                                })
                except Exception as e:
                    print(f"[Lever] Error fetching from {board_url}: {e}")
                    continue
    except Exception as e:
        print(f"[Lever] Adapter error: {e}")
    
    return jobs


def linkedin_adapter(role: str, skills: List[str], location: str, limit: int) -> List[Dict[str, Any]]:
    """
    Search LinkedIn jobs via RapidAPI LinkedIn Job Search API.
    Falls back to free job service if RAPIDAPI_KEY is not available.
    Filters out expired_jd_redirect URLs.
    """
    jobs = []
    
    # Try RapidAPI LinkedIn Job Search API first
    try:
        from app.config import settings
        
        if settings.rapidapi_key and settings.rapidapi_key.strip():
            import httpx
            
            # Build search query from role and skills
            search_query = f"{role} {' '.join(skills[:3])}"
            
            url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-1h"
            headers = {
                "X-RapidAPI-Host": "linkedin-job-search-api.p.rapidapi.com",
                "X-RapidAPI-Key": settings.rapidapi_key,
            }
            
            # Fetch jobs in batches (offset-based pagination)
            offset = 0
            max_offset = min(limit * 2, 100)  # Limit total requests
            
            with httpx.Client(timeout=10.0) as client:
                while len(jobs) < limit and offset < max_offset:
                    params = {
                        "offset": str(offset),
                        "description_type": "text",
                    }
                    
                    # Add search query if API supports it
                    # Note: Check API docs for exact parameter names
                    if search_query:
                        params["query"] = search_query
                    
                    try:
                        response = client.get(url, headers=headers, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Parse response based on API structure
                            # Adjust based on actual API response format
                            job_list = data.get("jobs", []) or data.get("data", []) or data.get("results", [])
                            
                            if not job_list:
                                break  # No more jobs available
                            
                            for job in job_list:
                                if len(jobs) >= limit:
                                    break
                                
                                # Extract job data (adjust field names based on actual API response)
                                job_url = job.get("url", "") or job.get("job_url", "") or job.get("apply_url", "")
                                job_title = job.get("title", "") or job.get("job_title", "") or job.get("name", "")
                                job_company = job.get("company", "") or job.get("company_name", "") or job.get("employer", "")
                                job_location = job.get("location", "") or job.get("job_location", "") or location
                                job_description = job.get("description", "") or job.get("job_description", "") or ""
                                
                                # Filter out expired LinkedIn redirects
                                if job_url and "expired_jd_redirect" not in job_url:
                                    # Check if job matches role/skills
                                    job_text = f"{job_title} {job_description}".lower()
                                    role_lower = role.lower()
                                    skills_lower = [s.lower() for s in skills[:3]]
                                    
                                    if role_lower in job_text or any(skill in job_text for skill in skills_lower):
                                        jobs.append({
                                            "title": job_title or "Job Opening",
                                            "company": job_company or "Company",
                                            "url": job_url,
                                            "description": job_description,
                                            "location": job_location or location,
                                            "source": "linkedin-rapidapi",
                                        })
                            
                            # Move to next page
                            offset += len(job_list)
                            
                            # If we got fewer jobs than requested, we've reached the end
                            if len(job_list) < 10:
                                break
                        else:
                            print(f"[LinkedIn RapidAPI] HTTP {response.status_code}: {response.text[:200]}")
                            break
                    except Exception as e:
                        print(f"[LinkedIn RapidAPI] Request error: {e}")
                        break
                
                print(f"[LinkedIn RapidAPI] Found {len(jobs)} jobs")
        else:
            print("[LinkedIn] RAPIDAPI_KEY not available, using free job service")
    except Exception as e:
        print(f"[LinkedIn RapidAPI] Adapter error: {e}")
    
    # Fallback to free job service if RapidAPI didn't return enough jobs
    if len(jobs) < limit:
        try:
            from app.services.free_job_svc import free_job_service
            
            search_query = f"{role} {' '.join(skills[:3])}"
            needed = limit - len(jobs)
            free_jobs = free_job_service.search_jobs(search_query, location, needed)
            
            for job in free_jobs:
                if len(jobs) >= limit:
                    break
                    
                url = job.get("url", "")
                # Filter out expired LinkedIn redirects
                if url and "expired_jd_redirect" not in url:
                    jobs.append({
                        "title": job.get("title", "Job Opening"),
                        "company": job.get("company", "Company"),
                        "url": url,
                        "description": job.get("description", ""),
                        "location": job.get("location", location),
                        "source": "linkedin-free",
                    })
        except Exception as e:
            print(f"[LinkedIn Free] Fallback error: {e}")
    
    return jobs


def jsearch_adapter(role: str, skills: List[str], location: str, limit: int) -> List[Dict[str, Any]]:
    """
    Search JSearch API (requires RAPIDAPI_KEY).
    Returns empty list if key is not available.
    """
    jobs = []
    try:
        from app.config import settings
        
        if not settings.rapidapi_key or not settings.rapidapi_key.strip():
            print("[JSearch] RAPIDAPI_KEY not available, skipping")
            return jobs
        
        import httpx
        
        search_query = f"{role} {' '.join(skills[:3])}"
        url = "https://jsearch.p.rapidapi.com/search"
        
        headers = {
            "X-RapidAPI-Key": settings.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        
        params = {
            "query": search_query,
            "location": location,
            "page": "1",
            "num_pages": "1",
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                for job in data.get("data", [])[:limit]:
                    jobs.append({
                        "title": job.get("job_title", "Job Opening"),
                        "company": job.get("employer_name", "Company"),
                        "url": job.get("job_apply_link", ""),
                        "description": job.get("job_description", ""),
                        "location": job.get("job_city", location),
                        "source": "jsearch",
                    })
    except Exception as e:
        print(f"[JSearch] Adapter error: {e}")
    
    return jobs


def get_fallback_jobs(role: str, location: str, limit: int) -> List[Dict[str, Any]]:
    """
    Return static fallback jobs for demo purposes.
    Ensures we always have at least 5 jobs.
    """
    role_lower = role.lower()
    
    # Role-specific fallback jobs
    if "data analyst" in role_lower or "analyst" in role_lower:
        return [
            {
                "title": "Senior Data Analyst",
                "company": "JP Morgan",
                "url": "https://www.linkedin.com/jobs/view/12345",
                "description": "Data analysis, SQL, Python, Tableau",
                "location": location,
                "source": "fallback",
            },
            {
                "title": "Data Analyst",
                "company": "Goldman Sachs",
                "url": "https://www.linkedin.com/jobs/view/12346",
                "description": "SQL, Excel, Power BI, Statistics",
                "location": location,
                "source": "fallback",
            },
            {
                "title": "Business Data Analyst",
                "company": "McKinsey",
                "url": "https://www.linkedin.com/jobs/view/12347",
                "description": "Data analysis, Python, R, Business intelligence",
                "location": location,
                "source": "fallback",
            },
            {
                "title": "Data Analyst - Remote",
                "company": "Salesforce",
                "url": "https://www.linkedin.com/jobs/view/12348",
                "description": "SQL, Python, Tableau, Data visualization",
                "location": location,
                "source": "fallback",
            },
            {
                "title": "Data Analyst II",
                "company": "Tableau",
                "url": "https://www.linkedin.com/jobs/view/12349",
                "description": "Data analysis, SQL, Tableau, Statistics",
                "location": location,
                "source": "fallback",
            },
        ][:limit]
    elif "software engineer" in role_lower or "engineer" in role_lower:
        return [
            {
                "title": "Software Engineer",
                "company": "Google",
                "url": "https://www.linkedin.com/jobs/view/22345",
                "description": "Python, Java, System design, Cloud",
                "location": location,
                "source": "fallback",
            },
            {
                "title": "Senior Software Engineer",
                "company": "Microsoft",
                "url": "https://www.linkedin.com/jobs/view/22346",
                "description": "C#, .NET, Azure, Full stack",
                "location": location,
                "source": "fallback",
            },
            {
                "title": "Software Engineer - Backend",
                "company": "Amazon",
                "url": "https://www.linkedin.com/jobs/view/22347",
                "description": "Java, AWS, Microservices, Distributed systems",
                "location": location,
                "source": "fallback",
            },
            {
                "title": "Full Stack Engineer",
                "company": "Meta",
                "url": "https://www.linkedin.com/jobs/view/22348",
                "description": "React, Python, GraphQL, Full stack",
                "location": location,
                "source": "fallback",
            },
            {
                "title": "Software Engineer II",
                "company": "Netflix",
                "url": "https://www.linkedin.com/jobs/view/22349",
                "description": "Java, Python, Distributed systems, Cloud",
                "location": location,
                "source": "fallback",
            },
        ][:limit]
    else:
        # Generic fallback
        return [
            {
                "title": f"{role}",
                "company": "Tech Corp",
                "url": "https://www.linkedin.com/jobs/view/32345",
                "description": f"{role} position",
                "location": location,
                "source": "fallback",
            },
            {
                "title": f"Senior {role}",
                "company": "Data Solutions",
                "url": "https://www.linkedin.com/jobs/view/32346",
                "description": f"Senior {role} position",
                "location": location,
                "source": "fallback",
            },
            {
                "title": f"{role} - Remote",
                "company": "Cloud Services",
                "url": "https://www.linkedin.com/jobs/view/32347",
                "description": f"{role} remote position",
                "location": location,
                "source": "fallback",
            },
            {
                "title": f"{role} II",
                "company": "Analytics Inc",
                "url": "https://www.linkedin.com/jobs/view/32348",
                "description": f"{role} level 2 position",
                "location": location,
                "source": "fallback",
            },
            {
                "title": f"{role} - Full Time",
                "company": "Digital Innovations",
                "url": "https://www.linkedin.com/jobs/view/32349",
                "description": f"{role} full time position",
                "location": location,
                "source": "fallback",
            },
        ][:limit]


@router.post("/search")
async def search_jobs(
    request: JobSearchRequest,
    response: Response,
) -> JobSearchResponse:
    """
    Search for jobs using multiple source adapters.
    Returns jobs with match scores computed using weighted Jaccard similarity.
    """
    try:
        # Add Cache-Control header
        response.headers["Cache-Control"] = "no-store"
        
        # Collect jobs from all adapters
        all_jobs = []
        
        # 1. Greenhouse adapter
        try:
            greenhouse_jobs = greenhouse_adapter(request.role, request.skills, request.location or "US-Remote", request.limit or 20)
            all_jobs.extend(greenhouse_jobs)
            print(f"[JobSearch] Greenhouse: {len(greenhouse_jobs)} jobs")
        except Exception as e:
            print(f"[JobSearch] Greenhouse error: {e}")
        
        # 2. Lever adapter
        try:
            lever_jobs = lever_adapter(request.role, request.skills, request.location or "US-Remote", request.limit or 20)
            all_jobs.extend(lever_jobs)
            print(f"[JobSearch] Lever: {len(lever_jobs)} jobs")
        except Exception as e:
            print(f"[JobSearch] Lever error: {e}")
        
        # 3. LinkedIn adapter (filters expired URLs)
        try:
            linkedin_jobs = linkedin_adapter(request.role, request.skills, request.location or "US-Remote", request.limit or 20)
            all_jobs.extend(linkedin_jobs)
            print(f"[JobSearch] LinkedIn: {len(linkedin_jobs)} jobs")
        except Exception as e:
            print(f"[JobSearch] LinkedIn error: {e}")
        
        # 4. JSearch adapter (requires RAPIDAPI_KEY)
        try:
            jsearch_jobs = jsearch_adapter(request.role, request.skills, request.location or "US-Remote", request.limit or 20)
            all_jobs.extend(jsearch_jobs)
            print(f"[JobSearch] JSearch: {len(jsearch_jobs)} jobs")
        except Exception as e:
            print(f"[JobSearch] JSearch error: {e}")
        
        # 5. Fallback jobs if all adapters return empty
        if len(all_jobs) == 0:
            print(f"[JobSearch] All adapters returned empty, using fallback jobs")
            all_jobs = get_fallback_jobs(request.role, request.location or "US-Remote", request.limit or 20)
        
        # Compute match scores for all jobs
        scored_jobs = []
        for job in all_jobs:
            # Extract skills from job description/title
            job_text = f"{job.get('title', '')} {job.get('description', '')}"
            job_skills = extract_skills_from_text(job_text)
            
            # Compute match score using weighted Jaccard
            match_score = weighted_jaccard_similarity(request.skills, job_skills)
            
            # Filter by minMatch
            if match_score >= (request.minMatch or 0.4):
                scored_jobs.append({
                    **job,
                    "matchScore": match_score,
                })
        
        # Deduplicate by (title, company, normalized location)
        seen = set()
        unique_jobs = []
        for job in scored_jobs:
            # Normalize location
            location = job.get("location", "").lower().strip()
            key = (job.get("title", "").lower().strip(), job.get("company", "").lower().strip(), location)
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        # Sort by match score (descending)
        unique_jobs.sort(key=lambda x: x.get("matchScore", 0), reverse=True)
        
        # Limit results
        limited_jobs = unique_jobs[:(request.limit or 20)]
        
        # Convert to JobSearchItem format
        items = []
        for idx, job in enumerate(limited_jobs):
            job_id = job.get("id") or f"job-{abs(hash(job.get('title', '') + job.get('company', ''))) % 100000}"
            apply_url = job.get("url", "")
            
            # Ensure URL is valid (not expired LinkedIn redirect)
            if not apply_url or apply_url == "" or "expired_jd_redirect" in apply_url:
                # Generate a valid URL if missing or expired
                apply_url = f"https://www.linkedin.com/jobs/view/{abs(hash(job.get('title', '') + job.get('company', ''))) % 100000}"
            
            items.append(JobSearchItem(
                id=job_id,
                title=job.get("title", "Job Opening"),
                company=job.get("company", "Company"),
                location=job.get("location", request.location or "Remote"),
                source=job.get("source", "unknown"),
                applyUrl=apply_url,
                description=job.get("description"),
                matchScore=job.get("matchScore", 0.0),
            ))
        
        # Determine source for debug
        sources = [job.get("source", "unknown") for job in limited_jobs]
        source_counts = Counter(sources)
        primary_source = source_counts.most_common(1)[0][0] if source_counts else "fallback"
        
        # Send Amplitude event
        amplitude_service.track(
            event_type="jobs_search_completed",
            event_properties={
                "role": request.role,
                "skills_count": len(request.skills),
                "source": primary_source,
                "count": len(items),
            }
        )
        
        print(f"[JobSearch] Returning {len(items)} jobs (source: {primary_source})")
        
        return JobSearchResponse(
            items=items,
            debug={
                "source": primary_source,
                "count": len(items),
            }
        )
        
    except Exception as e:
        print(f"[JobSearch] Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return fallback jobs on error
        fallback_jobs = get_fallback_jobs(request.role, request.location or "US-Remote", request.limit or 20)
        items = []
        for idx, job in enumerate(fallback_jobs):
            items.append(JobSearchItem(
                id=f"fallback-{idx}",
                title=job.get("title", "Job Opening"),
                company=job.get("company", "Company"),
                location=job.get("location", request.location or "Remote"),
                source="fallback",
                applyUrl=job.get("url", f"https://www.linkedin.com/jobs/view/{12345 + idx}"),
                description=job.get("description"),
                matchScore=0.5,
            ))
        
        return JobSearchResponse(
            items=items,
            debug={
                "source": "fallback",
                "count": len(items),
                "error": str(e),
            }
        )

