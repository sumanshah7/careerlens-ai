import { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { TrendingUp, TrendingDown, ArrowRight, CheckCircle2, XCircle, Target, Zap, Award, AlertCircle, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ResumeProgress } from '../types';
import { ErrorBoundary } from '../components/ErrorBoundary';

// ProgressModel with safe defaults
interface ProgressModel {
  newSkills: string[];
  closedGaps: string[];
  skillImprovements: Array<{ skill: string; previousStatus: string; currentStatus: string }>;
  domainChanges: Array<{ domain: string; previousScore: number; currentScore: number }>;
  versions: Array<{ date: string; score: number; skillsCount: number; strengthsCount: number; weaknessesCount: number; coreSkillsCount?: number; adjacentSkillsCount?: number; advancedSkillsCount?: number; metrics?: { domainScore: number; skillsScore: number; balanceScore: number } }>;
  currentScore: number;
  previousScore: number | null;
  scoreChange: number | null;
  scoreChangePercent: number | null;
  metrics?: { domainScore: number; skillsScore: number; balanceScore: number };
}

// Normalize progress data with safe defaults
const normalizeProgress = (progress: ResumeProgress | null): ProgressModel => {
  if (!progress) {
    return {
      newSkills: [],
      closedGaps: [],
      skillImprovements: [],
      domainChanges: [],
      versions: [],
      currentScore: 0,
      previousScore: null,
      scoreChange: null,
      scoreChangePercent: null,
      metrics: undefined,
    };
  }

  return {
    newSkills: Array.isArray(progress.newSkills) ? progress.newSkills : [],
    closedGaps: Array.isArray(progress.closedGaps) ? progress.closedGaps : [],
    skillImprovements: Array.isArray(progress.skillImprovements) ? progress.skillImprovements : [],
    domainChanges: Array.isArray(progress.domainChanges) ? progress.domainChanges : [],
    versions: Array.isArray(progress.versions) ? progress.versions : [],
    currentScore: progress.currentScore || 0,
    previousScore: progress.previousScore ?? null,
    scoreChange: progress.scoreChange ?? null,
    scoreChangePercent: progress.scoreChangePercent ?? null,
    metrics: progress.metrics || undefined,
  };
};

const ProgressContent = () => {
  const { resumes, getAllRoles, getResumeProgress, loadResume } = useAppStore();
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [rawProgress, setRawProgress] = useState<ResumeProgress | null>(null);
  const navigate = useNavigate();
  
  // Normalize progress with safe defaults
  const progress = normalizeProgress(rawProgress);
  
  const roles = getAllRoles();
  
  useEffect(() => {
    if (roles.length > 0 && !selectedRole) {
      setSelectedRole(roles[0]);
    }
  }, [roles, selectedRole]);
  
  useEffect(() => {
    if (selectedRole) {
      const resume = resumes.find(r => r.role === selectedRole);
      if (resume) {
        const progressData = getResumeProgress(resume.id);
        setRawProgress(progressData);
      } else {
        setRawProgress(null);
      }
    } else {
      setRawProgress(null);
    }
  }, [selectedRole, resumes, getResumeProgress]);
  
  const handleRoleChange = (role: string) => {
    setSelectedRole(role);
    const resume = resumes.find(r => r.role === role);
    if (resume) {
      loadResume(resume.id);
    }
  };
  
  if (roles.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
        <div className="container mx-auto px-4 py-8 max-w-6xl">
          <Card className="border-2 shadow-lg">
            <CardContent className="py-16 text-center">
              <div className="mb-6">
                <div className="mx-auto h-16 w-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center mb-4">
                  <TrendingUp className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">No Resume Progress Yet</h3>
                <p className="text-muted-foreground mb-6">
                  Upload and analyze a resume to start tracking your progress
                </p>
              </div>
              <Button onClick={() => navigate('/home')} size="lg">
                Upload Resume
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }
  
  const chartData = progress.versions.map((v: any, index: number) => ({
    version: `v${index + 1}`,
    score: v.score,
    skills: v.skillsCount,
    strengths: v.strengthsCount,
    weaknesses: v.weaknessesCount,
    core: v.coreSkillsCount || 0,
    adjacent: v.adjacentSkillsCount || 0,
    advanced: v.advancedSkillsCount || 0,
    date: new Date(v.date).toLocaleDateString(),
  })) || [];
  
  const metricsData = progress.versions.length > 0 ? [
    {
      name: 'Domain',
      current: progress.metrics?.domainScore || 0,
      previous: progress.previousScore !== null ? (progress.metrics?.domainScore || 0) : 0,
    },
    {
      name: 'Skills',
      current: progress.metrics?.skillsScore || 0,
      previous: progress.previousScore !== null ? (progress.metrics?.skillsScore || 0) : 0,
    },
    {
      name: 'Balance',
      current: progress.metrics?.balanceScore || 0,
      previous: progress.previousScore !== null ? (progress.metrics?.balanceScore || 0) : 0,
    },
  ] : [];
  
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };
  
  const getScoreBadge = (score: number) => {
    if (score >= 80) return { label: 'Excellent', color: 'bg-green-100 text-green-800' };
    if (score >= 60) return { label: 'Good', color: 'bg-blue-100 text-blue-800' };
    if (score >= 40) return { label: 'Fair', color: 'bg-yellow-100 text-yellow-800' };
    return { label: 'Needs Work', color: 'bg-red-100 text-red-800' };
  };
  
  const scoreBadge = getScoreBadge(progress.currentScore);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-1 w-12 bg-gradient-to-r from-primary to-primary/50 rounded-full"></div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Resume Progress
            </h1>
          </div>
          <p className="text-muted-foreground text-lg">Track your resume improvements with detailed metrics</p>
        </div>
        
        {/* Role Selector */}
        <Card className="mb-6 border-2 shadow-lg">
          <CardHeader>
            <CardTitle>Select Role</CardTitle>
            <CardDescription>Choose a role to view its progress</CardDescription>
          </CardHeader>
          <CardContent>
            <Select value={selectedRole} onValueChange={handleRoleChange}>
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                {roles.map((role) => (
                  <SelectItem key={role} value={role}>
                    {role}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
        
        {progress.versions.length === 0 && selectedRole && (
          <Card className="border-2 shadow-lg">
            <CardContent className="py-16 text-center">
              <div className="mb-6">
                <div className="mx-auto h-16 w-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center mb-4">
                  <TrendingUp className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">No Progress Data Yet</h3>
                <p className="text-muted-foreground mb-6">
                  Upload and analyze a new version of your resume to start tracking progress
                </p>
              </div>
              <Button onClick={() => navigate('/home')} size="lg">
                Upload New Version
              </Button>
            </CardContent>
          </Card>
        )}
        
        {progress.versions.length > 0 && (
          <>
            {/* Enhanced Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              <Card className="border-2 shadow-lg bg-gradient-to-br from-primary/5 to-transparent">
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    Overall Score
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-5xl font-bold ${getScoreColor(progress.currentScore)}`}>
                    {progress.currentScore}
                  </div>
                  {scoreBadge && (
                    <div className={`mt-2 inline-block px-2 py-1 rounded text-xs font-medium ${scoreBadge.color}`}>
                      {scoreBadge.label}
                    </div>
                  )}
                  {progress.previousScore !== null && progress.previousScore !== undefined && (
                    <div className="flex items-center gap-2 mt-3">
                      {progress.scoreChange !== null && progress.scoreChange > 0 ? (
                        <>
                          <TrendingUp className="h-4 w-4 text-green-600" />
                          <span className="text-sm font-medium text-green-600">
                            +{progress.scoreChange} points
                            {progress.scoreChangePercent && ` (+${progress.scoreChangePercent}%)`}
                          </span>
                        </>
                      ) : progress.scoreChange !== null && progress.scoreChange < 0 ? (
                        <>
                          <TrendingDown className="h-4 w-4 text-red-600" />
                          <span className="text-sm font-medium text-red-600">
                            {progress.scoreChange} points
                            {progress.scoreChangePercent && ` (${progress.scoreChangePercent}%)`}
                          </span>
                        </>
                      ) : (
                        <>
                          <Minus className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">No change</span>
                        </>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
              
              <Card className="border-2 shadow-lg bg-gradient-to-br from-blue-500/5 to-transparent">
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    Versions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-5xl font-bold text-blue-600">{progress.versions.length}</div>
                  <p className="text-sm text-muted-foreground mt-2">Resume versions tracked</p>
                  {progress.versions.length > 1 && (
                    <p className="text-xs text-muted-foreground mt-1">
                      First: {new Date(progress.versions[0].date).toLocaleDateString()}
                    </p>
                  )}
                </CardContent>
              </Card>
              
              <Card className="border-2 shadow-lg bg-gradient-to-br from-purple-500/5 to-transparent">
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Award className="h-4 w-4" />
                    Skill Improvements
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-5xl font-bold text-purple-600">{progress.skillImprovements?.length || 0}</div>
                  <p className="text-sm text-muted-foreground mt-2">Skills upgraded</p>
                  {progress.newSkills && progress.newSkills.length > 0 && (
                    <p className="text-xs text-green-600 mt-1">
                      +{progress.newSkills.length} new skills
                    </p>
                  )}
                </CardContent>
              </Card>
              
              <Card className="border-2 shadow-lg bg-gradient-to-br from-green-500/5 to-transparent">
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Gaps Closed
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-5xl font-bold text-green-600">{progress.closedGaps?.length || 0}</div>
                  <p className="text-sm text-muted-foreground mt-2">Areas for growth addressed</p>
                  {progress.closedGaps && progress.closedGaps.length > 0 && (
                    <p className="text-xs text-green-600 mt-1">Great progress!</p>
                  )}
                </CardContent>
              </Card>
            </div>
            
            {/* Score Breakdown */}
            {progress.metrics && (
            <Card className="mb-6 border-2 shadow-lg">
                <CardHeader>
                  <CardTitle>Score Breakdown</CardTitle>
                  <CardDescription>Detailed metrics that contribute to your overall score</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                      <div className="text-sm font-medium text-muted-foreground mb-1">Domain Confidence</div>
                      <div className="text-3xl font-bold text-blue-600">{Math.round(progress.metrics.domainScore)}</div>
                      <div className="text-xs text-muted-foreground mt-1">40% weight</div>
                    </div>
                    <div className="p-4 rounded-lg bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800">
                      <div className="text-sm font-medium text-muted-foreground mb-1">Skills Coverage</div>
                      <div className="text-3xl font-bold text-purple-600">{Math.round(progress.metrics.skillsScore)}</div>
                      <div className="text-xs text-muted-foreground mt-1">30% weight</div>
                    </div>
                    <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800">
                      <div className="text-sm font-medium text-muted-foreground mb-1">Strengths Balance</div>
                      <div className="text-3xl font-bold text-green-600">{Math.round(progress.metrics.balanceScore)}</div>
                      <div className="text-xs text-muted-foreground mt-1">30% weight</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Progress Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <Card className="border-2 shadow-lg">
              <CardHeader>
                <CardTitle>Score Over Time</CardTitle>
                  <CardDescription>Track your overall score improvements</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="version" stroke="#6b7280" />
                    <YAxis domain={[0, 100]} stroke="#6b7280" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px'
                      }} 
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#6366f1"
                      strokeWidth={3}
                      dot={{ fill: '#6366f1', r: 5 }}
                      activeDot={{ r: 7 }}
                        name="Overall Score"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
              
              <Card className="border-2 shadow-lg">
                <CardHeader>
                  <CardTitle>Skills Distribution</CardTitle>
                  <CardDescription>Core, Adjacent, and Advanced skills over time</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="version" stroke="#6b7280" />
                      <YAxis stroke="#6b7280" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px'
                        }} 
                      />
                      <Legend />
                      <Bar dataKey="core" stackId="a" fill="#3b82f6" name="Core" />
                      <Bar dataKey="adjacent" stackId="a" fill="#8b5cf6" name="Adjacent" />
                      <Bar dataKey="advanced" stackId="a" fill="#10b981" name="Advanced" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
            
            {/* Skill Improvements */}
            {progress.skillImprovements && progress.skillImprovements.length > 0 && (
              <Card className="mb-6 border-2 shadow-lg bg-gradient-to-br from-green-500/5 to-transparent">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    Skill Improvements
                  </CardTitle>
                  <CardDescription>Skills that have advanced to higher categories</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {(progress.skillImprovements || []).map((improvement: any, idx: number) => (
                      <div key={idx} className="flex items-center gap-3 p-4 rounded-lg bg-muted/50 border border-green-500/20 hover:border-green-500/40 transition-colors">
                        <div className="flex-shrink-0">
                          <ArrowUpRight className="h-5 w-5 text-green-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">{improvement.skill}</div>
                          <div className="text-sm text-muted-foreground flex items-center gap-1">
                            <span className="px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs">
                              {improvement.previousStatus}
                            </span>
                            <ArrowRight className="h-3 w-3" />
                            <span className="px-2 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs">
                              {improvement.currentStatus}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* New Skills */}
            {progress.newSkills && progress.newSkills.length > 0 && (
              <Card className="mb-6 border-2 shadow-lg bg-gradient-to-br from-blue-500/5 to-transparent">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-blue-600" />
                    New Skills Added
                  </CardTitle>
                  <CardDescription>Skills that were added in the latest version</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {(progress.newSkills || []).map((skill: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium border border-blue-200 dark:border-blue-800"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Closed Gaps */}
            {progress.closedGaps && progress.closedGaps.length > 0 && (
              <Card className="mb-6 border-2 shadow-lg bg-gradient-to-br from-green-500/5 to-transparent">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    Areas for Growth Closed
                  </CardTitle>
                  <CardDescription>Gaps that have been addressed in your latest version</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {(progress.closedGaps || []).map((gap: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm font-medium border border-green-200 dark:border-green-800 flex items-center gap-1"
                      >
                        <CheckCircle2 className="h-3 w-3" />
                        {gap}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Domain Changes */}
            {progress.domainChanges && progress.domainChanges.length > 0 && (
              <Card className="mb-6 border-2 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Domain Confidence Changes
                  </CardTitle>
                  <CardDescription>How your domain confidence scores have changed</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(progress.domainChanges || []).map((change: any, idx: number) => {
                      const diff = change.currentScore - change.previousScore;
                      return (
                        <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border">
                          <div className="flex-1">
                            <div className="font-medium">{change.domain}</div>
                            <div className="text-sm text-muted-foreground">
                              Confidence score change
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-muted-foreground">{change.previousScore}%</span>
                            <ArrowRight className="h-4 w-4 text-muted-foreground" />
                            <span className={`text-lg font-bold ${diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-muted-foreground'}`}>
                              {change.currentScore}%
                            </span>
                            {diff !== 0 && (
                              <span className={`text-sm font-medium ${diff > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {diff > 0 ? '+' : ''}{diff}%
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Insights */}
            {progress.versions.length > 1 && (
              <Card className="border-2 shadow-lg bg-gradient-to-br from-primary/5 to-transparent">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertCircle className="h-5 w-5" />
                    Progress Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {progress.scoreChange !== null && progress.scoreChange > 0 && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800">
                        <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-green-900 dark:text-green-100">
                            Score Improved by {progress.scoreChange} points
                          </div>
                          <div className="text-sm text-green-700 dark:text-green-300">
                            Your resume is getting stronger! Keep up the great work.
                          </div>
                        </div>
                      </div>
                    )}
                    {progress.skillImprovements && progress.skillImprovements.length > 0 && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                        <Award className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-blue-900 dark:text-blue-100">
                            {progress.skillImprovements.length} skill{progress.skillImprovements.length > 1 ? 's' : ''} upgraded
                          </div>
                          <div className="text-sm text-blue-700 dark:text-blue-300">
                            Skills are advancing to higher categories, showing real growth.
                          </div>
                        </div>
                      </div>
                    )}
                    {progress.closedGaps && progress.closedGaps.length > 0 && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800">
                        <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-green-900 dark:text-green-100">
                            {progress.closedGaps.length} gap{progress.closedGaps.length > 1 ? 's' : ''} closed
                          </div>
                          <div className="text-sm text-green-700 dark:text-green-300">
                            You've addressed areas for growth - excellent progress!
                          </div>
                        </div>
                      </div>
                    )}
                    {progress.newSkills && progress.newSkills.length > 0 && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800">
                        <Zap className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-purple-900 dark:text-purple-100">
                            {progress.newSkills.length} new skill{progress.newSkills.length > 1 ? 's' : ''} added
                          </div>
                          <div className="text-sm text-purple-700 dark:text-purple-300">
                            Expanding your skill set is key to career growth.
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// Export Progress component wrapped with ErrorBoundary
export const Progress = () => {
  return (
    <ErrorBoundary>
      <ProgressContent />
    </ErrorBoundary>
  );
};
