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


class OpenAIService:
    def __init__(self):
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
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
                    "minItems": 2,
                    "maxItems": 4
                },
                "pitch": {"type": "string"},
                "coverLetter": {"type": "string"}
            },
            "required": ["bullets", "pitch", "coverLetter"]
        }
        return json.dumps(schema, separators=(',', ':'))

    def _build_prompt(self, resume: str, jd: str, style: str = "STAR", is_retry: bool = False) -> str:
        """Build the prompt for GPT"""
        schema_json = self._get_schema_json()
        
        base_prompt = f"""Create tailored resume content for the following job description.

Resume:
{resume}

Job Description:
{jd}
"""
        
        if is_retry:
            base_prompt += "\nIMPORTANT: Your previous response did not match the required schema. Please correct it to match exactly.\n"
        
        base_prompt += f"""
Create 2-4 STAR-format bullets, a 50-word elevator pitch, and a 120-180 word cover letter. Return JSON matching TailorRes.

Requirements:
- bullets: array of 2-4 resume bullets in STAR format (Situation, Task, Action, Result)
- pitch: exactly 50 words elevator pitch
- coverLetter: 120-180 word cover letter tailored to the job description

STAR Format Example:
"Led (Situation) a team of 5 engineers (Task) to refactor legacy codebase (Action), resulting in 40% performance improvement and 50% reduction in bug reports (Result)"

Return STRICT minified JSON exactly matching this schema: {schema_json}

Return ONLY valid JSON, no markdown, no code blocks, no explanations."""

        return base_prompt

    def tailor_for_job(self, resume: str, jd: str, style: str = "STAR") -> Dict[str, Any]:
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
        
        last_error = None
        current_model = self.model
        
        for attempt in range(self.max_retries):
            try:
                is_retry = attempt > 0
                prompt = self._build_prompt(resume, jd, style, is_retry)
                
                try:
                    response = self.client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a professional resume writer. Return only valid JSON matching the specified schema."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.7,
                        max_tokens=1000,
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
                
                # Validate against Pydantic schema
                try:
                    tailor_response = TailorResponse(**data)
                    return tailor_response.model_dump()
                except ValidationError as e:
                    last_error = ValueError(f"Response does not match schema: {e}")
                    if attempt < self.max_retries - 1:
                        continue  # Retry
                    raise last_error
                
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
                raise Exception(f"Unexpected error during tailoring: {e}")
        
        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise Exception(f"Failed to tailor resume after {self.max_retries} attempts")


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

CRITICAL RULES:
1. Read the ENTIRE resume text carefully
2. Extract skills, technologies, tools, and experiences that are EXPLICITLY mentioned
3. Do NOT add skills based on domain names or assumptions
4. Do NOT use templates or boilerplate responses
5. If a skill is not mentioned, do NOT include it in strengths, skills, or keywords_detected
6. Base domains on actual evidence in the resume, not assumptions

Resume Text:
{resume_text}
"""
        
        if target_role:
            base_prompt += f"\nTARGET ROLE (USER SELECTED): {target_role}\n"
            base_prompt += f"\nCRITICAL: The user has selected '{target_role}' as their target role. This MUST be the PRIMARY domain in your analysis, regardless of profession (tech, healthcare, education, finance, business, etc.):\n"
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

1. domains: Return MULTIPLE domains (up to 5) with scores 0.0-1.0 based on evidence strength. Use open-world role names (e.g., "Clinical Research Coordinator", "Public Health Analyst", "Registered Nurse", "Teacher", "Accountant", "Financial Analyst", "Operations Coordinator", "Marketing Specialist", "Data Analyst", "Frontend Engineer", etc.). Each domain must have clear evidence in the resume text.

CRITICAL DOMAIN ORDERING RULES:
- If the resume explicitly mentions a role title (e.g., "Data Analyst", "Data Analyst Intern", "Business Analyst"), that domain MUST be the top domain with the highest score (0.8-1.0)
- If the resume has strong domain-specific keywords (e.g., SQL, Excel, Power BI, Tableau for Data Analyst), prioritize that domain as the top domain
- Only include Frontend/Full-Stack as top domain if the resume explicitly mentions frontend work, React development, or UI/UX work as primary responsibilities
- Order domains by PRIMARY role/experience, not by number of keywords. A Data Analyst resume with some React experience should have "Data Analyst" as top domain, not "Frontend"
- Scores should reflect PRIMARY role (0.8-1.0) vs secondary skills (0.4-0.7)

Order by score descending, with the PRIMARY role always first.

2. skills: Organize into core (strongly evidenced), adjacent (mentioned but not deeply), advanced (next-level). Only include skills explicitly present in resume text. Skills can be technical (SQL, Python, React) or professional (patient care, lesson planning, GAAP, etc.).

3. strengths: Extract 3-5 SPECIFIC strengths ONLY if evidenced in resume_text. Mention actual technologies, tools, certifications, or experiences. NO defaults/templates. For healthcare: mention specific systems (Epic, EHR), certifications (CPR, BLS), procedures. For education: mention teaching methods, curriculum design, assessment tools. For finance: mention software (QuickBooks), standards (GAAP), processes.

4. areas_for_growth: Build by comparing resume skills against role-specific competencies for target_role. Infer competencies from the role name and industry standards. For Clinical Research Coordinator: IRB protocols, GCP, REDCap, informed consent. For Public Health Analyst: epidemiology, SPSS/Stata/R, survey design, policy analysis. For Teacher: lesson planning, IEP management, classroom strategies. For Accountant: GAAP, QuickBooks, reconciliation, audits. Identify 3-5 specific gaps that are actually missing. NEVER leave this empty - always include at least 2 gaps.

5. recommended_roles: List 2-4 roles aligned to the TOP DOMAIN (primary role) and evidence. Use role names from the same profession family.
- If top domain is "Data Analyst": ["Data Analyst", "Business Analyst", "BI Analyst", "Analytics Engineer"]
- If top domain is "Frontend": ["Frontend Engineer", "UI Developer", "React Developer"]
- If top domain is "Backend": ["Backend Engineer", "Software Engineer", "API Developer"]
- If top domain is "ML/AI": ["ML Engineer", "Data Scientist", "AI Engineer"]
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
        
        last_error = None
        current_model = self.model
        
        for attempt in range(self.max_retries):
            try:
                is_retry = attempt > 0
                prompt = self._build_analysis_prompt(text, target_role, is_retry)
                
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

