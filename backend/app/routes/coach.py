from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.models.schemas import CoachPlan
from app.services.coach_svc import coach_service
from app.services.amplitude import amplitude_service

router = APIRouter(prefix="/autoCoach", tags=["coach"])


class CoachRequest(BaseModel):
    gaps: List[str]
    targetRole: Optional[str] = None
    domain: Optional[str] = None  # Domain/field (ML/AI, Frontend, Backend, etc.)
    reminders: bool = False


@router.post("", response_model=CoachPlan)
async def auto_coach(request: CoachRequest) -> CoachPlan:
    """
    Generate an automated 7-day coaching plan based on skill gaps using AI.
    """
    try:
        # Generate coaching plan using AI
        coach_plan = coach_service.generate_coach_plan(
            gaps=request.gaps,
            target_role=request.targetRole,
            domain=request.domain,
            reminders=request.reminders
        )
        
        # Send Amplitude event
        amplitude_service.track(
            event_type="coach_plan_generated",
            event_properties={
                "gap_count": len(request.gaps),
                "has_target_role": request.targetRole is not None,
                "reminders_enabled": request.reminders,
                "plan_days": len(coach_plan.plan),
            }
        )
        
        return coach_plan
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Fallback to mock data if AI fails
        from app.models.schemas import PlanDay
        
        # Generate domain-aware mock plan
        domain = request.domain or "Software Engineer"
        
        if domain == "ML/AI":
            mock_plan = [
                PlanDay(day=1, title="Introduction to Machine Learning", actions=[
                    "Complete 'Machine Learning' course on Coursera (https://www.coursera.org/learn/machine-learning)",
                    "Learn Python basics for ML on DataCamp (https://www.datacamp.com/courses/intro-to-python-for-data-science)"
                ]),
                PlanDay(day=2, title="Deep Learning Fundamentals", actions=[
                    "Complete Deep Learning course on Fast.ai (https://www.fast.ai/)",
                    "Learn PyTorch basics on PyTorch official tutorials (https://pytorch.org/tutorials/)"
                ]),
                PlanDay(day=3, title="Large Language Models", actions=[
                    "Learn Transformers on Hugging Face (https://huggingface.co/learn/nlp-course)",
                    "Watch 'LLM Tutorial' on YouTube (https://www.youtube.com/results?search_query=large+language+models)"
                ]),
                PlanDay(day=4, title="MLOps and Model Deployment", actions=[
                    "Learn MLOps on Coursera (https://www.coursera.org/courses?query=mlops)",
                    "Practice deploying models with AWS SageMaker (https://aws.amazon.com/sagemaker/)"
                ]),
                PlanDay(day=5, title="Vector Databases and Embeddings", actions=[
                    "Learn about vector databases on Pinecone (https://www.pinecone.io/learn/)",
                    "Practice with embeddings using Hugging Face (https://huggingface.co/docs/transformers/main/en/tasks)"
                ]),
                PlanDay(day=6, title="Advanced AI Topics", actions=[
                    "Study transformer architectures in depth",
                    "Build a practical AI project"
                ]),
                PlanDay(day=7, title="Review and Next Steps", actions=[
                    "Review entire week's learning",
                    "Plan next steps for continued growth in AI/ML"
                ])
            ]
        elif domain == "Data Analyst":
            mock_plan = [
                PlanDay(day=1, title="SQL Fundamentals", actions=[
                    "Complete 'Introduction to SQL' on DataCamp (https://www.datacamp.com/courses/introduction-to-sql)",
                    "Practice SQL queries on LeetCode (https://leetcode.com/problemset/database/)"
                ]),
                PlanDay(day=2, title="Data Visualization", actions=[
                    "Learn Tableau on Udemy (https://www.udemy.com/courses/search/?q=tableau)",
                    "Learn Power BI on Microsoft Learn (https://learn.microsoft.com/power-bi/)"
                ]),
                PlanDay(day=3, title="Python for Data Analysis", actions=[
                    "Complete 'Python for Data Science' on DataCamp (https://www.datacamp.com/courses/intro-to-python-for-data-science)",
                    "Learn Pandas on Kaggle (https://www.kaggle.com/learn/pandas)"
                ]),
                PlanDay(day=4, title="Statistics and Analytics", actions=[
                    "Learn Statistics on Coursera (https://www.coursera.org/courses?query=statistics)",
                    "Practice statistical analysis with real datasets"
                ]),
                PlanDay(day=5, title="Cloud Platforms", actions=[
                    "Learn AWS for Data Analytics (https://aws.amazon.com/training/learning-paths/data-analytics/)",
                    "Explore Google BigQuery (https://cloud.google.com/bigquery/docs)"
                ]),
                PlanDay(day=6, title="Data Storytelling", actions=[
                    "Learn data storytelling on Coursera (https://www.coursera.org/courses?query=data+storytelling)",
                    "Create a portfolio project with visualizations"
                ]),
                PlanDay(day=7, title="Review and Next Steps", actions=[
                    "Review entire week's learning",
                    "Plan next steps for continued growth"
                ])
            ]
        elif domain == "Frontend":
            mock_plan = [
                PlanDay(day=1, title="React Fundamentals", actions=[
                    "Complete 'React Basics' on freeCodeCamp (https://www.freecodecamp.org/learn/front-end-development-libraries/)",
                    "Build a simple React app"
                ]),
                PlanDay(day=2, title="TypeScript for React", actions=[
                    "Learn TypeScript on TypeScript official docs (https://www.typescriptlang.org/docs/)",
                    "Practice TypeScript with React on Udemy (https://www.udemy.com/courses/search/?q=typescript+react)"
                ]),
                PlanDay(day=3, title="Modern CSS and Styling", actions=[
                    "Learn Tailwind CSS (https://tailwindcss.com/docs)",
                    "Practice CSS Grid and Flexbox on CSS-Tricks (https://css-tricks.com/)"
                ]),
                PlanDay(day=4, title="Testing and Quality", actions=[
                    "Learn Jest and React Testing Library (https://testing-library.com/docs/react-testing-library/intro/)",
                    "Practice writing tests for React components"
                ]),
                PlanDay(day=5, title="Web Accessibility", actions=[
                    "Learn a11y on WebAIM (https://webaim.org/resources/)",
                    "Practice building accessible components"
                ]),
                PlanDay(day=6, title="Advanced Frontend Topics", actions=[
                    "Learn Next.js (https://nextjs.org/learn)",
                    "Build a portfolio project"
                ]),
                PlanDay(day=7, title="Review and Next Steps", actions=[
                    "Review entire week's learning",
                    "Plan next steps for continued growth"
                ])
            ]
        else:
            # Generic fallback for other domains
            mock_plan = [
                PlanDay(day=1, title="Fundamentals", actions=[
                    "Review core concepts in your domain",
                    "Complete a foundational course"
                ]),
                PlanDay(day=2, title="Intermediate Skills", actions=[
                    "Learn intermediate topics",
                    "Practice with hands-on exercises"
                ]),
                PlanDay(day=3, title="Advanced Concepts", actions=[
                    "Study advanced topics",
                    "Work on a project"
                ]),
                PlanDay(day=4, title="Practical Application", actions=[
                    "Build a real-world project",
                    "Apply learned skills"
                ]),
                PlanDay(day=5, title="Best Practices", actions=[
                    "Learn industry best practices",
                    "Review code and patterns"
                ]),
                PlanDay(day=6, title="Portfolio Development", actions=[
                    "Create portfolio projects",
                    "Document your work"
                ]),
                PlanDay(day=7, title="Review and Next Steps", actions=[
                    "Review entire week's learning",
                    "Plan next steps for continued growth"
                ])
        ]
        
        fallback_plan = CoachPlan(
            plan=mock_plan,
            reminders=request.reminders
        )
        
        # Still send Amplitude event with fallback flag
        amplitude_service.track(
            event_type="coach_plan_generated",
            event_properties={
                "gap_count": len(request.gaps),
                "has_target_role": request.targetRole is not None,
                "reminders_enabled": request.reminders,
                "plan_days": len(fallback_plan.plan),
                "fallback": True,
                "error": str(e)
            }
        )
        
        return fallback_plan

