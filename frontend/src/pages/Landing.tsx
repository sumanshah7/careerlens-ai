import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Logo } from '../components/Logo';
import { motion } from 'framer-motion';
import { Upload, BarChart3, Briefcase, FileCheck, ArrowRight } from 'lucide-react';

export const Landing = () => {
  return (
    <div className="min-h-screen bg-[#F9FAFB]">
      {/* Subtle radial tint behind hero (very subtle) */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(0,0,0,0.02)_0%,transparent_50%)] pointer-events-none" />
      
      {/* Minimal Navbar for Landing */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-sm border-b border-[#E5E7EB]">
        <div className="max-w-[1100px] mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            <Logo />
            <div className="flex items-center gap-4">
              <Link to="/login">
                <Button variant="ghost" className="text-[#64748B] hover:text-[#0F172A] hover:bg-transparent">
                  Sign In
                </Button>
              </Link>
              <Link to="/login">
                <Button className="bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-colors duration-200">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="relative">
        {/* Hero Section */}
        <section className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-[42px] md:text-[56px] font-semibold text-[#0F172A] mb-6 leading-tight">
              CareerLens AI
            </h1>
            <p className="text-lg md:text-xl text-[#64748B] mb-10 max-w-2xl mx-auto font-normal leading-relaxed">
              Your personal career copilot. Analyze your resume, match roles, and grow with a focused plan.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <Link to="/login">
                <Button 
                  size="lg" 
                  className="bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02] px-8 py-6 text-base"
                >
                  Get Started
                </Button>
              </Link>
              <Link to="/login">
                <Button 
                  size="lg" 
                  variant="outline" 
                  className="border-[#E5E7EB] text-[#0F172A] !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02] px-8 py-6 text-base"
                >
                  Sign In
                </Button>
              </Link>
            </div>
            <p className="text-sm text-[#64748B] font-medium">
              Private by design · No resume text sent to analytics
            </p>
          </motion.div>
        </section>

        {/* Feature Trio */}
        <section className="max-w-[1100px] mx-auto px-6 py-16 md:py-24">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
            >
              <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Resume Analysis</h2>
              <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">
                Evidence-based insights from your resume
              </p>
              <ul className="space-y-3 text-sm text-[#64748B] font-normal">
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Score, strengths, gaps, role hints</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Domain classification with confidence</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Skill extraction and mapping</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Recommended roles tailored to you</span>
                </li>
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
            >
              <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Smart Job Matching</h2>
              <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">
                Open roles that fit your skills
              </p>
              <ul className="space-y-3 text-sm text-[#64748B] font-normal">
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Matches by skills, clear reasons</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Real-time job search from multiple sources</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Match score with gap analysis</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Why you fit & how to improve</span>
                </li>
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
            >
              <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Personalized Coaching</h2>
              <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">
                A 7-day plan to close gaps
              </p>
              <ul className="space-y-3 text-sm text-[#64748B] font-normal">
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>7-day plan, real resources</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>DataCamp, Udemy, Coursera links</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Daily tasks with deliverables</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#64748B] flex-shrink-0" />
                  <span>Track progress and improvements</span>
                </li>
              </ul>
            </motion.div>
          </div>
        </section>

        {/* How It Works */}
        <section className="max-w-[1100px] mx-auto px-6 py-16 md:py-24">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-3xl font-semibold text-[#0F172A] text-center mb-12"
          >
            How it works
          </motion.h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { icon: Upload, title: 'Upload', desc: 'Paste text or upload a PDF' },
              { icon: BarChart3, title: 'Analyze', desc: 'See strengths and gaps' },
              { icon: Briefcase, title: 'Find Jobs', desc: 'Matches that fit your skills' },
              { icon: FileCheck, title: 'Tailor & Apply', desc: 'Bullets and cover letters' },
            ].map((step, idx) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.5 + idx * 0.1 }}
                className="text-center"
              >
                <div className="mb-4 flex justify-center">
                  <div className="w-12 h-12 rounded-full bg-[#F9FAFB] border border-[#E5E7EB] flex items-center justify-center">
                    <step.icon className="h-6 w-6 text-[#64748B]" />
                  </div>
                </div>
                <h3 className="font-semibold text-[#0F172A] mb-2">{step.title}</h3>
                <p className="text-sm text-[#64748B] font-normal">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Privacy Band */}
        <section className="bg-[#F9FAFB] border-y border-[#E5E7EB] py-8">
          <div className="max-w-[1100px] mx-auto px-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-base font-medium text-[#0F172A]">Privacy-first by design</p>
              <p className="text-sm text-[#64748B] font-normal">
                We hash your resume and never send PII to analytics
              </p>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="text-center"
          >
            <h2 className="text-3xl md:text-4xl font-semibold text-[#0F172A] mb-4">
              Ready to advance your career?
            </h2>
            <p className="text-lg text-[#64748B] mb-8 font-normal">
              Start with a quick analysis—free and private
            </p>
            <Link to="/login">
              <Button 
                size="lg" 
                className="bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02] px-8 py-6 text-base inline-flex items-center gap-2"
              >
                Analyze my resume
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
          </motion.div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#E5E7EB] py-6">
        <div className="max-w-[1100px] mx-auto px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-[#64748B] font-normal">
              © {new Date().getFullYear()} CareerLens AI
            </p>
            <div className="flex items-center gap-6 text-sm text-[#64748B] font-normal">
              <a href="#" className="hover:text-[#0F172A] transition-colors">Docs</a>
              <a href="#" className="hover:text-[#0F172A] transition-colors">Privacy</a>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-[#0F172A] transition-colors">GitHub</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
