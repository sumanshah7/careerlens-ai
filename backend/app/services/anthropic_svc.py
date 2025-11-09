"""
Anthropic service for resume analysis using Claude
"""
import json
import os
from typing import Optional, Dict, Any
from anthropic import Anthropic
from pydantic import ValidationError
from app.models.schemas import AnalyzeResponse, Skill
from app.config import settings
from app.services.pii_redaction import redact_pii


class AnthropicService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-haiku-20240307"
        self.max_retries = 3

    def _get_schema_json(self) -> str:
        """Get the JSON schema for AnalyzeResponse as a minified string"""
        schema = {
            "type": "object",
            "properties": {
                "domains": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},  # Open-world: any role name
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

    def _build_prompt(self, resume_text: str, target_role: Optional[str], is_retry: bool = False) -> str:
        """Build the prompt for Claude"""
        schema_json = self._get_schema_json()
        
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
            base_prompt += f"- Recommended roles MUST align with '{target_role}' and be from the same profession family:\n"
            base_prompt += f"  * Healthcare: ['Registered Nurse', 'Staff Nurse', 'Charge Nurse']\n"
            base_prompt += f"  * Education: ['Teacher', 'Education Coordinator', 'Curriculum Specialist']\n"
            base_prompt += f"  * Finance: ['Accountant', 'Staff Accountant', 'Financial Analyst']\n"
            base_prompt += f"  * Business: ['Operations Manager', 'Operations Coordinator', 'Logistics Coordinator']\n"
            base_prompt += f"  * Tech: ['AI Engineer', 'ML Engineer', 'Data Scientist']\n"
            base_prompt += f"- Strengths MUST be specific to '{target_role}' profession and evidenced in the resume:\n"
            base_prompt += f"  * Healthcare: mention specific systems (Epic, EHR), certifications (CPR, BLS), procedures (phlebotomy, vitals)\n"
            base_prompt += f"  * Education: mention teaching methods, curriculum design, assessment tools, IEP management\n"
            base_prompt += f"  * Finance: mention software (QuickBooks), standards (GAAP), processes (reconciliation, audits)\n"
            base_prompt += f"  * Business: mention tools (CRM), processes (SOPs, inventory), skills (scheduling, procurement)\n"
            base_prompt += f"  * Tech: mention technologies, frameworks, tools explicitly in resume\n"
            base_prompt += f"- Areas for growth MUST be based on '{target_role}' competencies and industry standards:\n"
            base_prompt += f"  * Healthcare: IRB protocols, GCP, REDCap, informed consent, medical coding (CPT/ICD-10)\n"
            base_prompt += f"  * Education: lesson planning, IEP management, classroom strategies, assessment design\n"
            base_prompt += f"  * Finance: GAAP, QuickBooks, reconciliation, financial reporting, audit procedures\n"
            base_prompt += f"  * Business: CRM systems, inventory management, procurement, logistics, operations optimization\n"
            base_prompt += f"  * Tech: domain-specific gaps (e.g., AI Engineer → MLOps, LLMs, deep learning frameworks)\n"
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
        Analyze resume text using Claude and return AnalyzeResponse as dict.
        
        Args:
            text: Resume text to analyze
            target_role: Optional target role for analysis
            
        Returns:
            Dict matching AnalyzeResponse schema
            
        Raises:
            Exception: If analysis fails after max retries
        """
        if not self.client.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        
        # Redact PII before sending to LLM
        redacted_text = redact_pii(text)
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                is_retry = attempt > 0
                # Use redacted text for prompt
                prompt = self._build_prompt(redacted_text, target_role, is_retry)
                
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,  # Increased for coaching plan
                    temperature=0.1,  # Low temperature for deterministic but allow some creativity
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                # Extract text from response
                response_text = message.content[0].text.strip()
                
                # Remove markdown code blocks if present
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
                # Non-retryable errors (API errors, etc.)
                raise Exception(f"Unexpected error during analysis: {e}")
        
        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise Exception(f"Failed to analyze resume after {self.max_retries} attempts")


# Global instance
anthropic_service = AnthropicService()

