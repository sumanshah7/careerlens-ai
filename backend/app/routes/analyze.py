from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from app.models.schemas import AnalyzeResponse
from app.services.anthropic_svc import anthropic_service
from app.services.openai_svc import openai_service
from app.services.amplitude import amplitude_service
import hashlib
import os
import json
from typing import Dict, Any, List, Tuple

router = APIRouter(prefix="/api/analyze-resume", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    resume_text: str
    preferred_roles: list[str] | None = None
    top_k_domains: int = 5  # Open-world: up to 5 domains
    text: str | None = None  # Legacy support
    target_role: str | None = None  # Primary field (snake_case) - user's selected target role
    targetRole: str | None = None  # Legacy support (camelCase)
    target_roles: list[str] | None = None  # Legacy support


# Domain keyword groups - open-world (tech and non-tech)
DOMAIN_KEYWORDS = {
    # Tech roles
    "Data Analyst": ["sql", "excel", "power bi", "tableau", "pandas", "numpy", "statistics", "regression", "etl", "looker", "snowflake", "bigquery"],
    "Frontend": ["react", "javascript", "next.js", "redux", "css", "tailwind"],  # Removed typescript - only add if explicitly present
    "Backend": ["python", "java", "node.js", "nodejs", "spring", "django", "flask", "express"],
    "Full-Stack": ["react", "python", "node.js", "full stack", "fullstack"],  # Removed typescript - only add if explicitly present
    "Data Engineer": ["airflow", "dbt", "spark", "kafka", "datalake", "glue", "emr"],
    "ML/AI": ["sklearn", "pytorch", "tensorflow", "sagemaker", "bedrock", "llm", "vector", "machine learning", "ml", "ai"],
    "Cloud/SA": ["aws", "azure", "gcp", "architecture", "lambda", "api gateway", "vpc", "iam"],
    "DevOps": ["docker", "kubernetes", "k8s", "ci/cd", "jenkins", "terraform", "ansible"],
    "QA": ["testing", "selenium", "cypress", "jest", "pytest", "qa", "quality assurance"],
    "Product/BA": ["product", "business analyst", "requirements", "agile", "scrum", "jira"],
    # Healthcare & Clinical
    "Registered Nurse": ["nursing", "patient care", "medication", "vitals", "charting", "epic", "ehr", "emr", "hipaa", "cpr", "bcls", "acls"],
    "Medical Assistant": ["medical assistant", "patient care", "vitals", "phlebotomy", "ehr", "epic", "cpt", "icd-10", "scheduling", "appointments"],
    "Clinical Research Coordinator": ["clinical trials", "irb", "gcp", "informed consent", "protocol", "redcap", "data entry", "adverse events", "regulatory"],
    "Public Health Analyst": ["epidemiology", "surveillance", "spss", "stata", "r", "survey", "literature review", "policy", "outbreak", "program evaluation"],
    # Education
    "Teacher": ["lesson planning", "iep", "classroom management", "assessment", "curriculum", "education", "teaching", "pedagogy"],
    "Education Coordinator": ["curriculum design", "assessment", "iep", "educational programs", "student services"],
    # Finance/Accounting
    "Accountant": ["gaap", "accounting", "quickbooks", "excel", "budgeting", "audits", "financial statements", "reconciliation"],
    "Financial Analyst": ["financial analysis", "excel models", "budgeting", "forecasting", "financial reporting", "gaap"],
    # Operations/Admin
    "Operations Coordinator": ["scheduling", "procurement", "sops", "inventory", "crm", "operations", "logistics"],
    "Administrative Assistant": ["scheduling", "administrative", "office management", "calendar", "correspondence"],
    # Marketing
    "Marketing Specialist": ["marketing", "campaigns", "social media", "seo", "content", "analytics", "branding"],
    # Sales
    "Sales Representative": ["sales", "crm", "customer relations", "quota", "prospecting", "negotiation"],
    # Creative/Design
    "Animation/Motion Graphics": ["animation", "motion graphics", "after effects", "maya", "blender", "character design", "storyboarding", "3d animation", "2d animation", "motion design", "visual effects", "vfx", "rigging", "unreal engine", "godot", "motion capture", "mocap"],
    "Graphic Designer": ["graphic design", "photoshop", "illustrator", "indesign", "branding", "visual design", "layout"],
    "UI/UX Designer": ["ui/ux", "user interface", "user experience", "figma", "wireframing", "prototyping", "design system"]
}

# Role competency matrices - required skills for each role (tech and non-tech)
ROLE_COMPETENCY_MATRIX = {
    # Tech roles
    "Data Analyst": {
        "SQL": ["sql", "join", "window function", "cte", "subquery", "aggregate"],
        "Excel": ["excel", "pivot", "vlookup", "xlookup", "pivot table"],
        "BI Tools": ["power bi", "tableau", "looker", "dashboard", "visualization"],
        "Statistics": ["statistics", "statistical", "hypothesis", "a/b", "ab test", "regression", "correlation"],
        "Python": ["python", "pandas", "numpy", "dataframe"],
        "Data Modeling": ["data modeling", "etl", "data pipeline", "data warehouse"],
        "Warehouse": ["snowflake", "bigquery", "redshift", "data warehouse", "warehouse"],
        "Dashboarding": ["dashboard", "kpi", "metric", "reporting"]
    },
    "AI Engineer": {
        "Deep Learning": ["pytorch", "tensorflow", "keras", "neural network", "deep learning"],
        "LLMs": ["llm", "transformer", "gpt", "bert", "language model"],
        "MLOps": ["mlops", "model deployment", "model serving", "model monitoring"],
        "Vector DBs": ["vector", "embedding", "pinecone", "weaviate", "vector database"],
        "Python ML": ["python", "scikit-learn", "sklearn", "pandas", "numpy"],
        "Cloud ML": ["sagemaker", "vertex ai", "bedrock", "ml platform"],
        "Model Evaluation": ["model evaluation", "metrics", "cross-validation", "hyperparameter"]
    },
    "Frontend Engineer": {
        "React": ["react", "jsx", "hooks", "component"],
        # TypeScript is optional - only suggest if React is present but TypeScript is not
        "Modern CSS": ["css", "tailwind", "styled-components", "sass"],
        "Testing": ["testing", "jest", "react testing library", "cypress"],
        "Accessibility": ["accessibility", "a11y", "aria", "wcag"]
    },
    "Backend Engineer": {
        "Backend Framework": ["django", "flask", "express", "spring", "fastapi"],
        "Database": ["sql", "postgresql", "mongodb", "database"],
        "API Design": ["api", "rest", "graphql", "endpoint"],
        "Testing": ["testing", "pytest", "unittest", "integration test"]
    },
    "DevOps": {
        "Containerization": ["docker", "containers", "containerization"],
        "Orchestration": ["kubernetes", "k8s", "orchestration", "helm"],
        "CI/CD": ["ci/cd", "jenkins", "github actions", "gitlab ci", "circleci", "travis", "continuous integration", "continuous deployment"],
        "Infrastructure as Code": ["terraform", "ansible", "pulumi", "cloudformation", "infrastructure as code", "iac"],
        "Cloud Platforms": ["aws", "azure", "gcp", "cloud", "ec2", "s3", "lambda"],
        "Monitoring": ["monitoring", "prometheus", "grafana", "datadog", "new relic", "observability"],
        "Scripting": ["bash", "python", "shell scripting", "automation"]
    },
    # Healthcare & Clinical
    "Clinical Research Coordinator": {
        "IRB": ["irb", "institutional review board", "protocol", "submission"],
        "GCP": ["gcp", "good clinical practice", "regulatory", "compliance"],
        "REDCap": ["redcap", "data entry", "database", "forms"],
        "Informed Consent": ["informed consent", "consent process", "patient communication"],
        "Clinical Trials": ["clinical trials", "study protocol", "adverse events", "safety"],
        "Data Management": ["data management", "case report forms", "source documents"]
    },
    "Medical Assistant": {
        "Patient Care": ["patient care", "vitals", "medical history", "examination"],
        "EHR/EMR": ["ehr", "emr", "epic", "electronic health record", "charting"],
        "CPT/ICD-10": ["cpt", "icd-10", "coding", "billing"],
        "Phlebotomy": ["phlebotomy", "blood draw", "specimen collection"],
        "Scheduling": ["scheduling", "appointments", "calendar management"]
    },
    "Public Health Analyst": {
        "Epidemiology": ["epidemiology", "surveillance", "outbreak", "disease tracking"],
        "Statistical Analysis": ["spss", "stata", "r", "statistical analysis", "regression"],
        "Survey Design": ["survey", "questionnaire", "data collection"],
        "Literature Review": ["literature review", "research", "evidence-based"],
        "Policy": ["policy", "program evaluation", "public health policy"],
        "Data Visualization": ["visualization", "reporting", "dashboards"]
    },
    # Education
    "Teacher": {
        "Lesson Planning": ["lesson planning", "curriculum", "instructional design"],
        "IEP": ["iep", "individualized education program", "special education"],
        "Classroom Management": ["classroom management", "student engagement", "discipline"],
        "Assessment": ["assessment", "grading", "rubrics", "evaluation"]
    },
    # Finance/Accounting
    "Accountant": {
        "GAAP": ["gaap", "generally accepted accounting principles", "accounting standards"],
        "QuickBooks": ["quickbooks", "accounting software", "bookkeeping"],
        "Financial Statements": ["financial statements", "balance sheet", "income statement"],
        "Reconciliation": ["reconciliation", "audits", "financial reporting"],
        "Excel": ["excel", "spreadsheets", "financial models"]
    },
    "Financial Analyst": {
        "Financial Analysis": ["financial analysis", "forecasting", "budgeting", "financial modeling"],
        "Excel Models": ["excel", "financial models", "spreadsheets", "vba"],
        "Financial Reporting": ["financial reporting", "gaap", "financial statements"],
        "Data Analysis": ["data analysis", "statistics", "trend analysis"]
    },
    # Operations/Admin
    "Operations Coordinator": {
        "Scheduling": ["scheduling", "coordination", "logistics"],
        "SOPs": ["sops", "standard operating procedures", "process documentation"],
        "Inventory": ["inventory", "procurement", "supply chain"],
        "CRM": ["crm", "customer relationship management", "database"]
    }
}


def classify_domains(resume_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Classify multiple domains from resume text using keyword matching (open-world)"""
    resume_lower = resume_text.lower()
    domain_scores = {}
    
    # Check for explicit role mentions first (highest priority)
    explicit_role_mentions = {
        "Data Analyst": ["data analyst", "data analysis", "analyst intern", "business analyst"],
        "Frontend": ["frontend engineer", "front-end engineer", "front end engineer", "ui developer", "react developer"],
        "Backend": ["backend engineer", "back-end engineer", "back end engineer", "api developer"],
        "Full-Stack": ["full stack", "fullstack", "full-stack developer"],
        "ML/AI": ["ml engineer", "ai engineer", "machine learning engineer", "data scientist"],
        "Data Engineer": ["data engineer", "etl engineer"],
        "Product/BA": ["product manager", "business analyst", "product analyst"],
        "Clinical Research Coordinator": ["clinical research coordinator", "crc", "clinical trial coordinator"],
        "Public Health Analyst": ["public health analyst", "epidemiologist"],
        "Teacher": ["teacher", "educator", "instructor"],
        "Accountant": ["accountant", "cpa"],
        "Financial Analyst": ["financial analyst", "finance analyst"]
    }
    
    # Boost score for explicit role mentions
    for domain, mentions in explicit_role_mentions.items():
        for mention in mentions:
            if mention in resume_lower:
                # Strong boost for explicit role mention
                domain_scores[domain] = domain_scores.get(domain, 0) + 0.5
    
    # Then check keyword matches
    for domain, keywords in DOMAIN_KEYWORDS.items():
        matches = sum(1 for keyword in keywords if keyword in resume_lower)
        if matches > 0:
            # Score based on match ratio, with boost for multiple matches
            base_score = min(1.0, (matches / len(keywords)) * 1.5)
            # Add to existing score if domain was already found via explicit mention
            domain_scores[domain] = domain_scores.get(domain, 0) + base_score
    
    # Special handling: If Data Analyst keywords are strong, prioritize it
    data_analyst_keywords = ["sql", "excel", "power bi", "tableau", "pandas", "numpy", "statistics", "regression", "etl", "looker", "snowflake", "bigquery"]
    data_analyst_matches = sum(1 for keyword in data_analyst_keywords if keyword in resume_lower)
    if data_analyst_matches >= 3:  # Strong Data Analyst signal
        # Boost Data Analyst if it has strong keyword support
        if "Data Analyst" in domain_scores:
            domain_scores["Data Analyst"] = max(domain_scores["Data Analyst"], 0.8)
        elif data_analyst_matches >= 5:  # Very strong signal
            domain_scores["Data Analyst"] = 0.85
    
    # Special handling: If Frontend keywords exist but Data Analyst is stronger, don't let Frontend override
    if "Data Analyst" in domain_scores and "Frontend" in domain_scores:
        if domain_scores["Data Analyst"] >= 0.7 and domain_scores["Frontend"] < 0.6:
            # Data Analyst is clearly primary, reduce Frontend score
            domain_scores["Frontend"] = min(domain_scores["Frontend"], 0.5)
    
    if not domain_scores:
        # Default fallback - try to infer from common terms
        if "patient" in resume_lower or "medical" in resume_lower or "clinical" in resume_lower:
            return [{"name": "Healthcare Professional", "score": 0.3}]
        elif "teaching" in resume_lower or "education" in resume_lower or "classroom" in resume_lower:
            return [{"name": "Education Professional", "score": 0.3}]
        elif "accounting" in resume_lower or "financial" in resume_lower or "gaap" in resume_lower:
            return [{"name": "Finance Professional", "score": 0.3}]
        else:
            return [{"name": "Professional", "score": 0.3}]
    
    # Sort by score descending and return top_k
    sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [{"name": domain, "score": min(1.0, score)} for domain, score in sorted_domains]


def classify_domain(resume_text: str) -> Tuple[str, float]:
    """Legacy function - returns top domain for backward compatibility"""
    domains = classify_domains(resume_text, top_k=1)
    if domains:
        return domains[0]["name"], domains[0]["score"]
    return "Software Engineer", 0.3


def extract_keywords(resume_text: str, domain: str) -> List[str]:
    """Extract detected keywords from resume text"""
    resume_lower = resume_text.lower()
    keywords = []
    
    # Get keywords for the detected domain
    domain_keywords = DOMAIN_KEYWORDS.get(domain, [])
    for keyword in domain_keywords:
        if keyword in resume_lower:
            keywords.append(keyword)
    
    # Also check other common keywords
    all_keywords = set()
    for kw_list in DOMAIN_KEYWORDS.values():
        all_keywords.update(kw_list)
    
    for keyword in all_keywords:
        if keyword in resume_lower and keyword not in keywords:
            keywords.append(keyword)
    
    return keywords[:20]  # Limit to top 20


def keyword_based_analysis(resume_text: str, top_k_domains: int = 5, target_role: str | None = None) -> Dict[str, Any]:
    """Perform keyword-based analysis when LLM is not available (open-world)"""
    from app.models.schemas import Skill
    
    resume_lower = resume_text.lower()
    domains = classify_domains(resume_text, top_k_domains)
    
    # If target_role is provided, prioritize it as the top domain
    if target_role:
        target_role_lower = target_role.lower()
        target_domain = None
        
        if "ai engineer" in target_role_lower or "ml engineer" in target_role_lower or "machine learning" in target_role_lower:
            target_domain = "ML/AI"
        elif "data analyst" in target_role_lower or "business analyst" in target_role_lower:
            target_domain = "Data Analyst"
        elif "data engineer" in target_role_lower:
            target_domain = "Data Engineer"
        elif "frontend" in target_role_lower or "ui developer" in target_role_lower or "react" in target_role_lower:
            target_domain = "Frontend"
        elif "backend" in target_role_lower or "api developer" in target_role_lower:
            target_domain = "Backend"
        elif "full stack" in target_role_lower or "fullstack" in target_role_lower or "full-stack" in target_role_lower:
            target_domain = "Full-Stack"
        elif "devops" in target_role_lower or "dev ops" in target_role_lower or "sre" in target_role_lower or "site reliability" in target_role_lower:
            target_domain = "DevOps"
        elif "cloud" in target_role_lower and ("engineer" in target_role_lower or "architect" in target_role_lower):
            target_domain = "Cloud/SA"
        elif "software engineer" in target_role_lower or "software developer" in target_role_lower:
            target_domain = "Backend"
        
        # If target_domain found, prioritize it
        if target_domain:
            target_domain_index = next((i for i, d in enumerate(domains) if d["name"] == target_domain), None)
            
            if target_domain_index is not None:
                # Move target domain to top and boost its score
                target_domain_obj = domains.pop(target_domain_index)
                target_domain_obj["score"] = min(1.0, max(0.8, target_domain_obj["score"]))  # Ensure at least 0.8
                domains.insert(0, target_domain_obj)
            else:
                # Add target domain at top with high score
                domains.insert(0, {"name": target_domain, "score": 0.85})
            
            domains = domains[:top_k_domains]  # Limit to top_k
    
    # Use top domain for keyword extraction (open-world)
    top_domain = domains[0]["name"] if domains else "Professional"
    keywords = extract_keywords(resume_text, top_domain)
    
    # Extract skills based on keywords
    skills_core = []
    skills_adjacent = []
    skills_advanced = []
    
    # Map keywords to skill names (open-world: tech and non-tech)
    keyword_to_skill = {
        # Tech
        "react": "React", "typescript": "TypeScript", "javascript": "JavaScript",
        "python": "Python", "java": "Java", "node.js": "Node.js", "nodejs": "Node.js",
        "sql": "SQL", "excel": "Excel", "power bi": "Power BI", "tableau": "Tableau",
        "pandas": "Pandas", "numpy": "NumPy", "aws": "AWS", "azure": "Azure", "gcp": "GCP",
        "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
        "airflow": "Airflow", "spark": "Spark", "kafka": "Kafka",
        "pytorch": "PyTorch", "tensorflow": "TensorFlow", "sklearn": "Scikit-learn",
        # Healthcare
        "epic": "Epic", "ehr": "EHR", "emr": "EMR", "redcap": "REDCap",
        "irb": "IRB", "cpt": "CPT", "icd-10": "ICD-10",
        "phlebotomy": "Phlebotomy", "hipaa": "HIPAA", "clinical trials": "Clinical Trials",
        # Public Health
        "spss": "SPSS", "stata": "Stata", "epidemiology": "Epidemiology",
        "surveillance": "Surveillance", "survey": "Survey Design",
        # Education
        "iep": "IEP", "lesson planning": "Lesson Planning", "curriculum": "Curriculum",
        "classroom management": "Classroom Management",
        # Finance
        "gaap": "GAAP", "quickbooks": "QuickBooks", "reconciliation": "Reconciliation",
        "financial analysis": "Financial Analysis"
    }
    
    detected_skills = []
    for keyword in keywords:
        skill_name = keyword_to_skill.get(keyword, keyword.title())
        if skill_name not in [s.name for s in detected_skills]:
            # Determine level based on frequency
            count = resume_lower.count(keyword)
            level = "core" if count >= 2 else "adjacent"
            detected_skills.append(Skill(name=skill_name, level=level, status="have"))
    
    # Organize skills by level
    for skill in detected_skills:
        if skill.level == "core":
            skills_core.append(skill.name)
        elif skill.level == "adjacent":
            skills_adjacent.append(skill.name)
        else:
            skills_advanced.append(skill.name)
    
    # Generate strengths based on detected skills AND target_role (if provided) or top domain - ONLY if evidenced in resume
    strengths = []
    top_domain = domains[0]["name"] if domains else "Professional"
    top_domain_lower = top_domain.lower()
    # Use target_role if provided, otherwise use top_domain
    role_for_strengths = (target_role or top_domain).lower()
    
    # Role-aware strengths: show strengths relevant to the target_role (if provided) or top domain
    if "ai engineer" in role_for_strengths or "ml engineer" in role_for_strengths or "machine learning" in role_for_strengths:
        if "python" in resume_lower:
            strengths.append("Python programming skills")
        if "pytorch" in resume_lower or "tensorflow" in resume_lower:
            strengths.append("Deep learning framework experience")
        if "machine learning" in resume_lower or "ml" in resume_lower:
            strengths.append("Machine learning experience")
        if "ai" in resume_lower or "artificial intelligence" in resume_lower:
            strengths.append("AI/ML expertise")
    elif "data analyst" in role_for_strengths or ("data" in role_for_strengths and "engineer" not in role_for_strengths):
        if "sql" in resume_lower:
            strengths.append("SQL and database querying skills")
        if "tableau" in resume_lower or "power bi" in resume_lower:
            strengths.append("Data visualization expertise")
        if "python" in resume_lower and ("pandas" in resume_lower or "numpy" in resume_lower):
            strengths.append("Python data analysis capabilities")
        if "excel" in resume_lower:
            strengths.append("Excel proficiency for data analysis")
    elif "frontend" in target_role_lower or "react" in target_role_lower:
        if "react" in resume_lower:
            strengths.append("React development experience")
        # Only add TypeScript if it's actually in the resume
        if "typescript" in resume_lower or "ts " in resume_lower or " typescript" in resume_lower:
            strengths.append("TypeScript proficiency")
        if "javascript" in resume_lower:
            strengths.append("JavaScript expertise")
    elif "backend" in target_role_lower:
        if "python" in resume_lower or "java" in resume_lower or "node" in resume_lower:
            strengths.append("Backend programming experience")
        if "api" in resume_lower or "rest" in resume_lower:
            strengths.append("API development skills")
    elif "ai engineer" in target_role_lower or "ml engineer" in target_role_lower or "machine learning" in target_role_lower:
        if "python" in resume_lower:
            strengths.append("Python programming skills")
        if "pytorch" in resume_lower or "tensorflow" in resume_lower:
            strengths.append("Deep learning framework experience")
        if "machine learning" in resume_lower or "ml" in resume_lower:
            strengths.append("Machine learning experience")
    elif "clinical research" in target_role_lower or "crc" in target_role_lower:
        if "irb" in resume_lower or "institutional review board" in resume_lower:
            strengths.append("IRB protocol experience")
        if "gcp" in resume_lower or "good clinical practice" in resume_lower:
            strengths.append("GCP compliance knowledge")
        if "redcap" in resume_lower:
            strengths.append("REDCap data management")
        if "clinical trials" in resume_lower:
            strengths.append("Clinical trials experience")
    elif "medical assistant" in target_role_lower:
        if "ehr" in resume_lower or "emr" in resume_lower or "epic" in resume_lower:
            strengths.append("EHR/EMR system proficiency")
        if "cpt" in resume_lower or "icd-10" in resume_lower:
            strengths.append("Medical coding knowledge")
        if "phlebotomy" in resume_lower:
            strengths.append("Phlebotomy skills")
        if "patient care" in resume_lower:
            strengths.append("Patient care experience")
    elif "public health" in target_role_lower:
        if "epidemiology" in resume_lower or "surveillance" in resume_lower:
            strengths.append("Epidemiology expertise")
        if "spss" in resume_lower or "stata" in resume_lower or " r " in resume_lower:
            strengths.append("Statistical analysis skills")
        if "survey" in resume_lower:
            strengths.append("Survey design experience")
    elif "teacher" in target_role_lower or "educator" in target_role_lower:
        if "lesson planning" in resume_lower or "curriculum" in resume_lower:
            strengths.append("Curriculum design experience")
        if "iep" in resume_lower:
            strengths.append("IEP management")
        if "classroom" in resume_lower:
            strengths.append("Classroom management experience")
    elif "accountant" in target_role_lower or "financial" in target_role_lower:
        if "gaap" in resume_lower:
            strengths.append("GAAP knowledge")
        if "quickbooks" in resume_lower:
            strengths.append("QuickBooks proficiency")
        if "reconciliation" in resume_lower:
            strengths.append("Financial reconciliation skills")
        if "financial" in resume_lower:
            strengths.append("Financial analysis experience")
    
    # Add general strengths based on core skills if not role-specific
    if not strengths and skills_core:
        for skill in skills_core[:3]:
            skill_lower = skill.lower()
            if skill_lower in resume_lower or any(kw in resume_lower for kw in skill_lower.split()):
                strengths.append(f"Experience with {skill}")
    
    # Only add generic experience if "experience" or "years" is actually mentioned AND we have some strengths
    if not strengths and ("experience" in resume_lower or "years" in resume_lower):
        strengths.append("Demonstrated professional experience")
    
    # Ensure strengths is never empty
    if not strengths:
        if skills_core:
            strengths.append(f"Proficiency in {skills_core[0]}")
        elif target_role:
            strengths.append(f"Relevant background for {target_role}")
        else:
            strengths.append("Professional background in relevant domain")
    
    # Generate areas for growth based on target_role and domain
    areas_for_growth = []
    target_role_lower = (target_role or "").lower()
    
    # Role-aware gap detection
    if "ai engineer" in target_role_lower or "ml engineer" in target_role_lower or "machine learning" in target_role_lower:
        # AI Engineer specific gaps
        if "pytorch" not in resume_lower and "tensorflow" not in resume_lower:
            areas_for_growth.append("Deep learning frameworks (PyTorch or TensorFlow)")
        if "llm" not in resume_lower and "transformer" not in resume_lower and "gpt" not in resume_lower:
            areas_for_growth.append("Large Language Models (LLMs) and transformer architectures")
        if "mlops" not in resume_lower and "model deployment" not in resume_lower:
            areas_for_growth.append("MLOps and model deployment practices")
        if "vector" not in resume_lower and "embedding" not in resume_lower:
            areas_for_growth.append("Vector databases and embeddings")
        if "python" not in resume_lower:
            areas_for_growth.append("Python for machine learning")
        if "sagemaker" not in resume_lower and "vertex" not in resume_lower:
            areas_for_growth.append("Cloud ML platforms (AWS SageMaker, GCP Vertex AI)")
    
    elif "data analyst" in target_role_lower:
        # Data Analyst competency matrix - check each required skill area
        matrix = ROLE_COMPETENCY_MATRIX.get("Data Analyst", {})
        
        # SQL: joins, window functions, CTEs
        if "sql" not in resume_lower:
            areas_for_growth.append("SQL fundamentals (joins, window functions, CTEs)")
        elif "join" not in resume_lower and "window" not in resume_lower and "cte" not in resume_lower:
            areas_for_growth.append("Advanced SQL (window functions, CTEs)")
        
        # Excel: pivot tables, VLOOKUP/XLOOKUP
        if "excel" not in resume_lower:
            areas_for_growth.append("Excel (pivot tables, VLOOKUP/XLOOKUP)")
        elif "pivot" not in resume_lower and "vlookup" not in resume_lower and "xlookup" not in resume_lower:
            areas_for_growth.append("Advanced Excel (pivot tables, lookup functions)")
        
        # BI Tools: Power BI, Tableau, Looker
        if "tableau" not in resume_lower and "power bi" not in resume_lower and "looker" not in resume_lower:
            areas_for_growth.append("BI tools (Power BI, Tableau, or Looker)")
        elif "dashboard" not in resume_lower and "visualization" not in resume_lower:
            areas_for_growth.append("Dashboard creation and data visualization")
        
        # Statistics: hypothesis tests, A/B testing
        if "statistics" not in resume_lower and "statistical" not in resume_lower:
            areas_for_growth.append("Statistical analysis (hypothesis testing, A/B testing)")
        elif ("hypothesis" not in resume_lower and "a/b" not in resume_lower and "ab test" not in resume_lower):
            areas_for_growth.append("A/B testing design and evaluation")
        
        # Python: pandas, numpy
        if "python" not in resume_lower:
            areas_for_growth.append("Python for data analysis (pandas, numpy)")
        elif "pandas" not in resume_lower and "numpy" not in resume_lower:
            areas_for_growth.append("Python data libraries (pandas, numpy)")
        
        # Data Modeling/ETL
        if "etl" not in resume_lower and "data pipeline" not in resume_lower and "data modeling" not in resume_lower:
            areas_for_growth.append("Data modeling and ETL processes")
        
        # Warehouse: Snowflake, BigQuery, Redshift
        if "snowflake" not in resume_lower and "bigquery" not in resume_lower and "redshift" not in resume_lower and "data warehouse" not in resume_lower:
            areas_for_growth.append("Data warehouse platforms (Snowflake, BigQuery, or Redshift)")
        
        # Dashboarding KPIs
        if "kpi" not in resume_lower and "metric" not in resume_lower and "dashboard" not in resume_lower:
            areas_for_growth.append("KPI dashboarding and metric reporting")
    
    elif "frontend" in target_role_lower or "react" in target_role_lower:
        # Frontend Engineer specific gaps - only suggest if React is present
        if "react" in resume_lower:
            # Only suggest TypeScript if React is present but TypeScript is not
            if "typescript" not in resume_lower and "ts " not in resume_lower and " typescript" not in resume_lower:
                areas_for_growth.append("TypeScript for type safety")
            if "testing" not in resume_lower and "jest" not in resume_lower:
                areas_for_growth.append("Testing frameworks (Jest, React Testing Library)")
            if "accessibility" not in resume_lower and "a11y" not in resume_lower:
                areas_for_growth.append("Web accessibility (a11y)")
        else:
            # If React is not present, suggest it
            areas_for_growth.append("React framework")
    elif "clinical research" in target_role_lower or "crc" in target_role_lower:
        # Clinical Research Coordinator specific gaps
        matrix = ROLE_COMPETENCY_MATRIX.get("Clinical Research Coordinator", {})
        for skill_area, keywords in matrix.items():
            has_skill = any(kw in resume_lower for kw in keywords)
            if not has_skill:
                areas_for_growth.append(f"{skill_area}")
    elif "medical assistant" in target_role_lower:
        # Medical Assistant specific gaps
        matrix = ROLE_COMPETENCY_MATRIX.get("Medical Assistant", {})
        for skill_area, keywords in matrix.items():
            has_skill = any(kw in resume_lower for kw in keywords)
            if not has_skill:
                areas_for_growth.append(f"{skill_area}")
    elif "public health" in target_role_lower:
        # Public Health Analyst specific gaps
        matrix = ROLE_COMPETENCY_MATRIX.get("Public Health Analyst", {})
        for skill_area, keywords in matrix.items():
            has_skill = any(kw in resume_lower for kw in keywords)
            if not has_skill:
                areas_for_growth.append(f"{skill_area}")
    elif "teacher" in target_role_lower or "educator" in target_role_lower:
        # Teacher specific gaps
        matrix = ROLE_COMPETENCY_MATRIX.get("Teacher", {})
        for skill_area, keywords in matrix.items():
            has_skill = any(kw in resume_lower for kw in keywords)
            if not has_skill:
                areas_for_growth.append(f"{skill_area}")
    elif "accountant" in target_role_lower:
        # Accountant specific gaps
        matrix = ROLE_COMPETENCY_MATRIX.get("Accountant", {})
        for skill_area, keywords in matrix.items():
            has_skill = any(kw in resume_lower for kw in keywords)
            if not has_skill:
                areas_for_growth.append(f"{skill_area}")
    elif "financial analyst" in target_role_lower:
        # Financial Analyst specific gaps
        matrix = ROLE_COMPETENCY_MATRIX.get("Financial Analyst", {})
        for skill_area, keywords in matrix.items():
            has_skill = any(kw in resume_lower for kw in keywords)
            if not has_skill:
                areas_for_growth.append(f"{skill_area}")
    elif "operations" in target_role_lower:
        # Operations Coordinator specific gaps
        matrix = ROLE_COMPETENCY_MATRIX.get("Operations Coordinator", {})
        for skill_area, keywords in matrix.items():
            has_skill = any(kw in resume_lower for kw in keywords)
            if not has_skill:
                areas_for_growth.append(f"{skill_area}")
    elif "devops" in target_role_lower or "dev ops" in target_role_lower or "sre" in target_role_lower or "site reliability" in target_role_lower:
        # DevOps specific gaps
        matrix = ROLE_COMPETENCY_MATRIX.get("DevOps", {})
        for skill_area, keywords in matrix.items():
            has_skill = any(kw in resume_lower for kw in keywords)
            if not has_skill:
                areas_for_growth.append(f"{skill_area}")
    elif "cloud" in target_role_lower and ("engineer" in target_role_lower or "architect" in target_role_lower):
        # Cloud/SA specific gaps
        if "aws" not in resume_lower and "azure" not in resume_lower and "gcp" not in resume_lower:
            areas_for_growth.append("Cloud platform expertise (AWS, Azure, or GCP)")
        if "terraform" not in resume_lower and "cloudformation" not in resume_lower:
            areas_for_growth.append("Infrastructure as Code (Terraform or CloudFormation)")
        if "architecture" not in resume_lower and "design" not in resume_lower:
            areas_for_growth.append("Cloud architecture and design patterns")
    
    else:
        # Domain-based gaps if no specific target_role - use competency matrix if available
        if top_domain in ROLE_COMPETENCY_MATRIX:
            matrix = ROLE_COMPETENCY_MATRIX[top_domain]
            for skill_area, keywords in matrix.items():
                # Check if any keyword in this skill area is present
                has_skill = any(kw in resume_lower for kw in keywords)
                if not has_skill:
                    areas_for_growth.append(f"{skill_area}")
        elif top_domain == "ML/AI":
            if "pytorch" not in resume_lower and "tensorflow" not in resume_lower:
                areas_for_growth.append("Deep learning frameworks (PyTorch or TensorFlow)")
            if "mlops" not in resume_lower:
                areas_for_growth.append("MLOps and model deployment")
        elif top_domain == "Data Analyst":
            # Use Data Analyst matrix
            matrix = ROLE_COMPETENCY_MATRIX.get("Data Analyst", {})
            for skill_area, keywords in matrix.items():
                has_skill = any(kw in resume_lower for kw in keywords)
                if not has_skill:
                    areas_for_growth.append(f"{skill_area}")
        elif top_domain == "Frontend":
            if "testing" not in resume_lower:
                areas_for_growth.append("Testing frameworks")
            if "accessibility" not in resume_lower:
                areas_for_growth.append("Web accessibility")
        else:
            if "docker" not in resume_lower:
                areas_for_growth.append("Containerization technologies")
    
    # Ensure areas_for_growth is never empty - add at least one generic gap if nothing found
    if not areas_for_growth:
        if top_domain == "Data Analyst":
            areas_for_growth.append("Advanced SQL techniques (window functions, CTEs)")
        elif top_domain == "ML/AI":
            areas_for_growth.append("Deep learning frameworks (PyTorch or TensorFlow)")
        elif top_domain == "Frontend":
            areas_for_growth.append("Modern testing frameworks")
        elif top_domain == "DevOps":
            areas_for_growth.append("CI/CD pipeline automation")
        elif top_domain == "Cloud/SA":
            areas_for_growth.append("Cloud architecture and design patterns")
        elif "Clinical Research" in top_domain or "CRC" in top_domain:
            areas_for_growth.append("IRB protocol management")
        elif "Medical Assistant" in top_domain:
            areas_for_growth.append("EHR/EMR system proficiency")
        elif "Public Health" in top_domain:
            areas_for_growth.append("Epidemiological analysis")
        elif "Teacher" in top_domain or "Education" in top_domain:
            areas_for_growth.append("Lesson planning and curriculum design")
        elif "Accountant" in top_domain or "Financial" in top_domain:
            areas_for_growth.append("GAAP and financial reporting")
        else:
            areas_for_growth.append("Industry best practices and advanced techniques")
    
    # Generate recommended_roles based on top domain (PRIMARY role) and evidence
    recommended_roles = []
    top_domain = domains[0]["name"] if domains else "Professional"
    top_domain_lower = top_domain.lower()
    
    # Always use top domain as primary recommendation
    if top_domain == "Data Analyst":
        recommended_roles = ["Data Analyst", "Business Analyst", "BI Analyst", "Analytics Engineer"]
    elif top_domain == "ML/AI":
        recommended_roles = ["ML Engineer", "Data Scientist", "AI Engineer", "ML Researcher"]
    elif top_domain == "Frontend":
        recommended_roles = ["Frontend Engineer", "UI Developer", "React Developer", "Frontend Developer"]
    elif top_domain == "Backend":
        recommended_roles = ["Backend Engineer", "API Developer", "Software Engineer", "Backend Developer"]
    elif top_domain == "Full-Stack":
        recommended_roles = ["Full Stack Developer", "Full-Stack Engineer", "Software Engineer", "Web Developer"]
    elif top_domain == "Data Engineer":
        recommended_roles = ["Data Engineer", "ETL Engineer", "Data Pipeline Engineer", "Big Data Engineer"]
    elif top_domain == "DevOps":
        recommended_roles = ["DevOps Engineer", "Site Reliability Engineer (SRE)", "Cloud Engineer", "Infrastructure Engineer"]
    elif top_domain == "Cloud/SA":
        recommended_roles = ["Cloud Architect", "Solutions Architect", "Cloud Engineer", "AWS/Azure/GCP Specialist"]
    elif "clinical research" in top_domain_lower or "crc" in top_domain_lower:
        recommended_roles = ["Clinical Research Coordinator", "Research Assistant", "Clinical Trial Manager", "Regulatory Affairs Specialist"]
    elif "public health" in top_domain_lower:
        recommended_roles = ["Public Health Analyst", "Epidemiologist", "Health Policy Analyst", "Research Analyst"]
    elif "teacher" in top_domain_lower or "education" in top_domain_lower:
        recommended_roles = ["Teacher", "Education Coordinator", "Curriculum Specialist", "Instructional Designer"]
    elif "accountant" in top_domain_lower:
        recommended_roles = ["Accountant", "Staff Accountant", "Senior Accountant", "Financial Analyst"]
    elif "financial analyst" in top_domain_lower:
        recommended_roles = ["Financial Analyst", "Investment Analyst", "Risk Analyst", "Business Analyst"]
    else:
        recommended_roles = [top_domain] if top_domain else ["Professional"]
    
    return {
        "domains": domains,
        "skills": {
            "core": skills_core,
            "adjacent": skills_adjacent,
            "advanced": skills_advanced
        },
        "strengths": strengths if strengths else ["Professional experience demonstrated"],
        "areas_for_growth": areas_for_growth,
        "recommended_roles": recommended_roles,
        "keywords_detected": keywords
    }


@router.post("")
async def analyze_resume(
    request: AnalyzeRequest,
    response: Response,
    hash: str | None = Query(None, description="Resume hash for cache busting")
):
    """
    Analyze resume text using Anthropic/OpenAI or keyword-based fallback.
    Returns domain classification, skills, strengths, and recommended roles.
    """
    try:
        # Use resume_text if provided, otherwise use text (legacy support)
        resume_text = request.resume_text or request.text
        
        if not resume_text or len(resume_text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Resume text cannot be empty")
        
        # Compute resume hash
        resume_hash = hashlib.sha256(resume_text.encode('utf-8')).hexdigest()
        debug_hash = resume_hash[:8]
        
        # Add Cache-Control header
        response.headers["Cache-Control"] = "no-store"
        
        provider = "heuristic"
        result_dict = None
        
        # Get target_role from request (primary field - check all possible fields)
        target_role = None
        if request.target_role:  # Primary field (snake_case)
            target_role = request.target_role
            print(f"[Analyze] Using target_role from request: {target_role}")
        elif request.targetRole:  # Legacy support (camelCase)
            target_role = request.targetRole
            print(f"[Analyze] Using targetRole from request: {target_role}")
        elif request.preferred_roles and len(request.preferred_roles) > 0:
            target_role = request.preferred_roles[0]
            print(f"[Analyze] Using preferred_roles[0] from request: {target_role}")
        elif request.target_roles and len(request.target_roles) > 0:
            target_role = request.target_roles[0]
            print(f"[Analyze] Using target_roles[0] from request: {target_role}")
        
        # PRE-VALIDATION: Check if target_role matches resume content BEFORE calling LLM
        # If target_role doesn't match, ignore it completely
        resume_lower = resume_text.lower()
        original_target_role = target_role
        if target_role:
            target_role_lower = target_role.lower()
            
            # Check if target_role is AI/ML but resume has Animation keywords
            if ("ai engineer" in target_role_lower or "ml engineer" in target_role_lower or "machine learning" in target_role_lower):
                ai_ml_keywords = ["machine learning", "ml", "ai", "pytorch", "tensorflow", "sklearn", "neural network", "deep learning", "llm", "transformer"]
                animation_keywords = ["animation", "motion graphics", "after effects", "maya", "blender", "character design", "storyboarding", "3d animation", "2d animation", "motion design", "unreal engine", "godot", "motion capture", "mocap"]
                
                has_ai_ml = any(keyword in resume_lower for keyword in ai_ml_keywords)
                has_animation = any(keyword in resume_lower for keyword in animation_keywords)
                
                # If resume has Animation keywords but NOT AI/ML keywords, ignore target_role
                if has_animation and not has_ai_ml:
                    print(f"[Analyze] WARNING: target_role '{target_role}' doesn't match resume (has Animation keywords, no AI/ML keywords). Ignoring target_role, hash={debug_hash}")
                    target_role = None  # Ignore target_role completely
                elif not has_ai_ml:
                    print(f"[Analyze] WARNING: target_role '{target_role}' doesn't match resume (no AI/ML keywords found). Ignoring target_role, hash={debug_hash}")
                    target_role = None  # Ignore target_role completely
        
        print(f"[Analyze] Final target_role: {target_role} (original: {original_target_role}), hash={debug_hash}")
        
        # Try Anthropic first (primary LLM)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                result_dict = anthropic_service.analyze_resume(
                    text=resume_text,
                    target_role=target_role
                )
                provider = "anthropic"
                print(f"[Analyze] Anthropic analysis successful: hash={debug_hash}, target_role={target_role}")
            except Exception as e:
                print(f"[Analyze] Anthropic failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Try OpenAI if Anthropic failed (fallback LLM)
        if not result_dict:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                try:
                    from app.services.openai_svc import openai_service
                    result_dict = openai_service.analyze_resume(
                        text=resume_text,
                        target_role=target_role
                    )
                    provider = "openai"
                    print(f"[Analyze] OpenAI analysis successful: hash={debug_hash}, target_role={target_role}")
                except Exception as e:
                    print(f"[Analyze] OpenAI failed: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Use keyword-based fallback if LLM not available or failed
        if not result_dict:
            print(f"[Analyze] Using keyword-based fallback: hash={debug_hash}, target_role={target_role}")
            result_dict = keyword_based_analysis(resume_text, request.top_k_domains, target_role)
            provider = "heuristic"
        
        # Ensure areas_for_growth is never empty (post-process LLM output if needed)
        if result_dict and (not result_dict.get("areas_for_growth") or len(result_dict.get("areas_for_growth", [])) == 0):
            print(f"[Analyze] areas_for_growth is empty, filling from competency matrix: hash={debug_hash}, target_role={target_role}")
            # Use keyword-based analysis to fill gaps
            top_domain = result_dict.get("domains", [{}])[0].get("name", "Professional") if result_dict.get("domains") else "Professional"
            fallback_gaps = keyword_based_analysis(resume_text, request.top_k_domains, target_role)
            result_dict["areas_for_growth"] = fallback_gaps.get("areas_for_growth", [])
        
        # Ensure we have the required fields
        if "domains" not in result_dict:
            result_dict["domains"] = classify_domains(resume_text, request.top_k_domains)
        
        # VALIDATION: Check if target_role matches the resume content
        # If target_role doesn't match, analyze based on actual resume content instead
        resume_lower = resume_text.lower()
        target_role_matches = False
        detected_primary_domain = None
        
        if result_dict.get("domains"):
            detected_primary_domain = result_dict["domains"][0]["name"] if result_dict["domains"] else None
            detected_primary_domain_lower = detected_primary_domain.lower() if detected_primary_domain else ""
            
            # Check if target_role matches the detected primary domain
            if target_role:
                target_role_lower = target_role.lower()
                
                # Check if target_role keywords match resume content
                # For AI/ML roles, check for ML/AI keywords in resume
                if "ai engineer" in target_role_lower or "ml engineer" in target_role_lower or "machine learning" in target_role_lower:
                    ai_ml_keywords = ["machine learning", "ml", "ai", "pytorch", "tensorflow", "sklearn", "neural network", "deep learning", "llm", "transformer"]
                    target_role_matches = any(keyword in resume_lower for keyword in ai_ml_keywords)
                # For Animation/Motion Graphics, check for animation keywords
                elif "animation" in target_role_lower or "motion graphics" in target_role_lower or "motion design" in target_role_lower:
                    animation_keywords = ["animation", "motion graphics", "after effects", "maya", "blender", "character design", "storyboarding", "3d animation", "2d animation", "motion design", "unreal engine", "godot"]
                    target_role_matches = any(keyword in resume_lower for keyword in animation_keywords)
                # For other roles, check if target_role domain matches detected domain
                else:
                    # Check if target_role is similar to detected primary domain
                    target_role_matches = (
                        target_role_lower in detected_primary_domain_lower or
                        detected_primary_domain_lower in target_role_lower or
                        any(word in detected_primary_domain_lower for word in target_role_lower.split() if len(word) > 3)
                    )
                
                print(f"[Analyze] target_role: {target_role}, detected_primary: {detected_primary_domain}, matches: {target_role_matches}, hash={debug_hash}")
        
        # CRITICAL: Only force target_role if it matches the resume content
        # If it doesn't match, analyze based on actual resume content
        if target_role and result_dict.get("domains") and target_role_matches:
            print(f"[Analyze] target_role matches resume content, prioritizing: {target_role}, hash={debug_hash}")
            target_role_lower = target_role.lower()
            target_domain = None
            
            # Map target_role to domain name (works for all professions)
            # Tech roles
            if "ai engineer" in target_role_lower or "ml engineer" in target_role_lower or "machine learning" in target_role_lower or ("ai" in target_role_lower and "engineer" in target_role_lower):
                target_domain = "ML/AI"
            elif "data analyst" in target_role_lower or "business analyst" in target_role_lower:
                target_domain = "Data Analyst"
            elif "data engineer" in target_role_lower:
                target_domain = "Data Engineer"
            elif "frontend" in target_role_lower or "ui developer" in target_role_lower or "react" in target_role_lower:
                target_domain = "Frontend"
            elif "backend" in target_role_lower or "api developer" in target_role_lower:
                target_domain = "Backend"
            elif "full stack" in target_role_lower or "fullstack" in target_role_lower or "full-stack" in target_role_lower:
                target_domain = "Full-Stack"
            elif "devops" in target_role_lower or "dev ops" in target_role_lower or "sre" in target_role_lower or "site reliability" in target_role_lower:
                target_domain = "DevOps"
            elif "cloud" in target_role_lower and ("engineer" in target_role_lower or "architect" in target_role_lower):
                target_domain = "Cloud/SA"
            elif "software engineer" in target_role_lower or "software developer" in target_role_lower:
                target_domain = "Backend"
            # Healthcare roles
            elif "registered nurse" in target_role_lower or "rn" in target_role_lower or ("nurse" in target_role_lower and "registered" in target_role_lower):
                target_domain = "Registered Nurse"
            elif "medical assistant" in target_role_lower or "ma" in target_role_lower:
                target_domain = "Medical Assistant"
            elif "clinical research" in target_role_lower or "crc" in target_role_lower or "clinical trial" in target_role_lower:
                target_domain = "Clinical Research Coordinator"
            # Public Health
            elif "public health" in target_role_lower or "epidemiologist" in target_role_lower:
                target_domain = "Public Health Analyst"
            # Education
            elif "teacher" in target_role_lower or "educator" in target_role_lower or "instructor" in target_role_lower:
                target_domain = "Teacher"
            elif "education coordinator" in target_role_lower:
                target_domain = "Education Coordinator"
            # Finance/Accounting
            elif "accountant" in target_role_lower or "cpa" in target_role_lower:
                target_domain = "Accountant"
            elif "financial analyst" in target_role_lower:
                target_domain = "Financial Analyst"
            # Operations/Management
            elif "operations coordinator" in target_role_lower or "operations manager" in target_role_lower:
                target_domain = "Operations Coordinator"
            elif "administrative assistant" in target_role_lower or "admin assistant" in target_role_lower:
                target_domain = "Administrative Assistant"
            # Marketing/Sales
            elif "marketing" in target_role_lower and "specialist" in target_role_lower:
                target_domain = "Marketing Specialist"
            elif "sales" in target_role_lower and ("representative" in target_role_lower or "rep" in target_role_lower):
                target_domain = "Sales Representative"
            # Product/Business
            elif "product manager" in target_role_lower or "product analyst" in target_role_lower:
                target_domain = "Product/BA"
            else:
                # Try to find matching domain from detected domains
                for domain in result_dict["domains"]:
                    domain_lower = domain["name"].lower()
                    # Check if target_role contains domain name or vice versa
                    if (target_role_lower in domain_lower or domain_lower in target_role_lower or
                        any(word in domain_lower for word in target_role_lower.split() if len(word) > 3)):
                        target_domain = domain["name"]
                        print(f"[Analyze] Found matching domain: {target_domain} for target_role: {target_role}")
                        break
                
                # If no match found, use target_role as the domain name itself (open-world)
                if not target_domain:
                    target_domain = target_role  # Use the exact target_role as domain name
                    print(f"[Analyze] Using target_role as domain name: {target_domain}")
            
            # If target_domain found, FORCE it to be top domain
            if target_domain:
                domains = result_dict["domains"]
                # Find if target_domain exists in domains
                target_domain_index = next((i for i, d in enumerate(domains) if d["name"] == target_domain), None)
                
                if target_domain_index is not None:
                    # Move target domain to top and FORCE high score
                    target_domain_obj = domains.pop(target_domain_index)
                    target_domain_obj["score"] = 0.9  # Force high score for user-selected role
                    domains.insert(0, target_domain_obj)
                    print(f"[Analyze] Moved {target_domain} to top with score 0.9")
                else:
                    # Add target domain at top with very high score
                    domains.insert(0, {"name": target_domain, "score": 0.9})
                    print(f"[Analyze] Added {target_domain} at top with score 0.9")
                
                # Reduce scores of other domains to make target_role clearly primary
                for i, domain in enumerate(domains[1:], start=1):
                    if domain["score"] >= 0.9:
                        domains[i]["score"] = min(0.85, domain["score"] - 0.1)  # Reduce competing high scores
                
                result_dict["domains"] = domains[:request.top_k_domains]  # Limit to top_k
                print(f"[Analyze] Forced {target_domain} as top domain, hash={debug_hash}")
                
                # Generate role-specific recommended_roles based on target_role (works for all professions)
                # Use LLM-generated roles if available, otherwise generate based on target_role
                if not result_dict.get("recommended_roles") or len(result_dict.get("recommended_roles", [])) == 0:
                    # Generate recommended roles based on target_role
                    recommended_roles = [target_role]  # Always include the target role first
                    
                    # Add related roles based on profession family
                    if "ai engineer" in target_role_lower or "ml engineer" in target_role_lower:
                        recommended_roles.extend(["ML Engineer", "Data Scientist", "ML Researcher"])
                    elif "data analyst" in target_role_lower:
                        recommended_roles.extend(["Business Analyst", "BI Analyst", "Analytics Engineer"])
                    elif "devops" in target_role_lower or "dev ops" in target_role_lower or "sre" in target_role_lower or "site reliability" in target_role_lower:
                        recommended_roles.extend(["DevOps Engineer", "Site Reliability Engineer (SRE)", "Cloud Engineer", "Infrastructure Engineer"])
                    elif "data engineer" in target_role_lower:
                        recommended_roles.extend(["ETL Engineer", "Data Pipeline Engineer", "Big Data Engineer", "Analytics Engineer"])
                    elif "cloud" in target_role_lower and ("engineer" in target_role_lower or "architect" in target_role_lower):
                        recommended_roles.extend(["Cloud Architect", "Solutions Architect", "Cloud Engineer", "AWS/Azure/GCP Specialist"])
                    elif "registered nurse" in target_role_lower or "rn" in target_role_lower:
                        recommended_roles.extend(["Staff Nurse", "Charge Nurse", "Nurse Practitioner"])
                    elif "medical assistant" in target_role_lower:
                        recommended_roles.extend(["Certified Medical Assistant", "Clinical Assistant", "Patient Care Technician"])
                    elif "clinical research" in target_role_lower:
                        recommended_roles.extend(["Research Assistant", "Clinical Trial Manager", "Regulatory Affairs Specialist"])
                    elif "public health" in target_role_lower:
                        recommended_roles.extend(["Epidemiologist", "Health Policy Analyst", "Research Analyst"])
                    elif "teacher" in target_role_lower:
                        recommended_roles.extend(["Education Coordinator", "Curriculum Specialist", "Instructional Designer"])
                    elif "accountant" in target_role_lower:
                        recommended_roles.extend(["Staff Accountant", "Senior Accountant", "Financial Analyst"])
                    elif "financial analyst" in target_role_lower:
                        recommended_roles.extend(["Investment Analyst", "Risk Analyst", "Business Analyst"])
                    elif "operations" in target_role_lower:
                        recommended_roles.extend(["Operations Manager", "Logistics Coordinator", "Supply Chain Coordinator"])
                    elif "marketing" in target_role_lower:
                        recommended_roles.extend(["Marketing Coordinator", "Digital Marketing Specialist", "Brand Manager"])
                    elif "sales" in target_role_lower:
                        recommended_roles.extend(["Account Executive", "Business Development Representative", "Sales Manager"])
                    elif "product" in target_role_lower:
                        recommended_roles.extend(["Product Analyst", "Business Analyst", "Product Owner"])
                    else:
                        # Generic related roles for unknown professions
                        recommended_roles.extend([f"Senior {target_role}", f"{target_role} Specialist"])
                    
                    result_dict["recommended_roles"] = recommended_roles[:4]  # Limit to 4 roles
                    print(f"[Analyze] Generated recommended_roles: {recommended_roles}")
                
                # Update strengths and areas_for_growth to be role-specific
                # The LLM should have already done this, but we ensure it's role-relevant
                # If strengths are too generic, we'll keep LLM output but log it
                print(f"[Analyze] Strengths: {result_dict.get('strengths', [])}")
                print(f"[Analyze] Areas for growth: {result_dict.get('areas_for_growth', [])}")
        elif original_target_role and not target_role_matches:
            # Target role doesn't match resume - analyze based on actual content
            print(f"[Analyze] target_role '{original_target_role}' doesn't match resume content (detected: {detected_primary_domain}). Analyzing based on actual resume content instead, hash={debug_hash}")
            # Don't force target_role - let the analysis be based on actual resume content
            # The domains are already correctly classified by classify_domains or LLM
            
            # POST-PROCESSING: If Animation/Motion Graphics is detected, ensure it's the top domain
            if result_dict.get("domains"):
                domains = result_dict["domains"]
                animation_domain_index = next((i for i, d in enumerate(domains) if "animation" in d["name"].lower() or "motion graphics" in d["name"].lower() or "motion design" in d["name"].lower()), None)
                
                if animation_domain_index is not None and animation_domain_index > 0:
                    # Move Animation/Motion Graphics to top
                    animation_domain = domains.pop(animation_domain_index)
                    animation_domain["score"] = 0.9  # High score for actual resume content
                    domains.insert(0, animation_domain)
                    result_dict["domains"] = domains
                    print(f"[Analyze] Moved {animation_domain['name']} to top (actual resume content), hash={debug_hash}")
                    
                    # Update recommended_roles to Animation roles
                    if not result_dict.get("recommended_roles") or any("ml" in r.lower() or "ai engineer" in r.lower() or "data scientist" in r.lower() for r in result_dict.get("recommended_roles", [])):
                        result_dict["recommended_roles"] = ["Motion Graphics Designer", "3D Animator", "Character Animator", "Visual Effects Artist"]
                        print(f"[Analyze] Updated recommended_roles to Animation roles, hash={debug_hash}")
                    
                    # Update strengths to Animation-specific (remove AI/ML strengths)
                    if result_dict.get("strengths"):
                        # Filter out AI/ML strengths, keep only Animation-related
                        animation_strengths = [s for s in result_dict["strengths"] if any(kw in s.lower() for kw in ["animation", "motion", "maya", "blender", "after effects", "character", "3d", "2d", "unreal", "godot", "rigging", "storyboard"])]
                        if animation_strengths:
                            result_dict["strengths"] = animation_strengths
                        else:
                            # Generate Animation-specific strengths from resume
                            result_dict["strengths"] = []
                            if "after effects" in resume_lower:
                                result_dict["strengths"].append("Experience with After Effects for motion graphics")
                            if "maya" in resume_lower or "blender" in resume_lower:
                                result_dict["strengths"].append("3D animation and modeling skills")
                            if "character design" in resume_lower:
                                result_dict["strengths"].append("Character design and animation expertise")
                            if "unreal engine" in resume_lower or "godot" in resume_lower:
                                result_dict["strengths"].append("Game engine experience for interactive animation")
                    
                    # Update areas_for_growth to Animation-specific (remove AI/ML gaps)
                    if result_dict.get("areas_for_growth"):
                        # Filter out AI/ML gaps, keep only Animation-related
                        animation_gaps = [g for g in result_dict["areas_for_growth"] if any(kw in g.lower() for kw in ["animation", "motion", "rigging", "compositing", "rendering", "lighting", "texturing", "vfx", "visual effects"])]
                        if not animation_gaps:
                            # Generate Animation-specific gaps
                            result_dict["areas_for_growth"] = [
                                "Advanced rigging techniques for complex characters",
                                "Compositing and visual effects integration",
                                "Rendering optimization and pipeline efficiency",
                                "Advanced lighting and texturing workflows"
                            ]
                        else:
                            result_dict["areas_for_growth"] = animation_gaps
                        print(f"[Analyze] Updated areas_for_growth to Animation-specific, hash={debug_hash}")
        
        # FINAL POST-PROCESSING: Always check if Animation is detected and ML/AI is incorrectly top
        # This runs regardless of target_role validation to ensure accuracy
        if result_dict.get("domains") and original_target_role:
            domains = result_dict["domains"]
            top_domain_name = domains[0]["name"] if domains else ""
            animation_domain_index = next((i for i, d in enumerate(domains) if "animation" in d["name"].lower() or "motion graphics" in d["name"].lower() or "motion design" in d["name"].lower()), None)
            
            # If ML/AI is top but Animation is detected and target_role was AI Engineer (but doesn't match)
            if ("ml/ai" in top_domain_name.lower() or "ai" in top_domain_name.lower()) and animation_domain_index is not None:
                # Check if resume has Animation keywords but NOT AI/ML keywords
                animation_keywords = ["animation", "motion graphics", "after effects", "maya", "blender", "character design", "storyboarding", "3d animation", "2d animation", "motion design", "unreal engine", "godot", "motion capture", "mocap"]
                ai_ml_keywords = ["machine learning", "ml", "pytorch", "tensorflow", "sklearn", "neural network", "deep learning", "llm", "transformer"]
                
                has_animation = any(kw in resume_lower for kw in animation_keywords)
                has_ai_ml = any(kw in resume_lower for kw in ai_ml_keywords)
                
                # If resume has Animation keywords but NOT AI/ML keywords, force Animation to top
                if has_animation and not has_ai_ml:
                    print(f"[Analyze] FINAL FIX: ML/AI is top but resume is clearly Animation. Moving Animation to top, hash={debug_hash}")
                    animation_domain = domains.pop(animation_domain_index)
                    animation_domain["score"] = 0.9
                    domains.insert(0, animation_domain)
                    result_dict["domains"] = domains
                    
                    # Force Animation-specific recommended_roles
                    result_dict["recommended_roles"] = ["Motion Graphics Designer", "3D Animator", "Character Animator", "Visual Effects Artist"]
                    
                    # Force Animation-specific strengths
                    animation_strengths = []
                    if "after effects" in resume_lower:
                        animation_strengths.append("Experience with After Effects for motion graphics")
                    if "maya" in resume_lower or "blender" in resume_lower:
                        animation_strengths.append("3D animation and modeling skills")
                    if "character design" in resume_lower:
                        animation_strengths.append("Character design and animation expertise")
                    if "unreal engine" in resume_lower or "godot" in resume_lower:
                        animation_strengths.append("Game engine experience for interactive animation")
                    if "motion graphics" in resume_lower:
                        animation_strengths.append("Motion graphics design and animation")
                    if not animation_strengths:
                        animation_strengths = ["Animation and motion graphics expertise"]
                    result_dict["strengths"] = animation_strengths
                    
                    # Force Animation-specific areas_for_growth
                    result_dict["areas_for_growth"] = [
                        "Advanced rigging techniques for complex characters",
                        "Compositing and visual effects integration",
                        "Rendering optimization and pipeline efficiency",
                        "Advanced lighting and texturing workflows"
                    ]
                    
                    print(f"[Analyze] FINAL FIX: Updated to Animation/Motion Graphics analysis, hash={debug_hash}")
        
        if "keywords_detected" not in result_dict:
            top_domain = result_dict["domains"][0]["name"] if result_dict["domains"] else "Professional"
            result_dict["keywords_detected"] = extract_keywords(resume_text, top_domain)
        
        # Add debug info
        result_dict["debug"] = {
            "hash": debug_hash,
            "provider": provider
        }
        
        # Validate and return response
        try:
            analyze_response = AnalyzeResponse(**result_dict)
        except Exception as e:
            print(f"[Analyze] Schema validation error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to keyword-based
            result_dict = keyword_based_analysis(resume_text, request.top_k_domains, target_role)
            result_dict["debug"] = {"hash": debug_hash, "provider": "heuristic"}
            analyze_response = AnalyzeResponse(**result_dict)
        
        # Send Amplitude event (only hash/counts/provider, no raw text)
        strengths_count = len(analyze_response.strengths)
        domains_count = len(analyze_response.domains)
        amplitude_service.track(
            event_type="analysis_completed_server",
            event_properties={
                "hash": debug_hash,
                "provider": provider,
                "strengths_count": strengths_count,
                "domains_count": domains_count,
            }
        )
        
        # Log only hash, counts, provider (no resume text)
        print(f"[Analyze] Completed: hash={debug_hash}, provider={provider}, strengths={strengths_count}, domains={domains_count}")
        
        return analyze_response.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analyze] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

