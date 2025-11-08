# CareerLens AI - Detailed Code Explanation

This document explains each part of the codebase and what it does.

---

## Table of Contents
1. [Backend Structure](#backend-structure)
2. [Frontend Structure](#frontend-structure)
3. [Key Components Explained](#key-components-explained)
4. [Data Flow](#data-flow)

---

## Backend Structure

### 1. Main Application Entry Point

**File**: `backend/app/main.py`

```python
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from app.routes import analyze, jobs, tailor, coach, predict, upload, roleMatch, generatePlan, jobSearch, linkedinJobs
```

**What it does**:
- **FastAPI**: Creates the main web application instance
- **CORS Middleware**: Allows frontend (running on different port) to make API requests
- **Mangum**: Wraps FastAPI app for AWS Lambda deployment (serverless)
- **Route Imports**: Imports all API endpoint routers

**CORS Configuration**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:5174",   # Alternative port
        "http://localhost:5175",   # Another alternative
        "http://localhost:3000",   # React default port
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],   # Allow all headers
)
```
**Purpose**: Enables cross-origin requests from frontend to backend

**Global Exception Handler**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure CORS headers are always sent"""
```
**What it does**:
- Catches ALL unhandled exceptions
- Ensures CORS headers are ALWAYS sent (even on errors)
- Returns JSON error response instead of crashing
- Special handling for `/roleMatchAndOpenings` endpoint (returns fallback jobs)

**Health Check Endpoint**:
```python
@app.get("/health")
async def health():
    """Health check endpoint with provider status"""
```
**What it does**:
- Checks if backend is running
- Verifies API keys are set (Anthropic, OpenAI, Dedalus)
- Returns status of all providers
- Used by frontend to show banners for missing keys

---

### 2. Configuration Management

**File**: `backend/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    amplitude_api_key: str | None = None
    rapidapi_key: str | None = None
    dedalus_api_key: str | None = None
    # ... more settings
    
    class Config:
        env_file = ".env"  # Load from .env file
        env_file_encoding = "utf-8"
        case_sensitive = False  # Case-insensitive env vars

settings = Settings()  # Global settings instance
```

**What it does**:
- **Pydantic Settings**: Validates and loads environment variables
- **`.env` File**: Reads API keys from `backend/.env` file
- **Type Safety**: Ensures correct types (str, int, bool, etc.)
- **Global Access**: `settings.anthropic_api_key` can be used anywhere

**Why Pydantic Settings?**:
- Automatic validation (e.g., ensures API key is a string)
- Type hints for IDE autocomplete
- Environment variable loading from `.env` file
- Default values if env var not set

---

### 3. Data Models (Schemas)

**File**: `backend/app/models/schemas.py`

**Purpose**: Defines the structure of all API requests and responses

**Example - AnalyzeRequest**:
```python
class AnalyzeRequest(BaseModel):
    resume_text: str  # Required field
    target_role: str | None = None  # Optional field
    preferred_roles: list[str] | None = None
    top_k_domains: int = 5
```

**What it does**:
- **Pydantic BaseModel**: Validates incoming JSON data
- **Type Checking**: Ensures `resume_text` is a string, `top_k_domains` is an integer
- **Required vs Optional**: `resume_text` is required, `target_role` is optional
- **Auto Validation**: FastAPI automatically validates request body against this schema

**Example - AnalyzeResponse**:
```python
class AnalyzeResponse(BaseModel):
    domains: List[DomainScore]
    skills: SkillsBreakdown
    strengths: List[str]
    areas_for_growth: List[str]
    recommended_roles: List[str]
    keywords_detected: List[str]
    debug: dict
    score: int | None = None
```

**What it does**:
- Defines the structure of the response sent to frontend
- Ensures all required fields are present
- Type-safe: Frontend knows exactly what to expect

**Why Schemas?**:
- **API Contract**: Clear contract between frontend and backend
- **Validation**: Automatic validation of request/response data
- **Documentation**: FastAPI auto-generates API docs from schemas
- **Type Safety**: Prevents bugs from wrong data types

---

### 4. Resume Analysis Endpoint

**File**: `backend/app/routes/analyze.py`

**Route Definition**:
```python
router = APIRouter(prefix="/api/analyze-resume", tags=["analyze"])

@router.post("")
async def analyze_resume(
    request: AnalyzeRequest,
    response: Response,
    hash: str | None = Query(None)
):
```

**What it does**:
- **APIRouter**: Groups related endpoints together
- **`prefix="/api/analyze-resume"`**: All routes in this file start with this prefix
- **`@router.post("")`**: Handles POST requests to `/api/analyze-resume`
- **`async def`**: Asynchronous function (can handle multiple requests concurrently)

**Step-by-Step Flow**:

**Step 1: Extract Target Role**
```python
target_role = None
if request.target_role:  # Primary field (snake_case)
    target_role = request.target_role
elif request.targetRole:  # Legacy support (camelCase)
    target_role = request.targetRole
```
**What it does**: Extracts user's selected target role from request (supports multiple field names for backward compatibility)

**Step 2: Compute Resume Hash**
```python
resume_hash = hashlib.sha256(resume_text.encode('utf-8')).hexdigest()
debug_hash = resume_hash[:8]
```
**What it does**:
- Creates unique identifier for resume (SHA256 hash)
- Uses first 8 characters for logging/tracking
- Same resume → same hash (deterministic)

**Step 3: Try Anthropic Claude (Primary LLM)**
```python
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    try:
        result_dict = anthropic_service.analyze_resume(
            text=resume_text,
            target_role=target_role
        )
        provider = "anthropic"
    except Exception as e:
        print(f"[Analyze] Anthropic failed: {e}")
```
**What it does**:
- Checks if Anthropic API key is set
- Calls Anthropic Claude API to analyze resume
- If successful, uses Anthropic result
- If fails, continues to fallback

**Step 4: Try OpenAI GPT (Fallback LLM)**
```python
if not result_dict:
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            result_dict = openai_service.analyze_resume(
                text=resume_text,
                target_role=target_role
            )
            provider = "openai"
        except Exception as e:
            print(f"[Analyze] OpenAI failed: {e}")
```
**What it does**:
- Only runs if Anthropic failed
- Tries OpenAI GPT as fallback
- Same analysis capabilities as Anthropic

**Step 5: Keyword-Based Fallback**
```python
if not result_dict:
    result_dict = keyword_based_analysis(resume_text, request.top_k_domains, target_role)
    provider = "heuristic"
```
**What it does**:
- Only runs if both LLMs failed
- Uses keyword matching to analyze resume
- No API keys required (works offline)

**Step 6: Post-Process (Prioritize Target Role)**
```python
if target_role and result_dict.get("domains"):
    target_role_lower = target_role.lower()
    # Map target_role to domain name
    if "ai engineer" in target_role_lower:
        target_domain = "ML/AI"
    elif "data analyst" in target_role_lower:
        target_domain = "Data Analyst"
    # ... more mappings
    
    # Force target domain to be top domain
    if target_domain:
        domains = result_dict["domains"]
        target_domain_index = next((i for i, d in enumerate(domains) if d["name"] == target_domain), None)
        
        if target_domain_index is not None:
            # Move target domain to top
            target_domain_obj = domains.pop(target_domain_index)
            target_domain_obj["score"] = 0.9  # Force high score
            domains.insert(0, target_domain_obj)
```
**What it does**:
- If user selected a target role, forces it to be the PRIMARY domain
- Moves target domain to top of list
- Sets score to 0.9 (90%) to make it clearly primary
- Updates recommended roles to match target role

**Step 7: Send Amplitude Event**
```python
amplitude_service.track(
    event_type="analysis_completed_server",
    event_properties={
        "hash": debug_hash,
        "provider": provider,
        "strengths_count": strengths_count,
        "domains_count": domains_count,
    }
)
```
**What it does**:
- Tracks that analysis completed
- Sends only hash, counts, provider (NO raw resume text)
- Privacy-compliant tracking

**Step 8: Return Response**
```python
return AnalyzeResponse(**result_dict)
```
**What it does**:
- Converts dictionary to Pydantic model
- Validates response structure
- Returns JSON to frontend

---

### 5. Anthropic Service

**File**: `backend/app/services/anthropic_svc.py`

**Class Definition**:
```python
class AnthropicService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-haiku-20240307"
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
```

**What it does**:
- Initializes Anthropic API client
- Sets model to Claude 3 Haiku (fast, cost-effective)
- Only creates client if API key is set

**Analyze Resume Method**:
```python
def analyze_resume(self, text: str, target_role: Optional[str] = None) -> Dict[str, Any]:
    prompt = self._build_analysis_prompt(text, target_role)
    
    message = self.client.messages.create(
        model=self.model,
        max_tokens=3000,
        temperature=0.1,  # Low temperature = more deterministic
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text.strip()
    result_dict = json.loads(response_text)
    return result_dict
```

**What it does**:
- **Builds Prompt**: Creates detailed prompt with instructions
- **Calls API**: Sends prompt to Anthropic Claude API
- **Parses Response**: Extracts JSON from response
- **Returns Dict**: Returns analysis as dictionary

**Prompt Building**:
```python
def _build_analysis_prompt(self, resume_text: str, target_role: Optional[str] = None) -> str:
    base_prompt = f"""You are an expert resume analyzer for ANY profession...
    
    Resume Text:
    {resume_text}
    """
    
    if target_role:
        base_prompt += f"\nTARGET ROLE (USER SELECTED): {target_role}\n"
        base_prompt += f"CRITICAL: The user has selected '{target_role}' as their target role..."
    
    return base_prompt
```

**What it does**:
- Creates detailed instructions for LLM
- Includes resume text
- If target_role provided, adds special instructions to prioritize it
- Returns complete prompt string

---

### 6. Free Job Service

**File**: `backend/app/services/free_job_svc.py`

**Purpose**: Provides job search without requiring API keys (uses free RSS feeds)

**Search Jobs Method**:
```python
def search_jobs(self, query: str, location: str = "US", num_results: int = 20) -> List[Dict[str, Any]]:
    jobs = []
    
    # Try Jobicy RSS feed
    try:
        jobicy_jobs = self._search_jobicy_rss(query, min(10, num_results))
        if jobicy_jobs:
            jobs.extend(jobicy_jobs)
    except Exception as e:
        print(f"[FreeJobService] Jobicy RSS failed: {e}")
    
    # Try RemoteOK RSS feed
    if len(jobs) < num_results:
        try:
            remoteok_jobs = self._search_remoteok_rss(query, min(10, num_results - len(jobs)))
            if remoteok_jobs:
                jobs.extend(remoteok_jobs)
        except Exception as e:
            print(f"[FreeJobService] RemoteOK RSS failed: {e}")
    
    # ... more RSS feeds
    
    # If still not enough, generate fallback jobs
    if len(jobs) < num_results:
        jobs.extend(self._generate_generic_jobs(query, location, num_results - len(jobs)))
    
    return jobs
```

**What it does**:
- **Tries Multiple Sources**: Attempts to fetch from multiple RSS feeds
- **Fallback**: If RSS feeds fail, generates realistic fallback jobs
- **Always Returns Jobs**: Never returns empty list (ensures "no jobs found" never happens)

**RSS Parsing**:
```python
def _search_jobicy_rss(self, query: str, limit: int) -> List[Dict[str, Any]]:
    url = f"https://jobicy.com/api/v2/remote-jobs?keywords={quote(query)}"
    response = httpx.get(url, timeout=10.0)
    data = response.json()
    
    jobs = []
    for item in data.get("jobs", [])[:limit]:
        jobs.append({
            "title": item.get("title", ""),
            "company": item.get("companyName", ""),
            "location": item.get("location", "Remote"),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
        })
    return jobs
```

**What it does**:
- **Fetches RSS Feed**: Makes HTTP request to RSS endpoint
- **Parses JSON**: Extracts job data from JSON response
- **Maps to Schema**: Converts to standard job format
- **Returns List**: Returns list of job dictionaries

---

## Frontend Structure

### 1. Main App Component

**File**: `frontend/src/App.tsx`

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/coaching-plan" element={<CoachingPlan />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**What it does**:
- **BrowserRouter**: Enables client-side routing (no page reloads)
- **Routes**: Defines all application routes
- **Route**: Maps URL path to React component
- **Navigation**: Users can navigate between pages without full page reload

**Example Flow**:
- User visits `/` → Shows `<Home />` component
- User clicks "View Analysis" → Navigates to `/analysis` → Shows `<Analysis />` component

---

### 2. State Management (Zustand)

**File**: `frontend/src/store/useAppStore.ts`

**Store Definition**:
```typescript
interface AppState {
  resumeText: string | null;
  analysis: AnalyzeResponse | null;
  jobs: Job[] | null;
  coach: CoachPlan | null;
  resumes: Resume[];
  currentRole: string | null;
  
  // Actions
  setResumeText: (text: string) => void;
  setAnalysis: (analysis: AnalyzeResponse) => void;
  setJobs: (jobs: Job[]) => void;
  // ... more actions
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      resumeText: null,
      analysis: null,
      // ... initial state
      
      setAnalysis: (analysis) => set({ analysis }),
      // ... actions
    }),
    {
      name: 'careerlens-storage',  // localStorage key
    }
  )
);
```

**What it does**:
- **Zustand**: Lightweight state management library
- **Persist**: Saves state to localStorage (survives page refresh)
- **Global State**: All components can access and update state
- **Actions**: Functions to update state (e.g., `setAnalysis`)

**Example Usage**:
```typescript
// In any component
const { analysis, setAnalysis } = useAppStore();

// Read state
console.log(analysis);

// Update state
setAnalysis(newAnalysis);
```

**Why Zustand?**:
- Simple API (no boilerplate like Redux)
- Small bundle size
- Built-in persistence
- TypeScript support

---

### 3. API Client

**File**: `frontend/src/lib/api.ts`

**Base URL Function**:
```typescript
const getApiBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
};
```

**What it does**:
- Gets API base URL from environment variable
- Falls back to `http://localhost:8000` if not set
- Used by all API functions

**Analyze Resume Function**:
```typescript
export const analyzeResume = async (
  resumeText: string,
  targetRole?: string,
  preferredRoles?: string[],
  topKDomains?: number,
  signal?: AbortSignal
): Promise<AnalyzeResponse> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/analyze-resume`;
  
  const hash = await sha256(resumeText);
  const queryParams = new URLSearchParams({ hash: hash.substring(0, 8) });
  
  return fetchWithFallback<AnalyzeResponse>(
    `${url}?${queryParams.toString()}`,
    {
      method: 'POST',
      body: JSON.stringify({
        resume_text: resumeText,
        target_role: targetRole,
        preferred_roles: preferredRoles || [],
        top_k_domains: topKDomains || 5
      }),
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
      },
      signal,  // AbortController signal
    },
    generateMockAnalysis(),  // Fallback mock data
    'analyze_resume',
    { hash: hash.substring(0, 8), targetRole }
  );
};
```

**What it does**:
- **Computes Hash**: Creates SHA256 hash of resume text
- **Builds URL**: Constructs API endpoint URL with query params
- **Makes Request**: Sends POST request with resume data
- **AbortController**: Can cancel request if user switches files
- **Fallback**: Returns mock data if API fails
- **Tracking**: Sends Amplitude event

**SHA256 Hash Function**:
```typescript
async function sha256(text: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
```

**What it does**:
- **TextEncoder**: Converts string to bytes
- **crypto.subtle.digest**: Web Crypto API for SHA256 hashing
- **Array Conversion**: Converts hash bytes to hex string
- **Returns**: Hex string (64 characters)

**Why Hash?**:
- Unique identifier for resume
- Used for caching (same resume = same hash)
- Privacy: Only sends hash, not full text, to analytics

---

### 4. Home Page (Resume Upload)

**File**: `frontend/src/pages/Home.tsx`

**State Management**:
```typescript
const [text, setText] = useState('');
const [role, setRole] = useState('');
const [loading, setLoading] = useState(false);
const abortControllerRef = useRef<AbortController | null>(null);
```

**What it does**:
- **`text`**: Stores resume text (from paste or file upload)
- **`role`**: Stores user's selected target role
- **`loading`**: Shows loading spinner during analysis
- **`abortControllerRef`**: Reference to AbortController for canceling requests

**File Upload Handler**:
```typescript
const handleFileUpload = async (file: File) => {
  setLoading(true);
  
  // Cancel previous request
  if (abortControllerRef.current) {
    abortControllerRef.current.abort();
  }
  
  // Create new AbortController
  const abortController = new AbortController();
  abortControllerRef.current = abortController;
  
  try {
    // Upload PDF to backend
    const uploadResult = await uploadPDF(file);
    const text = uploadResult.text;
    
    // Compute hash
    const hash = await sha256(text);
    
    // Clear previous state
    setAnalysis(null);
    setJobs(null);
    setPlan(null);
    
    // Analyze resume
    const analysis = await analyzeResume(text, role, undefined, 5, abortController.signal);
    
    // Save to store
    setAnalysis(analysis);
    saveResume(role, text, analysis);
    
    // Track event
    track('resume_uploaded', { hash: hash.substring(0, 8), size: text.length });
    
    // Navigate to analysis page
    navigate('/analysis');
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Request cancelled');
    } else {
      toast.error('Failed to analyze resume');
    }
  } finally {
    setLoading(false);
  }
};
```

**What it does**:
- **Cancels Previous Request**: If user uploads new file, cancels old request
- **Uploads PDF**: Sends PDF to backend for text extraction
- **Computes Hash**: Creates unique identifier for resume
- **Clears State**: Removes previous analysis/jobs/plan
- **Analyzes Resume**: Calls API to analyze resume
- **Saves to Store**: Stores analysis in Zustand store
- **Tracks Event**: Sends Amplitude event
- **Navigates**: Redirects to analysis page

**Why AbortController?**:
- If user uploads new file while analysis is running, cancels old request
- Prevents race conditions (old response overwriting new one)
- Saves bandwidth and API costs

---

### 5. Analysis Page

**File**: `frontend/src/pages/Analysis.tsx`

**Data Retrieval**:
```typescript
const { analysis, setCoach } = useAppStore();

useEffect(() => {
  if (analysis) {
    const topDomain = analysis.domains?.[0];
    track('ai_analyzed', { 
      domain: topDomain?.name || 'unknown',
      domain_score: topDomain?.score || 0,
      domains_count: analysis.domains.length 
    });
  }
}, [analysis]);
```

**What it does**:
- **Gets Analysis**: Retrieves analysis from Zustand store
- **Tracks Event**: Sends Amplitude event when analysis is displayed
- **useEffect**: Runs when `analysis` changes

**Recommended Roles Click Handler**:
```typescript
<button
  onClick={() => {
    navigate('/jobs', { state: { role } });
    track('recommended_role_clicked', { role });
  }}
>
  {role}
</button>
```

**What it does**:
- **Navigates**: Goes to Jobs page with role pre-filled
- **Passes State**: Sends role via navigation state (not URL params)
- **Tracks Event**: Sends Amplitude event

**Why Navigation State?**:
- Cleaner URLs (no query params)
- Can pass complex data (objects, arrays)
- Only available during navigation (not in URL)

---

### 6. Jobs Page

**File**: `frontend/src/pages/Jobs.tsx`

**State Management**:
```typescript
const [linkedInJobs, setLinkedInJobs] = useState<LinkedInJobSearchItem[]>([]);
const [loading, setLoading] = useState(false);
const [nextCursor, setNextCursor] = useState<string | null>(null);
const [filters, setFilters] = useState({
  role: '',
  location: 'US-Remote',
  radius_km: 50,
  remote: false,
});
```

**What it does**:
- **`linkedInJobs`**: Stores list of jobs from API
- **`loading`**: Shows loading spinner
- **`nextCursor`**: Pagination cursor for "Load More"
- **`filters`**: Search filters (role, location, etc.)

**Auto-Search on Navigation**:
```typescript
const location = useLocation();

useEffect(() => {
  const roleFromState = (location.state as any)?.role;
  
  if (roleFromState) {
    setFilters(prev => ({ ...prev, role: roleFromState }));
  }
}, [location.state]);

useEffect(() => {
  const roleFromState = (location.state as any)?.role;
  if (roleFromState && filters.role === roleFromState && linkedInJobs.length === 0 && !loading) {
    handleSearch(null);
  }
}, [filters.role, location.state, linkedInJobs.length, loading]);
```

**What it does**:
- **Reads Navigation State**: Gets role from previous page
- **Updates Filters**: Sets role in filters
- **Auto-Searches**: Automatically searches for jobs when role is set

**Search Handler**:
```typescript
const handleSearch = async (e: React.FormEvent | null) => {
  if (e) e.preventDefault();
  
  setLoading(true);
  setLinkedInJobs([]);
  setNextCursor(null);
  
  try {
    const response = await searchJobs({
      role: filters.role,
      location: filters.location,
      radius_km: filters.radius_km,
      remote: filters.remote,
      limit: 15,
    });
    
    setLinkedInJobs(response.jobs);
    setNextCursor(response.nextCursor || null);
  } catch (error) {
    toast.error('Failed to fetch jobs');
  } finally {
    setLoading(false);
  }
};
```

**What it does**:
- **Prevents Default**: Stops form submission
- **Clears Previous Results**: Resets jobs list
- **Calls API**: Searches for jobs with filters
- **Updates State**: Sets jobs and pagination cursor
- **Error Handling**: Shows error toast if API fails

**Load More Handler**:
```typescript
const handleLoadMore = async () => {
  if (!nextCursor || loadingMore) return;
  
  setLoadingMore(true);
  
  try {
    const response = await searchJobs({
      role: filters.role,
      location: filters.location,
      cursor: nextCursor,
      limit: 15,
    });
    
    setLinkedInJobs(prev => [...prev, ...response.jobs]);
    setNextCursor(response.nextCursor || null);
  } catch (error) {
    toast.error('Failed to load more jobs');
  } finally {
    setLoadingMore(false);
  }
};
```

**What it does**:
- **Checks Cursor**: Only runs if more pages available
- **Appends Results**: Adds new jobs to existing list (doesn't replace)
- **Updates Cursor**: Sets next cursor for next page

---

## Data Flow

### Complete Flow: Resume Upload → Analysis → Jobs

**Step 1: User Uploads Resume**
```
User selects PDF file
  ↓
Home.tsx: handleFileUpload()
  ↓
uploadPDF(file) → POST /api/upload/pdf
  ↓
Backend: pdf_parser.parse_pdf() → Extracts text
  ↓
Returns: { text: "...", filename: "resume.pdf" }
```

**Step 2: Analyze Resume**
```
Home.tsx: analyzeResume(text, role)
  ↓
Frontend: Computes hash = sha256(text)
  ↓
POST /api/analyze-resume?hash=<hash>
  Body: { resume_text: "...", target_role: "AI Engineer" }
  ↓
Backend: analyze_resume()
  ↓
Tries Anthropic Claude (primary)
  ↓
If fails → Tries OpenAI GPT (fallback)
  ↓
If fails → Keyword-based analysis (heuristic)
  ↓
Post-process: Prioritizes target_role
  ↓
Returns: AnalyzeResponse
  ↓
Frontend: Stores in Zustand store
  ↓
Navigates to /analysis
```

**Step 3: Display Analysis**
```
Analysis.tsx: Reads from store
  ↓
Displays: Domains, Skills, Strengths, Areas for Growth
  ↓
User clicks recommended role
  ↓
Navigates to /jobs with role in state
```

**Step 4: Search Jobs**
```
Jobs.tsx: Reads role from navigation state
  ↓
Auto-searches: searchJobs({ role: "AI Engineer", location: "US-Remote" })
  ↓
GET /api/jobs/search?role=AI+Engineer&location=US-Remote
  ↓
Backend: Tries RapidAPI LinkedIn
  ↓
If fails → Free job service (RSS feeds)
  ↓
If fails → Generated fallback jobs
  ↓
Returns: LinkedInJobSearchResponse
  ↓
Frontend: Displays jobs with match scores
```

---

## Key Concepts Explained

### 1. AbortController

**Purpose**: Cancel ongoing HTTP requests

**Example**:
```typescript
const abortController = new AbortController();

fetch(url, { signal: abortController.signal })
  .then(response => response.json())
  .catch(error => {
    if (error.name === 'AbortError') {
      console.log('Request cancelled');
    }
  });

// Later, cancel the request
abortController.abort();
```

**Why Use It?**:
- User uploads new file → Cancel old analysis request
- User navigates away → Cancel pending requests
- Saves bandwidth and API costs

---

### 2. Zustand Persist

**Purpose**: Save state to localStorage

**Example**:
```typescript
export const useAppStore = create<AppState>()(
  persist(
    (set) => ({ /* state */ }),
    { name: 'careerlens-storage' }
  )
);
```

**What it does**:
- Automatically saves state to localStorage
- Restores state on page refresh
- User's analysis/jobs persist across sessions

---

### 3. React Router Navigation State

**Purpose**: Pass data between pages without URL params

**Example**:
```typescript
// Page 1: Navigate with state
navigate('/jobs', { state: { role: 'AI Engineer' } });

// Page 2: Read state
const location = useLocation();
const role = (location.state as any)?.role;
```

**Why Use It?**:
- Clean URLs (no query params)
- Can pass complex data
- Only available during navigation

---

### 4. Cache-Control Headers

**Purpose**: Prevent caching of API responses

**Example**:
```typescript
headers: {
  'Cache-Control': 'no-cache',  // Frontend request
}

// Backend response
response.headers["Cache-Control"] = "no-store"
```

**What it does**:
- **`no-cache`**: Browser must revalidate with server
- **`no-store`**: Don't cache at all
- Ensures fresh data (same resume always gets new analysis)

---

### 5. SHA256 Hashing

**Purpose**: Create unique identifier for resume

**Example**:
```typescript
const hash = await sha256(resumeText);
// hash = "a1b2c3d4e5f6..."
```

**What it does**:
- Same resume → Same hash (deterministic)
- Different resume → Different hash
- Used for: Caching, tracking, deduplication

---

## Summary

This codebase implements a full-stack career development platform:

**Backend**:
- FastAPI for REST API
- Anthropic/OpenAI for AI analysis
- Multiple job sources (RapidAPI, RSS feeds, fallback)
- Privacy-compliant analytics (Amplitude)

**Frontend**:
- React with TypeScript
- Zustand for state management
- React Router for navigation
- AbortController for request cancellation

**Key Features**:
- Role-agnostic analysis (works for any profession)
- Target role prioritization
- Personalized learning plans
- Robust job search (always returns jobs)
- Privacy-compliant tracking

Each component has a specific purpose and works together to provide a seamless user experience.

