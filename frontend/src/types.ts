/**
 * API Contract Types
 * These types define the strict contracts used throughout the application
 */

export interface DomainScore {
  name: string;
  score: number; // 0..1
}

export interface SkillsBreakdown {
  core: string[];
  adjacent: string[];
  advanced: string[];
}

export interface AnalyzeResponse {
  domains: DomainScore[];
  skills: SkillsBreakdown;
  strengths: string[];
  areas_for_growth: string[];
  recommended_roles: string[];
  keywords_detected: string[];
  debug: {
    hash: string;
    provider: string;
  };
  // Legacy fields for backward compatibility
  score?: number;
  weaknesses?: string[];
  skills_legacy?: Skill[];
  suggestedRoles?: string[];
  domain?: string;
  confidence?: number;
}

export interface Skill {
  name: string;
  level: "core" | "adjacent" | "advanced";
  status: "have" | "gap" | "learning";
}

export interface Job {
  id: string;
  title: string;
  company: string;
  match: number; // 0..100
  why: string[];
  fix: string[];
  jdUrl: string;
  source?: string; // Source of job data (e.g., 'dedalus', 'fallback')
}

export interface RoleMatchItem {
  title: string;
  company: string;
  location: string;
  match: number; // 0..1
  why_fit: string[];
  gaps: string[];
  url: string;
  source: string;
}

export interface RoleMatchResponse {
  items: RoleMatchItem[];
  debug: {
    source: string;
    count: number;
    hash?: string;
  };
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

export interface PlanDay {
  day: number;
  title: string;
  actions: string[];
}

export interface Prediction {
  baseline: number;
  afterPlan: number;
  delta: number;
}

export interface ResumeVersion {
  id: string;
  role: string;
  resumeText: string;
  analysis: AnalyzeResponse;
  createdAt: string;
  updatedAt: string;
}

export interface ResumeProgress {
  resumeId: string;
  role: string;
  versions: {
    date: string;
    score: number;
    skillsCount: number;
    strengthsCount: number;
    weaknessesCount: number;
    coreSkillsCount?: number;
    adjacentSkillsCount?: number;
    advancedSkillsCount?: number;
    metrics?: {
      domainScore: number;
      skillsScore: number;
      balanceScore: number;
    };
  }[];
  currentScore: number;
  previousScore: number | null;
  scoreChange: number | null;
  scoreChangePercent: number | null;
  skillImprovements: {
    skill: string;
    previousStatus: string;
    currentStatus: string;
  }[];
  newSkills: string[];
  closedGaps: string[];
  domainChanges: Array<{
    domain: string;
    previousScore: number;
    currentScore: number;
  }>;
  metrics?: {
    domainScore: number;
    skillsScore: number;
    balanceScore: number;
  };
}

// LinkedIn Job Search Types (RapidAPI)
export interface LinkedInJobSearchItem {
  id: string;
  title: string;
  company: string;
  location?: string;
  url: string;
  listed_at?: string;
  source: string;
  description_snippet?: string;
  matchScore: number; // 0..100
  reasons: string[]; // Top 3 match reasons
  gaps: string[]; // Top 3 skills to improve
  skill_breakdown?: {
    resume_skills: string[];
    job_skills: string[];
    matched_skills: string[];
    missing_skills: string[];
    match_percentage: number;
    resume_skill_count: number;
    job_skill_count: number;
    matched_count: number;
  };
}

export interface LinkedInJobSearchResponse {
  jobs: LinkedInJobSearchItem[];
  nextCursor?: string | null;
  debug?: {
    source: string;
    count: number;
    hash?: string;
    message?: string;
  };
}

export interface GetJobsParams {
  role: string;
  location?: string;
  radius_km?: number; // Backend uses km (API requirement), frontend converts from miles
  remote?: boolean;
  limit?: number;
  cursor?: string;
}

