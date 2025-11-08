"""
Dedalus MCP (Model Context Protocol) integration
Provides MCP-based job research and tailoring capabilities
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, Callable
from app.models.schemas import Job, TailorResponse
from app.config import settings


class DedalusMCPService:
    """
    Dedalus MCP service for job research and tailoring using Model Context Protocol
    
    This service integrates with Dedalus MCP to provide:
    - Real-time job research using MCP tools
    - Multi-tool orchestration for job matching
    - Resume tailoring with MCP-powered analysis
    """
    
    def __init__(self):
        # Dedalus MCP configuration - check both settings and environment
        self.dedalus_api_key = settings.dedalus_api_key or os.getenv("DEDALUS_API_KEY")
        self.dedalus_mcp_url = os.getenv("DEDALUS_MCP_URL", "https://api.dedaluslabs.net/mcp")
        # Check if key exists and is not empty
        self.mcp_available = bool(self.dedalus_api_key and self.dedalus_api_key.strip())
        
        # Try to import Dedalus Labs SDK if available
        self.dedalus_client = None
        self.dedalus_runner = None
        try:
            from dedalus_labs import AsyncDedalus, DedalusRunner
            if self.dedalus_api_key:
                # Initialize with API key if available
                self.dedalus_client = AsyncDedalus(api_key=self.dedalus_api_key)
                self.dedalus_runner = DedalusRunner(self.dedalus_client)
                print("[Dedalus MCP] SDK initialized successfully")
                self.mcp_available = True
            else:
                print("[Dedalus MCP] SDK available but DEDALUS_API_KEY not set")
                self.mcp_available = False
        except ImportError:
            print("[Dedalus MCP] SDK not installed. Install with: pip install dedalus-labs")
            self.mcp_available = False
        except Exception as e:
            print(f"[Dedalus MCP] SDK initialization failed: {e}")
            self.mcp_available = False
    
    def _log_progress(self, callback: Optional[Callable[[str], None]], stage: str, message: str = ""):
        """Log progress for frontend updates"""
        if callback:
            callback(f"{stage}:{message}")
        print(f"[Dedalus MCP] {stage}: {message}")
    
    async def _run_dedalus_query(self, query: str, model: str = "openai/gpt-4o-mini", tools: Optional[List] = None):
        """
        Run a query using Dedalus Labs SDK
        
        Args:
            query: Query string
            model: Model to use (default: openai/gpt-4o-mini)
            tools: Optional list of tools/functions
            
        Returns:
            Response from Dedalus
        """
        if not self.dedalus_runner:
            raise ValueError("Dedalus SDK not available. Install with: pip install dedalus-labs and set DEDALUS_API_KEY")
        
        try:
            response = await self.dedalus_runner.run(
                input=query,
                model=model,
                tools=tools or []
            )
            return response
        except Exception as e:
            print(f"[Dedalus MCP] Query failed: {e}")
            raise
    
    async def run_job_research_mcp_async(
        self,
        target_role: str,
        resume_summary: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Job]:
        """
        Research jobs using Dedalus Labs SDK (async)
        
        Args:
            target_role: Target role to search for
            resume_summary: Summary of resume skills and experience
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of Job objects with match scores
        """
        if not self.mcp_available:
            raise ValueError("Dedalus MCP not available. Set DEDALUS_API_KEY in .env")
        
        self._log_progress(progress_callback, "Initializing", "Setting up Dedalus MCP")
        
        try:
            self._log_progress(progress_callback, "Searching", f"Searching for {target_role} positions using Dedalus")
            
            # Build query for job search
            query = f"Find {target_role} jobs matching these skills and experience: {resume_summary}. Return job listings with title, company, URL, and match score."
            
            # Run query using Dedalus
            response = await self._run_dedalus_query(
                query=query,
                model="openai/gpt-4o-mini"
            )
            
            self._log_progress(progress_callback, "Processing", "Processing Dedalus results")
            
            # Parse response and convert to Job objects
            jobs = self._parse_mcp_jobs(response, resume_summary)
            
            self._log_progress(progress_callback, "Ranking", f"Ranked {len(jobs)} jobs from Dedalus")
            
            return jobs
            
        except Exception as e:
            print(f"[Dedalus MCP] Job research failed: {e}")
            raise Exception(f"Dedalus MCP job research failed: {e}")
    
    def run_job_research_mcp(
        self,
        target_role: str,
        resume_summary: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Job]:
        """
        Research jobs using Dedalus MCP tools (sync wrapper)
        """
        try:
            return asyncio.run(self.run_job_research_mcp_async(target_role, resume_summary, progress_callback))
        except Exception as e:
            print(f"[Dedalus MCP] Sync wrapper failed: {e}")
            raise
    
    def run_tailor_suite_mcp(
        self,
        resume: str,
        jd: str
    ) -> TailorResponse:
        """
        Tailor resume using Dedalus MCP tools
        
        Uses MCP tools like:
        - resume-tailor-v1: Resume tailoring tool
        - star-formatter-v1: STAR format bullets
        - cover-letter-v1: Cover letter generation
        
        Args:
            resume: Resume text
            jd: Job description
            
        Returns:
            TailorResponse with bullets, pitch, and cover letter
        """
        if not self.mcp_available:
            raise ValueError("Dedalus MCP not available. Set DEDALUS_API_KEY in .env")
        
        try:
            # Define MCP tools for resume tailoring
            tools = [
                "dedalus-user-1/resume-tailor-v1",  # Resume tailoring
                "dedalus-user-1/star-formatter-v1",  # STAR format (if available)
                "dedalus-user-1/cover-letter-v1"  # Cover letter (if available)
            ]
            
            # Create MCP agent
            agent = self._create_mcp_agent(
                tools=tools,
                instructions="Tailor resumes and generate cover letters for job applications"
            )
            
            # Use agent to tailor resume
            query = f"Tailor this resume for this job description:\n\nResume:\n{resume}\n\nJob Description:\n{jd}"
            response = agent.run(query)
            
            # Parse response and convert to TailorResponse
            tailor_response = self._parse_mcp_tailor(response)
            
            return tailor_response
            
        except Exception as e:
            print(f"[Dedalus MCP] Resume tailoring failed: {e}")
            raise Exception(f"Dedalus MCP resume tailoring failed: {e}")
    
    def _parse_mcp_jobs(self, mcp_response: Any, resume_summary: str) -> List[Job]:
        """
        Parse MCP response and convert to Job objects
        
        Args:
            mcp_response: Response from Dedalus Labs SDK
            resume_summary: Resume summary for skill matching
            
        Returns:
            List of Job objects
        """
        jobs = []
        
        # Extract jobs from Dedalus response
        # Dedalus Labs returns response with final_output attribute
        response_text = ""
        if hasattr(mcp_response, 'final_output'):
            response_text = str(mcp_response.final_output)
        elif isinstance(mcp_response, dict):
            response_text = str(mcp_response.get("final_output", mcp_response.get("output", "")))
        else:
            response_text = str(mcp_response)
        
        # Try to extract jobs from text response
        job_data = self._extract_jobs_from_text(response_text, resume_summary)
        
        # Convert to Job objects
        for idx, job in enumerate(job_data[:8]):  # Limit to 8 jobs
            if isinstance(job, dict):
                # Ensure URL is valid
                job_url = job.get("url", job.get("apply_link", job.get("jdUrl", "")))
                if not job_url or job_url == "" or "google.com/search" in job_url:
                    continue  # Skip jobs without valid URLs
                
                jobs.append(Job(
                    id=job.get("id", f"dedalus-{idx}"),
                    title=job.get("title", ""),
                    company=job.get("company", job.get("employer", "")),
                    match=job.get("match_score", job.get("match", 75)),
                    why=job.get("why", [f"Relevant experience in {resume_summary[:50]}"]),
                    fix=job.get("fix", ["Continue building relevant skills"]),
                    jdUrl=job_url,
                    source="dedalus-mcp"
                ))
        
        return jobs
    
    def _parse_mcp_tailor(self, mcp_response: Any) -> TailorResponse:
        """
        Parse MCP response and convert to TailorResponse
        
        Args:
            mcp_response: Response from Dedalus MCP agent
            
        Returns:
            TailorResponse object
        """
        # Extract tailoring data from MCP response
        if isinstance(mcp_response, dict):
            bullets = mcp_response.get("bullets", [])
            pitch = mcp_response.get("pitch", "")
            cover_letter = mcp_response.get("cover_letter", "")
        else:
            # Try to extract from text response
            text = str(mcp_response)
            bullets = self._extract_bullets_from_text(text)
            pitch = self._extract_pitch_from_text(text)
            cover_letter = self._extract_cover_letter_from_text(text)
        
        return TailorResponse(
            bullets=bullets if bullets else ["Generated resume bullet point"],
            pitch=pitch if pitch else "Generated elevator pitch",
            coverLetter=cover_letter if cover_letter else "Generated cover letter"
        )
    
    def _extract_jobs_from_text(self, text: str, resume_summary: str) -> List[Dict[str, Any]]:
        """Extract job data from text response"""
        import re
        import json
        
        jobs = []
        
        # Try to parse JSON if present
        try:
            # Look for JSON blocks in the response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, dict) and "jobs" in data:
                    return data["jobs"]
                elif isinstance(data, list):
                    return data
        except:
            pass
        
        # Try to extract structured data from text
        # Look for job listings in various formats
        lines = text.split('\n')
        current_job = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_job and current_job.get("title"):
                    jobs.append(current_job)
                    current_job = {}
                continue
            
            # Try to extract job information
            if "title:" in line.lower() or "position:" in line.lower():
                current_job["title"] = re.sub(r'^(title|position):\s*', '', line, flags=re.IGNORECASE).strip()
            elif "company:" in line.lower() or "employer:" in line.lower():
                current_job["company"] = re.sub(r'^(company|employer):\s*', '', line, flags=re.IGNORECASE).strip()
            elif "url:" in line.lower() or "link:" in line.lower() or "http" in line.lower():
                url_match = re.search(r'https?://[^\s]+', line)
                if url_match:
                    current_job["url"] = url_match.group()
            elif "match:" in line.lower() or "score:" in line.lower():
                score_match = re.search(r'\d+', line)
                if score_match:
                    current_job["match"] = int(score_match.group())
        
        # Add final job if exists
        if current_job and current_job.get("title"):
            jobs.append(current_job)
        
        # If no jobs found, return empty list (don't create fake jobs)
        return jobs
    
    def _extract_bullets_from_text(self, text: str) -> List[str]:
        """Extract STAR bullets from text"""
        bullets = []
        # Simple extraction - in production, use more sophisticated parsing
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('*'):
                bullets.append(line.strip().lstrip('-* '))
        return bullets[:4]  # Limit to 4 bullets
    
    def _extract_pitch_from_text(self, text: str) -> str:
        """Extract elevator pitch from text"""
        # Simple extraction - in production, use more sophisticated parsing
        if "pitch:" in text.lower():
            parts = text.split("pitch:")
            if len(parts) > 1:
                return parts[1].strip()[:200]  # Limit to 200 chars
        return "Generated elevator pitch"
    
    def _extract_cover_letter_from_text(self, text: str) -> str:
        """Extract cover letter from text"""
        # Simple extraction - in production, use more sophisticated parsing
        if "cover letter:" in text.lower():
            parts = text.split("cover letter:")
            if len(parts) > 1:
                return parts[1].strip()[:500]  # Limit to 500 chars
        return "Generated cover letter"


# Global instance
dedalus_mcp_service = DedalusMCPService()

