# Code Explanation - How It Works

## 🏗️ Architecture Overview

```
User → Frontend (React) → Backend API (FastAPI) → External Services
```

### System Flow

1. **User interacts** with React frontend
2. **Frontend makes HTTP requests** to FastAPI backend
3. **Backend calls services** (Anthropic, OpenAI, Dedalus, etc.)
4. **Services call external APIs** (Claude, GPT, Amplitude, etc.)
5. **Response flows back** to frontend
6. **Frontend displays** results to user

## 📁 Project Structure

```
careerlens/
├── frontend/                    # React + Vite + TypeScript
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api.ts          # API calls to backend
│   │   │   ├── analytics.ts     # Amplitude tracking
│   │   │   └── utils.ts        # Utility functions
│   │   ├── store/
│   │   │   └── useAppStore.ts  # Zustand state management
│   │   ├── components/         # Reusable components
│   │   ├── pages/              # Route pages
│   │   └── types.ts            # TypeScript type definitions
│   └── package.json
├── backend/                     # FastAPI + Python 3.11
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Environment variable loading
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic models (API contracts)
│   │   ├── routes/              # API endpoints
│   │   │   ├── analyze.py      # POST /analyzeResume
│   │   │   ├── jobs.py         # POST /jobs/autoResearch
│   │   │   ├── tailor.py       # POST /tailor
│   │   │   ├── coach.py        # POST /autoCoach
│   │   │   └── predict.py      # GET /predict
│   │   └── services/            # Business logic
│   │       ├── anthropic_svc.py    # Claude AI for resume analysis
│   │       ├── openai_svc.py       # GPT for resume tailoring
│   │       ├── dedalus_svc.py      # Job research (multi-source)
│   │       ├── dedalus_mcp.py      # Dedalus MCP integration
│   │       ├── coach_svc.py         # Coaching plan generation
│   │       ├── predict_svc.py       # Score prediction formula
│   │       └── amplitude.py        # Analytics tracking
│   └── requirements.txt
└── .env                          # Environment variables
```

## 🔍 Service Explanations

### 1. Anthropic Service (Resume Analysis)

**File:** `backend/app/services/anthropic_svc.py`

**What it does:**
- Uses Claude AI to analyze resumes
- Returns score, strengths, weaknesses, skills, suggested roles

**How it works:**
```python
def analyze_resume(text: str, target_role: Optional[str]):
    # 1. Build prompt with strict JSON schema
    prompt = self._build_prompt(text, target_role)
    
    # 2. Call Claude API
    message = self.client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # 3. Parse response
    response_text = message.content[0].text.strip()
    
    # 4. Remove markdown code blocks if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    
    # 5. Parse JSON
    data = json.loads(response_text)
    
    # 6. Validate against Pydantic schema
    analyze_response = AnalyzeResponse(**data)
    
    # 7. Return as dict
    return analyze_response.model_dump()
```

**Key Features:**
- Retry logic (up to 3 times) for JSON parsing errors
- Schema validation with Pydantic
- Fallback to mock data if API fails
- Progress logging

**Route:** `POST /analyzeResume` → `backend/app/routes/analyze.py`

### 2. OpenAI Service (Resume Tailoring)

**File:** `backend/app/services/openai_svc.py`

**What it does:**
- Uses GPT to tailor resumes for specific jobs
- Generates STAR-format bullets, elevator pitch, cover letter

**How it works:**
```python
def tailor_for_job(resume: str, jd: str, style: str = "STAR"):
    # 1. Build prompt for tailoring
    prompt = self._build_prompt(resume, jd, style)
    
    # 2. Call OpenAI API
    response = self.client.chat.completions.create(
        model="gpt-4o",  # Falls back to gpt-4o-mini if unavailable
        messages=[
            {"role": "system", "content": "You are a professional resume writer."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    # 3. Parse response
    response_text = response.choices[0].message.content.strip()
    
    # 4. Parse JSON
    data = json.loads(response_text)
    
    # 5. Validate against Pydantic schema
    tailor_response = TailorResponse(**data)
    
    # 6. Return as dict
    return tailor_response.model_dump()
```

**Key Features:**
- Model fallback (gpt-4o → gpt-4o-mini)
- JSON schema validation
- Retry logic for validation errors
- STAR format support

**Route:** `POST /tailor` → `backend/app/routes/tailor.py`

### 3. Dedalus Service (Job Research)

**File:** `backend/app/services/dedalus_svc.py`

**What it does:**
- Researches jobs matching user's profile
- Uses multiple sources with intelligent fallback

**How it works:**
```python
def run_job_research(target_role: str, resume_summary: str):
    # Priority 1: Dedalus MCP (if available)
    if self.dedalus_mcp_service and self.dedalus_mcp_service.mcp_available:
        jobs = self.dedalus_mcp_service.run_job_research_mcp(...)
        return jobs
    
    # Priority 2: JSearch API (RapidAPI)
    if self.jsearch_available:
        jds = self._fetch_jobs_from_jsearch(target_role)
        # Process: extract skills, compute match scores
        return jobs
    
    # Priority 3: Fallback heuristics
    jds = self._fetch_jds_fallback(target_role)
    # Extract skills from resume and job descriptions
    resume_skills = self._extract_skills_from_text(resume_summary)
    jd_skills = self._extract_skills_from_text(jd["description"])
    
    # Compute match score
    match_score = self._compute_match_score(resume_skills, jd_skills, resume_gaps)
    
    # Generate why[] and fix[]
    why, fix = self._generate_why_and_fix(resume_skills, jd_skills, resume_gaps, match_score)
    
    return jobs
```

**Match Score Algorithm:**
```python
def _compute_match_score(resume_skills, jd_skills, resume_gaps):
    # Count matching skills
    matches = count of skills in both resume and job description
    
    # Calculate base score
    base_score = (matches / total_jd_skills) * 100
    
    # Apply penalties for gaps
    gap_penalty = gaps_in_jd * 10  # Max 30 points
    
    # Final score
    final_score = base_score - gap_penalty
    
    return final_score
```

**Key Features:**
- Multi-source fallback (MCP → JSearch → Heuristics)
- Skill extraction and matching
- Match score calculation
- Why/fix generation
- Progress logging

**Route:** `POST /jobs/autoResearch` → `backend/app/routes/jobs.py`

### 4. Coach Service (Coaching Plans)

**File:** `backend/app/services/coach_svc.py`

**What it does:**
- Generates 7-day personalized coaching plans
- Includes real course links from DataCamp, Udemy, Coursera, etc.

**How it works:**
```python
def generate_coach_plan(gaps: List[str], target_role: Optional[str], reminders: bool):
    # 1. Try Anthropic first, fallback to OpenAI
    if self.anthropic_client:
        data = self._generate_with_anthropic(gaps, target_role)
    elif self.openai_client:
        data = self._generate_with_openai(gaps, target_role)
    
    # 2. Extract plan from response
    plan_data = data.get("plan", [])
    
    # 3. Post-process to ensure exactly 7 days
    processed_plan = self._post_process_plan(plan_data)
    
    # 4. Create CoachPlan
    return CoachPlan(plan=processed_plan, reminders=reminders)
```

**Post-Processing:**
```python
def _post_process_plan(plan):
    # Ensure exactly 7 days
    if len(plan) < 7:
        # Pad with generic days
    elif len(plan) > 7:
        # Trim to 7 days
    
    # Ensure 2-3 actions per day
    for day in plan:
        if len(day.actions) < 2:
            # Add generic actions
        elif len(day.actions) > 3:
            # Trim to 3 actions
        
        # Ensure actions have real course links
        for action in day.actions:
            if not has_url(action):
                # Add real course link based on content
```

**Key Features:**
- AI-generated plans (Claude or OpenAI)
- Real course links (DataCamp, Udemy, Coursera, etc.)
- Post-processing for consistency
- Reminders support

**Route:** `POST /autoCoach` → `backend/app/routes/coach.py`

### 5. Amplitude Service (Analytics)

**File:** `backend/app/services/amplitude.py` + `frontend/src/lib/analytics.ts`

**What it does:**
- Tracks user events and behavior
- Provides insights into product usage

**How it works (Server-side):**
```python
def track(event_type: str, event_properties: Dict[str, Any]):
    payload = {
        "api_key": self.api_key,
        "events": [{
            "event_type": event_type,
            "event_properties": event_properties
        }]
    }
    
    response = httpx.post(
        "https://api2.amplitude.com/2/httpapi",
        json=payload
    )
```

**How it works (Client-side):**
```typescript
// Initialize
amplitude.init(API_KEY);

// Track event
amplitude.track(eventName, eventProperties);
```

**Events Tracked:**
- `resume_uploaded` - When user uploads resume
- `ai_analyzed` - When analysis is displayed
- `ai_analyzed_server` - When Claude analyzes resume (with score, gaps_count)
- `tailor_clicked` - When user clicks tailor button
- `tailor_completed` - When GPT tailors resume (with bullets_count, style)
- `coach_plan_generated` - When coaching plan is created (with gap_count, reminders)
- `job_viewed` - When user views a job
- `get_jobs_success` - When jobs are fetched (with jobCount, avgMatch)

**Key Features:**
- Dual tracking (client-side + server-side)
- Rich metadata for events
- Error handling (graceful degradation)

### 6. Predict Service (Score Prediction)

**File:** `backend/app/services/predict_svc.py`

**What it does:**
- Predicts score improvement after completing coaching plan
- Uses logistic formula

**How it works:**
```python
def compute_prediction(skills_have: List[str], skills_gap: List[str]):
    have_count = len(skills_have)
    gap_count = len(skills_gap)
    
    # Compute baseline score
    baseline_input = a * have_count - b * gap_count
    baseline = sigmoid(baseline_input) * 100
    
    # Compute afterPlan score (assuming 2 more skills learned, 2 gaps closed)
    after_plan_have = have_count + 2
    after_plan_gap = max(0, gap_count - 2)
    after_plan_input = a * after_plan_have - b * after_plan_gap
    after_plan = sigmoid(after_plan_input) * 100
    
    # Compute delta
    delta = after_plan - baseline
    
    return Prediction(
        baseline=round(baseline, 2),
        afterPlan=round(after_plan, 2),
        delta=round(delta, 2)
    )
```

**Formula:**
- `baseline = sigmoid(a × have_count - b × gap_count) × 100`
- `afterPlan = sigmoid(a × (have_count + 2) - b × (gap_count - 2)) × 100`
- `delta = afterPlan - baseline`
- Constants: `a = 0.15`, `b = 0.20`

**Sigmoid Function:**
```python
def sigmoid(x):
    return 1 / (1 + math.exp(-x))
```

**Key Features:**
- Deterministic formula
- Fixed constants for consistent results
- Sigmoid function for smooth scaling

**Route:** `GET /predict` → `backend/app/routes/predict.py`

## 🔄 Data Flow Examples

### Resume Analysis Flow

```
1. User uploads resume → Frontend (Home page)
2. Frontend calls: POST /analyzeResume
3. Backend route: analyze.py → anthropic_svc.analyze_resume()
4. Anthropic service calls Claude API
5. Claude returns analysis JSON
6. Service validates with Pydantic schema
7. Amplitude tracks: ai_analyzed_server
8. Backend returns: AnalyzeResponse
9. Frontend stores in Zustand store
10. Frontend navigates to /analysis page
11. Frontend displays: score, strengths, weaknesses, skills
```

### Job Research Flow

```
1. User clicks "Auto-Research" → Frontend (Jobs page)
2. Frontend calls: POST /jobs/autoResearch
3. Backend route: jobs.py → dedalus_svc.run_job_research()
4. Dedalus service tries:
   - Priority 1: Dedalus MCP (if available)
   - Priority 2: JSearch API (if RapidAPI key provided)
   - Priority 3: Fallback heuristics
5. Service extracts skills, computes match scores
6. Service generates why[] and fix[] arrays
7. Backend returns: List[Job]
8. Frontend stores in Zustand store
9. Frontend displays: Job cards with match scores
```

### Resume Tailoring Flow

```
1. User clicks "Tailor" → Frontend (Jobs page)
2. Frontend calls: POST /tailor
3. Backend route: tailor.py → openai_svc.tailor_for_job()
4. OpenAI service calls GPT API
5. GPT returns tailored content JSON
6. Service validates with Pydantic schema
7. Amplitude tracks: tailor_completed
8. Backend returns: TailorResponse
9. Frontend stores in Zustand store
10. Frontend displays: TailorModal with bullets, pitch, cover letter
```

## 📊 State Management

### Frontend Store (Zustand)

**File:** `frontend/src/store/useAppStore.ts`

**State:**
```typescript
{
  resumeText: string
  analysis: AnalyzeResponse | null
  jobs: Job[]
  tailor: TailorResponse | null
  coach: CoachPlan | null
}
```

**Usage:**
```typescript
// Get state
const { analysis, jobs } = useAppStore();

// Update state
const { setAnalysis, setJobs } = useAppStore();
setAnalysis(analysisData);
setJobs(jobsData);
```

## 🔐 API Contracts

### Frontend Types

**File:** `frontend/src/types.ts`

```typescript
export interface AnalyzeResponse {
  score: number; // 0..100
  strengths: string[];
  weaknesses: string[];
  skills: Skill[];
  suggestedRoles: string[];
}

export interface Job {
  id: string;
  title: string;
  company: string;
  match: number; // 0..100
  why: string[];
  fix: string[];
  jdUrl: string;
  source?: string; // "jsearch", "dedalus-mcp", "fallback"
}

export interface TailorResponse {
  bullets: string[];
  pitch: string;
  coverLetter: string;
}

export interface CoachPlan {
  plan: PlanDay[];
  reminders: boolean;
}
```

### Backend Schemas

**File:** `backend/app/models/schemas.py`

```python
class AnalyzeResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: List[str]
    weaknesses: List[str]
    skills: List[Skill]
    suggestedRoles: List[str]

class Job(BaseModel):
    id: str
    title: str
    company: str
    match: int = Field(ge=0, le=100)
    why: List[str]
    fix: List[str]
    jdUrl: HttpUrl
    source: str | None = None

class TailorResponse(BaseModel):
    bullets: List[str]
    pitch: str
    coverLetter: str

class CoachPlan(BaseModel):
    plan: List[PlanDay]
    reminders: bool
```

## 🎯 Key Design Patterns

1. **Service Layer Pattern** - Business logic separated from routes
2. **Fallback Pattern** - Graceful degradation if APIs fail
3. **Retry Pattern** - Retry logic for transient errors
4. **Validation Pattern** - Pydantic schemas for type safety
5. **State Management** - Zustand for frontend state
6. **Error Handling** - Try-catch with fallback to mock data

## 📝 Summary

- **Frontend:** React + TypeScript + Zustand for state
- **Backend:** FastAPI + Python + Pydantic for validation
- **Services:** Anthropic, OpenAI, Dedalus, Coach, Predict, Amplitude
- **Data Flow:** User → Frontend → Backend → Services → External APIs
- **Error Handling:** Fallback to mock data if APIs fail
- **Analytics:** Amplitude tracking (client + server)

