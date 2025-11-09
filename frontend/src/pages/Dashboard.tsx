import { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { getPrediction } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { TrendingUp, FileText, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

export const Dashboard = () => {
  const { analysis, jobs, coach, getAllRoles, resumes, currentRole } = useAppStore();
  const [prediction, setPrediction] = useState<any>(null);
  const roles = getAllRoles();

  useEffect(() => {
    const fetchPrediction = async () => {
      if (!analysis) return;
      
      // Extract skills from analysis - skills is now an object with core/adjacent/advanced arrays
      const allSkills = [
        ...(analysis.skills?.core || []),
        ...(analysis.skills?.adjacent || []),
        ...(analysis.skills?.advanced || [])
      ];
      
      // For prediction, use all skills as "have" and areas_for_growth as "gap"
      const skillsHave = allSkills || [];
      const skillsGap = analysis.areas_for_growth || analysis.weaknesses || [];
      
      const pred = await getPrediction(skillsHave, skillsGap);
      setPrediction(pred);
    };
    fetchPrediction();
  }, [analysis]);

  // Mock score over time data
  const scoreData = [
    { date: 'Week 1', score: 65 },
    { date: 'Week 2', score: 68 },
    { date: 'Week 3', score: 72 },
    { date: 'Week 4', score: 75 },
    { date: 'Week 5', score: 78 },
    { date: 'Week 6', score: 82 },
  ];

  return (
    <div className="min-h-screen bg-[#F9FAFB]">
      <div className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
          <h1 className="text-[42px] md:text-[56px] font-semibold text-[#0F172A] mb-6 leading-tight">Dashboard</h1>
          <p className="text-lg md:text-xl text-[#64748B] font-normal leading-relaxed">Your career progress at a glance</p>
        </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
        >
          <h2 className="text-sm font-medium text-[#64748B] mb-2">Current Score</h2>
          <p className="text-xs text-[#64748B] mb-4 font-normal">Your latest career readiness</p>
          <div className="text-5xl font-semibold text-[#0F172A]">
            {analysis?.score ?? (analysis?.domains?.[0] ? Math.round(analysis.domains[0].score * 100) : 'N/A')}
          </div>
          {analysis && (
            <p className="text-xs text-[#64748B] mt-2 font-normal">
              Based on your resume analysis
            </p>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
        >
          <h2 className="text-sm font-medium text-[#64748B] mb-2">Jobs Found</h2>
          <p className="text-xs text-[#64748B] mb-4 font-normal">Matching opportunities</p>
          <div className="text-5xl font-semibold text-[#0F172A]">
            {jobs.length}
          </div>
          <p className="text-xs text-[#64748B] mt-2 font-normal">
            Tailored to your profile
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
        >
          <h2 className="text-sm font-medium text-[#64748B] mb-2">Plan Days</h2>
          <p className="text-xs text-[#64748B] mb-4 font-normal">Your learning journey</p>
          <div className="text-5xl font-semibold text-[#0F172A]">
            {coach?.plan?.length ?? 0}
          </div>
          <p className="text-xs text-[#64748B] mt-2 font-normal">
            Personalized coaching plan
          </p>
        </motion.div>
      </div>

          {/* Resume Management Section */}
          {roles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200 mb-6"
            >
              <h2 className="text-2xl font-semibold text-[#0F172A] mb-3 flex items-center gap-2">
                <FileText className="h-5 w-5 text-[#64748B]" />
                Your Resumes
              </h2>
              <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Manage resumes for different roles</p>
              <div className="space-y-3">
                {roles.map((role) => {
                  const resume = resumes.find(r => r.role === role);
                  return (
                    <div key={role} className="flex items-center justify-between p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] hover:bg-white transition-colors">
                      <div className="flex-1">
                        <div className="font-medium text-[#0F172A]">{role}</div>
                        {resume && (
                          <div className="text-sm text-[#64748B] font-normal">
                            Score: {resume.analysis.score || Math.round((resume.analysis.domains?.[0]?.score || 0.5) * 100)} • Updated: {new Date(resume.updatedAt).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Link to="/progress">
                          <Button variant="outline" size="sm" className="border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200 hover:scale-[1.02]">
                            <TrendingUp className="h-4 w-4 mr-2" />
                            View Progress
                            <ChevronRight className="h-4 w-4 ml-2" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
              {currentRole && (
                <div className="mt-4 p-3 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                  <p className="text-sm text-[#64748B] font-normal">
                    Current role: <span className="font-medium text-[#0F172A]">{currentRole}</span>
                  </p>
                </div>
              )}
            </motion.div>
          )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
        >
          <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Score Over Time</h2>
          <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Your progress trajectory</p>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={scoreData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="date" stroke="#64748B" />
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
                name="Career Score"
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        {prediction && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
        >
          <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Growth Prediction</h2>
          <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Expected improvement after plan</p>
          <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#F9FAFB] border border-[#E5E7EB]">
                <div className="text-sm text-[#64748B] mb-2 font-normal">Current Baseline</div>
                <div className="text-3xl font-semibold text-[#0F172A]">{prediction.baseline}</div>
              </div>
              <div className="p-4 rounded-lg bg-[#f0fdf4] border border-[#86efac]">
                <div className="text-sm text-[#64748B] mb-2 font-normal">After Plan</div>
                <div className="text-3xl font-semibold text-[#16A34A]">
                  {prediction.afterPlan}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-[#eff6ff] border border-[#93c5fd]">
                <div className="text-sm text-[#64748B] mb-2 font-normal">Expected Improvement</div>
                <div className="text-3xl font-semibold text-[#2563EB]">
                  +{prediction.delta.toFixed(1)}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
      </div>
    </div>
  );
};

