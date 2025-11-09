import { LinkedInJobSearchItem } from '../types';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ExternalLink } from 'lucide-react';

interface LinkedInJobCardProps {
  job: LinkedInJobSearchItem;
  onTailor: (job: LinkedInJobSearchItem) => void;
}

export const LinkedInJobCard = ({ job, onTailor }: LinkedInJobCardProps) => {
  // Ensure URL is always valid - backend should provide this, but double-check
  const jobUrl = job.url || '';
  
  // Never render jobs without valid URLs
  if (!jobUrl || jobUrl === '') {
    return null;
  }

  const getMatchColor = (match: number) => {
    if (match >= 80) return 'bg-[#2563EB] text-white';
    if (match >= 60) return 'bg-[#F59E0B] text-white';
    return 'bg-[#EF4444] text-white';
  };

  const getMatchIcon = (match: number) => {
    if (match >= 80) return '✓';
    if (match >= 60) return '~';
    return '!';
  };

  return (
    <div className="bg-white rounded-[16px] p-6 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200">
      <div className="border-b border-[#E5E7EB] pb-4 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-[#111827] mb-1">{job.title}</h3>
            <p className="text-base font-medium text-[#6b7280]">{job.company}</p>
            {job.location && (
              <p className="text-sm text-[#6b7280] mt-1">
                📍 {job.location}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge className={`${getMatchColor(job.matchScore)} px-4 py-1.5 text-sm font-semibold rounded-lg`}>
              <span className="mr-1">{getMatchIcon(job.matchScore)}</span>
              {job.matchScore}% Match
            </Badge>
          </div>
        </div>
      </div>
      <div className="space-y-5">
        {/* Matched Skills - Show prominently */}
        {job.skill_breakdown && job.skill_breakdown.matched_skills && job.skill_breakdown.matched_skills.length > 0 && (
          <div className="bg-[#EFF6FF] border-l-4 border-[#2563EB] rounded-lg p-5">
            <h4 className="text-base font-semibold mb-3 flex items-center gap-2 text-[#2563EB]">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Skills That Match
            </h4>
            <p className="text-sm text-[#6b7280] mb-3">These skills from your resume match what this job requires:</p>
            <div className="flex flex-wrap gap-2">
              {job.skill_breakdown.matched_skills.map((skill, idx) => (
                <span key={idx} className="px-3 py-1.5 bg-[#2563EB] text-white rounded-lg text-sm font-medium border border-[#1d4ed8]">
                  {skill}
                </span>
              ))}
            </div>
            {job.skill_breakdown.matched_count && (
              <p className="text-xs text-[#6b7280] mt-3">
                {job.skill_breakdown.matched_count} of {job.skill_breakdown.job_skill_count} required skills matched
              </p>
            )}
          </div>
        )}

        {/* Why You're a Great Fit - Show prominently */}
        {job.reasons && job.reasons.length > 0 && (
          <div className="bg-[#EFF6FF] border-l-4 border-[#2563EB] rounded-lg p-5">
            <h4 className="text-base font-semibold mb-3 flex items-center gap-2 text-[#2563EB]">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Why You're a Great Fit for This Job
            </h4>
            <ul className="space-y-3">
              {job.reasons.map((reason, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm text-[#111827]">
                  <div className="mt-1 h-2 w-2 rounded-full bg-[#2563EB] flex-shrink-0"></div>
                  <span className="leading-relaxed">{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* What to Learn - Show prominently */}
        {job.gaps && job.gaps.length > 0 && (
          <div className="bg-[#FEF3C7] border-l-4 border-[#F59E0B] rounded-lg p-5">
            <h4 className="text-base font-semibold mb-3 flex items-center gap-2 text-[#F59E0B]">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              What You Need to Learn for This Job
            </h4>
            <p className="text-sm text-[#6b7280] mb-3">Focus on developing these skills to strengthen your application:</p>
            <ul className="space-y-3">
              {job.gaps.map((gap, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm text-[#111827]">
                  <div className="mt-1 h-2 w-2 rounded-full bg-[#F59E0B] flex-shrink-0"></div>
                  <span className="leading-relaxed">{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Missing Skills - Show if available */}
        {job.skill_breakdown && job.skill_breakdown.missing_skills && job.skill_breakdown.missing_skills.length > 0 && (
          <div className="bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg p-4">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-[#111827]">
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
              </svg>
              Additional Skills to Develop
            </h4>
            <div className="flex flex-wrap gap-2">
              {job.skill_breakdown.missing_skills.map((skill, idx) => (
                <span key={idx} className="px-2 py-1 bg-[#FEF3C7] text-[#F59E0B] rounded text-xs border border-[#FCD34D]">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Job Description Snippet */}
        {job.description_snippet && (
          <div className="bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg p-4">
            <h4 className="text-sm font-semibold mb-2 text-[#111827]">Job Description</h4>
            <p className="text-sm text-[#6b7280] line-clamp-3 leading-relaxed">
              {job.description_snippet}
            </p>
          </div>
        )}
      </div>
      <div className="flex gap-3 pt-4 mt-6 border-t border-[#E5E7EB]">
        <a
          href={jobUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1"
        >
          <Button
            variant="outline"
            size="sm"
            className="w-full border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200"
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            View Job Posting
          </Button>
        </a>
        <Button 
          size="sm" 
          onClick={() => onTailor(job)}
          className="flex-1 bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
        >
          <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          Tailor Resume
        </Button>
      </div>
    </div>
  );
};

