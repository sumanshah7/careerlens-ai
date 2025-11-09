import { TailorResponse } from '../types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Copy } from 'lucide-react';

interface TailorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tailor: TailorResponse;
}

export const TailorModal = ({ open, onOpenChange, tailor }: TailorModalProps) => {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  // Check if tailor data is empty
  if (!tailor || (!tailor.bullets?.length && !tailor.pitch && !tailor.coverLetter)) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Tailored Resume & Cover Letter</DialogTitle>
            <DialogDescription>
              Generating content...
            </DialogDescription>
          </DialogHeader>
          <div className="py-8 text-center text-muted-foreground">
            <p>Content is being generated. Please wait...</p>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader className="bg-gradient-to-r from-primary/5 to-transparent rounded-t-lg p-6 -m-6 mb-4">
          <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent flex items-center gap-2">
            <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            AI-Tailored Resume & Cover Letter
          </DialogTitle>
          <DialogDescription className="text-base">
            Professionally customized content powered by OpenAI GPT-4
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-card to-card/50">
            <CardHeader className="bg-gradient-to-r from-primary/5 to-transparent rounded-t-lg border-b">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse"></div>
                  Resume Bullets (STAR Format)
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    copyToClipboard(tailor.bullets.join('\n'));
                    // Show toast notification
                  }}
                  className="hover:bg-primary/10"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy All
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {tailor.bullets && tailor.bullets.length > 0 ? (
                <ul className="space-y-3">
                  {tailor.bullets.map((bullet, idx) => (
                    <li key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
                      <span className="flex-shrink-0 h-6 w-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-semibold mt-0.5">
                        {idx + 1}
                      </span>
                      <span className="text-sm leading-relaxed">{bullet}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground italic">No resume bullets generated yet.</p>
              )}
            </CardContent>
          </Card>

          <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-blue-500/5 to-blue-500/10">
            <CardHeader className="bg-gradient-to-r from-blue-500/5 to-transparent rounded-t-lg border-b">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                  Elevator Pitch
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(tailor.pitch)}
                  className="hover:bg-blue-500/10"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {tailor.pitch ? (
                <p className="text-sm leading-relaxed whitespace-pre-wrap bg-muted/30 p-4 rounded-lg border-l-4 border-blue-500">
                  {tailor.pitch}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground italic">No elevator pitch generated yet.</p>
              )}
            </CardContent>
          </Card>

          <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-green-500/5 to-green-500/10">
            <CardHeader className="bg-gradient-to-r from-green-500/5 to-transparent rounded-t-lg border-b">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500"></div>
                  Cover Letter
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(tailor.coverLetter)}
                  className="hover:bg-green-500/10"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {tailor.coverLetter ? (
                <p className="text-sm leading-relaxed whitespace-pre-wrap bg-muted/30 p-4 rounded-lg border-l-4 border-green-500">
                  {tailor.coverLetter}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground italic">No cover letter generated yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
};

