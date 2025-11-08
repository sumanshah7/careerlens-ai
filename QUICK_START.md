# 🚀 Quick Start Guide

## Prerequisites

- **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
- **Python 3.11** - [Download](https://www.python.org/downloads/)
- **npm** or **yarn** (comes with Node.js)

## Step 1: Set Up Environment Variables

1. Create a `.env` file in the root directory:
   ```bash
   cd /Users/sumansah/Desktop/careerlens
   touch .env
   ```

2. Add your API keys to `.env`:
   ```env
   # Required for AI features
   ANTHROPIC_API_KEY=your_anthropic_key_here
   OPENAI_API_KEY=your_openai_key_here
   
   # Optional - for analytics
   AMPLITUDE_API_KEY=your_amplitude_server_key
   VITE_AMPLITUDE_API_KEY=your_amplitude_browser_key
   
   # Optional - for real job data
   RAPIDAPI_KEY=your_rapidapi_key_here
   
   # Firebase (if using authentication)
   VITE_FIREBASE_API_KEY=your_firebase_api_key
   VITE_FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
   VITE_FIREBASE_PROJECT_ID=your_firebase_project_id
   VITE_FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
   VITE_FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
   VITE_FIREBASE_APP_ID=your_firebase_app_id
   VITE_FIREBASE_MEASUREMENT_ID=your_firebase_measurement_id
   ```

   **Note:** The app works in fallback mode without API keys (uses mock data), but for real AI analysis, you need at least `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`.

## Step 2: Start Backend Server

Open a terminal and run:

```bash
cd /Users/sumansah/Desktop/careerlens/backend

# Create virtual environment (first time only)
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
make dev
# OR: uvicorn app.main:app --reload --port 8000
```

✅ Backend should be running at: `http://localhost:8000`  
📚 API docs at: `http://localhost:8000/docs`

## Step 3: Start Frontend Server

Open a **new terminal** and run:

```bash
cd /Users/sumansah/Desktop/careerlens/frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

✅ Frontend should be running at: `http://localhost:5173` (or 5174, 5175 if 5173 is busy)

## Step 4: Use the Application

1. **Open your browser** and go to: `http://localhost:5173`
2. **Sign up / Sign in** using Firebase authentication
3. **Upload a resume:**
   - Go to Home page
   - Enter a target role (e.g., "Software Engineer")
   - Paste or upload your resume (PDF or text)
   - Click "Analyze Resume"
4. **View analysis** - See your career readiness score, strengths, weaknesses, and skills
5. **Find jobs** - Click "Find Matching Jobs" to discover opportunities
6. **Track progress** - Go to Progress page to see your resume improvements over time
7. **Generate coaching plan** - Get a 7-day personalized learning plan

## 🎯 Quick Test

To verify everything is working:

```bash
# In a new terminal, test backend health
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

## 📝 Running Both Servers

You need **two terminals** running simultaneously:

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate
make dev
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

## 🔧 Troubleshooting

### Backend not starting?
- Check if Python 3.11 is installed: `python3.11 --version`
- Check if port 8000 is available: `lsof -i :8000`
- Check if virtual environment is activated

### Frontend not starting?
- Check if Node.js is installed: `node --version`
- Check if dependencies are installed: `cd frontend && npm install`
- Check if port 5173 is available

### API calls failing?
- Make sure backend is running on port 8000
- Check browser console for CORS errors
- Verify API keys are set in `.env` file

### "Cannot connect to server"?
- Make sure backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `backend/app/main.py`
- Restart both servers

## 📚 More Information

- **Complete Guide:** See `COMPLETE_GUIDE.md`
- **How to Run:** See `HOW_TO_RUN.md`
- **Code Explanation:** See `CODE_EXPLANATION.md`
- **Features:** See `FEATURES.md`

