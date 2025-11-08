"""
Coach service for generating personalized coaching plans using AI
"""
import json
import os
import re
from typing import List, Optional, Dict, Any
from anthropic import Anthropic
from openai import OpenAI
from pydantic import ValidationError
from app.models.schemas import CoachPlan, PlanDay
from app.config import settings


class CoachService:
    def __init__(self):
        # Try Anthropic first, fallback to OpenAI
        anthropic_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        
        self.anthropic_client = Anthropic(api_key=anthropic_key) if anthropic_key else None
        self.openai_client = OpenAI(api_key=openai_key) if openai_key else None
        self.anthropic_model = "claude-3-haiku-20240307"
        self.openai_model = "gpt-4o-mini"
        self.max_retries = 3

    def _get_schema_json(self) -> str:
        """Get the JSON schema for CoachPlan as a minified string"""
        schema = {
            "type": "object",
            "properties": {
                "plan": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day": {"type": "integer", "minimum": 1, "maximum": 7},
                            "title": {"type": "string"},
                            "actions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 2,
                                "maxItems": 3
                            }
                        },
                        "required": ["day", "title", "actions"]
                    },
                    "minItems": 7,
                    "maxItems": 7
                }
            },
            "required": ["plan"]
        }
        return json.dumps(schema, separators=(',', ':'))

    def _build_prompt(self, gaps: List[str], target_role: Optional[str], domain: Optional[str] = None, is_retry: bool = False) -> str:
        """Build the prompt for AI"""
        schema_json = self._get_schema_json()
        
        gaps_text = "\n".join(f"- {gap}" for gap in gaps)
        
        base_prompt = f"""Create a 7-day personalized coaching plan to address the following skill gaps:

Skill Gaps:
{gaps_text}
"""
        
        if domain:
            base_prompt += f"\nDomain/Field: {domain}\n"
            # Add domain-specific guidance
            if domain == "ML/AI":
                base_prompt += "\nFocus on: Machine Learning, Deep Learning, LLMs, MLOps, AI frameworks (PyTorch, TensorFlow), vector databases, and AI/ML cloud platforms.\n"
            elif domain == "Data Analyst":
                base_prompt += "\nFocus on: Data analysis, SQL, visualization tools (Tableau, Power BI), Python/R, statistics, and data storytelling.\n"
            elif domain == "Frontend":
                base_prompt += "\nFocus on: React, TypeScript, modern JavaScript, CSS frameworks, testing, and web accessibility.\n"
            elif domain == "Backend":
                base_prompt += "\nFocus on: Server-side development, APIs, databases, cloud services, and system design.\n"
            elif domain == "Full-Stack":
                base_prompt += "\nFocus on: Both frontend and backend technologies, full-stack frameworks, and end-to-end development.\n"
            elif domain == "Data Engineer":
                base_prompt += "\nFocus on: ETL pipelines, data warehousing, big data tools (Spark, Kafka), and data infrastructure.\n"
            elif domain == "Cloud/SA":
                base_prompt += "\nFocus on: Cloud architecture, AWS/Azure/GCP, infrastructure as code, and system design.\n"
            elif domain == "DevOps":
                base_prompt += "\nFocus on: CI/CD, containerization (Docker, Kubernetes), infrastructure automation, and monitoring.\n"
        
        if target_role:
            base_prompt += f"\nTarget Role: {target_role}\n"
        
        if is_retry:
            base_prompt += "\nIMPORTANT: Your previous response did not match the required schema. Please correct it to match exactly.\n"
        
        base_prompt += f"""
Requirements:
- Generate exactly 7 days of coaching activities
- Each day must have a title and 2-3 actions
- Actions MUST include real course links from these platforms:
  * DataCamp: https://www.datacamp.com/courses (search for relevant courses)
  * Udemy: https://www.udemy.com/courses (search for relevant courses)
  * Coursera: https://www.coursera.org/courses (search for relevant courses)
  * edX: https://www.edx.org/course (search for relevant courses)
  * freeCodeCamp: https://www.freecodecamp.org/learn (free courses)
  * AWS Skill Builder: https://explore.skillbuilder.aws/learn (AWS courses)
  * YouTube: https://www.youtube.com (educational playlists)
  * Hugging Face: https://huggingface.co/learn (for ML/AI domain)
  * Fast.ai: https://www.fast.ai/ (for ML/AI domain)
- Actions should be specific and actionable with actual course URLs
- Progress from foundational to advanced topics
- Include a mix of theory and hands-on practice
- Prefer free resources when possible (freeCodeCamp, YouTube, AWS Skill Builder, Hugging Face, Fast.ai)
- Make the plan relevant to the domain/field specified above

Example action format:
"Complete 'Introduction to Python' on DataCamp (https://www.datacamp.com/courses/intro-to-python-for-data-science)"
"Take 'AWS Cloud Practitioner Essentials' on AWS Skill Builder (https://explore.skillbuilder.aws/learn/course/134/aws-cloud-practitioner-essentials)"
"Watch 'System Design Interview' playlist on YouTube (https://www.youtube.com/playlist?list=PLMCXHnjxnTnvo6alSjVkgxV-VH6EPyvoX)"
"Enroll in 'Machine Learning' course on Coursera (https://www.coursera.org/learn/machine-learning)"
"For ML/AI domain: 'Complete Deep Learning course on Fast.ai (https://www.fast.ai/)'"
"For ML/AI domain: 'Learn Transformers on Hugging Face (https://huggingface.co/learn/nlp-course)'"

IMPORTANT: Each action MUST include a real URL to an actual course or resource. Do not use placeholder URLs.

Return STRICT minified JSON exactly matching this schema: {schema_json}

Return ONLY valid JSON, no markdown, no code blocks, no explanations."""

        return base_prompt

    def _post_process_plan(self, plan: List[Dict[str, Any]]) -> List[PlanDay]:
        """Post-process plan to ensure exactly 7 days and 2-3 actions per day"""
        processed_plan = []
        
        # Ensure exactly 7 days
        if len(plan) < 7:
            # Pad with generic days
            for i in range(len(plan), 7):
                plan.append({
                    "day": i + 1,
                    "title": f"Day {i + 1}: Continue Learning",
                    "actions": [
                        "Review previous day's concepts",
                        "Practice with hands-on exercises"
                    ]
                })
        elif len(plan) > 7:
            # Trim to 7 days
            plan = plan[:7]
        
        # Process each day
        for i, day_data in enumerate(plan[:7]):
            day_num = i + 1
            title = day_data.get("title", f"Day {day_num}: Learning")
            
            # Ensure title is not too long
            if len(title) > 100:
                title = title[:97] + "..."
            
            actions = day_data.get("actions", [])
            
            # Ensure 2-3 actions
            if len(actions) < 2:
                # Add generic actions if needed
                actions.extend([
                    "Review key concepts from today's learning",
                    "Practice with hands-on exercises"
                ])
            elif len(actions) > 3:
                # Trim to 3 actions
                actions = actions[:3]
            
            # Ensure actions are not too long and contain resource links
            processed_actions = []
            for action in actions:
                # Ensure action is not too long
                if len(action) > 200:
                    action = action[:197] + "..."
                
                # Check if action contains a URL or resource reference
                # If not, try to add a generic resource link
                if not re.search(r'https?://', action, re.IGNORECASE):
                    # Try to infer resource based on action content and add real course links
                    action_lower = action.lower()
                    if 'aws' in action_lower or 'cloud' in action_lower:
                        action = f"{action} (https://explore.skillbuilder.aws/learn/course/134/aws-cloud-practitioner-essentials)"
                    elif 'python' in action_lower or 'data science' in action_lower or 'data' in action_lower:
                        action = f"{action} (https://www.datacamp.com/courses/intro-to-python-for-data-science)"
                    elif 'machine learning' in action_lower or 'ml' in action_lower:
                        action = f"{action} (https://www.coursera.org/learn/machine-learning)"
                    elif 'web development' in action_lower or 'react' in action_lower or 'javascript' in action_lower:
                        action = f"{action} (https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/)"
                    elif 'system design' in action_lower or 'architecture' in action_lower:
                        action = f"{action} (https://www.youtube.com/playlist?list=PLMCXHnjxnTnvo6alSjVkgxV-VH6EPyvoX)"
                    elif 'course' in action_lower or 'learn' in action_lower or 'tutorial' in action_lower:
                        action = f"{action} (https://www.udemy.com/courses/search/?q={action.split()[0] if action.split() else 'programming'})"
                    else:
                        action = f"{action} (https://www.freecodecamp.org/learn/)"
                
                processed_actions.append(action)
            
            processed_plan.append(PlanDay(
                day=day_num,
                title=title,
                actions=processed_actions
            ))
        
        return processed_plan

    def _generate_with_anthropic(self, gaps: List[str], target_role: Optional[str], domain: Optional[str] = None) -> Dict[str, Any]:
        """Generate plan using Anthropic Claude"""
        if not self.anthropic_client:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                is_retry = attempt > 0
                prompt = self._build_prompt(gaps, target_role, domain, is_retry)
                
                message = self.anthropic_client.messages.create(
                    model=self.anthropic_model,
                    max_tokens=2000,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
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
                        continue
                    raise last_error
                
                return data
                
            except ValueError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue
                raise
            except Exception as e:
                raise Exception(f"Unexpected error during plan generation: {e}")
        
        if last_error:
            raise last_error
        raise Exception(f"Failed to generate plan after {self.max_retries} attempts")

    def _generate_with_openai(self, gaps: List[str], target_role: Optional[str], domain: Optional[str] = None) -> Dict[str, Any]:
        """Generate plan using OpenAI GPT"""
        if not self.openai_client:
            raise ValueError("OPENAI_API_KEY is not set")
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                is_retry = attempt > 0
                prompt = self._build_prompt(gaps, target_role, domain, is_retry)
                
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
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
                    temperature=0.7,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
                
                response_text = response.choices[0].message.content.strip()
                
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
                        continue
                    raise last_error
                
                return data
                
            except ValueError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue
                raise
            except Exception as e:
                raise Exception(f"Unexpected error during plan generation: {e}")
        
        if last_error:
            raise last_error
        raise Exception(f"Failed to generate plan after {self.max_retries} attempts")

    def generate_coach_plan(
        self,
        gaps: List[str],
        target_role: Optional[str] = None,
        domain: Optional[str] = None,
        reminders: bool = False
    ) -> CoachPlan:
        """
        Generate a 7-day coaching plan using Claude or OpenAI.
        
        Args:
            gaps: List of skill gaps to address
            target_role: Optional target role for context
            domain: Optional domain/field (ML/AI, Frontend, Backend, etc.)
            reminders: Whether to enable reminders
            
        Returns:
            CoachPlan with exactly 7 days and 2-3 actions per day
        """
        # Try Anthropic first, fallback to OpenAI
        try:
            if self.anthropic_client:
                data = self._generate_with_anthropic(gaps, target_role, domain)
            elif self.openai_client:
                data = self._generate_with_openai(gaps, target_role, domain)
            else:
                raise ValueError("Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY is set")
        except Exception as e:
            # If both fail, raise
            raise Exception(f"Failed to generate plan: {e}")
        
        # Extract plan from response
        plan_data = data.get("plan", [])
        
        # Post-process to ensure exactly 7 days and 2-3 actions per day
        processed_plan = self._post_process_plan(plan_data)
        
        # Create CoachPlan
        return CoachPlan(
            plan=processed_plan,
            reminders=reminders
        )


# Global instance
coach_service = CoachService()

