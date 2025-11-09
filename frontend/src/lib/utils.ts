import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Check if demo mode is enabled
 * Demo mode can be enabled via:
 * 1. URL parameter ?demo=1
 * 2. localStorage flag 'careerlens_demo_mode'
 */
export function isDemo(): boolean {
  if (typeof window === 'undefined') return false;
  
  // Check URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('demo') === '1') {
    return true;
  }
  
  // Check localStorage
  const demoFlag = localStorage.getItem('careerlens_demo_mode');
  if (demoFlag === 'true') {
    return true;
  }
  
  return false;
}

/**
 * Set demo mode on/off
 */
export function setDemoMode(enabled: boolean): void {
  if (typeof window === 'undefined') return;
  
  if (enabled) {
    localStorage.setItem('careerlens_demo_mode', 'true');
    // Add ?demo=1 to URL if not present
    const url = new URL(window.location.href);
    url.searchParams.set('demo', '1');
    window.history.replaceState({}, '', url.toString());
  } else {
    localStorage.removeItem('careerlens_demo_mode');
    // Remove ?demo=1 from URL
    const url = new URL(window.location.href);
    url.searchParams.delete('demo');
    window.history.replaceState({}, '', url.toString());
  }
}

