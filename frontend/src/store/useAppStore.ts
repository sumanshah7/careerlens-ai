import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AnalyzeResponse, Job, TailorResponse, CoachPlan, ResumeVersion, ResumeProgress } from '../types';

interface AppStore {
  // Current session data
  resumeText: string;
  analysis: AnalyzeResponse | null;
  jobs: Job[];
  tailor: TailorResponse | null;
  coach: CoachPlan | null;
  currentRole: string | null;
  currentResumeId: string | null;
  
  // UI state
  darkMode: boolean;
  setDarkMode: (enabled: boolean) => void;
  toggleDarkMode: () => void;
  
  // Resume management (persisted)
  resumes: ResumeVersion[];
  resumeHistory: Map<string, ResumeProgress>;
  
  // Setters
  setResumeText: (text: string) => void;
  setAnalysis: (analysis: AnalyzeResponse) => void;
  setJobs: (jobs: Job[]) => void;
  setTailor: (tailor: TailorResponse) => void;
  setCoach: (coach: CoachPlan) => void;
  setCurrentRole: (role: string | null) => void;
  
  // Resume management
  saveResume: (role: string, resumeText: string, analysis: AnalyzeResponse) => string;
  loadResume: (resumeId: string) => void;
  deleteResume: (resumeId: string) => void;
  getResumeByRole: (role: string) => ResumeVersion | null;
  getAllRoles: () => string[];
  getResumeProgress: (resumeId: string) => ResumeProgress | null;
  
  clearAll: () => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      // Current session data
      resumeText: '',
      analysis: null,
      jobs: [],
      tailor: null,
      coach: null,
      currentRole: null,
      currentResumeId: null,
      
      // UI state
      darkMode: typeof window !== 'undefined' ? localStorage.getItem('careerlens-dark-mode') === 'true' : false,
      setDarkMode: (enabled) => {
        set({ darkMode: enabled });
        if (typeof window !== 'undefined') {
          localStorage.setItem('careerlens-dark-mode', enabled ? 'true' : 'false');
          if (enabled) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
        }
      },
      toggleDarkMode: () => {
        const current = get().darkMode;
        get().setDarkMode(!current);
      },
      
      // Resume management (persisted)
      resumes: [],
      resumeHistory: new Map(),
      
      // Setters
      setResumeText: (text) => set({ resumeText: text }),
      setAnalysis: (analysis) => set({ analysis }),
      setJobs: (jobs) => set({ jobs }),
      setTailor: (tailor) => set({ tailor }),
      setCoach: (coach) => set({ coach }),
      setCurrentRole: (role) => set({ currentRole: role }),
      
      // Resume management
      saveResume: (role, resumeText, analysis) => {
        const resumeId = `resume_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const now = new Date().toISOString();
        
        const newResume: ResumeVersion = {
          id: resumeId,
          role,
          resumeText,
          analysis,
          createdAt: now,
          updatedAt: now,
        };
        
        // Update or create resume for this role
        set((state) => {
          const existingIndex = state.resumes.findIndex(r => r.role === role);
          let updatedResumes: ResumeVersion[];
          
          if (existingIndex >= 0) {
            // Update existing resume
            updatedResumes = [...state.resumes];
            updatedResumes[existingIndex] = {
              ...updatedResumes[existingIndex],
              resumeText,
              analysis,
              updatedAt: now,
            };
          } else {
            // Add new resume
            updatedResumes = [...state.resumes, newResume];
          }
          
          // Update progress tracking
          const history = new Map(state.resumeHistory);
          
          // Calculate comprehensive score (more accurate)
          // Weighted average of top domain (50%) + Skills coverage (30%) + Strengths/Growth ratio (20%)
          const topDomain = analysis.domains[0];
          const domainScore = topDomain 
            ? Math.round(topDomain.score * 100)  // Use top domain score directly (0.0-1.0 → 0-100)
            : 50;
          
          const skillsCount = (analysis.skills.core?.length || 0) + 
                             (analysis.skills.adjacent?.length || 0) + 
                             (analysis.skills.advanced?.length || 0);
          // Normalize skills: 10+ skills = 100%, 5 skills = 50%, 0 skills = 0%
          const skillsScore = Math.min(100, Math.max(0, (skillsCount / 10) * 100));
          
          const strengthsCount = analysis.strengths.length;
          const weaknessesCount = (analysis.areas_for_growth || analysis.weaknesses || []).length;
          // Balance score: more strengths than weaknesses = higher score
          const balanceScore = weaknessesCount > 0 
            ? Math.min(100, Math.max(0, (strengthsCount / (strengthsCount + weaknessesCount)) * 100))
            : strengthsCount > 0 ? 100 : 50;
          
          // Weighted composite score (top domain is most important)
          const currentScore = Math.round(
            domainScore * 0.5 + 
            skillsScore * 0.3 + 
            balanceScore * 0.2
          );
          
          // Ensure score is realistic (not always 100)
          // Cap at 95 to leave room for improvement
          const finalScore = Math.min(95, Math.max(0, currentScore));
          
          // Store score in analysis for display
          analysis.score = finalScore;
          
          const progress = history.get(role) || {
            resumeId: existingIndex >= 0 ? state.resumes[existingIndex].id : resumeId,
            role,
            versions: [],
            currentScore: currentScore,
            previousScore: null,
            scoreChange: null,
            scoreChangePercent: null,
            skillImprovements: [],
            newSkills: [],
            closedGaps: [],
            domainChanges: [],
            metrics: {
              domainScore,
              skillsScore,
              balanceScore,
            },
          };
          
          // Get previous version for comparison
          const previousResume = existingIndex >= 0 ? state.resumes[existingIndex] : null;
          const previousScore = previousResume 
            ? (previousResume.analysis.score || Math.round((previousResume.analysis.domains[0]?.score || 0.5) * 100))
            : null;
          const scoreChange = previousScore !== null ? currentScore - previousScore : null;
          const scoreChangePercent = previousScore !== null && previousScore > 0
            ? Math.round((scoreChange! / previousScore) * 100)
            : null;
          
          // Track skill improvements across categories (core/adjacent/advanced)
          const skillImprovements: ResumeProgress['skillImprovements'] = [];
          const newSkills: string[] = [];
          const closedGaps: string[] = [];
          
          if (previousResume) {
            // Track skills moving between categories
            const prevSkills = {
              core: new Set((previousResume.analysis.skills?.core || []).map((s: string) => s.toLowerCase())),
              adjacent: new Set((previousResume.analysis.skills?.adjacent || []).map((s: string) => s.toLowerCase())),
              advanced: new Set((previousResume.analysis.skills?.advanced || []).map((s: string) => s.toLowerCase())),
            };
            
            const currSkills = {
              core: new Set((analysis.skills?.core || []).map((s: string) => s.toLowerCase())),
              adjacent: new Set((analysis.skills?.adjacent || []).map((s: string) => s.toLowerCase())),
              advanced: new Set((analysis.skills?.advanced || []).map((s: string) => s.toLowerCase())),
            };
            
            // Find skills that moved up (improvement)
            prevSkills.core.forEach(skill => {
              if (currSkills.adjacent.has(skill)) {
                skillImprovements.push({
                  skill: skill,
                  previousStatus: 'Core',
                  currentStatus: 'Adjacent',
                });
              } else if (currSkills.advanced.has(skill)) {
                skillImprovements.push({
                  skill: skill,
                  previousStatus: 'Core',
                  currentStatus: 'Advanced',
                });
              }
            });
            
            prevSkills.adjacent.forEach(skill => {
              if (currSkills.advanced.has(skill)) {
                skillImprovements.push({
                  skill: skill,
                  previousStatus: 'Adjacent',
                  currentStatus: 'Advanced',
                });
              }
            });
            
            // Find new skills added
            [...currSkills.core, ...currSkills.adjacent, ...currSkills.advanced].forEach(skill => {
              if (!prevSkills.core.has(skill) && !prevSkills.adjacent.has(skill) && !prevSkills.advanced.has(skill)) {
                newSkills.push(skill);
              }
            });
            
            // Track closed gaps (areas for growth that are now strengths or skills)
            const prevGaps = new Set((previousResume.analysis.areas_for_growth || previousResume.analysis.weaknesses || [])
              .map((g: string) => g.toLowerCase()));
            const currGaps = new Set((analysis.areas_for_growth || analysis.weaknesses || [])
              .map((g: string) => g.toLowerCase()));
            
            prevGaps.forEach(gap => {
              if (!currGaps.has(gap)) {
                // Check if it's now in skills
                const gapLower = gap.toLowerCase();
                const isNowSkill = [...currSkills.core, ...currSkills.adjacent, ...currSkills.advanced]
                  .some(skill => gapLower.includes(skill) || skill.includes(gapLower));
                
                if (isNowSkill || analysis.strengths.some(s => s.toLowerCase().includes(gapLower))) {
                  closedGaps.push(gap);
                }
              }
            });
          }
          
          // Track domain changes
          const domainChanges: Array<{domain: string; previousScore: number; currentScore: number}> = [];
          if (previousResume && previousResume.analysis.domains) {
            const prevDomains = new Map(
              previousResume.analysis.domains.map((d: any) => [d.name, d.score])
            );
            
            analysis.domains.forEach((domain: any) => {
              const prevScore = prevDomains.get(domain.name);
              if (prevScore !== undefined && Math.abs(domain.score - prevScore) > 0.1) {
                domainChanges.push({
                  domain: domain.name,
                  previousScore: Math.round(prevScore * 100),
                  currentScore: Math.round(domain.score * 100),
                });
              }
            });
          }
          
          // Calculate metrics for current version
          const currentMetrics = {
            domainScore,
            skillsScore,
            balanceScore,
          };
          
          // Add new version to history
          progress.versions.push({
            date: now,
            score: currentScore,
            skillsCount: skillsCount,
            strengthsCount: strengthsCount,
            weaknessesCount: weaknessesCount,
            coreSkillsCount: analysis.skills?.core?.length || 0,
            adjacentSkillsCount: analysis.skills?.adjacent?.length || 0,
            advancedSkillsCount: analysis.skills?.advanced?.length || 0,
            metrics: currentMetrics,
          });
          
          progress.currentScore = currentScore;
          progress.previousScore = previousScore;
          progress.scoreChange = scoreChange;
          progress.scoreChangePercent = scoreChangePercent;
          progress.skillImprovements = skillImprovements;
          progress.newSkills = newSkills;
          progress.closedGaps = closedGaps;
          progress.domainChanges = domainChanges;
          progress.metrics = currentMetrics;
          
          history.set(role, progress);
          
          return {
            resumes: updatedResumes,
            resumeHistory: history,
            currentResumeId: existingIndex >= 0 ? state.resumes[existingIndex].id : resumeId,
            currentRole: role,
            resumeText,
            analysis,
          };
        });
        
        return resumeId;
      },
      
      loadResume: (resumeId) => {
        const resume = get().resumes.find(r => r.id === resumeId);
        if (resume) {
          set({
            currentResumeId: resumeId,
            currentRole: resume.role,
            resumeText: resume.resumeText,
            analysis: resume.analysis,
          });
        }
      },
      
      deleteResume: (resumeId) => {
        set((state) => {
          const resume = state.resumes.find(r => r.id === resumeId);
          const updatedResumes = state.resumes.filter(r => r.id !== resumeId);
          const history = new Map(state.resumeHistory);
          
          if (resume) {
            history.delete(resume.role);
          }
          
          return {
            resumes: updatedResumes,
            resumeHistory: history,
            currentResumeId: state.currentResumeId === resumeId ? null : state.currentResumeId,
            currentRole: state.currentResumeId === resumeId ? null : state.currentRole,
          };
        });
      },
      
      getResumeByRole: (role) => {
        return get().resumes.find(r => r.role === role) || null;
      },
      
      getAllRoles: () => {
        return Array.from(new Set(get().resumes.map(r => r.role)));
      },
      
      getResumeProgress: (resumeId) => {
        const resume = get().resumes.find(r => r.id === resumeId);
        if (!resume) return null;
        return get().resumeHistory.get(resume.role) || null;
      },
      
      clearAll: () => set({ 
        resumeText: '', 
        analysis: null, 
        jobs: [], 
        tailor: null, 
        coach: null,
        currentResumeId: null,
        currentRole: null,
      }),
    }),
    {
      name: 'careerlens-storage',
      partialize: (state) => ({
        resumes: state.resumes,
        resumeHistory: Array.from(state.resumeHistory.entries()),
        darkMode: state.darkMode,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Convert array back to Map
          if (state.resumeHistory && Array.isArray(state.resumeHistory)) {
            state.resumeHistory = new Map(state.resumeHistory);
          } else if (!state.resumeHistory) {
            state.resumeHistory = new Map();
          }
          
          // Initialize dark mode from localStorage
          if (typeof window !== 'undefined') {
            const darkMode = localStorage.getItem('careerlens-dark-mode') === 'true';
            state.darkMode = darkMode;
            if (darkMode) {
              document.documentElement.classList.add('dark');
            } else {
              document.documentElement.classList.remove('dark');
            }
          }
        }
      },
    }
  )
);

