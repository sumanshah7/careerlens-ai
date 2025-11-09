/**
 * Smoke test for LinkedInJobCard component
 * Tests that component renders correctly with demo data (no network)
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LinkedInJobCard } from '../LinkedInJobCard';
import type { LinkedInJobSearchItem } from '../../types';

// Demo job data (no network required)
const demoJob: LinkedInJobSearchItem = {
  id: "demo-job-1",
  title: "AI Engineer",
  company: "Tech Corp",
  location: "San Francisco, CA",
  url: "https://www.linkedin.com/jobs/view/demo1",
  listed_at: new Date().toISOString(),
  source: "demo",
  description_snippet: "We are looking for an AI Engineer with experience in PyTorch, TensorFlow, and MLOps...",
  matchScore: 88,
  reasons: [
    "Python experience matches requirements",
    "Deep learning framework knowledge",
    "ML expertise aligns with role",
  ],
  gaps: [
    "MLOps and model deployment",
    "LLM fine-tuning experience",
  ],
};

describe('LinkedInJobCard', () => {
  it('renders job card with demo data', () => {
    render(<LinkedInJobCard job={demoJob} onTailor={() => {}} />);
    
    // Verify job title is rendered
    expect(screen.getByText('AI Engineer')).toBeInTheDocument();
    
    // Verify company is rendered
    expect(screen.getByText('Tech Corp')).toBeInTheDocument();
    
    // Verify location is rendered (text may be split across elements with emoji)
    expect(screen.getByText(/San Francisco, CA/)).toBeInTheDocument();
    
    // Verify match score is rendered
    expect(screen.getByText(/88/)).toBeInTheDocument();
  });
  
  it('renders match reasons', () => {
    render(<LinkedInJobCard job={demoJob} onTailor={() => {}} />);
    
    // Verify at least one reason is rendered
    expect(screen.getByText(/Python experience matches requirements/)).toBeInTheDocument();
  });
  
  it('renders skill gaps', () => {
    render(<LinkedInJobCard job={demoJob} onTailor={() => {}} />);
    
    // Verify at least one gap is rendered
    expect(screen.getByText(/MLOps and model deployment/)).toBeInTheDocument();
  });
  
  it('handles missing optional fields gracefully', () => {
    const minimalJob: LinkedInJobSearchItem = {
      id: "minimal-job",
      title: "Software Engineer",
      company: "Company",
      url: "https://example.com/job",
      source: "demo",
      matchScore: 50,
      reasons: [],
      gaps: [],
    };
    
    render(<LinkedInJobCard job={minimalJob} onTailor={() => {}} />);
    
    // Verify component still renders
    expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    expect(screen.getByText('Company')).toBeInTheDocument();
  });
});

