"""
Generate role-specific learning plan endpoint
"""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models.schemas import GeneratePlanResponse, PlanDay, ApplyCheckpoint
from app.services.anthropic_svc import anthropic_service
from app.services.openai_svc import openai_service
from app.services.amplitude import amplitude_service
import hashlib
import os
import json

router = APIRouter(prefix="/generatePlan", tags=["plan"])


class GeneratePlanRequest(BaseModel):
    resume_text: str
    selected_role: str
    jd_requirements: List[str]
    gaps: List[str]
    horizon_days: int = 14
    skills_core: List[str] | None = None  # Skills from resume analysis
    skills_adjacent: List[str] | None = None
    skills_advanced: List[str] | None = None


def _get_plan_schema_json() -> str:
    """Get JSON schema for GeneratePlanResponse"""
    schema = {
        "type": "object",
        "properties": {
            "role": {"type": "string"},
            "objectives": {"type": "array", "items": {"type": "string"}},
            "plan_days": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "day": {"type": "integer", "minimum": 1},
                        "title": {"type": "string"},
                        "actions": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 3}
                    },
                    "required": ["day", "title", "actions"]
                }
            },
            "deliverables": {"type": "array", "items": {"type": "string"}},
            "apply_checkpoints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "when": {"type": "string"},
                        "criteria": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["when", "criteria"]
                }
            }
        },
        "required": ["role", "objectives", "plan_days", "deliverables", "apply_checkpoints"]
    }
    return json.dumps(schema, separators=(',', ':'))


def _build_plan_prompt(resume_text: str, selected_role: str, jd_requirements: List[str], gaps: List[str], horizon_days: int, skills_core: List[str] | None = None, skills_adjacent: List[str] | None = None, skills_advanced: List[str] | None = None) -> str:
    """Build prompt for plan generation with personalized skills"""
    schema_json = _get_plan_schema_json()
    
    jd_text = "\n".join(f"- {req}" for req in jd_requirements)
    gaps_text = "\n".join(f"- {gap}" for gap in gaps)
    
    # Build skills summary for personalization
    skills_summary = ""
    if skills_core or skills_adjacent or skills_advanced:
        skills_parts = []
        if skills_core:
            skills_parts.append(f"Core skills: {', '.join(skills_core[:5])}")
        if skills_adjacent:
            skills_parts.append(f"Adjacent skills: {', '.join(skills_adjacent[:3])}")
        if skills_advanced:
            skills_parts.append(f"Advanced skills: {', '.join(skills_advanced[:2])}")
        skills_summary = "\n".join(skills_parts)
    
    prompt = f"""You are an expert career coach and learning path designer for ANY profession (tech and non-tech). Your task is to create a highly personalized, skill-level-appropriate learning plan that closes specific gaps while building on existing strengths. You have deep knowledge of online courses, platforms, and learning resources across all domains.

Resume Text:
{resume_text[:1000]}

Selected Role: {selected_role}

Candidate's Existing Skills:
{skills_summary if skills_summary else "Skills not provided - infer from resume text"}

Job Description Requirements:
{jd_text}

Identified Gaps:
{gaps_text}

Horizon: {horizon_days} days

CRITICAL INSTRUCTIONS FOR COURSE SELECTION:

1. SKILL-LEVEL MATCHING (MOST IMPORTANT):
   - Analyze candidate's existing skills carefully
   - For each gap, determine the appropriate course level:
     * If they know Python basics → recommend "Advanced Python for Data Science" (Coursera/DataCamp), NOT "Python for Beginners"
     * If they know SQL → recommend "Advanced SQL: Window Functions and CTEs" (DataCamp/Udemy), NOT "SQL Basics"
     * If they know Excel → recommend "Excel Advanced: Pivot Tables and Power Query" (LinkedIn Learning), NOT "Excel Fundamentals"
     * If they know React → recommend "TypeScript for React Developers" (Udemy), NOT "React Basics"
     * If they know EHR systems → recommend "Advanced EHR Workflows" (CITI), NOT "EHR Basics"
     * If they know GAAP → recommend "Advanced Financial Reporting" (Coursera), NOT "Accounting Basics"
   
2. SPECIFIC COURSE RECOMMENDATIONS:
   - Always include REAL, VERIFIABLE course URLs from reputable platforms:
     * Tech: DataCamp, Coursera, Udemy, freeCodeCamp, Pluralsight, LinkedIn Learning
     * ML/AI: Fast.ai, Hugging Face Courses, DeepLearning.AI (Coursera)
     * Healthcare: CITI Program, ACRP, SOCRA
     * Finance: Coursera Finance Specializations, CFA Institute
     * Education: Coursera Education courses, EdX
   - Include course titles, instructors (if known), and direct URLs
   - Example: "Complete 'Advanced SQL for Data Science' by Jose Portilla on Udemy (https://www.udemy.com/course/advanced-sql-for-data-science/)"
   - Example: "Take 'Machine Learning Specialization' by Andrew Ng on Coursera (https://www.coursera.org/specializations/machine-learning-introduction)"
   
3. GAP-SPECIFIC LEARNING:
   - Map each gap to a specific course or learning resource
   - If gap is "Advanced SQL (window functions, CTEs)" and they know SQL basics:
     * Course: "Advanced SQL: Window Functions" on DataCamp
     * Project: "Build a SQL window functions notebook on GitHub"
   - If gap is "TypeScript" and they know React:
     * Course: "TypeScript for React Developers" on Udemy
     * Project: "Convert existing React project to TypeScript"
   
4. LEARNING PATH PROGRESSION:
   - Day 1-2: Foundational concepts (if needed) or jump to intermediate if they have basics
   - Day 3-5: Hands-on practice with real projects
   - Day 6-7: Advanced topics and portfolio building
   - Each day should build on the previous day's learning
   
5. PROJECT-BASED LEARNING:
   - Every course recommendation should include a related project
   - Projects should be portfolio-worthy and demonstrate the skill
   - Example: "After completing SQL course, build a GitHub repo with 5 SQL window function examples solving real business problems"
   
6. RESOURCE QUALITY:
   - Prioritize courses with high ratings (4.5+ stars)
   - Include both free and paid options when available
   - Mention course duration and time commitment
   - Example: "Complete 'Python for Data Analysis' (8 hours, free on freeCodeCamp) OR 'Data Analysis with Python' (40 hours, paid on Coursera)"

Return STRICT minified JSON exactly matching this schema: {schema_json}

CRITICAL REQUIREMENTS:

1. objectives: List 2-4 specific objectives that directly address the gaps listed above.

2. plan_days: Generate exactly {horizon_days} days of tasks. Each day must have:
   - day: Day number (1 to {horizon_days})
   - title: Specific focus for that day
   - actions: 2-3 concrete, actionable tasks with real course URLs when applicable

3. deliverables: List 2-4 concrete deliverables that directly address the gaps. These must be role-specific and address the gaps:
   - For Data Analyst: "GitHub repo with SQL window functions notebook", "A/B test evaluation using statsmodels", "Power BI/Tableau dashboard replicating 2 JD KPIs", "Mini ETL (CSV → pandas → Snowflake/BigQuery demo)"
   - For Data Engineer: "ETL pipeline with Apache Airflow", "Data warehouse schema design", "Real-time streaming pipeline with Kafka", "SQL optimization report"
   - For Clinical Research Coordinator: "IRB protocol summary & checklist", "REDCap form + export", "Consent process script & SOP drafts", "Mock patient charting workflow"
   - For Public Health Analyst: "Epidemiology analysis using R", "Survey design document", "Policy brief template", "Outbreak investigation report"
   - For Teacher: "Sample lesson plan", "IEP template", "Assessment rubric", "Classroom management strategy document"
   - For Accountant: "QuickBooks reconciliation practice", "GAAP journal entry examples", "Financial model template", "Audit checklist"
   - For Operations Coordinator: "SOP template", "Inventory management system", "Process flow diagram", "CRM workflow documentation"
   - For AI Engineer: "ML pipeline with MLflow", "Deployed model with FastAPI", "Fine-tuned LLM with Hugging Face", "RAG implementation with vector database"
   - For Frontend Engineer: "React app with TypeScript", "Responsive design with Tailwind", "Unit tests with Jest", "Accessibility improvements with ARIA"
   - For Backend Engineer: "REST API with FastAPI", "Database optimization report", "JWT authentication implementation", "Integration test suite"

4. apply_checkpoints: List 2-3 checkpoints indicating when the candidate is ready to apply. Each checkpoint must have:
   - when: Day or milestone (e.g., "Day 5", "After completing SQL project")
   - criteria: List of specific criteria that must be met

CRITICAL COURSE SELECTION RULES:

1. SKILL-LEVEL ANALYSIS (REQUIRED FOR EVERY GAP):
   - Before recommending any course, analyze: "What does the candidate already know about this topic?"
   - If gap is "Advanced SQL" and they know SQL basics → Course: "Advanced SQL: Window Functions" (DataCamp/Udemy)
   - If gap is "TypeScript" and they know React → Course: "TypeScript for React Developers" (Udemy)
   - If gap is "Pivot Tables" and they know Excel → Course: "Excel Advanced: Pivot Tables" (LinkedIn Learning)
   - NEVER recommend beginner courses for skills they already have - always build on existing knowledge

2. SPECIFIC COURSE RECOMMENDATIONS (REQUIRED):
   - Include REAL course URLs with platform, instructor, and direct link
   - Format: "Course Name" by Instructor on Platform (URL)
   - Examples:
     * "Advanced SQL for Data Science" by Jose Portilla on Udemy (https://www.udemy.com/course/advanced-sql-for-data-science/)
     * "Machine Learning Specialization" by Andrew Ng on Coursera (https://www.coursera.org/specializations/machine-learning-introduction)
     * "TypeScript for React Developers" by Maximilian Schwarzmüller on Udemy (https://www.udemy.com/course/react-typescript/)
     * "Excel Advanced: Pivot Tables" on LinkedIn Learning (https://www.linkedin.com/learning/excel-advanced-pivot-tables)
   - Include course duration and rating when known
   - Provide both free and paid options when available

3. GAP-TO-COURSE MAPPING (REQUIRED):
   - Each gap must map to a specific course or learning resource
   - Example: Gap "Advanced SQL (window functions)" → Course "Advanced SQL: Window Functions" (DataCamp) + Project "Build SQL window functions notebook"
   - Example: Gap "TypeScript" → Course "TypeScript for React Developers" (Udemy) + Project "Convert React app to TypeScript"

4. PROJECT-BASED LEARNING (REQUIRED):
   - Every course must include a related hands-on project
   - Projects should be portfolio-worthy and demonstrate mastery
   - Example: "After SQL course, create GitHub repo with 5 SQL window function examples solving real business problems"

5. FOCUS ON GAPS ONLY:
   - Focus ONLY on gaps listed above - do NOT add generic content unless those are explicitly listed gaps
   - Tasks must be hands-on and project-based
   - Do NOT recommend courses for skills they already have (unless it's explicitly a gap)
ROLE-SPECIFIC GUIDANCE (APPLY BASED ON selected_role):

1. HEALTHCARE/CLINICAL ROLES (Clinical Research Coordinator, Medical Assistant, Registered Nurse):
   - Focus: SOPs, compliance (HIPAA/GCP), protocol reading, mock charting, vitals workflow, patient comms, IRB/REDcap tasks, clinical documentation
   - Courses: CITI Program (GCP, HIPAA), ACRP, SOCRA, Epic training, REDCap tutorials
   - Deliverables: "IRB protocol summary & checklist", "REDCap form + export", "Consent process script & SOP drafts", "Mock patient charting workflow", "HIPAA compliance checklist"
   - Projects: Create sample IRB protocol, design REDCap data collection form, draft informed consent script, build patient triage workflow
   - Example: For Clinical Research Coordinator gap "IRB submissions" → Course "CITI GCP Training" + Project "Draft IRB protocol for mock study"

2. PUBLIC HEALTH ROLES (Public Health Analyst, Epidemiologist):
   - Focus: Literature synthesis, dataset cleaning (R/Stata/SPSS), basic epi measures, visualization, policy brief
   - Courses: Coursera Epidemiology, R for Public Health, Stata tutorials, SPSS training
   - Deliverables: "Epidemiology analysis using R", "Survey design document", "Policy brief template", "Outbreak investigation report"
   - Projects: Analyze public health dataset with R, design survey questionnaire, create policy brief, build epidemiological dashboard
   - Example: For Public Health Analyst gap "SPSS proficiency" → Course "SPSS for Beginners" on Coursera + Project "Analyze health survey data with SPSS"

3. EDUCATION ROLES (Teacher, Education Coordinator):
   - Focus: Lesson plans, assessment rubrics, classroom strategy artifacts, IEP management
   - Courses: Coursera Education courses, EdX Teaching courses, Khan Academy Teacher Resources
   - Deliverables: "Sample lesson plan", "IEP template", "Assessment rubric", "Classroom management strategy document"
   - Projects: Create unit lesson plan, design assessment rubric, draft IEP for mock student, build classroom engagement strategy
   - Example: For Teacher gap "IEP management" → Course "Special Education and IEPs" on Coursera + Project "Create IEP template for diverse learners"

4. FINANCE/ACCOUNTING ROLES (Accountant, Financial Analyst):
   - Focus: Reconciliations, journal entries, small audit checklist, simple model, GAAP compliance
   - Courses: Coursera Finance Specializations, CFA Institute courses, QuickBooks training, Excel for Finance
   - Deliverables: "QuickBooks reconciliation practice", "GAAP journal entry examples", "Financial model template", "Audit checklist"
   - Projects: Reconcile sample accounts, create financial model in Excel, draft audit procedures, build budgeting template
   - Example: For Accountant gap "QuickBooks proficiency" → Course "QuickBooks Online Training" on Udemy + Project "Set up sample company in QuickBooks"

5. OPERATIONS/ADMIN ROLES (Operations Coordinator, Admin Assistant):
   - Focus: Scheduling, SOPs, inventory management, CRM systems, process documentation
   - Courses: LinkedIn Learning Operations Management, Coursera Supply Chain, CRM training
   - Deliverables: "SOP template", "Inventory management system", "Process flow diagram", "CRM workflow documentation"
   - Projects: Create SOP for common process, design inventory tracking system, build scheduling workflow, document CRM procedures
   - Example: For Operations Coordinator gap "SOPs" → Course "Process Documentation" on LinkedIn Learning + Project "Create SOP for order fulfillment"

6. TECH ROLES - Keep domain-specific, only where it closes named gaps:
   * Data Engineer: Focus on data pipelines, ETL, data warehousing, Spark, Airflow, Kafka, data modeling, SQL optimization, cloud data platforms (AWS S3/Redshift, GCP BigQuery, Azure Data Factory). Example: "Build ETL pipeline with Apache Airflow", "Design data warehouse schema", "Implement real-time data streaming with Kafka", "Optimize SQL queries for large datasets". NO generic cloud computing unless explicitly in gaps.
   * Data Analyst: "SQL window functions drills + GitHub notebook", "A/B test evaluation with statsmodels", "Build Power BI/Tableau dashboard replicating 2 JD KPIs", "One mini ETL (CSV → pandas → Snowflake/BigQuery demo)". NO AWS/DevOps unless explicitly in gaps.
   * AI Engineer: Focus on ML pipelines, model deployment, MLOps, LLMs, transformers, vector databases, model serving. Example: "Build ML pipeline with MLflow", "Deploy model with FastAPI", "Fine-tune LLM with Hugging Face", "Implement RAG with vector database". NO generic cloud computing unless explicitly in gaps.
   * Frontend Engineer: Focus on React, TypeScript, Next.js, CSS frameworks, testing, accessibility. Example: "Build React app with TypeScript", "Implement responsive design with Tailwind", "Add unit tests with Jest", "Improve accessibility with ARIA". NO backend/DevOps unless explicitly in gaps.
   * Backend Engineer: Focus on API design, database optimization, server frameworks, authentication, testing. Example: "Build REST API with FastAPI", "Optimize database queries", "Implement JWT authentication", "Add integration tests". NO frontend/DevOps unless explicitly in gaps.
   * DevOps Engineer: Focus on CI/CD, containerization, infrastructure as code, monitoring. Example: "Set up CI/CD pipeline with GitHub Actions", "Containerize app with Docker", "Deploy with Terraform", "Set up monitoring with Prometheus". NO application code unless explicitly in gaps.
- CRITICAL: If selected_role is outside any preset taxonomy, infer competencies from the JD itself: extract required tasks/skills from jd_requirements, mark missing ones as gaps, and build the plan only around those.

Return ONLY valid JSON, no markdown, no code blocks, no explanations."""
    
    return prompt


@router.post("")
async def generate_plan(
    request: GeneratePlanRequest,
    response: Response,
    hash: str | None = Query(None, description="Resume hash for cache busting")
):
    """
    Generate a role-specific learning/apply plan based on JD gaps.
    """
    try:
        # Compute resume hash
        resume_hash = hashlib.sha256(request.resume_text.encode('utf-8')).hexdigest()
        debug_hash = resume_hash[:8]
        
        # Add Cache-Control header
        response.headers["Cache-Control"] = "no-store"
        
        provider = "heuristic"
        result_dict = None
        
        # Try Anthropic first
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                prompt = _build_plan_prompt(
                    request.resume_text,
                    request.selected_role,
                    request.jd_requirements,
                    request.gaps,
                    request.horizon_days,
                    request.skills_core,
                    request.skills_adjacent,
                    request.skills_advanced
                )
                
                message = anthropic_service.client.messages.create(
                    model=anthropic_service.model,
                    max_tokens=3000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                response_text = message.content[0].text.strip()
                # Remove markdown code blocks
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                result_dict = json.loads(response_text)
                provider = "anthropic"
                print(f"[GeneratePlan] Anthropic plan successful: hash={debug_hash}, role={request.selected_role}")
            except Exception as e:
                print(f"[GeneratePlan] Anthropic failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Try OpenAI if Anthropic failed
        if not result_dict:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key and openai_service.client:
                try:
                    prompt = _build_plan_prompt(
                        request.resume_text,
                        request.selected_role,
                        request.jd_requirements,
                        request.gaps,
                        request.horizon_days,
                        request.skills_core,
                        request.skills_adjacent,
                        request.skills_advanced
                    )
                    
                    response = openai_service.client.chat.completions.create(
                        model=openai_service.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a professional career coach. Return only valid JSON matching the specified schema."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.1,
                        max_tokens=3000,
                        response_format={"type": "json_object"}
                    )
                    
                    response_text = response.choices[0].message.content.strip()
                    # Remove markdown code blocks
                    if response_text.startswith("```json"):
                        response_text = response_text[7:]
                    if response_text.startswith("```"):
                        response_text = response_text[3:]
                    if response_text.endswith("```"):
                        response_text = response_text[:-3]
                    response_text = response_text.strip()
                    
                    result_dict = json.loads(response_text)
                    provider = "openai"
                    print(f"[GeneratePlan] OpenAI plan successful: hash={debug_hash}, role={request.selected_role}")
                except Exception as e:
                    print(f"[GeneratePlan] OpenAI failed: {e}")
        
        # Fallback to heuristic if LLM not available
        if not result_dict:
            print(f"[GeneratePlan] Using heuristic fallback: hash={debug_hash}, role={request.selected_role}")
            # Generate basic plan from gaps
            plan_days = []
            for day in range(1, request.horizon_days + 1):
                if day <= len(request.gaps):
                    gap = request.gaps[day - 1]
                    plan_days.append({
                        "day": day,
                        "title": f"Address: {gap}",
                        "actions": [
                            f"Learn {gap} on Coursera (https://www.coursera.org/courses?query={gap.replace(' ', '+')})",
                            f"Practice {gap} with hands-on exercises",
                            f"Build a project demonstrating {gap}"
                        ]
                    })
                else:
                    plan_days.append({
                        "day": day,
                        "title": f"Day {day}: Review and Practice",
                        "actions": [
                            "Review previous days' concepts",
                            "Complete practice exercises",
                            "Work on portfolio project"
                        ]
                    })
            
            result_dict = {
                "role": request.selected_role,
                "objectives": [f"Close {gap}" for gap in request.gaps[:3]],
                "plan_days": plan_days,
                "deliverables": [
                    f"Portfolio project demonstrating {gap}" for gap in request.gaps[:2]
                ],
                "apply_checkpoints": [
                    {
                        "when": f"Day {request.horizon_days // 2}",
                        "criteria": ["Completed core learning tasks", "Built portfolio project"]
                    },
                    {
                        "when": f"Day {request.horizon_days}",
                        "criteria": ["All deliverables completed", "Ready to apply"]
                    }
                ]
            }
            provider = "heuristic"
        
        # Validate and return response
        try:
            plan_response = GeneratePlanResponse(**result_dict)
        except Exception as e:
            print(f"[GeneratePlan] Schema validation error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Plan generation validation failed: {str(e)}")
        
        # Send Amplitude event (only hash/role/provider, no raw text)
        amplitude_service.track(
            event_type="plan_generated",
            event_properties={
                "hash": debug_hash,
                "role": request.selected_role,
                "provider": provider,
                "horizon_days": request.horizon_days,
            }
        )
        
        # Log only hash, role, provider (no resume text)
        print(f"[GeneratePlan] Completed: hash={debug_hash}, role={request.selected_role}, provider={provider}")
        
        return plan_response.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GeneratePlan] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

