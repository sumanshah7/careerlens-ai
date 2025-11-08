"""
Dedalus service for job research and tailoring
Uses JSearch API (RapidAPI) for real job data with fallback heuristics
Supports Dedalus MCP (Model Context Protocol) integration
"""
import os
import re
import httpx
from typing import List, Dict, Any, Optional, Callable
from urllib.parse import urlparse, quote
from app.models.schemas import Job
from app.services.openai_svc import openai_service
from app.config import settings


class DedalusService:
    def __init__(self):
        # Dedalus MCP (Model Context Protocol) - preferred method
        # Check both settings and environment
        self.dedalus_api_key = settings.dedalus_api_key or os.getenv("DEDALUS_API_KEY")
        self.dedalus_mcp_available = bool(self.dedalus_api_key and self.dedalus_api_key.strip())
        
        # Try to import Dedalus MCP service
        self.dedalus_mcp_service = None
        try:
            from app.services.dedalus_mcp import dedalus_mcp_service
            self.dedalus_mcp_service = dedalus_mcp_service
            if self.dedalus_mcp_service.mcp_available:
                print("[Dedalus] MCP service available")
        except ImportError:
            print("[Dedalus] MCP service not available")
        
        # Legacy Dedalus API (if MCP not available)
        self.dedalus_api_url = os.getenv("DEDALUS_API_URL", "https://api.dedalus.ai")
        self.dedalus_available = bool(self.dedalus_api_key and self.dedalus_api_key.strip()) and not self.dedalus_mcp_available
        
        # JSearch API (RapidAPI) for real job data
        self.rapidapi_key = settings.rapidapi_key or os.getenv("RAPIDAPI_KEY")
        self.jsearch_api_url = "https://jsearch.p.rapidapi.com/search"
        self.jsearch_available = bool(self.rapidapi_key and self.rapidapi_key.strip())
        
        # Log availability
        print(f"[Dedalus Service] MCP available: {self.dedalus_mcp_available}, Legacy available: {self.dedalus_available}, JSearch available: {self.jsearch_available}")
        
    def _log_progress(self, callback: Optional[Callable[[str], None]], stage: str, message: str = ""):
        """Log progress for frontend updates"""
        if callback:
            callback(f"{stage}:{message}")
        print(f"[Dedalus] {stage}: {message}")
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using simple heuristics"""
        # Common tech skills
        tech_skills = [
            "React", "TypeScript", "JavaScript", "Python", "Java", "Node.js",
            "AWS", "Docker", "Kubernetes", "GraphQL", "REST", "SQL", "MongoDB",
            "PostgreSQL", "Redis", "Elasticsearch", "CI/CD", "Git", "Agile",
            "Scrum", "System Design", "Microservices", "API", "Frontend",
            "Backend", "Full Stack", "DevOps", "Machine Learning", "AI"
        ]
        
        text_lower = text.lower()
        found_skills = []
        for skill in tech_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _compute_match_score(self, resume_skills: List[str], jd_skills: List[str], resume_gaps: List[str]) -> int:
        """Compute match score based on skill overlap with penalties for gaps"""
        if not jd_skills:
            return 50  # Default score if no skills found
        
        # Count matching skills
        resume_skills_lower = [s.lower() for s in resume_skills]
        jd_skills_lower = [s.lower() for s in jd_skills]
        resume_gaps_lower = [s.lower() for s in resume_gaps]
        
        matches = sum(1 for skill in jd_skills_lower if skill in resume_skills_lower)
        gaps_in_jd = sum(1 for gap in resume_gaps_lower if gap in jd_skills_lower)
        
        # Calculate base score
        base_score = int((matches / len(jd_skills)) * 100) if jd_skills else 0
        
        # Apply penalties for gaps
        gap_penalty = min(gaps_in_jd * 10, 30)  # Max 30 point penalty
        
        # Final score
        final_score = max(0, min(100, base_score - gap_penalty))
        
        return final_score
    
    def _generate_why_and_fix(self, resume_skills: List[str], jd_skills: List[str], resume_gaps: List[str], match_score: int) -> tuple[List[str], List[str]]:
        """Generate why[] and fix[] arrays based on skill analysis"""
        resume_skills_lower = [s.lower() for s in resume_skills]
        jd_skills_lower = [s.lower() for s in jd_skills]
        resume_gaps_lower = [s.lower() for s in resume_gaps]
        
        # Find matching skills for "why"
        matching_skills = [skill for skill in jd_skills if skill.lower() in resume_skills_lower]
        why_items = []
        if matching_skills:
            why_items.append(f"Strong experience with {', '.join(matching_skills[:2])}")
        if match_score >= 70:
            why_items.append("Good overall skill alignment with role requirements")
        if len(matching_skills) >= 3:
            why_items.append("Multiple relevant skills match the job description")
        
        # Find gaps for "fix"
        gaps_in_jd = [skill for skill in jd_skills if skill.lower() in resume_gaps_lower]
        missing_skills = [skill for skill in jd_skills if skill.lower() not in resume_skills_lower and skill.lower() not in resume_gaps_lower]
        
        fix_items = []
        if gaps_in_jd:
            fix_items.append(f"Gain more experience with {', '.join(gaps_in_jd[:2])}")
        if missing_skills:
            fix_items.append(f"Learn {', '.join(missing_skills[:2])}")
        if not gaps_in_jd and not missing_skills and match_score < 80:
            fix_items.append("Improve depth in existing skills")
        
        return why_items[:3], fix_items[:3]  # Limit to 3 items each
    
    def _fetch_jobs_from_jsearch(self, target_role: str, resume_summary: str, count: int = 8) -> List[Dict[str, Any]]:
        """Fetch real jobs from JSearch API (RapidAPI) based on resume"""
        if not self.jsearch_available:
            return []
        
        try:
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            
            # Extract key skills from resume summary for better job matching
            resume_skills = self._extract_skills_from_text(resume_summary)
            skills_query = ", ".join(resume_skills[:5]) if resume_skills else target_role
            
            # Build query with role and skills
            query = f"{target_role} {skills_query}"
            
            params = {
                "query": query,
                "page": "1",
                "num_pages": "1",
                "employment_types": "FULLTIME",
                "job_requirements": "under_3_years_experience,more_than_3_years_experience",
                "remote_jobs_only": "false"
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.jsearch_api_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "data" in data and data["data"]:
                    jobs = []
                    for job in data["data"][:count]:
                        # Get full job description
                        job_description = job.get("job_description", "")
                        if not job_description and job.get("job_highlights"):
                            # Try to build description from highlights
                            highlights = job.get("job_highlights", {})
                            desc_parts = []
                            if highlights.get("Qualifications"):
                                desc_parts.extend(highlights["Qualifications"])
                            if highlights.get("Responsibilities"):
                                desc_parts.extend(highlights["Responsibilities"])
                            job_description = " ".join(desc_parts)
                        
                        # Get job URL - prioritize real job application links
                        job_url = job.get("job_apply_link") or job.get("job_google_link") or ""
                        
                        # Only use Google search as absolute last resort if no real URL exists
                        # Prefer to keep empty rather than Google search to indicate missing data
                        if not job_url or job_url == "" or "example.com" in job_url or "google.com/search" in job_url:
                            # Try to construct a better URL from job_id if available
                            job_id = job.get("job_id", "")
                            if job_id:
                                # Try common job board patterns
                                if "linkedin" in job_id.lower() or "linkedin.com" in (job.get("job_apply_link", "") or ""):
                                    job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
                                elif "indeed" in job_id.lower() or "indeed.com" in (job.get("job_apply_link", "") or ""):
                                    job_url = f"https://www.indeed.com/viewjob?jk={job_id}"
                                else:
                                    # Last resort: use job_google_link if it's a real job page
                                    job_google = job.get("job_google_link", "")
                                    if job_google and "google.com/search" not in job_google:
                                        job_url = job_google
                                    else:
                                        # Keep empty - frontend will handle display
                                        job_url = ""
                        
                        jobs.append({
                            "id": job.get("job_id", ""),
                            "title": job.get("job_title", ""),
                            "company": job.get("employer_name", ""),
                            "url": job_url,
                            "description": job_description or f"Looking for {target_role} with relevant experience."
                        })
                    return jobs
        except Exception as e:
            print(f"[JSearch] API call failed: {e}")
            return []
    
    def _fetch_jds_fallback(self, target_role: str, count: int = 8) -> List[Dict[str, Any]]:
        """Fallback: Return empty list - no mock jobs without real URLs"""
        # Don't return mock jobs with Google search URLs - they'll be filtered out anyway
        # Return empty list to indicate no real jobs found
        return []
    
    def _call_dedalus_api(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Call Dedalus API with multiple endpoint format attempts
        
        Note: If you get 404 errors, check the actual Dedalus API documentation
        for the correct endpoint format. This method tries common patterns.
        """
        if not self.dedalus_api_key:
            return None
        
        try:
            # Try different endpoint formats based on common API patterns
            api_urls = [
                f"{self.dedalus_api_url}/api/v1/{endpoint}",
                f"{self.dedalus_api_url}/v1/{endpoint}",
                f"{self.dedalus_api_url}/{endpoint}",
                f"https://api.dedaluslabs.net/v1/{endpoint}",
                f"https://api.dedalus.ai/v1/{endpoint}",
            ]
            
            headers = {
                "Authorization": f"Bearer {self.dedalus_api_key}",
                "Content-Type": "application/json"
            }
            
            for api_url in api_urls:
                try:
                    with httpx.Client(timeout=10.0) as client:
                        response = client.post(api_url, json=payload, headers=headers)
                        if response.status_code == 200:
                            return response.json()
                        elif response.status_code == 404:
                            # Try next URL format
                            continue
                        else:
                            response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        continue
                    raise
                except Exception:
                    continue
            
            # If all URLs fail, return None (will fall back to other methods)
            print(f"[Dedalus] All API endpoint attempts failed (404). Check Dedalus API documentation for correct endpoint format.")
            print(f"[Dedalus] Tried endpoints: {api_urls}")
            return None
            
        except Exception as e:
            print(f"[Dedalus] API call failed: {e}")
            return None
    
    def run_job_research(
        self,
        target_role: str,
        resume_summary: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Job]:
        """
        Research jobs using Dedalus or fallback heuristics.
        
        Steps:
        1. Fetch/crawl 5-10 JDs
        2. Summarize and extract skills
        3. Compute match% (skill overlap - penalties for gaps)
        4. Generate why[] and fix[]
        
        Args:
            target_role: Target role to search for
            resume_summary: Summary of resume skills and experience
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of Job objects with source annotation
        """
        self._log_progress(progress_callback, "Fetching", f"Searching for {target_role} positions")
        
        # Try Dedalus MCP first (preferred method)
        if self.dedalus_mcp_service and self.dedalus_mcp_service.mcp_available:
            try:
                self._log_progress(progress_callback, "Initializing", "Using Dedalus MCP for job research")
                jobs = self.dedalus_mcp_service.run_job_research_mcp(
                    target_role=target_role,
                    resume_summary=resume_summary,
                    progress_callback=progress_callback
                )
                if jobs:
                    self._log_progress(progress_callback, "Ranking", f"Found {len(jobs)} jobs from Dedalus MCP")
                    return jobs
            except Exception as e:
                print(f"[Dedalus] MCP failed, falling back: {e}")
        
        # Try JSearch API (real jobs)
        if self.jsearch_available:
            try:
                self._log_progress(progress_callback, "Fetching", "Fetching real jobs from JSearch API based on resume")
                jds = self._fetch_jobs_from_jsearch(target_role, resume_summary, count=8)
                if jds:
                    self._log_progress(progress_callback, "Parsing", f"Found {len(jds)} real jobs")
                    # Process real jobs
                    jobs = []
                    resume_skills = self._extract_skills_from_text(resume_summary)
                    resume_gaps = []  # Extract gaps from resume summary if available
                    
                    for jd in jds:
                        jd_skills = self._extract_skills_from_text(jd.get("description", ""))
                        match_score = self._compute_match_score(resume_skills, jd_skills, resume_gaps)
                        why, fix = self._generate_why_and_fix(resume_skills, jd_skills, resume_gaps, match_score)
                        
                        # Get job URL - prioritize real job application links
                        job_url = jd.get("url", "") or jd.get("job_apply_link") or jd.get("job_google_link") or ""
                        
                        # Only use real job URLs, not Google search
                        if not job_url or job_url == "" or "example.com" in job_url or "google.com/search" in job_url:
                            # Keep empty - frontend will handle display appropriately
                            job_url = ""
                        
                        jobs.append(Job(
                            id=jd.get("id", ""),
                            title=jd.get("title", ""),
                            company=jd.get("company", ""),
                            match=match_score,
                            why=why if why else ["Relevant experience matches role requirements"],
                            fix=fix if fix else ["Continue building relevant skills"],
                            jdUrl=job_url,
                            source="jsearch"
                        ))
                    
                    if jobs:
                        self._log_progress(progress_callback, "Ranking", f"Ranked {len(jobs)} real jobs")
                        return jobs
            except Exception as e:
                print(f"[JSearch] Failed to fetch jobs, using fallback: {e}")
        
        # Try Dedalus first
        if self.dedalus_available:
            try:
                dedalus_result = self._call_dedalus_api("jobs/research", {
                    "target_role": target_role,
                    "resume_summary": resume_summary,
                    "count": 8
                })
                
                if dedalus_result and "jobs" in dedalus_result:
                    self._log_progress(progress_callback, "Parsing", "Processing Dedalus results")
                    jobs = []
                    for job_data in dedalus_result["jobs"]:
                        jobs.append(Job(
                            id=job_data.get("id", ""),
                            title=job_data.get("title", ""),
                            company=job_data.get("company", ""),
                            match=job_data.get("match", 0),
                            why=job_data.get("why", []),
                            fix=job_data.get("fix", []),
                            jdUrl=job_data.get("url", ""),
                            source="dedalus"
                        ))
                    self._log_progress(progress_callback, "Ranking", f"Found {len(jobs)} jobs from Dedalus")
                    return jobs
            except Exception as e:
                print(f"[Dedalus] API call failed, using fallback: {e}")
        
        # Fallback: Use internal heuristics
        self._log_progress(progress_callback, "Fetching", "Using fallback job search")
        
        # Step 1: Fetch JDs
        jds = self._fetch_jds_fallback(target_role, count=8)
        self._log_progress(progress_callback, "Parsing", f"Processing {len(jds)} job descriptions")
        
        # Step 2: Extract skills from resume summary
        resume_skills = self._extract_skills_from_text(resume_summary)
        resume_gaps = ["AWS", "System Design", "GraphQL"]  # Example gaps - in production, extract from analysis
        
        # Step 3: Process each JD
        jobs = []
        for jd in jds:
            # Extract skills from JD
            jd_skills = self._extract_skills_from_text(jd["description"])
            
            # Compute match score
            match_score = self._compute_match_score(resume_skills, jd_skills, resume_gaps)
            
            # Generate why and fix
            why, fix = self._generate_why_and_fix(resume_skills, jd_skills, resume_gaps, match_score)
            
            jobs.append(Job(
                id=jd["id"],
                title=jd["title"],
                company=jd["company"],
                match=match_score,
                why=why if why else ["Relevant experience matches role requirements"],
                fix=fix if fix else ["Continue building relevant skills"],
                jdUrl=jd["url"],
                source="fallback"
            ))
        
        # Step 4: Sort by match score
        jobs.sort(key=lambda x: x.match, reverse=True)
        
        self._log_progress(progress_callback, "Ranking", f"Ranked {len(jobs)} jobs (match scores: {[j.match for j in jobs[:3]]})")
        
        return jobs
    
    def run_tailor_suite(self, resume: str, jd: str) -> Dict[str, Any]:
        """
        Run tailoring suite using Dedalus MCP, Dedalus API, or OpenAI.
        
        Priority:
        1. Dedalus MCP (if available)
        2. Dedalus API (if available)
        3. OpenAI service (fallback)
        
        Args:
            resume: Resume text
            jd: Job description text
            
        Returns:
            TailorResponse dict
        """
        # Try Dedalus MCP first (preferred method)
        if self.dedalus_mcp_service and self.dedalus_mcp_service.mcp_available:
            try:
                tailor_response = self.dedalus_mcp_service.run_tailor_suite_mcp(resume, jd)
                return tailor_response.model_dump()
            except Exception as e:
                print(f"[Dedalus] MCP tailoring failed, falling back: {e}")
        
        # Try Dedalus API if available
        if self.dedalus_available:
            try:
                dedalus_result = self._call_dedalus_api("tailor/suite", {
                    "resume": resume,
                    "jd": jd
                })
                
                if dedalus_result and "bullets" in dedalus_result:
                    return {
                        "bullets": dedalus_result.get("bullets", []),
                        "pitch": dedalus_result.get("pitch", ""),
                        "coverLetter": dedalus_result.get("coverLetter", "")
                    }
            except Exception as e:
                print(f"[Dedalus] Tailor suite failed, using OpenAI fallback: {e}")
        
        # Fallback to OpenAI service
        return openai_service.tailor_for_job(resume, jd, style="STAR")


# Global instance
dedalus_service = DedalusService()

