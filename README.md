# CareerLens AI

AI-powered career development platform with resume analysis, job matching, and personalized learning plans.

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.11+**
- **pip** (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/sumanshah7/careerlens-ai.git
cd careerlens-ai
```

### Step 2: Setup Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy template (if exists)
cp .env.example .env

# Or create manually
touch .env
```

Add your API keys to `.env`:

```env
# REQUIRED for AI features
ANTHROPIC_API_KEY=sk-ant-...          # Get from https://console.anthropic.com/
OPENAI_API_KEY=sk-...                 # Get from https://platform.openai.com/api-keys

# REQUIRED for analytics
AMPLITUDE_API_KEY=...                 # Server-side key from https://amplitude.com/
VITE_AMPLITUDE_API_KEY=...            # Browser-side key from https://amplitude.com/

# OPTIONAL (for real jobs)
RAPIDAPI_KEY=...                      # Get from https://rapidapi.com/
DEDALUS_API_KEY=...                   # Get from https://dedaluslabs.net/

# Backend config (defaults are fine)
API_BASE_URL=http://localhost:8000
```

**Note:** The app works in fallback mode without API keys (uses mock data).

### Step 3: Start Backend

Open **Terminal 1**:

```bash
cd backend

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

### Step 4: Start Frontend

Open **Terminal 2** (new terminal window):

```bash
cd frontend

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

## ✅ Verify Everything Works

### Test Backend

**Option 1: Use Browser (Easier)**
1. Open: `http://localhost:8000/docs`
2. Click any endpoint → "Try it out" → Fill form → "Execute"
3. See response formatted nicely

**Option 2: Use curl (Terminal)**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Test Frontend

1. **Open browser:** `http://localhost:5173`
2. **Test Home page:**
   - Paste resume text or upload a PDF
   - Click "Analyze Resume"
   - Should navigate to `/analysis` page

3. **Test Analysis page:**
   - Should show overall score
   - Should show domains, skills, strengths, areas for growth
   - Should show recommended roles

4. **Test Jobs page:**
   - Click "Find Matching Jobs"
   - Should show job cards with match scores
   - Click "View Job Posting" → Should open job URL
   - Click "Tailor Resume" → Should open modal

5. **Test Progress page:**
   - Should show score over time chart
   - Should show improvement metrics

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
- Install Python 3.11+ or use `python3` if 3.11+ is installed

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

## 📁 Project Structure

```
careerlens-ai/
├── frontend/              # React + Vite + TypeScript
│   ├── src/
│   │   ├── lib/           # API calls, utilities
│   │   ├── store/        # Zustand state management
│   │   ├── components/   # React components
│   │   └── pages/        # Route pages
│   └── package.json
├── backend/               # FastAPI + Python 3.11
│   ├── app/
│   │   ├── main.py       # FastAPI app entry point
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # Business logic
│   │   └── models/       # Pydantic schemas
│   └── requirements.txt
└── README.md              # This file
```

## 🎯 Key Features

- **Resume Analysis**: AI-powered analysis with multi-domain classification
- **Job Matching**: Skill-based job matching with match scores
- **Personalized Plans**: 7-day learning plans tailored to your gaps
- **Resume Tailoring**: AI-generated resume bullets and cover letters
- **Progress Tracking**: Track your career development over time
- **Dark Mode**: Toggle between light and dark themes

## 🔧 Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Zustand (state management)
- React Router
- Amplitude Analytics

**Backend:**
- FastAPI
- Python 3.11
- Anthropic Claude (resume analysis)
- OpenAI GPT (resume tailoring)
- Pydantic (validation)
- httpx (HTTP client)

## 📝 API Endpoints

- `POST /api/analyze-resume` - Analyze resume and get insights
- `POST /api/jobs/search` - Search for jobs matching your skills
- `POST /api/generate-plan` - Generate personalized learning plan
- `POST /api/tailor` - Tailor resume for specific job
- `GET /api/predict-score` - Predict resume score
- `GET /health` - Health check

Full API documentation: `http://localhost:8000/docs`

## 🧪 Testing

**Backend tests:**
```bash
cd backend
source venv/bin/activate
pytest
```

**Frontend tests:**
```bash
cd frontend
npm test
```

**Manual Testing Guide:**
See [TESTING_GUIDE.md](./TESTING_GUIDE.md) for comprehensive testing instructions, including:
- Step-by-step setup
- Tailor functionality testing (6 test cases)
- Troubleshooting guide
- Expected behavior examples

## 📄 License

This project is private and proprietary.

## 🤝 Contributing

This is a private repository. For questions or issues, please contact the repository owner.

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API documentation at `http://localhost:8000/docs`
3. Check backend/frontend terminal logs for errors

---

**Made with ❤️ for career development**
