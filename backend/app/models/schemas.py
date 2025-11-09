"""
API Contract Schemas
These schemas define the strict contracts used throughout the application
"""
from typing import List, Literal
from pydantic import BaseModel, Field, HttpUrl


class Skill(BaseModel):
    name: str
    level: Literal["core", "adjacent", "advanced"]
    status: Literal["have", "gap", "learning"]


class DomainScore(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=1.0)


class SkillsBreakdown(BaseModel):
    core: List[str]
    adjacent: List[str]
    advanced: List[str]


class AnalyzeResponse(BaseModel):
    domains: List[DomainScore]
    skills: SkillsBreakdown
    strengths: List[str]
    areas_for_growth: List[str]
    recommended_roles: List[str]
    keywords_detected: List[str]
    debug: dict


class Job(BaseModel):
    id: str
    title: str
    company: str
    match: int = Field(ge=0, le=100, description="Match score from 0 to 100")
    why: List[str]
    fix: List[str]
    jdUrl: str | HttpUrl  # Allow both string and HttpUrl for flexibility
    source: str | None = Field(default=None, description="Source of job data (e.g., 'dedalus', 'fallback')")


class RoleMatchItem(BaseModel):
    title: str
    company: str
    location: str
    match: float = Field(ge=0.0, le=1.0)
    why_fit: List[str]
    gaps: List[str]
    url: str  # Changed from HttpUrl to str for flexibility (some free sources might return simple strings)
    source: str


class RoleMatchResponse(BaseModel):
    items: List[RoleMatchItem]
    debug: dict


class PlanDay(BaseModel):
    day: int
    title: str
    actions: List[str]


class ApplyCheckpoint(BaseModel):
    when: str
    criteria: List[str]


class GeneratePlanResponse(BaseModel):
    role: str
    objectives: List[str]
    plan_days: List[PlanDay]
    deliverables: List[str]
    apply_checkpoints: List[ApplyCheckpoint]


class TailorResponse(BaseModel):
    bullets: List[str]
    pitch: str
    coverLetter: str


class CoachPlan(BaseModel):
    plan: List[PlanDay]
    reminders: bool


class Prediction(BaseModel):
    baseline: float
    afterPlan: float
    delta: float


# LinkedIn Job Search Schema (RapidAPI)
class LinkedInJobSearchItem(BaseModel):
    id: str
    title: str
    company: str
    location: str | None = None
    url: str
    listed_at: str | None = None
    source: str = "linkedin"
    description_snippet: str | None = None
    matchScore: int = Field(default=0, ge=0, le=100, description="Match score from 0 to 100")
    reasons: List[str] = Field(default_factory=list, description="Top 3 match reasons")
    gaps: List[str] = Field(default_factory=list, description="Top 3 skills to improve")
    skill_breakdown: dict | None = Field(default=None, description="Detailed skill comparison breakdown")


class LinkedInJobSearchResponse(BaseModel):
    jobs: List[LinkedInJobSearchItem]
    nextCursor: str | None = None
    debug: dict | None = None

