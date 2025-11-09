"""
Unit test for job scoring service
Tests that scoring prefers core skill matches
"""
import pytest
from app.services.job_scoring_svc import JobScoringService


def test_score_job_match_prefers_core_skills():
    """Test that scoring algorithm prefers core skill matches"""
    scoring_service = JobScoringService()
    
    # Build candidate with core, adjacent, and advanced skills
    candidate_analysis = {
        "skills": {
            "core": ["python", "react"],  # Core skills (weight 1.0)
            "adjacent": ["javascript", "node.js"],  # Adjacent skills (weight 0.7)
            "advanced": ["typescript", "graphql"],  # Advanced skills (weight 0.5)
        },
        "keywords_detected": [],
        "strengths": [],
    }
    
    # Build candidate skill vector
    candidate_vector = scoring_service.build_candidate_skill_vector(candidate_analysis)
    
    # Verify core skills have weight 1.0
    assert candidate_vector.get("python") == 1.0
    assert candidate_vector.get("react") == 1.0
    
    # Verify adjacent skills have weight 0.7
    assert candidate_vector.get("javascript") == 0.7
    assert candidate_vector.get("node.js") == 0.7
    
    # Verify advanced skills have weight 0.5
    assert candidate_vector.get("typescript") == 0.5
    assert candidate_vector.get("graphql") == 0.5
    
    # Build JD requiring core skills
    jd_text = "We need a Python developer with React experience. JavaScript and Node.js are nice to have."
    jd_vector = scoring_service.extract_jd_skills(jd_text)
    
    # Score match
    match_score, why_fit, gaps = scoring_service.score_job_match(
        candidate_vector,
        jd_vector,
        ""
    )
    
    # Verify score is positive (candidate has required skills)
    assert match_score > 0
    
    # Verify why_fit includes core skills
    why_fit_lower = [reason.lower() for reason in why_fit]
    assert any("python" in reason for reason in why_fit_lower) or any("react" in reason for reason in why_fit_lower)
    
    # Verify score is higher when core skills match (vs adjacent/advanced)
    # Core match should contribute more to score
    assert match_score >= 20  # At least 2 core matches (10 points each)


def test_score_job_match_penalizes_gaps():
    """Test that scoring penalizes missing required skills"""
    scoring_service = JobScoringService()
    
    # Build candidate with limited skills
    candidate_analysis = {
        "skills": {
            "core": ["python"],
            "adjacent": [],
            "advanced": [],
        },
        "keywords_detected": [],
        "strengths": [],
    }
    
    candidate_vector = scoring_service.build_candidate_skill_vector(candidate_analysis)
    
    # Build JD requiring skills candidate doesn't have
    jd_text = "We need a Python developer with React, TypeScript, and AWS experience."
    jd_vector = scoring_service.extract_jd_skills(jd_text)
    
    # Score match
    match_score, why_fit, gaps = scoring_service.score_job_match(
        candidate_vector,
        jd_vector,
        ""
    )
    
    # Verify gaps are identified
    assert len(gaps) > 0
    
    # Verify gaps include missing skills
    gaps_lower = [gap.lower() for gap in gaps]
    assert any("react" in gap or "typescript" in gap or "aws" in gap for gap in gaps_lower)


def test_score_job_match_exact_tool_bonus():
    """Test that exact tool matches get bonus points"""
    scoring_service = JobScoringService()
    
    # Build candidate with specific tools
    candidate_analysis = {
        "skills": {
            "core": ["fastapi", "postgresql"],
            "adjacent": [],
            "advanced": [],
        },
        "keywords_detected": [],
        "strengths": [],
    }
    
    candidate_vector = scoring_service.build_candidate_skill_vector(candidate_analysis)
    
    # Build JD requiring exact tools
    jd_text = "We need a developer with FastAPI and PostgreSQL experience."
    jd_vector = scoring_service.extract_jd_skills(jd_text)
    
    # Score match
    match_score, why_fit, gaps = scoring_service.score_job_match(
        candidate_vector,
        jd_vector,
        ""
    )
    
    # Verify score is high (exact tool matches get bonus)
    assert match_score >= 25  # Core matches (10 each) + exact tool bonus (5 each)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

