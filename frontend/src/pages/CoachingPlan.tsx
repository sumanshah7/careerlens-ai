import { useAppStore } from '../store/useAppStore';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { ExternalLink, Calendar, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

export const CoachingPlan = () => {
  const { coach } = useAppStore();

  if (!coach || !coach.plan || coach.plan.length === 0) {
    return (
      <div className="min-h-screen bg-[#F9FAFB]">
        <div className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="bg-white rounded-[16px] p-16 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] text-center"
          >
            <h1 className="text-3xl font-semibold text-[#0F172A] mb-4">No Coaching Plan Yet</h1>
            <p className="text-[#64748B] mb-6 font-normal">
              Generate a coaching plan from the Analysis page to get started.
            </p>
            <Button 
              onClick={() => window.location.href = '/analysis'}
              className="bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
            >
              Go to Analysis
            </Button>
          </motion.div>
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
    <div className="min-h-screen bg-[#F9FAFB]">
      <div className="max-w-[1100px] mx-auto px-6 py-20 md:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
          <h1 className="text-[42px] md:text-[56px] font-semibold text-[#0F172A] mb-6 leading-tight">Your 7-Day Coaching Plan</h1>
          <p className="text-lg md:text-xl text-[#64748B] font-normal leading-relaxed">
            Personalized learning plan to address your skill gaps
          </p>
          {coach.reminders && (
            <Badge variant="outline" className="flex items-center gap-2 border-[#E5E7EB] text-[#0F172A] mt-4 mx-auto w-fit">
              <Calendar className="h-4 w-4" />
              Reminders Enabled
            </Badge>
          )}
        </motion.div>

      <div className="space-y-6">
        {coach.plan.map((day, dayIdx) => (
          <motion.div
            key={day.day}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: dayIdx * 0.1 }}
            className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:-translate-y-[2px] transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
                  <span className="text-[#2563EB]">Day {day.day}</span>
                  <span className="text-xl font-medium">{day.title}</span>
                </h2>
              </div>
              <Badge variant="secondary" className="bg-[#F9FAFB] text-[#0F172A] border border-[#E5E7EB]">Day {day.day}</Badge>
            </div>
            <div className="space-y-3">
              {day.actions.map((action, idx) => {
                const url = extractUrl(action);
                const courseInfo = extractCourseInfo(action);
                
                return (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: dayIdx * 0.1 + idx * 0.05 }}
                    className="flex items-start gap-3 p-4 rounded-lg border border-[#E5E7EB] bg-white hover:bg-[#F9FAFB] transition-colors"
                  >
                    <CheckCircle2 className="h-5 w-5 text-[#2563EB] mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm leading-relaxed text-[#0F172A] font-normal">
                        {action.split('(')[0].trim()}
                      </p>
                      {courseInfo && (
                        <Badge variant="outline" className="mt-2 mr-2 border-[#E5E7EB] text-[#0F172A]">
                          {courseInfo.platform}
                        </Badge>
                      )}
                      {url && (
                        <Button
                          variant="link"
                          size="sm"
                          className="mt-2 p-0 h-auto text-[#2563EB] hover:text-[#1d4ed8]"
                          onClick={() => window.open(url, '_blank')}
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          Open Course
                        </Button>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.7 }}
        className="bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB] mt-6 bg-[#eff6ff] border-[#93c5fd]"
      >
        <h2 className="text-2xl font-semibold text-[#0F172A] mb-3">Next Steps</h2>
        <p className="text-sm text-[#64748B] font-normal leading-relaxed">
          Complete each day's activities and track your progress. After completing the 7-day plan, 
          return to the Analysis page to see your improved score!
        </p>
      </motion.div>
    </div>
    </div>
  );
};

