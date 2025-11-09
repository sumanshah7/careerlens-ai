import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { analyzeResume, uploadPDF } from '../lib/api';
import { track } from '../lib/analytics';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Upload } from 'lucide-react';
import { toast } from 'sonner';
import { Spinner } from '../components/ui/spinner';
import { motion } from 'framer-motion';

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
    <div key={resumeHash || 'default'} className="min-h-screen bg-[#F9FAFB]">
      <div className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
          <h1 className="text-[42px] md:text-[56px] font-semibold text-[#0F172A] mb-6 leading-tight">Resume Analysis</h1>
          <p className="text-lg md:text-xl text-[#64748B] font-normal leading-relaxed">Upload your resume to get AI-powered career insights</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <div className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB]">
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Upload Your Resume</h2>
              <p className="text-sm text-[#64748B] font-normal leading-relaxed">
                Paste your resume text or upload a file to get started
              </p>
            </div>
            <div className="space-y-6">
              {/* Role Selection */}
              <div>
                <Label htmlFor="role" className="text-sm font-medium text-[#0F172A] mb-2 block">
                  Target Role
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    id="role"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    placeholder="e.g., Software Engineer, Data Scientist"
                    className="flex-1 border-[#E5E7EB] rounded-lg focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
                  />
                  {existingRoles.length > 0 && (
                    <Select value={role} onValueChange={handleLoadResume}>
                      <SelectTrigger className="w-full border-[#E5E7EB] rounded-lg">
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
                  <p className="text-xs text-[#64748B] mt-2 font-normal">
                    You have {existingRoles.length} saved resume{existingRoles.length > 1 ? 's' : ''} for different roles
                  </p>
                )}
              </div>
              
              {/* Resume Text */}
              <div>
                <Label className="text-sm font-medium text-[#0F172A] mb-2 block">Resume Text</Label>
                <Textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste your resume content here..."
                  className="min-h-[300px] border-[#E5E7EB] rounded-lg focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
                />
              </div>
              
              {/* File Upload */}
              <div>
                <Label className="text-sm font-medium text-[#0F172A] mb-2 block">Or Upload File</Label>
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
                    className="border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200"
                  >
                    {uploading ? (
                      <>
                        <Spinner className="h-4 w-4 mr-2" size="sm" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Choose File
                      </>
                    )}
                  </Button>
                </div>
              </div>
              
              <Button
                onClick={handleSubmit}
                disabled={loading || !text.trim()}
                className="w-full bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
                size="lg"
              >
                {loading ? (
                  <>
                    <Spinner className="mr-2" size="sm" />
                    Analyzing...
                  </>
                ) : (
                  'Analyze Resume'
                )}
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

