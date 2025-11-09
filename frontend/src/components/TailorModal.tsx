import { TailorResponse } from '../types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Copy, RefreshCw, AlertTriangle, Download } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { useState } from 'react';
import { tailor, downloadCoverLetterPDF } from '../lib/api';
import { useAppStore } from '../store/useAppStore';
import { useAuth } from '../contexts/AuthContext';

interface TailorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tailor: TailorResponse;
  jobTitle?: string;
  company?: string;
  jobDescription?: string;
  onRegenerate?: (newTailor: TailorResponse) => void;
}

export const TailorModal = ({ open, onOpenChange, tailor, jobTitle, company, jobDescription, onRegenerate }: TailorModalProps) => {
  const { resumeText } = useAppStore();
  const { currentUser } = useAuth();
  const [regenerating, setRegenerating] = useState(false);
  const [downloadingPDF, setDownloadingPDF] = useState(false);
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };
  
  const handleRegenerateWithMetrics = async () => {
    if (!resumeText || !jobDescription) {
      toast.error('Resume and job description required for regeneration');
      return;
    }
    
    setRegenerating(true);
    try {
      const newTailor = await tailor(
        resumeText,
        jobTitle || '',
        company || '',
        jobDescription,
        true, // emphasize_metrics = true
        currentUser?.uid || null // user_id from Firebase Auth
      );
      if (onRegenerate) {
        onRegenerate(newTailor);
      }
      toast.success('Regenerated with emphasis on metrics');
    } catch (error) {
      toast.error('Failed to regenerate');
      console.error(error);
    } finally {
      setRegenerating(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!tailor.coverLetter) {
      toast.error('No cover letter to download');
      return;
    }
    
    setDownloadingPDF(true);
    try {
      await downloadCoverLetterPDF(
        tailor.doc_id || null,
        tailor.coverLetter,
        jobTitle,
        company,
        currentUser?.displayName || undefined,
        currentUser?.email || undefined
      );
      toast.success('Cover letter PDF downloaded successfully!');
    } catch (error) {
      toast.error('Failed to download PDF');
      console.error('[PDF] Error:', error);
    } finally {
      setDownloadingPDF(false);
    }
  };

  // Check if tailor data is empty
  if (!tailor || (!tailor.bullets?.length && !tailor.pitch && !tailor.coverLetter && !tailor.pointsToInclude?.length)) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl bg-white">
          <DialogHeader className="pb-6">
            <DialogTitle className="text-2xl font-semibold text-[#111827]">Tailored Resume & Cover Letter</DialogTitle>
          <DialogDescription className="text-base text-[#6b7280]">
            Generating content...
          </DialogDescription>
        </DialogHeader>
        <div className="py-8 text-center text-[#6b7280]">
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              <div className="h-16 w-16 border-4 border-[#2563eb]/20 border-t-[#2563eb] rounded-full animate-spin"></div>
            </div>
            <div>
              <p className="font-medium text-[#111827] mb-2">AI is crafting your tailored content</p>
              <p className="text-sm">This usually takes 10-30 seconds...</p>
              <p className="text-xs mt-2 text-[#6b7280]">If it takes longer than 90 seconds, please try again</p>
            </div>
          </div>
        </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-white">
        <DialogHeader className="pb-6">
          <DialogTitle className="text-2xl font-semibold text-[#111827] flex items-center gap-2">
            <svg className="h-6 w-6 text-[#2563eb]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {jobTitle ? `Tailored for ${jobTitle}` : 'AI-Tailored Resume & Cover Letter'}
            {company && <span className="text-lg font-normal text-[#6b7280]"> at {company}</span>}
          </DialogTitle>
          <DialogDescription className="text-base text-[#6b7280] flex items-center gap-2 flex-wrap">
            {jobTitle || company 
              ? `Professionally customized content for ${jobTitle || 'this role'}${company ? ` at ${company}` : ''}`
              : 'Professionally customized content powered by OpenAI GPT-4'}
            {tailor.evidenceUsed && tailor.evidenceUsed.length > 0 && (
              <span className="text-xs text-[#2563eb] flex items-center gap-1" title={`Grounded in your resume: ${tailor.evidenceUsed.slice(0, 3).join(', ')}`}>
                <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Grounded in your resume
              </span>
            )}
            {tailor.isEvidenceOnly && (
              <span className="text-xs text-[#f59e0b] flex items-center gap-1 bg-[#fef3c7] px-2 py-1 rounded">
                <AlertTriangle className="h-3 w-3" />
                Evidence-only draft—no claims beyond your resume
              </span>
            )}
            {tailor.validationWarnings && tailor.validationWarnings.length > 0 && (
              <span className="text-xs text-[#f59e0b] flex items-center gap-1 bg-[#fef3c7] px-2 py-1 rounded" title={`We tightened phrasing to remove generic language: ${tailor.validationWarnings.join(', ')}`}>
                <AlertTriangle className="h-3 w-3" />
                We tightened phrasing to remove generic language
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="bg-white rounded-[16px] shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#e5e7eb] p-6"
          >
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-[#e5e7eb]">
              <h3 className="text-lg font-semibold text-[#111827] flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-[#2563eb]"></div>
                Resume Bullets (STAR Format)
              </h3>
              <div className="flex items-center gap-2">
                {jobDescription && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRegenerateWithMetrics}
                    disabled={regenerating}
                    className="border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200"
                  >
                    <RefreshCw className={`h-4 w-4 mr-2 ${regenerating ? 'animate-spin' : ''}`} />
                    Regenerate with more metrics
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    copyToClipboard(tailor.bullets.join('\n'));
                  }}
                  className="border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy All
                </Button>
              </div>
            </div>
            <div>
              {tailor.bullets && tailor.bullets.length > 0 ? (
                <ul className="space-y-3">
                  {tailor.bullets.map((bullet, idx) => (
                    <li key={idx} className="flex items-start gap-3 p-4 rounded-lg bg-[#f9fafb] hover:bg-[#f3f4f6] transition-colors border-l-4 border-[#2563eb]">
                      <span className="flex-shrink-0 h-6 w-6 rounded-full bg-[#2563eb]/10 text-[#2563eb] flex items-center justify-center text-xs font-semibold mt-0.5">
                        {idx + 1}
                      </span>
                      <span className="text-sm leading-relaxed text-[#111827]">{bullet}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-[#6b7280] italic">No resume bullets generated yet.</p>
              )}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="bg-white rounded-[16px] shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#e5e7eb] p-6"
          >
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-[#e5e7eb]">
              <h3 className="text-lg font-semibold text-[#111827] flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-[#2563eb]"></div>
                Elevator Pitch
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(tailor.pitch)}
                className="border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200"
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy
              </Button>
            </div>
            <div>
              {tailor.pitch ? (
                <p className="text-sm leading-relaxed whitespace-pre-wrap bg-[#eff6ff] p-4 rounded-lg border-l-4 border-[#2563eb] text-[#111827]">
                  {tailor.pitch}
                </p>
              ) : (
                <p className="text-sm text-[#6b7280] italic">No elevator pitch generated yet.</p>
              )}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="bg-white rounded-[16px] shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#e5e7eb] p-6"
          >
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-[#e5e7eb]">
              <h3 className="text-lg font-semibold text-[#111827] flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-[#2563eb]"></div>
                Cover Letter
              </h3>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadPDF}
                  disabled={downloadingPDF || !tailor.coverLetter}
                  className="border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200"
                >
                  <Download className={`h-4 w-4 mr-2 ${downloadingPDF ? 'animate-spin' : ''}`} />
                  {downloadingPDF ? 'Generating...' : 'Download PDF'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(tailor.coverLetter)}
                  className="border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </Button>
              </div>
            </div>
            <div>
              {tailor.coverLetter ? (
                <p className="text-sm leading-relaxed whitespace-pre-wrap bg-[#eff6ff] p-4 rounded-lg border-l-4 border-[#2563eb] text-[#111827]">
                  {tailor.coverLetter}
                </p>
              ) : (
                <p className="text-sm text-[#6b7280] italic">No cover letter generated yet.</p>
              )}
            </div>
          </motion.div>

          {/* Points to Include Section */}
          {tailor.pointsToInclude && tailor.pointsToInclude.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.3 }}
              className="bg-white rounded-[16px] shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#e5e7eb] p-6"
            >
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-[#e5e7eb]">
                <h3 className="text-lg font-semibold text-[#111827] flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#f59e0b]"></div>
                  Points to Include in Your Resume
                </h3>
                <span className="text-xs text-[#6b7280] bg-[#fef3c7] px-2 py-1 rounded">
                  {tailor.pointsToInclude.length} suggestions
                </span>
              </div>
              <div>
                <ul className="space-y-3">
                  {tailor.pointsToInclude.map((point, idx) => (
                    <li key={idx} className="flex items-start gap-3 p-4 rounded-lg bg-[#fffbeb] hover:bg-[#fef3c7] transition-colors border-l-4 border-[#f59e0b]">
                      <span className="flex-shrink-0 h-6 w-6 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] flex items-center justify-center text-xs font-semibold mt-0.5">
                        {idx + 1}
                      </span>
                      <span className="text-sm leading-relaxed text-[#111827]">{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

