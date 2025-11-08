import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { analyzeResume, uploadPDF } from '../lib/api';
import { track } from '../lib/analytics';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Upload, FileText, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { Spinner } from '../components/ui/spinner';

// SHA256 hash utility
async function sha256(text: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export const Home = () => {
  const [text, setText] = useState('');
  const [role, setRole] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [resumeHash, setResumeHash] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const navigate = useNavigate();
  const { 
    setResumeText, 
    setAnalysis, 
    setJobs,
    clearAll, 
    saveResume, 
    getResumeByRole, 
    getAllRoles,
    loadResume,
    resumes,
    currentRole,
  } = useAppStore();
  
  const existingRoles = getAllRoles();
  
  useEffect(() => {
    // If there's a current role, try to load it
    if (currentRole) {
      const existingResume = getResumeByRole(currentRole);
      if (existingResume) {
        setRole(currentRole);
        setText(existingResume.resumeText);
      }
    }
  }, [currentRole, getResumeByRole]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Cancel any ongoing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Immediately clear analysis and jobs on new file upload
    setAnalysis(null);
    setJobs([]);
    
    if (file.type === 'application/pdf') {
      // Handle PDF upload
      setUploading(true);
      try {
        const result = await uploadPDF(file);
        const content = result.text;
        setText(content);
        
        // Compute hash for new resume
        const hash = await sha256(content);
        setResumeHash(hash);
        
        toast.success(`PDF uploaded successfully! Extracted ${content.length} characters.`);
      } catch (error: any) {
        const errorMessage = error?.message || 'Failed to upload PDF. Please try again.';
        toast.error(errorMessage);
        console.error('PDF upload error:', error);
      } finally {
        setUploading(false);
      }
      return;
    }
    
    // Handle text files
    if (file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const content = event.target?.result as string;
        setText(content);
        
        // Compute hash for new resume
        const hash = await sha256(content);
        setResumeHash(hash);
      };
      reader.readAsText(file);
    }
  };

  const handleSubmit = async () => {
    if (!text.trim()) {
      toast.error('Please enter or upload your resume');
      return;
    }
    
    if (!role.trim()) {
      toast.error('Please enter a target role (e.g., "Software Engineer", "Data Scientist")');
      return;
    }

    // Cancel any ongoing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Immediately clear analysis and jobs on new file upload
    setAnalysis(null);
    setJobs([]);
    
    // Compute hash for resume text
    const hash = await sha256(text);
    setResumeHash(hash);

    setLoading(true);
    try {
      // Clear all previous data when uploading a new resume
      clearAll();
      
      setResumeText(text);
      console.log('📤 Sending resume to backend for analysis...', { 
        textLength: text.length, 
        textPreview: text.substring(0, 100),
        role,
        hash: hash.substring(0, 8)
      });
      const analysis = await analyzeResume(text, role, undefined, 5, abortController.signal);
      console.log('✅ Received analysis from backend:', analysis);
      console.log('✅ Analysis domains:', analysis.domains);
      console.log('✅ Analysis skills:', analysis.skills);
      console.log('✅ Analysis strengths:', analysis.strengths.length);
      
      // Check if request was aborted
      if (abortController.signal.aborted) {
        return;
      }
      
      // Show success message
      toast.success('Resume analyzed successfully!');
      
      setAnalysis(analysis);
      
      // Save resume with role for progress tracking
      const resumeId = saveResume(role, text, analysis);
      console.log('💾 Saved resume:', resumeId, 'for role:', role);
      
      // Track with hash only (no raw text) - reuse hash computed earlier
      track('resume_uploaded', { 
        hash: hash.substring(0, 8),
        filename: 'resume.txt', // Could extract from file if available
        size: text.length,
      });
      navigate('/analysis');
    } catch (error: any) {
      // Don't show error if request was aborted
      if (error?.name === 'AbortError' || abortController.signal.aborted) {
        console.log('Request aborted');
        return;
      }
      console.error('❌ Analysis error:', error);
      toast.error('Failed to analyze resume. Check console for details.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleLoadResume = (selectedRole: string) => {
    const resume = getResumeByRole(selectedRole);
    if (resume) {
      setRole(selectedRole);
      setText(resume.resumeText);
      loadResume(resume.id);
      toast.success(`Loaded resume for ${selectedRole}`);
    }
  };

  return (
    <div key={resumeHash || 'default'} className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="h-1 w-12 bg-gradient-to-r from-primary to-primary/50 rounded-full"></div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Resume Analysis
            </h1>
            <div className="h-1 w-12 bg-gradient-to-r from-primary/50 to-primary rounded-full"></div>
          </div>
          <p className="text-muted-foreground text-lg">Upload your resume to get AI-powered career insights</p>
        </div>
        <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-card to-card/50">
          <CardHeader className="bg-gradient-to-r from-primary/5 to-transparent rounded-t-lg border-b">
            <CardTitle className="flex items-center gap-2">
              <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Upload Your Resume
            </CardTitle>
            <CardDescription className="text-base">
              Paste your resume text or upload a file to get started with CareerLens AI
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
          {/* Role Selection */}
          <div>
            <Label htmlFor="role" className="text-sm font-medium mb-2 block">
              Target Role <span className="text-muted-foreground">(e.g., Software Engineer, Data Scientist)</span>
            </Label>
            <div className="flex gap-2">
              <Input
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Enter target role..."
                className="flex-1"
              />
              {existingRoles.length > 0 && (
                <Select value={role} onValueChange={handleLoadResume}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Load existing" />
                  </SelectTrigger>
                  <SelectContent>
                    {existingRoles.map((r) => (
                      <SelectItem key={r} value={r}>
                        {r}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            {existingRoles.length > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                You have {existingRoles.length} saved resume{existingRoles.length > 1 ? 's' : ''} for different roles
              </p>
            )}
          </div>
          
          {/* Resume Text */}
          <div>
            <label className="text-sm font-medium mb-2 block">Resume Text</label>
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your resume content here..."
              className="min-h-[300px]"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Or Upload File</label>
            <div className="flex items-center gap-2">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileUpload}
                accept=".pdf,.txt,.doc,.docx"
                className="hidden"
                disabled={uploading}
              />
              <Button
                variant="outline"
                onClick={() => document.getElementById('file-upload')?.click()}
                disabled={uploading}
              >
                {uploading ? (
                  <>
                    <Spinner className="h-4 w-4 mr-2" size="sm" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Choose File (PDF, TXT, DOC, DOCX)
                  </>
                )}
              </Button>
            </div>
          </div>
          <Button
            onClick={handleSubmit}
            disabled={loading || !text.trim()}
            className="w-full bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg hover:shadow-xl transition-all"
            size="lg"
          >
            {loading ? (
              <>
                <Spinner className="mr-2" size="sm" />
                Analyzing...
              </>
            ) : (
              <>
                <svg className="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Analyze Resume
              </>
            )}
          </Button>
        </CardContent>
      </Card>
      </div>
    </div>
  );
};

