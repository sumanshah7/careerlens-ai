# Features Explanation

## 🎯 Overview

CareerLens AI is a comprehensive career development platform that helps job seekers:
- **Analyze** their resume and get career readiness score
- **Find** matching job opportunities
- **Tailor** their resume for specific jobs
- **Learn** with personalized 7-day coaching plans
- **Track** their progress and predict improvement

## ✨ Core Features

### 1. Resume Analysis

**What it does:**
- Analyzes your resume using AI (Claude)
- Provides career readiness score (0-100)
- Identifies strengths and weaknesses
- Categorizes skills by level (core, adjacent, advanced)
- Suggests matching roles

**How to use:**
1. Go to Home page (`/`)
2. Paste your resume text or upload file
3. Click "Analyze Resume"
4. View analysis on Analysis page

**What you get:**
- **Score:** Career readiness score (0-100)
- **Strengths:** What you're good at
- **Weaknesses:** Areas to improve
- **Skills:** Categorized by level and status (have, gap, learning)
- **Suggested Roles:** Roles that match your profile

**Technical Details:**
- Uses Anthropic Claude AI
- Validates response with Pydantic schema
- Retries up to 3 times if JSON parsing fails
- Falls back to mock data if API fails

### 2. Job Research

**What it does:**
- Searches for jobs matching your profile
- Computes match scores based on skill overlap
- Provides personalized "why" and "fix" recommendations
- Shows real jobs from job boards (if API keys provided)

**How to use:**
1. Go to Jobs page (`/jobs`)
2. Click "Auto-Research (Dedalus)"
3. View matching jobs with match scores
4. See why you're a good fit and what to improve

**What you get:**
- **Job Listings:** Matching jobs with titles, companies
- **Match Scores:** Percentage match (0-100)
- **Why:** Reasons you're a good fit
- **Fix:** Areas to improve for better match
- **Job Links:** Direct links to job descriptions

**Technical Details:**
- Priority: Dedalus MCP → JSearch API → Fallback heuristics
- Extracts skills from resume and job descriptions
- Computes match: `(matching_skills / total_jd_skills) * 100 - gap_penalties`
- Generates personalized why[] and fix[] arrays
- Annotates jobs with source (jsearch, dedalus-mcp, fallback)

### 3. Resume Tailoring

**What it does:**
- Tailors your resume for specific jobs
- Generates STAR-format bullet points
- Creates elevator pitch
- Writes cover letter

**How to use:**
1. Go to Jobs page (`/jobs`)
2. Click "Tailor with Dedalus" on any job
3. View tailored content in modal
4. Copy bullets, pitch, or cover letter

**What you get:**
- **Bullets:** STAR-format resume bullet points
- **Pitch:** 50-word elevator pitch
- **Cover Letter:** 120-180 word cover letter

**Technical Details:**
- Uses OpenAI GPT (gpt-4o with fallback to gpt-4o-mini)
- Validates response with Pydantic schema
- Retries up to 3 times if validation fails
- Falls back to mock data if API fails

### 4. Coaching Plan

**What it does:**
- Generates personalized 7-day coaching plan
- Addresses skill gaps identified in analysis
- Includes real course links from major platforms
- Provides actionable daily tasks

**How to use:**
1. Go to Analysis page (`/analysis`)
2. Review your weaknesses (skill gaps)
3. Check "Enable daily reminders" (optional)
4. Click "Generate Plan"
5. View plan on Coaching Plan page (`/coaching-plan`)

**What you get:**
- **7-Day Plan:** Structured learning plan
- **Daily Tasks:** 2-3 actionable items per day
- **Course Links:** Real links to DataCamp, Udemy, Coursera, etc.
- **Platform Badges:** Shows which platform (DataCamp, Udemy, etc.)
- **Reminders:** Optional daily reminders

**Technical Details:**
- Uses Claude or OpenAI to generate plan
- Post-processes to ensure exactly 7 days
- Ensures 2-3 actions per day
- Adds real course links if AI doesn't include them
- Links to: DataCamp, Udemy, Coursera, edX, freeCodeCamp, AWS Skill Builder, YouTube

### 5. Score Prediction

**What it does:**
- Predicts score improvement after completing coaching plan
- Shows baseline, after-plan, and delta scores
- Uses logistic formula for prediction

**How to use:**
1. Go to Dashboard page (`/dashboard`)
2. View prediction tile
3. See baseline, after-plan, and delta scores

**What you get:**
- **Baseline:** Current predicted score
- **After Plan:** Predicted score after completing plan
- **Delta:** Expected improvement

**Technical Details:**
- Uses logistic formula: `sigmoid(a × skills_have - b × skills_gap) × 100`
- Constants: `a = 0.15`, `b = 0.20`
- Assumes 2 more skills learned, 2 gaps closed
- Deterministic calculation

### 6. Dashboard

**What it does:**
- Shows career progress overview
- Displays current score, jobs found, plan days
- Shows score over time chart
- Displays prediction tile

**How to use:**
1. Go to Dashboard page (`/dashboard`)
2. View all metrics and charts

**What you get:**
- **Current Score:** Latest analysis score (from API)
- **Jobs Found:** Total matching opportunities
- **Plan Days:** Days in your coaching plan
- **Score Over Time:** Progress trajectory chart
- **Prediction:** Expected improvement after plan

**Technical Details:**
- Score comes from API (not hardcoded)
- Jobs count from Zustand store
- Plan days from coaching plan
- Score chart uses mock data (not connected to real history)

### 7. Settings

**What it does:**
- Create alert rules for job searches
- Set role, location, min match, frequency
- Persists locally (localStorage)

**How to use:**
1. Go to Settings page (`/settings`)
2. Fill in alert rule form
3. Click "Create Alert"
4. Rule is saved locally

**What you get:**
- **Alert Rules:** Custom job search alerts
- **Local Persistence:** Rules saved in browser

**Technical Details:**
- Uses localStorage for persistence
- No backend integration yet
- Form validation

## 🎨 UI Features

### Score Donut Chart
- Visual representation of career readiness score
- Uses Recharts library
- Color-coded (green for high, yellow for medium, red for low)

### Skill Chips
- Displays skills grouped by level
- Color-coded badges (core, adjacent, advanced)
- Shows status (have, gap, learning)

### Job Cards
- Displays job listings with match scores
- Shows why[] and fix[] recommendations
- Clickable "View JD" button
- "Tailor with Dedalus" button

### Tailor Modal
- Displays tailored content
- Tabs for bullets, pitch, cover letter
- Copy buttons for each section

### Coaching Plan Page
- Shows all 7 days of plan
- Course links with platform badges
- "Open Course" buttons
- Reminders indicator

### Loading States
- Skeleton loaders for initial load
- Spinners for actions
- Progress indicators

## 📊 Analytics Features

### Event Tracking
- **Client-side:** Tracks user interactions (clicks, views, etc.)
- **Server-side:** Tracks API calls and AI operations
- **Metadata:** Rich metadata for each event (score, gap_count, etc.)

### Events Tracked
- `resume_uploaded` - When user uploads resume
- `ai_analyzed` - When analysis is displayed
- `ai_analyzed_server` - When Claude analyzes resume
- `tailor_clicked` - When user clicks tailor button
- `tailor_completed` - When GPT tailors resume
- `coach_plan_generated` - When coaching plan is created
- `job_viewed` - When user views a job
- `get_jobs_success` - When jobs are fetched

## 🔄 Workflow Features

### Complete User Journey
1. **Upload Resume** → Get analysis
2. **View Analysis** → See score, strengths, weaknesses, skills
3. **Generate Plan** → Create 7-day coaching plan
4. **Research Jobs** → Find matching opportunities
5. **Tailor Resume** → Customize for specific jobs
6. **Track Progress** → View dashboard and predictions

### Navigation
- Top navigation bar with all pages
- Breadcrumbs (implicit through navigation)
- Back buttons where needed
- Toast notifications for actions

## 🎯 Key Benefits

1. **AI-Powered Analysis** - Real AI analysis using Claude
2. **Personalized Recommendations** - Tailored to your profile
3. **Real Course Links** - Actual links to learning resources
4. **Multi-Source Job Research** - Multiple fallback options
5. **Graceful Degradation** - Works even without API keys
6. **Type-Safe** - Strict API contracts with Pydantic/TypeScript
7. **Analytics** - Comprehensive tracking with Amplitude

## 📱 Pages Overview

### Home (`/`)
- Resume upload form
- Text area for resume text
- File upload (PDF disabled for now)
- "Analyze Resume" button

### Analysis (`/analysis`)
- Score donut chart
- Skills breakdown
- Strengths and weaknesses
- Suggested roles
- "Generate Plan" button

### Jobs (`/jobs`)
- "Auto-Research" button
- Job cards with match scores
- "Tailor with Dedalus" buttons
- Loading skeletons

### Dashboard (`/dashboard`)
- Current score card
- Jobs found card
- Plan days card
- Score over time chart
- Prediction tile

### Coaching Plan (`/coaching-plan`)
- 7-day plan display
- Course links with platform badges
- "Open Course" buttons
- Reminders indicator

### Settings (`/settings`)
- Alert rule form
- Role, location, min match, frequency
- Local persistence

## 🔐 Security Features

- **Environment Variables** - API keys stored in `.env` (not committed)
- **CORS** - Configured for localhost only
- **Input Validation** - Pydantic schemas validate all inputs
- **Error Handling** - Graceful error handling with fallbacks

## 🚀 Performance Features

- **Lazy Loading** - Components loaded on demand
- **Skeleton Loaders** - Better perceived performance
- **Error Boundaries** - Graceful error handling
- **Retry Logic** - Automatic retries for transient errors
- **Fallback Data** - Mock data if APIs fail

## 📈 Future Features (Not Yet Implemented)

- PDF resume parsing
- Real-time progress updates (SSE/WebSocket)
- User authentication
- Resume history tracking
- Job application tracking
- Interview preparation
- Salary predictions

