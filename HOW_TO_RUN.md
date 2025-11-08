# How to Run CareerLens AI

## 📋 Prerequisites

- **Node.js 18+** and npm/yarn/pnpm
- **Python 3.11+**
- **pip** or poetry

## 🔑 Step 1: Setup Environment

### Create `.env` File

```bash
cd /Users/sumansah/Desktop/careerlens
cp .env.example .env
```

### Add API Keys to `.env`

Open `.env` file and add your keys:

```env
# REQUIRED for AI features
ANTHROPIC_API_KEY=sk-ant-...          # Get from https://console.anthropic.com/
OPENAI_API_KEY=sk-...                 # Get from https://platform.openai.com/api-keys

# REQUIRED for analytics
AMPLITUDE_API_KEY=...                 # Server-side key from https://amplitude.com/
VITE_AMPLITUDE_API_KEY=...            # Browser-side key from https://amplitude.com/

# OPTIONAL (for real jobs)
RAPIDAPI_KEY=...                      # Get from https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
DEDALUS_API_KEY=...                   # Get from https://dedaluslabs.net/

# Backend config (defaults are fine)
API_BASE_URL=http://localhost:8000
AWS_REGION=us-east-1
S3_BUCKET=careerlens-uploads
```

**Note:** App works in fallback mode without API keys (uses mock data).

## 🚀 Step 2: Start Backend

### Terminal 1: Backend

```bash
cd /Users/sumansah/Desktop/careerlens/backend

# Create virtual environment (first time only)
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

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

## 🎨 Step 3: Start Frontend

### Terminal 2: Frontend (NEW terminal window)

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

## ✅ Step 4: Verify Everything Works

### Test Backend

**Option 1: Use Browser (Easier)**
1. Open: `http://localhost:8000/docs`
2. Click any endpoint → "Try it out" → Fill form → "Execute"
3. See response formatted nicely

**Option 2: Use curl (Terminal)**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

### Test Frontend

1. **Open browser:** `http://localhost:5173`
2. **Test Home page:**
   - Paste resume text (e.g., "Software engineer with 5 years React experience")
   - Click "Analyze Resume"
   - Should navigate to `/analysis` page

3. **Test Analysis page:**
   - Should show score donut chart
   - Should show skills, strengths, weaknesses
   - Click "Generate Plan" → Should create 7-day plan

4. **Test Jobs page:**
   - Click "Auto-Research (Dedalus)"
   - Should show job cards with match scores
   - Click "Tailor with Dedalus" → Should open modal

5. **Test Dashboard:**
   - Should show score over time chart
   - Should show prediction tile

6. **Test Coaching Plan:**
   - Navigate to "Coaching Plan" in top nav
   - Should show 7-day plan with course links

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

**Error:** `python3.11: command not found`

**Solution:**
- Install Python 3.11+
- Or use `python3` if 3.11+ is installed

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

### API Calls Failing

**Error:** `Connection refused` or `Failed to connect`

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check API keys in `.env` file
3. Restart backend: `cd backend && make dev`

**Error:** Getting mock data instead of real data

**Solution:**
1. Check `.env` file exists in root directory
2. Verify API keys are correct (no extra spaces)
3. Restart backend after adding keys
4. Check backend logs for errors

### No Real Data (Only Mock Data)

**Problem:** API keys not set or incorrect

**Solution:**
1. Check `.env` file exists: `cat .env`
2. Verify API keys: `cat .env | grep API_KEY`
3. Restart backend: `cd backend && make dev`
4. Check backend logs for: `[Anthropic] API call failed, using fallback`

## 📊 Verification Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can access `http://localhost:8000/docs` (API docs)
- [ ] Can access `http://localhost:5173` (Frontend)
- [ ] Can upload resume and get analysis
- [ ] Can generate coaching plan
- [ ] Can research jobs
- [ ] Can tailor resume
- [ ] No errors in browser console
- [ ] No errors in backend terminal

## 🎯 Quick Reference

**Start Backend:**
```bash
cd backend && make dev
```

**Start Frontend:**
```bash
cd frontend && npm run dev
```

**Test API:**
```bash
curl http://localhost:8000/health
```

**View API Docs:**
```
http://localhost:8000/docs
```

**View Frontend:**
```
http://localhost:5173
```

## 📝 Notes

- **Backend must be running** before frontend can make API calls
- **Use two terminal windows** - one for backend, one for frontend
- **Keep both running** while testing
- **API keys are optional** - app works with mock data if keys not provided
- **Check logs** in both terminals for errors

