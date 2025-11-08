"""
Configuration settings using pydantic-settings
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    amplitude_api_key: str | None = None
    rapidapi_key: str | None = None  # For RapidAPI LinkedIn Job Search API (RAPIDAPI_KEY)
    rapidapi_host: str = "linkedin-job-search-api.p.rapidapi.com"  # RAPIDAPI_HOST
    linkedin_base_url: str = "https://linkedin-job-search-api.p.rapidapi.com"  # LINKEDIN_BASE_URL
    dedalus_api_key: str | None = None  # For Dedalus Labs job research
    
    # Firebase
    firebase_service_account_path: str = "backend/firebase-service-account.json"
    
    # AWS
    aws_region: str = "us-east-1"
    s3_bucket: str = "careerlens-uploads"
    
    # API
    api_base_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

