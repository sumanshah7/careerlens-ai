from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.schemas import TailorResponse
from app.services.openai_svc import openai_service
from app.services.amplitude import amplitude_service
from app.services.firestore_svc import firestore_service
from app.config import settings

router = APIRouter(prefix="/api/tailor", tags=["tailor"])


class TailorRequest(BaseModel):
    resume: str | None = None
    jd: str | None = None
    style: str = "STAR"
    resume_text: str | None = None  # Alternative field name
    job_title: str | None = None  # Optional job title
    company: str | None = None  # Optional company name
    job_description: str | None = None  # Alternative field name
    emphasize_metrics: bool = False  # Flag to emphasize quantifiable outcomes
    user_id: str | None = None  # Firebase user ID for storing in Firestore


@router.post("", response_model=TailorResponse)
async def tailor_resume(request: TailorRequest) -> TailorResponse:
    """
    Tailor resume and cover letter for a specific job using GPT.
    """
    try:
        # Use resume_text if provided, otherwise use resume (backward compatibility)
        resume_text = request.resume_text or request.resume
        # Use job_description if provided, otherwise use jd (backward compatibility)
        jd_text = request.job_description or request.jd
        
        # Validate that we have both resume and job description
        if not resume_text:
            raise HTTPException(status_code=400, detail="resume or resume_text is required")
        if not jd_text:
            raise HTTPException(status_code=400, detail="jd or job_description is required")
        
        print(f"[Tailor] Starting tailor request: job_title={request.job_title}, company={request.company}, resume_len={len(resume_text)}, jd_len={len(jd_text)}")
        
        import time
        start_time = time.time()
        
        # Check if OpenAI API key is available
        openai_key = settings.openai_api_key
        if not openai_key:
            print("[Tailor] ERROR: OPENAI_API_KEY not found in settings")
            raise HTTPException(status_code=500, detail="OpenAI API key not configured. Please set OPENAI_API_KEY in backend/.env")
        
        # Call OpenAI service with job title and company for better personalization
        # Run in thread pool to avoid blocking the event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        def tailor_sync():
            try:
                return openai_service.tailor_for_job(
                    resume=resume_text,
                    jd=jd_text,
                    style=request.style,
                    job_title=request.job_title,
                    company=request.company,
                    emphasize_metrics=request.emphasize_metrics
                )
            except Exception as e:
                print(f"[Tailor] Error in tailor_for_job: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        result_dict = await loop.run_in_executor(None, tailor_sync)
        
        print(f"[Tailor] Tailor request completed in {time.time() - start_time:.2f}s")
        
        elapsed_time = time.time() - start_time
        
        # Convert to Pydantic model
        tailor_response = TailorResponse(**result_dict)
        
        # Store in Firestore if user_id is provided
        doc_id = None
        if request.user_id:
            try:
                doc_id = firestore_service.save_cover_letter(
                    user_id=request.user_id,
                    resume_text=resume_text,
                    job_title=request.job_title or "Unknown",
                    company=request.company or "Unknown",
                    job_description=jd_text,
                    cover_letter=tailor_response.coverLetter,
                    bullets=tailor_response.bullets,
                    pitch=tailor_response.pitch,
                    metadata={
                        "style": request.style,
                        "is_evidence_only": tailor_response.isEvidenceOnly,
                        "validation_warnings": tailor_response.validationWarnings,
                        "evidence_used": tailor_response.evidenceUsed,
                        "elapsed_time_ms": int(elapsed_time * 1000),
                        "emphasize_metrics": request.emphasize_metrics,
                    }
                )
                print(f"[Tailor] Saved cover letter to Firestore with ID: {doc_id}")
            except Exception as e:
                print(f"[Tailor] Warning: Failed to save to Firestore: {e}")
                # Don't fail the request if Firestore save fails
        
        # Send Amplitude event (privacy-safe: no PII, only metadata)
        amplitude_service.track(
            event_type="tailor_completed",
            event_properties={
                "bullets_count": len(tailor_response.bullets),
                "pitch_length": len(tailor_response.pitch),
                "cover_letter_length": len(tailor_response.coverLetter),
                "style": request.style,
                "is_evidence_only": tailor_response.isEvidenceOnly,
                "has_validation_warnings": len(tailor_response.validationWarnings) > 0,
                "evidence_used_count": len(tailor_response.evidenceUsed),
                "elapsed_time_ms": int(elapsed_time * 1000),
                "emphasize_metrics": request.emphasize_metrics,
                "firestore_saved": doc_id is not None,
            }
        )
        
        # Add doc_id to response if available (we'll need to update the schema)
        response_dict = tailor_response.model_dump()
        if doc_id:
            response_dict["doc_id"] = doc_id
        
        return TailorResponse(**response_dict)
        
    except ValueError as e:
        print(f"[Tailor] ValueError: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        error_msg = str(e) if e else "Unknown error"
        error_type = type(e).__name__
        print(f"[Tailor] Exception ({error_type}): {error_msg}")
        import traceback
        traceback.print_exc()
        
        # This should not happen as tailor_for_job now returns evidence-only draft
        # But keep as safety net
        amplitude_service.track(
            event_type="tailor_failed",
            event_properties={
                "error": error_msg[:100],  # Truncate to avoid PII
                "error_type": error_type,
                "style": request.style,
            }
        )
        # Provide more helpful error message
        if not error_msg or error_msg.strip() == "":
            error_msg = f"{error_type}: Check backend logs for details"
        raise HTTPException(status_code=500, detail=f"Tailoring service unavailable: {error_msg[:200]}")

