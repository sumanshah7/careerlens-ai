"""
OpenAI service for resume tailoring and analysis using GPT
"""
import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from pydantic import ValidationError
from app.models.schemas import TailorResponse, AnalyzeResponse
from app.config import settings
from app.services.pii_redaction import redact_pii


class OpenAIService:
    def __init__(self):
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        # Add timeout to prevent hanging (60 seconds for connection, 90 seconds for read)
        self.client = OpenAI(
            api_key=api_key,
            timeout=90.0,  # 90 seconds total timeout
            max_retries=2  # Limit retries to avoid long waits
        ) if api_key else None
        # Try gpt-4o first, fallback to gpt-4o-mini
        self.model = "gpt-4o"  # Will check availability
        self.fallback_model = "gpt-4o-mini"
        self.max_retries = 3

    def _get_schema_json(self) -> str:
        """Get the JSON schema for TailorResponse as a minified string"""
        schema = {
            "type": "object",
            "properties": {
                "bullets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 4,
                    "maxItems": 6
                },
                "pitch": {"type": "string"},
                "coverLetter": {"type": "string"},
                "evidenceUsed": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "pointsToInclude": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 8
                }
            },
            "required": ["bullets", "pitch", "coverLetter", "evidenceUsed"]
        }
        return json.dumps(schema, separators=(',', ':'))

    def _extract_job_requirements(self, jd: str) -> Dict[str, Any]:
        """
        Extract key requirements and details from job description.
        
        Args:
            jd: Job description text
            
        Returns:
            Dict with extracted requirements, skills, responsibilities, etc.
        """
        import re
        
        jd_lower = jd.lower()
        requirements = {
            "job_title": None,
            "company": None,
            "required_skills": [],
            "preferred_skills": [],
            "responsibilities": [],
            "qualifications": [],
            "years_experience": None,
            "education": None,
            "location": None,
            "keywords": []
        }
        
        # Extract job title
        title_patterns = [
            r'(?:position|role|job|opening|title)[:\s]+([A-Z][a-zA-Z\s]+(?:Engineer|Analyst|Developer|Manager|Specialist|Coordinator|Assistant|Architect))',
            r'([A-Z][a-zA-Z\s]+(?:Engineer|Analyst|Developer|Manager|Specialist|Coordinator|Assistant|Architect))',
            r'we are looking for (?:a|an) ([a-zA-Z\s]+(?:engineer|analyst|developer|manager|specialist|coordinator|assistant|architect))',
        ]
        for pattern in title_patterns:
            match = re.search(pattern, jd, re.IGNORECASE)
            if match:
                requirements["job_title"] = match.group(1).strip()
                break
        
        # Extract company name
        company_patterns = [
            r'(?:at|join|work for) ([A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Ltd|Company|Technologies|Systems))',
            r'([A-Z][a-zA-Z\s&]+) is (?:looking|seeking|hiring)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, jd, re.IGNORECASE)
            if match:
                requirements["company"] = match.group(1).strip()
                break
        
        # Extract required skills
        required_skills_patterns = [
            r'required[:\s]+([^\.]+)',
            r'must have[:\s]+([^\.]+)',
            r'requirements[:\s]+([^\.]+)',
        ]
        for pattern in required_skills_patterns:
            matches = re.finditer(pattern, jd, re.IGNORECASE)
            for match in matches:
                skills_text = match.group(1)
                # Extract common skills
                common_skills = ["python", "sql", "react", "typescript", "javascript", "java", "aws", "azure", "gcp", "docker", "kubernetes", "pytorch", "tensorflow", "machine learning", "ml", "ai", "data analysis", "excel", "power bi", "tableau", "spark", "kafka", "airflow", "dbt", "terraform", "ansible", "jenkins", "ci/cd"]
                for skill in common_skills:
                    if skill in skills_text.lower() and skill not in requirements["required_skills"]:
                        requirements["required_skills"].append(skill)
        
        # Extract preferred skills
        preferred_patterns = [
            r'preferred[:\s]+([^\.]+)',
            r'nice to have[:\s]+([^\.]+)',
            r'bonus[:\s]+([^\.]+)',
        ]
        for pattern in preferred_patterns:
            matches = re.finditer(pattern, jd, re.IGNORECASE)
            for match in matches:
                skills_text = match.group(1)
                common_skills = ["python", "sql", "react", "typescript", "javascript", "java", "aws", "azure", "gcp", "docker", "kubernetes", "pytorch", "tensorflow", "machine learning", "ml", "ai", "data analysis", "excel", "power bi", "tableau", "spark", "kafka", "airflow", "dbt", "terraform", "ansible", "jenkins", "ci/cd"]
                for skill in common_skills:
                    if skill in skills_text.lower() and skill not in requirements["preferred_skills"]:
                        requirements["preferred_skills"].append(skill)
        
        # Extract years of experience
        years_pattern = re.compile(r'(\d+)\s*(?:\+)?\s*years?\s*(?:of\s*)?(?:experience|exp)')
        years_match = years_pattern.search(jd_lower)
        if years_match:
            requirements["years_experience"] = years_match.group(1)
        
        # Extract responsibilities (look for bullet points or numbered lists)
        responsibility_patterns = [
            r'(?:responsibilities|duties|what you\'ll do|key responsibilities)[:\s]+([^\.]+)',
            r'[•\-\*]\s*([^•\-\*]+)',
            r'\d+\.\s*([^\.]+)',
        ]
        for pattern in responsibility_patterns:
            matches = re.finditer(pattern, jd, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                resp = match.group(1).strip()
                if len(resp) > 10 and len(resp) < 200:
                    requirements["responsibilities"].append(resp)
        
        # Extract qualifications
        qual_patterns = [
            r'(?:qualifications|requirements|must have)[:\s]+([^\.]+)',
        ]
        for pattern in qual_patterns:
            matches = re.finditer(pattern, jd, re.IGNORECASE)
            for match in matches:
                qual = match.group(1).strip()
                if len(qual) > 10:
                    requirements["qualifications"].append(qual)
        
        # Extract location
        location_patterns = [
            r'(?:location|based in|remote|hybrid|on-site)[:\s]+([^\.]+)',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, jd, re.IGNORECASE)
            if match:
                requirements["location"] = match.group(1).strip()
                break
        
        # Extract keywords (common tech terms)
        keywords = []
        common_keywords = ["python", "sql", "react", "typescript", "javascript", "java", "aws", "azure", "gcp", "docker", "kubernetes", "pytorch", "tensorflow", "machine learning", "ml", "ai", "data analysis", "excel", "power bi", "tableau", "spark", "kafka", "airflow", "dbt", "terraform", "ansible", "jenkins", "ci/cd", "api", "rest", "graphql", "microservices", "cloud", "devops", "data engineer", "data analyst", "software engineer", "full stack", "backend", "frontend"]
        for keyword in common_keywords:
            if keyword in jd_lower:
                keywords.append(keyword)
        requirements["keywords"] = keywords[:20]  # Limit to top 20
        
        return requirements

    def _extract_resume_evidence(self, resume: str, max_snippets: int = 20) -> list[str]:
        """
        Extract evidence tokens/snippets from resume (tools, frameworks, metrics, team sizes, project names).
        
        Args:
            resume: Resume text
            max_snippets: Maximum number of evidence snippets to extract
            
        Returns:
            List of evidence tokens/snippets
        """
        import re
        
        evidence = []
        resume_lower = resume.lower()
        
        # Extract tools and frameworks
        tools_frameworks = [
            "python", "sql", "react", "typescript", "javascript", "java", "aws", "azure", "gcp",
            "docker", "kubernetes", "pytorch", "tensorflow", "sklearn", "pandas", "numpy",
            "fastapi", "django", "flask", "express", "spring", "postgresql", "mongodb",
            "spark", "kafka", "airflow", "dbt", "terraform", "ansible", "jenkins",
            "power bi", "tableau", "looker", "excel", "snowflake", "bigquery", "redshift"
        ]
        for tool in tools_frameworks:
            if tool in resume_lower:
                # Find context around the tool
                pattern = rf'.{{0,30}}{re.escape(tool)}.{{0,30}}'
                matches = re.finditer(pattern, resume, re.IGNORECASE)
                for match in matches:
                    snippet = match.group(0).strip()
                    if snippet not in evidence and len(snippet) > 10:
                        evidence.append(snippet)
        
        # Extract metrics (percentages, numbers, dollar amounts)
        percent_pattern = re.compile(r'.{0,30}\d+(?:\.\d+)?\s*%.{0,30}', re.IGNORECASE)
        for match in percent_pattern.finditer(resume):
            snippet = match.group(0).strip()
            if snippet not in evidence and len(snippet) > 10:
                evidence.append(snippet)
        
        # Extract numbers (team sizes, user counts, etc.)
        number_pattern = re.compile(r'.{0,30}\b(\d+(?:,\d+)?)\s*(?:engineers?|users?|requests?|req/day|team|people|members?).{0,30}', re.IGNORECASE)
        for match in number_pattern.finditer(resume):
            snippet = match.group(0).strip()
            if snippet not in evidence and len(snippet) > 10:
                evidence.append(snippet)
        
        # Extract project names (capitalized phrases)
        project_pattern = re.compile(r'\b([A-Z][a-zA-Z\s]{5,30}(?:Project|System|Platform|Service|Application|App))\b')
        for match in project_pattern.finditer(resume):
            snippet = match.group(1).strip()
            if snippet not in evidence:
                evidence.append(snippet)
        
        # Extract action verbs with achievements (STAR format)
        action_verbs = ["developed", "led", "implemented", "created", "built", "designed", "managed", "improved", "optimized", "delivered", "reduced", "increased", "scaled", "architected"]
        for verb in action_verbs:
            pattern = rf'.{{0,50}}{re.escape(verb)}.{{0,100}}'
            matches = re.finditer(pattern, resume, re.IGNORECASE)
            for match in matches:
                snippet = match.group(0).strip()
                if snippet not in evidence and len(snippet) > 20 and len(snippet) < 150:
                    evidence.append(snippet)
        
        # Remove duplicates and limit
        unique_evidence = []
        seen = set()
        for item in evidence:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                unique_evidence.append(item)
                if len(unique_evidence) >= max_snippets:
                    break
        
        return unique_evidence[:max_snippets]

    def _build_prompt(self, resume: str, jd: str, style: str = "STAR", is_retry: bool = False, job_title: str | None = None, company: str | None = None, resume_evidence: list[str] | None = None, strict_retry: bool = False, emphasize_metrics: bool = False) -> str:
        """Build the prompt for GPT"""
        schema_json = self._get_schema_json()
        
        # Extract job requirements from JD
        job_requirements = self._extract_job_requirements(jd)
        
        # Use extracted job title if not provided
        if not job_title and job_requirements["job_title"]:
            job_title = job_requirements["job_title"]
        
        # Use extracted company if not provided
        if not company and job_requirements["company"]:
            company = job_requirements["company"]
        
        # Build job context for better personalization
        job_context = ""
        if job_title:
            job_context += f"\nJOB TITLE: {job_title}"
        if company:
            job_context += f"\nCOMPANY: {company}"
        
        # Build extracted requirements summary
        requirements_summary = ""
        if job_requirements["required_skills"]:
            requirements_summary += f"\nREQUIRED SKILLS: {', '.join(job_requirements['required_skills'][:10])}"
        if job_requirements["preferred_skills"]:
            requirements_summary += f"\nPREFERRED SKILLS: {', '.join(job_requirements['preferred_skills'][:10])}"
        if job_requirements["years_experience"]:
            requirements_summary += f"\nYEARS OF EXPERIENCE REQUIRED: {job_requirements['years_experience']}"
        if job_requirements["responsibilities"]:
            requirements_summary += f"\nKEY RESPONSIBILITIES:\n" + "\n".join([f"- {r}" for r in job_requirements["responsibilities"][:5]])
        if job_requirements["keywords"]:
            requirements_summary += f"\nKEYWORDS: {', '.join(job_requirements['keywords'][:15])}"
        
        # Build must-have skills from JD
        must_haves = job_requirements.get("required_skills", [])[:10]
        must_haves_text = ", ".join(must_haves) if must_haves else "See job description"
        
        if strict_retry or is_retry:
            retry_instruction = "\n\nCRITICAL: Your previous output failed validation. You MUST:\n- Use at least 3 unique resume evidence tokens in bullets\n- Mention the exact role and company names\n- Include measurable impact in STAR format\n- Avoid all boilerplate phrases\n- Ensure bullets start with different verbs\n- Pitch MUST be 45-60 words (NOT just a sentence!)\n- Cover letter MUST be 150-250 words with 3-4 paragraphs (NOT just a sentence!)\n- Generate FULL, complete content - not truncated or incomplete\n"
        else:
            retry_instruction = ""
        
        if emphasize_metrics:
            retry_instruction += "\n\nMETRIC EMPHASIS: Prioritize quantifiable outcomes (percentages, numbers, dollar amounts, timeframes) in bullets. Include metrics from resume evidence wherever possible.\n"
        
        base_prompt = f"""You write tailored application materials strictly grounded in the candidate's resume and the provided job description.

YOUR PRIMARY TASK: Analyze the candidate's resume to identify their ACTUAL role/domain, then customize ALL content (bullets, pitch, cover letter) specifically for the TARGET JOB ROLE while using ONLY experiences from the resume.

CRITICAL ROLE CUSTOMIZATION RULES:
1. FIRST: Identify the candidate's actual role/domain from their resume (e.g., Data Analyst, AI Engineer, Medical Assistant, Teacher, Accountant, etc.)
2. SECOND: Analyze the TARGET JOB ROLE requirements from the job description
3. THIRD: Match resume experiences to job requirements - highlight experiences that align with the target role
4. FOURTH: Customize pitch and cover letter to speak directly to the target role's needs and responsibilities
5. The pitch and cover letter MUST be different for different roles - a Data Analyst pitch should focus on data analysis, an AI Engineer pitch should focus on ML/AI, a Medical Assistant pitch should focus on patient care, etc.

Rules:
- Never invent experience or tools not in the resume.
- Each bullet must be STAR-style and quantify impact where possible.
- Use the exact role and company names from the JD.
- Avoid boilerplate like "passionate", "results-driven", "dynamic", "seasoned professional", "fast-paced environment", "team player", "synergy".
- Output valid JSON only and nothing else.
- Prefer concrete nouns, verbs, metrics and named tools from the resume evidence.
- If evidence is missing for a claim, omit it.{retry_instruction}

TARGET JOB ROLE: {job_title or 'See job description'}
COMPANY: {company or 'See job description'}

JOB DESCRIPTION (Analyze requirements carefully):
{jd}

EXTRACTED JOB REQUIREMENTS:
{requirements_summary}

RESUME EVIDENCE (top 12-20 snippets from resume - use these tokens):
{evidence_summary}

MUST-HAVE SKILLS FROM JOB DESCRIPTION:
{must_haves_text}

word_limits (CRITICAL - These are MINIMUM requirements, not suggestions):
- bullet_max_words: 28 (each bullet must be substantial, not just a few words)
- pitch_words: 45-60 (MUST be at least 45 words - include role, company, skills, fit, enthusiasm)
- cover_letter_words: 150-250 (MUST be at least 150 words - MUST have 3-4 full paragraphs)

CRITICAL - READ THIS CAREFULLY:
The pitch and cover letter MUST be FULL, complete content. DO NOT generate just a sentence or two. 

FOR PITCH:
- MUST be 45-60 words (NOT 5-10 words!)
- MUST be a complete paragraph with multiple sentences
- MUST include: role title, company name, key skills from resume, why you're a fit, enthusiasm
- Example of GOOD pitch (45-60 words): "I am writing to express my strong interest in the Data Analyst position at TechCorp. My experience building data pipelines using Python and SQL, combined with my expertise in Tableau and Power BI, makes me an ideal fit for this role. I am excited to bring my analytical skills to your team."
- Example of BAD pitch (too short): "Applying for Data Analyst at TechCorp." ❌ DO NOT GENERATE THIS!

FOR COVER LETTER:
- MUST be 150-250 words (NOT 20-50 words!)
- MUST have 3-4 paragraphs separated by blank lines (\n\n)
- MUST include: opening hook (40-60 words), value proposition (50-70 words), specific example (40-60 words), closing enthusiasm (30-40 words)
- Example of GOOD cover letter (150-250 words with 3-4 paragraphs): See examples below
- Example of BAD cover letter (too short): "I am applying for the Data Analyst position at TechCorp." ❌ DO NOT GENERATE THIS!

If you generate content that is too short, the system will reject it and you will need to retry. Generate FULL, complete content from the start.

Return JSON matching this schema: {schema_json}

JSON format:
{{
  "bullets": ["<max 28 words each, 4-6 items, STAR with metrics>"],
  "pitch": "<MUST be 45-60 words - NOT just a sentence! Include: role title, company name, key skills from resume, why you're a fit, enthusiasm>",
  "coverLetter": "<MUST be 150-250 words - NOT just a sentence! MUST have 3-4 paragraphs with clear structure: opening hook (40-60 words), value proposition (50-70 words), specific example (40-60 words), closing enthusiasm (30-40 words)>",
  "evidenceUsed": ["<IDs or short substrings from resume_evidence used>"],
  "pointsToInclude": ["<3-8 specific, actionable suggestions for what to add to resume based on job requirements vs current resume>"]
}}

COVER LETTER STRUCTURE (CRITICAL - Follow this exact format):
Paragraph 1 (Opening - 40-60 words):
- Start with a strong opening that shows you understand the role and company
- Mention the specific job title and company name
- Express genuine interest in the position
- Example: "I am writing to express my strong interest in the [Job Title] position at [Company]. Your focus on [specific company value/mission from JD] aligns perfectly with my experience in [relevant area from resume]."

Paragraph 2 (Value Proposition - 50-70 words):
- Connect your key skills/experiences from the resume to the job requirements
- Highlight 2-3 most relevant achievements or experiences
- Use specific examples from resume evidence
- Show how you can contribute to the company's needs
- Example: "In my previous role, I [specific achievement from resume] which directly relates to your requirement for [specific JD requirement]. My experience with [specific tool/skill from resume] has enabled me to [specific outcome], and I'm excited to bring this expertise to [Company]."

Paragraph 3 (Specific Example - 40-60 words):
- Tell a brief, concrete story from your resume that demonstrates relevant skills
- Use STAR format: Situation, Task, Action, Result
- Make it specific and memorable
- Example: "For example, when I [specific situation from resume], I [specific action] using [specific tool/skill], resulting in [specific result/metric from resume]. This experience has prepared me to [relevant JD requirement]."

Paragraph 4 (Closing - 30-40 words):
- Reiterate enthusiasm for the role
- Mention one specific thing about the company/role that excites you
- Express eagerness to discuss further
- Example: "I am particularly excited about [specific aspect from JD] and would welcome the opportunity to discuss how my background in [relevant area] can contribute to [Company]'s success."

IMPORTANT: For "pointsToInclude", analyze the job description requirements and compare them to what's in the resume. Generate 3-8 specific, actionable suggestions for what the candidate should add to their resume to better match the job. Examples:
- "Add experience with [specific tool/technology] mentioned in job requirements"
- "Include quantifiable metrics (e.g., 'improved performance by X%', 'reduced costs by $Y')"
- "Highlight experience with [specific skill/responsibility] from job description"
- "Add examples of [specific type of project/achievement] relevant to this role"
Make each point specific, actionable, and directly tied to the job requirements.

CRITICAL RULES - MUST FOLLOW (NO EXCEPTIONS):
- All content MUST be based ONLY on information explicitly mentioned in the provided resume
- Do NOT invent, fabricate, or create any experiences, skills, achievements, metrics, numbers, percentages, dollar amounts, or results that are NOT explicitly stated in the resume
- Do NOT add quantifiable metrics (numbers, percentages, dollar amounts) unless they are explicitly mentioned in the resume
- If the resume doesn't have quantifiable metrics, use descriptive impact instead (e.g., "significantly improved", "substantially reduced", "enhanced performance") - DO NOT make up numbers
- Do NOT mention years of experience (e.g., "5+ years", "3 years") unless explicitly stated in the resume - if not mentioned, do not include it
- Customize content for the SPECIFIC job role (use the actual job title from job description, not generic "engineer" or "Frontend Engineer")
- The pitch and cover letter MUST be role-specific: 
  * For Data Analyst roles: Focus on data analysis, SQL, visualization, reporting, insights
  * For AI Engineer roles: Focus on machine learning, ML models, MLOps, AI systems
  * For Medical Assistant roles: Focus on patient care, clinical support, medical records, healthcare
  * For Teacher roles: Focus on education, curriculum, student learning, classroom management
  * For DevOps roles: Focus on infrastructure, automation, CI/CD, cloud platforms
  * For other roles: Analyze the job requirements and customize accordingly
- Use keywords from the job description naturally - don't force them, but ensure role-specific terminology is used
- Maintain professional, confident tone throughout
- Ensure all content is truthful and verifiable from the resume - if you cannot verify it from the resume, DO NOT include it
- Make the cover letter feel personalized and specific to THIS job and THIS role, not generic
- Show that you understand what the company needs and how you can help
- The pitch should immediately identify the target role and connect resume experiences to that role's requirements
- The cover letter should demonstrate deep understanding of the target role's responsibilities and how the candidate's resume experiences align
- For bullet points: Only use experiences, achievements, and skills that are explicitly mentioned in the resume
- For cover letter: Only reference experiences, skills, and achievements that are explicitly mentioned in the resume
- Cover letter must tell a story: Opening hook → Value proposition → Concrete example → Enthusiastic closing
- Each paragraph should flow naturally into the next, creating a compelling narrative
- Use active voice and strong action verbs from the resume
- Show, don't tell: Use specific examples rather than generic statements
- Make it conversational yet professional - write as if you're speaking directly to the hiring manager
- For pitch: Only mention years of experience if explicitly stated in the resume, and customize for the SPECIFIC role
- If a required skill or experience is not in the resume, DO NOT create fake bullet points - instead, focus on what IS in the resume that relates to the job
- Be honest: If the resume doesn't have strong matches for certain job requirements, acknowledge that in the content rather than making things up
- DO NOT use generic templates - every piece of content must be customized based on the actual resume and job description
- The content must be DIFFERENT for different roles - a Data Analyst resume should produce Data Analyst content, an AI Engineer resume should produce AI Engineer content, etc.

EXAMPLES OF WHAT NOT TO DO (DO NOT GENERATE THESE):
- DO NOT generate: "Developed scalable React applications using TypeScript, improving performance by 40%" if the resume doesn't mention "40%" or "performance improvement"
- DO NOT generate: "Led cross-functional teams to deliver high-quality software solutions" if the resume doesn't mention "cross-functional teams" or "led teams"
- DO NOT generate: "Implemented modern frontend architectures resulting in 50% reduction in bug reports" if the resume doesn't mention "50%" or "bug reports" or "reduction"
- DO NOT generate: "I'm a passionate frontend engineer with 5+ years of experience" if the resume doesn't mention "5 years" or "5+ years" or years of experience
- DO NOT generate: "With my extensive experience in React and TypeScript" if the resume doesn't mention "React" or "TypeScript" or "extensive experience"
- DO NOT use generic job titles like "Frontend Engineer" or "engineer" - use the ACTUAL job title from the job description

EXAMPLES OF WHAT TO DO (GENERATE THESE INSTEAD):

For Bullets:
- If resume mentions "Python" and "SQL" and job is "Data Analyst": "Developed data analysis workflows using Python and SQL to extract insights from large datasets"
- If resume mentions "PyTorch" and "machine learning" and job is "AI Engineer": "Built machine learning models using PyTorch to solve complex prediction problems"
- If resume mentions "AWS" and "Docker" and job is "DevOps Engineer": "Deployed applications on AWS using Docker containers to improve scalability"

For Pitch (MUST be customized for the specific target role):
- Data Analyst role: "I'm a data analyst with experience building data pipelines and creating visualizations. My expertise in Python, SQL, and Tableau makes me an ideal fit for this Data Analyst role at [Company]."
- AI Engineer role: "I'm an AI engineer with experience developing machine learning models and deploying ML systems. My expertise in PyTorch, TensorFlow, and MLOps makes me an ideal fit for this AI Engineer role at [Company]."
- Medical Assistant role: "I'm a medical assistant with experience providing patient care and managing clinical workflows. My expertise in patient assessment, medical records, and clinical procedures makes me an ideal fit for this Medical Assistant role at [Company]."
- Teacher role: "I'm a teacher with experience developing curriculum and managing classrooms. My expertise in lesson planning, student assessment, and educational technology makes me an ideal fit for this Teacher role at [Company]."
- DevOps Engineer role: "I'm a DevOps engineer with experience automating deployments and managing cloud infrastructure. My expertise in AWS, Docker, and CI/CD makes me an ideal fit for this DevOps Engineer role at [Company]."
- If resume doesn't mention years: Use the ACTUAL job title from job description and focus on relevant experiences from resume
- If resume mentions years: Include years ONLY if explicitly stated in resume
- ALWAYS use the ACTUAL job title from the job description, not generic terms

For Cover Letter (MUST be customized for the specific target role):

Example 1 - Data Analyst Role:
"I am writing to express my strong interest in the Data Analyst position at TechCorp. Your focus on data-driven decision making aligns perfectly with my experience building analytical solutions.

In my previous role, I developed automated reporting dashboards using Python and SQL that reduced reporting time by 60%, which directly relates to your requirement for data analysis and visualization. My experience with Tableau and Power BI has enabled me to transform complex datasets into actionable insights, and I'm excited to bring this expertise to TechCorp.

For example, when I was tasked with analyzing customer behavior patterns, I built a Python-based ETL pipeline that processed 2 million records daily, resulting in a 40% improvement in marketing campaign targeting. This experience has prepared me to handle the large-scale data analysis your team requires.

I am particularly excited about TechCorp's commitment to innovation in data science and would welcome the opportunity to discuss how my background in data analysis can contribute to your team's success."

Example 2 - AI Engineer Role:
"I am writing to express my strong interest in the AI Engineer position at AI Innovations. Your focus on developing cutting-edge machine learning solutions aligns perfectly with my experience building and deploying ML models.

In my previous role, I developed deep learning models using PyTorch that improved prediction accuracy by 35%, which directly relates to your requirement for ML model development. My experience with transformer architectures and MLOps has enabled me to deploy production-ready AI systems, and I'm excited to bring this expertise to AI Innovations.

For example, when I was tasked with building a recommendation system, I implemented a transformer-based model that processed 10 million user interactions daily, resulting in a 25% increase in user engagement. This experience has prepared me to handle the large-scale ML infrastructure your team requires.

I am particularly excited about AI Innovations' commitment to advancing AI research and would welcome the opportunity to discuss how my background in machine learning can contribute to your team's success."

Example 3 - Medical Assistant Role:
"I am writing to express my strong interest in the Medical Assistant position at HealthCare Plus. Your focus on providing quality patient care aligns perfectly with my experience supporting clinical operations.

In my previous role, I assisted physicians with patient examinations and managed electronic health records, which directly relates to your requirement for clinical support. My experience with patient assessment and medical documentation has enabled me to ensure efficient clinical workflows, and I'm excited to bring this expertise to HealthCare Plus.

For example, when I was tasked with managing a high-volume clinic, I streamlined patient intake processes and maintained accurate medical records for over 50 patients daily, resulting in improved patient satisfaction scores. This experience has prepared me to handle the fast-paced clinical environment your team requires.

I am particularly excited about HealthCare Plus' commitment to patient-centered care and would welcome the opportunity to discuss how my background in medical assistance can contribute to your team's success."

IMPORTANT: The cover letter MUST be customized for the SPECIFIC target role. Use role-specific language, responsibilities, and examples that match the job description.

VALIDATION CHECKLIST - Before generating content, verify:
1. Every bullet point must reference something explicitly mentioned in the resume
2. Every metric (number, percentage, dollar amount) must be explicitly mentioned in the resume
3. Years of experience must be explicitly mentioned in the resume (if included)
4. Every skill mentioned must be explicitly mentioned in the resume
5. Every achievement mentioned must be explicitly mentioned in the resume
6. The job title used must match the ACTUAL job title from the job description
7. The content must be customized for the SPECIFIC role, not generic
8. Cover letter has 3-4 paragraphs with clear structure (opening, value prop, example, closing)
9. Cover letter tells a story and flows naturally from paragraph to paragraph
10. Cover letter uses specific examples from resume evidence, not generic statements
11. Cover letter shows genuine enthusiasm and understanding of the role/company
12. Cover letter is 150-250 words (not too short, not too long)
13. Pitch is customized for the SPECIFIC target role (e.g., Data Analyst pitch focuses on data analysis, AI Engineer pitch focuses on ML/AI)
14. Cover letter is customized for the SPECIFIC target role (uses role-specific language, responsibilities, and examples)
15. Both pitch and cover letter mention the ACTUAL job title from the job description, not generic terms
16. The content demonstrates understanding of the target role's requirements and how the candidate's resume experiences align

Return STRICT minified JSON exactly matching this schema: {schema_json}

Return ONLY valid JSON, no markdown, no code blocks, no explanations."""

        return base_prompt

    def _validate_tailor_output(self, data: Dict[str, Any], resume: str, jd: str, job_title: str | None = None, company: str | None = None, resume_evidence: list[str] | None = None) -> tuple[bool, list[str]]:
        """
        Validate tailor output against strict requirements.
        
        Args:
            data: Generated tailor response data
            resume: Original resume text
            jd: Job description text
            job_title: Job title from job description
            company: Company name from job description
            resume_evidence: List of resume evidence tokens
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        import re
        from difflib import SequenceMatcher
        
        errors = []
        resume_lower = resume.lower()
        jd_lower = jd.lower()
        
        # Extract job title and company from JD if not provided
        if not job_title:
            job_title_match = re.search(r'(?:position|role|job|opening|title)[:\s]+([A-Z][a-zA-Z\s]+(?:Engineer|Analyst|Developer|Manager|Specialist|Coordinator|Assistant|Architect))', jd, re.IGNORECASE)
            if job_title_match:
                job_title = job_title_match.group(1).strip()
        
        if not company:
            company_match = re.search(r'(?:at|join|work for) ([A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Ltd|Company|Technologies|Systems))', jd, re.IGNORECASE)
            if company_match:
                company = company_match.group(1).strip()
        
        job_title_lower = (job_title or "").lower()
        company_lower = (company or "").lower()
        
        # Extract resume evidence if not provided
        if resume_evidence is None:
            resume_evidence = self._extract_resume_evidence(resume, max_snippets=20)
        
        # Extract must-have skills from JD
        must_haves = []
        required_patterns = [r'required[:\s]+([^\.]+)', r'must have[:\s]+([^\.]+)', r'requirements[:\s]+([^\.]+)']
        for pattern in required_patterns:
            matches = re.finditer(pattern, jd, re.IGNORECASE)
            for match in matches:
                skills_text = match.group(1)
                common_skills = ["python", "sql", "react", "typescript", "javascript", "java", "aws", "azure", "gcp", "docker", "kubernetes", "pytorch", "tensorflow", "machine learning", "ml", "ai", "data analysis", "excel", "power bi", "tableau", "spark", "kafka", "airflow", "dbt", "terraform", "ansible", "jenkins", "ci/cd"]
                for skill in common_skills:
                    if skill in skills_text.lower() and skill not in must_haves:
                        must_haves.append(skill)
        
        bullets = data.get("bullets", [])
        pitch = data.get("pitch", "")
        cover_letter = data.get("coverLetter", "")
        evidence_used = data.get("evidenceUsed", [])
        
        # 1. Company & Role presence check
        if job_title and job_title_lower not in pitch.lower():
            errors.append(f"Pitch must mention job title '{job_title}'")
        if company and company_lower not in pitch.lower():
            errors.append(f"Pitch must mention company '{company}'")
        if job_title and job_title_lower not in cover_letter.lower():
            errors.append(f"Cover letter must mention job title '{job_title}'")
        if company and company_lower not in cover_letter.lower():
            errors.append(f"Cover letter must mention company '{company}'")
        
        # 2. Evidence grounding check
        evidence_lower = [ev.lower() for ev in resume_evidence]
        bullets_with_evidence = 0
        for bullet in bullets:
            bullet_lower = bullet.lower()
            # Check if bullet contains any evidence token
            for ev in evidence_lower:
                # Check if evidence token appears in bullet (fuzzy match for substrings)
                if len(ev) > 5 and ev in bullet_lower:
                    bullets_with_evidence += 1
                    break
        if bullets_with_evidence < 2:
            errors.append(f"At least 2 bullets must include tools/metrics from resume evidence (found {bullets_with_evidence})")
        
        # 3. Boilerplate check
        boilerplate_phrases = ["passionate", "results-driven", "dynamic", "seasoned professional", "fast-paced environment", "team player", "synergy", "proven track record", "go-getter", "self-starter"]
        all_text = " ".join(bullets) + " " + pitch + " " + cover_letter
        all_text_lower = all_text.lower()
        found_boilerplate = []
        for phrase in boilerplate_phrases:
            if phrase in all_text_lower:
                found_boilerplate.append(phrase)
        if found_boilerplate:
            errors.append(f"Found boilerplate phrases: {', '.join(found_boilerplate)}")
        
        # 4. Diversity check (bullets must start with different verbs)
        first_words = []
        for bullet in bullets:
            words = bullet.strip().split()
            if words:
                first_word = words[0].lower()
                first_words.append(first_word)
        
        # Check Levenshtein distance > 2
        for i, word1 in enumerate(first_words):
            for j, word2 in enumerate(first_words[i+1:], start=i+1):
                # Simple similarity check (not full Levenshtein, but good enough)
                similarity = SequenceMatcher(None, word1, word2).ratio()
                if similarity > 0.7:  # Too similar
                    errors.append(f"Bullets must start with different verbs (found similar: '{word1}' and '{word2}')")
                    break
            if errors:
                break
        
        # 5. Length limits check
        for i, bullet in enumerate(bullets):
            word_count = len(bullet.split())
            if word_count > 28:
                errors.append(f"Bullet {i+1} exceeds 28 words (has {word_count})")
        
        pitch_word_count = len(pitch.split())
        if pitch_word_count < 45 or pitch_word_count > 60:
            errors.append(f"Pitch must be 45-60 words (has {pitch_word_count})")
        
        cover_letter_word_count = len(cover_letter.split())
        if cover_letter_word_count < 150:
            errors.append(f"Cover letter must be at least 150 words (has {cover_letter_word_count})")
        if cover_letter_word_count > 250:
            errors.append(f"Cover letter must be 150-250 words (has {cover_letter_word_count})")
        
        # 5b. Cover letter structure check (should have 3-4 paragraphs)
        cover_letter_paragraphs = [p.strip() for p in cover_letter.split('\n\n') if p.strip()]
        if len(cover_letter_paragraphs) < 3:
            errors.append(f"Cover letter must have at least 3 paragraphs (has {len(cover_letter_paragraphs)})")
        if len(cover_letter_paragraphs) > 4:
            errors.append(f"Cover letter should have 3-4 paragraphs (has {len(cover_letter_paragraphs)})")
        
        # 6. Similarity guard (Jaccard similarity among bullets < 0.6)
        def jaccard_similarity(text1: str, text2: str) -> float:
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            intersection = words1 & words2
            union = words1 | words2
            return len(intersection) / len(union) if union else 0.0
        
        for i, bullet1 in enumerate(bullets):
            for j, bullet2 in enumerate(bullets[i+1:], start=i+1):
                similarity = jaccard_similarity(bullet1, bullet2)
                if similarity >= 0.6:
                    errors.append(f"Bullets {i+1} and {j+1} are too similar (Jaccard similarity: {similarity:.2f})")
        
        # 7. JD alignment check (at least one bullet must explicitly cover one must-have)
        if must_haves:
            bullets_covering_must_have = 0
            for bullet in bullets:
                bullet_lower = bullet.lower()
                for must_have in must_haves:
                    if must_have in bullet_lower:
                        bullets_covering_must_have += 1
                        break
            if bullets_covering_must_have == 0:
                errors.append(f"At least one bullet must explicitly cover a must-have skill from JD: {', '.join(must_haves[:5])}")
        
        return len(errors) == 0, errors

    def _validate_and_filter_content(self, data: Dict[str, Any], resume: str, jd: str, job_title: str | None = None) -> Dict[str, Any]:
        """
        Validate and filter out fake content that doesn't match the resume.
        
        Args:
            data: Generated tailor response data
            resume: Original resume text
            jd: Job description text
            job_title: Job title from job description
            
        Returns:
            Validated and filtered data
        """
        import re
        
        resume_lower = resume.lower()
        jd_lower = jd.lower()
        
        # Extract actual job title from JD if not provided
        if not job_title:
            # Try to extract job title from JD (look for common patterns)
            job_title_match = re.search(r'(?:position|role|job|opening)[:\s]+([A-Z][a-zA-Z\s]+(?:Engineer|Analyst|Developer|Manager|Specialist|Coordinator|Assistant))', jd, re.IGNORECASE)
            if job_title_match:
                job_title = job_title_match.group(1).strip()
            else:
                # Fallback: look for common job title patterns
                common_titles = ["Data Analyst", "AI Engineer", "DevOps Engineer", "Frontend Engineer", "Backend Engineer", "Software Engineer", "Data Engineer", "ML Engineer"]
                for title in common_titles:
                    if title.lower() in jd_lower:
                        job_title = title
                        break
        
        job_title_lower = (job_title or "").lower()
        
        # Extract years of experience from resume (if mentioned)
        years_pattern = re.compile(r'(\d+)\s*(?:\+)?\s*years?\s*(?:of\s*)?(?:experience|exp)')
        years_match = years_pattern.search(resume_lower)
        years_in_resume = years_match.group(1) if years_match else None
        
        # Extract metrics from resume (numbers, percentages, dollar amounts)
        metrics_in_resume = set()
        # Find percentages
        percent_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%')
        for match in percent_pattern.finditer(resume_lower):
            metrics_in_resume.add(match.group(1) + "%")
        # Find numbers (but not years of experience)
        number_pattern = re.compile(r'\b(\d+(?:,\d+)?)\b')
        for match in number_pattern.finditer(resume_lower):
            num = match.group(1)
            # Skip if it's likely a year (4 digits starting with 19 or 20)
            if not (len(num) == 4 and (num.startswith('19') or num.startswith('20'))):
                metrics_in_resume.add(num)
        
        # Extract skills from resume
        skills_in_resume = set()
        common_skills = ["python", "sql", "react", "typescript", "javascript", "java", "aws", "docker", "kubernetes", "pytorch", "tensorflow", "machine learning", "ml", "ai", "data analysis", "excel", "power bi", "tableau"]
        for skill in common_skills:
            if skill in resume_lower:
                skills_in_resume.add(skill)
        
        # Validate and filter bullets
        validated_bullets = []
        for bullet in data.get("bullets", []):
            bullet_lower = bullet.lower()
            is_valid = True
            
            # Check for fake metrics
            bullet_percentages = percent_pattern.findall(bullet_lower)
            for pct in bullet_percentages:
                if pct + "%" not in metrics_in_resume:
                    # Remove fake percentage
                    bullet = re.sub(r'\d+(?:\.\d+)?\s*%', '', bullet, flags=re.IGNORECASE)
                    is_valid = False
            
            # Check for fake years of experience
            if years_pattern.search(bullet_lower) and not years_in_resume:
                # Remove years of experience mention
                bullet = re.sub(r'\d+\s*(?:\+)?\s*years?\s*(?:of\s*)?(?:experience|exp)', '', bullet, flags=re.IGNORECASE)
                is_valid = False
            
            # Check if bullet mentions skills not in resume
            bullet_skills = [skill for skill in common_skills if skill in bullet_lower]
            if bullet_skills and not any(skill in skills_in_resume for skill in bullet_skills):
                # Keep bullet but note it might be generic
                pass
            
            # Clean up bullet (remove extra spaces, fix punctuation)
            bullet = re.sub(r'\s+', ' ', bullet).strip()
            bullet = re.sub(r'\s*,\s*,', ',', bullet)  # Remove double commas
            bullet = re.sub(r'\s*\.\s*\.', '.', bullet)  # Remove double periods
            
            if bullet and len(bullet) > 10:  # Only keep non-empty, meaningful bullets
                validated_bullets.append(bullet)
        
        # If no valid bullets, create generic ones from resume content
        if not validated_bullets:
            # Extract actual experiences from resume
            # Look for bullet points or action verbs
            action_verbs = ["developed", "led", "implemented", "created", "built", "designed", "managed", "improved", "optimized", "delivered"]
            resume_sentences = re.split(r'[.!?]\s+', resume)
            for sentence in resume_sentences[:3]:  # Take first 3 sentences
                sentence_lower = sentence.lower()
                if any(verb in sentence_lower for verb in action_verbs):
                    # Clean up and add
                    sentence = sentence.strip()
                    if len(sentence) > 20 and len(sentence) < 150:
                        validated_bullets.append(sentence)
        
        # Validate and filter pitch
        pitch = data.get("pitch", "")
        pitch_lower = pitch.lower()
        
        # Remove fake years of experience
        if years_pattern.search(pitch_lower) and not years_in_resume:
            pitch = re.sub(r'\d+\s*(?:\+)?\s*years?\s*(?:of\s*)?(?:experience|exp)', '', pitch, flags=re.IGNORECASE)
        
        # Replace generic job titles with actual job title
        generic_titles = ["frontend engineer", "engineer", "developer", "software engineer"]
        if job_title:
            for generic in generic_titles:
                if generic in pitch_lower and job_title_lower not in pitch_lower:
                    pitch = re.sub(rf'\b{re.escape(generic)}\b', job_title, pitch, flags=re.IGNORECASE)
        
        # Clean up pitch
        pitch = re.sub(r'\s+', ' ', pitch).strip()
        
        # Ensure pitch meets minimum word count (45 words)
        pitch_words = len(pitch.split())
        if pitch_words < 45:
            # Add more content to meet minimum
            if job_title and company:
                pitch += f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
            elif job_title:
                pitch += f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
            else:
                pitch += " I am confident that my skills and experience make me a strong candidate for this role."
        
        # Validate and filter cover letter
        cover_letter = data.get("coverLetter", "")
        cover_letter_lower = cover_letter.lower()
        
        # Remove fake years of experience
        if years_pattern.search(cover_letter_lower) and not years_in_resume:
            cover_letter = re.sub(r'\d+\s*(?:\+)?\s*years?\s*(?:of\s*)?(?:experience|exp)', '', cover_letter, flags=re.IGNORECASE)
        
        # Replace generic job titles with actual job title
        if job_title:
            for generic in generic_titles:
                if generic in cover_letter_lower and job_title_lower not in cover_letter_lower:
                    cover_letter = re.sub(rf'\b{re.escape(generic)}\b', job_title, cover_letter, flags=re.IGNORECASE)
        
        # Clean up cover letter
        cover_letter = re.sub(r'\s+', ' ', cover_letter).strip()
        
        # Ensure cover letter meets minimum word count (150 words) and has paragraphs
        cover_letter_words = len(cover_letter.split())
        if cover_letter_words < 150:
            # Check if it has paragraphs
            paragraphs = [p.strip() for p in cover_letter.split('\n\n') if p.strip()]
            if len(paragraphs) < 3:
                # Add more paragraphs to meet requirements
                if job_title and company:
                    additional = f"\n\nI am particularly excited about the opportunity to contribute to {company}'s mission and would welcome the chance to discuss how my background in this field can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                elif job_title:
                    additional = f"\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                else:
                    additional = "\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for this role."
                cover_letter += additional
            else:
                # Add more content to existing paragraphs
                if job_title and company:
                    cover_letter += f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                elif job_title:
                    cover_letter += f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                else:
                    cover_letter += " I am confident that my skills and experience make me a strong candidate for this role."
        
        # Extract pointsToInclude from data if present, otherwise generate default
        points_to_include = data.get("pointsToInclude", [])
        if not points_to_include or len(points_to_include) < 3:
            # Generate default points if not provided or insufficient
            points_to_include = [
                "Add quantifiable metrics to achievements (e.g., percentages, dollar amounts, timeframes)",
                "Include specific tools and technologies mentioned in the job description",
                "Highlight relevant projects or experiences that match the job requirements"
            ]
        
        return {
            "bullets": validated_bullets[:4],  # Limit to 4 bullets
            "pitch": pitch,
            "coverLetter": cover_letter,
            "pointsToInclude": points_to_include[:8]
        }

    def _create_evidence_only_draft(self, resume: str, jd: str, job_title: str | None = None, company: str | None = None, resume_evidence: list[str] | None = None, must_haves: list[str] | None = None) -> Dict[str, Any]:
        """
        Create a minimal evidence-only draft when OpenAI fails or validation fails.
        
        Args:
            resume: Resume text
            jd: Job description text
            job_title: Job title
            company: Company name
            resume_evidence: Resume evidence tokens
            must_haves: Must-have skills from JD
            
        Returns:
            Evidence-only draft with plain phrasing
        """
        import re
        
        if resume_evidence is None:
            resume_evidence = self._extract_resume_evidence(resume, max_snippets=20)
        
        if must_haves is None:
            job_requirements = self._extract_job_requirements(jd)
            must_haves = job_requirements.get("required_skills", [])[:10]
        
        # Create simple bullets from evidence + must-haves
        bullets = []
        action_verbs = ["Built", "Delivered", "Automated", "Optimized", "Scaled", "Deployed", "Designed", "Led", "Reduced", "Migrated", "Integrated", "Architected"]
        verb_idx = 0
        
        # Use first 4-6 evidence snippets that relate to must-haves or are strong
        used_evidence = []
        for ev in resume_evidence[:6]:
            if len(ev) > 10:
                verb = action_verbs[verb_idx % len(action_verbs)]
                bullets.append(f"{verb} {ev}")
                used_evidence.append(ev[:50])  # Short substring
                verb_idx += 1
                if len(bullets) >= 6:
                    break
        
        # If we need more bullets, add must-have related ones
        if len(bullets) < 4 and must_haves:
            for must_have in must_haves[:2]:
                if len(bullets) >= 6:
                    break
                verb = action_verbs[verb_idx % len(action_verbs)]
                bullets.append(f"{verb} using {must_have}")
                verb_idx += 1
        
        # Create proper pitch (45-60 words)
        pitch_parts = []
        if job_title and company:
            pitch_parts.append(f"I am writing to express my strong interest in the {job_title} position at {company}.")
        elif job_title:
            pitch_parts.append(f"I am writing to express my strong interest in the {job_title} position.")
        
        # Add skills/experience from resume evidence
        if resume_evidence:
            tools = [ev for ev in resume_evidence[:3] if len(ev) < 30 and len(ev) > 5]
            if tools:
                pitch_parts.append(f"My experience with {', '.join(tools[:2])} makes me an ideal fit for this role.")
        
        # Add value proposition
        if must_haves and resume_evidence:
            pitch_parts.append(f"I am excited to bring my expertise in {must_haves[0] if must_haves else 'this field'} to your team.")
        
        pitch = " ".join(pitch_parts)
        
        # Ensure pitch is at least 45 words
        pitch_words = len(pitch.split())
        if pitch_words < 45:
            additional = f" My background in {', '.join([ev[:20] for ev in resume_evidence[:2] if len(ev) > 5])} aligns perfectly with your requirements. I am confident that my skills and experience make me a strong candidate for this position."
            pitch += additional
        
        # Ensure pitch doesn't exceed 60 words
        pitch_words = len(pitch.split())
        if pitch_words > 60:
            words = pitch.split()
            pitch = " ".join(words[:60])
        
        # Create proper cover letter (150-250 words, 3-4 paragraphs)
        cover_letter_parts = []
        
        # Paragraph 1: Opening (40-60 words)
        if job_title and company:
            cover_letter_parts.append(f"I am writing to express my strong interest in the {job_title} position at {company}. Your focus on innovation and excellence aligns perfectly with my experience and career goals.")
        elif job_title:
            cover_letter_parts.append(f"I am writing to express my strong interest in the {job_title} position. I am excited about the opportunity to contribute to your team and bring my expertise to this role.")
        
        # Paragraph 2: Value Proposition (50-70 words)
        if resume_evidence:
            tools = [ev for ev in resume_evidence[:3] if len(ev) < 30 and len(ev) > 5]
            if tools:
                cover_letter_parts.append(f"In my previous role, I developed expertise in {', '.join(tools[:2])}, which directly relates to your requirements. My experience with these technologies has enabled me to deliver impactful results, and I'm excited to bring this expertise to your team.")
        
        # Paragraph 3: Specific Example (40-60 words)
        if resume_evidence:
            example = resume_evidence[0] if resume_evidence else ""
            if example and len(example) > 20:
                cover_letter_parts.append(f"For example, when I was tasked with {example[:50]}, I successfully delivered results that exceeded expectations. This experience has prepared me to handle the challenges your team faces.")
        
        # Paragraph 4: Closing (30-40 words)
        if company:
            cover_letter_parts.append(f"I am particularly excited about {company}'s commitment to excellence and would welcome the opportunity to discuss how my background can contribute to your team's success.")
        else:
            cover_letter_parts.append("I would welcome the opportunity to discuss how my background and experience can contribute to your team's success.")
        
        cover_letter = "\n\n".join(cover_letter_parts)
        
        # Ensure cover letter is at least 150 words
        cover_letter_words = len(cover_letter.split())
        if cover_letter_words < 150:
            additional = f" My experience includes working with {', '.join([ev[:20] for ev in resume_evidence[:3] if len(ev) > 5])} and I am confident that I can make a meaningful contribution to your organization. I look forward to the opportunity to discuss how my skills and experience align with your needs."
            cover_letter += additional
        
        # Ensure cover letter doesn't exceed 250 words
        cover_letter_words = len(cover_letter.split())
        if cover_letter_words > 250:
            words = cover_letter.split()
            cover_letter = " ".join(words[:250])
        
        # Generate points to include based on job requirements vs resume
        points_to_include = []
        if must_haves:
            resume_lower = resume.lower()
            for skill in must_haves[:5]:
                if skill.lower() not in resume_lower:
                    points_to_include.append(f"Add experience with {skill} mentioned in job requirements")
        if not points_to_include:
            points_to_include = [
                "Add quantifiable metrics to achievements (e.g., percentages, dollar amounts, timeframes)",
                "Include specific tools and technologies mentioned in the job description",
                "Highlight relevant projects or experiences that match the job requirements"
            ]
        
        return {
            "bullets": bullets[:6],
            "pitch": pitch[:60],  # Limit to 60 words
            "coverLetter": cover_letter[:250],  # Limit to 250 words
            "evidenceUsed": used_evidence[:5],
            "isEvidenceOnly": True,
            "pointsToInclude": points_to_include[:8]
        }

    def tailor_for_job(self, resume: str, jd: str, style: str = "STAR", job_title: str | None = None, company: str | None = None, emphasize_metrics: bool = False) -> Dict[str, Any]:
        """
        Tailor resume content for a specific job using GPT.
        
        Args:
            resume: Resume text
            jd: Job description text
            style: Format style (default: "STAR")
            
        Returns:
            Dict matching TailorResponse schema
            
        Raises:
            Exception: If tailoring fails after max retries
        """
        if not self.client:
            raise ValueError("OPENAI_API_KEY is not set")
        
        # Redact PII from resume and JD before sending to LLM
        redacted_resume = redact_pii(resume)
        redacted_jd = redact_pii(jd)
        
        # Stage 1: Evidence Extraction (deterministic, no LLM)
        resume_evidence = self._extract_resume_evidence(redacted_resume, max_snippets=20)
        job_requirements = self._extract_job_requirements(redacted_jd)
        must_haves = job_requirements.get("required_skills", [])[:10]
        
        last_error = None
        current_model = self.model
        validation_failed = False
        repair_attempted = False
        
        for attempt in range(self.max_retries):
            try:
                is_retry = attempt > 0
                strict_retry = validation_failed or is_retry
                # Stage 2: OpenAI Structured Writing
                prompt = self._build_prompt(redacted_resume, redacted_jd, style, is_retry, job_title, company, resume_evidence, strict_retry=strict_retry, emphasize_metrics=emphasize_metrics)
                
                try:
                    print(f"[Tailor] Attempt {attempt + 1}/{self.max_retries}: Calling OpenAI API with model {current_model}")
                    response = self.client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert resume writer and career coach. You MUST create content based ONLY on the provided resume. DO NOT invent, fabricate, or create any information that is NOT explicitly stated in the resume. DO NOT use generic templates or examples. Every piece of content must be customized based on the actual resume and job description. CRITICAL: The pitch MUST be 45-60 words (NOT just a sentence!). The cover letter MUST be 150-250 words with 3-4 paragraphs (NOT just a sentence!). Return only valid JSON matching the specified schema."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.65,  # Balanced temperature (0.6-0.75 range) to reduce templating
                        presence_penalty=0.4,  # Discourage repetition (0.3-0.6 range)
                        frequency_penalty=0.35,  # Discourage repetition (0.2-0.5 range)
                        max_tokens=4000,  # Increased for full cover letters (150-250 words) and pitch (45-60 words)
                        response_format={"type": "json_object"}
                    )
                    print(f"[Tailor] OpenAI API call successful for attempt {attempt + 1}")
                except Exception as model_error:
                    # Check if it's a model availability error and try fallback
                    error_str = str(model_error).lower()
                    if ("gpt-4o" in error_str or "model" in error_str or "not found" in error_str) and current_model == self.model:
                        # Try fallback model
                        current_model = self.fallback_model
                        if attempt < self.max_retries - 1:
                            continue
                    raise
                
                # Extract text from response
                response_text = response.choices[0].message.content.strip()
                
                # Remove markdown code blocks if present (shouldn't happen with json_object format, but just in case)
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                # Parse JSON
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    last_error = ValueError(f"Failed to parse JSON: {e}")
                    if attempt < self.max_retries - 1:
                        continue  # Retry
                    raise last_error
                
                # Validate against Pydantic schema
                try:
                    # Ensure pointsToInclude is present in data
                    if "pointsToInclude" not in data or not data.get("pointsToInclude"):
                        # Generate default points if missing
                        job_requirements = self._extract_job_requirements(jd)
                        must_haves = job_requirements.get("required_skills", [])[:10]
                        points_to_include = []
                        if must_haves:
                            resume_lower = resume.lower()
                            for skill in must_haves[:5]:
                                if skill.lower() not in resume_lower:
                                    points_to_include.append(f"Add experience with {skill} mentioned in job requirements")
                        if not points_to_include:
                            points_to_include = [
                                "Add quantifiable metrics to achievements (e.g., percentages, dollar amounts, timeframes)",
                                "Include specific tools and technologies mentioned in the job description",
                                "Highlight relevant projects or experiences that match the job requirements"
                            ]
                        data["pointsToInclude"] = points_to_include[:8]
                    
                    # Ensure all required fields are present
                    if "bullets" not in data:
                        data["bullets"] = []
                    if "pitch" not in data:
                        data["pitch"] = ""
                    if "coverLetter" not in data:
                        data["coverLetter"] = ""
                    if "evidenceUsed" not in data:
                        data["evidenceUsed"] = []
                    
                    try:
                        tailor_response = TailorResponse(**data)
                        data_dict = tailor_response.model_dump()
                    except ValidationError as ve:
                        print(f"[Tailor] Pydantic validation error: {ve}")
                        print(f"[Tailor] Data keys: {list(data.keys())}")
                        # Try to fix missing fields
                        if "pointsToInclude" not in data:
                            data["pointsToInclude"] = []
                        if "evidenceUsed" not in data:
                            data["evidenceUsed"] = []
                        if "isEvidenceOnly" not in data:
                            data["isEvidenceOnly"] = False
                        if "validationWarnings" not in data:
                            data["validationWarnings"] = []
                        # Retry validation
                        tailor_response = TailorResponse(**data)
                        data_dict = tailor_response.model_dump()
                    
                    # Check minimum word counts before validation - CRITICAL CHECK
                    pitch = data_dict.get("pitch", "").strip()
                    cover_letter = data_dict.get("coverLetter", "").strip()
                    
                    pitch_words = len(pitch.split()) if pitch else 0
                    cover_letter_words = len(cover_letter.split()) if cover_letter else 0
                    
                    print(f"[Tailor] Generated content lengths - Pitch: {pitch_words} words, Cover Letter: {cover_letter_words} words")
                    
                    if pitch_words < 45:
                        print(f"[Tailor] ❌ Pitch too short ({pitch_words} words, need 45-60). Content: '{pitch[:100]}...' Retrying...")
                        raise ValueError(f"Pitch too short - must be 45-60 words (got {pitch_words} words)")
                    
                    if cover_letter_words < 150:
                        print(f"[Tailor] ❌ Cover letter too short ({cover_letter_words} words, need 150-250). Content: '{cover_letter[:100]}...' Retrying...")
                        raise ValueError(f"Cover letter too short - must be 150-250 words (got {cover_letter_words} words)")
                    
                    # Check if cover letter has paragraphs
                    cover_letter_paragraphs = [p.strip() for p in cover_letter.split('\n\n') if p.strip()]
                    if len(cover_letter_paragraphs) < 3:
                        print(f"[Tailor] ❌ Cover letter has too few paragraphs ({len(cover_letter_paragraphs)} paragraphs, need 3-4). Retrying...")
                        raise ValueError(f"Cover letter must have 3-4 paragraphs (got {len(cover_letter_paragraphs)} paragraphs)")
                    
                    # Run strict validator (using already extracted evidence from Stage 1)
                    is_valid, validation_errors = self._validate_tailor_output(
                        data_dict,
                        resume,
                        jd,
                        job_title,
                        company,
                        resume_evidence
                    )
                    
                    if is_valid:
                        # Post-process to validate and filter out fake content
                        validated_data = self._validate_and_filter_content(
                            data_dict,
                            resume,
                            jd,
                            job_title
                        )
                        
                        # Final check: Ensure minimum word counts after post-processing
                        final_pitch = validated_data.get("pitch", "").strip()
                        final_cover_letter = validated_data.get("coverLetter", "").strip()
                        final_pitch_words = len(final_pitch.split()) if final_pitch else 0
                        final_cover_letter_words = len(final_cover_letter.split()) if final_cover_letter else 0
                        
                        print(f"[Tailor] ✅ Final content lengths after post-processing - Pitch: {final_pitch_words} words, Cover Letter: {final_cover_letter_words} words")
                        
                        if final_pitch_words < 45:
                            print(f"[Tailor] ⚠️ Pitch still too short after post-processing ({final_pitch_words} words). Adding content...")
                            # Add more content to pitch
                            if job_title and company:
                                validated_data["pitch"] = final_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                            elif job_title:
                                validated_data["pitch"] = final_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                            else:
                                validated_data["pitch"] = final_pitch + " I am confident that my skills and experience make me a strong candidate for this role."
                        
                        if final_cover_letter_words < 150:
                            print(f"[Tailor] ⚠️ Cover letter still too short after post-processing ({final_cover_letter_words} words). Adding content...")
                            # Add more paragraphs to cover letter
                            paragraphs = [p.strip() for p in final_cover_letter.split('\n\n') if p.strip()]
                            if len(paragraphs) < 3:
                                # Add missing paragraphs
                                if job_title and company:
                                    additional = f"\n\nI am particularly excited about the opportunity to contribute to {company}'s mission and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                                elif job_title:
                                    additional = f"\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                                else:
                                    additional = "\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for this role."
                                validated_data["coverLetter"] = final_cover_letter + additional
                            else:
                                # Add more content to existing paragraphs
                                if job_title and company:
                                    validated_data["coverLetter"] = final_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                                elif job_title:
                                    validated_data["coverLetter"] = final_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                                else:
                                    validated_data["coverLetter"] = final_cover_letter + " I am confident that my skills and experience make me a strong candidate for this role."
                        # Ensure pointsToInclude is present
                        if "pointsToInclude" not in validated_data or not validated_data.get("pointsToInclude"):
                            # Generate default points if missing
                            job_requirements = self._extract_job_requirements(jd)
                            must_haves = job_requirements.get("required_skills", [])[:10]
                            points_to_include = []
                            if must_haves:
                                resume_lower = resume.lower()
                                for skill in must_haves[:5]:
                                    if skill.lower() not in resume_lower:
                                        points_to_include.append(f"Add experience with {skill} mentioned in job requirements")
                            if not points_to_include:
                                points_to_include = [
                                    "Add quantifiable metrics to achievements (e.g., percentages, dollar amounts, timeframes)",
                                    "Include specific tools and technologies mentioned in the job description",
                                    "Highlight relevant projects or experiences that match the job requirements"
                                ]
                            validated_data["pointsToInclude"] = points_to_include[:8]
                        
                        # Add validation warnings if any clichés were found and removed
                        validation_warnings = []
                        if validation_errors:
                            # Check if clichés were mentioned in errors
                            cliche_errors = [e for e in validation_errors if "boilerplate" in e.lower() or "cliché" in e.lower()]
                            if cliche_errors:
                                validation_warnings.append("Generic phrasing removed")
                        validated_data["validationWarnings"] = validation_warnings
                        validated_data["isEvidenceOnly"] = False
                        return validated_data
                    else:
                        # Validation failed - run repair pass (Critique → Repair Loop)
                        if not repair_attempted and attempt < self.max_retries - 1:
                            print(f"[Tailor] Validation failed: {validation_errors}. Running repair pass...")
                            validation_failed = True
                            repair_attempted = True
                            # Retry with repair instructions
                            continue
                        else:
                            # Both attempts failed - return evidence-only draft
                            print(f"[Tailor] Validation failed after repair attempt: {validation_errors}. Returning evidence-only draft.")
                            evidence_draft = self._create_evidence_only_draft(
                                resume,
                                jd,
                                job_title,
                                company,
                                resume_evidence,
                                must_haves
                            )
                            # Ensure evidence-only draft also meets minimum word counts
                            evidence_pitch = evidence_draft.get("pitch", "").strip()
                            evidence_cover_letter = evidence_draft.get("coverLetter", "").strip()
                            evidence_pitch_words = len(evidence_pitch.split()) if evidence_pitch else 0
                            evidence_cover_letter_words = len(evidence_cover_letter.split()) if evidence_cover_letter else 0
                            
                            print(f"[Tailor] Evidence-only draft lengths - Pitch: {evidence_pitch_words} words, Cover Letter: {evidence_cover_letter_words} words")
                            
                            if evidence_pitch_words < 45:
                                print(f"[Tailor] ⚠️ Evidence-only pitch too short ({evidence_pitch_words} words). Adding content...")
                                if job_title and company:
                                    evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                                elif job_title:
                                    evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                                else:
                                    evidence_draft["pitch"] = evidence_pitch + " I am confident that my skills and experience make me a strong candidate for this role."
                            
                            if evidence_cover_letter_words < 150:
                                print(f"[Tailor] ⚠️ Evidence-only cover letter too short ({evidence_cover_letter_words} words). Adding content...")
                                paragraphs = [p.strip() for p in evidence_cover_letter.split('\n\n') if p.strip()]
                                if len(paragraphs) < 3:
                                    if job_title and company:
                                        additional = f"\n\nI am particularly excited about the opportunity to contribute to {company}'s mission and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                                    elif job_title:
                                        additional = f"\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                                    else:
                                        additional = "\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for this role."
                                    evidence_draft["coverLetter"] = evidence_cover_letter + additional
                                else:
                                    if job_title and company:
                                        evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                                    elif job_title:
                                        evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                                    else:
                                        evidence_draft["coverLetter"] = evidence_cover_letter + " I am confident that my skills and experience make me a strong candidate for this role."
                            
                            return evidence_draft
                except ValidationError as e:
                    last_error = ValueError(f"Response does not match schema: {e}")
                    if attempt < self.max_retries - 1:
                        continue  # Retry
                    # If all retries failed, return evidence-only draft
                    print(f"[Tailor] Schema validation failed after {self.max_retries} attempts: {e}. Returning evidence-only draft.")
                    evidence_draft = self._create_evidence_only_draft(
                        resume,
                        jd,
                        job_title,
                        company,
                        resume_evidence,
                        must_haves
                    )
                    # Ensure minimum word counts (same logic as above)
                    evidence_pitch = evidence_draft.get("pitch", "").strip()
                    evidence_cover_letter = evidence_draft.get("coverLetter", "").strip()
                    evidence_pitch_words = len(evidence_pitch.split()) if evidence_pitch else 0
                    evidence_cover_letter_words = len(evidence_cover_letter.split()) if evidence_cover_letter else 0
                    
                    if evidence_pitch_words < 45:
                        if job_title and company:
                            evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                        elif job_title:
                            evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                        else:
                            evidence_draft["pitch"] = evidence_pitch + " I am confident that my skills and experience make me a strong candidate for this role."
                    
                    if evidence_cover_letter_words < 150:
                        paragraphs = [p.strip() for p in evidence_cover_letter.split('\n\n') if p.strip()]
                        if len(paragraphs) < 3:
                            if job_title and company:
                                additional = f"\n\nI am particularly excited about the opportunity to contribute to {company}'s mission and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                            elif job_title:
                                additional = f"\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                            else:
                                additional = "\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for this role."
                            evidence_draft["coverLetter"] = evidence_cover_letter + additional
                        else:
                            if job_title and company:
                                evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                            elif job_title:
                                evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                            else:
                                evidence_draft["coverLetter"] = evidence_cover_letter + " I am confident that my skills and experience make me a strong candidate for this role."
                    
                    return evidence_draft
                
            except ValueError as e:
                # Retryable validation/parsing errors
                last_error = e
                if attempt < self.max_retries - 1:
                    continue
                # If all retries failed, return evidence-only draft
                print(f"[Tailor] OpenAI API failed after {self.max_retries} attempts: {e}. Returning evidence-only draft.")
                evidence_draft = self._create_evidence_only_draft(
                    resume,
                    jd,
                    job_title,
                    company,
                    resume_evidence,
                    must_haves
                )
                # Ensure minimum word counts (same logic as above)
                evidence_pitch = evidence_draft.get("pitch", "").strip()
                evidence_cover_letter = evidence_draft.get("coverLetter", "").strip()
                evidence_pitch_words = len(evidence_pitch.split()) if evidence_pitch else 0
                evidence_cover_letter_words = len(evidence_cover_letter.split()) if evidence_cover_letter else 0
                
                if evidence_pitch_words < 45:
                    if job_title and company:
                        evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                    elif job_title:
                        evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                    else:
                        evidence_draft["pitch"] = evidence_pitch + " I am confident that my skills and experience make me a strong candidate for this role."
                
                if evidence_cover_letter_words < 150:
                    paragraphs = [p.strip() for p in evidence_cover_letter.split('\n\n') if p.strip()]
                    if len(paragraphs) < 3:
                        if job_title and company:
                            additional = f"\n\nI am particularly excited about the opportunity to contribute to {company}'s mission and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                        elif job_title:
                            additional = f"\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                        else:
                            additional = "\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for this role."
                        evidence_draft["coverLetter"] = evidence_cover_letter + additional
                    else:
                        if job_title and company:
                            evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                        elif job_title:
                            evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                        else:
                            evidence_draft["coverLetter"] = evidence_cover_letter + " I am confident that my skills and experience make me a strong candidate for this role."
                
                return evidence_draft
            except Exception as e:
                # Check if it's a model availability error and try fallback
                error_str = str(e).lower()
                if ("gpt-4o" in error_str or "model" in error_str or "not found" in error_str) and current_model == self.model:
                    # Try fallback model
                    current_model = self.fallback_model
                    if attempt < self.max_retries - 1:
                        continue
                # If all retries failed, return evidence-only draft
                print(f"[Tailor] Unexpected error after {self.max_retries} attempts: {e}. Returning evidence-only draft.")
                evidence_draft = self._create_evidence_only_draft(
                    resume,
                    jd,
                    job_title,
                    company,
                    resume_evidence,
                    must_haves
                )
                # Ensure minimum word counts (same logic as above)
                evidence_pitch = evidence_draft.get("pitch", "").strip()
                evidence_cover_letter = evidence_draft.get("coverLetter", "").strip()
                evidence_pitch_words = len(evidence_pitch.split()) if evidence_pitch else 0
                evidence_cover_letter_words = len(evidence_cover_letter.split()) if evidence_cover_letter else 0
                
                if evidence_pitch_words < 45:
                    if job_title and company:
                        evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                    elif job_title:
                        evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                    else:
                        evidence_draft["pitch"] = evidence_pitch + " I am confident that my skills and experience make me a strong candidate for this role."
                
                if evidence_cover_letter_words < 150:
                    paragraphs = [p.strip() for p in evidence_cover_letter.split('\n\n') if p.strip()]
                    if len(paragraphs) < 3:
                        if job_title and company:
                            additional = f"\n\nI am particularly excited about the opportunity to contribute to {company}'s mission and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                        elif job_title:
                            additional = f"\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                        else:
                            additional = "\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for this role."
                        evidence_draft["coverLetter"] = evidence_cover_letter + additional
                    else:
                        if job_title and company:
                            evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                        elif job_title:
                            evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                        else:
                            evidence_draft["coverLetter"] = evidence_cover_letter + " I am confident that my skills and experience make me a strong candidate for this role."
                
                return evidence_draft
        
        # If we get here, all retries failed - return evidence-only draft
        print(f"[Tailor] All retries failed. Returning evidence-only draft.")
        evidence_draft = self._create_evidence_only_draft(
            resume,
            jd,
            job_title,
            company,
            resume_evidence,
            must_haves
        )
        # Ensure minimum word counts (same logic as above)
        evidence_pitch = evidence_draft.get("pitch", "").strip()
        evidence_cover_letter = evidence_draft.get("coverLetter", "").strip()
        evidence_pitch_words = len(evidence_pitch.split()) if evidence_pitch else 0
        evidence_cover_letter_words = len(evidence_cover_letter.split()) if evidence_cover_letter else 0
        
        if evidence_pitch_words < 45:
            if job_title and company:
                evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
            elif job_title:
                evidence_draft["pitch"] = evidence_pitch + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
            else:
                evidence_draft["pitch"] = evidence_pitch + " I am confident that my skills and experience make me a strong candidate for this role."
        
        if evidence_cover_letter_words < 150:
            paragraphs = [p.strip() for p in evidence_cover_letter.split('\n\n') if p.strip()]
            if len(paragraphs) < 3:
                if job_title and company:
                    additional = f"\n\nI am particularly excited about the opportunity to contribute to {company}'s mission and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                elif job_title:
                    additional = f"\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                else:
                    additional = "\n\nI am particularly excited about this opportunity and would welcome the chance to discuss how my background can help achieve your goals. I am confident that my skills and experience make me a strong candidate for this role."
                evidence_draft["coverLetter"] = evidence_cover_letter + additional
            else:
                if job_title and company:
                    evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position at {company}."
                elif job_title:
                    evidence_draft["coverLetter"] = evidence_cover_letter + f" I am confident that my skills and experience make me a strong candidate for the {job_title} position."
                else:
                    evidence_draft["coverLetter"] = evidence_cover_letter + " I am confident that my skills and experience make me a strong candidate for this role."
        
        return evidence_draft


    def _get_analysis_schema_json(self) -> str:
        """Get the JSON schema for AnalyzeResponse as a minified string"""
        schema = {
            "type": "object",
            "properties": {
                "domains": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "score": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                        },
                        "required": ["name", "score"]
                    }
                },
                "skills": {
                    "type": "object",
                    "properties": {
                        "core": {"type": "array", "items": {"type": "string"}},
                        "adjacent": {"type": "array", "items": {"type": "string"}},
                        "advanced": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["core", "adjacent", "advanced"]
                },
                "strengths": {"type": "array", "items": {"type": "string"}},
                "areas_for_growth": {"type": "array", "items": {"type": "string"}},
                "recommended_roles": {"type": "array", "items": {"type": "string"}},
                "keywords_detected": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["domains", "skills", "strengths", "areas_for_growth", "recommended_roles", "keywords_detected"]
        }
        return json.dumps(schema, separators=(',', ':'))

    def _build_analysis_prompt(self, resume_text: str, target_role: Optional[str], is_retry: bool = False) -> str:
        """Build the prompt for GPT resume analysis"""
        schema_json = self._get_analysis_schema_json()
        
        base_prompt = f"""You are an expert resume analyzer for ANY profession (tech and non-tech). Your task is to analyze the resume text below and extract ONLY what is explicitly mentioned. Do NOT infer, assume, or add skills that are not present in the resume text.

CRITICAL RULES - READ CAREFULLY:
1. Read the ENTIRE resume text word-by-word, including all sections: Summary, Education, Skills, Experience, Projects, Certifications
2. Extract skills, technologies, tools, certifications, and experiences that are EXPLICITLY mentioned in the resume text
3. Do NOT add skills based on domain names, role titles, or assumptions - ONLY extract what is written
4. Do NOT use templates, boilerplate responses, or generic statements
5. If a skill is not mentioned anywhere in the resume, do NOT include it in strengths, skills, or keywords_detected
6. Base domains on actual evidence in the resume - look for explicit role titles, job descriptions, and skill mentions
7. For domains: Look for explicit role titles (e.g., "Data Analyst", "Medical Assistant", "Teacher") or strong keyword clusters that indicate a profession
8. For skills: Extract ONLY technologies, tools, software, languages, frameworks, certifications, or professional skills that are explicitly written
9. For strengths: Mention specific technologies, tools, certifications, or experiences that are actually in the resume
10. For areas_for_growth: Compare actual resume skills against target role requirements and identify ONLY missing skills - be specific and natural

Resume Text:
{resume_text}
"""
        
        if target_role:
            base_prompt += f"\nTARGET ROLE (USER SELECTED): {target_role}\n"
            base_prompt += f"\nIMPORTANT: The user has selected '{target_role}' as their target role. However, you MUST first analyze the resume content to determine if '{target_role}' actually matches the resume:\n"
            base_prompt += f"- If '{target_role}' matches the resume content (e.g., resume mentions AI/ML keywords and target_role is 'AI Engineer'), then '{target_role}' should be the PRIMARY domain\n"
            base_prompt += f"- If '{target_role}' does NOT match the resume content (e.g., resume is about Animation/Motion Graphics but target_role is 'AI Engineer'), then analyze based on the ACTUAL resume content and ignore the target_role\n"
            base_prompt += f"- Always prioritize accuracy: the PRIMARY domain should reflect what is actually in the resume, not what the user selected if it doesn't match\n"
            base_prompt += f"\nCRITICAL: Only use '{target_role}' as the PRIMARY domain if it matches the resume content. Otherwise, analyze based on what is actually in the resume:\n"
            base_prompt += f"- The top domain MUST be '{target_role}' or the closest matching domain from ANY profession:\n"
            base_prompt += f"  * Tech: 'AI Engineer' → 'ML/AI', 'Data Scientist' → 'ML/AI', 'Software Engineer' → 'Backend'/'Full-Stack'\n"
            base_prompt += f"  * Healthcare: 'Registered Nurse' → 'Registered Nurse', 'Medical Assistant' → 'Medical Assistant', 'Clinical Research Coordinator' → 'Clinical Research Coordinator'\n"
            base_prompt += f"  * Education: 'Teacher' → 'Teacher', 'Education Coordinator' → 'Education Coordinator'\n"
            base_prompt += f"  * Finance: 'Accountant' → 'Accountant', 'Financial Analyst' → 'Financial Analyst'\n"
            base_prompt += f"  * Business: 'Operations Manager' → 'Operations Coordinator', 'Marketing Specialist' → 'Marketing Specialist', 'Sales Representative' → 'Sales Representative'\n"
            base_prompt += f"  * If '{target_role}' doesn't match a known domain, use '{target_role}' as the domain name itself (open-world classification)\n"
            base_prompt += f"- The top domain score MUST be 0.8-1.0 (highest score)\n"
            base_prompt += f"- Recommended roles MUST align with '{target_role}' and be from the same profession family\n"
            base_prompt += f"- Strengths MUST be specific to '{target_role}' profession and evidenced in the resume\n"
            base_prompt += f"- Areas for growth MUST be based on '{target_role}' competencies and industry standards\n"
            base_prompt += f"- Even if the resume has strong keywords for other domains, prioritize '{target_role}' as the PRIMARY domain\n"
            base_prompt += f"- Extract skills, strengths, and gaps that are SPECIFIC to '{target_role}' profession, not generic\n"
        
        if is_retry:
            base_prompt += "\nIMPORTANT: Your previous response did not match the required schema. Please correct it to match exactly.\n"
        
        base_prompt += f"""
Return STRICT minified JSON exactly matching this schema: {schema_json}

CRITICAL REQUIREMENTS:

1. domains: Return MULTIPLE domains (up to 5) with scores 0.0-1.0 based on evidence strength. Use open-world role names (e.g., "Clinical Research Coordinator", "Public Health Analyst", "Registered Nurse", "Teacher", "Accountant", "Financial Analyst", "Operations Coordinator", "Marketing Specialist", "Data Analyst", "Frontend Engineer", "Animation/Motion Graphics", "Graphic Designer", "UI/UX Designer", etc.). Each domain must have clear evidence in the resume text. 

CRITICAL DOMAIN ORDERING RULES - BE PRECISE:
- STEP 1: Check for explicit role titles in the resume (e.g., "Data Analyst", "Medical Assistant", "Teacher", "Animation Student", "Motion Graphics Designer")
  * If found, that domain MUST be the top domain with the highest score (0.85-1.0)
  * Look in: Summary, Experience section job titles, Education degree programs, Skills section headers
  
- STEP 2: If no explicit role title, check for strong domain-specific keyword clusters:
  * Data Analyst: SQL, Excel, Power BI, Tableau, pandas, numpy, statistics, regression, ETL
  * Medical Assistant: patient care, vitals, phlebotomy, EHR, Epic, CPT, ICD-10, scheduling, appointments
  * Teacher: lesson planning, IEP, classroom management, curriculum, assessment, teaching, education
  * Animation/Motion Graphics: animation, motion graphics, After Effects, Maya, Blender, character design, storyboarding, 3D animation, motion capture
  * Frontend: React, JavaScript, CSS, Tailwind, UI/UX, frontend development, web development
  * Backend: Python, Java, Node.js, Django, Flask, Spring, API development, backend development
  * ML/AI: machine learning, ML, AI, PyTorch, TensorFlow, sklearn, neural network, deep learning, LLM, transformer
  
- STEP 3: Score domains based on evidence strength:
  * Explicit role title + strong keywords: 0.9-1.0 (highest confidence)
  * Explicit role title only: 0.85-0.95
  * Strong keyword cluster (5+ keywords): 0.75-0.9
  * Moderate keyword cluster (3-4 keywords): 0.6-0.75
  * Weak keyword cluster (1-2 keywords): 0.4-0.6
  
- STEP 4: Order domains by PRIMARY role/experience, not by number of keywords:
  * A Data Analyst resume with some React experience should have "Data Analyst" as top domain (0.9), not "Frontend" (0.5)
  * An Animation student resume with some Python experience should have "Animation/Motion Graphics" as top domain (0.9), not "Backend" (0.4)
  * A Medical Assistant resume with some Excel experience should have "Medical Assistant" as top domain (0.9), not "Data Analyst" (0.3)
  
- STEP 5: Limit to top 5 domains, ordered by score descending, with the PRIMARY role always first.

2. skills: Organize into core (strongly evidenced), adjacent (mentioned but not deeply), advanced (next-level). Only include skills explicitly present in resume text. Skills can be technical (SQL, Python, React) or professional (patient care, lesson planning, GAAP, etc.).

CRITICAL SKILL EXTRACTION RULES:
- Extract skills from ALL sections: Summary, Skills, Experience, Projects, Certifications, Education
- Core skills: Technologies/tools mentioned multiple times or in primary responsibilities (e.g., "React" mentioned in 3+ bullet points)
- Adjacent skills: Technologies/tools mentioned once or in secondary contexts (e.g., "Python" mentioned in one project)
- Advanced skills: Next-level technologies/tools that are mentioned but not deeply (e.g., "Docker" mentioned but not explained)
- Be precise: "React" is different from "React Native" - only include what's explicitly mentioned
- For healthcare: Include systems (Epic, EHR), certifications (CPR, BLS, ACLS), procedures (phlebotomy, vitals)
- For education: Include teaching methods, curriculum tools, assessment platforms, IEP management
- For finance: Include software (QuickBooks), standards (GAAP), processes (reconciliation, audits)
- For animation: Include software (After Effects, Maya, Blender), techniques (rigging, compositing, motion capture)
- Do NOT infer skills from domain names - only extract what is explicitly written

3. strengths: Extract 3-5 SPECIFIC strengths ONLY if evidenced in resume_text. Mention actual technologies, tools, certifications, or experiences. NO defaults/templates. 

CRITICAL STRENGTH EXTRACTION RULES:
- Read the resume carefully and identify what the candidate actually does well based on their experience
- For healthcare: Mention specific systems (Epic, EHR), certifications (CPR, BLS, ACLS), procedures (phlebotomy, vitals, medication administration), patient care experience
- For education: Mention teaching methods, curriculum design, assessment tools, IEP management, classroom management strategies, student engagement techniques
- For finance: Mention software (QuickBooks, Excel), standards (GAAP), processes (reconciliation, audits, financial reporting), analytical skills
- For animation: Mention software proficiency (After Effects, Maya, Blender), techniques (character design, storyboarding, 3D animation, motion capture), creative skills
- For tech: Mention technologies, frameworks, tools, programming languages, system design, problem-solving
- Be specific: Instead of "Strong technical skills", say "Proficient in React and JavaScript for frontend development" (if React and JavaScript are mentioned)
- Reference actual experiences: Instead of "Experience with data analysis", say "Experience with SQL and Excel for data analysis" (if SQL and Excel are mentioned)
- Make strengths sound natural and specific to the resume, not generic templates

4. areas_for_growth: CRITICAL - This MUST be dynamic, natural, and resume-specific. Follow these steps EXACTLY:
   a) First, extract ALL skills from the resume (from the skills section you identified above: core, adjacent, advanced, and keywords_detected)
      - Create a comprehensive list of ALL skills mentioned in the resume
      - Include technologies, tools, software, languages, frameworks, certifications, and professional skills
      - Be thorough - check all sections: Summary, Skills, Experience, Projects, Certifications
   
   b) Then, identify the required competencies for target_role based on industry standards:
      - If target_role is "AI Engineer": Required skills include PyTorch/TensorFlow, LLMs/transformers, MLOps, vector databases, Python ML, cloud ML platforms (SageMaker, Vertex AI)
      - If target_role is "Data Analyst": Required skills include SQL (joins, window functions, CTEs), Excel (pivot tables, VLOOKUP), BI tools (Power BI/Tableau), statistics, Python (pandas/numpy), data modeling/ETL
      - If target_role is "Medical Assistant": Required skills include patient care, vitals, phlebotomy, EHR/Epic, medical coding (CPT/ICD-10), scheduling, HIPAA compliance
      - If target_role is "Clinical Research Coordinator": Required skills include IRB protocols, GCP, REDCap, informed consent, clinical trial management, regulatory compliance
      - If target_role is "Public Health Analyst": Required skills include epidemiology, SPSS/Stata/R, survey design, policy analysis, surveillance, program evaluation
      - If target_role is "Teacher": Required skills include lesson planning, IEP management, classroom management, assessment design, curriculum development, differentiated instruction
      - If target_role is "Accountant": Required skills include GAAP, QuickBooks, reconciliation, financial reporting, audit procedures, tax preparation
      - If target_role is "Animation/Motion Graphics": Required skills include After Effects, Maya, Blender, character design, storyboarding, 3D animation, motion capture, compositing
      - If target_role is "Graphic Designer": Required skills include Photoshop, Illustrator, InDesign, branding, visual design, layout design, typography
      - For ANY other role: Research industry-standard required skills for that specific role
   
   c) Compare the resume skills (from step a) against the required competencies (from step b):
      - For each required skill, check if it appears in the resume skills list
      - Use fuzzy matching: "Python" matches "python", "Python programming", "Python scripting"
      - Be careful: "React" does NOT match "React Native" unless both are mentioned
      - Check for related skills: If resume has "pandas" but not "numpy", consider if "Python data libraries" is a gap
   
   d) ONLY include gaps that are ACTUALLY MISSING from the resume:
      - Do NOT include skills that are already present (even if mentioned once)
      - Do NOT include skills that are closely related to existing skills (e.g., if resume has "pandas", don't list "Python" as a gap)
      - Be specific: Instead of "Deep learning frameworks", say "PyTorch or TensorFlow" if neither is in the resume
      - Be natural: Write gaps as if you're giving personalized advice, not using a template
   
   e) Prioritize gaps by importance:
      - Core/essential skills for the role should be listed first
      - Advanced/next-level skills should be listed after core skills
      - Limit to 3-5 most important gaps
   
   f) Write gaps naturally and specifically:
      - Instead of: "Deep learning frameworks"
      - Write: "PyTorch or TensorFlow for deep learning model development" (if neither is in resume)
      - Instead of: "SQL"
      - Write: "Advanced SQL (window functions, CTEs) for complex data queries" (if SQL basics are present but advanced features are not)
      - Instead of: "Patient care"
      - Write: "Phlebotomy and specimen collection procedures" (if patient care is mentioned but phlebotomy is not)
      - Make each gap sound like personalized advice, not a template
   
   g) NEVER use templates or generic statements:
      - Each gap must be specific to what's missing in THIS resume
      - Reference the actual resume content when writing gaps
      - If the resume has strong skills in one area, focus gaps on complementary areas
   
   h) Identify 3-5 specific gaps that are actually missing:
      - Always include at least 2 gaps
      - If the resume has most required skills, identify advanced/next-level skills that are missing
      - If the resume has few required skills, identify core/essential skills that are missing
      - Make sure gaps are relevant to the target_role and the resume's current skill level

5. recommended_roles: List 2-4 roles aligned to the TOP DOMAIN (primary role) and evidence. Use role names from the same profession family.
- If top domain is "Data Analyst": ["Data Analyst", "Business Analyst", "BI Analyst", "Analytics Engineer"]
- If top domain is "Frontend": ["Frontend Engineer", "UI Developer", "React Developer"]
- If top domain is "Backend": ["Backend Engineer", "Software Engineer", "API Developer"]
- If top domain is "ML/AI": ["ML Engineer", "Data Scientist", "AI Engineer"]
- If top domain is "DevOps": ["DevOps Engineer", "Site Reliability Engineer (SRE)", "Cloud Engineer", "Infrastructure Engineer"]
- If top domain is "Cloud/SA": ["Cloud Architect", "Solutions Architect", "Cloud Engineer", "AWS/Azure/GCP Specialist"]
- If top domain is "Data Engineer": ["Data Engineer", "ETL Engineer", "Data Pipeline Engineer", "Big Data Engineer"]
- For Clinical Research Coordinator: ["Clinical Research Coordinator", "Research Assistant", "Clinical Trial Manager"]
- For Public Health Analyst: ["Public Health Analyst", "Epidemiologist", "Health Policy Analyst"]
- For Teacher: ["Teacher", "Education Coordinator", "Curriculum Specialist"]
Base on actual evidence in resume and the PRIMARY domain, not secondary skills.

6. keywords_detected: List of key technologies, tools, certifications, or skills detected in the resume (extract from actual text).

CRITICAL ANALYSIS RULES:
1. Extract skills ONLY from what is explicitly written in the resume text
2. Do NOT infer skills from domain names (e.g., don't add TypeScript just because it's a Frontend role)
3. Do NOT use templates or generic responses
4. Forbid canned lines like "Strong experience with React and TypeScript" unless BOTH "React" AND "TypeScript" explicitly appear in resume_text
5. NEVER add TypeScript unless "typescript", "ts ", "TypeScript", or ".ts" explicitly appears in the resume
6. NEVER add skills that are not mentioned in the resume text
7. Multi-domain classification: A resume can match multiple domains ONLY if there is clear evidence for each (e.g., Data Analyst + ML/AI if both are evidenced)
8. Skills must be extracted from actual resume content, not inferred from domain names or role titles
9. If a skill is not mentioned, do NOT include it in strengths, skills, or keywords_detected
10. Strengths must be specific and evidenced (e.g., "Python programming" only if Python is mentioned)
11. Areas for growth must be based on actual gaps when comparing resume skills to role requirements
12. Recommended roles must be based on actual evidence in the resume, not assumptions

EXAMPLE:
- If resume mentions "React" but NOT "TypeScript", do NOT add TypeScript to skills or strengths
- If resume mentions "Python" and "SQL", add both to skills
- If resume mentions "Data Analyst" role but no specific tools, extract only what is mentioned
- If resume mentions "AWS Certified Solutions Architect", add "AWS" and "Solutions Architecture" to skills

Return ONLY valid JSON, no markdown, no code blocks, no explanations."""

        return base_prompt

    def analyze_resume(self, text: str, target_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze resume text using GPT and return AnalyzeResponse as dict.
        
        Args:
            text: Resume text to analyze
            target_role: Optional target role for analysis
            
        Returns:
            Dict matching AnalyzeResponse schema
            
        Raises:
            Exception: If analysis fails after max retries
        """
        if not self.client:
            raise ValueError("OPENAI_API_KEY is not set")
        
        # Redact PII before sending to LLM
        redacted_text = redact_pii(text)
        
        last_error = None
        current_model = self.model
        
        for attempt in range(self.max_retries):
            try:
                is_retry = attempt > 0
                # Use redacted text for prompt
                prompt = self._build_analysis_prompt(redacted_text, target_role, is_retry)
                
                try:
                    response = self.client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert resume analyzer. Return only valid JSON matching the specified schema. Extract ONLY what is explicitly mentioned in the resume text."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.1,  # Low temperature for deterministic analysis
                        max_tokens=3000,
                        response_format={"type": "json_object"}
                    )
                except Exception as model_error:
                    # Check if it's a model availability error and try fallback
                    error_str = str(model_error).lower()
                    if ("gpt-4o" in error_str or "model" in error_str or "not found" in error_str) and current_model == self.model:
                        # Try fallback model
                        current_model = self.fallback_model
                        if attempt < self.max_retries - 1:
                            continue
                    raise
                
                # Extract text from response
                response_text = response.choices[0].message.content.strip()
                
                # Remove markdown code blocks if present (shouldn't happen with json_object format, but just in case)
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                # Parse JSON
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    last_error = ValueError(f"Failed to parse JSON: {e}")
                    if attempt < self.max_retries - 1:
                        continue  # Retry
                    raise last_error
                
                # Return data directly (validation happens at route level)
                return data
                
            except ValueError as e:
                # Retryable validation/parsing errors
                last_error = e
                if attempt < self.max_retries - 1:
                    continue
                raise
            except Exception as e:
                # Check if it's a model availability error and try fallback
                error_str = str(e).lower()
                if ("gpt-4o" in error_str or "model" in error_str or "not found" in error_str) and current_model == self.model:
                    # Try fallback model
                    current_model = self.fallback_model
                    if attempt < self.max_retries - 1:
                        continue
                # Non-retryable errors
                raise Exception(f"Unexpected error during analysis: {e}")
        
        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise Exception(f"Failed to analyze resume after {self.max_retries} attempts")


# Global instance
openai_service = OpenAIService()

