# CareerLens AI

A mono-repo containing the frontend and backend applications for CareerLens AI.

## 📚 Documentation

- **[COMPLETE_GUIDE.md](./COMPLETE_GUIDE.md)** - **Complete guide with everything you need** (START HERE!)
  - How to run
  - API keys setup
  - How APIs work
  - Code explanation
  - Features
  - Troubleshooting

**Reference guides:**
- [HOW_TO_RUN.md](./HOW_TO_RUN.md) - Quick start guide
- [CODE_EXPLANATION.md](./CODE_EXPLANATION.md) - Detailed code explanation
- [FEATURES.md](./FEATURES.md) - Features explanation
- [DEDALUS_MCP_SETUP.md](./DEDALUS_MCP_SETUP.md) - Dedalus MCP integration (optional)

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys (see HOW_TO_RUN.md for details)
```

**Required API Keys:**
- `ANTHROPIC_API_KEY` - For resume analysis (get from https://console.anthropic.com/)
- `OPENAI_API_KEY` - For resume tailoring (get from https://platform.openai.com/api-keys)
- `AMPLITUDE_API_KEY` - Server-side analytics key
- `VITE_AMPLITUDE_API_KEY` - Browser-side analytics key

**Note:** The app works in fallback mode without API keys (uses mock data).

### 2. Backend Setup

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
make dev
# OR: uvicorn app.main:app --reload --port 8000
```

API available at: `http://localhost:8000`  
API docs at: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

## 📖 Code Explanation

See [CODE_EXPLANATION.md](./CODE_EXPLANATION.md) for detailed code explanation.

**Quick Overview:**
- **Anthropic Service** - Uses Claude AI for resume analysis
- **OpenAI Service** - Uses GPT for resume tailoring
- **Dedalus Service** - Job research with multi-source fallback
- **Coach Service** - Generates 7-day personalized plans
- **Predict Service** - Computes score predictions using logistic formula
- **Amplitude Service** - Analytics tracking

## 🧪 Testing

See [HOW_TO_RUN.md](./HOW_TO_RUN.md) for detailed testing instructions.

**Quick test:**
```bash
# Backend health check
curl http://localhost:8000/health

# Or use browser: http://localhost:8000/docs
```

## 📁 Project Structure

```
careerlens-ai/
├── frontend/              # React + Vite + TypeScript
│   ├── src/
│   │   ├── lib/api.ts     # API calls
│   │   ├── store/         # Zustand state
│   │   ├── components/    # React components
│   │   └── pages/         # Route pages
│   └── package.json
├── backend/               # FastAPI + Python 3.11
│   ├── app/
│   │   ├── main.py        # FastAPI app
│   │   ├── routes/        # API endpoints
│   │   └── services/       # Business logic
│   └── requirements.txt
├── .env.example           # Environment template
├── HOW_TO_RUN.md          # How to run the project
├── CODE_EXPLANATION.md    # Code explanation
├── FEATURES.md            # Features explanation
├── DEDALUS_MCP_SETUP.md   # Dedalus MCP guide (optional)
└── README.md              # This file
```

## 🔍 How to Verify Everything Works

1. **Start both servers** (backend on 8000, frontend on 5173)
2. **Open frontend:** `http://localhost:5173`
3. **Test flow:**
   - Upload resume → Get analysis → Generate plan → View jobs
4. **Check API docs:** `http://localhost:8000/docs`
5. **Check console logs** for errors or Amplitude events

For detailed instructions, see [HOW_TO_RUN.md](./HOW_TO_RUN.md).

## 📝 API Contracts

All contracts defined in:
- **Frontend:** `frontend/src/types.ts`
- **Backend:** `backend/app/models/schemas.py`

See [CODE_EXPLANATION.md](./CODE_EXPLANATION.md) for complete code explanation.


