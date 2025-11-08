"""
Job scoring service using skill vectors and rule-based matching
Implements the scoring algorithm: match% = 100 * (weighted overlap) - (gap_penalty)
"""
from typing import List, Dict, Any, Tuple
import re


class JobScoringService:
    """Service for scoring job matches using skill vectors"""
    
    def __init__(self):
        # Scoring weights
        self.CORE_MATCH_BONUS = 10
        self.ADJACENT_MATCH_BONUS = 5
        self.ADVANCED_MATCH_BONUS = 3
        self.REQUIRED_GAP_PENALTY = 8
        self.OPTIONAL_GAP_PENALTY = 4
        self.EXACT_TOOL_BONUS = 5
        self.EXPERIENCE_BOOST = 2
        
    def build_candidate_skill_vector(self, analysis: Dict[str, Any]) -> Dict[str, float]:
        """
        Build candidate skill vector from analysis
        Returns: {skill: weight} where weight is 0.0-1.0
        """
        skill_vector = {}
        
        # Core skills get weight 1.0
        core_skills = analysis.get("skills", {}).get("core", [])
        for skill in core_skills:
            skill_lower = skill.lower().strip()
            skill_vector[skill_lower] = 1.0
        
        # Adjacent skills get weight 0.7
        adjacent_skills = analysis.get("skills", {}).get("adjacent", [])
        for skill in adjacent_skills:
            skill_lower = skill.lower().strip()
            if skill_lower not in skill_vector:  # Don't override core
                skill_vector[skill_lower] = 0.7
        
        # Advanced skills get weight 0.5
        advanced_skills = analysis.get("skills", {}).get("advanced", [])
        for skill in advanced_skills:
            skill_lower = skill.lower().strip()
            if skill_lower not in skill_vector:  # Don't override core/adjacent
                skill_vector[skill_lower] = 0.5
        
        # Keywords detected get weight 0.3 (mentioned but not categorized)
        keywords = analysis.get("keywords_detected", [])
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            if keyword_lower not in skill_vector:
                skill_vector[keyword_lower] = 0.3
        
        # Strengths boost (if skill mentioned in strengths, boost weight)
        strengths = analysis.get("strengths", [])
        for strength in strengths:
            # Extract skills from strength text
            strength_lower = strength.lower()
            for skill_key in skill_vector.keys():
                if skill_key in strength_lower:
                    # Boost existing skill weight
                    skill_vector[skill_key] = min(1.0, skill_vector[skill_key] + 0.2)
        
        return skill_vector
    
    def extract_jd_skills(self, jd_text: str, jd_requirements: List[str] = None) -> Dict[str, float]:
        """
        Extract required skills from job description
        Returns: {skill: weight} where weight indicates importance (1.0 = required, 0.5 = nice-to-have)
        """
        jd_skill_vector = {}
        
        # Combine JD text and requirements
        full_text = jd_text
        if jd_requirements:
            full_text += " " + " ".join(jd_requirements)
        
        full_text_lower = full_text.lower()
        
        # Common tech skills to look for
        tech_skills = [
            # Languages
            "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#", "ruby", "php", "swift", "kotlin",
            # Frameworks
            "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring", "express", "next.js",
            # Databases
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb", "cassandra",
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "ci/cd", "github actions",
            # Data & ML
            "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "spark", "hadoop", "kafka", "airflow",
            # Tools
            "git", "linux", "bash", "rest api", "graphql", "microservices", "agile", "scrum",
            # Data specific
            "tableau", "power bi", "looker", "snowflake", "redshift", "bigquery", "s3", "etl",
            # Frontend
            "html", "css", "sass", "tailwind", "webpack", "vite", "jest", "cypress",
            # Backend
            "api", "rest", "graphql", "grpc", "message queue", "rabbitmq", "celery",
        ]
        
        # Check for required skills (mentioned with "required", "must have", "essential")
        required_patterns = [
            r"required.*?(\w+)",
            r"must have.*?(\w+)",
            r"essential.*?(\w+)",
            r"need.*?(\w+)",
            r"requirement.*?(\w+)",
        ]
        
        for pattern in required_patterns:
            matches = re.finditer(pattern, full_text_lower, re.IGNORECASE)
            for match in matches:
                skill = match.group(1).lower().strip()
                if len(skill) > 2:  # Filter out short words
                    jd_skill_vector[skill] = 1.0
        
        # Check for nice-to-have skills (mentioned with "preferred", "nice to have", "bonus")
        preferred_patterns = [
            r"preferred.*?(\w+)",
            r"nice to have.*?(\w+)",
            r"bonus.*?(\w+)",
            r"plus.*?(\w+)",
        ]
        
        for pattern in preferred_patterns:
            matches = re.finditer(pattern, full_text_lower, re.IGNORECASE)
            for match in matches:
                skill = match.group(1).lower().strip()
                if len(skill) > 2:
                    if skill not in jd_skill_vector:  # Don't override required
                        jd_skill_vector[skill] = 0.5
        
        # Check for tech skills in the list
        for skill in tech_skills:
            skill_lower = skill.lower()
            # Count occurrences
            count = full_text_lower.count(skill_lower)
            if count > 0:
                # More mentions = higher importance
                weight = min(1.0, 0.5 + (count * 0.1))
                if skill_lower not in jd_skill_vector or jd_skill_vector[skill_lower] < weight:
                    jd_skill_vector[skill_lower] = weight
        
        # If no skills found, extract from common patterns
        if not jd_skill_vector:
            # Look for "X years of Y" patterns
            years_pattern = r"(\d+)\+?\s*years?\s*(?:of|experience)?\s*(\w+)"
            matches = re.finditer(years_pattern, full_text_lower, re.IGNORECASE)
            for match in matches:
                years = int(match.group(1))
                skill = match.group(2).lower().strip()
                if len(skill) > 2:
                    weight = min(1.0, years / 5.0)  # Normalize to 0-1
                    jd_skill_vector[skill] = weight
        
        return jd_skill_vector
    
    def score_job_match(
        self,
        candidate_vector: Dict[str, float],
        jd_vector: Dict[str, float],
        resume_text: str = ""
    ) -> Tuple[int, List[str], List[str]]:
        """
        Score job match using rule-based algorithm
        Returns: (match_score, why_fit, gaps)
        
        Algorithm:
        - +10 for each core match (candidate has skill at 1.0)
        - +5 for each adjacent match (candidate has skill at 0.7)
        - +3 for each advanced match (candidate has skill at 0.5)
        - +5 bonus for exact tool match (e.g., "FastAPI", "Redshift")
        - -8 for each required gap (JD requires but candidate doesn't have)
        - -4 for each optional gap (JD prefers but candidate doesn't have)
        """
        score = 0
        why_fit = []
        gaps = []
        
        resume_lower = resume_text.lower() if resume_text else ""
        
        # Track matched skills
        matched_skills = set()
        
        # Score matches
        for jd_skill, jd_weight in jd_vector.items():
            jd_skill_lower = jd_skill.lower().strip()
            
            # Check if candidate has this skill
            candidate_weight = None
            for candidate_skill, weight in candidate_vector.items():
                # Exact match
                if candidate_skill == jd_skill_lower:
                    candidate_weight = weight
                    break
                # Partial match (e.g., "python" matches "python3")
                elif jd_skill_lower in candidate_skill or candidate_skill in jd_skill_lower:
                    candidate_weight = weight
                    break
            
            if candidate_weight is not None:
                # Candidate has this skill - add to why_fit
                matched_skills.add(jd_skill_lower)
                
                # Calculate match bonus based on candidate skill level
                if candidate_weight >= 1.0:
                    # Core skill match
                    bonus = self.CORE_MATCH_BONUS
                    why_fit.append(f"{jd_skill.title()} ✓ (core skill)")
                elif candidate_weight >= 0.7:
                    # Adjacent skill match
                    bonus = self.ADJACENT_MATCH_BONUS
                    why_fit.append(f"{jd_skill.title()} ✓ (adjacent skill)")
                elif candidate_weight >= 0.5:
                    # Advanced skill match
                    bonus = self.ADVANCED_MATCH_BONUS
                    why_fit.append(f"{jd_skill.title()} ✓ (advanced skill)")
                else:
                    # Mentioned skill match
                    bonus = 2
                    why_fit.append(f"{jd_skill.title()} ✓ (mentioned)")
                
                score += bonus
                
                # Exact tool bonus (check for specific tools/technologies)
                exact_tools = ["fastapi", "redshift", "snowflake", "bigquery", "airflow", "kafka", "terraform", "kubernetes"]
                if jd_skill_lower in exact_tools:
                    score += self.EXACT_TOOL_BONUS
                    why_fit.append(f"Exact tool match: {jd_skill.title()} (+{self.EXACT_TOOL_BONUS})")
                
                # Experience boost (if mentioned in resume)
                if jd_skill_lower in resume_lower:
                    score += self.EXPERIENCE_BOOST
            else:
                # Candidate doesn't have this skill - add to gaps
                if jd_weight >= 1.0:
                    # Required skill gap
                    penalty = self.REQUIRED_GAP_PENALTY
                    gaps.append(f"{jd_skill.title()} ❌ (required)")
                else:
                    # Optional skill gap
                    penalty = self.OPTIONAL_GAP_PENALTY
                    gaps.append(f"{jd_skill.title()} ❌ (preferred)")
                
                score -= penalty
        
        # Normalize score to 0-100 range
        # Base score is around 50, then adjust based on matches/gaps
        normalized_score = max(0, min(100, 50 + score))
        
        # Limit why_fit and gaps to top items
        why_fit = why_fit[:5]  # Top 5 matches
        gaps = gaps[:3]  # Top 3 gaps
        
        # If no matches found, add generic message
        if not why_fit:
            why_fit.append("Relevant role match")
        
        return int(normalized_score), why_fit, gaps
    
    def generate_fix_actions(self, gaps: List[str], resume_text: str = "") -> List[str]:
        """
        Generate micro-actions for gaps
        Returns: List of actionable learning tasks
        """
        fix_actions = []
        
        for gap in gaps:
            # Extract skill name (remove ❌ and status)
            skill_match = re.search(r'([A-Za-z\s]+)', gap)
            if skill_match:
                skill = skill_match.group(1).strip()
                skill_lower = skill.lower()
                
                # Generate specific learning action based on skill
                if "aws" in skill_lower or "cloud" in skill_lower:
                    fix_actions.append(f"Learn AWS S3 basics (2h) - FreeCodeCamp AWS course")
                elif "python" in skill_lower:
                    fix_actions.append(f"Complete Python fundamentals (4h) - Python.org tutorial")
                elif "sql" in skill_lower:
                    fix_actions.append(f"Practice SQL queries (3h) - SQLBolt interactive tutorial")
                elif "react" in skill_lower or "frontend" in skill_lower:
                    fix_actions.append(f"Build React app (5h) - React official tutorial")
                elif "docker" in skill_lower or "kubernetes" in skill_lower:
                    fix_actions.append(f"Learn containerization basics (3h) - Docker docs")
                elif "data" in skill_lower or "analyst" in skill_lower:
                    fix_actions.append(f"Learn data analysis with pandas (4h) - DataCamp course")
                else:
                    fix_actions.append(f"Learn {skill} basics (3h) - Online course")
        
        return fix_actions[:3]  # Top 3 actions

