"""
PDF generation endpoint for cover letters
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.firestore_svc import firestore_service
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


class PDFRequest(BaseModel):
    doc_id: str | None = None  # Firestore document ID
    cover_letter: str | None = None  # Direct cover letter text
    job_title: str | None = None
    company: str | None = None
    user_name: str | None = None
    user_email: str | None = None


@router.post("/cover-letter")
async def generate_cover_letter_pdf(request: PDFRequest) -> StreamingResponse:
    """
    Generate PDF cover letter from Firestore document or direct text
    """
    try:
        cover_letter_text = None
        job_title = request.job_title or "Position"
        company = request.company or "Company"
        
        # Get cover letter from Firestore if doc_id provided
        if request.doc_id:
            doc = firestore_service.get_cover_letter(request.doc_id)
            if not doc:
                raise HTTPException(status_code=404, detail="Cover letter not found")
            cover_letter_text = doc.get("cover_letter", "")
            job_title = doc.get("job_title", job_title)
            company = doc.get("company", company)
        elif request.cover_letter:
            cover_letter_text = request.cover_letter
        else:
            raise HTTPException(status_code=400, detail="Either doc_id or cover_letter must be provided")
        
        if not cover_letter_text:
            raise HTTPException(status_code=400, detail="Cover letter text is empty")
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=inch, bottomMargin=inch)
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor='#111827',
            spaceAfter=12,
            alignment=TA_LEFT
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            textColor='#111827',
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        date_style = ParagraphStyle(
            'CustomDate',
            parent=styles['BodyText'],
            fontSize=11,
            textColor='#6b7280',
            alignment=TA_LEFT,
            spaceAfter=24
        )
        
        # Build PDF content
        story = []
        
        # Date
        today = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(today, date_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Company and job title
        if company and job_title:
            story.append(Paragraph(f"{company}<br/>{job_title}", title_style))
        elif company:
            story.append(Paragraph(company, title_style))
        elif job_title:
            story.append(Paragraph(job_title, title_style))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # Cover letter text (split into paragraphs)
        paragraphs = cover_letter_text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Replace line breaks with <br/> for proper formatting
                para_formatted = para.replace('\n', '<br/>')
                story.append(Paragraph(para_formatted, body_style))
                story.append(Spacer(1, 0.15 * inch))
        
        # Closing
        story.append(Spacer(1, 0.2 * inch))
        if request.user_name:
            story.append(Paragraph(request.user_name, body_style))
        if request.user_email:
            story.append(Paragraph(request.user_email, body_style))
        
        # Build PDF
        doc.build(story)
        
        # Reset buffer position
        buffer.seek(0)
        
        # Generate filename
        filename = f"cover_letter_{company.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Return PDF as streaming response
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PDF] Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

