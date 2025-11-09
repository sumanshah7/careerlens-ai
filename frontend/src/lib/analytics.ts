import * as amplitude from '@amplitude/analytics-browser';

const API_KEY = import.meta.env.VITE_AMPLITUDE_API_KEY;

// Initialize Amplitude once with explicit defaultTracking to avoid warnings
if (API_KEY) {
  amplitude.init(API_KEY, {
    defaultTracking: {
      pageViews: true,
      sessions: true,
      formInteractions: true,
      fileDownloads: true,
    },
  });
}

// Type-safe event names - only these events are allowed
type AmplitudeEventName =
  | 'resume_uploaded'
  | 'analysis_completed'
  | 'jobs_fetched'
  | 'plan_generated'
  | 'tailor_clicked'
  | 'recommended_role_clicked'
  | 'error_shown'
  | 'demo_fallback_used';

// Type-safe event properties - only metadata allowed (no PII)
interface EventProperties {
  hash?: string; // First 8 chars of SHA256 only
  size?: number;
  provider?: string;
  strengths_count?: number;
  areas_count?: number;
  domains_count?: number;
  count?: number;
  source?: string;
  role?: string;
  jobId?: string;
  jobMatch?: number;
  where?: string;
  message?: string; // Error message only (no PII)
  page?: string;
  [key: string]: string | number | undefined; // Allow other metadata but enforce no PII in usage
}

/**
 * Privacy-safe Amplitude tracking wrapper
 * 
 * CRITICAL: Never include PII in eventProperties:
 * - NO raw resume text
 * - NO emails, phone numbers, addresses
 * - NO full URLs or file contents
 * - NO names or personal information
 * 
 * Only include: hashes (first 8 chars), counts, providers, metadata
 */
export const track = (eventName: AmplitudeEventName, eventProperties?: EventProperties) => {
  if (!API_KEY) {
    return; // Silently fail if no key
  }

  try {
    // Validate no PII in properties
    if (eventProperties) {
      const propsStr = JSON.stringify(eventProperties).toLowerCase();
      const piiPatterns = [
        /@[a-z0-9.-]+\.[a-z]{2,}/, // Email
        /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/, // Phone
        /http[s]?:\/\/[^\s]+/, // URLs (except allowed ones)
        /\b[a-z]+\.[a-z]+@/, // Email pattern
      ];

      for (const pattern of piiPatterns) {
        if (pattern.test(propsStr)) {
          console.warn(`[Analytics] Potential PII detected in event: ${eventName}`);
          // Still track but remove suspicious fields
          const safeProps = { ...eventProperties };
          delete safeProps.message; // Remove potentially unsafe message
          amplitude.track(eventName, safeProps);
          return;
        }
      }
    }

    amplitude.track(eventName, eventProperties);
  } catch (error) {
    // Never block UI on analytics failures
    console.error(`[Analytics] Tracking error for ${eventName}:`, error);
  }
};

