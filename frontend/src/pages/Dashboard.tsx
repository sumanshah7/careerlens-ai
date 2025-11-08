import { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { getPrediction } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { TrendingUp, FileText } from 'lucide-react';

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
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-1 w-12 bg-gradient-to-r from-primary to-primary/50 rounded-full"></div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Dashboard
            </h1>
          </div>
          <p className="text-muted-foreground text-lg">Your career progress at a glance</p>
        </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-primary/5 to-transparent">
          <CardHeader className="bg-gradient-to-r from-primary/10 to-transparent rounded-t-lg">
            <CardTitle className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse"></div>
              Current Score
            </CardTitle>
            <CardDescription>Your latest career readiness</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="text-5xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              {analysis?.score ?? (analysis?.domains?.[0] ? Math.round(analysis.domains[0].score * 100) : 'N/A')}
            </div>
            {analysis && (
              <p className="text-xs text-muted-foreground mt-2">
                Based on your resume analysis
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-blue-500/5 to-transparent">
          <CardHeader className="bg-gradient-to-r from-blue-500/10 to-transparent rounded-t-lg">
            <CardTitle className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500"></div>
              Jobs Found
            </CardTitle>
            <CardDescription>Matching opportunities</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">
              {jobs.length}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Tailored to your profile
            </p>
          </CardContent>
        </Card>

            <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-purple-500/5 to-transparent">
              <CardHeader className="bg-gradient-to-r from-purple-500/10 to-transparent rounded-t-lg">
                <CardTitle className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-purple-500"></div>
                  Plan Days
                </CardTitle>
                <CardDescription>Your learning journey</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-transparent">
                  {coach?.plan.length ?? 0}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Personalized coaching plan
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Resume Management Section */}
          {roles.length > 0 && (
            <Card className="border-2 shadow-lg mb-6 bg-gradient-to-br from-indigo-500/5 to-transparent">
              <CardHeader className="bg-gradient-to-r from-indigo-500/10 to-transparent rounded-t-lg">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-indigo-600" />
                  Your Resumes
                </CardTitle>
                <CardDescription>Manage resumes for different roles</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="space-y-3">
                  {roles.map((role) => {
                    const resume = resumes.find(r => r.role === role);
                    return (
                      <div key={role} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-indigo-500/20">
                        <div className="flex-1">
                          <div className="font-medium">{role}</div>
                          {resume && (
                            <div className="text-sm text-muted-foreground">
                              Score: {resume.analysis.score || Math.round((resume.analysis.domains?.[0]?.score || 0.5) * 100)} • Updated: {new Date(resume.updatedAt).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Link to="/progress">
                            <Button variant="outline" size="sm">
                              <TrendingUp className="h-4 w-4 mr-2" />
                              View Progress
                            </Button>
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                </div>
                {currentRole && (
                  <div className="mt-4 p-3 rounded-lg bg-primary/10 border border-primary/20">
                    <p className="text-sm text-muted-foreground">
                      Current role: <span className="font-medium text-foreground">{currentRole}</span>
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card className="border-2 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-indigo-500/10 to-transparent rounded-t-lg">
            <CardTitle className="flex items-center gap-2">
              <svg className="h-5 w-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Score Over Time
            </CardTitle>
            <CardDescription>Your progress trajectory</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={scoreData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" stroke="#6b7280" />
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
                  name="Career Score"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {prediction && (
          <Card className="border-2 shadow-lg bg-gradient-to-br from-green-500/5 to-transparent">
            <CardHeader className="bg-gradient-to-r from-green-500/10 to-transparent rounded-t-lg">
              <CardTitle className="flex items-center gap-2">
                <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                Growth Prediction
              </CardTitle>
              <CardDescription>Expected improvement after plan</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-6">
                <div className="p-4 rounded-lg bg-muted/50 border border-muted">
                  <div className="text-sm text-muted-foreground mb-2">Current Baseline</div>
                  <div className="text-3xl font-bold">{prediction.baseline}</div>
                </div>
                <div className="p-4 rounded-lg bg-gradient-to-r from-green-500/10 to-green-500/5 border border-green-500/20">
                  <div className="text-sm text-muted-foreground mb-2">After Plan</div>
                  <div className="text-3xl font-bold text-green-600">
                    {prediction.afterPlan}
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-gradient-to-r from-blue-500/10 to-blue-500/5 border border-blue-500/20">
                  <div className="text-sm text-muted-foreground mb-2">Expected Improvement</div>
                  <div className="text-3xl font-bold text-blue-600">
                    +{prediction.delta.toFixed(1)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
      </div>
    </div>
  );
};

