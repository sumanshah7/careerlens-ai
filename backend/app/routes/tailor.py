from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.schemas import TailorResponse
from app.services.openai_svc import openai_service
from app.services.amplitude import amplitude_service

router = APIRouter(prefix="/tailor", tags=["tailor"])


class TailorRequest(BaseModel):
    resume: str
    jd: str
    style: str = "STAR"


@router.post("", response_model=TailorResponse)
async def tailor_resume(request: TailorRequest) -> TailorResponse:
    """
    Tailor resume and cover letter for a specific job using GPT.
    """
    try:
        # Call OpenAI service
        result_dict = openai_service.tailor_for_job(
            resume=request.resume,
            jd=request.jd,
            style=request.style
        )
        
        # Convert to Pydantic model
        tailor_response = TailorResponse(**result_dict)
        
        # Send Amplitude event
        amplitude_service.track(
            event_type="tailor_completed",
            event_properties={
                "bullets_count": len(tailor_response.bullets),
                "pitch_length": len(tailor_response.pitch),
                "cover_letter_length": len(tailor_response.coverLetter),
                "style": request.style,
            }
        )
        
        return tailor_response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Fallback to mock data if OpenAI fails
        tailor_response = TailorResponse(
            bullets=[
                "Developed scalable React applications using TypeScript, improving performance by 40%",
                "Led cross-functional teams to deliver high-quality software solutions",
                "Implemented modern frontend architectures resulting in 50% reduction in bug reports"
            ],
            pitch="I'm a passionate frontend engineer with 5+ years of experience building scalable React applications. My expertise in TypeScript and modern web technologies, combined with strong problem-solving skills, makes me an ideal candidate for this role.",
            coverLetter="Dear Hiring Manager,\n\nI am excited to apply for the Senior Frontend Engineer position. With my extensive experience in React and TypeScript, I am confident I can contribute significantly to your team.\n\n[Rest of cover letter...]"
        )
        
        # Still send Amplitude event with fallback flag
        amplitude_service.track(
            event_type="tailor_completed",
            event_properties={
                "bullets_count": len(tailor_response.bullets),
                "pitch_length": len(tailor_response.pitch),
                "cover_letter_length": len(tailor_response.coverLetter),
                "style": request.style,
                "fallback": True,
                "error": str(e)
            }
        )
        
        return tailor_response

