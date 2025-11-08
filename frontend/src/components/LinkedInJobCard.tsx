import { LinkedInJobSearchItem } from '../types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
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
    if (match >= 80) return 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md';
    if (match >= 60) return 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-md';
    return 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-md';
  };

  const getMatchIcon = (match: number) => {
    if (match >= 80) return '✓';
    if (match >= 60) return '~';
    return '!';
  };

  return (
    <Card className="border-2 shadow-lg hover:shadow-xl transition-all duration-300 hover:border-primary/30 bg-gradient-to-br from-card to-card/50">
      <CardHeader className="bg-gradient-to-r from-primary/5 to-transparent border-b">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl mb-1">{job.title}</CardTitle>
            <CardDescription className="text-base font-medium">{job.company}</CardDescription>
            {job.location && (
              <CardDescription className="text-sm text-muted-foreground mt-1">
                📍 {job.location}
              </CardDescription>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge className={`${getMatchColor(job.matchScore)} px-4 py-1.5 text-sm font-semibold`}>
              <span className="mr-1">{getMatchIcon(job.matchScore)}</span>
              {job.matchScore}% Match
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5 pt-6">
        {job.reasons && job.reasons.length > 0 && (
          <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-4">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-green-700 dark:text-green-400">
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Why you're a great fit
            </h4>
            <ul className="space-y-2">
              {job.reasons.map((reason, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-foreground">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-green-500 flex-shrink-0"></div>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {job.gaps && job.gaps.length > 0 && (
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-4">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-amber-700 dark:text-amber-400">
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              Areas to strengthen
            </h4>
            <ul className="space-y-2">
              {job.gaps.map((gap, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-foreground">
                  <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-500 flex-shrink-0"></div>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {job.description_snippet && (
          <div className="text-sm text-muted-foreground line-clamp-3">
            {job.description_snippet}
          </div>
        )}
      </CardContent>
      <CardFooter className="flex gap-3 pt-4 border-t bg-muted/30">
        <a
          href={jobUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1"
        >
          <Button
            variant="outline"
            size="sm"
            className="w-full hover:bg-primary/5 hover:border-primary/30 transition-all"
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            View Job Posting
          </Button>
        </a>
        <Button 
          size="sm" 
          onClick={() => onTailor(job)}
          className="flex-1 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-md hover:shadow-lg transition-all"
        >
          <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          Tailor Resume
        </Button>
      </CardFooter>
    </Card>
  );
};

