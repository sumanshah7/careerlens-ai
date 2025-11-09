import { useAppStore } from '../store/useAppStore';
import { autoCoach, checkHealth } from '../lib/api';
import { track } from '../lib/analytics';
import { ScoreDonut } from '../components/ScoreDonut';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { Spinner } from '../components/ui/spinner';
import { toast } from 'sonner';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

export const Analysis = () => {
  const { analysis, setCoach, resumeText, currentRole } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [reminders, setReminders] = useState(false);
  const [healthStatus, setHealthStatus] = useState<{ ok: boolean; providers: { anthropic: boolean; openai: boolean; dedalus: boolean; mcp: boolean } } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check health on mount
    checkHealth().then(setHealthStatus).catch(() => setHealthStatus({ ok: false, providers: { anthropic: false, openai: false, dedalus: false, mcp: false } }));
  }, []);

  useEffect(() => {
    if (analysis) {
      console.log('📊 Displaying analysis:', analysis);
      console.log('📊 Analysis domains:', analysis.domains);
      console.log('📊 Analysis skills:', analysis.skills);
      const topDomain = analysis.domains?.[0];
      track('ai_analyzed', { 
        domain: topDomain?.name || 'unknown',
        domain_score: topDomain?.score || 0,
        domains_count: analysis.domains.length 
      });
      // Simulate small latency for better UX
      setTimeout(() => setInitialLoading(false), 300);
      
      // Role Match Score removed - focusing only on Areas for Growth
    } else {
      // Don't redirect, just show empty state
      setInitialLoading(false);
    }
  }, [analysis, resumeText, currentRole]);

  const handleGeneratePlan = async () => {
    if (!analysis) {
      toast.error('No analysis data available');
      return;
    }
    
    setLoading(true);
    try {
      const gaps = analysis.areas_for_growth || analysis.weaknesses || [];
      const topDomain = analysis.domains?.[0];
      const targetRole = topDomain?.name || 'Software Engineer';
      const domain = topDomain?.name || analysis.domain;
      const coachPlan = await autoCoach(gaps, targetRole, domain, reminders);
      setCoach(coachPlan);
      track('coach_plan_generated', { 
        domain: topDomain?.name || 'unknown',
        gapCount: gaps.length,
        targetRole,
        domain,
        reminders
      });
      toast.success('Coaching plan generated successfully!', {
        action: {
          label: 'View Plan',
          onClick: () => navigate('/coaching-plan')
        }
      });
    } catch (error) {
      const errorName = error instanceof Error ? error.name : 'UnknownError';
      const topDomain = analysis.domains?.[0];
      track('coach_plan_failed', { 
        domain: topDomain?.name || 'unknown',
        errorName,
        errorMessage: error instanceof Error ? error.message : String(error)
      });
      toast.error('Failed to generate coaching plan');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Health check banner
  const getHealthBanner = () => {
    if (!healthStatus) return null;
    // All good if backend is running and at least one LLM provider is available
    if (healthStatus.ok && (healthStatus.providers.anthropic || healthStatus.providers.openai)) return null;
    
    const missingProviders: string[] = [];
    if (!healthStatus.ok) {
      return (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-red-500 font-semibold">Backend not running</p>
          <p className="text-sm text-muted-foreground mt-1">Please start the backend server: <code className="bg-muted px-2 py-1 rounded">cd backend && make dev</code></p>
        </div>
      );
    }
    
    if (!healthStatus.providers.anthropic && !healthStatus.providers.openai) {
      missingProviders.push('ANTHROPIC_API_KEY or OPENAI_API_KEY');
    }
    
    if (missingProviders.length > 0) {
      return (
        <div className="mb-4 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
          <p className="text-amber-500 font-semibold">Missing API Keys</p>
          <p className="text-sm text-muted-foreground mt-1">Please set in <code className="bg-muted px-2 py-1 rounded">backend/.env</code>: {missingProviders.join(', ')}</p>
        </div>
      );
    }
    
    return null;
  };

  // Show empty state if no analysis
  if (!analysis && !initialLoading) {
    return (
      <div className="min-h-screen bg-[#f9fafb]">
        <div className="max-w-[1100px] mx-auto px-6 py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-8"
          >
            <h1 className="text-4xl font-semibold text-[#111827] mb-3">Resume Analysis</h1>
            <p className="text-[#6b7280] text-lg font-normal">Your personalized career insights powered by AI</p>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="bg-white rounded-[16px] p-16 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] text-center"
          >
            <div className="mb-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-[#F9FAFB] flex items-center justify-center mb-4">
                <svg className="h-8 w-8 text-[#64748B]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">No analysis yet</h3>
              <p className="text-[#64748B] mb-6 font-normal">
                Upload and analyze your resume to get started
              </p>
            </div>
            <Button 
              onClick={() => navigate('/home')} 
              size="lg"
              className="bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
            >
              Go to Resume Upload
            </Button>
          </motion.div>
        </div>
      </div>
    );
  }

  if (initialLoading) {
    return (
      <div className="min-h-screen bg-[#F9FAFB]">
        <div className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
          <div className="mb-12 text-center">
            <Skeleton className="h-14 w-64 mb-6 mx-auto" />
            <Skeleton className="h-6 w-96 mx-auto" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB]">
              <Skeleton className="h-6 w-32 mb-2" />
              <Skeleton className="h-4 w-48 mb-6" />
              <div className="flex items-center justify-center h-[300px]">
                <Spinner size="lg" />
              </div>
            </div>

            <div className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB]">
              <Skeleton className="h-6 w-32 mb-2" />
              <Skeleton className="h-4 w-48 mb-6" />
              <div className="space-y-4">
                <Skeleton className="h-4 w-24" />
                <div className="flex flex-wrap gap-2">
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-8 w-24" />
                  <Skeleton className="h-8 w-16" />
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB]">
              <Skeleton className="h-6 w-24 mb-6" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </div>

            <div className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB]">
              <Skeleton className="h-6 w-24 mb-6" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F9FAFB]">
      <div className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
          <h1 className="text-[42px] md:text-[56px] font-semibold text-[#0F172A] mb-6 leading-tight">Resume Analysis</h1>
          <p className="text-lg md:text-xl text-[#64748B] font-normal leading-relaxed">Your personalized career insights powered by AI</p>
        </motion.div>
        
        {/* Health check banner */}
        {getHealthBanner()}

        {/* Score and Domains Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
          >
            <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Overall Score</h2>
            <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Your career readiness assessment</p>
            <ScoreDonut score={analysis.score || Math.round((analysis.domains[0]?.score || 0.5) * 100)} />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
          >
            <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Domains & Skills</h2>
            <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Your technical expertise mapped</p>
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-medium text-[#0F172A] mb-3">Top Domains</h4>
                <div className="flex flex-wrap gap-2">
                  {analysis.domains.map((domain, idx) => (
                    <span key={idx} className="px-3 py-1.5 bg-[#F9FAFB] text-[#0F172A] rounded-lg text-sm font-normal border border-[#E5E7EB]">
                      {domain.name} ({Math.round(domain.score * 100)}%)
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="text-sm font-medium text-[#0F172A] mb-3">Core Skills</h4>
                <div className="flex flex-wrap gap-2">
                  {analysis.skills.core.map((skill, idx) => (
                    <span key={idx} className="px-2.5 py-1 bg-[#F9FAFB] text-[#0F172A] rounded-md text-xs font-normal border border-[#E5E7EB]">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              {analysis.skills.adjacent.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-[#0F172A] mb-3">Adjacent Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.skills.adjacent.map((skill, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-[#F9FAFB] text-[#0F172A] rounded-md text-xs font-normal border border-[#E5E7EB]">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Strengths and Areas for Growth */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border-l-4 border-[#2563EB] border-t border-r border-b border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
          >
            <h2 className="text-2xl font-semibold text-[#0F172A] mb-6">Strengths</h2>
            <ul className="space-y-3">
              {analysis.strengths.map((strength, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm text-[#0F172A] font-normal">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#2563EB] flex-shrink-0"></div>
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border-l-4 border-[#F59E0B] border-t border-r border-b border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
          >
            <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Areas for Growth</h2>
            <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">
              {currentRole ? (
                <>Skills to develop for <span className="font-medium text-[#0F172A]">{currentRole}</span> role</>
              ) : (
                "Skills to develop based on your resume analysis"
              )}
            </p>
            <ul className="space-y-3">
              {(analysis.areas_for_growth || analysis.weaknesses || []).map((area, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm text-[#0F172A] font-normal">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#F59E0B] flex-shrink-0"></div>
                  <span>{area}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        </div>

        {/* Recommended Roles */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200 mb-6"
        >
          <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Recommended Roles</h2>
          <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Roles tailored to your experience and skills</p>
          <div className="flex flex-wrap gap-3">
            {(analysis.recommended_roles || analysis.suggestedRoles || analysis.domains.map(d => d.name)).map((role, idx) => (
              <button
                key={idx}
                onClick={() => {
                  navigate('/jobs', { state: { role } });
                  track('recommended_role_clicked', { role });
                }}
                className="px-4 py-2 bg-[#2563EB] text-white rounded-lg text-sm font-medium hover:bg-[#1d4ed8] transition-all duration-200 hover:scale-[1.02] cursor-pointer"
              >
                {role}
              </button>
            ))}
          </div>
        </motion.div>

        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] flex flex-col items-center gap-4"
        >
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="reminders"
              checked={reminders}
              onChange={(e) => setReminders(e.target.checked)}
              className="h-4 w-4 rounded border-[#E5E7EB] text-[#2563EB] focus:ring-[#2563EB]"
            />
            <label htmlFor="reminders" className="text-sm font-medium text-[#0F172A] cursor-pointer">
              Enable daily reminders for my learning plan
            </label>
          </div>
          <Button 
            onClick={handleGeneratePlan} 
            disabled={loading} 
            size="lg"
            className="bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
          >
            {loading ? (
              <>
                <Spinner className="mr-2" size="sm" />
                Generating Plan...
              </>
            ) : (
              'Generate Personalized Plan'
            )}
          </Button>
        </motion.div>
      </div>
    </div>
  );
};

