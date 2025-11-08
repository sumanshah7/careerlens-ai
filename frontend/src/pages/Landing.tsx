import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { BarChart3, Briefcase, BookOpen, Target, Zap, Shield } from 'lucide-react';

export const Landing = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-muted/20">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <div className="mb-6">
            <div className="inline-block mb-4">
              <div className="h-2 w-24 bg-gradient-to-r from-primary to-primary/50 rounded-full mx-auto mb-2"></div>
            </div>
            <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent animate-pulse">
              CareerLens AI
            </h1>
            <div className="h-2 w-24 bg-gradient-to-r from-primary/50 to-primary rounded-full mx-auto"></div>
          </div>
          <p className="text-2xl text-muted-foreground mb-4 max-w-3xl mx-auto font-medium">
            Your AI-powered career companion
          </p>
          <p className="text-lg text-muted-foreground/80 mb-10 max-w-2xl mx-auto">
            Analyze your resume, find matching jobs, tailor your applications, 
            and get personalized coaching to advance your career.
          </p>
          <div className="flex gap-4 justify-center">
            <Link to="/login">
              <Button size="lg" className="bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg hover:shadow-xl transition-all text-lg px-8 py-6">
                Get Started
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="border-2 text-lg px-8 py-6 hover:bg-primary/5 transition-all">
                Sign In
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <Card className="border-2 shadow-lg hover:shadow-xl transition-all bg-gradient-to-br from-card to-card/50 hover:border-primary/30">
            <CardHeader className="bg-gradient-to-r from-primary/5 to-transparent rounded-t-lg border-b">
              <div className="bg-primary/10 rounded-full w-14 h-14 flex items-center justify-center mb-3">
                <BarChart3 className="h-7 w-7 text-primary" />
              </div>
              <CardTitle className="text-xl">AI Resume Analysis</CardTitle>
              <CardDescription className="text-base">
                Get instant feedback on your resume with AI-powered analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                  <span className="text-foreground">Career readiness score</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                  <span className="text-foreground">Strengths and weaknesses</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                  <span className="text-foreground">Skill gap analysis</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                  <span className="text-foreground">Role recommendations</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-2 shadow-lg hover:shadow-xl transition-all bg-gradient-to-br from-card to-card/50 hover:border-primary/30">
            <CardHeader className="bg-gradient-to-r from-blue-500/5 to-transparent rounded-t-lg border-b">
              <div className="bg-blue-500/10 rounded-full w-14 h-14 flex items-center justify-center mb-3">
                <Briefcase className="h-7 w-7 text-blue-600" />
              </div>
              <CardTitle className="text-xl">Smart Job Matching</CardTitle>
              <CardDescription className="text-base">
                Find jobs that match your profile with AI-powered matching
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
                  <span className="text-foreground">Real-time job search</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
                  <span className="text-foreground">Match score calculation</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
                  <span className="text-foreground">Personalized recommendations</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
                  <span className="text-foreground">Why you fit & how to improve</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-2 shadow-lg hover:shadow-xl transition-all bg-gradient-to-br from-card to-card/50 hover:border-primary/30">
            <CardHeader className="bg-gradient-to-r from-purple-500/5 to-transparent rounded-t-lg border-b">
              <div className="bg-purple-500/10 rounded-full w-14 h-14 flex items-center justify-center mb-3">
                <BookOpen className="h-7 w-7 text-purple-600" />
              </div>
              <CardTitle className="text-xl">Personalized Coaching</CardTitle>
              <CardDescription className="text-base">
                Get a 7-day personalized plan to close your skill gaps
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-purple-500"></div>
                  <span className="text-foreground">7-day learning plan</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-purple-500"></div>
                  <span className="text-foreground">Real course links</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-purple-500"></div>
                  <span className="text-foreground">DataCamp, Udemy, Coursera</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-purple-500"></div>
                  <span className="text-foreground">Daily reminders</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* How It Works */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-8">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="bg-primary/10 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">1</span>
              </div>
              <h3 className="font-semibold mb-2">Upload Resume</h3>
              <p className="text-sm text-muted-foreground">
                Upload your resume (PDF or text) for AI analysis
              </p>
            </div>
            <div className="text-center">
              <div className="bg-primary/10 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">2</span>
              </div>
              <h3 className="font-semibold mb-2">Get Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Receive instant feedback on your career readiness
              </p>
            </div>
            <div className="text-center">
              <div className="bg-primary/10 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">3</span>
              </div>
              <h3 className="font-semibold mb-2">Find Jobs</h3>
              <p className="text-sm text-muted-foreground">
                Discover matching opportunities with AI-powered search
              </p>
            </div>
            <div className="text-center">
              <div className="bg-primary/10 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">4</span>
              </div>
              <h3 className="font-semibold mb-2">Tailor & Apply</h3>
              <p className="text-sm text-muted-foreground">
                Get tailored resumes and cover letters for each job
              </p>
            </div>
          </div>
        </div>

        {/* Benefits */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <div className="flex items-start gap-4">
            <Zap className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold mb-2">AI-Powered</h3>
              <p className="text-sm text-muted-foreground">
                Uses Claude AI and GPT for intelligent analysis and tailoring
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <Target className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold mb-2">Personalized</h3>
              <p className="text-sm text-muted-foreground">
                Tailored recommendations based on your unique profile
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <Shield className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold mb-2">Secure</h3>
              <p className="text-sm text-muted-foreground">
                Your data is secure and never shared with third parties
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="pt-6">
              <h2 className="text-2xl font-bold mb-4">Ready to Advance Your Career?</h2>
              <p className="text-muted-foreground mb-6">
                Join thousands of professionals using AI to land their dream jobs
              </p>
              <Link to="/login">
                <Button size="lg">Get Started Free</Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

