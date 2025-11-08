# CareerLens AI - Complete Guide

**This is your ONE guide for everything!** 📚

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [How to Run](#how-to-run)
3. [API Keys Setup](#api-keys-setup)
4. [How APIs Work](#how-apis-work)
5. [Code Explanation](#code-explanation)
6. [Features](#features)
7. [Troubleshooting](#troubleshooting)
8. [How to Debug API Issues](#how-to-debug-api-issues)

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- API keys (see [API Keys Setup](#api-keys-setup))

### Start Backend
```bash
cd backend
source venv/bin/activate
make dev
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### Access App
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 📖 How to Run

### Step 1: Environment Setup

**Create `.env` file in root directory:**
```bash
cp .env.example .env
```

**Add API keys to `.env`:**
```env
# Required for AI features
ANTHROPIC_API_KEY=sk-ant-...          # Get from https://console.anthropic.com/
OPENAI_API_KEY=sk-...                 # Get from https://platform.openai.com/api-keys

# Required for analytics
AMPLITUDE_API_KEY=...                 # Server-side key from https://amplitude.com/
VITE_AMPLITUDE_API_KEY=...            # Browser-side key from https://amplitude.com/

# Optional (for real jobs)
RAPIDAPI_KEY=...                      # Get from https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

# Firebase Authentication
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
VITE_FIREBASE_MEASUREMENT_ID=...
FIREBASE_SERVICE_ACCOUNT_PATH=backend/firebase-service-account.json

# Backend config
API_BASE_URL=http://localhost:8000
AWS_REGION=us-east-1
S3_BUCKET=careerlens-uploads
```

**Also create `frontend/.env` with same Firebase keys:**
```bash
cp .env frontend/.env
```

### Step 2: Install Dependencies

**Backend:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### Step 3: Start Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
make dev
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 4: Verify

**Test backend:**
```bash
curl http://localhost:8000/health
```

**Test frontend:**
- Open: `http://localhost:5173`
- Should see landing page

---

## 🔑 API Keys Setup

### 1. Anthropic API Key (Required for Resume Analysis)

**What it's used for:** Resume analysis using Claude AI

**How to get:**
1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)

**Where it's used:**
- `backend/app/services/anthropic_svc.py` - Claude AI service
- `backend/app/routes/analyze.py` - Resume analysis endpoint

**Add to `.env`:**
```env
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. OpenAI API Key (Required for Resume Tailoring)

**What it's used for:** Resume tailoring using GPT

**How to get:**
1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

**Where it's used:**
- `backend/app/services/openai_svc.py` - GPT service
- `backend/app/routes/tailor.py` - Resume tailoring endpoint

**Add to `.env`:**
```env
OPENAI_API_KEY=sk-...
```

### 3. Amplitude API Keys (Required for Analytics)

**What it's used for:** User analytics tracking

**How to get:**
1. Go to: https://amplitude.com/
2. Sign up or log in (Pro account)
3. Go to "Settings" → "Projects"
4. Select your project
5. Go to "General" tab
6. Copy "API Key" (server-side)
7. Go to "Data" → "Sources" → "Browser"
8. Copy "API Key" (browser-side)

**Where it's used:**
- `frontend/src/lib/analytics.ts` - Browser tracking
- `backend/app/services/amplitude.py` - Server tracking

**Add to `.env`:**
```env
AMPLITUDE_API_KEY=...              # Server-side
VITE_AMPLITUDE_API_KEY=...        # Browser-side
```

### 4. RapidAPI Key (Optional - for Real Jobs)

**What it's used for:** Real job data from JSearch API

**How to get:**
1. Go to: https://rapidapi.com/
2. Sign up or log in
3. Go to: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
4. Click "Subscribe to Test"
5. Copy "X-RapidAPI-Key" from code examples

**Where it's used:**
- `backend/app/services/dedalus_svc.py` - Job research service

**Add to `.env`:**
```env
RAPIDAPI_KEY=...
```

### 5. Firebase Authentication (Required for Login)

**What it's used for:** User authentication

**How to get:**
1. Go to: https://console.firebase.google.com/
2. Create a project
3. Enable Authentication → Email/Password
4. Get Web app config (Project Settings → Your apps)
5. Get Service Account key (Project Settings → Service Accounts)

**Where it's used:**
- `frontend/src/lib/firebase.ts` - Firebase initialization
- `frontend/src/contexts/AuthContext.tsx` - Auth context
- `backend/app/services/firebase_auth.py` - Token verification

**Add to `.env`:**
```env
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
VITE_FIREBASE_MEASUREMENT_ID=...
FIREBASE_SERVICE_ACCOUNT_PATH=backend/firebase-service-account.json
```

**Also save Service Account JSON as:**
```
backend/firebase-service-account.json
```

---

## 🔌 How APIs Work

### Architecture Overview

```
User → Frontend (React) → Backend API (FastAPI) → External Services
```

### API Flow

1. **User Action** → Frontend makes HTTP request
2. **Frontend** → Calls `frontend/src/lib/api.ts` functions
3. **API Layer** → Makes fetch request to backend
4. **Backend** → Processes request in `backend/app/routes/`
5. **Services** → Calls external APIs (Claude, GPT, etc.)
6. **Response** → Flows back to frontend
7. **Frontend** → Updates UI with results

### API Endpoints

#### 1. Resume Analysis (`POST /analyzeResume`)

**Frontend:** `frontend/src/lib/api.ts` → `analyzeResume()`
**Backend:** `backend/app/routes/analyze.py` → `/analyzeResume`
**Service:** `backend/app/services/anthropic_svc.py` → Claude AI

**Flow:**
1. User uploads resume text
2. Frontend calls `analyzeResume(text)`
3. Backend receives request
4. Backend calls Claude AI with resume text
5. Claude returns analysis (score, strengths, weaknesses, skills)
6. Backend validates with Pydantic schema
7. Backend returns `AnalyzeResponse`
8. Frontend stores in Zustand store
9. Frontend displays on Analysis page

**Code:**
- Frontend: `frontend/src/pages/Home.tsx` → `handleSubmit()`
- Frontend API: `frontend/src/lib/api.ts` → `analyzeResume()`
- Backend Route: `backend/app/routes/analyze.py` → `upload_resume()`
- Backend Service: `backend/app/services/anthropic_svc.py` → `analyze_resume()`

#### 2. Job Research (`POST /jobs/autoResearch`)

**Frontend:** `frontend/src/lib/api.ts` → `getJobs()`
**Backend:** `backend/app/routes/jobs.py` → `/jobs/autoResearch`
**Service:** `backend/app/services/dedalus_svc.py` → Job research

**Flow:**
1. User clicks "Auto-Research"
2. Frontend calls `getJobs(targetRole, resumeSummary)`
3. Backend receives request
4. Backend tries multiple sources:
   - Priority 1: Dedalus MCP (if available)
   - Priority 2: JSearch API (if RapidAPI key provided)
   - Priority 3: Fallback heuristics
5. Backend extracts skills, computes match scores
6. Backend generates why[] and fix[] arrays
7. Backend returns `Job[]`
8. Frontend stores in Zustand store
9. Frontend displays on Jobs page

**Code:**
- Frontend: `frontend/src/pages/Jobs.tsx` → `handleAutoResearch()`
- Frontend API: `frontend/src/lib/api.ts` → `getJobs()`
- Backend Route: `backend/app/routes/jobs.py` → `auto_research()`
- Backend Service: `backend/app/services/dedalus_svc.py` → `run_job_research()`

#### 3. Resume Tailoring (`POST /tailor`)

**Frontend:** `frontend/src/lib/api.ts` → `tailor()`
**Backend:** `backend/app/routes/tailor.py` → `/tailor`
**Service:** `backend/app/services/openai_svc.py` → GPT

**Flow:**
1. User clicks "Tailor with Dedalus" on a job
2. Frontend calls `tailor(resumeText, job.jdUrl)`
3. Backend receives request
4. Backend calls GPT with resume and job description
5. GPT returns tailored content (bullets, pitch, cover letter)
6. Backend validates with Pydantic schema
7. Backend returns `TailorResponse`
8. Frontend displays in TailorModal

**Code:**
- Frontend: `frontend/src/pages/Jobs.tsx` → `handleTailor()`
- Frontend API: `frontend/src/lib/api.ts` → `tailor()`
- Backend Route: `backend/app/routes/tailor.py` → `tailor_resume()`
- Backend Service: `backend/app/services/openai_svc.py` → `tailor_for_job()`

#### 4. Coaching Plan (`POST /autoCoach`)

**Frontend:** `frontend/src/lib/api.ts` → `autoCoach()`
**Backend:** `backend/app/routes/coach.py` → `/autoCoach`
**Service:** `backend/app/services/coach_svc.py` → Claude/OpenAI

**Flow:**
1. User clicks "Generate Plan"
2. Frontend calls `autoCoach(gaps, targetRole, reminders)`
3. Backend receives request
4. Backend calls Claude or OpenAI with skill gaps
5. AI generates 7-day coaching plan
6. Backend post-processes to ensure exactly 7 days
7. Backend adds real course links
8. Backend returns `CoachPlan`
9. Frontend displays on Coaching Plan page

**Code:**
- Frontend: `frontend/src/pages/Analysis.tsx` → `handleGeneratePlan()`
- Frontend API: `frontend/src/lib/api.ts` → `autoCoach()`
- Backend Route: `backend/app/routes/coach.py` → `auto_coach()`
- Backend Service: `backend/app/services/coach_svc.py` → `generate_coach_plan()`

#### 5. Score Prediction (`GET /predict`)

**Frontend:** `frontend/src/lib/api.ts` → `getPrediction()`
**Backend:** `backend/app/routes/predict.py` → `/predict`
**Service:** `backend/app/services/predict_svc.py` → Logistic formula

**Flow:**
1. User views Dashboard
2. Frontend calls `getPrediction(skillsHave, skillsGap)`
3. Backend receives request
4. Backend computes prediction using logistic formula
5. Backend returns `Prediction`
6. Frontend displays on Dashboard

**Code:**
- Frontend: `frontend/src/pages/Dashboard.tsx` → `useEffect()`
- Frontend API: `frontend/src/lib/api.ts` → `getPrediction()`
- Backend Route: `backend/app/routes/predict.py` → `get_prediction()`
- Backend Service: `backend/app/services/predict_svc.py` → `compute_prediction()`

#### 6. PDF Upload (`POST /upload/pdf`)

**Frontend:** `frontend/src/lib/api.ts` → `uploadPDF()`
**Backend:** `backend/app/routes/upload.py` → `/upload/pdf`
**Service:** `backend/app/services/pdf_parser.py` → PDF parsing

**Flow:**
1. User uploads PDF file
2. Frontend calls `uploadPDF(file)`
3. Backend receives file
4. Backend parses PDF using `pypdf`
5. Backend extracts text
6. Backend returns extracted text
7. Frontend displays text in textarea

**Code:**
- Frontend: `frontend/src/pages/Home.tsx` → `handleFileUpload()`
- Frontend API: `frontend/src/lib/api.ts` → `uploadPDF()`
- Backend Route: `backend/app/routes/upload.py` → `upload_pdf()`
- Backend Service: `backend/app/services/pdf_parser.py` → `parse_pdf()`

### Fallback Mechanism

**How it works:**
- If API call fails → Falls back to mock data
- Console shows warning: `⚠️ Using fallback mock data`
- User sees data but it's not real

**To use real APIs:**
1. Make sure backend is running
2. Add API keys to `.env`
3. Check browser console for errors
4. Look for `✅ API call succeeded` messages

---

## 💻 Code Explanation

### Frontend Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── api.ts              # API calls to backend
│   │   ├── analytics.ts         # Amplitude tracking
│   │   ├── firebase.ts          # Firebase initialization
│   │   └── utils.ts             # Utility functions
│   ├── store/
│   │   └── useAppStore.ts       # Zustand state management
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── ScoreDonut.tsx       # Score chart
│   │   ├── SkillChips.tsx       # Skills display
│   │   ├── JobCard.tsx           # Job card
│   │   ├── TailorModal.tsx       # Tailor modal
│   │   └── TopNav.tsx            # Navigation
│   ├── pages/
│   │   ├── Landing.tsx           # Landing page
│   │   ├── Login.tsx             # Login page
│   │   ├── Home.tsx              # Resume upload
│   │   ├── Analysis.tsx          # Analysis display
│   │   ├── Jobs.tsx              # Jobs list
│   │   ├── Dashboard.tsx         # Dashboard
│   │   ├── Settings.tsx          # Settings
│   │   └── CoachingPlan.tsx     # Coaching plan
│   ├── contexts/
│   │   └── AuthContext.tsx       # Authentication context
│   ├── types.ts                  # TypeScript types
│   └── App.tsx                   # Main app component
```

### Backend Structure

```
backend/
├── app/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Environment variables
│   ├── models/
│   │   └── schemas.py            # Pydantic models
│   ├── routes/
│   │   ├── analyze.py            # POST /analyzeResume
│   │   ├── jobs.py               # POST /jobs/autoResearch
│   │   ├── tailor.py             # POST /tailor
│   │   ├── coach.py              # POST /autoCoach
│   │   ├── predict.py            # GET /predict
│   │   └── upload.py             # POST /upload/pdf
│   └── services/
│       ├── anthropic_svc.py     # Claude AI service
│       ├── openai_svc.py         # GPT service
│       ├── dedalus_svc.py        # Job research service
│       ├── coach_svc.py           # Coaching plan service
│       ├── predict_svc.py         # Prediction service
│       ├── pdf_parser.py          # PDF parsing service
│       └── amplitude.py           # Analytics service
```

### Key Files Explained

#### `frontend/src/lib/api.ts`
- **Purpose:** API calls to backend
- **Functions:**
  - `analyzeResume()` - Calls `/analyzeResume`
  - `getJobs()` - Calls `/jobs/autoResearch`
  - `tailor()` - Calls `/tailor`
  - `autoCoach()` - Calls `/autoCoach`
  - `getPrediction()` - Calls `/predict`
  - `uploadPDF()` - Calls `/upload/pdf`
- **Fallback:** Uses `fetchWithFallback()` to fall back to mock data if API fails

#### `backend/app/services/anthropic_svc.py`
- **Purpose:** Resume analysis using Claude AI
- **Function:** `analyze_resume(text, target_role)`
- **Model:** `claude-3-haiku-20240307`
- **Retry Logic:** Up to 3 retries for JSON parsing errors
- **Validation:** Uses Pydantic schema validation

#### `backend/app/services/openai_svc.py`
- **Purpose:** Resume tailoring using GPT
- **Function:** `tailor_for_job(resume, jd, style)`
- **Model:** `gpt-4o` (falls back to `gpt-4o-mini`)
- **Retry Logic:** Up to 3 retries for validation errors
- **Output:** STAR-format bullets, elevator pitch, cover letter

#### `backend/app/services/dedalus_svc.py`
- **Purpose:** Job research with multi-source fallback
- **Function:** `run_job_research(target_role, resume_summary)`
- **Priority:**
  1. Dedalus MCP (if available)
  2. JSearch API (if RapidAPI key provided)
  3. Fallback heuristics
- **Features:**
  - Skill extraction
  - Match score calculation
  - Why[] and fix[] generation

#### `backend/app/services/coach_svc.py`
- **Purpose:** Generate 7-day coaching plans
- **Function:** `generate_coach_plan(gaps, target_role, reminders)`
- **AI:** Claude (preferred) or OpenAI
- **Post-processing:** Ensures exactly 7 days, adds real course links

#### `backend/app/services/predict_svc.py`
- **Purpose:** Score prediction using logistic formula
- **Function:** `compute_prediction(skills_have, skills_gap)`
- **Formula:** `sigmoid(a × have_count - b × gap_count) × 100`

---

## ✨ Features

### 1. Resume Analysis
- AI-powered analysis using Claude
- Career readiness score (0-100)
- Strengths and weaknesses
- Skill categorization
- Role recommendations

### 2. Job Research
- Real-time job search
- Match score calculation
- Personalized recommendations
- Why you fit & how to improve

### 3. Resume Tailoring
- STAR-format bullets
- Elevator pitch
- Cover letter generation

### 4. Coaching Plan
- 7-day personalized plan
- Real course links
- Daily reminders

### 5. Score Prediction
- Baseline score
- After-plan score
- Expected improvement

### 6. PDF Upload
- PDF text extraction
- Automatic parsing
- Text display

---

## 🐛 Troubleshooting

### Issue: "Load failed" or "Cannot connect to server"

**Problem:** Backend server is not running

**Solution:**
```bash
cd backend
source venv/bin/activate
make dev
```

### Issue: Using mock data instead of real data

**Problem:** Backend not running or API keys missing

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check API keys in `.env`
3. Check browser console for errors
4. Look for `✅ API call succeeded` messages

### Issue: "Firebase is not configured"

**Problem:** Firebase config missing in `.env`

**Solution:**
1. Add Firebase config to `.env` (see [API Keys Setup](#api-keys-setup))
2. Also add to `frontend/.env`
3. Restart frontend server

### Issue: PDF upload fails

**Problem:** Backend not running or `pypdf` not installed

**Solution:**
1. Start backend server
2. Install dependencies: `pip install pypdf python-multipart`

### Issue: Jobs show "Example Domain"

**Problem:** Using fallback mock data

**Solution:**
1. Start backend server
2. Add RapidAPI key to `.env` for real jobs
3. Check browser console for errors

### Issue: Analysis not updating

**Problem:** Backend not running or API call failing

**Solution:**
1. Check backend is running
2. Check browser console for errors
3. Verify API keys are set
4. Look for `✅ API call succeeded` in console

---

## 📝 Summary

**To use real APIs:**
1. ✅ Start backend server (`make dev`)
2. ✅ Add API keys to `.env`
3. ✅ Check browser console for `✅ API call succeeded`
4. ✅ If you see `⚠️ Using fallback mock data`, backend is not running

**Key Files:**
- API calls: `frontend/src/lib/api.ts`
- Backend routes: `backend/app/routes/`
- Backend services: `backend/app/services/`

**Check if APIs are working:**
- Browser console: Look for `✅ API call succeeded`
- Backend terminal: Look for request logs
- Network tab: Check API requests in DevTools

