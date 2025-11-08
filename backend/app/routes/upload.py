"""
File upload route for PDF parsing
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_parser import pdf_parser

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)) -> dict:
    """
    Upload PDF file and extract text
    
    Args:
        file: PDF file to upload
        
    Returns:
        Extracted text from PDF
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Accept both 'application/pdf' and 'application/x-pdf' content types
    if file.content_type and file.content_type not in ['application/pdf', 'application/x-pdf']:
        raise HTTPException(status_code=400, detail=f"File must be a PDF. Got content type: {file.content_type}")
    
    try:
        # Read file content
        pdf_bytes = await file.read()
        
        if not pdf_bytes or len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Parse PDF
        text = pdf_parser.parse_pdf(pdf_bytes)
        
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="No text found in PDF. The PDF might be image-based or empty.")
        
        return {
            "text": text,
            "filename": file.filename,
            "size": len(pdf_bytes)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")

