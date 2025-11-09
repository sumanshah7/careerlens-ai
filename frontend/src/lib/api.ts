import type { AnalyzeResponse, Job, TailorResponse, CoachPlan, Prediction, LinkedInJobSearchItem, LinkedInJobSearchResponse, GetJobsParams } from '../types';
import { track } from './analytics';

// Get API base URL from environment
const getApiBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || import.meta.env.API_BASE_URL || 'http://localhost:8000';
};

// Mock data generators (fallback)
const generateMockAnalysis = (): AnalyzeResponse => ({
  domains: [
    { name: "Frontend", score: 0.85 },
    { name: "Full-Stack", score: 0.65 }
  ],
  skills: {
    core: ["React", "TypeScript", "JavaScript"],
    adjacent: ["Node.js", "CSS", "HTML"],
    advanced: ["System Design", "GraphQL"]
  },
  strengths: [
    "Strong experience with React and TypeScript",
    "Excellent problem-solving skills",
    "Good communication abilities"
  ],
  areas_for_growth: [
    "Limited experience with cloud infrastructure",
    "Need to improve system design knowledge"
  ],
  keywords_detected: ["react", "typescript", "javascript", "node.js"],
  debug: {
    hash: "unknown",
    provider: "fallback"
  },
  // Legacy fields for backward compatibility (calculated dynamically, not hardcoded)
  // score is calculated in useAppStore based on domains, skills, and strengths/growth ratio
  suggestedRoles: [
    "Senior Frontend Engineer",
    "Full Stack Developer",
    "React Developer"
  ]
});

const generateMockJobs = (): Job[] => [
  {
    id: "1",
    title: "Senior Frontend Engineer",
    company: "Tech Corp",
    match: 85,
    why: ["Strong React experience", "TypeScript proficiency"],
    fix: ["AWS knowledge", "System design"],
    jdUrl: "https://example.com/job/1",
    source: "mock"
  }
];

// Generic fetch wrapper with error handling
async function fetchWithFallback<T>(
  url: string,
  options: RequestInit,
  fallback: T,
  eventName: string,
  eventProps?: Record<string, any>
): Promise<T> {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      console.error(`[${eventName}] HTTP ${response.status}: ${await response.text()}`);
      track(eventName, { ...eventProps, error: response.status });
      return fallback;
    }
    
    const data = await response.json();
    track(eventName, { ...eventProps, success: true });
    return data;
  } catch (error: any) {
    console.error(`[${eventName}] Error:`, error);
    track(eventName, { ...eventProps, error: error.message });
    return fallback;
  }
}

// API functions
export const analyzeResume = async (
  resumeText: string,
  targetRole?: string,
  preferredRoles?: string[],
  topKDomains?: number,
  signal?: AbortSignal
): Promise<AnalyzeResponse> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/analyze-resume`;
  
  const hash = await sha256(resumeText);
  const queryParams = new URLSearchParams({ hash: hash.substring(0, 8) });
  if (topKDomains) {
    queryParams.append('top_k_domains', topKDomains.toString());
  }
  
  return fetchWithFallback<AnalyzeResponse>(
    `${url}?${queryParams.toString()}`,
    {
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
    },
    generateMockAnalysis(),
    'analyze_resume',
    { hash: hash.substring(0, 8), targetRole }
  );
};

// SHA256 hash utility
async function sha256(text: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export const getJobs = async (
  targetRole: string,
  location?: string,
  resumeText?: string,
  hash?: string,
  signal?: AbortSignal,
  domains?: Array<{ name: string; score: number }>
): Promise<Job[]> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/roleMatchAndOpenings`;
  
  const queryParams = new URLSearchParams();
  if (hash) {
    queryParams.append('hash', hash.substring(0, 8));
  }
  
  const requestBody = {
    resume_text: resumeText || '',
    domains: domains || [],
    preferred_roles: [targetRole],
    locations: location ? [location] : ['US-Remote'],
    top_n: 20
  };
  
  try {
    const response = await fetch(`${url}?${queryParams.toString()}`, {
      method: 'POST',
      body: JSON.stringify(requestBody),
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
      },
      signal,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[getJobs] HTTP ${response.status}: ${errorText}`);
      throw new Error(`Failed to fetch jobs: ${response.status} ${errorText}`);
    }
    
    const data = await response.json();
    
    // Map RoleMatchItem[] to Job[]
    const jobs: Job[] = (data.items || []).map((item: any) => ({
      id: item.id || `job-${Math.random()}`,
      title: item.title || 'Job Opening',
      company: item.company || 'Company',
      match: Math.round((item.match || 0.5) * 100), // Convert 0-1 to 0-100
      why: item.why_fit || item.why || [],
      fix: item.gaps || item.fix || [],
      jdUrl: item.url || item.jdUrl || '',
      source: item.source || 'unknown'
    }));
    
    track('jobs_fetched', {
      hash: hash?.substring(0, 8) || 'unknown',
      count: jobs.length,
      source: data.debug?.source || 'unknown',
    });
    
    return jobs;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('[getJobs] Request aborted');
      throw error;
    }
    
    console.error('[getJobs] Error:', error);
    return generateMockJobs();
  }
};

/**
 * Search LinkedIn jobs using RapidAPI LinkedIn Job Search API
 */
export const searchJobs = async (
  params: {
    role: string;
    location?: string;
    radius_km?: number;
    remote?: boolean;
    limit?: number;
    cursor?: string | null;
    resume_skills?: string[]; // Resume skills from analysis
  },
  signal?: AbortSignal
): Promise<LinkedInJobSearchResponse> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/jobs/search`;

  const queryParams = new URLSearchParams({
    role: params.role,
    ...(params.location && { location: params.location }),
    ...(params.radius_km && { radius_km: params.radius_km.toString() }),
    ...(params.remote !== undefined && { remote: params.remote.toString() }),
    ...(params.limit && { limit: params.limit.toString() }),
    ...(params.cursor && { cursor: params.cursor }),
    ...(params.resume_skills && params.resume_skills.length > 0 && { resume_skills: params.resume_skills.join(',') }),
  });

  const fullUrl = `${url}?${queryParams.toString()}`;

  try {
    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
      },
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[searchJobs] HTTP ${response.status}: ${errorText}`);
      throw new Error(`Failed to fetch jobs: ${response.status} ${errorText}`);
    }

    const data: LinkedInJobSearchResponse = await response.json();
    
    // Track event (only hash/counts, no PII)
    track('linkedin_jobs_searched', {
      hash: data.debug?.hash || 'unknown',
      count: data.jobs?.length || 0,
      source: data.debug?.source || 'unknown',
    });

    return data;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('[searchJobs] Request aborted');
      throw error;
    }
    
    console.error('[searchJobs] Error:', error);
    throw error;
  }
};

export const tailor = async (
  resumeText: string,
  jobTitle: string,
  company: string,
  jobDescription: string,
  signal?: AbortSignal
): Promise<TailorResponse> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/tailor`;
  
  return fetchWithFallback<TailorResponse>(
    url,
    {
      method: 'POST',
      body: JSON.stringify({
        resume_text: resumeText,
        job_title: jobTitle,
        company: company,
        job_description: jobDescription
      }),
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
      },
      signal,
    },
    {
      bullets: [],
      pitch: '',
      coverLetter: ''
    },
    'tailor_resume',
    { jobTitle, company }
  );
};

export const generatePlan = async (
  resumeText: string,
  selectedRole: string,
  jdRequirements: string[],
  gaps: string[],
  skills: { core: string[]; adjacent: string[]; advanced: string[] },
  horizonDays: number = 7,
  hash?: string,
  signal?: AbortSignal
): Promise<CoachPlan> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/generatePlan`;
  
  const queryParams = new URLSearchParams();
  if (hash) {
    queryParams.append('hash', hash.substring(0, 8));
  }
  
  return fetchWithFallback<CoachPlan>(
    `${url}?${queryParams.toString()}`,
    {
      method: 'POST',
      body: JSON.stringify({
        resume_text: resumeText,
        selected_role: selectedRole,
        jd_requirements: jdRequirements,
        gaps: gaps,
        skills: skills,
        horizon_days: horizonDays
      }),
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
      },
      signal,
    },
    {
      plan: [],
      reminders: false
    },
    'generate_plan',
    { hash: hash?.substring(0, 8) || 'unknown', role: selectedRole }
  );
};

export const autoCoach = async (
  gaps: string[],
  targetRole?: string,
  domain?: string,
  reminders: boolean = false,
  signal?: AbortSignal
): Promise<CoachPlan> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/autoCoach`;
  
  return fetchWithFallback<CoachPlan>(
    url,
    {
      method: 'POST',
      body: JSON.stringify({
        gaps: gaps,
        targetRole: targetRole,
        domain: domain,
        reminders: reminders
      }),
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
      },
      signal,
    },
    {
      plan: [],
      reminders: false
    },
    'auto_coach',
    { targetRole, domain, gapCount: gaps.length }
  );
};

export const getRoleMatchScore = async (
  resumeText: string,
  targetRole: string | null,
  signal?: AbortSignal
): Promise<{ score: number; debug: { hash: string; provider: string } }> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/predictScore`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume_text: resumeText,
        target_role: targetRole || null,
      }),
      signal,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    track('role_match_score_fetched', {
      score: data.score,
      has_target_role: !!targetRole,
    });
    return data;
  } catch (error) {
    console.error('❌ Failed to fetch role match score:', error);
    // Return a default score if API fails
    return { score: 0, debug: { hash: 'error', provider: 'fallback' } };
  }
};

export const getPrediction = async (
  skillsHave: string[],
  skillsGap: string[],
  signal?: AbortSignal
): Promise<Prediction> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/predict`;
  
  // Build query parameters
  const queryParams = new URLSearchParams();
  if (skillsHave.length > 0) {
    skillsHave.forEach(skill => queryParams.append('skills_have', skill));
  }
  if (skillsGap.length > 0) {
    skillsGap.forEach(skill => queryParams.append('skills_gap', skill));
  }
  
  const fullUrl = queryParams.toString() ? `${url}?${queryParams.toString()}` : url;
  
  return fetchWithFallback<Prediction>(
    fullUrl,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
      },
      signal,
    },
    {
      baseline: 0.5,
      afterPlan: 0.7,
      delta: 0.2
    },
    'get_prediction',
    { skillsHaveCount: skillsHave.length, skillsGapCount: skillsGap.length }
  );
};

export const checkHealth = async (): Promise<{
  ok: boolean;
  providers: {
    anthropic: boolean;
    openai: boolean;
    dedalus: boolean;
    mcp: boolean;
  };
}> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/health`;
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Cache-Control': 'no-cache',
      },
    });
    
    if (!response.ok) {
      return {
        ok: false,
        providers: {
          anthropic: false,
          openai: false,
          dedalus: false,
          mcp: false,
        },
      };
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('[checkHealth] Error:', error);
    return {
      ok: false,
      providers: {
        anthropic: false,
        openai: false,
        dedalus: false,
        mcp: false,
      },
    };
  }
};

export const uploadPDF = async (file: File, signal?: AbortSignal): Promise<{ text: string }> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/upload/pdf`;
  
  const formData = new FormData();
  formData.append('file', file);
  
  console.log('📤 Uploading PDF to:', url);
  console.log('📤 File:', file.name, '-', file.size, 'bytes');
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      signal,
    });
    
    console.log('📥 Response status:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[uploadPDF] HTTP ${response.status}: ${errorText}`);
      throw new Error(`Failed to upload PDF: ${response.status} ${errorText}`);
    }
    
    const data = await response.json();
    console.log('✅ PDF uploaded successfully:', data);
    
    track('resume_uploaded', {
      hash: data.hash?.substring(0, 8) || 'unknown',
      size: file.size,
    });
    
    return data;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('[uploadPDF] Request aborted');
      throw error;
    }
    
    console.error('[uploadPDF] Error:', error);
    throw error;
  }
};

// Removed duplicate searchJobs - using the LinkedIn jobs search function above instead
// This was the old /jobs/search endpoint, now replaced by /api/jobs/search
