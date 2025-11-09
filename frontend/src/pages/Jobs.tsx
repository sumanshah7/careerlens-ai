import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { searchJobs, tailor, checkHealth, fetchJobDescription } from '../lib/api';
import { track } from '../lib/analytics';
import { LinkedInJobCard } from '../components/LinkedInJobCard';
import { TailorModal } from '../components/TailorModal';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { useAuth } from '../contexts/AuthContext';
import { Spinner } from '../components/ui/spinner';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Job, TailorResponse, LinkedInJobSearchItem } from '../types';
import { toast } from 'sonner';
import { Sparkles, Search, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

// SHA256 hash utility
async function sha256(text: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export const Jobs = () => {
  const location = useLocation();
  const { setTailor, resumeText, tailor: tailorData, analysis, currentResumeId, currentRole, getResumeByRole, resumes } = useAppStore();
  const { currentUser } = useAuth();
  const [linkedInJobs, setLinkedInJobs] = useState<LinkedInJobSearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [tailorLoading, setTailorLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState<LinkedInJobSearchItem | null>(null);
  const [tailorOpen, setTailorOpen] = useState(false);
  const [currentTailor, setCurrentTailor] = useState<TailorResponse | null>(null);
  
  const handleTailorRegenerate = (newTailor: TailorResponse) => {
    setCurrentTailor(newTailor);
    setTailor(newTailor);
  };
  const [healthStatus, setHealthStatus] = useState<{ ok: boolean; providers: { anthropic: boolean; openai: boolean; dedalus: boolean; mcp: boolean } } | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    role: '',
    location: 'US-Remote',
    radius_miles: 25, // Default 25 miles (converted to ~40 km for API)
    remote: false,
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Check health on mount
    checkHealth().then(setHealthStatus).catch(() => setHealthStatus({ ok: false, providers: { anthropic: false, openai: false, dedalus: false, mcp: false } }));
  }, []);

  useEffect(() => {
    // Initialize filters from navigation state (e.g., clicking recommended role) or analysis
    const roleFromState = (location.state as any)?.role;
    
    if (roleFromState) {
      // Role passed from navigation (e.g., clicking recommended role)
      setFilters(prev => ({ ...prev, role: roleFromState }));
    } else if (analysis && !filters.role) {
      // Fallback to analysis if no role from navigation
      const targetRole = analysis?.recommended_roles?.[0] || analysis?.suggestedRoles?.[0] || analysis?.domains?.[0]?.name || '';
      if (targetRole) {
        setFilters(prev => ({ ...prev, role: targetRole }));
      }
    }
  }, [location.state, analysis]);

  useEffect(() => {
    // Track job views
    if (linkedInJobs.length > 0) {
      console.log('📋 Jobs loaded:', linkedInJobs.length, 'jobs');
      linkedInJobs.forEach((job) => {
        track('job_viewed', { jobId: job.id, jobMatch: job.matchScore });
      });
    }
  }, [linkedInJobs]);

  const handleSearch = async (cursor: string | null = null) => {
    if (!filters.role) {
      toast.error('Please enter a job role');
      return;
    }

    if (!healthStatus || !healthStatus.ok) {
      toast.error('Backend is not available. Please check if the server is running.');
      return;
    }
    
    // Cancel any ongoing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    if (cursor) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setLinkedInJobs([]);
      setNextCursor(null);
    }

    try {
      // Get resume skills from analysis if available
      const resumeSkills: string[] = [];
      if (analysis?.skills) {
        resumeSkills.push(...(analysis.skills.core || []));
        resumeSkills.push(...(analysis.skills.adjacent || []));
        resumeSkills.push(...(analysis.skills.advanced || []));
      }
      
      const response = await searchJobs({
        role: filters.role,
        location: filters.location,
        radius_km: Math.round(filters.radius_miles * 1.60934), // Convert miles to km
        remote: filters.remote,
        limit: 15,
        cursor: cursor,
        resume_skills: resumeSkills.length > 0 ? resumeSkills : undefined,
      }, abortController.signal);
      
      // Check if request was aborted
      if (abortController.signal.aborted) {
        return;
      }
      
      console.log('✅ Received jobs from backend:', response.jobs);
      console.log('✅ Jobs count:', response.jobs.length);
      console.log('✅ Next cursor:', response.nextCursor);
      
      if (cursor) {
        // Append to existing jobs
        setLinkedInJobs(prev => [...prev, ...response.jobs]);
      } else {
        // Replace jobs
        setLinkedInJobs(response.jobs || []);
      }
      
      setNextCursor(response.nextCursor || null);
      
      // Show success message only if jobs found
      if (response.jobs && response.jobs.length > 0) {
        toast.success(`Found ${response.jobs.length} matching jobs!`);
      } else {
        toast.error('No jobs found. Try adjusting your search criteria.');
      }
    } catch (error: any) {
      // Don't show error if request was aborted
      if (error?.name === 'AbortError' || abortController.signal.aborted) {
        console.log('Request aborted');
        return;
      }
      // Error tracking is handled in the API layer
      toast.error('Failed to fetch jobs');
      console.error('❌ Jobs fetch error:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleLoadMore = () => {
    if (nextCursor) {
      handleSearch(nextCursor);
    }
  };

  // Auto-search when role is set from navigation (after handleSearch is defined)
  useEffect(() => {
    const roleFromState = (location.state as any)?.role;
    if (roleFromState && filters.role === roleFromState && linkedInJobs.length === 0 && !loading && healthStatus?.ok) {
      // Auto-search when role is set from navigation
      handleSearch(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.role, location.state, linkedInJobs.length, loading, healthStatus]);

  const handleTailor = async (job: LinkedInJobSearchItem) => {
    track('tailor_clicked', { jobId: job.id, jobMatch: job.matchScore });
    setSelectedJob(job);
    setTailorLoading(true);
    setTailorOpen(true); // Open modal immediately to show loading state
    setCurrentTailor({
      bullets: [],
      pitch: '',
      coverLetter: '',
      evidenceUsed: [],
      isEvidenceOnly: false,
      validationWarnings: [],
      pointsToInclude: []
    }); // Set empty state to show loading
    
    try {
      // Step 0: Get resume text - try multiple sources
      let actualResumeText = resumeText || '';
      
      // If resumeText is empty, try to get it from saved resumes
      if (!actualResumeText || actualResumeText.trim().length === 0) {
        // Try to get from current resume ID
        if (currentResumeId) {
          const currentResume = resumes.find(r => r.id === currentResumeId);
          if (currentResume && currentResume.resumeText) {
            actualResumeText = currentResume.resumeText;
            console.log('✅ Loaded resume from currentResumeId');
          }
        }
        
        // If still empty, try to get from current role
        if ((!actualResumeText || actualResumeText.trim().length === 0) && currentRole) {
          const roleResume = getResumeByRole(currentRole);
          if (roleResume && roleResume.resumeText) {
            actualResumeText = roleResume.resumeText;
            console.log('✅ Loaded resume from currentRole');
          }
        }
        
        // If still empty, try to get from the most recent resume
        if (!actualResumeText || actualResumeText.trim().length === 0) {
          const mostRecentResume = resumes.length > 0 
            ? resumes.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())[0]
            : null;
          if (mostRecentResume && mostRecentResume.resumeText) {
            actualResumeText = mostRecentResume.resumeText;
            console.log('✅ Loaded resume from most recent resume');
          }
        }
      }
      
      // Validate that we have resume text
      if (!actualResumeText || actualResumeText.trim().length < 50) {
        throw new Error('Resume text is required. Please upload your resume first on the Home page.');
      }
      
      // Step 1: Fetch full job description from URL
      let jobDescription = job.description_snippet || '';
      
      if (job.url && !job.url.includes('expired_jd_redirect')) {
        try {
          toast.info('Fetching full job description...', { duration: 2000 });
          const descResponse = await fetchJobDescription(job.url);
          if (descResponse.success && descResponse.description && descResponse.description.length > 200) {
            jobDescription = descResponse.description;
            console.log('✅ Fetched full job description:', descResponse.description.length, 'characters');
          } else {
            console.warn('⚠️ Could not fetch full description, using snippet');
            // Keep using snippet if fetch fails
          }
        } catch (descError) {
          console.warn('⚠️ Error fetching job description:', descError);
          // Continue with snippet if fetch fails
        }
      }
      
      // Validate that we have a job description
      if (!jobDescription || jobDescription.trim().length < 50) {
        throw new Error('Job description is required. Please ensure the job posting has a valid description.');
      }
      
      // Step 2: Get top skills from analysis if available
      const topSkills = analysis?.skills 
        ? [...(analysis.skills.core || []), ...(analysis.skills.adjacent || [])].slice(0, 5)
        : [];
      
      // Step 3: Call tailor API with full description
      const tailorResponse = await tailor(
        actualResumeText, // Use the resolved resume text
        job.title, 
        job.company, 
        jobDescription, // Use fetched full description
        false, // emphasizeMetrics
        currentUser?.uid || null // user_id from Firebase Auth
      );
      setTailor(tailorResponse);
      setCurrentTailor(tailorResponse);
      
      track('tailor_success', {
        jobId: job.id,
        jobMatch: job.matchScore,
      });
    } catch (error) {
      const errorName = error instanceof Error ? error.name : 'UnknownError';
      const errorMessage = error instanceof Error ? error.message : String(error);
      
      track('tailor_failure', {
        jobId: job.id,
        jobMatch: job.matchScore,
        errorName,
        errorMessage,
      });
      
      // Show user-friendly error
      if (errorMessage.includes('timeout') || errorMessage.includes('90 seconds')) {
        toast.error('Request timed out. Please try again or check your connection.');
      } else if (errorMessage.includes('Resume text is required')) {
        toast.error('Resume text is required. Please upload your resume first on the Home page.');
      } else if (errorMessage.includes('Job description is required')) {
        toast.error('Job description is missing. Please try a different job posting.');
      } else {
        toast.error('Failed to tailor resume. Please try again.');
      }
      console.error('[Tailor] Error:', error);
      
      // Close modal on error
      setTailorOpen(false);
    } finally {
      setTailorLoading(false);
    }
  };

  // Health check banner
  const getHealthBanner = () => {
    if (!healthStatus) return null;
    if (healthStatus.ok && healthStatus.providers.dedalus) return null; // All good
    
    if (!healthStatus.ok) {
      return (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-red-500 font-semibold">Backend not running</p>
          <p className="text-sm text-muted-foreground mt-1">Please start the backend server: <code className="bg-muted px-2 py-1 rounded">cd backend && make dev</code></p>
        </div>
      );
    }
    
    if (!healthStatus.providers.dedalus) {
      return (
        <div className="mb-4 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
          <p className="text-amber-500 font-semibold">Missing API Key</p>
          <p className="text-sm text-muted-foreground mt-1">Set <code className="bg-muted px-2 py-1 rounded">DEDALUS_API_KEY</code> in <code className="bg-muted px-2 py-1 rounded">backend/.env</code> and restart server.</p>
        </div>
      );
    }
    
    return null;
  };

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
          <h1 className="text-[42px] md:text-[56px] font-semibold text-[#0F172A] mb-6 leading-tight">Job Opportunities</h1>
          <p className="text-lg md:text-xl text-[#64748B] font-normal leading-relaxed">AI-powered job matching tailored to your resume</p>
        </motion.div>
        
        {/* Health check banner */}
        {getHealthBanner()}

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200 mb-6"
        >
          <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Search Filters</h2>
          <p className="text-sm text-[#64748B] mb-6 font-normal leading-relaxed">Enter your job search criteria</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div>
                <Label htmlFor="role" className="text-sm font-medium text-[#0F172A] mb-2 block">Job Role *</Label>
                <Input
                  id="role"
                  placeholder="e.g., AI Engineer"
                  value={filters.role}
                  onChange={(e) => setFilters(prev => ({ ...prev, role: e.target.value }))}
                  className="border-[#E5E7EB] rounded-lg focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
                />
              </div>
              <div>
                <Label htmlFor="location" className="text-sm font-medium text-[#0F172A] mb-2 block">Location</Label>
                <Input
                  id="location"
                  placeholder="e.g., United States"
                  value={filters.location}
                  onChange={(e) => setFilters(prev => ({ ...prev, location: e.target.value }))}
                  className="border-[#E5E7EB] rounded-lg focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
                />
              </div>
              <div>
                <Label htmlFor="radius" className="text-sm font-medium text-[#0F172A] mb-2 block">Radius (miles)</Label>
                <Input
                  id="radius"
                  type="number"
                  min="1"
                  max="125"
                  value={filters.radius_miles}
                  onChange={(e) => setFilters(prev => ({ ...prev, radius_miles: parseInt(e.target.value) || 25 }))}
                  className="border-[#E5E7EB] rounded-lg focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
                />
              </div>
              <div className="flex items-end">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="remote"
                    checked={filters.remote}
                    onCheckedChange={(checked) => setFilters(prev => ({ ...prev, remote: checked === true }))}
                    className="border-[#E5E7EB]"
                  />
                  <Label htmlFor="remote" className="text-sm font-medium text-[#0F172A] cursor-pointer">Remote only</Label>
                </div>
              </div>
            </div>
            <Button 
              onClick={() => handleSearch(null)} 
              disabled={loading || !filters.role}
              size="lg"
              className="w-full md:w-auto bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
            >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="h-5 w-5 mr-2" />
                Find Matching Jobs
              </>
            )}
          </Button>
        </motion.div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB]">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <Skeleton className="h-6 w-48 mb-2" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-6 w-20" />
              </div>
              <div className="space-y-4">
                <div>
                  <Skeleton className="h-4 w-32 mb-2" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                </div>
                <div>
                  <Skeleton className="h-4 w-32 mb-2" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <Skeleton className="h-9 w-24" />
                <Skeleton className="h-9 w-40" />
              </div>
            </div>
          ))}
        </div>
      ) : linkedInJobs.length === 0 && !loading ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-white rounded-[16px] p-16 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] text-center"
        >
          <div className="mb-6">
            <div className="mx-auto h-16 w-16 rounded-full bg-[#F9FAFB] flex items-center justify-center mb-4">
              <Sparkles className="h-8 w-8 text-[#64748B]" />
            </div>
            <h3 className="text-xl font-semibold text-[#0F172A] mb-2">Ready to find your next opportunity?</h3>
            <p className="text-[#64748B] mb-6 font-normal">
              Enter your job search criteria above and click "Find Matching Jobs"
            </p>
          </div>
        </motion.div>
      ) : linkedInJobs.length > 0 ? (
        <div className="space-y-4">
          {linkedInJobs.map((job, idx) => (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: idx * 0.05 }}
            >
              <LinkedInJobCard job={job} onTailor={handleTailor} />
            </motion.div>
          ))}
          {nextCursor && (
            <div className="flex justify-center pt-4">
              <Button
                onClick={handleLoadMore}
                disabled={loadingMore}
                variant="outline"
                size="lg"
                className="border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200 hover:scale-[1.02]"
              >
                {loadingMore ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Loading more...
                  </>
                ) : (
                  'Load More Jobs'
                )}
              </Button>
            </div>
          )}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-white rounded-[16px] p-16 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] text-center"
        >
          <div className="mb-6">
            <div className="mx-auto h-16 w-16 rounded-full bg-[#F9FAFB] flex items-center justify-center mb-4">
              <Sparkles className="h-8 w-8 text-[#64748B]" />
            </div>
            <h3 className="text-xl font-semibold text-[#0F172A] mb-2">No jobs found</h3>
            <p className="text-[#64748B] mb-6 font-normal">
              Try adjusting your search criteria and click "Find Matching Jobs" to search again.
            </p>
          </div>
        </motion.div>
      )}

      {currentTailor && selectedJob && (
        <TailorModal
          open={tailorOpen}
          onOpenChange={setTailorOpen}
          tailor={currentTailor}
          jobTitle={selectedJob.title}
          company={selectedJob.company}
          jobDescription={selectedJob.description_snippet || ''}
          onRegenerate={handleTailorRegenerate}
        />
      )}
      </div>
    </div>
  );
};

