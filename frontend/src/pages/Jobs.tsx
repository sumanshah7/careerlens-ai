import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { searchJobs, tailor, checkHealth } from '../lib/api';
import { track } from '../lib/analytics';
import { LinkedInJobCard } from '../components/LinkedInJobCard';
import { TailorModal } from '../components/TailorModal';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { Spinner } from '../components/ui/spinner';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Job, TailorResponse, LinkedInJobSearchItem } from '../types';
import { toast } from 'sonner';
import { Sparkles, Search, Loader2 } from 'lucide-react';

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
  const { setTailor, resumeText, tailor: tailorData, analysis } = useAppStore();
  const [linkedInJobs, setLinkedInJobs] = useState<LinkedInJobSearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [tailorLoading, setTailorLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState<LinkedInJobSearchItem | null>(null);
  const [tailorOpen, setTailorOpen] = useState(false);
  const [currentTailor, setCurrentTailor] = useState<TailorResponse | null>(null);
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
    try {
      // Get top skills from analysis if available
      const topSkills = analysis?.skills 
        ? [...(analysis.skills.core || []), ...(analysis.skills.adjacent || [])].slice(0, 5)
        : [];
      
      const tailorResponse = await tailor(
        resumeText || '', 
        job.title, 
        job.company, 
        job.description_snippet || ''
      );
      setTailor(tailorResponse);
      setCurrentTailor(tailorResponse);
      setTailorOpen(true);
      
      track('tailor_success', {
        jobId: job.id,
        jobMatch: job.matchScore,
      });
    } catch (error) {
      const errorName = error instanceof Error ? error.name : 'UnknownError';
      track('tailor_failure', {
        jobId: job.id,
        jobMatch: job.matchScore,
        errorName,
        errorMessage: error instanceof Error ? error.message : String(error),
      });
      toast.error('Failed to tailor resume');
      console.error(error);
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
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Enhanced Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-1 w-12 bg-gradient-to-r from-primary to-primary/50 rounded-full"></div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Job Opportunities
            </h1>
          </div>
          <p className="text-muted-foreground text-lg">AI-powered job matching tailored to your resume</p>
        </div>
        
        {/* Health check banner */}
        {getHealthBanner()}

        {/* Filters */}
        <Card className="mb-6 border-2 shadow-lg">
          <CardHeader>
            <CardTitle>Search Filters</CardTitle>
            <CardDescription>Enter your job search criteria</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="role">Job Role *</Label>
                <Input
                  id="role"
                  placeholder="e.g., AI Engineer"
                  value={filters.role}
                  onChange={(e) => setFilters(prev => ({ ...prev, role: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  placeholder="e.g., United States"
                  value={filters.location}
                  onChange={(e) => setFilters(prev => ({ ...prev, location: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="radius">Radius (miles)</Label>
                <Input
                  id="radius"
                  type="number"
                  min="1"
                  max="125"
                  value={filters.radius_miles}
                  onChange={(e) => setFilters(prev => ({ ...prev, radius_miles: parseInt(e.target.value) || 25 }))}
                />
              </div>
              <div className="flex items-end">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="remote"
                    checked={filters.remote}
                    onCheckedChange={(checked) => setFilters(prev => ({ ...prev, remote: checked === true }))}
                  />
                  <Label htmlFor="remote" className="cursor-pointer">Remote only</Label>
                </div>
              </div>
            </div>
            <div className="mt-4">
              <Button 
                onClick={() => handleSearch(null)} 
                disabled={loading || !filters.role}
                size="lg"
                className="w-full md:w-auto bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg hover:shadow-xl transition-all"
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
            </div>
          </CardContent>
        </Card>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <Skeleton className="h-6 w-48 mb-2" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                  <Skeleton className="h-6 w-20" />
                </div>
              </CardHeader>
              <CardContent>
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
              </CardContent>
              <CardContent>
                <div className="flex gap-2">
                  <Skeleton className="h-9 w-24" />
                  <Skeleton className="h-9 w-40" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : linkedInJobs.length === 0 && !loading ? (
        <Card className="border-2 shadow-lg">
          <CardContent className="py-16 text-center">
            <div className="mb-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center mb-4">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Ready to find your next opportunity?</h3>
              <p className="text-muted-foreground mb-6">
                Enter your job search criteria above and click "Find Matching Jobs"
              </p>
            </div>
          </CardContent>
        </Card>
      ) : linkedInJobs.length > 0 ? (
        <div className="space-y-4">
          {linkedInJobs.map((job) => (
            <LinkedInJobCard key={job.id} job={job} onTailor={handleTailor} />
          ))}
          {nextCursor && (
            <div className="flex justify-center pt-4">
              <Button
                onClick={handleLoadMore}
                disabled={loadingMore}
                variant="outline"
                size="lg"
                className="bg-gradient-to-r from-primary/10 to-primary/5 hover:from-primary/20 hover:to-primary/10"
              >
                {loadingMore ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Loading more...
                  </>
                ) : (
                  <>
                    Load More Jobs
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      ) : (
        <Card className="border-2 shadow-lg">
          <CardContent className="py-16 text-center">
            <div className="mb-6">
              <div className="mx-auto h-16 w-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center mb-4">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">No jobs found</h3>
              <p className="text-muted-foreground mb-6">
                Try adjusting your search criteria and click "Find Matching Jobs" to search again.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

        {currentTailor && (
          <TailorModal
            open={tailorOpen}
            onOpenChange={setTailorOpen}
            tailor={currentTailor}
          />
        )}
      </div>
    </div>
  );
};

