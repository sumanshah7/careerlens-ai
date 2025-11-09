# Testing & Running Guide

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+** and npm
- **Python 3.11+**
- **API Keys** (optional but recommended):
  - `OPENAI_API_KEY` - Required for tailor functionality
  - `ANTHROPIC_API_KEY` - Required for resume analysis
  - `AMPLITUDE_API_KEY` - For analytics (optional)

### Step 1: Setup Environment Variables

Create a `.env` file in the **root directory** (`/Users/sumansah/Desktop/careerlens/.env`):

```bash
# Required for AI features
OPENAI_API_KEY=sk-...                    # Get from https://platform.openai.com/api-keys
ANTHROPIC_API_KEY=sk-ant-...             # Get from https://console.anthropic.com/

# Required for analytics
AMPLITUDE_API_KEY=...                    # Server-side key
VITE_AMPLITUDE_API_KEY=...               # Browser-side key

# Optional (for real jobs)
RAPIDAPI_KEY=...                         # Get from https://rapidapi.com/
DEDALUS_API_KEY=...                      # Get from https://dedaluslabs.net/

# Backend config
API_BASE_URL=http://localhost:8000
```

### Step 2: Start Backend

**Open Terminal 1:**

```bash
cd /Users/sumansah/Desktop/careerlens/backend

# Activate virtual environment (if not already activated)
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start backend server
make dev
# OR
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Backend will be available at:**
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

**Keep this terminal running!**

### Step 3: Start Frontend

**Open Terminal 2** (new terminal window):

```bash
cd /Users/sumansah/Desktop/careerlens/frontend

# Install dependencies (first time only)
npm install

# Start frontend server
npm run dev
```

**Expected output:**
```
VITE v5.0.8  ready in 500 ms

➜  Local:   http://localhost:5173/
```

**Frontend will be available at:**
- App: `http://localhost:5173`

**Keep this terminal running!**

### Step 4: Open Application

1. Open browser: `http://localhost:5173`
2. You should see the CareerLens landing page

---

## 🧪 Testing the Tailor Functionality

### Test 1: Evidence-Based Output

**Goal:** Verify outputs include role/company and resume evidence

1. **Upload a resume with concrete tools/metrics:**
   - Example resume text:
     ```
     Software Engineer at Tech Corp
     - Developed FastAPI service handling 2M requests/day
     - Reduced latency by 38% using Kubernetes
     - Built PostgreSQL database serving 1M+ users
     - Implemented Python data pipeline processing 500GB daily
     ```

2. **Select a job** (e.g., "Software Engineer" at "Google")

3. **Click "Tailor Resume"** button on the job card

4. **Verify:**
   - ✅ Modal opens with job title and company name in header
   - ✅ Bullets include tools/metrics from resume (e.g., "FastAPI", "38%", "Kubernetes", "2M requests/day")
   - ✅ "Grounded in your resume" indicator appears
   - ✅ Hover over indicator shows evidence tokens (e.g., "FastAPI", "reduced latency 38%", "Kubernetes")

### Test 2: Generic Content Detection & Repair

**Goal:** Verify validator catches clichés and performs repair

1. **Upload a generic resume** (minimal specific details):
   ```
   Software Engineer
   - Worked on various projects
   - Collaborated with team members
   - Improved system performance
   ```

2. **Select a job** and click "Tailor Resume"

3. **Verify:**
   - ✅ If clichés detected (e.g., "passionate", "results-driven"), repair pass runs automatically
   - ✅ If repair succeeds: Output is cleaner, no clichés
   - ✅ If repair fails: Evidence-only draft is returned with "Evidence-only draft—no claims beyond your resume" label
   - ✅ Warning ribbon appears if validation warnings exist: "We tightened phrasing to remove generic language"

### Test 3: API Failure Fallback

**Goal:** Verify fallback to evidence-only draft when API fails

**Option A: Temporarily disable API key**
1. In `.env`, comment out or remove `OPENAI_API_KEY`
2. Restart backend: `Ctrl+C` then `make dev`
3. Upload resume and select job
4. Click "Tailor Resume"

**Option B: Simulate network failure**
1. Stop backend: `Ctrl+C` in Terminal 1
2. Upload resume and select job
3. Click "Tailor Resume"
4. Should show error, then restart backend

**Verify:**
- ✅ Evidence-only draft is returned
- ✅ "Evidence-only draft—no claims beyond your resume" label appears
- ✅ Bullets are simple and evidence-based (e.g., "Built FastAPI service", "Reduced latency 38%")

### Test 4: Regenerate with Metrics

**Goal:** Verify "Regenerate with more metrics" button works

1. **Upload resume** with metrics (e.g., "reduced latency 38%", "2M requests/day")
2. **Select job** and click "Tailor Resume"
3. **Click "Regenerate with more metrics"** button
4. **Verify:**
   - ✅ Button shows loading spinner while regenerating
   - ✅ New bullets include more quantifiable outcomes (percentages, numbers, dollar amounts)
   - ✅ Modal updates with new content
   - ✅ Success toast appears: "Regenerated with emphasis on metrics"

### Test 5: Evidence Tooltip

**Goal:** Verify hover tooltip shows evidence tokens

1. **Upload resume** with specific tools/metrics
2. **Select job** and click "Tailor Resume"
3. **Hover over "Grounded in your resume"** indicator
4. **Verify:**
   - ✅ Tooltip appears showing 2-3 evidence tokens
   - ✅ Examples: "FastAPI", "reduced latency 38%", "Kubernetes"
   - ✅ Tokens match what's in the resume

### Test 6: Length Limits & Verb Diversity

**Goal:** Verify bullets respect word limits and start with different verbs

1. **Upload resume** and select job
2. **Click "Tailor Resume"**
3. **Verify:**
   - ✅ Each bullet ≤28 words (count manually or check visually)
   - ✅ Pitch is 45-60 words
   - ✅ Cover letter is 120-180 words
   - ✅ Bullets start with different verbs (e.g., "Developed", "Reduced", "Built", "Implemented" - not all "Led" or "Developed")

---

## 🔍 Manual Testing Checklist

### Backend API Testing

**Test via API Docs (Easier):**
1. Open: `http://localhost:8000/docs`
2. Find `POST /api/tailor` endpoint
3. Click "Try it out"
4. Fill in request body:
   ```json
   {
     "resume_text": "Software Engineer with 3 years experience. Built FastAPI service handling 2M requests/day. Reduced latency by 38% using Kubernetes.",
     "job_title": "Senior Software Engineer",
     "company": "Google",
     "job_description": "We are looking for a Senior Software Engineer with experience in Python, FastAPI, and Kubernetes. Must have experience with high-scale systems.",
     "emphasize_metrics": false
   }
   ```
5. Click "Execute"
6. **Verify response:**
   - ✅ `bullets` array has 4-6 items
   - ✅ `pitch` mentions "Senior Software Engineer" and "Google"
   - ✅ `coverLetter` mentions role and company
   - ✅ `evidenceUsed` array has 3-5 tokens
   - ✅ `isEvidenceOnly` is `false`
   - ✅ `validationWarnings` is empty array (or has warnings if clichés were removed)

**Test via curl (Terminal):**
```bash
curl -X POST "http://localhost:8000/api/tailor" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Software Engineer. Built FastAPI service. Reduced latency 38%.",
    "job_title": "Senior Software Engineer",
    "company": "Google",
    "job_description": "Looking for Senior Software Engineer with Python and FastAPI experience.",
    "emphasize_metrics": false
  }'
```

### Frontend UI Testing

**Test Tailor Modal:**
1. Navigate to Jobs page: `http://localhost:5173/jobs`
2. Search for jobs (or use existing results)
3. Click "Tailor Resume" on any job card
4. **Verify:**
   - ✅ Modal opens smoothly
   - ✅ Title shows: "Tailored for [Job Title] at [Company]"
   - ✅ Description shows role and company
   - ✅ "Grounded in your resume" indicator appears (if evidence used)
   - ✅ "Regenerate with more metrics" button appears
   - ✅ Bullets section shows 4-6 items
   - ✅ Pitch section shows 45-60 words
   - ✅ Cover letter section shows 120-180 words
   - ✅ Copy buttons work (test by clicking)

**Test Regenerate Button:**
1. Open Tailor Modal
2. Click "Regenerate with more metrics"
3. **Verify:**
   - ✅ Button shows loading spinner
   - ✅ Modal updates with new content
   - ✅ New bullets have more metrics/numbers
   - ✅ Success toast appears

**Test Evidence Tooltip:**
1. Open Tailor Modal
2. Hover over "Grounded in your resume" indicator
3. **Verify:**
   - ✅ Tooltip appears
   - ✅ Shows 2-3 evidence tokens
   - ✅ Tokens match resume content

**Test Warning Ribbons:**
1. Upload generic resume (with clichés)
2. Tailor for a job
3. **Verify:**
   - ✅ If clichés detected: Warning ribbon appears: "We tightened phrasing to remove generic language"
   - ✅ If API fails: Warning ribbon appears: "Evidence-only draft—no claims beyond your resume"

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error:** `Port 8000 already in use`

**Solution:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or change port in Makefile
```

**Error:** `ImportError: No module named '...'`

**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Error:** `OPENAI_API_KEY is not set`

**Solution:**
1. Check `.env` file exists in root directory
2. Verify `OPENAI_API_KEY=sk-...` is set (no quotes, no spaces)
3. Restart backend after adding key

### Frontend Won't Start

**Error:** `Port 5173 already in use`

**Solution:**
- Vite will automatically use next available port
- Check terminal output for actual port

**Error:** `npm: command not found`

**Solution:**
- Install Node.js 18+ from https://nodejs.org/
- Or use `yarn` or `pnpm` if installed

**Error:** Build fails or dependencies missing

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Tailor Not Working

**Error:** "Failed to tailor resume"

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check `OPENAI_API_KEY` in `.env` file
3. Check backend terminal logs for errors
4. Verify resume text and job description are provided

**Error:** Getting evidence-only draft when API key is set

**Solution:**
1. Check API key is valid: Test at https://platform.openai.com/
2. Check backend logs for API errors
3. Verify API key has credits/quota available

**Error:** Modal shows "Evidence-only draft" label

**Solution:**
- This is expected if validation fails or API fails
- Check backend logs for validation errors
- Try with a more detailed resume

---

## 📊 Expected Behavior

### Successful Tailor Response

**Response structure:**
```json
{
  "bullets": [
    "Developed FastAPI service on Kubernetes handling 2M requests/day, reducing latency by 38% through async I/O and connection pooling",
    "Built PostgreSQL database serving 1M+ users with optimized queries and indexing",
    "Implemented Python data pipeline processing 500GB daily with Spark and Airflow",
    "Scaled microservices architecture using Docker and Kubernetes, improving system reliability"
  ],
  "pitch": "I'm a Software Engineer with experience building high-scale systems. My expertise in FastAPI, Kubernetes, and PostgreSQL, combined with a track record of reducing latency by 38%, makes me an ideal fit for the Senior Software Engineer role at Google.",
  "coverLetter": "I am excited to apply for the Senior Software Engineer position at Google. My experience developing FastAPI services handling 2M requests/day and reducing latency by 38% using Kubernetes aligns with your requirements for high-scale systems.\n\nI have built PostgreSQL databases serving 1M+ users and implemented Python data pipelines processing 500GB daily. I am interested in working with Python, FastAPI, and Kubernetes at Google.",
  "evidenceUsed": ["FastAPI", "reduced latency 38%", "Kubernetes", "2M requests/day", "PostgreSQL"],
  "isEvidenceOnly": false,
  "validationWarnings": []
}
```

### Evidence-Only Draft Response

**Response structure:**
```json
{
  "bullets": [
    "Built FastAPI service",
    "Reduced latency 38%",
    "Scaled Kubernetes deployment",
    "Implemented PostgreSQL database"
  ],
  "pitch": "Applying for Senior Software Engineer at Google. Experience with FastAPI, Kubernetes.",
  "coverLetter": "I am applying for the Senior Software Engineer position at Google. My experience includes FastAPI, Kubernetes. I am interested in working with Python and related technologies.",
  "evidenceUsed": ["FastAPI", "reduced latency 38%", "Kubernetes"],
  "isEvidenceOnly": true,
  "validationWarnings": []
}
```

---

## ✅ Success Criteria

All tests should pass:

1. ✅ **Evidence-Based Output**: Outputs include role/company and resume evidence
2. ✅ **Generic Content Detection**: Validator catches clichés and performs repair
3. ✅ **API Failure Fallback**: Evidence-only draft returned when API fails
4. ✅ **Regenerate with Metrics**: Button works and emphasizes quantifiable outcomes
5. ✅ **Evidence Tooltip**: Hover shows 2-3 evidence tokens
6. ✅ **Length Limits**: Bullets ≤28 words, pitch 45-60, cover letter 120-180
7. ✅ **Verb Diversity**: Bullets start with different verbs
8. ✅ **No Crashes**: Application handles malformed input gracefully
9. ✅ **User-Friendly Errors**: Errors are clear and actionable
10. ✅ **No PII Logged**: No personal information in logs or analytics

---

## 🎯 Next Steps

After testing:

1. **If all tests pass:** You're ready to use the application!
2. **If tests fail:** Check troubleshooting section above
3. **For production:** Set up proper environment variables and deploy

---

**Happy Testing! 🚀**

