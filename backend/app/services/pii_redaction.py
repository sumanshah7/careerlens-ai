"""
PII Redaction utility for removing personal information before sending to LLMs
Redacts: emails, phone numbers, URLs
"""
import re


def redact_pii(text: str) -> str:
    """
    Redact PII from text before sending to LLMs.
    
    Redacts:
    - Email addresses (user@example.com)
    - Phone numbers (various formats)
    - URLs (http://, https://)
    
    Returns text with PII replaced by placeholders.
    """
    if not text:
        return text
    
    # Redact email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, '[EMAIL_REDACTED]', text)
    
    # Redact phone numbers (various formats)
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890, 123.456.7890, 1234567890
        r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b',  # (123) 456-7890
        r'\b\+1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # +1-123-456-7890
        r'\b\d{10}\b',  # 10 digits
    ]
    for pattern in phone_patterns:
        text = re.sub(pattern, '[PHONE_REDACTED]', text)
    
    # Redact URLs (but keep domain names in text for context)
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    text = re.sub(url_pattern, '[URL_REDACTED]', text)
    
    # Redact LinkedIn profile URLs specifically
    linkedin_pattern = r'linkedin\.com/in/[^\s<>"{}|\\^`\[\]]+'
    text = re.sub(linkedin_pattern, '[LINKEDIN_REDACTED]', text)
    
    # Redact GitHub profile URLs
    github_pattern = r'github\.com/[^\s<>"{}|\\^`\[\]]+'
    text = re.sub(github_pattern, '[GITHUB_REDACTED]', text)
    
    return text

