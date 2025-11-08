# CareerLens AI - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture](#architecture)
4. [API Endpoints](#api-endpoints)
5. [Services & APIs Used](#services--apis-used)
6. [Code Structure](#code-structure)
7. [Key Features](#key-features)
8. [How It Works](#how-it-works)
9. [Environment Variables](#environment-variables)
10. [Deployment](#deployment)

---

## Project Overview

CareerLens AI is a comprehensive career development platform that provides:
- **Resume Analysis**: AI-powered analysis of resumes for any profession (tech, healthcare, education, finance, business, etc.)
- **Job Matching**: Intelligent job search with skill-based matching
- **Learning Plans**: Personalized 7-14 day coaching plans tailored to specific roles and skill gaps
- **Resume Tailoring**: AI-generated resume bullets, elevator pitches, and cover letters
- **Progress Tracking**: Track resume improvements over time with detailed metrics

The platform uses advanced AI (Anthropic Claude, OpenAI GPT) to provide role-agnostic analysis and recommendations, making it suitable for professionals across all industries.

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn 0.24.0
- **Language**: Python 3.11+
- **Data Validation**: Pydantic 2.5.0, Pydantic-Settings 2.1.0
- **HTTP Client**: httpx 0.25.2
- **PDF Parsing**: pypdf 3.17.4
- **AWS Lambda**: mangum 0.17.0 (for serverless deployment)

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **State Management**: Zustand with persistence
- **Routing**: React Router DOM
- **Authentication**: Firebase Auth
- **Analytics**: Amplitude
- **HTTP Client**: Fetch API with AbortController

### AI/ML Services
- **Primary LLM**: Anthropic Claude (claude-3-haiku-20240307)
- **Fallback LLM**: OpenAI GPT-4o / GPT-4o-mini
- **Job Search**: RapidAPI LinkedIn Job Search API, Dedalus Labs SDK
- **Free Job Sources**: Jobicy RSS, RemoteOK, WeWorkRemotely, Authentic Jobs, Indeed RSS

### Analytics
- **Frontend**: Amplitude (browser-based tracking)
- **Backend**: Amplitude (server-side tracking)

---

## Architecture

### Backend Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, global exception handler
│   ├── config.py               # Settings (pydantic-settings)
│   ├── models/
│   │   └── schemas.py          # Pydantic models (API contracts)
│   ├── routes/
│   │   ├── analyze.py          # Resume analysis endpoint
│   │   ├── generatePlan.py     # Learning plan generation
│   │   ├── roleMatch.py        # Job matching with Dedalus/free sources
│   │   ├── linkedinJobs.py     # RapidAPI LinkedIn job search
│   │   ├── tailor.py           # Resume tailoring
│   │   ├── coach.py            # 7-day coaching plan
│   │   ├── predict.py          # Score prediction
│   │   ├── upload.py           # PDF upload & parsing
│   │   └── jobs.py             # Legacy job endpoint
│   └── services/
│       ├── anthropic_svc.py    # Anthropic Claude integration
│       ├── openai_svc.py       # OpenAI GPT integration
│       ├── dedalus_svc.py      # Dedalus Labs SDK integration
│       ├── dedalus_mcp.py      # Dedalus MCP integration
│       ├── free_job_svc.py     # Free job sources (RSS, public APIs)
│       ├── job_scoring_svc.py  # Skill-based job matching algorithm
│       ├── pdf_parser.py       # PDF text extraction
│       ├── coach_svc.py        # Coaching plan generation
│       ├── predict_svc.py      # Score prediction algorithm
│       └── amplitude.py        # Amplitude analytics
└── requirements.txt
```

### Frontend Structure
```
frontend/
├── src/
│   ├── main.tsx                # React entry point
│   ├── App.tsx                 # Main app component with routing
│   ├── pages/
│   │   ├── Home.tsx            # Resume upload & analysis trigger
│   │   ├── Analysis.tsx        # Analysis results display
│   │   ├── Jobs.tsx            # Job listings with filters
│   │   ├── Dashboard.tsx       # Overview dashboard
│   │   ├── Progress.tsx        # Progress tracking
│   │   └── CoachingPlan.tsx   # Learning plan display
│   ├── components/
│   │   ├── LinkedInJobCard.tsx # Job card component
│   │   ├── TailorModal.tsx     # Resume tailoring modal
│   │   ├── ErrorBoundary.tsx   # Error boundary for crashes
│   │   └── ui/                 # shadcn/ui components
│   ├── lib/
│   │   ├── api.ts              # API client functions
│   │   ├── analytics.ts        # Amplitude tracking
│   │   └── utils.ts            # Utility functions
│   ├── store/
│   │   └── useAppStore.ts      # Zustand state management
│   └── types.ts                # TypeScript type definitions
└── package.json
```

---

## API Endpoints

### 1. Resume Analysis
**Endpoint**: `POST /api/analyze-resume?hash=<resume_hash>&top_k_domains=5`

**Request Body**:
```json
{
  "resume_text": "Full resume text...",
  "target_role": "AI Engineer",  // Optional: user's selected target role
  "preferred_roles": ["AI Engineer"],  // Optional
  "top_k_domains": 5
}
```

**Response**:
```json
{
  "domains": [
    {"name": "ML/AI", "score": 0.9},
    {"name": "Data Analyst", "score": 0.75}
  ],
  "skills": {
    "core": ["Python", "PyTorch", "TensorFlow"],
    "adjacent": ["SQL", "Pandas"],
    "advanced": ["MLOps", "LLMs"]
  },
  "strengths": ["Python programming skills", "Deep learning framework experience"],
  "areas_for_growth": ["MLOps and model deployment", "Large Language Models"],
  "recommended_roles": ["AI Engineer", "ML Engineer", "Data Scientist"],
  "keywords_detected": ["python", "pytorch", "tensorflow", "ml"],
  "debug": {
    "hash": "a1b2c3d4",
    "provider": "anthropic"
  }
}
```

**Functionality**:
- Uses Anthropic Claude (primary) or OpenAI GPT (fallback) for AI analysis
- Falls back to keyword-based analysis if LLM unavailable
- Supports **any profession** (tech, healthcare, education, finance, business, etc.)
- If `target_role` is provided, it becomes the PRIMARY domain (score 0.9)
- Extracts skills, strengths, and gaps specific to the target role
- Returns multi-domain classification (up to 5 domains)

**Code Location**: `backend/app/routes/analyze.py`, `backend/app/services/anthropic_svc.py`, `backend/app/services/openai_svc.py`

---

### 2. Job Search (LinkedIn via RapidAPI)
**Endpoint**: `GET /api/jobs/search?role=<role>&location=<location>&radius_km=50&remote=false&limit=15&cursor=<cursor>`

**Response**:
```json
{
  "jobs": [
    {
      "id": "job-123",
      "title": "AI Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "url": "https://www.linkedin.com/jobs/view/12345",
      "listed_at": "2024-01-15",
      "source": "linkedin",
      "description_snippet": "We are looking for...",
      "matchScore": 85,
      "reasons": ["Python experience", "ML framework knowledge"],
      "gaps": ["MLOps", "LLMs"]
    }
  ],
  "nextCursor": "cursor_string",
  "debug": {
    "source": "rapidapi",
    "count": 15
  }
}
```

**Functionality**:
- Calls RapidAPI LinkedIn "Ultra - Get Jobs Hourly" endpoint
- Falls back to free job service if RapidAPI fails or key not set
- Computes match score using weighted Jaccard similarity
- Filters expired LinkedIn URLs
- Supports pagination with cursor

**Code Location**: `backend/app/routes/linkedinJobs.py`

---

### 3. Job Matching (Dedalus + Free Sources)
**Endpoint**: `POST /api/roleMatchAndOpenings?hash=<resume_hash>`

**Request Body**:
```json
{
  "resume_text": "Full resume text...",
  "domains": [{"name": "ML/AI", "score": 0.9}],
  "preferred_roles": ["AI Engineer"],
  "locations": ["US-Remote", "San Francisco, CA"],
  "top_n": 20
}
```

**Response**:
```json
{
  "items": [
    {
      "title": "AI Engineer",
      "company": "Tech Corp",
      "location": "Remote",
      "match": 0.85,
      "why_fit": ["Python experience", "ML framework knowledge"],
      "gaps": ["MLOps", "LLMs"],
      "url": "https://...",
      "source": "dedalus"
    }
  ],
  "debug": {
    "source": "dedalus",
    "count": 15
  }
}
```

**Functionality**:
- Uses Dedalus Labs SDK if `DEDALUS_API_KEY` is set
- Falls back to free job service (RSS feeds, public APIs)
- Computes match score using skill vectorization and rule-based scoring
- Extracts "why_fit" and "gaps" from job descriptions
- Always returns jobs with valid URLs (filters expired/invalid)

**Code Location**: `backend/app/routes/roleMatch.py`, `backend/app/services/dedalus_svc.py`, `backend/app/services/free_job_svc.py`, `backend/app/services/job_scoring_svc.py`

---

### 4. Learning Plan Generation
**Endpoint**: `POST /api/generatePlan?hash=<resume_hash>`

**Request Body**:
```json
{
  "resume_text": "Full resume text...",
  "selected_role": "AI Engineer",
  "jd_requirements": ["MLOps experience", "LLM fine-tuning", "Model deployment"],
  "gaps": ["MLOps", "LLMs"],
  "horizon_days": 7,
  "skills_core": ["Python", "PyTorch"],
  "skills_adjacent": ["SQL", "Pandas"],
  "skills_advanced": []
}
```

**Response**:
```json
{
  "role": "AI Engineer",
  "objectives": [
    "Master MLOps and model deployment",
    "Learn LLM fine-tuning techniques"
  ],
  "plan_days": [
    {
      "day": 1,
      "title": "MLOps Fundamentals",
      "actions": [
        "Complete 'MLOps Specialization' on Coursera",
        "Set up MLflow tracking server"
      ]
    }
  ],
  "deliverables": [
    "ML pipeline with MLflow",
    "Deployed model with FastAPI"
  ],
  "apply_checkpoints": [
    {
      "when": "Day 5",
      "criteria": ["MLflow pipeline complete", "Model deployed"]
    }
  ]
}
```

**Functionality**:
- Uses Anthropic Claude or OpenAI GPT to generate personalized learning plans
- **Role-agnostic**: Works for any profession (tech, healthcare, education, finance, etc.)
- Personalizes courses based on existing skills (avoids beginner courses if advanced)
- Includes real course URLs from Coursera, Udemy, DataCamp, LinkedIn Learning, etc.
- Maps each gap to specific courses and projects
- Generates role-specific deliverables (e.g., IRB protocols for clinical roles, lesson plans for teachers)

**Code Location**: `backend/app/routes/generatePlan.py`

---

### 5. Resume Tailoring
**Endpoint**: `POST /api/tailor`

**Request Body**:
```json
{
  "resume": "Resume text...",
  "job_description": "Job description...",
  "style": "STAR"
}
```

**Response**:
```json
{
  "bullets": [
    "Led team of 5 engineers to refactor legacy codebase, resulting in 40% performance improvement"
  ],
  "pitch": "50-word elevator pitch...",
  "coverLetter": "120-180 word cover letter..."
}
```

**Functionality**:
- Uses OpenAI GPT-4o to generate tailored resume content
- Creates STAR-format bullets, elevator pitch, and cover letter
- Tailored to specific job description

**Code Location**: `backend/app/routes/tailor.py`, `backend/app/services/openai_svc.py`

---

### 6. PDF Upload
**Endpoint**: `POST /api/upload/pdf`

**Request**: Multipart form data with PDF file

**Response**:
```json
{
  "text": "Extracted resume text...",
  "filename": "resume.pdf"
}
```

**Functionality**:
- Extracts text from PDF using pypdf
- Returns plain text for analysis

**Code Location**: `backend/app/routes/upload.py`, `backend/app/services/pdf_parser.py`

---

### 7. Health Check
**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "ok": true,
  "providers": {
    "anthropic": true,
    "openai": true,
    "dedalus": false,
    "mcp": false
  }
}
```

**Functionality**:
- Checks backend health and API key availability
- Used by frontend to show banners for missing keys

**Code Location**: `backend/app/main.py`

---

## Services & APIs Used

### 1. Anthropic Claude API
**Purpose**: Primary LLM for resume analysis and learning plan generation

**Usage**:
- **Model**: `claude-3-haiku-20240307`
- **Temperature**: 0.1 (deterministic)
- **Max Tokens**: 3000
- **Retries**: 3 attempts with exponential backoff

**Key Features**:
- Multi-domain classification (open-world)
- Role-agnostic analysis (works for any profession)
- Extracts skills, strengths, gaps from resume text
- Generates personalized learning plans

**Code Location**: `backend/app/services/anthropic_svc.py`

**API Key**: `ANTHROPIC_API_KEY` in `.env`

---

### 2. OpenAI GPT API
**Purpose**: Fallback LLM for analysis and primary LLM for resume tailoring

**Usage**:
- **Model**: `gpt-4o` (primary), `gpt-4o-mini` (fallback)
- **Temperature**: 0.1 (analysis), 0.7 (tailoring)
- **Max Tokens**: 3000 (analysis), 1000 (tailoring)
- **Response Format**: JSON object for structured output

**Key Features**:
- Same analysis capabilities as Anthropic
- Specialized for resume tailoring (STAR format, cover letters)
- JSON mode for reliable structured output

**Code Location**: `backend/app/services/openai_svc.py`

**API Key**: `OPENAI_API_KEY` in `.env`

---

### 3. RapidAPI LinkedIn Job Search API
**Purpose**: Fetch real-time LinkedIn job listings

**Usage**:
- **Endpoint**: `GET https://linkedin-job-search-api.p.rapidapi.com/active-jb-1h`
- **Headers**: `X-RapidAPI-Key`, `X-RapidAPI-Host`
- **Parameters**: `keywords`, `location`, `radius_km`, `remote`, `limit`, `cursor`

**Key Features**:
- Real-time job listings from LinkedIn
- Pagination support (cursor-based)
- Filters expired/invalid URLs
- Generates valid LinkedIn search URLs if original URL is missing

**Code Location**: `backend/app/routes/linkedinJobs.py`

**API Key**: `RAPIDAPI_KEY` in `.env`

**API Host**: `linkedin-job-search-api.p.rapidapi.com`

---

### 4. Dedalus Labs SDK
**Purpose**: Job research and matching (optional, premium feature)

**Usage**:
- **SDK**: `dedalus-labs` Python package
- **MCP Integration**: Optional MCP (Model Context Protocol) support
- **Features**: Job search, JD analysis, skill matching

**Key Features**:
- Premium job search with detailed JD analysis
- MCP integration for enhanced job matching
- Falls back to free sources if not available

**Code Location**: `backend/app/services/dedalus_svc.py`, `backend/app/services/dedalus_mcp.py`

**API Key**: `DEDALUS_API_KEY` in `.env`

---

### 5. Free Job Service
**Purpose**: Fallback job search using free sources (no API keys required)

**Sources**:
1. **Jobicy RSS**: `https://jobicy.com/api/v2/remote-jobs`
2. **RemoteOK RSS**: `https://remoteok.com/remote-jobs.rss`
3. **WeWorkRemotely RSS**: `https://weworkremotely.com/categories/remote-programming-jobs.rss`
4. **Authentic Jobs RSS**: `https://authenticjobs.com/rss/`
5. **Indeed RSS**: `https://rss.indeed.com/rss?q=<query>&l=<location>`
6. **USAJOBS API**: `https://data.usajobs.gov/api/Search` (if `USAJOBS_API_KEY` provided)
7. **Static Fallback Jobs**: Pre-generated jobs for demo purposes

**Key Features**:
- No API keys required (except USAJOBS, optional)
- Parses RSS feeds using `xml.etree.ElementTree`
- Generates realistic job data with valid URLs
- Role-specific job generation (Data Engineer, AI Engineer, etc.)
- Always returns jobs (ensures no "no jobs found" errors)

**Code Location**: `backend/app/services/free_job_svc.py`

---

### 6. Job Scoring Service
**Purpose**: Skill-based job matching algorithm

**Algorithm**:
- **Skill Vectorization**: Represents candidate and JD skills as numerical vectors
- **Weighted Jaccard Similarity**: Computes overlap between skill vectors
- **Rule-Based Scoring**:
  - Core skill match: +10 points
  - Adjacent skill match: +5 points
  - Advanced skill match: +3 points
  - Required skill gap: -8 points
  - Optional skill gap: -4 points
  - Exact tool match: +5 points
  - Experience boost: +2 points
- **Normalization**: Maps to 0-100 score range

**Key Features**:
- Generates "why_fit" reasons (top 5 matches)
- Generates "gaps" list (top 3 missing skills)
- Micro-actions for closing gaps

**Code Location**: `backend/app/services/job_scoring_svc.py`

---

### 7. Amplitude Analytics
**Purpose**: User behavior tracking (privacy-compliant)

**Events Tracked**:
- `resume_uploaded`: {hash, size}
- `analysis_completed`: {hash, provider, strengths_count, areas_count}
- `jobs_fetched`: {hash, count, source}
- `plan_generated`: {hash, role}
- `tailor_clicked`: {jobId, jobMatch}
- `recommended_role_clicked`: {role}

**Privacy**:
- **Never** sends raw resume text or PII
- Only sends hash (first 8 chars), counts, and metadata
- Complies with GDPR/CCPA

**Code Location**: 
- Frontend: `frontend/src/lib/analytics.ts`
- Backend: `backend/app/services/amplitude.py`

**API Key**: 
- Frontend: `VITE_AMPLITUDE_API_KEY` in `.env`
- Backend: `AMPLITUDE_API_KEY` in `.env`

---

### 8. Firebase Authentication
**Purpose**: User authentication and session management

**Usage**:
- Firebase Auth for login/signup
- JWT tokens for session management
- Protected routes in frontend

**Code Location**: `frontend/src/contexts/AuthContext.tsx`

---

## Code Structure

### Backend Analysis Flow

1. **Request Received** (`backend/app/routes/analyze.py:676`)
   - Extracts `target_role` from request (supports `target_role`, `targetRole`, `preferred_roles`)
   - Computes resume hash (SHA256)

2. **LLM Analysis** (`backend/app/services/anthropic_svc.py:119`)
   - Builds prompt with role-agnostic instructions
   - Calls Anthropic Claude API
   - Falls back to OpenAI GPT if Anthropic fails
   - Falls back to keyword-based analysis if both fail

3. **Post-Processing** (`backend/app/routes/analyze.py:769`)
   - If `target_role` provided, forces it as top domain (score 0.9)
   - Updates recommended_roles to match target_role
   - Updates strengths and areas_for_growth to be role-specific
   - Validates response against Pydantic schema

4. **Response** (`backend/app/routes/analyze.py:920`)
   - Returns `AnalyzeResponse` with domains, skills, strengths, gaps, recommended_roles
   - Sends Amplitude event (hash, counts, provider only)

### Frontend Analysis Flow

1. **Resume Upload** (`frontend/src/pages/Home.tsx:120`)
   - User uploads PDF or pastes text
   - Computes `resumeHash = sha256(resumeText)`
   - Clears previous analysis/jobs/plan
   - Sets container `key={resumeHash}` to force remount

2. **API Call** (`frontend/src/lib/api.ts:84`)
   - Calls `POST /api/analyze-resume?hash=<hash>`
   - Includes `Cache-Control: no-cache` header
   - Uses `AbortController` to cancel prior requests
   - Sends full `resume_text` in body

3. **State Update** (`frontend/src/pages/Home.tsx:150`)
   - Stores analysis in Zustand store
   - Calculates dynamic score (not hardcoded)
   - Tracks Amplitude event (hash, counts only)

4. **Display** (`frontend/src/pages/Analysis.tsx`)
   - Shows domains, skills, strengths, areas for growth
   - Recommended roles are clickable (navigate to Jobs page)
   - Score displayed in donut chart

### Job Search Flow

1. **User Clicks Recommended Role** (`frontend/src/pages/Analysis.tsx:373`)
   - Navigates to Jobs page with role pre-filled
   - Tracks `recommended_role_clicked` event

2. **Jobs Page** (`frontend/src/pages/Jobs.tsx:52`)
   - Initializes filters from navigation state or analysis
   - Auto-searches if role passed from navigation

3. **API Call** (`frontend/src/lib/api.ts:521`)
   - Calls `GET /api/jobs/search?role=<role>&location=<location>...`
   - Uses `AbortController` for cancellation

4. **Backend Processing** (`backend/app/routes/linkedinJobs.py:28`)
   - Tries RapidAPI LinkedIn first
   - Falls back to free job service if RapidAPI fails
   - Computes match scores using skill vectorization
   - Filters expired/invalid URLs
   - Returns paginated results

5. **Display** (`frontend/src/pages/Jobs.tsx:280`)
   - Renders `LinkedInJobCard` for each job
   - Shows match score, reasons, gaps
   - "View Job Posting" opens job URL in new tab
   - "Tailor Resume" opens tailoring modal

---

## Key Features

### 1. Role-Agnostic Analysis
- **Works for ANY profession**: Tech, Healthcare, Education, Finance, Business, etc.
- **Open-World Classification**: Can classify any role, not limited to predefined list
- **Target Role Prioritization**: User's selected target role becomes PRIMARY domain
- **Domain Mapping**: Maps target roles to domains (e.g., "AI Engineer" → "ML/AI", "Registered Nurse" → "Registered Nurse")

### 2. Dynamic Skill Extraction
- **Evidence-Based**: Only extracts skills explicitly mentioned in resume
- **No Inference**: Never adds skills not present (e.g., won't add TypeScript unless mentioned)
- **Multi-Level**: Organizes skills into core, adjacent, advanced based on evidence strength

### 3. Personalized Learning Plans
- **Skill-Level Matching**: Recommends advanced courses if basics are known
- **Gap-Specific**: Each gap maps to specific courses and projects
- **Real Course URLs**: Includes actual course links from Coursera, Udemy, DataCamp, etc.
- **Role-Specific Deliverables**: 
  - Healthcare: IRB protocols, REDCap forms, consent scripts
  - Education: Lesson plans, IEP templates, assessment rubrics
  - Finance: QuickBooks reconciliations, GAAP journal entries
  - Tech: GitHub repos, deployed models, API implementations

### 4. Robust Job Search
- **Multi-Source**: RapidAPI LinkedIn → Free RSS feeds → Static fallback
- **Always Returns Jobs**: Never shows "no jobs found" (fallback ensures results)
- **Skill-Based Matching**: Computes match scores using skill vectors
- **Valid URLs Only**: Filters expired/invalid job URLs

### 5. Progress Tracking
- **Version History**: Tracks resume versions over time
- **Score Calculation**: Dynamic score based on domains, skills, strengths/growth ratio
- **Improvement Metrics**: Tracks new skills, improved skills, closed gaps
- **Visual Charts**: Score over time, skill improvements, domain changes

---

## How It Works

### Resume Analysis Pipeline

```
1. User uploads resume → PDF parsed → Text extracted
2. Frontend computes hash = sha256(resumeText)
3. Frontend calls POST /api/analyze-resume?hash=<hash>
   Body: { resume_text, target_role, preferred_roles, top_k_domains }
4. Backend extracts target_role from request
5. Backend tries Anthropic Claude (primary LLM)
   - Prompt: Role-agnostic, evidence-based, target_role prioritized
   - Response: JSON with domains, skills, strengths, gaps, recommended_roles
6. If Anthropic fails → Try OpenAI GPT (fallback LLM)
7. If both fail → Keyword-based analysis (heuristic)
8. Backend post-processes:
   - If target_role provided → Force as top domain (score 0.9)
   - Update recommended_roles to match target_role
   - Update strengths/gaps to be role-specific
9. Backend returns AnalyzeResponse
10. Frontend stores in Zustand, calculates dynamic score
11. Frontend displays in Analysis page
```

### Job Search Pipeline

```
1. User clicks recommended role or searches manually
2. Frontend calls GET /api/jobs/search?role=<role>&location=<location>...
3. Backend tries RapidAPI LinkedIn:
   - Calls RapidAPI endpoint with role/location
   - Maps response to Job schema
   - Computes match scores using skill vectors
   - Filters expired URLs
4. If RapidAPI fails → Free job service:
   - Parses RSS feeds (Jobicy, RemoteOK, etc.)
   - Generates role-specific jobs
   - Ensures valid URLs
5. Backend returns paginated jobs
6. Frontend displays jobs with match scores, reasons, gaps
7. User can click "View Job Posting" or "Tailor Resume"
```

### Learning Plan Generation Pipeline

```
1. User selects a job and clicks "Generate Plan"
2. Frontend calls POST /api/generatePlan
   Body: { resume_text, selected_role, jd_requirements, gaps, skills_core, skills_adjacent, skills_advanced }
3. Backend builds prompt:
   - Includes candidate's existing skills (for personalization)
   - Lists JD requirements and gaps
   - Role-specific guidance (healthcare, education, finance, tech, etc.)
4. Backend calls Anthropic Claude or OpenAI GPT
5. LLM generates:
   - Objectives (2-4 specific goals)
   - Plan days (7-14 days with daily tasks)
   - Deliverables (role-specific artifacts)
   - Apply checkpoints (when ready to apply)
6. Backend returns GeneratePlanResponse
7. Frontend displays in CoachingPlan page
```

---

## Environment Variables

### Backend (.env)
```bash
# AI/ML APIs
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Job Search APIs
RAPIDAPI_KEY=...
DEDALUS_API_KEY=...  # Optional
USAJOBS_API_KEY=...  # Optional

# Analytics
AMPLITUDE_API_KEY=...

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=backend/firebase-service-account.json

# AWS (for serverless)
AWS_REGION=us-east-1
S3_BUCKET=careerlens-uploads
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_AMPLITUDE_API_KEY=...
```

---

## Deployment

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### AWS Lambda (Serverless)
- Uses `mangum` adapter for FastAPI
- Handler: `handler = Mangum(app)` in `main.py`
- Deploy using AWS SAM or Serverless Framework

---

## API Functionality Details

### Resume Analysis (`/api/analyze-resume`)

**LLM Prompt Structure**:
1. **System Instructions**: Role-agnostic analyzer, evidence-based extraction
2. **Target Role Instructions**: If provided, prioritize as PRIMARY domain
3. **Domain Ordering Rules**: Primary role first, secondary skills lower scores
4. **Skill Extraction Rules**: Only explicit mentions, no inference
5. **Strengths Rules**: Role-specific, evidenced, no templates
6. **Gaps Rules**: Based on role competencies, industry standards
7. **Recommended Roles Rules**: Same profession family as target_role

**Keyword-Based Fallback**:
- Uses `DOMAIN_KEYWORDS` dictionary (50+ domains)
- Uses `ROLE_COMPETENCY_MATRIX` for gap detection
- Supports explicit role mentions (highest priority)
- Boosts Data Analyst if strong keywords detected
- Prevents Frontend from overriding Data Analyst

**Post-Processing**:
- Forces target_role to be top domain (score 0.9)
- Reduces competing domain scores
- Updates recommended_roles to match target_role
- Updates strengths/gaps to be role-specific

### Job Search (`/api/jobs/search`)

**RapidAPI Integration**:
- Endpoint: `GET /active-jb-1h`
- Headers: `X-RapidAPI-Key`, `X-RapidAPI-Host`
- Query Params: `keywords`, `location`, `radius_km`, `remote`, `limit`, `cursor`
- Response Mapping: Maps RapidAPI response to `LinkedInJobSearchItem` schema
- URL Generation: Creates valid LinkedIn search URL if original URL is missing/expired

**Free Job Service**:
- Parses RSS feeds using `xml.etree.ElementTree`
- Extracts: title, company, location, description, URL
- Generates role-specific jobs if RSS fails
- Always returns jobs (no "no jobs found" errors)

**Match Scoring**:
- Extracts skills from resume (from stored analysis)
- Extracts keywords from job title + description
- Computes weighted Jaccard similarity
- Generates "reasons" (top 3 matches)
- Generates "gaps" (top 3 missing skills)

### Learning Plan Generation (`/api/generatePlan`)

**Prompt Structure**:
1. **Role-Specific Guidance**: Different instructions for healthcare, education, finance, tech, etc.
2. **Skill-Level Matching**: Analyzes existing skills to recommend appropriate course levels
3. **Gap-to-Course Mapping**: Each gap maps to specific courses with URLs
4. **Project-Based Learning**: Every course includes a related project
5. **Real Course URLs**: Includes actual links from Coursera, Udemy, DataCamp, etc.

**Role-Specific Examples**:
- **Healthcare**: CITI Program courses, REDCap tutorials, IRB protocols
- **Education**: Coursera Education courses, lesson plan templates, IEP management
- **Finance**: QuickBooks training, GAAP courses, financial modeling
- **Tech**: Domain-specific (AI Engineer → MLOps, LLMs; Data Analyst → SQL, BI tools)

**Deliverables**:
- Role-specific artifacts (IRB protocols, lesson plans, financial models, GitHub repos)
- Portfolio-worthy projects
- Real-world applications

---

## Code Examples

### Resume Analysis Request
```python
# Backend: backend/app/routes/analyze.py
@router.post("")
async def analyze_resume(
    request: AnalyzeRequest,
    response: Response,
    hash: str | None = Query(None)
):
    target_role = request.target_role or request.targetRole or ...
    
    # Try Anthropic
    result_dict = anthropic_service.analyze_resume(
        text=resume_text,
        target_role=target_role
    )
    
    # Post-process: Force target_role as top domain
    if target_role and result_dict.get("domains"):
        # Map target_role to domain
        # Force to top with score 0.9
        # Update recommended_roles
```

### Job Search Request
```python
# Backend: backend/app/routes/linkedinJobs.py
@router.get("/search")
async def search_linkedin_jobs(
    role: str = Query(...),
    location: str = Query("US-Remote"),
    limit: int = Query(15)
):
    if not settings.rapidapi_key:
        # Fallback to free service
        jobs = free_job_service.search_jobs(role, location, limit)
    else:
        # Call RapidAPI
        response = httpx.get(rapidapi_url, headers=headers)
        jobs = map_rapidapi_response_to_job(response.json())
    
    return LinkedInJobSearchResponse(jobs=jobs, nextCursor=cursor)
```

### Frontend API Call
```typescript
// Frontend: frontend/src/lib/api.ts
export const analyzeResume = async (
  resumeText: string,
  targetRole?: string,
  preferredRoles?: string[],
  topKDomains?: number,
  signal?: AbortSignal
): Promise<AnalyzeResponse> => {
  const hash = await sha256(resumeText);
  const response = await fetch(`${url}?hash=${hash.substring(0, 8)}`, {
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
    signal,
  });
  return response.json();
};
```

---

## Testing

### Backend
```bash
cd backend
pytest tests/
```

### Frontend
```bash
cd frontend
npm test
```

---

## Future Enhancements

1. **Multi-Language Support**: Analyze resumes in multiple languages
2. **Resume Templates**: Generate resume templates based on role
3. **Interview Prep**: AI-powered interview question generation
4. **Salary Insights**: Salary range predictions based on skills/role
5. **Company Research**: Company culture and fit analysis
6. **Networking**: LinkedIn connection suggestions
7. **Portfolio Builder**: Portfolio website generator

---

## License

MIT License

---

## Contact

For questions or issues, please open an issue on GitHub.

