import * as amplitude from '@amplitude/analytics-browser';

const API_KEY = import.meta.env.VITE_AMPLITUDE_API_KEY;

if (API_KEY) {
  amplitude.init(API_KEY, {
    defaultTracking: true, // Enable all default tracking to silence warning
  });
}

export const track = (eventName: string, eventProperties?: Record<string, any>) => {
  if (API_KEY) {
    amplitude.track(eventName, eventProperties);
  }
};

