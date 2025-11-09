import { useAppStore } from '../store/useAppStore';
import { autoCoach, checkHealth, getRoleMatchScore } from '../lib/api';
import { track } from '../lib/analytics';
import { ScoreDonut } from '../components/ScoreDonut';
import { SkillChips } from '../components/SkillChips';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { Spinner } from '../components/ui/spinner';
import { toast } from 'sonner';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const Analysis = () => {
  const { analysis, setCoach, resumeText, currentRole } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [reminders, setReminders] = useState(false);
  const [roleMatchScore, setRoleMatchScore] = useState<number | null>(null);
  const [roleMatchLoading, setRoleMatchLoading] = useState(false);
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
      
      // Fetch role-specific match score if we have resume text and target role
      if (resumeText && currentRole) {
        setRoleMatchLoading(true);
        getRoleMatchScore(resumeText, currentRole)
          .then((result) => {
            setRoleMatchScore(result.score);
            console.log('📊 Role match score:', result.score, 'for role:', currentRole);
          })
          .catch((error) => {
            console.error('❌ Failed to fetch role match score:', error);
            setRoleMatchScore(null);
          })
          .finally(() => {
            setRoleMatchLoading(false);
          });
      }
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
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
        <div className="container mx-auto px-4 py-8 max-w-6xl">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-1 w-12 bg-gradient-to-r from-primary to-primary/50 rounded-full"></div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                Resume Analysis
              </h1>
            </div>
            <p className="text-muted-foreground text-lg">Your personalized career insights powered by AI</p>
          </div>
          
          <Card className="border-2 shadow-lg">
            <CardContent className="py-16 text-center">
              <div className="mb-6">
                <div className="mx-auto h-16 w-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center mb-4">
                  <svg className="h-8 w-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">No analysis yet</h3>
                <p className="text-muted-foreground mb-6">
                  Upload and analyze your resume to get started
                </p>
              </div>
              <Button 
                onClick={() => navigate('/home')} 
                size="lg"
                className="bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg hover:shadow-xl transition-all"
              >
                Go to Resume Upload
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (initialLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-6">
          <Skeleton className="h-10 w-64 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32 mb-2" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center h-[300px]">
                <Spinner size="lg" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32 mb-2" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Skeleton className="h-4 w-24" />
                <div className="flex flex-wrap gap-2">
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-8 w-24" />
                  <Skeleton className="h-8 w-16" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-24" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-24" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header with gradient */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-1 w-12 bg-gradient-to-r from-primary to-primary/50 rounded-full"></div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Resume Analysis
            </h1>
          </div>
          <p className="text-muted-foreground text-lg">Your personalized career insights powered by AI</p>
        </div>
        
        {/* Health check banner */}
        {getHealthBanner()}

        {/* Score Card with enhanced design */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="bg-gradient-to-br from-primary/5 to-primary/10 rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-primary animate-pulse"></div>
                Overall Score
              </CardTitle>
              <CardDescription>Your career readiness assessment</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <ScoreDonut score={analysis.score || Math.round((analysis.domains[0]?.score || 0.5) * 100)} />
            </CardContent>
          </Card>

          {currentRole && (
            <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="bg-gradient-to-br from-green-500/5 to-green-500/10 rounded-t-lg">
                <CardTitle className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                  Role Match Score
                </CardTitle>
                <CardDescription>
                  Match against: <span className="font-semibold text-green-600 dark:text-green-400">{currentRole}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {roleMatchLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <Spinner className="h-8 w-8" />
                  </div>
                ) : roleMatchScore !== null ? (
                  <ScoreDonut score={roleMatchScore} />
                ) : (
                  <div className="flex items-center justify-center h-32 text-muted-foreground">
                    <p className="text-sm">Unable to calculate match score</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="bg-gradient-to-br from-blue-500/5 to-blue-500/10 rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                Domains & Skills
              </CardTitle>
              <CardDescription>Your technical expertise mapped</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold mb-2">Top Domains</h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.domains.map((domain, idx) => (
                      <span key={idx} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">
                        {domain.name} ({Math.round(domain.score * 100)}%)
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-2">Core Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.skills.core.map((skill, idx) => (
                      <span key={idx} className="px-2 py-1 bg-green-500/10 text-green-700 dark:text-green-400 rounded text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                {analysis.skills.adjacent.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Adjacent Skills</h4>
                    <div className="flex flex-wrap gap-2">
                      {analysis.skills.adjacent.map((skill, idx) => (
                        <span key={idx} className="px-2 py-1 bg-blue-500/10 text-blue-700 dark:text-blue-400 rounded text-xs">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Strengths and Weaknesses with better visuals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card className="border-2 border-green-500/20 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-green-500/5 to-transparent">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Strengths
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {analysis.strengths.map((strength, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm">
                    <div className="mt-1 h-1.5 w-1.5 rounded-full bg-green-500 flex-shrink-0"></div>
                    <span className="text-foreground">{strength}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="border-2 border-amber-500/20 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-amber-500/5 to-transparent">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Areas for Growth
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {(analysis.areas_for_growth || analysis.weaknesses || []).map((area, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm">
                    <div className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 flex-shrink-0"></div>
                    <span className="text-foreground">{area}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Suggested Roles with enhanced design */}
        <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow mb-6 bg-gradient-to-br from-purple-500/5 to-transparent">
          <CardHeader className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-t-lg">
            <CardTitle className="flex items-center gap-2">
              <svg className="h-5 w-5 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
              </svg>
              Recommended Roles
            </CardTitle>
            <CardDescription>Roles tailored to your experience and skills</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="flex flex-wrap gap-3">
              {(analysis.recommended_roles || analysis.suggestedRoles || analysis.domains.map(d => d.name)).map((role, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    // Navigate to Jobs page with this role pre-filled
                    navigate('/jobs', { state: { role } });
                    track('recommended_role_clicked', { role });
                  }}
                  className="px-4 py-2 bg-gradient-to-r from-primary/10 to-primary/5 text-primary border border-primary/20 rounded-lg text-sm font-medium hover:from-primary/20 hover:to-primary/10 hover:border-primary/40 transition-all cursor-pointer shadow-sm hover:shadow-md"
                >
                  {role}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* CTA Section */}
        <div className="mt-8 flex flex-col items-center gap-4 p-6 rounded-xl bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border border-primary/20">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="reminders"
              checked={reminders}
              onChange={(e) => setReminders(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <label htmlFor="reminders" className="text-sm font-medium cursor-pointer">
              Enable daily reminders for my learning plan
            </label>
          </div>
          <Button 
            onClick={handleGeneratePlan} 
            disabled={loading} 
            size="lg"
            className="bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg hover:shadow-xl transition-all"
          >
            {loading ? (
              <>
                <Spinner className="mr-2" size="sm" />
                Generating Plan...
              </>
            ) : (
              <>
                <svg className="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Generate Personalized Plan
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

