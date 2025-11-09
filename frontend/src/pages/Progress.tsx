import { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { TrendingUp, TrendingDown, ArrowRight, CheckCircle2, XCircle, Target, Zap, Award, AlertCircle, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ResumeProgress } from '../types';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { motion } from 'framer-motion';

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
      <div className="min-h-screen bg-[#F9FAFB]">
        <div className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="bg-white rounded-[16px] p-16 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] text-center"
          >
            <div className="mb-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-[#F9FAFB] flex items-center justify-center mb-4">
                <TrendingUp className="h-8 w-8 text-[#64748B]" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">No Resume Progress Yet</h3>
              <p className="text-[#64748B] mb-6 font-normal">
                Upload and analyze a resume to start tracking your progress
              </p>
            </div>
            <Button 
              onClick={() => navigate('/home')} 
              size="lg"
              className="bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
            >
              Upload Resume
            </Button>
          </motion.div>
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
    <div className="min-h-screen bg-[#F9FAFB]">
      <div className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
          <h1 className="text-[42px] md:text-[56px] font-semibold text-[#0F172A] mb-6 leading-tight">Resume Progress</h1>
          <p className="text-lg md:text-xl text-[#64748B] font-normal leading-relaxed">Track your resume improvements with detailed metrics</p>
        </motion.div>
        
        {/* Role Selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] mb-6"
        >
          <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Select Role</h2>
          <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Choose a role to view its progress</p>
          <Select value={selectedRole} onValueChange={handleRoleChange}>
            <SelectTrigger className="w-full max-w-md border-[#E5E7EB] rounded-lg">
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
        </motion.div>
        
        {progress.versions.length === 0 && selectedRole && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white rounded-[16px] p-16 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] text-center"
          >
            <div className="mb-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-[#F9FAFB] flex items-center justify-center mb-4">
                <TrendingUp className="h-8 w-8 text-[#64748B]" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">No Progress Data Yet</h3>
              <p className="text-[#64748B] mb-6 font-normal">
                Upload and analyze a new version of your resume to start tracking progress
              </p>
            </div>
            <Button 
              onClick={() => navigate('/home')} 
              size="lg"
              className="bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
            >
              Upload New Version
            </Button>
          </motion.div>
        )}
        
        {progress.versions.length > 0 && (
          <>
            {/* Enhanced Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
              >
                <h3 className="text-sm font-medium text-[#64748B] mb-2 flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Overall Score
                </h3>
                <div className={`text-5xl font-semibold ${getScoreColor(progress.currentScore)}`}>
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
                </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
              >
                <h3 className="text-sm font-medium text-[#64748B] mb-2 flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Versions
                </h3>
                <div className="text-5xl font-semibold text-[#2563EB]">{progress.versions.length}</div>
                <p className="text-sm text-[#64748B] mt-2 font-normal">Resume versions tracked</p>
                {progress.versions.length > 1 && (
                  <p className="text-xs text-[#64748B] mt-1 font-normal">
                    First: {new Date(progress.versions[0].date).toLocaleDateString()}
                  </p>
                )}
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.5 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
              >
                <h3 className="text-sm font-medium text-[#64748B] mb-2 flex items-center gap-2">
                  <Award className="h-4 w-4" />
                  Skill Improvements
                </h3>
                <div className="text-5xl font-semibold text-[#2563EB]">{progress.skillImprovements?.length || 0}</div>
                <p className="text-sm text-[#64748B] mt-2 font-normal">Skills upgraded</p>
                {progress.newSkills && progress.newSkills.length > 0 && (
                  <p className="text-xs text-[#16A34A] mt-1 font-normal">
                    +{progress.newSkills.length} new skills
                  </p>
                )}
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.6 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
              >
                <h3 className="text-sm font-medium text-[#64748B] mb-2 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Gaps Closed
                </h3>
                <div className="text-5xl font-semibold text-[#16A34A]">{progress.closedGaps?.length || 0}</div>
                <p className="text-sm text-[#64748B] mt-2 font-normal">Areas for growth addressed</p>
                {progress.closedGaps && progress.closedGaps.length > 0 && (
                  <p className="text-xs text-[#16A34A] mt-1 font-normal">Great progress!</p>
                )}
              </motion.div>
            </div>
            
            {/* Score Breakdown */}
            {progress.metrics && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.7 }}
              className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] mb-6"
            >
                <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Score Breakdown</h2>
                <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Detailed metrics that contribute to your overall score</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="p-4 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                      <div className="text-sm font-medium text-[#64748B] mb-1 font-normal">Domain Confidence</div>
                      <div className="text-3xl font-semibold text-[#2563EB]">{Math.round(progress.metrics.domainScore)}</div>
                      <div className="text-xs text-[#64748B] mt-1 font-normal">40% weight</div>
                    </div>
                    <div className="p-4 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                      <div className="text-sm font-medium text-[#64748B] mb-1 font-normal">Skills Coverage</div>
                      <div className="text-3xl font-semibold text-[#2563EB]">{Math.round(progress.metrics.skillsScore)}</div>
                      <div className="text-xs text-[#64748B] mt-1 font-normal">30% weight</div>
                    </div>
                    <div className="p-4 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                      <div className="text-sm font-medium text-[#64748B] mb-1 font-normal">Strengths Balance</div>
                      <div className="text-3xl font-semibold text-[#16A34A]">{Math.round(progress.metrics.balanceScore)}</div>
                      <div className="text-xs text-[#64748B] mt-1 font-normal">30% weight</div>
                    </div>
                  </div>
              </motion.div>
            )}
            
            {/* Progress Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.8 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
              >
              <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Score Over Time</h2>
                  <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Track your overall score improvements</p>
              <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="version" stroke="#64748B" />
                    <YAxis domain={[0, 100]} stroke="#64748B" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                        border: '1px solid #E5E7EB',
                        borderRadius: '8px'
                      }} 
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#2563EB"
                      strokeWidth={2}
                      dot={{ fill: '#2563EB', r: 4 }}
                      activeDot={{ r: 6 }}
                        name="Overall Score"
                    />
                  </LineChart>
                </ResponsiveContainer>
            </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.9 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
              >
                <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Skills Distribution</h2>
                  <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Core, Adjacent, and Advanced skills over time</p>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="version" stroke="#64748B" />
                      <YAxis stroke="#64748B" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                          border: '1px solid #E5E7EB',
                          borderRadius: '8px'
                        }} 
                      />
                      <Legend />
                      <Bar dataKey="core" stackId="a" fill="#2563EB" name="Core" />
                      <Bar dataKey="adjacent" stackId="a" fill="#8b5cf6" name="Adjacent" />
                      <Bar dataKey="advanced" stackId="a" fill="#16A34A" name="Advanced" />
                    </BarChart>
                  </ResponsiveContainer>
              </motion.div>
            </div>
            
            {/* Skill Improvements */}
            {progress.skillImprovements && progress.skillImprovements.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 1.0 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] mb-6"
              >
                <h2 className="text-2xl font-semibold text-[#0F172A] mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-[#16A34A]" />
                  Skill Improvements
                </h2>
                <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Skills that have advanced to higher categories</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {(progress.skillImprovements || []).map((improvement: any, idx: number) => (
                      <div key={idx} className="flex items-center gap-3 p-4 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] hover:bg-white transition-colors">
                        <div className="flex-shrink-0">
                          <ArrowUpRight className="h-5 w-5 text-[#16A34A]" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-[#0F172A] truncate">{improvement.skill}</div>
                          <div className="text-sm text-[#64748B] flex items-center gap-1 mt-1">
                            <span className="px-2 py-0.5 rounded bg-[#F9FAFB] text-[#64748B] text-xs border border-[#E5E7EB]">
                              {improvement.previousStatus}
                            </span>
                            <ArrowRight className="h-3 w-3" />
                            <span className="px-2 py-0.5 rounded bg-[#f0fdf4] text-[#16A34A] text-xs border border-[#86efac]">
                              {improvement.currentStatus}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
              </motion.div>
            )}
            
            {/* New Skills */}
            {progress.newSkills && progress.newSkills.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 1.1 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] mb-6"
              >
                <h2 className="text-2xl font-semibold text-[#0F172A] mb-3 flex items-center gap-2">
                  <Zap className="h-5 w-5 text-[#2563EB]" />
                  New Skills Added
                </h2>
                <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Skills that were added in the latest version</p>
                  <div className="flex flex-wrap gap-2">
                    {(progress.newSkills || []).map((skill: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 rounded-lg bg-[#F9FAFB] text-[#0F172A] text-sm font-normal border border-[#E5E7EB]"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
              </motion.div>
            )}
            
            {/* Closed Gaps */}
            {progress.closedGaps && progress.closedGaps.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 1.2 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] mb-6"
              >
                <h2 className="text-2xl font-semibold text-[#0F172A] mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-[#16A34A]" />
                  Areas for Growth Closed
                </h2>
                <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Gaps that have been addressed in your latest version</p>
                  <div className="flex flex-wrap gap-2">
                    {(progress.closedGaps || []).map((gap: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 rounded-lg bg-[#f0fdf4] text-[#16A34A] text-sm font-medium border border-[#86efac] flex items-center gap-1"
                      >
                        <CheckCircle2 className="h-3 w-3" />
                        {gap}
                      </span>
                    ))}
                  </div>
              </motion.div>
            )}
            
            {/* Domain Changes */}
            {progress.domainChanges && progress.domainChanges.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 1.3 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] mb-6"
              >
                <h2 className="text-2xl font-semibold text-[#0F172A] mb-3 flex items-center gap-2">
                  <Target className="h-5 w-5 text-[#64748B]" />
                  Domain Confidence Changes
                </h2>
                <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">How your domain confidence scores have changed</p>
                  <div className="space-y-3">
                    {(progress.domainChanges || []).map((change: any, idx: number) => {
                      const diff = change.currentScore - change.previousScore;
                      return (
                        <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                          <div className="flex-1">
                            <div className="font-medium text-[#0F172A]">{change.domain}</div>
                            <div className="text-sm text-[#64748B] font-normal">
                              Confidence score change
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-[#64748B] font-normal">{change.previousScore}%</span>
                            <ArrowRight className="h-4 w-4 text-[#64748B]" />
                            <span className={`text-lg font-semibold ${diff > 0 ? 'text-[#16A34A]' : diff < 0 ? 'text-red-600' : 'text-[#64748B]'}`}>
                              {change.currentScore}%
                            </span>
                            {diff !== 0 && (
                              <span className={`text-sm font-medium ${diff > 0 ? 'text-[#16A34A]' : 'text-red-600'}`}>
                                {diff > 0 ? '+' : ''}{diff}%
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
              </motion.div>
            )}
            
            {/* Insights */}
            {progress.versions.length > 1 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 1.4 }}
                className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB]"
              >
                <h2 className="text-2xl font-semibold text-[#0F172A] mb-3 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-[#64748B]" />
                  Progress Insights
                </h2>
                <div className="space-y-3">
                    {progress.scoreChange !== null && progress.scoreChange > 0 && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-[#f0fdf4] border border-[#86efac]">
                        <CheckCircle2 className="h-5 w-5 text-[#16A34A] mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-[#0F172A]">
                            Score Improved by {progress.scoreChange} points
                          </div>
                          <div className="text-sm text-[#64748B] font-normal">
                            Your resume is getting stronger! Keep up the great work.
                          </div>
                        </div>
                      </div>
                    )}
                    {progress.skillImprovements && progress.skillImprovements.length > 0 && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-[#eff6ff] border border-[#93c5fd]">
                        <Award className="h-5 w-5 text-[#2563EB] mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-[#0F172A]">
                            {progress.skillImprovements.length} skill{progress.skillImprovements.length > 1 ? 's' : ''} upgraded
                          </div>
                          <div className="text-sm text-[#64748B] font-normal">
                            Skills are advancing to higher categories, showing real growth.
                          </div>
                        </div>
                      </div>
                    )}
                    {progress.closedGaps && progress.closedGaps.length > 0 && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-[#f0fdf4] border border-[#86efac]">
                        <CheckCircle2 className="h-5 w-5 text-[#16A34A] mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-[#0F172A]">
                            {progress.closedGaps.length} gap{progress.closedGaps.length > 1 ? 's' : ''} closed
                          </div>
                          <div className="text-sm text-[#64748B] font-normal">
                            You've addressed areas for growth - excellent progress!
                          </div>
                        </div>
                      </div>
                    )}
                    {progress.newSkills && progress.newSkills.length > 0 && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-[#f3e8ff] border border-[#c4b5fd]">
                        <Zap className="h-5 w-5 text-[#8b5cf6] mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-[#0F172A]">
                            {progress.newSkills.length} new skill{progress.newSkills.length > 1 ? 's' : ''} added
                          </div>
                          <div className="text-sm text-[#64748B] font-normal">
                            Expanding your skill set is key to career growth.
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
              </motion.div>
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
