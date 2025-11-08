# API Usage Summary: Amplitude, Anthropic, and OpenAI

## 📊 Amplitude Analytics

### **Purpose**
User behavior and event tracking for analytics

### **Where It's Used**

#### **Frontend (Client-Side)**
- **File:** `frontend/src/lib/analytics.ts`
- **Package:** `@amplitude/analytics-browser`
- **Initialization:** On app load with `VITE_AMPLITUDE_API_KEY`
- **Events Tracked:**
  - `resume_uploaded` - When user uploads resume (hash, filename, size)
  - `analysis_completed` - When analysis is displayed (hash, provider, strengths_count, roles_count)
  - `jobs_fetched` - When jobs are retrieved (hash, count, source)
  - `coach_plan_generated` - When coaching plan is created (score, gapCount, targetRole, domain, reminders)
  - `coach_plan_failed` - When coaching plan generation fails
  - `get_jobs_success` - When jobs API call succeeds
  - `get_prediction_success` - When prediction API call succeeds

#### **Backend (Server-Side)**
- **File:** `backend/app/services/amplitude.py`
- **API Endpoint:** `https://api2.amplitude.com/2/httpapi`
- **Environment Variable:** `AMPLITUDE_API_KEY`
- **Events Tracked:**
  - `analysis_completed_server` - When resume analysis completes (hash, provider, strengths_count, roles_count)
  - `jobs_fetched_server` - When job research completes (hash, source, count)
  - `coach_plan_generated` - When coaching plan is generated (gap_count, has_target_role, reminders, plan_days)
  - `tailor_completed` - When resume tailoring completes (bullets_count, style)

### **Key Features**
- ✅ **Privacy-Safe:** Only tracks hashes, counts, and metadata - **NEVER raw resume text**
- ✅ **Dual Tracking:** Both client-side and server-side events
- ✅ **Graceful Degradation:** Works even if API key is missing (silently fails)

---

## 🤖 Anthropic Claude AI

### **Purpose**
Resume analysis using Claude AI

### **Where It's Used**

#### **Backend Service**
- **File:** `backend/app/services/anthropic_svc.py`
- **Package:** `anthropic==0.18.1`
- **Model:** `claude-3-haiku-20240307`
- **Environment Variable:** `ANTHROPIC_API_KEY`

#### **Primary Use Case: Resume Analysis**
- **Route:** `POST /analyzeResume` → `backend/app/routes/analyze.py`
- **Function:** `anthropic_service.analyze_resume(text, target_role)`
- **What It Does:**
  1. Analyzes resume text
  2. Classifies domain (Frontend, Backend, ML/AI, etc.)
  3. Extracts skills, strengths, weaknesses
  4. Suggests recommended roles
  5. Returns structured JSON response

#### **Secondary Use Case: Coaching Plans**
- **File:** `backend/app/services/coach_svc.py`
- **Function:** `_generate_with_anthropic(gaps, target_role, domain)`
- **Model:** `claude-3-haiku-20240307`
- **What It Does:**
  1. Generates 7-day personalized coaching plans
  2. Creates domain-specific learning activities
  3. Includes real course URLs and resources

### **Fallback Chain**
1. **Try Anthropic first** (if `ANTHROPIC_API_KEY` is set)
2. **Try OpenAI** (if Anthropic fails and `OPENAI_API_KEY` is set)
3. **Use keyword-based fallback** (if both LLMs fail or unavailable)

### **Key Features**
- ✅ **Structured Output:** Uses JSON schema validation
- ✅ **Retry Logic:** Up to 3 retries for JSON parsing errors
- ✅ **Temperature:** `0.0` for deterministic domain classification
- ✅ **Domain Classification:** Automatically detects ML/AI, Frontend, Backend, etc.

---

## 🧠 OpenAI GPT

### **Purpose**
Resume tailoring and coaching plan generation (fallback)

### **Where It's Used**

#### **Backend Service**
- **File:** `backend/app/services/openai_svc.py`
- **Package:** `openai==1.12.0`
- **Primary Model:** `gpt-4o`
- **Fallback Model:** `gpt-4o-mini`
- **Environment Variable:** `OPENAI_API_KEY`

#### **Primary Use Case: Resume Tailoring**
- **Route:** `POST /tailor` → `backend/app/routes/tailor.py`
- **Function:** `openai_service.tailor_for_job(resume, jd, style="STAR")`
- **What It Does:**
  1. Tailors resume bullets to job description
  2. Creates STAR-format bullets (Situation, Task, Action, Result)
  3. Generates 50-word elevator pitch
  4. Writes 120-180 word cover letter

#### **Secondary Use Case: Coaching Plans (Fallback)**
- **File:** `backend/app/services/coach_svc.py`
- **Function:** `_generate_with_openai(gaps, target_role, domain)`
- **Model:** `gpt-4o-mini`
- **What It Does:**
  1. Generates 7-day coaching plans (if Anthropic unavailable)
  2. Creates domain-specific learning activities
  3. Includes real course URLs

#### **Tertiary Use Case: Resume Analysis (Planned)**
- **File:** `backend/app/routes/analyze.py`
- **Status:** ⚠️ **Currently a placeholder** - falls back to keyword-based analysis
- **Future:** Will use OpenAI for resume analysis if Anthropic fails

### **Fallback Chain**
1. **Try Dedalus MCP** (if available)
2. **Try Dedalus API** (if MCP unavailable)
3. **Use OpenAI** (if Dedalus unavailable)
4. **Use keyword-based fallback** (if OpenAI fails)

### **Key Features**
- ✅ **Model Fallback:** Automatically falls back to `gpt-4o-mini` if `gpt-4o` unavailable
- ✅ **JSON Mode:** Uses `response_format={"type": "json_object"}` for structured output
- ✅ **Retry Logic:** Up to 3 retries for validation errors
- ✅ **Temperature:** `0.7` for creative but consistent output

---

## 📋 Summary Table

| Service | Primary Use | Secondary Use | Fallback Position |
|---------|------------|---------------|-------------------|
| **Amplitude** | Analytics tracking | - | Always available (graceful degradation) |
| **Anthropic** | Resume analysis | Coaching plans | First choice for analysis |
| **OpenAI** | Resume tailoring | Coaching plans (fallback) | Second choice for analysis, primary for tailoring |

---

## 🔑 Environment Variables Required

```env
# Amplitude (Analytics)
AMPLITUDE_API_KEY=your_server_key          # Backend
VITE_AMPLITUDE_API_KEY=your_browser_key    # Frontend

# Anthropic (Resume Analysis)
ANTHROPIC_API_KEY=sk-ant-...               # Get from https://console.anthropic.com/

# OpenAI (Resume Tailoring)
OPENAI_API_KEY=sk-...                      # Get from https://platform.openai.com/
```

---

## 🔄 API Call Flow

### **Resume Analysis Flow**
```
1. User uploads resume
2. Frontend → POST /analyzeResume
3. Backend tries:
   a. Anthropic Claude (if ANTHROPIC_API_KEY set)
   b. OpenAI GPT (if Anthropic fails and OPENAI_API_KEY set) ⚠️ Not implemented yet
   c. Keyword-based fallback (if both fail)
4. Backend → Amplitude: analysis_completed_server
5. Frontend → Amplitude: analysis_completed
6. Return analysis to user
```

### **Resume Tailoring Flow**
```
1. User clicks "Tailor" on a job
2. Frontend → POST /tailor
3. Backend tries:
   a. Dedalus MCP (if available)
   b. Dedalus API (if MCP unavailable)
   c. OpenAI GPT (if Dedalus unavailable)
4. Backend → Amplitude: tailor_completed
5. Return tailored content to user
```

### **Coaching Plan Flow**
```
1. User clicks "Generate Plan"
2. Frontend → POST /autoCoach
3. Backend tries:
   a. Anthropic Claude (if ANTHROPIC_API_KEY set)
   b. OpenAI GPT (if Anthropic unavailable and OPENAI_API_KEY set)
   c. Fallback mock data (if both fail)
4. Backend → Amplitude: coach_plan_generated
5. Frontend → Amplitude: coach_plan_generated
6. Return plan to user
```

---

## 🛡️ Privacy & Security

### **Amplitude**
- ✅ **Never sends raw resume text**
- ✅ Only tracks: hashes (first 8 chars), counts, provider names, metadata
- ✅ Both client and server-side tracking for complete analytics

### **Anthropic & OpenAI**
- ✅ **Sends full resume text** (required for analysis)
- ✅ API keys stored in environment variables (never in code)
- ✅ All API calls are server-side (keys never exposed to frontend)

---

## 📝 Notes

1. **OpenAI for Analysis:** Currently a placeholder in `analyze.py` - will be implemented in the future
2. **Fallback Behavior:** All services gracefully degrade if API keys are missing
3. **Model Selection:** Anthropic uses `claude-3-haiku` (faster, cheaper), OpenAI uses `gpt-4o` (more capable)
4. **Temperature Settings:** Anthropic uses `0.0` (deterministic), OpenAI uses `0.7` (creative)

