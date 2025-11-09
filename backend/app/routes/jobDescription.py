"""
Endpoint to fetch full job descriptions from URLs
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class FetchDescriptionRequest(BaseModel):
    url: str


class FetchDescriptionResponse(BaseModel):
    description: str
    success: bool
    source: str  # 'scraped', 'api', 'fallback'


@router.post("/fetch-description")
async def fetch_job_description(request: FetchDescriptionRequest) -> FetchDescriptionResponse:
    """
    Fetch full job description from a job URL.
    Attempts to scrape the page or use API if available.
    """
    url = request.url.strip()
    
    if not url or not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid URL provided")
    
    # Skip expired LinkedIn redirects
    if "expired_jd_redirect" in url:
        raise HTTPException(status_code=400, detail="Job posting has expired")
    
    try:
        # Try to fetch the page
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try different selectors based on common job board patterns
            description = ""
            
            # LinkedIn job description
            if "linkedin.com" in url:
                # Try LinkedIn-specific selectors
                selectors = [
                    'div[class*="description__text"]',
                    'div[class*="show-more-less-html__markup"]',
                    'div[class*="jobs-description"]',
                    'section[class*="description"]',
                    'div[class*="job-details"]',
                ]
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        description = element.get_text(separator='\n', strip=True)
                        if len(description) > 200:  # Minimum length to be valid
                            break
            
            # Greenhouse job board
            elif "greenhouse.io" in url or "boards.greenhouse.io" in url:
                selectors = [
                    'div[id*="content"]',
                    'div[class*="description"]',
                    'section[class*="content"]',
                ]
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        description = element.get_text(separator='\n', strip=True)
                        if len(description) > 200:
                            break
            
            # Lever job board
            elif "lever.co" in url or "jobs.lever.co" in url:
                selectors = [
                    'div[class*="content"]',
                    'div[class*="description"]',
                    'section[class*="content"]',
                ]
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        description = element.get_text(separator='\n', strip=True)
                        if len(description) > 200:
                            break
            
            # Generic fallback: look for common job description patterns
            if not description or len(description) < 200:
                # Try to find main content area
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|description|job', re.I))
                if main_content:
                    description = main_content.get_text(separator='\n', strip=True)
            
            # Final fallback: extract all text and clean it
            if not description or len(description) < 200:
                # Get body text, excluding navigation and footer
                body = soup.find('body')
                if body:
                    # Remove common non-content elements
                    for tag in body.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                        tag.decompose()
                    description = body.get_text(separator='\n', strip=True)
            
            # Clean up the description
            if description:
                # Remove excessive whitespace
                description = re.sub(r'\n{3,}', '\n\n', description)
                description = re.sub(r' {2,}', ' ', description)
                description = description.strip()
            
            # If we got a reasonable description, return it
            if description and len(description) >= 200:
                return FetchDescriptionResponse(
                    description=description,
                    success=True,
                    source="scraped"
                )
            else:
                # Return a fallback message
                return FetchDescriptionResponse(
                    description=f"Job description could not be fully extracted from {url}. Please visit the job posting directly to view full details.",
                    success=False,
                    source="fallback"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timeout while fetching job description")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch job description: {e.response.status_code}")
    except Exception as e:
        print(f"[JobDescription] Error fetching description: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching job description: {str(e)}")

