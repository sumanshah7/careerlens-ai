from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from app.routes import analyze, jobs, tailor, coach, predict, upload, roleMatch, generatePlan, jobSearch, linkedinJobs
import traceback

app = FastAPI(title="CareerLens AI API", version="1.0.0")

# CORS middleware - allow localhost ports (Vite default ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze.router)
app.include_router(jobs.router)
app.include_router(tailor.router)
app.include_router(coach.router)
app.include_router(predict.router)
app.include_router(upload.router)
app.include_router(roleMatch.router)
app.include_router(generatePlan.router)
app.include_router(jobSearch.router)
app.include_router(linkedinJobs.router)


@app.get("/")
async def root():
    return {"message": "CareerLens AI API"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure CORS headers are always sent"""
    print(f"[Global Error Handler] {type(exc).__name__}: {str(exc)}")
    traceback.print_exc()
    
    # For roleMatch endpoint, return a valid response with jobs
    if "/roleMatchAndOpenings" in str(request.url):
        from app.models.schemas import RoleMatchResponse, RoleMatchItem
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "items": [{
                    "title": "Job Opening",
                    "company": "Company",
                    "location": "Remote",
                    "match": 0.5,
                    "why_fit": ["Relevant role match"],
                    "gaps": [],
                    "url": "https://www.linkedin.com/jobs/view/12345",
                    "source": "error-fallback"
                }],
                "debug": {
                    "hash": "error",
                    "source": "error-fallback",
                    "count": 1,
                    "error": str(exc)
                }
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    # For other endpoints, return error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "message": "An internal server error occurred"
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/health")
async def health():
    """Health check endpoint with provider status"""
    from app.config import settings
    from app.services.dedalus_svc import dedalus_service
    
    # Use settings object which loads from .env via pydantic-settings
    anthropic_key = settings.anthropic_api_key
    openai_key = settings.openai_api_key
    dedalus_key = settings.dedalus_api_key
    
    return {
        "ok": True,
        "providers": {
            "anthropic": bool(anthropic_key and anthropic_key.strip()),
            "openai": bool(openai_key and openai_key.strip()),
            "dedalus": bool(dedalus_key and dedalus_key.strip()),
            "mcp": bool(dedalus_service.dedalus_mcp_service and dedalus_service.dedalus_mcp_service.mcp_available) if dedalus_service.dedalus_mcp_service else False
        }
    }


# AWS Lambda handler
handler = Mangum(app)

