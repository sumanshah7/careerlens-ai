import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { ExternalLink, Calendar, CheckCircle2 } from 'lucide-react';

export const CoachingPlan = () => {
  const { coach } = useAppStore();

  if (!coach || !coach.plan || coach.plan.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="text-center py-12">
          <h1 className="text-3xl font-bold mb-4">No Coaching Plan Yet</h1>
          <p className="text-muted-foreground mb-6">
            Generate a coaching plan from the Analysis page to get started.
          </p>
          <Button onClick={() => window.location.href = '/analysis'}>
            Go to Analysis
          </Button>
        </div>
      </div>
    );
  }

  const extractUrl = (action: string): string | null => {
    // Extract URL from action text
    const urlMatch = action.match(/https?:\/\/[^\s\)]+/);
    return urlMatch ? urlMatch[0] : null;
  };

  const extractCourseInfo = (action: string): { platform: string; course: string } | null => {
    // Try to identify platform and course name
    const platforms = ['DataCamp', 'Udemy', 'Coursera', 'edX', 'freeCodeCamp', 'YouTube', 'AWS Skill Builder'];
    for (const platform of platforms) {
      if (action.includes(platform)) {
        // Try to extract course name
        const courseMatch = action.match(/(?:'|")([^'"]+)(?:'|")/);
        const course = courseMatch ? courseMatch[1] : action.split(platform)[0].trim();
        return { platform, course };
      }
    }
    return null;
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-3xl font-bold mb-2">Your 7-Day Coaching Plan</h1>
            <p className="text-muted-foreground">
              Personalized learning plan to address your skill gaps
            </p>
          </div>
          {coach.reminders && (
            <Badge variant="outline" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Reminders Enabled
            </Badge>
          )}
        </div>
      </div>

      <div className="space-y-6">
        {coach.plan.map((day) => (
          <Card key={day.day} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-primary">Day {day.day}</span>
                    <span className="text-xl">{day.title}</span>
                  </CardTitle>
                </div>
                <Badge variant="secondary">Day {day.day}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {day.actions.map((action, idx) => {
                  const url = extractUrl(action);
                  const courseInfo = extractCourseInfo(action);
                  
                  return (
                    <div
                      key={idx}
                      className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                    >
                      <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm leading-relaxed">
                          {action.split('(')[0].trim()}
                        </p>
                        {courseInfo && (
                          <Badge variant="outline" className="mt-2 mr-2">
                            {courseInfo.platform}
                          </Badge>
                        )}
                        {url && (
                          <Button
                            variant="link"
                            size="sm"
                            className="mt-2 p-0 h-auto"
                            onClick={() => window.open(url, '_blank')}
                          >
                            <ExternalLink className="h-4 w-4 mr-1" />
                            Open Course
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="mt-6 bg-primary/5">
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Complete each day's activities and track your progress. After completing the 7-day plan, 
            return to the Analysis page to see your improved score!
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

